"""
api/copilot.py
--------------
POST /ai/copilot — FixLoop Copilot conversational endpoint.

Loads cluster context (cluster details, investigation, deployment
correlation, recommendation) and calls Groq to answer questions
scoped to incident analysis only.

Request:
    { "cluster_id": str, "message": str }

Response:
    { "reply": str, "cluster_id": str }
"""

from __future__ import annotations

import structlog
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel

from core.config import settings
from services.supabase_client import get_supabase

logger = structlog.get_logger(__name__)
router = APIRouter()

# ---------------------------------------------------------------------------
# Request / Response models
# ---------------------------------------------------------------------------

class CopilotRequest(BaseModel):
    cluster_id: str
    message: str

class CopilotResponse(BaseModel):
    reply: str
    cluster_id: str

# ---------------------------------------------------------------------------
# System prompt — scoped exclusively to incident analysis topics
# ---------------------------------------------------------------------------

SYSTEM_PROMPT = """You are FixLoop Copilot, an AI assistant embedded inside FixLoop AI — an intelligent incident-management platform.

You have been given structured context about a specific ticket cluster, its root-cause investigation, deployment correlation, and engineering recommendations.

You MUST only answer questions about:
- Root cause analysis
- Deployment correlation
- Ticket impact (volume, trend, product area)
- Customer impact
- Revenue impact
- Engineering recommendations
- Executive summaries
- Jira ticket generation
- Postmortem summaries

If the user asks anything outside these topics, politely decline and redirect them to the incident data.

Always base your answer on the context provided. Be concise, direct, and technical. Use Markdown formatting when helpful."""

# ---------------------------------------------------------------------------
# Data loaders
# ---------------------------------------------------------------------------

async def _load_cluster(sb, cluster_id: str) -> dict:
    try:
        resp = (
            await sb.table("ticket_clusters")
            .select("*")
            .eq("id", cluster_id)
            .single()
            .execute()
        )
        return resp.data or {}
    except Exception:
        return {}


async def _load_investigation(sb, cluster_id: str) -> dict:
    try:
        resp = (
            await sb.table("investigations")
            .select("*")
            .eq("cluster_id", cluster_id)
            .order("created_at", desc=True)
            .limit(1)
            .execute()
        )
        rows = resp.data or []
        return rows[0] if rows else {}
    except Exception:
        return {}


async def _load_deployment(sb, deploy_id: str) -> dict:
    if not deploy_id:
        return {}
    try:
        resp = (
            await sb.table("deployments")
            .select("id, version, title, deployed_at, environment, status")
            .eq("id", deploy_id)
            .single()
            .execute()
        )
        return resp.data or {}
    except Exception:
        return {}


async def _load_recommendation(sb, investigation_id: str) -> dict:
    if not investigation_id:
        return {}
    try:
        resp = (
            await sb.table("fix_recommendations")
            .select("*")
            .eq("investigation_id", investigation_id)
            .order("created_at", desc=True)
            .limit(1)
            .execute()
        )
        rows = resp.data or []
        return rows[0] if rows else {}
    except Exception:
        return {}

# ---------------------------------------------------------------------------
# Prompt builder
# ---------------------------------------------------------------------------

