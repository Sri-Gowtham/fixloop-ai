"""
services/investigation.py
-------------------------
Production Root Cause Investigation Engine for FixLoop AI.

Pipeline
--------
  ① Load cluster metadata + member ticket samples from Supabase
  ② Query deployments within the correlation window
  ③ Detect deploy-spike correlation (temporal proximity + ticket-count delta)
  ④ Run LLM reasoning chain (Groq)
       → root_cause, confidence, impact_level, revenue_impact,
         reasoning_steps, evidence_items, simulation
  ⑤ Persist to public.investigations + public.investigation_evidence
  ⑥ Return InvestigationOut

Public API
----------
    run_investigation(request: InvestigateRequest) → InvestigationOut
"""

from __future__ import annotations

import json
import re
import uuid
from collections import Counter
from datetime import date, datetime, timedelta, timezone
from typing import Optional

import structlog

from core.config import settings
from models.common import EvidenceType, SeverityLevel
from models.investigation import (
    ClusterContext,
    CorrelationResult,
    DeployCorrelation,
    DeploymentRow,
    EvidenceOut,
    InvestigateRequest,
    InvestigationOut,
    ReasonerOutput,
    SimulationResult,
)
from services.supabase_client import get_supabase

logger = structlog.get_logger(__name__)

_MODEL_VERSION = "fixloop-reasoner-v3"


# ============================================================
# ① Data loading helpers
# ============================================================

async def _load_cluster_context(cluster_id: str) -> ClusterContext | None:
    """
    Fetch cluster row + up to INVESTIGATION_TICKET_SAMPLE_SIZE member tickets.
    Returns None when the cluster_id does not exist.
    """
    sb = await get_supabase()

    # Cluster row
    cluster_resp = (
        await sb.table("ticket_clusters")
        .select("*")
        .eq("id", cluster_id)
        .single()
        .execute()
    )
    row = cluster_resp.data
    if not row:
        return None

    # Member ticket samples via junction
    junction_resp = (
        await sb.table("cluster_tickets")
        .select("ticket_id")
        .eq("cluster_id", cluster_id)
        .limit(settings.INVESTIGATION_TICKET_SAMPLE_SIZE)
        .execute()
    )
    ticket_ids = [r["ticket_id"] for r in (junction_resp.data or [])]

    ticket_samples: list[dict] = []
    if ticket_ids:
        tickets_resp = (
            await sb.table("tickets")
            .select("id, title, body, severity, customer_id, ticket_created_at")
            .in_("id", ticket_ids)
            .execute()
        )
        ticket_samples = tickets_resp.data or []

    return ClusterContext(
        cluster_id         = cluster_id,
        title              = row.get("title", ""),
        summary            = row.get("summary"),
        severity           = row.get("severity", "medium"),
        ticket_count       = row.get("ticket_count", 0),
        affected_customers = row.get("affected_customers", 0),
        monthly_cost_usd   = float(row.get("monthly_cost_usd", 0)),
        product_area       = row.get("product_area"),
        example_titles     = row.get("example_titles") or [],
        first_seen_at      = row.get("first_seen_at"),
        last_seen_at       = row.get("last_seen_at"),
        ticket_samples     = ticket_samples,
    )


async def _load_deployments(window_days: int) -> list[DeploymentRow]:
    """
    Load all deployments from public.deployments within the last N days
    PLUS a buffer of 14 days before that (to catch pre-spike deploys).
    """
    sb = await get_supabase()
    cutoff = (
        datetime.now(timezone.utc) - timedelta(days=window_days + 14)
    ).date().isoformat()

    resp = (
        await sb.table("deployments")
        .select("id, version, title, deployed_at, risk, notes")
        .gte("deployed_at", cutoff)
        .order("deployed_at", desc=False)
        .execute()
    )

    return [
        DeploymentRow(
            id          = r["id"],
            version     = r.get("version", ""),
            title       = r.get("title", ""),
            deployed_at = r.get("deployed_at", ""),
            risk        = r.get("risk", "low"),
            notes       = r.get("notes"),
        )
        for r in (resp.data or [])
    ]


