"""
services/recommendation.py
--------------------------
Fix Recommendation Engine for FixLoop AI.

Pipeline
--------
  ① Cache guard — return recent recommendation if one exists
  ② Load investigation row + evidence + deploy correlation
  ③ Load cluster context (tickets, metadata)
  ④ Run LLM recommendation chain (Groq)
       → title, description, priority, engineering_effort,
         expected_reduction_pct, expected_recovery_usd,
         confidence_score, estimated_eta, Jira ticket content
  ⑤ Persist to public.fix_recommendations
  ⑥ Return RecommendationOut

Public API
----------
    generate_recommendation(request: RecommendRequest) → RecommendationOut
    estimate_revenue_recovery(monthly_cost_usd, expected_reduction_pct) → float
"""

from __future__ import annotations

import json
import re
import uuid
from datetime import datetime, timedelta, timezone
from typing import Optional

import structlog

from core.config import settings
from models.common import ItemStatus
from models.recommendation import (
    RecommendRequest,
    RecommendationOut,
    RecommenderOutput,
)
from services.supabase_client import get_supabase

logger = structlog.get_logger(__name__)

_MODEL_VERSION = "fixloop-recommender-v1"


# ============================================================
# ① Cache guard
# ============================================================

async def _fetch_existing_recommendation(
    investigation_id: str,
) -> RecommendationOut | None:
    """
    Return a recent recommendation for this investigation if one exists
    within the RECOMMENDATION_CACHE_DAYS window.
    """
    sb     = await get_supabase()
    cutoff = (
        datetime.now(timezone.utc) - timedelta(days=settings.RECOMMENDATION_CACHE_DAYS)
    ).isoformat()

    resp = (
        await sb.table("fix_recommendations")
        .select("*")
        .eq("investigation_id", investigation_id)
        .gte("created_at", cutoff)
        .order("created_at", desc=True)
        .limit(1)
        .execute()
    )

    rows = resp.data or []
    if not rows:
        return None

    row = rows[0]
    logger.info(
        "cached_recommendation_found",
        recommendation_id  = row["id"],
        investigation_id   = investigation_id,
    )
    return _row_to_recommendation_out(row)


# ============================================================
# ② Data loading helpers
# ============================================================

async def _load_investigation(investigation_id: str) -> dict | None:
    """Fetch an investigation row by ID."""
    sb = await get_supabase()
    resp = (
        await sb.table("investigations")
        .select("*")
        .eq("id", investigation_id)
        .single()
        .execute()
    )
    return resp.data if resp.data else None


async def _load_evidence(investigation_id: str) -> list[dict]:
    """Fetch all investigation_evidence rows for an investigation."""
    sb = await get_supabase()
    resp = (
        await sb.table("investigation_evidence")
        .select("*")
        .eq("investigation_id", investigation_id)
        .order("sort_order")
        .execute()
    )
    return resp.data or []


async def _load_cluster(cluster_id: str) -> dict | None:
    """Fetch a cluster row by ID."""
    sb = await get_supabase()
    resp = (
        await sb.table("ticket_clusters")
        .select("*")
        .eq("id", cluster_id)
        .single()
        .execute()
    )
    return resp.data if resp.data else None


async def _load_deployment(deploy_id: str) -> dict | None:
    """Fetch a deployment row by ID."""
    sb = await get_supabase()
    resp = (
        await sb.table("deployments")
        .select("id, version, title, deployed_at, risk, notes")
        .eq("id", deploy_id)
        .single()
        .execute()
    )
    return resp.data if resp.data else None


# ============================================================
# ③ LLM recommendation chain
# ============================================================

