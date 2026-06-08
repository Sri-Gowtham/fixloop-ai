"""
tests/test_clustering.py
------------------------
Unit + integration tests for the semantic clustering engine.

Test categories:
  A. Internal helpers (normalise, centroid, label parsing)
  B. HDBSCAN pipeline (mocked)
  C. LLM labelling (mocked OpenAI)
  D. Supabase writes (mocked)
  E. Full run_clustering() integration (all mocked)
  F. API endpoints
"""

from __future__ import annotations

import json
import math
from datetime import date, datetime, timezone
from typing import Optional
from unittest.mock import AsyncMock, MagicMock, patch

import numpy as np
import pytest
from httpx import ASGITransport, AsyncClient

from main import app
from models.cluster import (
    ClusterLabel,
    ClusterRecord,
    ClusterRequest,
    ClusteringResult,
    RawTicket,
)
from models.common import ItemStatus, SeverityLevel
from services.clustering import (
    _build_cluster_records,
    _compute_centroid,
    _count_affected_customers,
    _normalise,
    _parse_label_response,
    _pick_example_titles,
    run_clustering,
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


def _make_ticket(
    tid: int,
    title: str = "Test ticket",
    embedding: Optional[list[float]] = None,
    customer_id: Optional[str] = None,
) -> RawTicket:
    if embedding is None:
        rng = np.random.default_rng(tid)
        embedding = rng.normal(size=1536).tolist()
    return RawTicket(
        id          = tid,
        title       = title,
        body        = f"Body for {title}",
        embedding   = embedding,
        customer_id = customer_id or f"CUST-{tid:04d}",
        created_at  = "2026-05-01T10:00:00Z",
    )


def _fake_label(title: str = "Auth Issue") -> ClusterLabel:
    return ClusterLabel(
        title        = title,
        summary      = f"{title} summary.",
        severity     = SeverityLevel.HIGH,
        confidence   = 87.5,
        product_area = "Auth & SSO",
    )


def _make_cluster_record(ticket_ids: list[int]) -> ClusterRecord:
    tickets = [_make_ticket(i) for i in ticket_ids]
    return ClusterRecord(
        cluster_id         = f"CL-ABCD{ticket_ids[0]:04d}",
        label              = _fake_label(),
        ticket_ids         = ticket_ids,
        centroid           = _compute_centroid([t.embedding for t in tickets]),
        example_titles     = [t.title for t in tickets[:3]],
        affected_customers = len(ticket_ids),
        first_seen_at      = date(2026, 5, 1),
        last_seen_at       = date(2026, 5, 10),
    )


# ============================================================
# A. Internal helpers
# ============================================================

class TestInternalHelpers:

    def test_normalise_produces_unit_vectors(self):
        arr = np.random.default_rng(42).normal(size=(10, 16)).astype(np.float32)
        normed = _normalise(arr)
        norms = np.linalg.norm(normed, axis=1)
        np.testing.assert_allclose(norms, np.ones(10), atol=1e-5)

    def test_normalise_handles_zero_vector(self):
        arr = np.zeros((3, 8), dtype=np.float32)
        normed = _normalise(arr)
        # Should not crash; zero vectors stay zero
        assert normed.shape == (3, 8)

    def test_compute_centroid_shape(self):
        embeddings = [np.random.default_rng(i).normal(size=16).tolist() for i in range(5)]
        centroid = _compute_centroid(embeddings)
        assert len(centroid) == 16

    def test_compute_centroid_unit_norm(self):
        embeddings = [np.random.default_rng(i).normal(size=32).tolist() for i in range(4)]
        centroid = _compute_centroid(embeddings)
        norm = math.sqrt(sum(v ** 2 for v in centroid))
        assert abs(norm - 1.0) < 1e-4

    def test_compute_centroid_single_embedding(self):
        emb = [0.5] * 8
        centroid = _compute_centroid([emb])
        norm = math.sqrt(sum(v ** 2 for v in centroid))
        assert abs(norm - 1.0) < 1e-4

    def test_pick_example_titles_deduplicates(self):
        tickets = [_make_ticket(i, title="Same title") for i in range(5)]
        titles = _pick_example_titles(tickets, n=3)
        # All duplicates — should return exactly 1 unique title
        assert len(titles) == 1
        assert titles[0] == "Same title"

    def test_pick_example_titles_max_n(self):
        tickets = [_make_ticket(i, title=f"Title {i}") for i in range(10)]
        titles = _pick_example_titles(tickets, n=3)
        assert len(titles) == 3

    def test_count_affected_customers_distinct(self):
        tickets = [
            _make_ticket(1, customer_id="C-001"),
            _make_ticket(2, customer_id="C-001"),   # duplicate
            _make_ticket(3, customer_id="C-002"),
            _make_ticket(4, customer_id=None),      # None excluded
        ]
        count = _count_affected_customers(tickets)
        assert count == 2


# ============================================================
# B. _build_cluster_records
# ============================================================

class TestBuildClusterRecords:

    def _make_tickets_with_labels(self, assignments: list[int]) -> tuple:
        tickets = [_make_ticket(i) for i in range(len(assignments))]
        labels  = np.array(assignments, dtype=np.int32)
        return tickets, labels

    def test_noise_tickets_separated(self):
        tickets, labels = self._make_tickets_with_labels([-1, -1, 0, 0, 0])
        records, noise_ids = _build_cluster_records(tickets, labels)
        assert len(records) == 1
        assert len(noise_ids) == 2
        assert records[0].ticket_ids == [tickets[2].id, tickets[3].id, tickets[4].id]

    def test_multiple_clusters(self):
        tickets, labels = self._make_tickets_with_labels([0, 0, 1, 1, 1, -1])
        records, noise_ids = _build_cluster_records(tickets, labels)
        assert len(records) == 2
        assert len(noise_ids) == 1
        sizes = sorted(len(r.ticket_ids) for r in records)
        assert sizes == [2, 3]

    def test_all_noise(self):
        tickets, labels = self._make_tickets_with_labels([-1, -1, -1])
        records, noise_ids = _build_cluster_records(tickets, labels)
        assert len(records) == 0
        assert len(noise_ids) == 3

    def test_cluster_id_format(self):
        tickets, labels = self._make_tickets_with_labels([0, 0, 0])
        records, _ = _build_cluster_records(tickets, labels)
        assert records[0].cluster_id.startswith("CL-")
        assert len(records[0].cluster_id) > 3

    def test_centroid_is_unit_vector(self):
        tickets, labels = self._make_tickets_with_labels([0, 0, 0, 0])
        records, _ = _build_cluster_records(tickets, labels)
        norm = math.sqrt(sum(v ** 2 for v in records[0].centroid))
        assert abs(norm - 1.0) < 1e-4

    def test_example_titles_populated(self):
        tickets = [_make_ticket(i, title=f"Title {i}") for i in range(4)]
        labels  = np.zeros(4, dtype=np.int32)
        records, _ = _build_cluster_records(tickets, labels)
        assert len(records[0].example_titles) > 0


# ============================================================
# C. LLM label parsing
# ============================================================

class TestLabelParsing:

    def _valid_response(self, n: int) -> str:
        items = [
            {
                "title":        f"Issue {i}",
                "summary":      f"Summary for issue {i}.",
                "severity":     "high",
                "confidence":   85.0,
                "product_area": "Auth & SSO",
            }
            for i in range(n)
        ]
        return json.dumps(items)

    def test_parse_valid_array(self):
        raw = self._valid_response(3)
        labels = _parse_label_response(raw, 3)
        assert len(labels) == 3
        assert labels[0].title == "Issue 0"
        assert labels[0].severity == SeverityLevel.HIGH
        assert labels[0].confidence == 85.0

    def test_parse_wrapped_object(self):
        items = [{"title": "Auth Loop", "summary": "s", "severity": "critical", "confidence": 92.0}]
        raw = json.dumps({"clusters": items})
        labels = _parse_label_response(raw, 1)
        assert len(labels) == 1
        assert labels[0].title == "Auth Loop"

    def test_parse_markdown_fenced(self):
        items = [{"title": "T1", "summary": "s", "severity": "low", "confidence": 55.0}]
        raw = f"```json\n{json.dumps(items)}\n```"
        labels = _parse_label_response(raw, 1)
        assert len(labels) == 1

    def test_parse_invalid_json_returns_defaults(self):
        labels = _parse_label_response("not valid json!!!", 2)
        assert len(labels) == 2
        # Default label should have a non-empty title
        assert all(l.title for l in labels)

    def test_parse_pads_to_expected_count(self):
        """If LLM returns fewer items than clusters, pad with defaults."""
        raw = self._valid_response(1)
        labels = _parse_label_response(raw, 3)
        assert len(labels) == 3

    def test_parse_unknown_severity_defaults_to_medium(self):
        items = [{"title": "T", "summary": "s", "severity": "not_a_severity", "confidence": 70.0}]
        labels = _parse_label_response(json.dumps(items), 1)
        assert labels[0].severity == SeverityLevel.MEDIUM

    def test_parse_confidence_clamped(self):
        items = [{"title": "T", "summary": "s", "severity": "high", "confidence": 150.0}]
        labels = _parse_label_response(json.dumps(items), 1)
        assert labels[0].confidence == 100.0


# ============================================================
# D. Database write helpers (mocked)
# ============================================================

class TestDatabaseWrites:

    @pytest.mark.asyncio
    async def test_upsert_clusters_called(self):
        from services.clustering import _upsert_clusters
        records = [_make_cluster_record([1, 2, 3])]

        mock_sb = AsyncMock()
        mock_sb.table.return_value.upsert.return_value.execute = AsyncMock(
            return_value=MagicMock(data=[{"id": records[0].cluster_id}])
        )

        with patch("services.clustering.get_supabase", AsyncMock(return_value=mock_sb)):
            result = await _upsert_clusters(records)

        mock_sb.table.assert_called_with("ticket_clusters")
        assert isinstance(result, list)

    @pytest.mark.asyncio
    async def test_insert_cluster_tickets_called(self):
        from services.clustering import _insert_cluster_tickets
        records = [_make_cluster_record([10, 11, 12])]

        mock_sb = AsyncMock()
        mock_sb.table.return_value.upsert.return_value.execute = AsyncMock(
            return_value=MagicMock(data=[{}])
        )

        with patch("services.clustering.get_supabase", AsyncMock(return_value=mock_sb)):
            count = await _insert_cluster_tickets(records)

        assert count == 3  # 3 tickets in the cluster


# ============================================================
# E. Full run_clustering() integration (all mocked)
# ============================================================

class TestRunClustering:

    def _make_mock_supabase(self, tickets: list[RawTicket]):
        """Build a mock Supabase client that returns the given tickets."""
        mock_sb = AsyncMock()

        # Chain: .table().select().not_.is_().limit().execute()
        mock_select_chain = AsyncMock()
        mock_select_chain.execute = AsyncMock(return_value=MagicMock(
            data=[
                {
                    "id":          t.id,
                    "title":       t.title,
                    "body":        t.body,
                    "embedding":   t.embedding,
                    "customer_id": t.customer_id,
                    "severity":    t.severity,
                    "created_at":  t.created_at,
                }
                for t in tickets
            ]
        ))

        # Make the fluent chain work
        mock_sb.table.return_value.select.return_value.not_.is_.return_value.limit.return_value = mock_select_chain
        mock_sb.table.return_value.select.return_value.not_.is_.return_value.in_.return_value.limit.return_value = mock_select_chain

        # Upserts / inserts
        mock_sb.table.return_value.upsert.return_value.execute = AsyncMock(
            return_value=MagicMock(data=[{}])
        )

        return mock_sb

    @pytest.mark.asyncio
    async def test_no_tickets_returns_empty_result(self):
        mock_sb = AsyncMock()
        mock_sb.table.return_value.select.return_value.not_.is_.return_value.limit.return_value.execute = AsyncMock(
            return_value=MagicMock(data=[])
        )

        with patch("services.clustering.get_supabase", AsyncMock(return_value=mock_sb)):
            result = await run_clustering(ClusterRequest())

        assert result.cluster_count == 0
        assert result.clustered_tickets == 0
        assert result.noise_tickets == 0
        assert result.clusters == []

    @pytest.mark.asyncio
    async def test_dry_run_skips_db_writes(self):
        """dry_run=True should skip all Supabase upserts."""
        rng = np.random.default_rng(42)
        # 10 tickets split into 2 obvious clusters
        cluster_a = [rng.normal(loc=1.0, size=8).tolist() for _ in range(5)]
        cluster_b = [rng.normal(loc=-1.0, size=8).tolist() for _ in range(5)]
        tickets = [
            _make_ticket(i, title=f"Auth ticket {i}", embedding=cluster_a[i])
            for i in range(5)
        ] + [
            _make_ticket(10 + i, title=f"Export ticket {i}", embedding=cluster_b[i])
            for i in range(5)
        ]

        # Pad embeddings to 1536 dims for realistic behaviour
        for t in tickets:
            t.embedding = (t.embedding * (1536 // len(t.embedding) + 1))[:1536]

        mock_sb = self._make_mock_supabase(tickets)
        fake_labels = [
            ClusterLabel("Auth Loop", "Auth issues.", SeverityLevel.HIGH, 88.0, "Auth & SSO"),
            ClusterLabel("Export Fail", "Export issues.", SeverityLevel.CRITICAL, 94.0, "Exports & Reports"),
        ]

        with (
            patch("services.clustering.get_supabase", AsyncMock(return_value=mock_sb)),
            patch("services.clustering._label_clusters", AsyncMock(return_value=fake_labels)),
        ):
            result = await run_clustering(ClusterRequest(dry_run=True))

        # No upserts should have been called
        mock_sb.table.return_value.upsert.assert_not_called()
        assert isinstance(result, ClusteringResult)

    @pytest.mark.asyncio
    async def test_clustering_result_schema(self):
        """ClusteringResult must have correct field types."""
        result = ClusteringResult(
            cluster_count     = 2,
            clustered_tickets = 8,
            noise_tickets     = 2,
            clusters          = [],
        )
        assert result.cluster_count == 2
        assert result.clustered_tickets == 8
        assert result.noise_tickets == 2
        assert isinstance(result.clusters, list)


# ============================================================
# F. API endpoint tests
# ============================================================

class TestClusterEndpoints:

    @pytest.mark.asyncio
    async def test_post_cluster_invalid_min_cluster_size(self, http_client: AsyncClient):
        """min_cluster_size < 2 should fail validation."""
        response = await http_client.post("/ai/cluster", json={
            "min_cluster_size": 1,
        })
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_post_cluster_dry_run_no_tickets(self, http_client: AsyncClient):
        """Dry run with no available tickets should return empty result."""
        mock_sb = AsyncMock()
        mock_sb.table.return_value.select.return_value.not_.is_.return_value.limit.return_value.execute = AsyncMock(
            return_value=MagicMock(data=[])
        )

        with patch("services.clustering.get_supabase", AsyncMock(return_value=mock_sb)):
            response = await http_client.post("/ai/cluster", json={
                "process_all": False,
                "dry_run":     True,
            })

        assert response.status_code == 200
        body = response.json()
        assert body["cluster_count"] == 0
        assert body["clustered_tickets"] == 0
        assert body["noise_tickets"] == 0
        assert body["clusters"] == []

    @pytest.mark.asyncio
    async def test_post_cluster_response_schema(self, http_client: AsyncClient):
        """Response must contain all required ClusteringResult fields."""
        mock_sb = AsyncMock()
        mock_sb.table.return_value.select.return_value.not_.is_.return_value.limit.return_value.execute = AsyncMock(
            return_value=MagicMock(data=[])
        )

        with patch("services.clustering.get_supabase", AsyncMock(return_value=mock_sb)):
            response = await http_client.post("/ai/cluster", json={"dry_run": True})

        assert response.status_code == 200
        body = response.json()
        required_fields = {"cluster_count", "clustered_tickets", "noise_tickets", "clusters"}
        assert required_fields.issubset(body.keys()), (
            f"Missing: {required_fields - body.keys()}"
        )

    @pytest.mark.asyncio
    async def test_get_clusters_list(self, http_client: AsyncClient):
        """GET /ai/cluster should return a list."""
        mock_sb = AsyncMock()
        mock_sb.table.return_value.select.return_value.order.return_value.range.return_value.execute = AsyncMock(
            return_value=MagicMock(data=[])
        )

        with patch("services.clustering.get_supabase", AsyncMock(return_value=mock_sb)):
            # Direct DB mock for the list endpoint
            with patch("api.cluster.get_supabase", AsyncMock(return_value=mock_sb)):
                response = await http_client.get("/ai/cluster")

        assert response.status_code == 200
        assert isinstance(response.json(), list)

    @pytest.mark.asyncio
    async def test_get_cluster_not_found(self, http_client: AsyncClient):
        """GET /ai/cluster/{id} with nonexistent ID should return 404."""
        mock_sb = AsyncMock()
        mock_sb.table.return_value.select.return_value.eq.return_value.single.return_value.execute = AsyncMock(
            return_value=MagicMock(data=None)
        )

        with patch("api.cluster.get_supabase", AsyncMock(return_value=mock_sb)):
            response = await http_client.get("/ai/cluster/CL-NONEXIST")

        assert response.status_code == 404
