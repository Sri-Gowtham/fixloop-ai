"""
agents/validate_agent.py
------------------------
Validation agent — measures before/after ticket deflection post-fix.

Responsibilities:
  1. Accept a ValidateRequest payload
  2. Query post-ship ticket counts for the parent cluster
  3. Compute deflection percentage and revenue recovered
  4. Persist ValidationResultIn rows
  5. Determine if the loop is closed (deflection ≥ expected target)
  6. Return ValidationSummary

TODO: implement run() once services.validation is complete.
"""

from __future__ import annotations

from agents.base import AgentResult, BaseAgent
from models.validation import ValidateRequest, ValidationSummary
from services import validation


class ValidateAgent(BaseAgent[ValidateRequest, ValidationSummary]):
    """
    Loop-closure validation agent.
    Confirms a fix actually deflected tickets and recovered revenue.
    """

    name = "validate_agent"

    async def run(self, payload: ValidateRequest) -> AgentResult[ValidationSummary]:
        """
        TODO:
            1. Call validation.run_validation(payload) → ValidationSummary
            2. Wrap in AgentResult with loop_closed and deflection_pct in meta
            3. Return
        """
        raise NotImplementedError("ValidateAgent.run: not yet implemented")
