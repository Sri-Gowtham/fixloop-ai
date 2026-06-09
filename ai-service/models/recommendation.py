"""
models/recommendation.py
------------------------
Pydantic models for AI fix recommendations.

Mirrors: public.fix_recommendations table in supabase/schema.sql
"""

from __future__ import annotations

from dataclasses import dataclass, field as dc_field
from datetime import datetime
from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel, Field, HttpUrl

from .common import ItemStatus, SeverityLevel


# ================================================================
# Request models
# ================================================================

class RecommendRequest(BaseModel):
    """Request body for POST /ai/recommend."""
    investigation_id: str   = Field(..., description="Parent investigation ID (e.g. AI-7741)")
    cluster_id:       str   = Field(..., description="Target cluster ID")
    owner_user_id:    Optional[UUID] = Field(None, description="Assign recommendation to this user")
    force_refresh:    bool  = Field(
        False, description="Re-run even if a recent recommendation exists for this investigation"
    )

    model_config = {"json_schema_extra": {"example": {
        "investigation_id": "AI-7741",
        "cluster_id":       "CL-1042",
        "owner_user_id":    None,
        "force_refresh":    False,
    }}}


# ================================================================
# Input / output models
# ================================================================

class RecommendationIn(BaseModel):
    """Manual or AI-generated fix recommendation (write model)."""
    cluster_id:              str
    investigation_id:        Optional[str]   = None
    title:                   str             = Field(..., min_length=1, max_length=256)
    description:             str             = Field(..., min_length=1)
    priority:                Optional[str]   = Field(None, description="critical|high|medium|low")
    engineering_effort:      Optional[str]   = Field(None, description="low|medium|high|very_high")
    confidence_score:        Optional[float] = Field(None, ge=0, le=100)
    owner_name:              Optional[str]   = None
    owner_user_id:           Optional[UUID]  = None
    expected_reduction_pct:  Optional[float] = Field(None, ge=0, le=100)
    expected_recovery_usd:   Optional[float] = Field(None, ge=0)
    estimated_eta:           Optional[str]   = Field(None, description="Human-readable ETA, e.g. '2 days'")
    external_ticket_url:     Optional[HttpUrl] = None
    # Jira-style ticket content
    jira_title:              Optional[str]   = None
    jira_description:        Optional[str]   = None
    jira_acceptance_criteria: Optional[List[str]] = None
    jira_severity:           Optional[str]   = None


class RecommendationOut(BaseModel):
    """Persisted fix recommendation returned to the caller."""
    id:                      str
    cluster_id:              str
    investigation_id:        Optional[str]
    title:                   str
    description:             str
    priority:                Optional[str]
    engineering_effort:      Optional[str]
    confidence_score:        Optional[float]
    owner_name:              Optional[str]
    owner_user_id:           Optional[UUID]
    status:                  ItemStatus
    expected_reduction_pct:  Optional[float]
    expected_recovery_usd:   Optional[float]
    actual_reduction_pct:    Optional[float]
    actual_recovery_usd:     Optional[float]
    before_ticket_count:     Optional[int]
    after_ticket_count:      Optional[int]
    estimated_eta:           Optional[str]
    external_ticket_url:     Optional[str]
    # Jira-style ticket content
    jira_title:              Optional[str]
    jira_description:        Optional[str]
    jira_acceptance_criteria: Optional[List[str]]
    jira_severity:           Optional[str]
    created_by:              Optional[UUID]
    resolved_by:             Optional[UUID]
    resolved_at:             Optional[datetime]
    created_at:              datetime
    updated_at:              datetime

    model_config = {"from_attributes": True}


# ================================================================
# Internal dataclass (service layer only — not exposed via API)
# ================================================================

@dataclass
class RecommenderOutput:
    """Structured output from the LLM recommendation chain."""
    title:                    str
    description:              str
    priority:                 str        # critical | high | medium | low
    engineering_effort:       str        # low | medium | high | very_high
    confidence_score:         float      # 0–100
    expected_reduction_pct:   float      # 0–100
    expected_recovery_usd:    float      # estimated USD/month
    estimated_eta:            str        # human-readable, e.g. "2 days"
    # Jira-style ticket content
    jira_title:               str              = ""
    jira_description:         str              = ""
    jira_acceptance_criteria: list[str]        = dc_field(default_factory=list)
    jira_severity:            str              = "medium"
