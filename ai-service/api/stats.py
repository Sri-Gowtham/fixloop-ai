from typing import Optional
from fastapi import APIRouter, status
from pydantic import BaseModel
import structlog

from services.supabase_client import get_supabase

logger = structlog.get_logger(__name__)
router = APIRouter()

class StatsOut(BaseModel):
    total_tickets: int
    active_clusters: int
    revenue_risk_usd: float
    recommendations_generated: int
    fix_success_rate_pct: float
    deployments_tracked: int

@router.get("/", response_model=StatsOut, status_code=status.HTTP_200_OK)
async def get_dashboard_stats() -> StatsOut:
    sb = await get_supabase()

    # 1. Total Tickets
    tickets_resp = await sb.table("tickets").select("*", count="exact").limit(1).execute()
    total_tickets = tickets_resp.count if tickets_resp.count is not None else 0

    # 2. Active Clusters & 3. Revenue Risk
    clusters_resp = await sb.table("ticket_clusters").select("monthly_cost_usd").eq("status", "open").execute()
    clusters_data = clusters_resp.data or []
    active_clusters = len(clusters_data)
    revenue_risk_usd = sum((c.get("monthly_cost_usd") or 0.0) for c in clusters_data)

    # 4. Recommendations Generated
    recs_resp = await sb.table("fix_recommendations").select("*", count="exact").limit(1).execute()
    recommendations_generated = recs_resp.count if recs_resp.count is not None else 0

    # 5. Fix Success Rate
    # Calculate percentage of validations where loop_closed is True or deflection_pct >= 80
    vals_resp = await sb.table("validation_results").select("deflection_pct").execute()
    vals_data = vals_resp.data or []
    total_vals = len(vals_data)
    if total_vals > 0:
        success_count = sum(1 for v in vals_data if (v.get("deflection_pct") or 0.0) >= 80.0)
        fix_success_rate_pct = round((success_count / total_vals) * 100.0, 1)
    else:
        fix_success_rate_pct = 100.0  # default to 100 if no data

    # 6. Deployments Tracked
    deps_resp = await sb.table("deployments").select("*", count="exact").limit(1).execute()
    deployments_tracked = deps_resp.count if deps_resp.count is not None else 0

    return StatsOut(
        total_tickets=total_tickets,
        active_clusters=active_clusters,
        revenue_risk_usd=revenue_risk_usd,
        recommendations_generated=recommendations_generated,
        fix_success_rate_pct=fix_success_rate_pct,
        deployments_tracked=deployments_tracked,
    )