_RECOMMENDER_SYSTEM = """\
You are the FixLoop AI fix recommendation engine.
Given a root-cause investigation report, cluster metadata, evidence trail,
and optional deployment correlation, produce an actionable engineering fix
recommendation.

Return ONLY a valid JSON object with EXACTLY these fields:
{
  "title":                    "<concise fix title, 5-12 words>",
  "description":              "<technical fix description, 2-5 sentences>",
  "priority":                 "<critical|high|medium|low>",
  "engineering_effort":       "<low|medium|high|very_high>",
  "confidence_score":         <float 0-100>,
  "expected_reduction_pct":   <float 0-100 — expected ticket reduction after fix>,
  "expected_recovery_usd":    <float — estimated monthly revenue recovery>,
  "estimated_eta":            "<human-readable ETA, e.g. '2 days', '1 week'>",
  "jira_title":               "<Jira ticket title>",
  "jira_description":         "<Jira ticket description in markdown, 3-8 sentences>",
  "jira_acceptance_criteria": [
    "<criterion 1>",
    "<criterion 2>",
    "<criterion 3>"
  ],
  "jira_severity":            "<blocker|critical|major|minor|trivial>"
}

Priority guide:
  critical = data loss / security / all users blocked, fix within hours
  high     = major feature broken, many users affected, fix within 1-2 days
  medium   = degraded UX, workaround exists, fix within 1 week
  low      = minor / cosmetic, schedule in next sprint

Engineering effort guide:
  low       = < 4 hours (config change, one-liner)
  medium    = 4 hours – 2 days (targeted code change)
  high      = 2-5 days (multi-component refactor)
  very_high = 5+ days (architectural change)

Revenue recovery: use the formula
  expected_recovery_usd = monthly_cost_usd × (expected_reduction_pct / 100)
  Then adjust upward if enterprise customers are affected.

Acceptance criteria: provide 3-5 specific, testable criteria.

Return ONLY the JSON — no markdown, no explanation.
"""


def _build_recommender_prompt(
    investigation: dict,
    cluster:       dict,
    evidence:      list[dict],
    deployment:    dict | None,
) -> str:
    """Assemble the user message for the LLM recommendation call."""

    # Evidence summary
    evidence_lines = []
    for i, ev in enumerate(evidence, 1):
        ev_type = ev.get("evidence_type", "unknown")
        title   = ev.get("title", "")
        detail  = ev.get("detail", "")
        weight  = ev.get("weight", 0.0)
        evidence_lines.append(
            f"  [{i}] ({ev_type}, weight={weight:.2f}) {title}: {detail}"
        )

    # Reasoning steps
    reasoning_steps = investigation.get("reasoning_steps") or []
    reasoning_text = "\n".join(f"  {i}. {s}" for i, s in enumerate(reasoning_steps, 1))

    # Deployment info
    deploy_section = "No correlated deployment found."
    if deployment:
        deploy_section = (
            f"Deployment ID:    {deployment.get('id', 'N/A')}\n"
            f"Version:          {deployment.get('version', 'N/A')}\n"
            f"Title:            {deployment.get('title', 'N/A')}\n"
            f"Deployed:         {deployment.get('deployed_at', 'N/A')}\n"
            f"Risk:             {deployment.get('risk', 'N/A')}\n"
            f"Notes:            {deployment.get('notes', 'N/A')}\n"
            f"Correlation:      {investigation.get('deploy_correlation_score', 0):.2%}"
        )

    # Simulation numbers
    sim_before = investigation.get("sim_before_ticket_count", 0)
    sim_after  = investigation.get("sim_after_ticket_count", 0)
    sim_pct    = investigation.get("sim_deflection_pct", 0)
    sim_usd    = investigation.get("sim_recovered_usd", 0)

    monthly_cost = float(cluster.get("monthly_cost_usd", 0))

    return f"""
INVESTIGATION REPORT
====================
Investigation ID:    {investigation.get("id", "N/A")}
Root Cause:          {investigation.get("root_cause", "Unknown")}
Confidence:          {investigation.get("confidence", 0):.1f}%
Impact Level:        {investigation.get("impact_level", "medium")}
Affected Customers:  {investigation.get("affected_customers", 0)}
Revenue Impact:      ${float(investigation.get("revenue_impact_usd", 0)):,.2f}/month

REASONING CHAIN
===============
{reasoning_text or "  No reasoning steps available."}

EVIDENCE TRAIL ({len(evidence)} items)
======================================
{chr(10).join(evidence_lines) if evidence_lines else "  No evidence items available."}

CLUSTER CONTEXT
===============
Cluster ID:          {cluster.get("id", "N/A")}
Title:               {cluster.get("title", "N/A")}
Summary:             {cluster.get("summary", "N/A")}
Product Area:        {cluster.get("product_area", "Unknown")}
Severity:            {cluster.get("severity", "medium")}
Total Tickets:       {cluster.get("ticket_count", 0)}
Affected Customers:  {cluster.get("affected_customers", 0)}
Monthly Cost (USD):  ${monthly_cost:,.2f}

DEPLOYMENT CORRELATION
======================
{deploy_section}

SIMULATION (from investigation)
===============================
Before Fix:          {sim_before} tickets
After Fix:           {sim_after} tickets (projected)
Deflection:          {sim_pct:.1f}%
Revenue Recovered:   ${float(sim_usd):,.2f}/month

Produce the fix recommendation JSON.
""".strip()