# ============================================================
# ② Deploy correlation analysis
# ============================================================

def _parse_date_safe(value: str | None) -> date | None:
    if not value:
        return None
    try:
        return date.fromisoformat(value[:10])
    except (ValueError, TypeError):
        return None


def _days_between(d1: date | None, d2: date | None) -> int | None:
    if d1 is None or d2 is None:
        return None
    return abs((d2 - d1).days)


async def detect_deploy_correlation(
    ctx: ClusterContext,
    deployments: list[DeploymentRow],
    window_days: int,
) -> CorrelationResult:
    """
    Identify the deployment most likely responsible for the ticket cluster spike.

    Algorithm:
        1. Determine the cluster's "onset date" (first_seen_at or earliest ticket).
        2. For each deployment, compute temporal proximity to the onset:
               proximity = 1 / (1 + days_between_deploy_and_onset)
        3. Apply a risk multiplier (critical=1.4, high=1.2, medium=1.0, low=0.8).
        4. Normalise all scores to [0, 1].
        5. Require the deploy to be BEFORE the onset (causal ordering).
        6. Return the highest-scoring deployment above 0.30 threshold.
    """
    if not deployments:
        logger.info("no_deployments_for_correlation", cluster_id=ctx.cluster_id)
        return CorrelationResult(
            best_deploy       = None,
            correlation_score = 0.0,
            days_to_spike     = None,
            all_deployments   = [],
        )

    onset = _parse_date_safe(ctx.first_seen_at)
    if onset is None:
        # Fall back to earliest ticket created_at
        dates = [
            _parse_date_safe(t.get("ticket_created_at"))
            for t in ctx.ticket_samples
            if t.get("ticket_created_at")
        ]
        onset = min(dates) if dates else date.today()

    risk_multiplier = {"critical": 1.4, "high": 1.2, "medium": 1.0, "low": 0.8}

    scored: list[tuple[DeploymentRow, float, int]] = []  # (deploy, raw_score, days)
    for deploy in deployments:
        d_date = _parse_date_safe(deploy.deployed_at)
        if d_date is None:
            continue

        days = (onset - d_date).days   # positive = deploy came BEFORE onset
        if days < 0:
            # Deploy happened AFTER spike onset — cannot be a cause
            continue
        if days > window_days + 14:
            continue

        # Proximity score: peaks at 0 days, decays with distance
        proximity = 1.0 / (1.0 + days)
        # Risk multiplier
        multiplier = risk_multiplier.get(deploy.risk.lower(), 1.0)
        score = proximity * multiplier
        scored.append((deploy, score, days))

    if not scored:
        return CorrelationResult(
            best_deploy       = None,
            correlation_score = 0.0,
            days_to_spike     = None,
            all_deployments   = deployments,
        )

    # Normalise to [0, 1]
    max_score = max(s for _, s, _ in scored)
    if max_score == 0:
        return CorrelationResult(
            best_deploy       = None,
            correlation_score = 0.0,
            days_to_spike     = None,
            all_deployments   = deployments,
        )

    scored = [(d, s / max_score, days) for d, s, days in scored]
    scored.sort(key=lambda x: x[1], reverse=True)

    best_deploy, best_score, best_days = scored[0]

    logger.info(
        "deploy_correlation_result",
        cluster_id        = ctx.cluster_id,
        best_deploy_id    = best_deploy.id,
        score             = round(best_score, 4),
        days_to_spike     = best_days,
    )

    return CorrelationResult(
        best_deploy       = best_deploy if best_score >= 0.30 else None,
        correlation_score = round(best_score, 4),
        days_to_spike     = best_days,
        all_deployments   = deployments,
    )


# ============================================================
# ③ LLM reasoning chain
# ============================================================

