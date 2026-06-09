"""
tests/test_investigation.py
---------------------------
Unit + integration tests for the Root Cause Investigation Engine.

Test categories:
  A. Deploy correlation helpers (pure unit)
  B. LLM response parsing (_parse_reasoner_output)
  C. Evidence coercion and weight clamping
  D. Full run_investigation() pipeline (all mocked)
  E. Cache guard (_fetch_existing_investigation)
  F. API endpoints (POST, GET by ID, GET by cluster)
"""

from __future__ import annotations

import json
import uuid
from datetime import date, datetime, timezone
from typing import Optional
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from httpx import ASGITransport, AsyncClient

from main import app
from models.common import EvidenceType, SeverityLevel
from models.investigation import (
    ClusterContext,
    CorrelationResult,
    DeploymentRow,
    InvestigateRequest,
    InvestigationOut,
    ReasonerOutput,
)
from services.investigation import (
    _build_investigation_out,
    _fallback_reasoner_output,
    _parse_reasoner_output,
    detect_deploy_correlation,
    run_investigation,
)


# ============================================================
# Fixtures
# ============================================================

@pytest.fixture
async def http_client():
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as c:
        yield c


def _make_ctx(
    cluster_id: str = "CL-TEST01",
    ticket_count: int = 50,
    severity: str = "high",
    affected_customers: int = 30,
    first_seen_at: Optional[str] = "2026-05-10",
    ticket_samples: Optional[list] = None,
) -> ClusterContext:
    return ClusterContext(
        cluster_id         = cluster_id,
        title              = "CSV Export Timeout",
        summary            = "Users experience export failures above 500 rows.",
        severity           = severity,
        ticket_count       = ticket_count,
        affected_customers = affected_customers,
        monthly_cost_usd   = 3500.0,
        product_area       = "Exports & Reports",
        example_titles     = ["Export fails at 500 rows", "CSV download hangs"],
        first_seen_at      = first_seen_at,
        last_seen_at       = "2026-05-22",
        ticket_samples     = ticket_samples or [
            {"id": i, "title": f"Ticket {i}", "body": "Export timeout occurred."}
            for i in range(1, 11)
        ],
    )


def _make_deploy(
    did: str = "DEPLOY-001",
    version: str = "v2.4.1",
    deployed_at: str = "2026-05-08",
    risk: str = "high",
) -> DeploymentRow:
    return DeploymentRow(
        id          = did,
        version     = version,
        title       = f"Release {version}",
        deployed_at = deployed_at,
        risk        = risk,
    )


def _valid_reasoner_json(
    root_cause: str = "CSV export service fails above 500 rows.",
    confidence: float = 94.0,
    impact: str = "high",
) -> str:
    return json.dumps({
        "root_cause":      root_cause,
        "confidence":      confidence,
        "impact_level":    impact,
        "revenue_impact":  34000.0,
        "reasoning_steps": [
            "487 tickets mention timeout or export failure.",
            "Spike onset correlates with v2.4.1 deploy.",
            "All affected users triggered the bulk-export endpoint.",
        ],
        "evidence_items": [
            {
                "type":   "ticket_pattern",
                "title":  "Export timeout pattern",
                "detail": "487 tickets report export failure above 500 rows.",
                "weight": 0.95,
            },
            {
                "type":   "deploy_correlation",
                "title":  "v2.4.1 deploy spike",
                "detail": "Ticket volume spiked 3× within 48 h of v2.4.1.",
                "weight": 0.88,
            },
        ],
        "sim_deflection_pct": 85.0,
        "sim_before_count":   50,
        "sim_after_count":    8,
    })


# ============================================================
# A. Deploy correlation helpers
# ============================================================

