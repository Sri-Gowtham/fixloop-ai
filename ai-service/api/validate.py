"""
api/validate.py
---------------
POST /ai/validate
GET  /ai/validate/{fix_recommendation_id}

Measures before/after ticket counts to confirm a shipped fix
actually deflected tickets and recovered revenue (loop closure).
"""

from __future__ import annotations

import structlog
from fastapi import APIRouter, HTTPException, status

from agents.validate_agent import ValidateAgent
from models.validation import ValidateRequest, ValidationSummary
from services.validation import get_validation_summary

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
        404: {"description": "Fix recommendation not found"},
        500: {"description": "Validation pipeline error"},
    },
)
async def validate(
    request: ValidateRequest,
    # user: dict = Depends(get_current_user),
) -> ValidationSummary:
    """Run loop-closure validation on a shipped fix recommendation."""
    logger.info(
        "validate_request",
        fix_recommendation_id=request.fix_recommendation_id,
        force_revalidate=request.force_revalidate,
    )

    agent = ValidateAgent()

    try:
        agent_result = await agent(request)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        )
    except Exception as exc:
        logger.exception("validate_unhandled_error", error=str(exc))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Validation pipeline error: {exc}",
        )

    if not agent_result.success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=agent_result.error or "Validation failed.",
        )

    return agent_result.output  # type: ignore[return-value]


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
        500: {"description": "Database error"},
    },
)
async def get_validation(
    fix_recommendation_id: str,
    # user: dict = Depends(get_current_user),
) -> ValidationSummary:
    """Fetch all validation measurements and aggregate ValidationSummary."""
    logger.info("get_validation_request", fix_recommendation_id=fix_recommendation_id)
    
    try:
        summary = await get_validation_summary(fix_recommendation_id)
        return summary
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        )
    except Exception as exc:
        logger.exception("get_validation_db_error", error=str(exc))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database error: {exc}",
        )