from services.llm import generate_recommendation

async def _run_recommender(
    investigation: dict,
    cluster:       dict,
    evidence:      list[dict],
    deployment:    dict | None,
) -> RecommenderOutput:
    """Dispatch to the Groq LLM backend."""
    logger.info(
        "recommender_start",
        investigation_id = investigation.get("id"),
        backend          = "groq",
        evidence_count   = len(evidence),
    )

    try:
        raw = await generate_recommendation(
            system_prompt=_RECOMMENDER_SYSTEM,
            user_prompt=_build_recommender_prompt(investigation, cluster, evidence, deployment),
        )
        output = _parse_recommender_output(raw, investigation, cluster)
    except Exception as exc:
        logger.error(
            "recommender_failed",
            error=str(exc),
            investigation_id=investigation.get("id"),
        )
        output = _fallback_recommender_output(investigation, cluster)

    logger.info(
        "recommender_complete",
        investigation_id = investigation.get("id"),
        priority         = output.priority,
        confidence       = output.confidence_score,
    )
    return output

# ============================================================
# ④ Persist to Supabase
# ============================================================

async def _persist_recommendation(
    investigation: dict,
    cluster:       dict,
    output:        RecommenderOutput,
    owner_user_id: Optional[str],
) -> str:
    """
    Upsert recommendation row to public.fix_recommendations.
    Returns the recommendation ID.
    """
    sb     = await get_supabase()
    rec_id = f"REC-{uuid.uuid4().hex[:6].upper()}"
    now    = datetime.now(timezone.utc).isoformat()

    row = {
        "id":                         rec_id,
        "cluster_id":                 cluster["id"],
        "investigation_id":           investigation.get("id"),
        "title":                      output.title,
        "description":                output.description,
        "priority":                   output.priority,
        "engineering_effort":         output.engineering_effort,
        "confidence_score":           round(output.confidence_score, 2),
        "owner_user_id":              owner_user_id,
        "status":                     "open",
        "expected_reduction_pct":     round(output.expected_reduction_pct, 2),
        "expected_recovery_usd":      round(output.expected_recovery_usd, 2),
        "before_ticket_count":        investigation.get("sim_before_ticket_count"),
        "after_ticket_count":         investigation.get("sim_after_ticket_count"),
        "estimated_eta":              output.estimated_eta,
        "jira_title":                 output.jira_title or None,
        "jira_description":           output.jira_description or None,
        "jira_acceptance_criteria":   output.jira_acceptance_criteria or None,
        "jira_severity":              output.jira_severity or None,
    }

    try:
        await sb.table("fix_recommendations").upsert(row, on_conflict="id").execute()
        logger.info("recommendation_persisted", recommendation_id=rec_id)
    except Exception as exc:
        logger.error("recommendation_persist_failed", error=str(exc))
        raise

    return rec_id