class TestDeployCorrelation:

    @pytest.mark.asyncio
    async def test_no_deployments_returns_zero(self):
        ctx    = _make_ctx()
        result = await detect_deploy_correlation(ctx, [], 7)
        assert result.best_deploy is None
        assert result.correlation_score == 0.0

    @pytest.mark.asyncio
    async def test_deploy_before_onset_is_correlated(self):
        """Deploy 2 days before spike onset should be picked up."""
        ctx     = _make_ctx(first_seen_at="2026-05-10")
        deploy  = _make_deploy(deployed_at="2026-05-08", risk="high")   # 2 days before
        result  = await detect_deploy_correlation(ctx, [deploy], 7)
        assert result.best_deploy is not None
        assert result.best_deploy.id == "DEPLOY-001"
        assert result.correlation_score > 0.0

    @pytest.mark.asyncio
    async def test_deploy_after_onset_excluded(self):
        """Deploy that happened AFTER the spike onset cannot be a cause."""
        ctx    = _make_ctx(first_seen_at="2026-05-08")
        deploy = _make_deploy(deployed_at="2026-05-12")   # 4 days AFTER onset
        result = await detect_deploy_correlation(ctx, [deploy], 7)
        assert result.best_deploy is None

    @pytest.mark.asyncio
    async def test_high_risk_deploy_scores_higher(self):
        """High-risk deploys should score higher than low-risk at same proximity."""
        ctx        = _make_ctx(first_seen_at="2026-05-10")
        deploy_hi  = _make_deploy("D-HI",  deployed_at="2026-05-09", risk="high")
        deploy_lo  = _make_deploy("D-LO",  deployed_at="2026-05-09", risk="low")

        result_hi = await detect_deploy_correlation(ctx, [deploy_hi], 7)
        result_lo = await detect_deploy_correlation(ctx, [deploy_lo], 7)

        # Both found; hi-risk should have higher normalised score
        # (with a single deploy they're both normalised to 1.0 since max is itself)
        # So we test with two deploys in one call:
        result = await detect_deploy_correlation(ctx, [deploy_hi, deploy_lo], 7)
        assert result.best_deploy.id == "D-HI"

    @pytest.mark.asyncio
    async def test_closest_deploy_beats_older_one(self):
        """Deploy closest in time to spike onset should rank highest."""
        ctx    = _make_ctx(first_seen_at="2026-05-10")
        close  = _make_deploy("D-CLOSE", deployed_at="2026-05-09", risk="medium")   # 1 day before
        far    = _make_deploy("D-FAR",   deployed_at="2026-05-01", risk="medium")   # 9 days before
        result = await detect_deploy_correlation(ctx, [close, far], 7)
        assert result.best_deploy.id == "D-CLOSE"

    @pytest.mark.asyncio
    async def test_onset_fallback_to_ticket_dates(self):
        """When first_seen_at is None, fallback to earliest ticket created_at."""
        ctx = _make_ctx(
            first_seen_at = None,
            ticket_samples = [
                {"id": 1, "title": "T1", "ticket_created_at": "2026-05-10T08:00:00Z"},
                {"id": 2, "title": "T2", "ticket_created_at": "2026-05-12T08:00:00Z"},
            ],
        )
        deploy = _make_deploy(deployed_at="2026-05-09", risk="high")
        result = await detect_deploy_correlation(ctx, [deploy], 7)
        assert result.best_deploy is not None

    @pytest.mark.asyncio
    async def test_beyond_window_deploy_excluded(self):
        """Deploy beyond window_days + 14 buffer should be ignored."""
        ctx    = _make_ctx(first_seen_at="2026-05-10")
        deploy = _make_deploy(deployed_at="2026-04-01", risk="critical")  # 39 days before
        result = await detect_deploy_correlation(ctx, [deploy], window_days=7)
        assert result.best_deploy is None


# ============================================================
# B. LLM response parsing
# ============================================================

