"""
models/investigation.py
-----------------------
Pydantic models for AI root-cause investigations.

Mirrors: public.investigations + public.investigation_evidence
         tables in supabase/schema.sql
"""

from __future__ import annotations

from datetime import datetime
from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel, Field

from .common import EvidenceType, SeverityLevel


# ================================================================
# Sub-models
# ================================================================

class DeployCorrelation(BaseModel):
    """Deploy-spike correlation measured by the investigation engine."""
    deploy_id:   str
    version:     str
    deployed_at: str              # ISO date string
    correlation: float            = Field(..., ge=0.0, le=1.0, description="0–1 Pearson-like score")


class SimulationResult(BaseModel):
    """Fix Validation Simulator — projected outcome if the fix ships."""
    before_ticket_count: int
    after_ticket_count:  int
    deflection_pct:      float   = Field(..., ge=0, le=100)
    recovered_usd:       float   = Field(..., ge=0)


class EvidenceOut(BaseModel):
    """A single weighted evidence item in the explainability chain."""
    id:            str
    evidence_type: EvidenceType
    title:         str
    detail:        Optional[str]
    weight:        float         = Field(..., ge=0.0, le=1.0)
    sort_order:    int

    model_config = {"from_attributes": True}


# ================================================================
# Request models
# ================================================================

class InvestigateRequest(BaseModel):
    """Request body for POST /ai/investigate."""
    cluster_id:              str
    force_refresh:           bool  = Field(False, description="Re-run even if a recent investigation exists")
    confidence_threshold:    float = Field(0.70, ge=0.0, le=1.0)
    deploy_correlation_days: int   = Field(7, ge=1, le=90, description="Window (days) for deploy-spike correlation")

    model_config = {"json_schema_extra": {"example": {
        "cluster_id":  "CL-1042",
        "force_refresh": False,
        "confidence_threshold": 0.70,
        "deploy_correlation_days": 7,
    }}}


# ================================================================
# Response models
# ================================================================

class InvestigationOut(BaseModel):
    """Full AI investigation report returned to the caller."""
    id:                       str
    cluster_id:               str
    root_cause:               str
    confidence:               float             = Field(..., ge=0, le=100)
    impact_level:             SeverityLevel
    affected_customers:       int
    revenue_impact_usd:       float
    deploy_correlation:       Optional[DeployCorrelation]
    reasoning_steps:          List[str]
    evidence:                 List[EvidenceOut]
    simulation:               Optional[SimulationResult]
    model_version:            str
    created_by:               Optional[UUID]
    approved_by:              Optional[UUID]
    approved_at:              Optional[datetime]
    created_at:               datetime
    updated_at:               datetime

    model_config = {"from_attributes": True}