# ============================================================
# ⑤ Serialisation helpers
# ============================================================

def _row_to_recommendation_out(row: dict) -> RecommendationOut:
    """Convert a raw Supabase row into a RecommendationOut API model."""
    now = datetime.now(timezone.utc)

    def _parse_dt(v: str | None) -> datetime:
        if not v:
            return now
        try:
            return datetime.fromisoformat(v.replace("Z", "+00:00"))
        except (ValueError, AttributeError):
            return now

    # Jira fields stored as JSON in description metadata — decode if present
    # For DB-only rows (no Jira columns), these return None gracefully
    jira_criteria_raw = row.get("jira_acceptance_criteria")
    jira_criteria: list[str] | None = None
    if isinstance(jira_criteria_raw, list):
        jira_criteria = jira_criteria_raw
    elif isinstance(jira_criteria_raw, str):
        try:
            parsed = json.loads(jira_criteria_raw)
            jira_criteria = parsed if isinstance(parsed, list) else None
        except (json.JSONDecodeError, ValueError):
            jira_criteria = None

    return RecommendationOut(
        id                      = row["id"],
        cluster_id              = row["cluster_id"],
        investigation_id        = row.get("investigation_id"),
        title                   = row.get("title", ""),
        description             = row.get("description", ""),
        priority                = row.get("priority"),
        engineering_effort      = row.get("engineering_effort"),
        confidence_score        = float(row["confidence_score"]) if row.get("confidence_score") is not None else None,
        owner_name              = row.get("owner_name"),
        owner_user_id           = row.get("owner_user_id"),
        status                  = ItemStatus(row.get("status", "open")),
        expected_reduction_pct  = float(row["expected_reduction_pct"]) if row.get("expected_reduction_pct") is not None else None,
        expected_recovery_usd   = float(row["expected_recovery_usd"]) if row.get("expected_recovery_usd") is not None else None,
        actual_reduction_pct    = float(row["actual_reduction_pct"]) if row.get("actual_reduction_pct") is not None else None,
        actual_recovery_usd     = float(row["actual_recovery_usd"]) if row.get("actual_recovery_usd") is not None else None,
        before_ticket_count     = int(row["before_ticket_count"]) if row.get("before_ticket_count") is not None else None,
        after_ticket_count      = int(row["after_ticket_count"]) if row.get("after_ticket_count") is not None else None,
        estimated_eta           = row.get("estimated_eta"),
        external_ticket_url     = row.get("external_ticket_url"),
        jira_title              = row.get("jira_title"),
        jira_description        = row.get("jira_description"),
        jira_acceptance_criteria = jira_criteria,
        jira_severity           = row.get("jira_severity"),
        created_by              = row.get("created_by"),
        resolved_by             = row.get("resolved_by"),
        resolved_at             = _parse_dt(row.get("resolved_at")) if row.get("resolved_at") else None,
        created_at              = _parse_dt(row.get("created_at")),
        updated_at              = _parse_dt(row.get("updated_at")),
    )


def _build_recommendation_out(
    rec_id:        str,
    investigation: dict,
    cluster:       dict,
    output:        RecommenderOutput,
    owner_user_id: Optional[str],
) -> RecommendationOut:
    """Build RecommendationOut directly from in-memory objects (no second DB read)."""
    now = datetime.now(timezone.utc)

    return RecommendationOut(
        id                      = rec_id,
        cluster_id              = cluster["id"],
        investigation_id        = investigation.get("id"),
        title                   = output.title,
        description             = output.description,
        priority                = output.priority,
        engineering_effort      = output.engineering_effort,
        confidence_score        = output.confidence_score,
        owner_name              = None,
        owner_user_id           = owner_user_id,
        status                  = ItemStatus.OPEN,
        expected_reduction_pct  = output.expected_reduction_pct,
        expected_recovery_usd   = output.expected_recovery_usd,
        actual_reduction_pct    = None,
        actual_recovery_usd     = None,
        before_ticket_count     = investigation.get("sim_before_ticket_count"),
        after_ticket_count      = investigation.get("sim_after_ticket_count"),
        estimated_eta           = output.estimated_eta,
        external_ticket_url     = None,
        jira_title              = output.jira_title,
        jira_description        = output.jira_description,
        jira_acceptance_criteria = output.jira_acceptance_criteria,
        jira_severity           = output.jira_severity,
        created_by              = None,
        resolved_by             = None,
        resolved_at             = None,
        created_at              = now,
        updated_at              = now,
    )


