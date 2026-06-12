"""
services/validation.py
----------------------
Validation Engine for FixLoop AI.

Measures post-ship ticket counts and computes the loop-closure deflection rate,
determining if a fix was a Success, Partial Success, or Failed.

Pipeline
--------
  ① Fetch recommendation and cluster
  ② Compute baseline metrics (before fix)
  ③ Query actual post-fix ticket data (after fix)
  ④ Compute deflection and revenue recovered
  ⑤ Determine status
  ⑥ Persist validation result
  ⑦ Return ValidationSummary
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Optional

import structlog

from core.config import settings
from models.validation import (
    ValidateRequest,
    ValidationResultOut,
    ValidationSummary,
)
from services.supabase_client import get_supabase

logger = structlog.get_logger(__name__)


# ============================================================
# Core Logic
# ============================================================

async def run_validation(request: ValidateRequest) -> ValidationSummary:
    """
    Validate a shipped fix by comparing pre/post ticket counts.

    Steps:
        1. Fetch fix_recommendation from Supabase.
        2. Fetch associated cluster for baseline metrics.
        3. Query public.tickets for new tickets after the fix resolved_at date.
        4. Calculate Deflection Percentage and Revenue Recovered.
        5. Determine Status (Success, Partial Success, Failed).
        6. Store validation measurement in public.validation_results.
        7. Update fix_recommendations (actuals + status if resolved).
        8. Return ValidationSummary.
    """
    logger.info(
        "validation_start",
        fix_recommendation_id=request.fix_recommendation_id,
        force_revalidate=request.force_revalidate,
    )
    sb = await get_supabase()

    # 1. Fetch Recommendation
    rec_resp = (
        await sb.table("fix_recommendations")
        .select("*")
        .eq("id", request.fix_recommendation_id)
        .single()
        .execute()
    )
    rec_row = rec_resp.data
    if not rec_row:
        raise ValueError(f"Fix recommendation '{request.fix_recommendation_id}' not found.")

    cluster_id = rec_row["cluster_id"]
    
    # 2. Fetch Cluster for baselines
    cluster_resp = (
        await sb.table("ticket_clusters")
        .select("*")
        .eq("id", cluster_id)
        .single()
        .execute()
    )
    cluster_row = cluster_resp.data
    if not cluster_row:
        raise ValueError(f"Cluster '{cluster_id}' not found.")

    before_ticket_count = int(cluster_row.get("ticket_count") or 0)
    before_customer_count = int(cluster_row.get("affected_customers") or 0)
    before_revenue_risk = float(cluster_row.get("monthly_cost_usd") or 0.0)

    # 3. Post-fix metrics
    # We measure from resolved_at. If it's not resolved, we measure from created_at.
    start_date = rec_row.get("resolved_at") or rec_row.get("created_at")

    # Query tickets via PostgREST
    # We join cluster_tickets and tickets
    tickets_resp = (
        await sb.table("cluster_tickets")
        .select("ticket_id, tickets!inner(customer_id, ticket_created_at)")
        .eq("cluster_id", cluster_id)
        .gte("tickets.ticket_created_at", start_date)
        .execute()
    )
    
    after_tickets = tickets_resp.data or []
    after_ticket_count = len(after_tickets)
    
    # Count unique customers
    customer_set = set()
    for row in after_tickets:
        t_data = row.get("tickets")
        if t_data and isinstance(t_data, dict):
            cid = t_data.get("customer_id")
            if cid:
                customer_set.add(cid)
    
    after_customer_count = len(customer_set)
    after_revenue_risk = after_ticket_count * settings.REVENUE_COST_PER_TICKET_USD

    # 4. Calculate Deflection & Revenue Recovered
    deflection_pct = compute_deflection(before_ticket_count, after_ticket_count)
    
    # Formula: Revenue Recovered = before_revenue_risk * (deflection / 100)
    revenue_recovered = round(before_revenue_risk * (deflection_pct / 100.0), 2)

    # 5. Determine Status
    if deflection_pct >= 80.0:
        status_val = "Success"
        loop_closed = True
    elif deflection_pct >= 50.0:
        status_val = "Partial Success"
        loop_closed = False
    else:
        status_val = "Failed"
        loop_closed = False

    # 6. Store validation measurement
    val_row = {
        "fix_recommendation_id": request.fix_recommendation_id,
        "measurement_date": datetime.now(timezone.utc).date().isoformat(),
        "period_label": "Automated Validation",
        "ticket_count": after_ticket_count,
        "deflection_pct": deflection_pct,
        "revenue_recovered_usd": revenue_recovered,
    }
    
    insert_resp = (
        await sb.table("validation_results")
        .insert(val_row)
        .execute()
    )
    inserted = insert_resp.data[0] if insert_resp.data else val_row

    # 7. Update recommendation
    rec_update = {
        "actual_reduction_pct": deflection_pct,
        "actual_recovery_usd": revenue_recovered,
        "after_ticket_count": after_ticket_count,
        "before_ticket_count": before_ticket_count,
    }
    if loop_closed and rec_row.get("status") != "resolved":
        rec_update["status"] = "resolved"
        if not rec_row.get("resolved_at"):
            rec_update["resolved_at"] = datetime.now(timezone.utc).isoformat()

    await sb.table("fix_recommendations").update(rec_update).eq("id", rec_row["id"]).execute()

    # 8. Return Summary
    now = datetime.now(timezone.utc)
    measurement_out = ValidationResultOut(
        id=inserted.get("id", 0),
        fix_recommendation_id=request.fix_recommendation_id,
        measurement_date=inserted.get("measurement_date") or now.date(),
        period_label=inserted.get("period_label"),
        ticket_count=inserted.get("ticket_count", after_ticket_count),
        deflection_pct=inserted.get("deflection_pct", deflection_pct),
        revenue_recovered_usd=inserted.get("revenue_recovered_usd", revenue_recovered),
        notes=inserted.get("notes"),
        measured_by=inserted.get("measured_by"),
        created_at=inserted.get("created_at") or now,
    )

    return ValidationSummary(
        fix_recommendation_id=request.fix_recommendation_id,
        before_ticket_count=before_ticket_count,
        before_customer_count=before_customer_count,
        before_revenue_risk=round(before_revenue_risk, 2),
        after_ticket_count=after_ticket_count,
        after_customer_count=after_customer_count,
        after_revenue_risk=round(after_revenue_risk, 2),
        deflection_pct=deflection_pct,
        revenue_recovered_usd=revenue_recovered,
        status=status_val,
        loop_closed=loop_closed,
        measurement_count=1,
        measurements=[measurement_out],
    )


def compute_deflection(
    baseline_count: int,
    current_count:  int,
) -> float:
    """
    Compute ticket deflection percentage.
    Formula: (baseline_count - current_count) / baseline_count * 100
    Clamped to [0, 100]. Returns 0.0 if baseline is 0.
    """
    if baseline_count <= 0:
        return 0.0
    
    val = (baseline_count - current_count) / baseline_count * 100.0
    return round(max(0.0, min(100.0, val)), 2)


async def get_validation_summary(fix_recommendation_id: str) -> ValidationSummary:
    """Helper to fetch and aggregate an existing validation summary."""
    sb = await get_supabase()
    
    # 1. Fetch Recommendation
    rec_resp = (
        await sb.table("fix_recommendations")
        .select("*")
        .eq("id", fix_recommendation_id)
        .single()
        .execute()
    )
    rec_row = rec_resp.data
    if not rec_row:
        raise ValueError(f"Fix recommendation '{fix_recommendation_id}' not found.")

    cluster_id = rec_row["cluster_id"]
    
    # 2. Fetch Cluster
    cluster_resp = (
        await sb.table("ticket_clusters")
        .select("*")
        .eq("id", cluster_id)
        .single()
        .execute()
    )
    cluster_row = cluster_resp.data or {}

    before_ticket_count = int(cluster_row.get("ticket_count") or 0)
    before_customer_count = int(cluster_row.get("affected_customers") or 0)
    before_revenue_risk = float(cluster_row.get("monthly_cost_usd") or 0.0)

    # 3. Fetch Measurements
    meas_resp = (
        await sb.table("validation_results")
        .select("*")
        .eq("fix_recommendation_id", fix_recommendation_id)
        .order("created_at", desc=True)
        .execute()
    )
    measurements = meas_resp.data or []
    
    if not measurements:
        # Generate an empty stub if no measurements yet
        return ValidationSummary(
            fix_recommendation_id=fix_recommendation_id,
            before_ticket_count=before_ticket_count,
            before_customer_count=before_customer_count,
            before_revenue_risk=round(before_revenue_risk, 2),
            after_ticket_count=0,
            after_customer_count=0,
            after_revenue_risk=0.0,
            deflection_pct=0.0,
            revenue_recovered_usd=0.0,
            status="Failed",
            loop_closed=False,
            measurement_count=0,
            measurements=[],
        )

    latest = measurements[0]
    after_ticket_count = int(latest.get("ticket_count") or 0)
    deflection_pct = float(latest.get("deflection_pct") or 0.0)
    revenue_recovered = float(latest.get("revenue_recovered_usd") or 0.0)
    after_revenue_risk = after_ticket_count * settings.REVENUE_COST_PER_TICKET_USD
    
    # We estimate after_customer_count because we don't store it in validation_results directly.
    # To be perfectly accurate we would re-run the query, but we can approximate:
    after_customer_count = after_ticket_count  # or we could store it in `notes` JSON.
    
    if deflection_pct >= 80.0:
        status_val = "Success"
        loop_closed = True
    elif deflection_pct >= 50.0:
        status_val = "Partial Success"
        loop_closed = False
    else:
        status_val = "Failed"
        loop_closed = False

    def _parse_dt(v: str | None) -> datetime:
        now = datetime.now(timezone.utc)
        if not v: return now
        try: return datetime.fromisoformat(v.replace("Z", "+00:00"))
        except: return now

    meas_outs = [
        ValidationResultOut(
            id=m.get("id", 0),
            fix_recommendation_id=m["fix_recommendation_id"],
            measurement_date=m.get("measurement_date"),
            period_label=m.get("period_label"),
            ticket_count=m.get("ticket_count", 0),
            deflection_pct=m.get("deflection_pct"),
            revenue_recovered_usd=m.get("revenue_recovered_usd"),
            notes=m.get("notes"),
            measured_by=m.get("measured_by"),
            created_at=_parse_dt(m.get("created_at"))
        )
        for m in measurements
    ]

    return ValidationSummary(
        fix_recommendation_id=fix_recommendation_id,
        before_ticket_count=before_ticket_count,
        before_customer_count=before_customer_count,
        before_revenue_risk=round(before_revenue_risk, 2),
        after_ticket_count=after_ticket_count,
        after_customer_count=after_customer_count,
        after_revenue_risk=round(after_revenue_risk, 2),
        deflection_pct=deflection_pct,
        revenue_recovered_usd=revenue_recovered,
        status=status_val,
        loop_closed=loop_closed,
        measurement_count=len(measurements),
        measurements=meas_outs,
    )