def _build_context_prompt(cluster: dict, investigation: dict, deployment: dict, recommendation: dict) -> str:
    lines: list[str] = ["## Cluster Context\n"]

    if cluster:
        lines += [
            f"- **ID**: {cluster.get('id', 'N/A')}",
            f"- **Title**: {cluster.get('title', 'N/A')}",
            f"- **Summary**: {cluster.get('summary', 'N/A')}",
            f"- **Severity**: {cluster.get('severity', 'N/A')}",
            f"- **Status**: {cluster.get('status', 'N/A')}",
            f"- **Ticket count**: {cluster.get('ticket_count', 0)}",
            f"- **Affected customers**: {cluster.get('affected_customers', 0)}",
            f"- **Monthly cost (USD)**: ${cluster.get('monthly_cost_usd', 0):.0f}",
            f"- **Product area**: {cluster.get('product_area', 'N/A')}",
            f"- **Root cause (cluster)**: {cluster.get('root_cause', 'N/A')}",
        ]
    else:
        lines.append("- No cluster data found.")

    lines.append("\n## Investigation\n")
    if investigation:
        lines += [
            f"- **Root cause**: {investigation.get('root_cause', 'N/A')}",
            f"- **Impact level**: {investigation.get('impact_level', 'N/A')}",
            f"- **Confidence**: {investigation.get('confidence', 0):.1f}%",
            f"- **Affected customers**: {investigation.get('affected_customers', 0)}",
            f"- **Revenue impact (USD/mo)**: ${investigation.get('revenue_impact_usd', 0):.0f}",
            f"- **Reasoning**: {'; '.join(investigation.get('reasoning_steps') or [])}",
        ]
    else:
        lines.append("- No investigation found for this cluster.")

    lines.append("\n## Deployment Correlation\n")
    if deployment:
        lines += [
            f"- **Deploy ID**: {deployment.get('id', 'N/A')}",
            f"- **Version**: {deployment.get('version', 'N/A')}",
            f"- **Title**: {deployment.get('title', 'N/A')}",
            f"- **Deployed at**: {deployment.get('deployed_at', 'N/A')}",
            f"- **Environment**: {deployment.get('environment', 'N/A')}",
            f"- **Status**: {deployment.get('status', 'N/A')}",
        ]
    else:
        lines.append("- No correlated deployment found.")

    lines.append("\n## Engineering Recommendation\n")
    if recommendation:
        lines += [
            f"- **Title**: {recommendation.get('title', 'N/A')}",
            f"- **Priority**: {recommendation.get('priority', 'N/A')}",
            f"- **Effort**: {recommendation.get('effort_estimate', 'N/A')}",
            f"- **Expected deflection**: {recommendation.get('expected_deflection_pct', 0):.0f}%",
            f"- **Revenue recovery**: ${recommendation.get('revenue_recovery_usd', 0):.0f}/mo",
            f"- **Steps**: {'; '.join(recommendation.get('implementation_steps') or [])}",
        ]
    else:
        lines.append("- No recommendation generated yet.")

    return "\n".join(lines)

# ---------------------------------------------------------------------------
# Endpoint
# ---------------------------------------------------------------------------

@router.post(
    "/copilot",
    response_model=CopilotResponse,
    status_code=status.HTTP_200_OK,
    summary="FixLoop Copilot — conversational incident assistant",
    description=(
        "Loads cluster, investigation, deployment, and recommendation context, "
        "then calls Groq to answer incident-scoped questions."
    ),
)
async def copilot(request: CopilotRequest) -> CopilotResponse:
    logger.info("copilot_request", cluster_id=request.cluster_id, message=request.message[:120])

    if not request.message.strip():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="message must not be empty.")

    if not settings.GROQ_API_KEY:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="GROQ_API_KEY not configured.")

    sb = await get_supabase()

    # Load context
    cluster      = await _load_cluster(sb, request.cluster_id)
    investigation = await _load_investigation(sb, request.cluster_id)
    deploy_id    = investigation.get("deploy_correlation_id") or cluster.get("related_deploy_id") or ""
    deployment   = await _load_deployment(sb, deploy_id)
    rec          = await _load_recommendation(sb, investigation.get("id", ""))

    context_prompt = _build_context_prompt(cluster, investigation, deployment, rec)

    user_content = f"{context_prompt}\n\n---\n\n**User question:** {request.message}"

    # Call Groq
    from groq import AsyncGroq
    client = AsyncGroq(api_key=settings.GROQ_API_KEY)

    try:
        completion = await client.chat.completions.create(
            model=settings.GROQ_MODEL,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user",   "content": user_content},
            ],
            temperature=0.3,
            max_tokens=1024,
        )
        reply = completion.choices[0].message.content or "I could not generate a response."
    except Exception as exc:
        logger.exception("copilot_groq_error", error=str(exc))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"LLM error: {exc}",
        )

    logger.info("copilot_response_ok", cluster_id=request.cluster_id, reply_len=len(reply))
    return CopilotResponse(reply=reply, cluster_id=request.cluster_id)
