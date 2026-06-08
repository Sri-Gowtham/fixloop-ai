"""
models/ticket.py
----------------
Pydantic models for raw ticket ingestion.

Mirrors: public.tickets table in supabase/schema.sql
"""

from __future__ import annotations

from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, EmailStr, Field

from .common import ItemStatus, SeverityLevel


# ================================================================
# Input models (request bodies)
# ================================================================

class TicketIn(BaseModel):
    """
    A single support ticket submitted for ingestion.
    Accepted from CSV rows, Zendesk JSON, or log streams.
    """
    external_id:       Optional[str]           = Field(None,  description="Source system ID (Zendesk ticket ID, etc.)")
    source:            str                     = Field("csv", pattern="^(csv|zendesk|intercom|logs|manual)$")
    title:             str                     = Field(...,   min_length=1, max_length=512)
    body:              Optional[str]           = Field(None,  description="Full ticket description / conversation body")
    customer_id:       Optional[str]           = Field(None,  description="Opaque external customer identifier")
    customer_email:    Optional[EmailStr]      = Field(None)
    severity:          Optional[SeverityLevel] = Field(None)
    channel:           Optional[str]           = Field(None,  description="email | chat | phone | web")
    tags:              List[str]               = Field(default_factory=list)
    related_deploy_id: Optional[str]           = Field(None,  description="FK to deployments.id if already correlated")
    ticket_created_at: Optional[datetime]      = Field(None,  description="Original creation timestamp in source system")

    model_config = {"json_schema_extra": {"example": {
        "external_id":    "ZD-88001",
        "source":         "zendesk",
        "title":          "Export keeps spinning on 2k row sheet",
        "body":           "I started a CSV export of our 2000-row contact list and it just spins forever.",
        "customer_id":    "CUST-0312",
        "customer_email": "user@acmecorp.com",
        "severity":       "critical",
        "channel":        "email",
        "tags":           ["export", "timeout"],
        "ticket_created_at": "2026-05-16T09:12:00Z",
    }}}


class TicketIngestBatch(BaseModel):
    """Request body for POST /ai/ingest — supports batch + metadata."""
    tickets:    List[TicketIn] = Field(..., min_length=1, description="Tickets to ingest (max 5000 per request)")
    source:     str            = Field("csv",  description="Batch source type override")
    run_cluster: bool          = Field(True,  description="Trigger re-clustering after ingestion")
    dry_run:    bool           = Field(False, description="Validate without persisting to the database")


# ================================================================
# Output models (response bodies)
# ================================================================

class TicketOut(BaseModel):
    """Persisted ticket returned from the database."""
    id:                int
    external_id:       Optional[str]
    source:            str
    title:             str
    body:              Optional[str]
    customer_id:       Optional[str]
    customer_email:    Optional[str]
    severity:          Optional[SeverityLevel]
    status:            ItemStatus
    sentiment_score:   Optional[float]         = Field(None, ge=-1.0, le=1.0)
    channel:           Optional[str]
    tags:              List[str]
    related_deploy_id: Optional[str]
    embedding_ready:   bool                    = Field(False, description="True once the embedding vector is populated")
    ingested_at:       datetime
    ticket_created_at: Optional[datetime]
    created_at:        datetime

    model_config = {"from_attributes": True}
