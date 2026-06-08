"""
agents/investigate_agent.py
---------------------------
Investigation agent — runs the FixLoop Reasoner root-cause pipeline.

Responsibilities:
  1. Accept an InvestigateRequest payload
  2. Detect deploy correlations
  3. Run LLM reasoning chain
  4. Score and weight evidence
  5. Run fix simulation
  6. Persist and return InvestigationOut

TODO: implement run() once services.investigation is complete.
"""

from __future__ import annotations

from agents.base import AgentResult, BaseAgent
from models.investigation import InvestigateRequest, InvestigationOut
from services import investigation


class InvestigateAgent(BaseAgent[InvestigateRequest, InvestigationOut]):
    """
    Autonomous root-cause investigation agent.
    Uses GPT-4o to reason over cluster evidence and deploy signals.
    """

    name = "investigate_agent"

    async def run(self, payload: InvestigateRequest) -> AgentResult[InvestigationOut]:
        """
        TODO:
            1. Call investigation.run_investigation(payload) → InvestigationOut
            2. Wrap in AgentResult with confidence + cluster_id in meta
            3. Return
        """
        raise NotImplementedError("InvestigateAgent.run: not yet implemented")