_REASONER_SYSTEM = """\
You are the FixLoop AI root-cause investigation engine.
Given a cluster of support tickets and optional deployment data, produce a
structured root-cause analysis.

Return ONLY a valid JSON object with EXACTLY these fields:
{
  "root_cause":      "<1-2 sentence description of the technical root cause>",
  "confidence":      <float 0-100>,
  "impact_level":    "<critical|high|medium|low>",
  "revenue_impact":  <estimated USD per month as a number>,
  "reasoning_steps": [
    "<step 1 observation>",
    "<step 2 observation>",
    "<step 3 observation>"
  ],
  "evidence_items": [
    {
      "type":   "<ticket_pattern|deploy_correlation|customer_impact|similar_ticket>",
      "title":  "<short title>",
      "detail": "<1 sentence detail>",
      "weight": <float 0.0-1.0>
    }
  ],
  "sim_deflection_pct": <float 0-100 — estimated ticket reduction after a fix>,
  "sim_before_count":   <int — current open ticket count>,
  "sim_after_count":    <int — estimated count after fix>
}

Severity guide:
  critical = data loss / security / all users blocked
  high     = major feature broken, many users affected
  medium   = degraded UX, workaround exists
  low      = minor / cosmetic

Revenue impact: use the ticket count × $70/ticket/month as a floor estimate,
then adjust up if enterprise customers are mentioned.

Return ONLY the JSON — no markdown, no explanation.
"""


def _build_reasoner_prompt(
    ctx: ClusterContext,
    correlation: CorrelationResult,
) -> str:
    """Assemble the user message for the LLM reasoning call."""
    # Sample ticket titles + bodies for the LLM
    ticket_lines = []
    for i, t in enumerate(ctx.ticket_samples[:20], 1):
        title = (t.get("title") or "").strip()
        body  = (t.get("body")  or "").strip()[:300]
        ticket_lines.append(f"  [{i}] {title}: {body}")

    # Keyword frequency analysis
    all_text = " ".join(
        (t.get("title", "") + " " + t.get("body", "")).lower()
        for t in ctx.ticket_samples
    )
    words = re.findall(r'\b[a-z]{4,}\b', all_text)
    top_keywords = [w for w, _ in Counter(words).most_common(15)
                    if w not in {"that", "this", "with", "from", "have", "when",
                                 "your", "been", "they", "their", "after", "will",
                                 "just", "then", "also", "about", "some"}]

    # Deploy info
    deploy_section = "No correlated deployment found."
    if correlation.best_deploy:
        d = correlation.best_deploy
        deploy_section = (
            f"Deployment ID: {d.id}\n"
            f"Version: {d.version}\n"
            f"Title: {d.title}\n"
            f"Deployed: {d.deployed_at}\n"
            f"Risk: {d.risk}\n"
            f"Notes: {d.notes or 'N/A'}\n"
            f"Correlation Score: {correlation.correlation_score:.2%}\n"
            f"Days before spike: {correlation.days_to_spike}"
        )

    return f"""
CLUSTER INFORMATION
===================
Cluster ID:         {ctx.cluster_id}
Title:              {ctx.title}
Summary:            {ctx.summary or 'N/A'}
Product Area:       {ctx.product_area or 'Unknown'}
Severity:           {ctx.severity}
Total Tickets:      {ctx.ticket_count}
Affected Customers: {ctx.affected_customers}
Monthly Cost (USD): ${ctx.monthly_cost_usd:,.2f}
First Seen:         {ctx.first_seen_at or 'Unknown'}
Last Seen:          {ctx.last_seen_at or 'Unknown'}

TOP KEYWORDS (frequency analysis)
===================================
{', '.join(top_keywords)}

SAMPLE TICKETS ({len(ctx.ticket_samples)} loaded)
================================================
{chr(10).join(ticket_lines) if ticket_lines else 'No ticket samples available.'}

DEPLOYMENT CORRELATION
======================
{deploy_section}

Produce the root-cause investigation JSON.
""".strip()


from services.llm import generate_investigation

