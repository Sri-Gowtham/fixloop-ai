"""
services/recommendation.py
--------------------------
Fix recommendation service.

Synthesises actionable fix plans from AI investigation output
and persists them to public.fix_recommendations.

Business logic is stubbed — see TODO markers.
"""

from __future__ import annotations

import structlog

from models.recommendation import RecommendRequest, RecommendationOut

logger = structlog.get_logger(__name__)


async def generate_recommendation(request: RecommendRequest) -> RecommendationOut:
    """
    Generate an AI fix recommendation from an investigation.

    Steps (to be implemented):
        1. Fetch the investigation (InvestigationOut) by request.investigation_id.
        2. Fetch cluster detail for context.
        3. Prompt LLM with:
           - Root cause + reasoning steps
           - Evidence trail
           - Deploy correlation
           - Historical similar-issue fixes (if available via ANN search)
        4. Parse LLM output into RecommendationIn fields:
           - title, description, expected_reduction_pct, expected_recovery_usd, estimated_eta
        5. Assign owner if request.owner_user_id is set.
        6. Persist to public.fix_recommendations via Supabase.
        7. Return RecommendationOut.

    TODO: implement the 7 steps above.
    TODO: add Jira / Linear ticket creation webhook option.
    """
    logger.info(
        "recommendation_start",
        investigation_id=request.investigation_id,
        cluster_id=request.cluster_id,
    )
    raise NotImplementedError("generate_recommendation: business logic not yet implemented")


async def estimate_revenue_recovery(
    monthly_cost_usd:       float,
    expected_reduction_pct: float,
) -> float:
    """
    Calculate the estimated monthly revenue recovery for a fix.

    Formula: monthly_cost_usd * (expected_reduction_pct / 100)

    TODO: refine with historical deflection accuracy data.
    """
    raise NotImplementedError("estimate_revenue_recovery: not yet implemented")
