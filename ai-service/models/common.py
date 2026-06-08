"""
models/common.py
----------------
Shared enumerations, base types, and generic response wrappers
used across all Pydantic models in the FixLoop AI service.

These map 1-to-1 with the PostgreSQL enums defined in
supabase/migrations/00002_create_enums.sql.
"""

from __future__ import annotations

from enum import Enum
from typing import Generic, List, TypeVar

from pydantic import BaseModel, Field

T = TypeVar("T")


# ================================================================
# Enumerations  (mirror SQL enums exactly)
# ================================================================

class SeverityLevel(str, Enum):
    """severity_level — used by tickets, clusters, investigations."""
    CRITICAL = "critical"
    HIGH     = "high"
    MEDIUM   = "medium"
    LOW      = "low"


class ItemStatus(str, Enum):
    """item_status — lifecycle state for tickets, clusters, fix recs."""
    OPEN        = "open"
    IN_PROGRESS = "in_progress"
    RESOLVED    = "resolved"
    CLOSED      = "closed"


class EvidenceType(str, Enum):
    """evidence_type — signal categories in investigation evidence."""
    TICKET_PATTERN     = "ticket_pattern"
    DEPLOY_CORRELATION = "deploy_correlation"
    CUSTOMER_IMPACT    = "customer_impact"
    SIMILAR_TICKET     = "similar_ticket"


class DeployRisk(str, Enum):
    """deploy_risk — pre-deploy risk assessment."""
    CRITICAL = "critical"
    HIGH     = "high"
    MEDIUM   = "medium"
    LOW      = "low"


class ReportType(str, Enum):
    """report_type — exported intelligence report variants."""
    EXECUTIVE_SUMMARY = "executive_summary"
    CLUSTER_DETAIL    = "cluster_detail"
    FINANCIAL_IMPACT  = "financial_impact"
    CUSTOM            = "custom"


class PipelineStage(str, Enum):
    """Stage labels for the ingest pipeline progress stream."""
    INGEST    = "ingest"
    CLUSTER   = "cluster"
    ROOT      = "root"
    DEPLOY    = "deploy"
    FIX       = "fix"
    IMPACT    = "impact"


# ================================================================
# Generic helpers
# ================================================================

class ErrorDetail(BaseModel):
    """Structured error body returned by 4xx / 5xx responses."""
    code:    str  = Field(..., description="Machine-readable error code")
    message: str  = Field(..., description="Human-readable description")
    details: dict = Field(default_factory=dict, description="Optional extra context")


class PaginatedResponse(BaseModel, Generic[T]):
    """Generic pagination envelope."""
    items:   List[T] = Field(..., description="Page of results")
    total:   int     = Field(..., description="Total matching rows")
    page:    int     = Field(1,   ge=1, description="Current page (1-based)")
    size:    int     = Field(20,  ge=1, le=200, description="Page size")

    @property
    def pages(self) -> int:
        return max(1, -(-self.total // self.size))  # ceiling division
