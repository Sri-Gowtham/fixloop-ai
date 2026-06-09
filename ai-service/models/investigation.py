"""
models/investigation.py
-----------------------
Pydantic + dataclass models for AI root-cause investigations.

Mirrors:
    public.investigations          → InvestigationOut
    public.investigation_evidence  → EvidenceOut
    public.deployments             → DeploymentRow  (internal)
"""

from __future__ import annotations

from dataclasses import dataclass, field as dc_field
from datetime import date, datetime
from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel, Field

from .common import EvidenceType, SeverityLevel


# ================================================================
# Pydantic sub-models (API surface)
# ================================================================

class DeployCorrelation(BaseModel):
    """Deploy-spike correlation measured by the investigation engine."""
    deploy_id:   str
    version:     str
    deployed_at: str          # ISO date string
    title:       str  = ""
    correlation: float = Field(..., ge=0.0, le=1.0,
                               description="0–1 normalised correlation score")


class SimulationResult(BaseModel):
    """Fix Validation Simulator — projected outcome if the fix ships."""
    before_ticket_count: int
    after_ticket_count:  int
    deflection_pct:      float  = Field(..., ge=0, le=100)
    recovered_usd:       float  = Field(..., ge=0)


class EvidenceOut(BaseModel):
    """A single weighted evidence item in the explainability chain."""
    id:            str
    evidence_type: EvidenceType
    title:         str
    detail:        Optional[str]
    weight:        float   = Field(..., ge=0.0, le=1.0)
    sort_order:    int

    model_config = {"from_attributes": True}


# ================================================================
# Request / response models
# ================================================================

class InvestigateRequest(BaseModel):
    """Request body for POST /ai/investigate."""
    cluster_id:              str
    force_refresh:           bool  = Field(
        False, description="Re-run even if a recent high-confidence investigation exists"
    )
    confidence_threshold:    float = Field(0.70, ge=0.0, le=1.0)
    deploy_correlation_days: int   = Field(
        7, ge=1, le=90, description="Window (days) to search for correlated deployments"
    )

    model_config = {"json_schema_extra": {"example": {
        "cluster_id":              "CL-1042",
        "force_refresh":           False,
        "confidence_threshold":    0.70,
        "deploy_correlation_days": 7,
    }}}


class InvestigationOut(BaseModel):
    """Full AI investigation report returned to the caller."""
    id:                  str
    cluster_id:          str
    root_cause:          str
    confidence:          float             = Field(..., ge=0, le=100)
    impact_level:        SeverityLevel
    affected_customers:  int
    revenue_impact_usd:  float
    deploy_correlation:  Optional[DeployCorrelation]
    reasoning_steps:     List[str]
    evidence:            List[EvidenceOut]
    simulation:          Optional[SimulationResult]
    model_version:       str
    created_by:          Optional[UUID]
    approved_by:         Optional[UUID]
    approved_at:         Optional[datetime]
    created_at:          datetime
    updated_at:          datetime

    model_config = {"from_attributes": True}


# ================================================================
# Internal dataclasses (service layer only — not exposed via API)
# ================================================================

@dataclass
class ClusterContext:
    """All data fetched about a cluster before the LLM reasoning step."""
    cluster_id:         str
    title:              str
    summary:            Optional[str]
    severity:           str
    ticket_count:       int
    affected_customers: int
    monthly_cost_usd:   float
    product_area:       Optional[str]
    example_titles:     list[str]
    first_seen_at:      Optional[str]
    last_seen_at:       Optional[str]
    # Member ticket samples (title + body) for the LLM
    ticket_samples:     list[dict]         = dc_field(default_factory=list)


@dataclass
class DeploymentRow:
    """A deployment record fetched from public.deployments."""
    id:          str
    version:     str
    title:       str
    deployed_at: str          # ISO date string  (date only)
    risk:        str
    notes:       Optional[str] = None


@dataclass
class CorrelationResult:
    """Result of the deploy-spike correlation analysis."""
    best_deploy:       Optional[DeploymentRow]
    correlation_score: float      # 0–1
    days_to_spike:     Optional[int]   # days from deploy to ticket spike onset
    all_deployments:   list[DeploymentRow] = dc_field(default_factory=list)


@dataclass
class ReasonerOutput:
    """Structured output from the LLM reasoning chain."""
    root_cause:      str
    confidence:      float          # 0–100
    impact_level:    str            # critical | high | medium | low
    revenue_impact:  float          # estimated USD/month
    reasoning_steps: list[str]
    evidence_items:  list[dict]     # [{type, title, detail, weight}]
    # Simulation
    sim_deflection_pct:    Optional[float] = None
    sim_before_count:      Optional[int]   = None
    sim_after_count:       Optional[int]   = None