async def _run_reasoner(
    ctx: ClusterContext,
    correlation: CorrelationResult,
) -> ReasonerOutput:
    """Dispatch to the Groq LLM backend."""
    logger.info(
        "reasoner_start",
        cluster_id = ctx.cluster_id,
        backend    = "groq",
        ticket_samples = len(ctx.ticket_samples),
    )

    try:
        raw = await generate_investigation(
            system_prompt=_REASONER_SYSTEM,
            user_prompt=_build_reasoner_prompt(ctx, correlation),
        )
        output = _parse_reasoner_output(raw, ctx)
    except Exception as exc:
        logger.error("reasoner_failed", error=str(exc), cluster_id=ctx.cluster_id)
        output = _fallback_reasoner_output(ctx)

    logger.info(
        "reasoner_complete",
        cluster_id  = ctx.cluster_id,
        confidence  = output.confidence,
        impact      = output.impact_level,
    )
    return output

def _parse_reasoner_output(raw: str, ctx: ClusterContext) -> ReasonerOutput:
    """
    Parse the LLM JSON response into a ReasonerOutput.
    Falls back to safe defaults on any parse failure.
    """
    # Strip markdown fences
    cleaned = re.sub(r"^```(?:json)?\s*|\s*```$", "", raw.strip(), flags=re.MULTILINE)

    try:
        data = json.loads(cleaned)
    except (json.JSONDecodeError, ValueError):
        logger.error("reasoner_parse_failed", raw=raw[:500], cluster_id=ctx.cluster_id)
        return _fallback_reasoner_output(ctx)

    # Coerce impact_level
    impact_raw = str(data.get("impact_level", ctx.severity)).lower().strip()
    valid_levels = {"critical", "high", "medium", "low"}
    impact_level = impact_raw if impact_raw in valid_levels else ctx.severity

    # Confidence clamped
    confidence = float(data.get("confidence", 70.0))
    confidence = max(0.0, min(100.0, confidence))

    # Revenue impact (floor at ticket_count × cost_per_ticket)
    floor_revenue = ctx.ticket_count * settings.REVENUE_COST_PER_TICKET_USD
    revenue_impact = max(
        float(data.get("revenue_impact", floor_revenue)),
        floor_revenue,
    )

    # Evidence items — validate types
    raw_evidence = data.get("evidence_items") or []
    evidence_items: list[dict] = []
    valid_types = {e.value for e in EvidenceType}
    for item in raw_evidence:
        ev_type = str(item.get("type", "ticket_pattern")).lower()
        if ev_type not in valid_types:
            ev_type = "ticket_pattern"
        weight = float(item.get("weight", 0.7))
        weight = max(0.0, min(1.0, weight))
        evidence_items.append({
            "type":   ev_type,
            "title":  str(item.get("title", "Evidence"))[:200],
            "detail": str(item.get("detail", ""))[:500] or None,
            "weight": weight,
        })

    # Simulation
    sim_before = int(data.get("sim_before_count") or ctx.ticket_count)
    deflection  = float(data.get("sim_deflection_pct") or 80.0)
    deflection  = max(0.0, min(100.0, deflection))
    sim_after   = int(data.get("sim_after_count")
                      or round(sim_before * (1 - deflection / 100)))

    return ReasonerOutput(
        root_cause         = str(data.get("root_cause", "Root cause could not be determined."))[:2000],
        confidence         = confidence,
        impact_level       = impact_level,
        revenue_impact     = revenue_impact,
        reasoning_steps    = [str(s) for s in (data.get("reasoning_steps") or [])],
        evidence_items     = evidence_items,
        sim_deflection_pct = deflection,
        sim_before_count   = sim_before,
        sim_after_count    = sim_after,
    )


def _fallback_reasoner_output(ctx: ClusterContext) -> ReasonerOutput:
    return ReasonerOutput(
        root_cause     = (
            f"A significant volume of tickets ({ctx.ticket_count}) report issues in the "
            f"{ctx.product_area or 'product'} area. Manual review required."
        ),
        confidence     = 55.0,
        impact_level   = ctx.severity,
        revenue_impact = ctx.ticket_count * settings.REVENUE_COST_PER_TICKET_USD,
        reasoning_steps = [
            f"{ctx.ticket_count} tickets grouped into a single semantic cluster.",
            f"{ctx.affected_customers} unique customers affected.",
            "LLM reasoning could not be completed — manual review recommended.",
        ],
        evidence_items = [
            {
                "type":   "ticket_pattern",
                "title":  f"{ctx.ticket_count} tickets in cluster",
                "detail": f"Cluster '{ctx.title}' with {ctx.affected_customers} affected customers.",
                "weight": 0.70,
            }
        ],
        sim_deflection_pct = 75.0,
        sim_before_count   = ctx.ticket_count,
        sim_after_count    = max(0, ctx.ticket_count - int(ctx.ticket_count * 0.75)),
    )