class TestReasonerParsing:

    def test_parse_valid_json(self):
        ctx    = _make_ctx()
        output = _parse_reasoner_output(_valid_reasoner_json(), ctx)
        assert output.root_cause == "CSV export service fails above 500 rows."
        assert output.confidence == 94.0
        assert output.impact_level == "high"
        assert output.revenue_impact == 34000.0
        assert len(output.reasoning_steps) == 3
        assert len(output.evidence_items) == 2

    def test_parse_simulation_values(self):
        ctx    = _make_ctx(ticket_count=50)
        output = _parse_reasoner_output(_valid_reasoner_json(), ctx)
        assert output.sim_before_count == 50
        assert output.sim_after_count == 8
        assert output.sim_deflection_pct == 85.0

    def test_confidence_clamped_to_100(self):
        raw = _valid_reasoner_json(confidence=150.0)
        ctx = _make_ctx()
        output = _parse_reasoner_output(raw, ctx)
        assert output.confidence == 100.0

    def test_confidence_clamped_to_zero(self):
        raw = _valid_reasoner_json(confidence=-10.0)
        ctx = _make_ctx()
        output = _parse_reasoner_output(raw, ctx)
        assert output.confidence == 0.0

    def test_invalid_json_returns_fallback(self):
        ctx    = _make_ctx(ticket_count=20)
        output = _parse_reasoner_output("not json!!!", ctx)
        assert output.root_cause  # non-empty
        assert output.confidence > 0

    def test_markdown_fenced_json_parsed(self):
        raw = f"```json\n{_valid_reasoner_json()}\n```"
        ctx = _make_ctx()
        output = _parse_reasoner_output(raw, ctx)
        assert output.confidence == 94.0

    def test_unknown_impact_level_defaults_to_cluster_severity(self):
        data = json.loads(_valid_reasoner_json())
        data["impact_level"] = "super_critical"
        ctx    = _make_ctx(severity="medium")
        output = _parse_reasoner_output(json.dumps(data), ctx)
        assert output.impact_level == "medium"

    def test_evidence_type_coerced_to_valid(self):
        data = json.loads(_valid_reasoner_json())
        data["evidence_items"][0]["type"] = "unknown_type"
        ctx    = _make_ctx()
        output = _parse_reasoner_output(json.dumps(data), ctx)
        assert output.evidence_items[0]["type"] == "ticket_pattern"

    def test_evidence_weight_clamped(self):
        data = json.loads(_valid_reasoner_json())
        data["evidence_items"][0]["weight"] = 5.0   # > 1.0
        ctx    = _make_ctx()
        output = _parse_reasoner_output(json.dumps(data), ctx)
        assert output.evidence_items[0]["weight"] == 1.0

    def test_revenue_floor_applied(self):
        """Revenue impact should be at least ticket_count × cost_per_ticket."""
        data = json.loads(_valid_reasoner_json())
        data["revenue_impact"] = 1.0   # unrealistically low
        ctx    = _make_ctx(ticket_count=100)
        output = _parse_reasoner_output(json.dumps(data), ctx)
        # floor = 100 × $70 = $7000
        assert output.revenue_impact >= 7000.0


# ============================================================
# C. Fallback reasoner output
# ============================================================

class TestFallbackReasonerOutput:

    def test_fallback_is_non_empty(self):
        ctx    = _make_ctx(ticket_count=42, affected_customers=15)
        output = _fallback_reasoner_output(ctx)
        assert output.root_cause
        assert len(output.reasoning_steps) > 0
        assert len(output.evidence_items) > 0

    def test_fallback_revenue_reflects_ticket_count(self):
        ctx    = _make_ctx(ticket_count=100)
        output = _fallback_reasoner_output(ctx)
        assert output.revenue_impact == pytest.approx(100 * 70.0)

    def test_fallback_simulation_consistent(self):
        ctx    = _make_ctx(ticket_count=80)
        output = _fallback_reasoner_output(ctx)
        assert output.sim_before_count == 80
        assert output.sim_after_count <= output.sim_before_count


# ============================================================
# D. _build_investigation_out
# ============================================================