# ============================================================
# ⑥ Revenue recovery estimator
# ============================================================

async def estimate_revenue_recovery(
    monthly_cost_usd:       float,
    expected_reduction_pct: float,
) -> float:
    """
    Calculate the estimated monthly revenue recovery for a fix.

    Formula: monthly_cost_usd × (expected_reduction_pct / 100)
    """
    return round(monthly_cost_usd * (expected_reduction_pct / 100), 2)


# ============================================================
# Public entry point
# ============================================================

async def generate_recommendation(request: RecommendRequest) -> RecommendationOut:
    """
    Run the full fix recommendation pipeline for an investigation.

    Steps:
        ① Check cache — return recent recommendation if available
        ② Load investigation, cluster, evidence, deployment
        ③ Call LLM recommendation chain (GPT-4o or Gemini)
        ④ Persist recommendation row
        ⑤ Return RecommendationOut

    Args:
        request: RecommendRequest with investigation_id, cluster_id.

    Returns:
        RecommendationOut — the full recommendation report.

    Raises:
        ValueError  — investigation or cluster not found.
        RuntimeError — LLM or DB error that could not be recovered.
    """
    log = logger.bind(
        investigation_id = request.investigation_id,
        cluster_id       = request.cluster_id,
    )
    log.info("recommendation_pipeline_start")

    # ── Cache guard ────────────────────────────────────────────
    if not request.force_refresh:
        cached = await _fetch_existing_recommendation(request.investigation_id)
        if cached:
            log.info("recommendation_cache_hit", recommendation_id=cached.id)
            return cached

    # ② Load investigation
    investigation = await _load_investigation(request.investigation_id)
    if investigation is None:
        raise ValueError(
            f"Investigation '{request.investigation_id}' not found."
        )

    # ② Load cluster
    cluster = await _load_cluster(request.cluster_id)
    if cluster is None:
        raise ValueError(f"Cluster '{request.cluster_id}' not found.")

    log.info(
        "context_loaded",
        root_cause         = investigation.get("root_cause", "")[:80],
        ticket_count       = cluster.get("ticket_count", 0),
        affected_customers = cluster.get("affected_customers", 0),
    )

    # ② Load evidence
    evidence = await _load_evidence(request.investigation_id)
    log.info("evidence_loaded", count=len(evidence))

    # ② Load deployment correlation
    deployment: dict | None = None
    deploy_id = investigation.get("deploy_correlation_id")
    if deploy_id:
        deployment = await _load_deployment(deploy_id)
        log.info("deployment_loaded", deploy_id=deploy_id)

    # ③ LLM recommendation
    output = await _run_recommender(investigation, cluster, evidence, deployment)

    # ④ Persist
    owner_str = str(request.owner_user_id) if request.owner_user_id else None
    rec_id = await _persist_recommendation(
        investigation, cluster, output, owner_str
    )

    # ⑤ Return
    result = _build_recommendation_out(
        rec_id, investigation, cluster, output, owner_str
    )
    log.info(
        "recommendation_pipeline_complete",
        recommendation_id      = rec_id,
        priority               = result.priority,
        expected_reduction_pct = result.expected_reduction_pct,
        expected_recovery_usd  = result.expected_recovery_usd,
    )
    return result