# ============================================================
# ④ Persist to Supabase
# ============================================================

async def _persist_investigation(
    ctx:         ClusterContext,
    output:      ReasonerOutput,
    correlation: CorrelationResult,
) -> str:
    """
    Upsert investigation row + evidence items.
    Returns the investigation ID.
    """
    sb             = await get_supabase()
    investigation_id = f"AI-{uuid.uuid4().hex[:6].upper()}"
    now            = datetime.now(timezone.utc).isoformat()

    # Simulation numbers
    sim_recovered = round(
        (output.sim_before_count - output.sim_after_count)
        * settings.REVENUE_COST_PER_TICKET_USD,
        2,
    )

    inv_row = {
        "id":                       investigation_id,
        "cluster_id":               ctx.cluster_id,
        "root_cause":               output.root_cause,
        "confidence":               round(output.confidence, 2),
        "impact_level":             output.impact_level,
        "affected_customers":       ctx.affected_customers,
        "revenue_impact_usd":       round(output.revenue_impact, 2),
        "deploy_correlation_id":    correlation.best_deploy.id if correlation.best_deploy else None,
        "deploy_correlation_score": round(correlation.correlation_score, 4) if correlation.best_deploy else None,
        "reasoning_steps":          output.reasoning_steps,
        "sim_before_ticket_count":  output.sim_before_count,
        "sim_after_ticket_count":   output.sim_after_count,
        "sim_deflection_pct":       round(output.sim_deflection_pct or 0.0, 2),
        "sim_recovered_usd":        sim_recovered,
        "model_version":            _MODEL_VERSION,
    }

    try:
        await sb.table("investigations").upsert(inv_row, on_conflict="id").execute()
        logger.info("investigation_persisted", investigation_id=investigation_id)
    except Exception as exc:
        logger.error("investigation_persist_failed", error=str(exc))
        raise

    # Evidence items
    evidence_rows = []
    for i, item in enumerate(output.evidence_items):
        evidence_rows.append({
            "id":               f"{investigation_id}-E{i+1}",
            "investigation_id": investigation_id,
            "evidence_type":    item["type"],
            "title":            item["title"],
            "detail":           item.get("detail"),
            "weight":           round(item["weight"], 4),
            "sort_order":       i,
        })

    if evidence_rows:
        try:
            await (
                sb.table("investigation_evidence")
                .upsert(evidence_rows, on_conflict="id")
                .execute()
            )
            logger.info("evidence_persisted", count=len(evidence_rows))
        except Exception as exc:
            logger.warning("evidence_persist_failed", error=str(exc))
            # Non-fatal — investigation still valid without evidence rows

    return investigation_id


# ============================================================
# ⑤ Check for recent investigation (cache guard)
# ============================================================

async def _fetch_existing_investigation(
    cluster_id:           str,
    confidence_threshold: float,
) -> InvestigationOut | None:
    """
    Return a recent investigation if one exists above the confidence threshold.
    "Recent" = created within the last 7 days.
    """
    sb      = await get_supabase()
    cutoff  = (datetime.now(timezone.utc) - timedelta(days=7)).isoformat()

    resp = (
        await sb.table("investigations")
        .select("*")
        .eq("cluster_id", cluster_id)
        .gte("confidence", confidence_threshold * 100)
        .gte("created_at", cutoff)
        .order("created_at", desc=True)
        .limit(1)
        .execute()
    )

    rows = resp.data or []
    if not rows:
        return None

    row = rows[0]
    # Fetch associated evidence
    ev_resp = (
        await sb.table("investigation_evidence")
        .select("*")
        .eq("investigation_id", row["id"])
        .order("sort_order")
        .execute()
    )
    evidence_rows = ev_resp.data or []

    logger.info(
        "cached_investigation_found",
        investigation_id = row["id"],
        confidence       = row.get("confidence"),
    )
    return _row_to_investigation_out(row, evidence_rows)


