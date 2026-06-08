"""
agents/recommend_agent.py
-------------------------
Recommendation agent — synthesises actionable fix plans from investigations.

Responsibilities:
  1. Accept a RecommendRequest payload
  2. Load investigation + cluster context
  3. Prompt LLM for fix plan (title, description, owner, ETA, expected metrics)
  4. Persist and return RecommendationOut

TODO: implement run() once services.recommendation is complete.
"""

from __future__ import annotations

from agents.base import AgentResult, BaseAgent
from models.recommendation import RecommendRequest, RecommendationOut
from services import recommendation


class RecommendAgent(BaseAgent[RecommendRequest, RecommendationOut]):
    """
    LLM-powered fix synthesis agent.
    Produces ranked, actionable fix plans from investigation output.
    """

    name = "recommend_agent"

    async def run(self, payload: RecommendRequest) -> AgentResult[RecommendationOut]:
        """
        TODO:
            1. Call recommendation.generate_recommendation(payload) → RecommendationOut
            2. Wrap in AgentResult with expected_reduction_pct in meta
            3. Return
        """
        raise NotImplementedError("RecommendAgent.run: not yet implemented")