class TestBuildInvestigationOut:

    def _reasoner(self) -> ReasonerOutput:
        raw = _valid_reasoner_json()
        return _parse_reasoner_output(raw, _make_ctx())

    def _correlation(self, has_deploy: bool = True) -> CorrelationResult:
        return CorrelationResult(
            best_deploy       = _make_deploy() if has_deploy else None,
            correlation_score = 0.87 if has_deploy else 0.0,
            days_to_spike     = 2 if has_deploy else None,
        )

    def test_basic_fields_populated(self):
        ctx   = _make_ctx()
        out   = _build_investigation_out("AI-TEST01", ctx, self._reasoner(), self._correlation())
        assert out.id == "AI-TEST01"
        assert out.cluster_id == "CL-TEST01"
        assert out.root_cause
        assert 0 <= out.confidence <= 100
        assert out.impact_level in list(SeverityLevel)
        assert out.revenue_impact_usd > 0

    def test_deploy_correlation_populated(self):
        out = _build_investigation_out(
            "AI-T1", _make_ctx(), self._reasoner(), self._correlation(has_deploy=True)
        )
        assert out.deploy_correlation is not None
        assert out.deploy_correlation.deploy_id == "DEPLOY-001"
        assert out.deploy_correlation.version == "v2.4.1"
        assert 0 <= out.deploy_correlation.correlation <= 1.0

    def test_deploy_correlation_none_when_missing(self):
        out = _build_investigation_out(
            "AI-T2", _make_ctx(), self._reasoner(), self._correlation(has_deploy=False)
        )
        assert out.deploy_correlation is None

    def test_evidence_order_preserved(self):
        out = _build_investigation_out(
            "AI-T3", _make_ctx(), self._reasoner(), self._correlation()
        )
        orders = [e.sort_order for e in out.evidence]
        assert orders == sorted(orders)

    def test_simulation_fields_present(self):
        out = _build_investigation_out(
            "AI-T4", _make_ctx(), self._reasoner(), self._correlation()
        )
        assert out.simulation is not None
        assert out.simulation.before_ticket_count >= out.simulation.after_ticket_count
        assert 0 <= out.simulation.deflection_pct <= 100
        assert out.simulation.recovered_usd >= 0

    def test_model_version_set(self):
        out = _build_investigation_out(
            "AI-T5", _make_ctx(), self._reasoner(), self._correlation()
        )
        assert "fixloop" in out.model_version.lower()


# ============================================================
# E. Full run_investigation() pipeline
# ============================================================

