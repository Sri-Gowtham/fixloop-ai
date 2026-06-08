"""
agents/cluster_agent.py
-----------------------
Cluster agent — wraps the semantic clustering pipeline.

Responsibilities:
  1. Accept a ClusterRequest payload
  2. Delegate to services.clustering.run_clustering()
  3. Return a typed AgentResult[ClusteringResult]
"""

from __future__ import annotations

import structlog

from agents.base import AgentResult, BaseAgent
from models.cluster import ClusterRequest, ClusteringResult
from services.clustering import run_clustering

logger = structlog.get_logger(__name__)


class ClusterAgent(BaseAgent[ClusterRequest, ClusteringResult]):
    """
    Autonomous semantic clustering agent.

    Reads unclustered embedded tickets from Supabase,
    groups them with HDBSCAN, labels them via LLM,
    and persists the results.
    """

    name = "cluster_agent"

    async def run(self, payload: ClusterRequest) -> AgentResult[ClusteringResult]:
        logger.info(
            "cluster_agent_run",
            process_all = payload.process_all,
            dry_run     = payload.dry_run,
            ticket_ids  = len(payload.ticket_ids) if payload.ticket_ids else "all",
        )

        result = await run_clustering(payload)

        return AgentResult(
            success = True,
            output  = result,
            meta    = {
                "cluster_count":     result.cluster_count,
                "clustered_tickets": result.clustered_tickets,
                "noise_tickets":     result.noise_tickets,
            },
        )
