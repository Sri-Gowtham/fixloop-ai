"""
api/validate.py
---------------
POST /ai/validate

Measures before/after ticket counts to confirm a shipped fix
actually deflected tickets and recovered revenue (loop closure).

Endpoint contract:
    POST /ai/validate
    Content-Type: application/json

    Request:
        ValidateRequest

    Response 200:
        ValidationSummary
"""

from __future__ import annotations

import structlog
from fastapi import APIRouter, HTTPException, status

from agents.validate_agent import ValidateAgent
from models.validation import ValidateRequest, ValidationResultOut, ValidationSummary
from api.deps import get_current_user

logger = structlog.get_logger(__name__)
router = APIRouter()


# ----------------------------------------------------------------
# Endpoint: POST /ai/validate
# ----------------------------------------------------------------

@router.post(
    "/validate",
    response_model=ValidationSummary,
    status_code=status.HTTP_200_OK,
    summary="Validate a shipped fix (loop closure)",
    description=(
        "Measures post-ship ticket counts for the parent cluster and computes "
        "the achieved deflection rate and revenue recovered. "
        "Sets loop_closed = True when deflection meets the expected target. "
        "Updates fix_recommendations.status → 'resolved' on loop closure."
    ),
    responses={
        200: {"description": "Validation completed — ValidationSummary returned"},
        400: {"description": "Invalid fix_recommendation_id"},
        401: {"description": "Missing or invalid Bearer token"},
        404: {"description": "Fix recommendation not found"},
        500: {"description": "Validation pipeline error"},
    },
)
async def validate(
    request: ValidateRequest,
    # user: dict = Depends(get_current_user),  # TODO: enable auth
) -> ValidationSummary:
    """
    Run loop-closure validation on a shipped fix recommendation.

    TODO:
        1. Validate fix_recommendation_id exists in Supabase
        2. Instantiate ValidateAgent and call agent(request)
        3. Handle AgentResult — raise 404 / 500 on failure
        4. Return ValidationSummary (loop_closed, deflection_pct, recovered_usd)
    """
    logger.info(
        "validate_request",
        fix_recommendation_id=request.fix_recommendation_id,
        force_revalidate=request.force_revalidate,
    )

    agent = ValidateAgent()

    # TODO: agent_result = await agent(request)
    # if not agent_result:
    #     raise HTTPException(status_code=500, detail=agent_result.error)
    # return agent_result.output

    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="POST /ai/validate is not yet implemented — measurement pipeline pending.",
    )


# ----------------------------------------------------------------
# Endpoint: GET /ai/validate/{fix_recommendation_id}
# ----------------------------------------------------------------

@router.get(
    "/validate/{fix_recommendation_id}",
    response_model=ValidationSummary,
    status_code=status.HTTP_200_OK,
    summary="Get validation summary for a fix",
    description="Fetch all validation measurements and the loop-closure summary for a fix recommendation.",
    responses={
        200: {"description": "Validation summary found"},
        404: {"description": "Fix recommendation or measurements not found"},
    },
)
async def get_validation(
    fix_recommendation_id: str,
    # user: dict = Depends(get_current_user),  # TODO: enable auth
) -> ValidationSummary:
    """
    TODO:
        1. Query public.validation_results by fix_recommendation_id
        2. Query fix_recommendations for expected_reduction_pct
        3. Compute aggregate ValidationSummary
        4. Return
    """
    logger.info("get_validation_request", fix_recommendation_id=fix_recommendation_id)

    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="GET /ai/validate/{id} is not yet implemented.",
    )
