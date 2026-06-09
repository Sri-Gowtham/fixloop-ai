"""
agents/recommend_agent.py
-------------------------
Recommendation agent — synthesises actionable fix plans from investigations.

Responsibilities:
  1. Accept a RecommendRequest payload
  2. Delegate to services.recommendation.generate_recommendation()
  3. Return a typed AgentResult[RecommendationOut]
"""

from __future__ import annotations

import structlog

from agents.base import AgentResult, BaseAgent
from models.recommendation import RecommendRequest, RecommendationOut
from services.recommendation import generate_recommendation

logger = structlog.get_logger(__name__)


class RecommendAgent(BaseAgent[RecommendRequest, RecommendationOut]):
    """
    LLM-powered fix synthesis agent.
    Produces ranked, actionable fix plans from investigation output.
    """

    name = "recommend_agent"

    async def run(self, payload: RecommendRequest) -> AgentResult[RecommendationOut]:
        logger.info(
            "recommend_agent_run",
            investigation_id = payload.investigation_id,
            cluster_id       = payload.cluster_id,
            force_refresh    = payload.force_refresh,
        )

        result = await generate_recommendation(payload)

        return AgentResult(
            success = True,
            output  = result,
            meta    = {
                "recommendation_id":     result.id,
                "investigation_id":      result.investigation_id,
                "cluster_id":            result.cluster_id,
                "priority":              result.priority,
                "engineering_effort":    result.engineering_effort,
                "confidence_score":      result.confidence_score,
                "expected_reduction_pct": result.expected_reduction_pct,
                "expected_recovery_usd": result.expected_recovery_usd,
            },
        )
