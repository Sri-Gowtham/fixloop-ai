"""
agents/base.py
--------------
Abstract base class for all FixLoop AI agents.

Each agent wraps a pipeline stage (ingest / investigate /
recommend / validate) and provides:
  - A standard run() entry point
  - Structured logging with stage context
  - Retry logic via tenacity
  - A common result envelope
"""

from __future__ import annotations

import abc
from typing import Any, Generic, TypeVar

import structlog

Input  = TypeVar("Input")
Output = TypeVar("Output")

logger = structlog.get_logger(__name__)


class AgentResult(Generic[Output]):
    """Standard result envelope returned by every agent."""

    def __init__(
        self,
        success: bool,
        output:  Output | None = None,
        error:   str | None    = None,
        meta:    dict          = None,
    ):
        self.success = success
        self.output  = output
        self.error   = error
        self.meta    = meta or {}

    def __bool__(self) -> bool:
        return self.success


class BaseAgent(abc.ABC, Generic[Input, Output]):
    """
    Abstract agent base.

    Subclasses must implement:
        name       (class property) — human-readable agent name
        run()      — core processing logic
    """

    name: str = "base_agent"

    @abc.abstractmethod
    async def run(self, payload: Input) -> AgentResult[Output]:
        """Execute the agent and return a typed AgentResult."""
        ...

    async def __call__(self, payload: Input) -> AgentResult[Output]:
        log = logger.bind(agent=self.name)
        log.info("agent_start")
        try:
            result = await self.run(payload)
            if result.success:
                log.info("agent_success", meta=result.meta)
            else:
                log.warning("agent_failure", error=result.error)
            return result
        except Exception as exc:
            log.exception("agent_exception", error=str(exc))
            return AgentResult(success=False, error=str(exc))
