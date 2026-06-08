"""
api/investigate.py
------------------
POST /ai/investigate

Triggers the FixLoop Reasoner to run an autonomous root-cause
investigation for a given ticket cluster.

Endpoint contract:
    POST /ai/investigate
    Content-Type: application/json

    Request:
        InvestigateRequest

    Response 200:
        InvestigationOut
"""

from __future__ import annotations

import structlog
from fastapi import APIRouter, HTTPException, status

from agents.investigate_agent import InvestigateAgent
from models.investigation import InvestigateRequest, InvestigationOut
from api.deps import get_current_user

logger = structlog.get_logger(__name__)
router = APIRouter()


# ----------------------------------------------------------------
# Endpoint: POST /ai/investigate
# ----------------------------------------------------------------

@router.post(
    "/investigate",
    response_model=InvestigationOut,
    status_code=status.HTTP_200_OK,
    summary="Run AI root-cause investigation",
    description=(
        "Runs the FixLoop Reasoner autonomous agent on a ticket cluster. "
        "Detects deploy correlations, builds a reasoning chain, scores evidence, "
        "and returns a full InvestigationOut with simulation results."
    ),
    responses={
        200: {"description": "Investigation completed successfully"},
        400: {"description": "Invalid cluster_id or request parameters"},
        401: {"description": "Missing or invalid Bearer token"},
        404: {"description": "Cluster not found"},
        500: {"description": "Reasoner pipeline error"},
    },
)
async def investigate(
    request: InvestigateRequest,
    # user: dict = Depends(get_current_user),  # TODO: enable auth
) -> InvestigationOut:
    """
    Perform root-cause investigation on a ticket cluster.

    TODO:
        1. Validate cluster_id exists in Supabase
        2. Instantiate InvestigateAgent and call agent(request)
        3. Handle AgentResult — raise 404 / 500 on failure
        4. Return InvestigationOut
    """
    logger.info(
        "investigate_request",
        cluster_id=request.cluster_id,
        force_refresh=request.force_refresh,
        confidence_threshold=request.confidence_threshold,
    )

    agent = InvestigateAgent()

    # TODO: agent_result = await agent(request)
    # if not agent_result:
    #     raise HTTPException(status_code=500, detail=agent_result.error)
    # return agent_result.output

    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="POST /ai/investigate is not yet implemented — Reasoner pipeline pending.",
    )


# ----------------------------------------------------------------
# Endpoint: GET /ai/investigate/{investigation_id}
# ----------------------------------------------------------------

@router.get(
    "/investigate/{investigation_id}",
    response_model=InvestigationOut,
    status_code=status.HTTP_200_OK,
    summary="Get investigation by ID",
    description="Fetch a previously completed AI investigation report.",
    responses={
        200: {"description": "Investigation found"},
        404: {"description": "Investigation not found"},
    },
)
async def get_investigation(
    investigation_id: str,
    # user: dict = Depends(get_current_user),  # TODO: enable auth
) -> InvestigationOut:
    """
    TODO:
        1. Query public.investigations by investigation_id via Supabase
        2. Join public.investigation_evidence
        3. Return InvestigationOut
    """
    logger.info("get_investigation_request", investigation_id=investigation_id)

    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="GET /ai/investigate/{id} is not yet implemented.",
    )