class TestRunInvestigation:

    def _mock_supabase(
        self,
        cluster_exists: bool = True,
        junction_ids: list[int] | None = None,
        ticket_samples: list[dict] | None = None,
        cached_inv: dict | None = None,
    ):
        sb = AsyncMock()
        now = datetime.now(timezone.utc).isoformat()

        # Cluster row
        cluster_data = {
            "id": "CL-TEST01", "title": "Export Timeout",
            "summary": "Summary", "severity": "high",
            "ticket_count": 50, "affected_customers": 30,
            "monthly_cost_usd": 3500.0, "product_area": "Exports",
            "example_titles": ["Title 1"],
            "first_seen_at": "2026-05-10", "last_seen_at": "2026-05-22",
        } if cluster_exists else None

        sb.table.return_value.select.return_value.eq.return_value.single.return_value.execute = AsyncMock(
            return_value=MagicMock(data=cluster_data)
        )

        # Junction table
        jids = junction_ids or [1, 2, 3]
        sb.table.return_value.select.return_value.eq.return_value.limit.return_value.execute = AsyncMock(
            return_value=MagicMock(data=[{"ticket_id": i} for i in jids])
        )

        # Ticket samples
        samples = ticket_samples or [
            {"id": i, "title": f"Export fails {i}", "body": "Timeout error."}
            for i in range(1, 4)
        ]
        sb.table.return_value.select.return_value.in_.return_value.execute = AsyncMock(
            return_value=MagicMock(data=samples)
        )

        # Cached investigation check
        sb.table.return_value.select.return_value.eq.return_value.gte.return_value.gte.return_value.order.return_value.limit.return_value.execute = AsyncMock(
            return_value=MagicMock(data=[cached_inv] if cached_inv else [])
        )

        # Deployments
        sb.table.return_value.select.return_value.gte.return_value.order.return_value.execute = AsyncMock(
            return_value=MagicMock(data=[
                {"id": "D-1", "version": "v2.4.1", "title": "Release v2.4.1",
                 "deployed_at": "2026-05-08", "risk": "high", "notes": None}
            ])
        )

        # Upsert investigation + evidence
        sb.table.return_value.upsert.return_value.execute = AsyncMock(
            return_value=MagicMock(data=[{}])
        )

        return sb

    @pytest.mark.asyncio
    async def test_cluster_not_found_raises_value_error(self):
        mock_sb = self._mock_supabase(cluster_exists=False)
        with (
            patch("services.investigation.get_supabase", AsyncMock(return_value=mock_sb)),
            pytest.raises(ValueError, match="not found"),
        ):
            await run_investigation(InvestigateRequest(cluster_id="CL-GHOST"))

    @pytest.mark.asyncio
    async def test_full_pipeline_returns_investigation_out(self):
        mock_sb = self._mock_supabase()
        fake_reasoner = ReasonerOutput(
            root_cause         = "CSV export service fails above 500 rows.",
            confidence         = 92.0,
            impact_level       = "high",
            revenue_impact     = 35000.0,
            reasoning_steps    = ["Step 1", "Step 2"],
            evidence_items     = [
                {"type": "ticket_pattern", "title": "Timeout pattern",
                 "detail": "487 tickets.", "weight": 0.95},
            ],
            sim_deflection_pct = 80.0,
            sim_before_count   = 50,
            sim_after_count    = 10,
        )

        with (
            patch("services.investigation.get_supabase", AsyncMock(return_value=mock_sb)),
            patch("services.investigation._run_reasoner",
                  AsyncMock(return_value=fake_reasoner)),
            patch("services.investigation._fetch_existing_investigation",
                  AsyncMock(return_value=None)),
        ):
            result = await run_investigation(
                InvestigateRequest(cluster_id="CL-TEST01", force_refresh=True)
            )

        assert isinstance(result, InvestigationOut)
        assert result.cluster_id == "CL-TEST01"
        assert result.root_cause == "CSV export service fails above 500 rows."
        assert result.confidence == 92.0
        assert result.impact_level == SeverityLevel.HIGH
        assert result.revenue_impact_usd == 35000.0
        assert len(result.reasoning_steps) == 2
        assert len(result.evidence) == 1
        assert result.simulation is not None
        assert result.simulation.deflection_pct == 80.0

    @pytest.mark.asyncio
    async def test_cache_hit_skips_pipeline(self):
        """If a recent high-confidence investigation exists, pipeline should not run."""
        now = datetime.now(timezone.utc).isoformat()
        cached = InvestigationOut(
            id                 = "AI-CACHED",
            cluster_id         = "CL-TEST01",
            root_cause         = "Cached root cause",
            confidence         = 91.0,
            impact_level       = SeverityLevel.HIGH,
            affected_customers = 25,
            revenue_impact_usd = 28000.0,
            deploy_correlation = None,
            reasoning_steps    = ["Cached step"],
            evidence           = [],
            simulation         = None,
            model_version      = "fixloop-reasoner-v3",
            created_by         = None,
            approved_by        = None,
            approved_at        = None,
            created_at         = datetime.now(timezone.utc),
            updated_at         = datetime.now(timezone.utc),
        )

        with (
            patch("services.investigation._fetch_existing_investigation",
                  AsyncMock(return_value=cached)),
            patch("services.investigation._run_reasoner") as mock_reasoner,
        ):
            result = await run_investigation(
                InvestigateRequest(cluster_id="CL-TEST01", force_refresh=False)
            )

        mock_reasoner.assert_not_called()
        assert result.id == "AI-CACHED"

    @pytest.mark.asyncio
    async def test_force_refresh_bypasses_cache(self):
        """force_refresh=True must bypass the cache guard."""
        mock_sb = self._mock_supabase()
        fake_reasoner = ReasonerOutput(
            root_cause="Fresh analysis.", confidence=88.0,
            impact_level="medium", revenue_impact=10000.0,
            reasoning_steps=["Step"], evidence_items=[],
            sim_deflection_pct=70.0, sim_before_count=20, sim_after_count=6,
        )

        with (
            patch("services.investigation.get_supabase", AsyncMock(return_value=mock_sb)),
            patch("services.investigation._run_reasoner",
                  AsyncMock(return_value=fake_reasoner)),
            patch("services.investigation._fetch_existing_investigation") as mock_cache,
        ):
            await run_investigation(
                InvestigateRequest(cluster_id="CL-TEST01", force_refresh=True)
            )

        mock_cache.assert_not_called()


# ============================================================
# F. API endpoint tests
# ============================================================

