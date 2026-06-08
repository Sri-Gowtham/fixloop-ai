"""
agents/ingest_agent.py
----------------------
Ingestion agent — wraps the ingestion service pipeline.
Optionally triggers the ClusterAgent after ingestion completes.

Responsibilities:
  1. Accept a TicketIngestBatch payload
  2. Delegate to services.ingestion.ingest_batch()
  3. If run_cluster=True and new tickets were embedded, trigger ClusterAgent
  4. Return a typed AgentResult with combined statistics
"""

from __future__ import annotations

import structlog

from agents.base import AgentResult, BaseAgent
from models.cluster import ClusterRequest
from models.ticket import TicketIngestBatch
from services.ingestion import IngestionResult, ingest_batch

logger = structlog.get_logger(__name__)


class IngestAgent(BaseAgent[TicketIngestBatch, dict]):
    """
    Runs the end-to-end ticket ingestion pipeline:
    validate → dedup → persist → embed → (optional) cluster.
    """

    name = "ingest_agent"

    async def run(self, payload: TicketIngestBatch) -> AgentResult[dict]:
        """
        Execute ingestion, then optionally trigger clustering.
        """
        logger.info(
            "ingest_agent_run",
            ticket_count = len(payload.tickets),
            source       = payload.source,
            dry_run      = payload.dry_run,
            run_cluster  = payload.run_cluster,
        )

        # ── Step 1: Ingest ──────────────────────────────────────
        ingest_result: IngestionResult = await ingest_batch(payload)

        meta: dict = {
            "total_tickets":     ingest_result.total_tickets,
            "successful":        ingest_result.successful,
            "failed":            ingest_result.failed,
            "skipped_dupes":     ingest_result.skipped_dupes,
            "embeddings_stored": ingest_result.embeddings_stored,
            "cluster_count":     0,
            "clustered_tickets": 0,
            "noise_tickets":     0,
        }

        # ── Step 2: Cluster (if requested and tickets were embedded) ──
        if (
            payload.run_cluster
            and not payload.dry_run
            and ingest_result.embeddings_stored > 0
        ):
            # Import here to avoid circular-import at module load time
            from agents.cluster_agent import ClusterAgent

            new_ticket_ids = [t.id for t in ingest_result.tickets]
            cluster_request = ClusterRequest(
                ticket_ids  = new_ticket_ids if new_ticket_ids else None,
                process_all = False,
                dry_run     = False,
            )

            logger.info(
                "ingest_agent_triggering_clustering",
                new_ticket_ids_count = len(new_ticket_ids),
            )

            cluster_agent  = ClusterAgent()
            cluster_result = await cluster_agent(cluster_request)

            if cluster_result.success and cluster_result.output:
                cr = cluster_result.output
                meta.update({
                    "cluster_count":     cr.cluster_count,
                    "clustered_tickets": cr.clustered_tickets,
                    "noise_tickets":     cr.noise_tickets,
                })

        return AgentResult(
            success = True,
            output  = {
                "ingest": ingest_result,
                "meta":   meta,
            },
            meta = meta,
        )
