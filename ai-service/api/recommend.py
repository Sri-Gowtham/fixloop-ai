"""
api/recommend.py
----------------
POST /ai/recommend                                — Generate AI fix recommendation
GET  /ai/recommend/{recommendation_id}            — Fetch recommendation by ID
GET  /ai/recommend/investigation/{investigation_id} — List recommendations for an investigation

Generates actionable engineering recommendations from AI investigations,
including priority, effort estimate, expected ticket reduction,
revenue recovery, and Jira-style ticket content.
"""

from __future__ import annotations

import structlog
from fastapi import APIRouter, HTTPException, Query, status

from agents.recommend_agent import RecommendAgent
from models.recommendation import RecommendRequest, RecommendationOut
from services.recommendation import _row_to_recommendation_out
from services.supabase_client import get_supabase

logger = structlog.get_logger(__name__)
router = APIRouter()


# ----------------------------------------------------------------
# Endpoint: POST /ai/recommend
# ----------------------------------------------------------------

@router.post(
    "/recommend",
    response_model=RecommendationOut,
    status_code=status.HTTP_201_CREATED,
    summary="Generate AI fix recommendation",
    description=(
        "Uses GPT-4o / Gemini to synthesise an actionable fix plan from an AI "
        "investigation. Persists the recommendation to public.fix_recommendations "
        "and returns the full RecommendationOut including expected deflection, "
        "revenue recovery, priority, effort estimate, and Jira ticket content."
    ),
    responses={
        201: {"description": "Recommendation created successfully"},
        400: {"description": "Invalid investigation_id or cluster_id"},
        404: {"description": "Investigation or cluster not found"},
        500: {"description": "LLM synthesis error"},
    },
)
async def recommend(
    request: RecommendRequest,
    # user: dict = Depends(get_current_user),
) -> RecommendationOut:
    """Generate and persist a fix recommendation from an investigation."""
    logger.info(
        "recommend_request",
        investigation_id = request.investigation_id,
        cluster_id       = request.cluster_id,
        owner_user_id    = str(request.owner_user_id) if request.owner_user_id else None,
        force_refresh    = request.force_refresh,
    )

    agent = RecommendAgent()

    try:
        agent_result = await agent(request)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        )
    except Exception as exc:
        logger.exception("recommend_unhandled_error", error=str(exc))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Recommendation pipeline error: {exc}",
        )

    if not agent_result.success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=agent_result.error or "Recommendation generation failed.",
        )

    return agent_result.output  # type: ignore[return-value]


# ----------------------------------------------------------------
# Endpoint: GET /ai/recommend/{recommendation_id}
# ----------------------------------------------------------------

@router.get(
    "/recommend/{recommendation_id}",
    response_model=RecommendationOut,
    status_code=status.HTTP_200_OK,
    summary="Get fix recommendation by ID",
    description="Fetch a previously generated fix recommendation.",
    responses={
        200: {"description": "Recommendation found"},
        404: {"description": "Recommendation not found"},
        500: {"description": "Database error"},
    },
)
async def get_recommendation(
    recommendation_id: str,
    # user: dict = Depends(get_current_user),
) -> RecommendationOut:
    """Fetch a single recommendation from the database."""
    logger.info("get_recommendation_request", recommendation_id=recommendation_id)
    sb = await get_supabase()

    try:
        resp = (
            await sb.table("fix_recommendations")
            .select("*")
            .eq("id", recommendation_id)
            .single()
            .execute()
        )
    except Exception as exc:
        logger.exception("get_recommendation_db_error", error=str(exc))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database error: {exc}",
        )

    row = resp.data
    if not row:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Recommendation '{recommendation_id}' not found.",
        )

    return _row_to_recommendation_out(row)


# ----------------------------------------------------------------
# Endpoint: GET /ai/recommend/investigation/{investigation_id}
# ----------------------------------------------------------------

@router.get(
    "/recommend/investigation/{investigation_id}",
    response_model=list[RecommendationOut],
    status_code=status.HTTP_200_OK,
    summary="List recommendations for an investigation",
    description="Return all fix recommendations for a given investigation, newest first.",
    responses={
        200: {"description": "Recommendation list returned"},
        500: {"description": "Database error"},
    },
)
async def list_investigation_recommendations(
    investigation_id: str,
    limit: int = Query(10, ge=1, le=50, description="Max recommendations to return"),
    # user: dict = Depends(get_current_user),
) -> list[RecommendationOut]:
    """Return all recommendations for an investigation, ordered by created_at desc."""
    logger.info(
        "list_recommendations_request",
        investigation_id=investigation_id,
    )
    sb = await get_supabase()

    try:
        resp = (
            await sb.table("fix_recommendations")
            .select("*")
            .eq("investigation_id", investigation_id)
            .order("created_at", desc=True)
            .limit(limit)
            .execute()
        )
    except Exception as exc:
        logger.exception("list_recommendations_db_error", error=str(exc))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database error: {exc}",
        )

    rows = resp.data or []
    results: list[RecommendationOut] = []

    for row in rows:
        try:
            results.append(_row_to_recommendation_out(row))
        except Exception as exc:
            logger.warning(
                "recommendation_row_parse_failed",
                recommendation_id=row.get("id"),
                error=str(exc),
            )

    return results
