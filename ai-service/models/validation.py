"""
models/validation.py
--------------------
Pydantic models for fix validation (before/after measurements).

Mirrors: public.validation_results table in supabase/schema.sql
"""

from __future__ import annotations

from datetime import date, datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field


# ================================================================
# Request models
# ================================================================

class ValidateRequest(BaseModel):
    """Request body for POST /ai/validate."""
    fix_recommendation_id: str   = Field(..., description="Target fix recommendation to validate (e.g. R-1)")
    force_revalidate:      bool  = Field(False, description="Re-run validation even if a recent result exists")

    model_config = {"json_schema_extra": {"example": {
        "fix_recommendation_id": "REC-1042",
        "force_revalidate":      False,
    }}}


# ================================================================
# Input / output models
# ================================================================

class ValidationResultIn(BaseModel):
    """A single before/after measurement submission."""
    fix_recommendation_id: str
    measurement_date:      date              = Field(default_factory=date.today)
    period_label:          Optional[str]     = Field(None, description="E.g. 'Week 1 post-ship'")
    ticket_count:          int               = Field(..., ge=0)
    deflection_pct:        Optional[float]   = Field(None, ge=0, le=100)
    revenue_recovered_usd: Optional[float]   = Field(None, ge=0)
    notes:                 Optional[str]     = None
    measured_by:           Optional[UUID]    = None


class ValidationResultOut(BaseModel):
    """Persisted validation measurement returned to the caller."""
    id:                    int
    fix_recommendation_id: str
    measurement_date:      date
    period_label:          Optional[str]
    ticket_count:          int
    deflection_pct:        Optional[float]
    revenue_recovered_usd: Optional[float]
    notes:                 Optional[str]
    measured_by:           Optional[UUID]
    created_at:            datetime

    model_config = {"from_attributes": True}


class ValidationSummary(BaseModel):
    """
    Aggregate validation outcome for a fix recommendation,
    matching the dashboard-ready requirement.
    """
    fix_recommendation_id: str
    
    # Before
    before_ticket_count:   int
    before_customer_count: int
    before_revenue_risk:   float
    
    # After
    after_ticket_count:    int
    after_customer_count:  int
    after_revenue_risk:    float
    
    # Metrics
    deflection_pct:        float
    revenue_recovered_usd: float
    
    # Status
    status:                str   # 'Success' | 'Partial Success' | 'Failed'
    
    # Metadata
    loop_closed:           bool
    measurement_count:     int
    measurements:          list[ValidationResultOut] = Field(default_factory=list)
