"""
agents/validate_agent.py
------------------------
Validation agent — measures before/after ticket deflection post-fix.

Responsibilities:
  1. Accept a ValidateRequest payload
  2. Call services.validation.run_validation()
  3. Return a typed AgentResult[ValidationSummary]
"""

from __future__ import annotations

import structlog

from agents.base import AgentResult, BaseAgent
from models.validation import ValidateRequest, ValidationSummary
from services.validation import run_validation

logger = structlog.get_logger(__name__)


class ValidateAgent(BaseAgent[ValidateRequest, ValidationSummary]):
    """
    Loop-closure validation agent.
    Confirms a fix actually deflected tickets and recovered revenue.
    """

    name = "validate_agent"

    async def run(self, payload: ValidateRequest) -> AgentResult[ValidationSummary]:
        logger.info(
            "validate_agent_run",
            fix_recommendation_id=payload.fix_recommendation_id,
            force_revalidate=payload.force_revalidate,
        )

        result = await run_validation(payload)

        return AgentResult(
            success = True,
            output  = result,
            meta    = {
                "fix_recommendation_id": result.fix_recommendation_id,
                "deflection_pct":        result.deflection_pct,
                "revenue_recovered_usd": result.revenue_recovered_usd,
                "status":                result.status,
                "loop_closed":           result.loop_closed,
            },
        )
