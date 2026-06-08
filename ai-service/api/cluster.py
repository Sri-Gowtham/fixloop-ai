"""
api/cluster.py
--------------
POST /ai/cluster   — Run semantic clustering on embedded tickets
GET  /ai/cluster   — List all clusters (paginated)
GET  /ai/cluster/{cluster_id}  — Get single cluster detail

Response shape for POST /ai/cluster:
    {
        "cluster_count":      <int>,
        "clustered_tickets":  <int>,
        "noise_tickets":      <int>,
        "clusters":           [ClusterOut, ...]
    }
"""

from __future__ import annotations

import structlog
from fastapi import APIRouter, HTTPException, Query, status

from agents.cluster_agent import ClusterAgent
from models.cluster import ClusterOut, ClusterRequest, ClusteringResult
from services.supabase_client import get_supabase

logger = structlog.get_logger(__name__)
router = APIRouter()


# ============================================================
# POST /ai/cluster
# ============================================================

@router.post(
    "/cluster",
    response_model=ClusteringResult,
    status_code=status.HTTP_200_OK,
    summary="Run semantic clustering",
    description=(
        "Reads unclustered embedded tickets from Supabase, groups them "
        "with HDBSCAN, labels each cluster using GPT-4o or Gemini, "
        "and persists the results to public.ticket_clusters. "
        "Returns the number of clusters created and clustered tickets."
    ),
    responses={
        200: {"description": "Clustering complete — ClusteringResult returned"},
        400: {"description": "Invalid request parameters"},
        500: {"description": "Clustering pipeline error"},
    },
)
async def cluster(
    request: ClusterRequest,
    # user: dict = Depends(get_current_user),  # Enable when auth is wired
) -> ClusteringResult:
    """
    Run the full semantic clustering pipeline.

    - If `ticket_ids` is provided, clusters only those tickets.
    - If `process_all=true`, re-clusters ALL embedded tickets.
    - If `dry_run=true`, runs HDBSCAN + LLM labelling without DB writes.
    """
    logger.info(
        "cluster_request",
        process_all = request.process_all,
        dry_run     = request.dry_run,
        ticket_ids  = len(request.ticket_ids) if request.ticket_ids else "all",
    )

    agent = ClusterAgent()

    try:
        result = await agent(request)
    except Exception as exc:
        logger.exception("cluster_agent_unhandled_error", error=str(exc))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Clustering pipeline error: {exc}",
        )

    if not result.success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=result.error or "Clustering failed.",
        )

    return result.output  # type: ignore[return-value]


# ============================================================
# GET /ai/cluster
# ============================================================

@router.get(
    "/cluster",
    response_model=list[ClusterOut],
    status_code=status.HTTP_200_OK,
    summary="List all clusters",
    description="Return a paginated list of ticket clusters ordered by monthly cost.",
    responses={
        200: {"description": "Cluster list returned"},
        500: {"description": "Database error"},
    },
)
async def list_clusters(
    page:     int = Query(1,  ge=1,   description="Page number (1-based)"),
    size:     int = Query(20, ge=1, le=100, description="Page size"),
    severity: str = Query(None,       description="Filter by severity: critical|high|medium|low"),
    status_f: str = Query(None, alias="status", description="Filter by status: open|in_progress|resolved"),
    # user: dict = Depends(get_current_user),
) -> list[ClusterOut]:
    """
    List clusters from public.ticket_clusters, ordered by monthly_cost_usd desc.
    """
    sb     = await get_supabase()
    offset = (page - 1) * size

    query = (
        sb.table("ticket_clusters")
        .select("*")
        .order("monthly_cost_usd", desc=True)
        .range(offset, offset + size - 1)
    )

    if severity:
        query = query.eq("severity", severity)
    if status_f:
        query = query.eq("status", status_f)

    try:
        resp = await query.execute()
    except Exception as exc:
        logger.exception("list_clusters_db_error", error=str(exc))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database error: {exc}",
        )

    rows   = resp.data or []
    now    = __import__("datetime").datetime.now(__import__("datetime").timezone.utc)

    clusters = []
    for row in rows:
        try:
            clusters.append(
                ClusterOut(
                    id                 = row["id"],
                    title              = row.get("title", ""),
                    summary            = row.get("summary"),
                    severity           = row.get("severity", "medium"),
                    status             = row.get("status", "open"),
                    ticket_count       = row.get("ticket_count", 0),
                    affected_customers = row.get("affected_customers", 0),
                    monthly_cost_usd   = float(row.get("monthly_cost_usd", 0)),
                    confidence         = float(row["confidence"]) if row.get("confidence") else None,
                    product_area       = row.get("product_area"),
                    related_deploy_id  = row.get("related_deploy_id"),
                    first_seen_at      = row.get("first_seen_at"),
                    last_seen_at       = row.get("last_seen_at"),
                    root_cause         = row.get("root_cause"),
                    ticket_trend       = row.get("ticket_trend") or [],
                    example_titles     = row.get("example_titles") or [],
                    created_by         = row.get("created_by"),
                    created_at         = row.get("created_at") or now,
                    updated_at         = row.get("updated_at") or now,
                )
            )
        except Exception as exc:
            logger.warning("cluster_row_parse_failed", cluster_id=row.get("id"), error=str(exc))

    return clusters


# ============================================================
# GET /ai/cluster/{cluster_id}
# ============================================================

@router.get(
    "/cluster/{cluster_id}",
    response_model=ClusterOut,
    status_code=status.HTTP_200_OK,
    summary="Get cluster by ID",
    description="Fetch the full detail of a single ticket cluster.",
    responses={
        200: {"description": "Cluster found"},
        404: {"description": "Cluster not found"},
    },
)
async def get_cluster(
    cluster_id: str,
    # user: dict = Depends(get_current_user),
) -> ClusterOut:
    sb = await get_supabase()

    try:
        resp = (
            await sb.table("ticket_clusters")
            .select("*")
            .eq("id", cluster_id)
            .single()
            .execute()
        )
    except Exception as exc:
        logger.exception("get_cluster_db_error", cluster_id=cluster_id, error=str(exc))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database error: {exc}",
        )

    row = resp.data
    if not row:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Cluster '{cluster_id}' not found.",
        )

    now = __import__("datetime").datetime.now(__import__("datetime").timezone.utc)
    return ClusterOut(
        id                 = row["id"],
        title              = row.get("title", ""),
        summary            = row.get("summary"),
        severity           = row.get("severity", "medium"),
        status             = row.get("status", "open"),
        ticket_count       = row.get("ticket_count", 0),
        affected_customers = row.get("affected_customers", 0),
        monthly_cost_usd   = float(row.get("monthly_cost_usd", 0)),
        confidence         = float(row["confidence"]) if row.get("confidence") else None,
        product_area       = row.get("product_area"),
        related_deploy_id  = row.get("related_deploy_id"),
        first_seen_at      = row.get("first_seen_at"),
        last_seen_at       = row.get("last_seen_at"),
        root_cause         = row.get("root_cause"),
        ticket_trend       = row.get("ticket_trend") or [],
        example_titles     = row.get("example_titles") or [],
        created_by         = row.get("created_by"),
        created_at         = row.get("created_at") or now,
        updated_at         = row.get("updated_at") or now,
    )