class TestInvestigateEndpoints:

    @pytest.mark.asyncio
    async def test_post_investigate_missing_cluster_id(self, http_client: AsyncClient):
        response = await http_client.post("/ai/investigate", json={})
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_post_investigate_invalid_confidence(self, http_client: AsyncClient):
        response = await http_client.post("/ai/investigate", json={
            "cluster_id": "CL-1",
            "confidence_threshold": 2.0,   # > 1.0 — invalid
        })
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_post_investigate_cluster_not_found_returns_404(self, http_client: AsyncClient):
        with patch(
            "services.investigation.get_supabase",
            AsyncMock(return_value=self._mock_sb_cluster_none()),
        ):
            with patch(
                "services.investigation._fetch_existing_investigation",
                AsyncMock(return_value=None),
            ):
                response = await http_client.post("/ai/investigate", json={
                    "cluster_id":   "CL-NONEXISTENT",
                    "force_refresh": True,
                })

        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_post_investigate_valid_returns_200(self, http_client: AsyncClient):
        now = datetime.now(timezone.utc)
        fake_out = InvestigationOut(
            id="AI-XYZ123", cluster_id="CL-001",
            root_cause="Export service OOM above 500 rows.",
            confidence=93.5, impact_level=SeverityLevel.HIGH,
            affected_customers=120, revenue_impact_usd=40000.0,
            deploy_correlation=None, reasoning_steps=["Step 1"],
            evidence=[], simulation=None,
            model_version="fixloop-reasoner-v3",
            created_by=None, approved_by=None, approved_at=None,
            created_at=now, updated_at=now,
        )

        with patch(
            "agents.investigate_agent.run_investigation",
            AsyncMock(return_value=fake_out),
        ):
            response = await http_client.post("/ai/investigate", json={
                "cluster_id":   "CL-001",
                "force_refresh": True,
            })

        assert response.status_code == 200
        body = response.json()
        assert body["id"] == "AI-XYZ123"
        assert body["confidence"] == 93.5
        assert "root_cause" in body
        assert "reasoning_steps" in body
        assert "evidence" in body

    @pytest.mark.asyncio
    async def test_post_investigate_response_schema(self, http_client: AsyncClient):
        """All required InvestigationOut fields must be present."""
        now = datetime.now(timezone.utc)
        fake_out = InvestigationOut(
            id="AI-SCHEMA", cluster_id="CL-001",
            root_cause="Root cause here.", confidence=80.0,
            impact_level=SeverityLevel.MEDIUM, affected_customers=5,
            revenue_impact_usd=1000.0, deploy_correlation=None,
            reasoning_steps=[], evidence=[], simulation=None,
            model_version="fixloop-reasoner-v3",
            created_by=None, approved_by=None, approved_at=None,
            created_at=now, updated_at=now,
        )

        with patch(
            "agents.investigate_agent.run_investigation",
            AsyncMock(return_value=fake_out),
        ):
            response = await http_client.post("/ai/investigate", json={
                "cluster_id": "CL-001", "force_refresh": True
            })

        required_fields = {
            "id", "cluster_id", "root_cause", "confidence", "impact_level",
            "affected_customers", "revenue_impact_usd", "deploy_correlation",
            "reasoning_steps", "evidence", "simulation", "model_version",
            "created_at", "updated_at",
        }
        body = response.json()
        missing = required_fields - body.keys()
        assert not missing, f"Missing fields: {missing}"

    @pytest.mark.asyncio
    async def test_get_investigation_not_found(self, http_client: AsyncClient):
        mock_sb = AsyncMock()
        mock_sb.table.return_value.select.return_value.eq.return_value.single.return_value.execute = AsyncMock(
            return_value=MagicMock(data=None)
        )
        with patch("api.investigate.get_supabase", AsyncMock(return_value=mock_sb)):
            response = await http_client.get("/ai/investigate/AI-GHOST")
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_get_cluster_investigations_list(self, http_client: AsyncClient):
        mock_sb = AsyncMock()
        mock_sb.table.return_value.select.return_value.eq.return_value.order.return_value.limit.return_value.execute = AsyncMock(
            return_value=MagicMock(data=[])
        )
        with patch("api.investigate.get_supabase", AsyncMock(return_value=mock_sb)):
            response = await http_client.get("/ai/investigate/cluster/CL-001")
        assert response.status_code == 200
        assert response.json() == []

    # ---- helpers ----

    def _mock_sb_cluster_none(self):
        sb = AsyncMock()
        sb.table.return_value.select.return_value.eq.return_value.single.return_value.execute = AsyncMock(
            return_value=MagicMock(data=None)
        )
        sb.table.return_value.select.return_value.eq.return_value.gte.return_value.gte.return_value.order.return_value.limit.return_value.execute = AsyncMock(
            return_value=MagicMock(data=[])
        )
        sb.table.return_value.select.return_value.gte.return_value.order.return_value.execute = AsyncMock(
            return_value=MagicMock(data=[])
        )
        return sb
