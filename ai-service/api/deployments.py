"""
api/deployments.py
------------------
REST endpoint for deployments data.

Provides:
  GET /ai/deployments  — list recent deployments (ordered by deployed_at desc)
"""

from __future__ import annotations

from typing import Optional, List

import structlog
from fastapi import APIRouter, Query, status
from pydantic import BaseModel

from services.supabase_client import get_supabase

logger = structlog.get_logger(__name__)
router = APIRouter()


# ----------------------------------------------------------------
# Response model
# ----------------------------------------------------------------
class DeploymentOut(BaseModel):
    id: str
    version: str
    title: Optional[str] = None
    deployed_at: Optional[str] = None
    notes: Optional[str] = None
    risk: Optional[str] = "medium"


# ----------------------------------------------------------------
# GET /ai/deployments
# ----------------------------------------------------------------
@router.get(
    "/deployments",
    response_model=List[DeploymentOut],
    status_code=status.HTTP_200_OK,
    summary="List recent deployments",
    description="Returns deployments ordered by deployed_at descending.",
)
async def list_deployments(
    limit: int = Query(50, ge=1, le=200, description="Max rows to return"),
    start: Optional[str] = Query(None, description="Filter: deployed_at >= start (ISO date)"),
    end: Optional[str] = Query(None, description="Filter: deployed_at <= end (ISO date)"),
) -> List[DeploymentOut]:
    sb = await get_supabase()

    query = (
        sb.table("deployments")
        .select("id, version, title, deployed_at, notes, risk")
        .order("deployed_at", desc=True)
        .limit(limit)
    )

    if start:
        query = query.gte("deployed_at", start)
    if end:
        query = query.lte("deployed_at", end)

    resp = await query.execute()
    rows = resp.data or []

    logger.info("deployments_listed", count=len(rows))

    return [
        DeploymentOut(
            id=row["id"],
            version=row.get("version") or row["id"],
            title=row.get("title"),
            deployed_at=row.get("deployed_at"),
            notes=row.get("notes"),
            risk=row.get("risk") or "medium",
        )
        for row in rows
    ]
