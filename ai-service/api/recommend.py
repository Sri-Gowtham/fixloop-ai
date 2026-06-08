"""
api/recommend.py
----------------
POST /ai/recommend

Generates an AI fix recommendation from an existing investigation.

Endpoint contract:
    POST /ai/recommend
    Content-Type: application/json

    Request:
        RecommendRequest

    Response 201:
        RecommendationOut
"""

from __future__ import annotations

structlog_import = True
import structlog
from fastapi import APIRouter, HTTPException, status

from agents.recommend_agent import RecommendAgent
from models.recommendation import RecommendRequest, RecommendationOut
from api.deps import get_current_user

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
        "Uses GPT-4o to synthesise an actionable fix plan from an AI investigation. "
        "Persists the recommendation to public.fix_recommendations and returns "
        "the full RecommendationOut including expected deflection and revenue recovery."
    ),
    responses={
        201: {"description": "Recommendation created successfully"},
        400: {"description": "Invalid investigation_id or cluster_id"},
        401: {"description": "Missing or invalid Bearer token"},
        404: {"description": "Investigation or cluster not found"},
        500: {"description": "LLM synthesis error"},
    },
)
async def recommend(
    request: RecommendRequest,
    # user: dict = Depends(get_current_user),  # TODO: enable auth
) -> RecommendationOut:
    """
    Generate and persist a fix recommendation.

    TODO:
        1. Validate investigation_id and cluster_id exist
        2. Instantiate RecommendAgent and call agent(request)
        3. Handle AgentResult — raise 404 / 500 on failure
        4. Return RecommendationOut (HTTP 201)
    """
    logger.info(
        "recommend_request",
        investigation_id=request.investigation_id,
        cluster_id=request.cluster_id,
        owner_user_id=str(request.owner_user_id) if request.owner_user_id else None,
    )

    agent = RecommendAgent()

    # TODO: agent_result = await agent(request)
    # if not agent_result:
    #     raise HTTPException(status_code=500, detail=agent_result.error)
    # return agent_result.output

    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="POST /ai/recommend is not yet implemented — LLM synthesis pending.",
    )


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
    },
)
async def get_recommendation(
    recommendation_id: str,
    # user: dict = Depends(get_current_user),  # TODO: enable auth
) -> RecommendationOut:
    """
    TODO:
        1. Query public.fix_recommendations by recommendation_id
        2. Return RecommendationOut
    """
    logger.info("get_recommendation_request", recommendation_id=recommendation_id)

    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="GET /ai/recommend/{id} is not yet implemented.",
    )
