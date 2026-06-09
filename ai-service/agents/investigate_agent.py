"""
agents/investigate_agent.py
---------------------------
Investigation agent — wraps the root-cause investigation pipeline.

Responsibilities:
  1. Accept an InvestigateRequest
  2. Delegate to services.investigation.run_investigation()
  3. Return a typed AgentResult[InvestigationOut]
"""

from __future__ import annotations

import structlog

from agents.base import AgentResult, BaseAgent
from models.investigation import InvestigateRequest, InvestigationOut
from services.investigation import run_investigation

logger = structlog.get_logger(__name__)


class InvestigateAgent(BaseAgent[InvestigateRequest, InvestigationOut]):
    """
    Autonomous root-cause investigation agent.

    Uses the configured LLM backend (GPT-4o or Gemini) to reason
    over cluster evidence, deployment history, and ticket patterns,
    producing a full InvestigationOut report.
    """

    name = "investigate_agent"

    async def run(self, payload: InvestigateRequest) -> AgentResult[InvestigationOut]:
        logger.info(
            "investigate_agent_run",
            cluster_id           = payload.cluster_id,
            force_refresh        = payload.force_refresh,
            confidence_threshold = payload.confidence_threshold,
        )

        result = await run_investigation(payload)

        return AgentResult(
            success = True,
            output  = result,
            meta    = {
                "investigation_id":  result.id,
                "cluster_id":        result.cluster_id,
                "confidence":        result.confidence,
                "impact_level":      result.impact_level.value,
                "revenue_impact_usd": result.revenue_impact_usd,
                "deploy_correlated": result.deploy_correlation is not None,
            },
        )
