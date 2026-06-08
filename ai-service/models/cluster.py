"""
models/cluster.py
-----------------
Pydantic models for semantic ticket clusters.

Mirrors: public.ticket_clusters + public.cluster_tickets
         tables in supabase/schema.sql

Exported:
    ClusterSummary       — lightweight list/dashboard view
    ClusterOut           — full detail (API response)
    ClusterRequest       — POST /ai/cluster request body
    ClusteringResult     — returned by the clustering service
    ClusterTicketRef     — a ticket reference within a cluster result
"""

from __future__ import annotations

from dataclasses import dataclass, field as dc_field
from datetime import date, datetime
from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel, Field

from .common import ItemStatus, SeverityLevel


# ================================================================
# API response models
# ================================================================

class ClusterSummary(BaseModel):
    """Lightweight cluster used in list views and dashboard widgets."""
    id:                 str
    title:              str
    severity:           SeverityLevel
    status:             ItemStatus
    ticket_count:       int
    affected_customers: int
    monthly_cost_usd:   float
    confidence:         Optional[float] = Field(None, ge=0, le=100)
    product_area:       Optional[str]
    related_deploy_id:  Optional[str]
    first_seen_at:      Optional[date]

    model_config = {"from_attributes": True}


class ClusterOut(ClusterSummary):
    """Full cluster detail including trend, examples, and root cause."""
    summary:           Optional[str]
    root_cause:        Optional[str]
    ticket_trend:      List[float]      = Field(default_factory=list, description="Rolling daily ticket counts")
    example_titles:    List[str]        = Field(default_factory=list, description="Representative ticket titles")
    last_seen_at:      Optional[date]
    created_by:        Optional[UUID]
    created_at:        datetime
    updated_at:        datetime

    model_config = {"from_attributes": True}


# ================================================================
# Request model
# ================================================================

class ClusterRequest(BaseModel):
    """
    Request body for POST /ai/cluster.

    Either ticket_ids (subset) or process_all (full run) must be provided.
    """
    ticket_ids:     Optional[List[int]]  = Field(
        None,
        description="Specific ticket IDs to cluster. If omitted, all unclustered embedded tickets are used.",
    )
    process_all:    bool = Field(
        False,
        description="Re-cluster ALL embedded tickets, including already-clustered ones.",
    )
    dry_run:        bool = Field(
        False,
        description="Run HDBSCAN and LLM labelling without writing to the database.",
    )
    min_cluster_size: Optional[int] = Field(
        None, ge=2,
        description="Override HDBSCAN min_cluster_size for this run.",
    )

    model_config = {"json_schema_extra": {"example": {
        "ticket_ids": None,
        "process_all": False,
        "dry_run": False,
    }}}


# ================================================================
# Internal / service-layer dataclasses
# ================================================================

@dataclass
class RawTicket:
    """Ticket row fetched from Supabase for clustering."""
    id:          int
    title:       str
    body:        Optional[str]
    embedding:   list[float]
    customer_id: Optional[str] = None
    severity:    Optional[str] = None
    created_at:  Optional[str] = None


@dataclass
class ClusterLabel:
    """
    LLM-generated human-readable label for a single cluster.
    Produced by the cluster_labeller service.
    """
    title:        str
    summary:      str
    severity:     SeverityLevel
    confidence:   float                  # 0–100
    product_area: Optional[str] = None


@dataclass
class ClusterRecord:
    """
    Fully resolved cluster ready to be written to public.ticket_clusters.
    """
    cluster_id:         str               # CL-<uuid4 prefix>
    label:              ClusterLabel
    ticket_ids:         list[int]
    centroid:           list[float]
    example_titles:     list[str]
    affected_customers: int
    first_seen_at:      Optional[date]
    last_seen_at:       Optional[date]


@dataclass
class ClusteringResult:
    """
    Returned by run_clustering() — the canonical response shape
    required by the API and the IngestAgent.
    """
    cluster_count:      int              = 0
    clustered_tickets:  int              = 0
    noise_tickets:      int              = 0
    clusters:           list[ClusterOut] = dc_field(default_factory=list)