# ============================================================
# ⑥ Serialisation helpers
# ============================================================

def _row_to_investigation_out(
    row: dict,
    evidence_rows: list[dict],
) -> InvestigationOut:
    """Convert raw Supabase rows into an InvestigationOut API model."""
    now = datetime.now(timezone.utc)

    # Deploy correlation
    deploy_correlation: DeployCorrelation | None = None
    if row.get("deploy_correlation_id"):
        deploy_correlation = DeployCorrelation(
            deploy_id   = row["deploy_correlation_id"],
            version     = row.get("_deploy_version", ""),
            deployed_at = row.get("_deploy_deployed_at", ""),
            title       = row.get("_deploy_title", ""),
            correlation = float(row.get("deploy_correlation_score") or 0.0),
        )

    # Evidence
    evidence: list[EvidenceOut] = []
    for i, ev in enumerate(evidence_rows):
        try:
            evidence.append(
                EvidenceOut(
                    id            = ev.get("id", f"E{i}"),
                    evidence_type = ev.get("evidence_type", "ticket_pattern"),
                    title         = ev.get("title", ""),
                    detail        = ev.get("detail"),
                    weight        = float(ev.get("weight", 0.7)),
                    sort_order    = int(ev.get("sort_order", i)),
                )
            )
        except Exception:
            pass

    # Simulation
    simulation: SimulationResult | None = None
    if row.get("sim_before_ticket_count") is not None:
        simulation = SimulationResult(
            before_ticket_count = int(row["sim_before_ticket_count"]),
            after_ticket_count  = int(row.get("sim_after_ticket_count") or 0),
            deflection_pct      = float(row.get("sim_deflection_pct") or 0.0),
            recovered_usd       = float(row.get("sim_recovered_usd") or 0.0),
        )

    def _parse_dt(v: str | None) -> datetime:
        if not v:
            return now
        try:
            return datetime.fromisoformat(v.replace("Z", "+00:00"))
        except (ValueError, AttributeError):
            return now

    return InvestigationOut(
        id                 = row["id"],
        cluster_id         = row["cluster_id"],
        root_cause         = row.get("root_cause", ""),
        confidence         = float(row.get("confidence") or 0.0),
        impact_level       = SeverityLevel(row.get("impact_level", "medium")),
        affected_customers = int(row.get("affected_customers") or 0),
        revenue_impact_usd = float(row.get("revenue_impact_usd") or 0.0),
        deploy_correlation = deploy_correlation,
        reasoning_steps    = row.get("reasoning_steps") or [],
        evidence           = evidence,
        simulation         = simulation,
        model_version      = row.get("model_version", _MODEL_VERSION),
        created_by         = row.get("created_by"),
        approved_by        = row.get("approved_by"),
        approved_at        = _parse_dt(row.get("approved_at")) if row.get("approved_at") else None,
        created_at         = _parse_dt(row.get("created_at")),
        updated_at         = _parse_dt(row.get("updated_at")),
    )


