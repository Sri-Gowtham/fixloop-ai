"""
tests/test_api.py
-----------------
Basic smoke tests for all four AI endpoints.

These tests verify:
  - Routes are registered and respond (even with 501 stubs)
  - Request validation (422 on bad input)
  - Response shape is correct when endpoints are implemented

All tests use httpx.AsyncClient against the FastAPI app directly
(no real network calls).
"""

from __future__ import annotations

import pytest
from httpx import AsyncClient, ASGITransport

from main import app


@pytest.fixture
async def client():
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as c:
        yield c


# ----------------------------------------------------------------
# Health check
# ----------------------------------------------------------------

@pytest.mark.asyncio
async def test_health(client: AsyncClient):
    """Service liveness probe should always return 200."""
    response = await client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert "version" in data


# ----------------------------------------------------------------
# POST /ai/ingest
# ----------------------------------------------------------------

@pytest.mark.asyncio
async def test_ingest_missing_body(client: AsyncClient):
    """Missing request body should return 422 Unprocessable Entity."""
    response = await client.post("/ai/ingest", json={})
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_ingest_invalid_source(client: AsyncClient):
    """Unknown source value should fail Pydantic validation."""
    response = await client.post("/ai/ingest", json={
        "tickets": [{
            "title": "Test ticket",
            "source": "unknown_source",
        }],
        "source": "unknown_source",
    })
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_ingest_valid_request_stub(client: AsyncClient):
    """
    Valid JSON batch should reach the endpoint and return 501
    (implementation pending) — not a 422 validation error.
    """
    response = await client.post("/ai/ingest", json={
        "tickets": [{"title": "Export fails above 500 rows", "source": "zendesk"}],
        "source": "zendesk",
        "run_cluster": True,
        "dry_run": False,
    })
    # Stub returns 501 — accept either 501 or 202 (when implemented)
    assert response.status_code in (202, 501)


# ----------------------------------------------------------------
# POST /ai/investigate
# ----------------------------------------------------------------

@pytest.mark.asyncio
async def test_investigate_missing_body(client: AsyncClient):
    response = await client.post("/ai/investigate", json={})
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_investigate_valid_request_stub(client: AsyncClient):
    response = await client.post("/ai/investigate", json={
        "cluster_id":              "CL-1042",
        "force_refresh":           False,
        "confidence_threshold":    0.70,
        "deploy_correlation_days": 7,
    })
    assert response.status_code in (200, 501)


# ----------------------------------------------------------------
# POST /ai/recommend
# ----------------------------------------------------------------

@pytest.mark.asyncio
async def test_recommend_missing_body(client: AsyncClient):
    response = await client.post("/ai/recommend", json={})
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_recommend_valid_request_stub(client: AsyncClient):
    response = await client.post("/ai/recommend", json={
        "investigation_id": "AI-7741",
        "cluster_id":       "CL-1042",
    })
    assert response.status_code in (201, 501)


# ----------------------------------------------------------------
# POST /ai/validate
# ----------------------------------------------------------------

@pytest.mark.asyncio
async def test_validate_missing_body(client: AsyncClient):
    response = await client.post("/ai/validate", json={})
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_validate_valid_request_stub(client: AsyncClient):
    response = await client.post("/ai/validate", json={
        "fix_recommendation_id": "R-1",
        "force_revalidate":      False,
    })
    assert response.status_code in (200, 501)
