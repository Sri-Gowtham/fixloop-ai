"""
api/investigate.py
------------------
POST /ai/investigate           — Run root-cause investigation on a cluster
GET  /ai/investigate/{id}      — Fetch a completed investigation report
GET  /ai/investigate/cluster/{cluster_id}  — List investigations for a cluster

Response shape (InvestigationOut):
    {
        "id":                  "AI-xxxxxx",
        "cluster_id":          "CL-xxxxxx",
        "root_cause":          "...",
        "confidence":          94.0,
        "impact_level":        "high",
        "affected_customers":  487,
        "revenue_impact_usd":  34000.0,
        "deploy_correlation":  { deploy_id, version, deployed_at, correlation },
        "reasoning_steps":     [ "...", "..." ],
        "evidence":            [ { id, evidence_type, title, detail, weight } ],
        "simulation":          { before_ticket_count, after_ticket_count,
                                 deflection_pct, recovered_usd },
        "model_version":       "fixloop-reasoner-v3",
        "created_at":          "...",
        "updated_at":          "..."
    }
"""

from __future__ import annotations

import structlog
from fastapi import APIRouter, HTTPException, Query, status

from agents.investigate_agent import InvestigateAgent
from models.investigation import InvestigateRequest, InvestigationOut
from services.investigation import _fetch_existing_investigation, _row_to_investigation_out
from services.supabase_client import get_supabase

logger = structlog.get_logger(__name__)
router = APIRouter()


# ============================================================
# POST /ai/investigate
# ============================================================

@router.post(
    "/investigate",
    response_model=InvestigationOut,
    status_code=status.HTTP_200_OK,
    summary="Run AI root-cause investigation",
    description=(
        "Runs the FixLoop Reasoner pipeline on a ticket cluster. "
        "Loads cluster tickets, correlates against recent deployments, "
        "generates a root-cause report via LLM, and persists the result. "
        "Returns a cached result if a recent high-confidence investigation exists "
        "(override with force_refresh=true)."
    ),
    responses={
        200: {"description": "Investigation report returned"},
        404: {"description": "Cluster not found"},
        400: {"description": "Invalid request parameters"},
        500: {"description": "Investigation pipeline error"},
    },
)
async def investigate(
    request: InvestigateRequest,
    # user: dict = Depends(get_current_user),  # Enable when auth is wired
) -> InvestigationOut:
    """
    Root-cause investigation endpoint.

    - Results are cached for 7 days at the configured confidence threshold.
    - Set `force_refresh=true` to bypass the cache and re-run.
    - `deploy_correlation_days` controls how far back to search for
       correlated deployments (default: 7 days).
    """
    logger.info(
        "investigate_request",
        cluster_id           = request.cluster_id,
        force_refresh        = request.force_refresh,
        confidence_threshold = request.confidence_threshold,
    )

    agent = InvestigateAgent()

    try:
        result = await agent(request)
    except ValueError as exc:
        # Cluster not found
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        )
    except Exception as exc:
        logger.exception("investigate_unhandled_error", error=str(exc))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Investigation pipeline error: {exc}",
        )

    if not result.success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=result.error or "Investigation failed.",
        )

    return result.output  # type: ignore[return-value]


# ============================================================
# GET /ai/investigate/{investigation_id}
# ============================================================

@router.get(
    "/investigate/{investigation_id}",
    response_model=InvestigationOut,
    status_code=status.HTTP_200_OK,
    summary="Get investigation by ID",
    description="Fetch a previously completed AI investigation report by its ID.",
    responses={
        200: {"description": "Investigation found"},
        404: {"description": "Investigation not found"},
        500: {"description": "Database error"},
    },
)
async def get_investigation(
    investigation_id: str,
    # user: dict = Depends(get_current_user),
) -> InvestigationOut:
    """Fetch a single investigation report from the database."""
    logger.info("get_investigation_request", investigation_id=investigation_id)
    sb = await get_supabase()

    # Fetch investigation row
    try:
        inv_resp = (
            await sb.table("investigations")
            .select("*")
            .eq("id", investigation_id)
            .single()
            .execute()
        )
    except Exception as exc:
        logger.exception("get_investigation_db_error", error=str(exc))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database error: {exc}",
        )

    row = inv_resp.data
    if not row:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Investigation '{investigation_id}' not found.",
        )

    # Fetch associated evidence
    ev_resp = (
        await sb.table("investigation_evidence")
        .select("*")
        .eq("investigation_id", investigation_id)
        .order("sort_order")
        .execute()
    )
    evidence_rows = ev_resp.data or []

    # Enrich deploy correlation with version/date
    if row.get("deploy_correlation_id"):
        try:
            deploy_resp = (
                await sb.table("deployments")
                .select("id, version, title, deployed_at")
                .eq("id", row["deploy_correlation_id"])
                .single()
                .execute()
            )
            deploy_data = deploy_resp.data or {}
            # Merge into row so _row_to_investigation_out can use it
            row["_deploy_version"]     = deploy_data.get("version", "")
            row["_deploy_title"]       = deploy_data.get("title", "")
            row["_deploy_deployed_at"] = deploy_data.get("deployed_at", "")
        except Exception:
            pass

    return _row_to_investigation_out(row, evidence_rows)


# ============================================================
# GET /ai/investigate/cluster/{cluster_id}
# ============================================================

@router.get(
    "/investigate/cluster/{cluster_id}",
    response_model=list[InvestigationOut],
    status_code=status.HTTP_200_OK,
    summary="List investigations for a cluster",
    description="Return all investigation reports for a given cluster, newest first.",
    responses={
        200: {"description": "Investigation list returned"},
        500: {"description": "Database error"},
    },
)
async def list_cluster_investigations(
    cluster_id: str,
    limit:      int = Query(10, ge=1, le=50, description="Max investigations to return"),
    # user: dict = Depends(get_current_user),
) -> list[InvestigationOut]:
    """Return all investigation reports for a cluster, ordered by created_at desc."""
    logger.info("list_investigations_request", cluster_id=cluster_id)
    sb = await get_supabase()

    try:
        resp = (
            await sb.table("investigations")
            .select("*")
            .eq("cluster_id", cluster_id)
            .order("created_at", desc=True)
            .limit(limit)
            .execute()
        )
    except Exception as exc:
        logger.exception("list_investigations_db_error", error=str(exc))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database error: {exc}",
        )

    rows = resp.data or []
    results: list[InvestigationOut] = []

    for row in rows:
        try:
            ev_resp = (
                await sb.table("investigation_evidence")
                .select("*")
                .eq("investigation_id", row["id"])
                .order("sort_order")
                .execute()
            )
            results.append(_row_to_investigation_out(row, ev_resp.data or []))
        except Exception as exc:
            logger.warning(
                "investigation_row_parse_failed",
                investigation_id=row.get("id"),
                error=str(exc),
            )

    return results