def _build_investigation_out(
    investigation_id: str,
    ctx:              ClusterContext,
    output:           ReasonerOutput,
    correlation:      CorrelationResult,
) -> InvestigationOut:
    """Build InvestigationOut directly from in-memory objects (no second DB read)."""
    now = datetime.now(timezone.utc)

    deploy_corr: DeployCorrelation | None = None
    if correlation.best_deploy:
        d = correlation.best_deploy
        deploy_corr = DeployCorrelation(
            deploy_id   = d.id,
            version     = d.version,
            deployed_at = d.deployed_at,
            title       = d.title,
            correlation = correlation.correlation_score,
        )

    evidence: list[EvidenceOut] = [
        EvidenceOut(
            id            = f"{investigation_id}-E{i+1}",
            evidence_type = EvidenceType(item["type"]),
            title         = item["title"],
            detail        = item.get("detail"),
            weight        = item["weight"],
            sort_order    = i,
        )
        for i, item in enumerate(output.evidence_items)
    ]

    sim_recovered = round(
        (output.sim_before_count - output.sim_after_count)
        * settings.REVENUE_COST_PER_TICKET_USD,
        2,
    )
    simulation = SimulationResult(
        before_ticket_count = output.sim_before_count or ctx.ticket_count,
        after_ticket_count  = output.sim_after_count or 0,
        deflection_pct      = output.sim_deflection_pct or 0.0,
        recovered_usd       = max(0.0, sim_recovered),
    )

    return InvestigationOut(
        id                 = investigation_id,
        cluster_id         = ctx.cluster_id,
        root_cause         = output.root_cause,
        confidence         = output.confidence,
        impact_level       = SeverityLevel(output.impact_level),
        affected_customers = ctx.affected_customers,
        revenue_impact_usd = output.revenue_impact,
        deploy_correlation = deploy_corr,
        reasoning_steps    = output.reasoning_steps,
        evidence           = evidence,
        simulation         = simulation,
        model_version      = _MODEL_VERSION,
        created_by         = None,
        approved_by        = None,
        approved_at        = None,
        created_at         = now,
        updated_at         = now,
    )


# ============================================================
# Public entry point
# ============================================================

async def run_investigation(request: InvestigateRequest) -> InvestigationOut:
    """
    Run the full root-cause investigation pipeline for a cluster.

    Steps:
        ① Load cluster context + ticket samples
        ② Load recent deployments from Supabase
        ③ Correlate deployments against the ticket-volume spike onset
        ④ Call LLM reasoning chain (GPT-4o or Gemini)
        ⑤ Persist investigation + evidence rows
        ⑥ Return InvestigationOut

    Args:
        request: InvestigateRequest with cluster_id and tuning params.

    Returns:
        InvestigationOut — the full investigation report.

    Raises:
        ValueError  — cluster not found.
        RuntimeError — LLM or DB error that could not be recovered.
    """
    log = logger.bind(
        cluster_id         = request.cluster_id,
        force_refresh      = request.force_refresh,
        confidence_threshold = request.confidence_threshold,
        window_days        = request.deploy_correlation_days,
    )
    log.info("investigation_start")

    # ── Cache guard ────────────────────────────────────────────────
    if not request.force_refresh:
        cached = await _fetch_existing_investigation(
            cluster_id           = request.cluster_id,
            confidence_threshold = request.confidence_threshold,
        )
        if cached:
            log.info("investigation_cache_hit", investigation_id=cached.id)
            return cached

    # ① Load cluster context
    ctx = await _load_cluster_context(request.cluster_id)
    if ctx is None:
        raise ValueError(f"Cluster '{request.cluster_id}' not found.")

    log.info(
        "cluster_loaded",
        ticket_count       = ctx.ticket_count,
        ticket_samples     = len(ctx.ticket_samples),
        affected_customers = ctx.affected_customers,
    )

    # ② Load deployments
    deployments = await _load_deployments(request.deploy_correlation_days)
    log.info("deployments_loaded", count=len(deployments))

    # ③ Deploy correlation
    correlation = await detect_deploy_correlation(ctx, deployments, request.deploy_correlation_days)

    # ④ LLM reasoning
    output = await _run_reasoner(ctx, correlation)

    # ⑤ Persist
    investigation_id = await _persist_investigation(ctx, output, correlation)

    # ⑥ Return
    result = _build_investigation_out(investigation_id, ctx, output, correlation)
    log.info(
        "investigation_complete",
        investigation_id   = investigation_id,
        confidence         = result.confidence,
        revenue_impact_usd = result.revenue_impact_usd,
    )
    return result


# Backward-compat wrappers
async def score_evidence(
    cluster_id: str,
    investigation_id: str,
    reasoning: list[str],
) -> list[dict]:
    """Deprecated stub — evidence scoring is now embedded inside run_investigation()."""
    raise NotImplementedError(
        "score_evidence() is deprecated. Use run_investigation() instead."
    )
