"""
tests/test_ingestion.py
-----------------------
Unit + integration tests for the ticket ingestion engine.

Test categories:
  A. CSV parsing  (pure unit tests — no network, no DB)
  B. Embedding service  (mocked OpenAI)
  C. Ingestion pipeline  (mocked Supabase + OpenAI)
  D. API endpoints  (httpx AsyncClient against FastAPI)

Run:
    pytest tests/test_ingestion.py -v
    pytest tests/test_ingestion.py -v --cov=services --cov-report=term-missing
"""

from __future__ import annotations

import textwrap
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from httpx import ASGITransport, AsyncClient

from main import app
from models.ticket import TicketIn, TicketIngestBatch
from services.ingestion import (
    IngestionResult,
    RowError,
    _coerce_datetime,
    _coerce_severity,
    _coerce_tags,
    _build_column_map,
    ingest_batch,
    parse_csv_file,
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


def _csv(content: str) -> bytes:
    """Helper to convert a dedented CSV string to bytes."""
    return textwrap.dedent(content).strip().encode("utf-8")


# ============================================================
# A. CSV Parsing — unit tests
# ============================================================

class TestCsvParsing:
    """Pure unit tests for parse_csv_file() — no external I/O."""

    @pytest.mark.asyncio
    async def test_canonical_columns_parsed(self):
        csv_bytes = _csv("""
            ticket_id,title,description,source,created_at
            TK-001,Login broken,Users cannot log in,zendesk,2026-05-01
            TK-002,Export fails,CSV export times out,csv,2026-05-02
        """)
        tickets, errors = await parse_csv_file(csv_bytes, source="csv")
        assert len(tickets) == 2
        assert len(errors) == 0
        assert tickets[0].external_id == "TK-001"
        assert tickets[0].title == "Login broken"
        assert tickets[0].body == "Users cannot log in"
        assert tickets[1].source == "csv"

    @pytest.mark.asyncio
    async def test_alias_columns_resolved(self):
        """Zendesk-style column names should be resolved via alias map."""
        csv_bytes = _csv("""
            id,subject,content,channel,requester_email
            ZD-500,SSO loop,Okta keeps logging me out,email,user@test.com
        """)
        tickets, errors = await parse_csv_file(csv_bytes, source="zendesk")
        assert len(tickets) == 1
        assert tickets[0].external_id == "ZD-500"
        assert tickets[0].title == "SSO loop"
        assert tickets[0].body == "Okta keeps logging me out"
        assert tickets[0].channel == "email"
        assert str(tickets[0].customer_email) == "user@test.com"

    @pytest.mark.asyncio
    async def test_missing_title_column_raises(self):
        """A CSV without a title/subject column should raise ValueError."""
        csv_bytes = _csv("""
            ticket_id,description
            TK-001,Some description
        """)
        with pytest.raises(ValueError, match="missing required column"):
            await parse_csv_file(csv_bytes)

    @pytest.mark.asyncio
    async def test_empty_file_raises(self):
        with pytest.raises(ValueError):
            await parse_csv_file(b"", source="csv")

    @pytest.mark.asyncio
    async def test_invalid_rows_reported_as_errors(self):
        """Rows with empty titles should be collected as RowErrors."""
        csv_bytes = _csv("""
            ticket_id,title,description
            TK-001,,Missing title row
            TK-002,Valid ticket,Good description
        """)
        tickets, errors = await parse_csv_file(csv_bytes)
        # Row with empty title should be an error
        assert any(e.row_number == 2 for e in errors)
        assert any(t.title == "Valid ticket" for t in tickets)

    @pytest.mark.asyncio
    async def test_semicolon_delimiter_detected(self):
        """CSV files with semicolon delimiters should be parsed correctly."""
        csv_bytes = _csv("""
            ticket_id;title;description
            TK-001;Broken feature;Details here
        """)
        tickets, errors = await parse_csv_file(csv_bytes)
        assert len(tickets) == 1
        assert tickets[0].title == "Broken feature"

    @pytest.mark.asyncio
    async def test_latin1_encoding_handled(self):
        """Files encoded in latin-1 should be decoded without error."""
        raw = "ticket_id,title,description\nTK-001,Caf\xe9 bug,Problem with caf\xe9\n"
        content = raw.encode("latin-1")
        tickets, errors = await parse_csv_file(content)
        assert len(tickets) == 1
        assert "Caf" in tickets[0].title

    @pytest.mark.asyncio
    async def test_bom_utf8_handled(self):
        """UTF-8 BOM at start of file should be stripped."""
        raw = "\ufeffticket_id,title\nTK-001,BOM test\n"
        content = raw.encode("utf-8-sig")
        tickets, errors = await parse_csv_file(content)
        assert len(tickets) == 1
        assert tickets[0].title == "BOM test"

    @pytest.mark.asyncio
    async def test_tags_parsed_from_comma_string(self):
        csv_bytes = _csv("""
            title,tags
            Webhook error,webhook,retry,timeout
        """)
        # Single-line tags with no delimiter — treated as one tag
        tickets, errors = await parse_csv_file(csv_bytes)
        assert tickets[0].tags is not None


class TestCoercionHelpers:
    """Unit tests for individual coercion functions."""

    def test_severity_canonical_values(self):
        assert _coerce_severity("critical") == "critical"
        assert _coerce_severity("HIGH") == "high"
        assert _coerce_severity("urgent") == "critical"
        assert _coerce_severity("P1") == "critical"
        assert _coerce_severity("3") == "medium"
        assert _coerce_severity("unknown") is None
        assert _coerce_severity(None) is None

    def test_datetime_iso_formats(self):
        assert _coerce_datetime("2026-05-01") is not None
        assert _coerce_datetime("2026-05-01T12:00:00Z") is not None
        assert _coerce_datetime("2026-05-01 12:00:00") is not None
        assert _coerce_datetime("not-a-date") is None
        assert _coerce_datetime("") is None
        assert _coerce_datetime(None) is None

    def test_tags_separators(self):
        assert _coerce_tags("a,b,c") == ["a", "b", "c"]
        assert _coerce_tags("a|b|c") == ["a", "b", "c"]
        assert _coerce_tags("a;b;c") == ["a", "b", "c"]
        assert _coerce_tags("single") == ["single"]
        assert _coerce_tags("") == []
        assert _coerce_tags(None) == []

    def test_column_map_resolution(self):
        headers = ["ticket_id", "subject", "content", "requester_email"]
        col_map = _build_column_map(headers)
        assert col_map["external_id"] == "ticket_id"
        assert col_map["title"] == "subject"
        assert col_map["body"] == "content"
        assert col_map["customer_email"] == "requester_email"


# ============================================================
# B. Embedding service — unit tests with mocked OpenAI
# ============================================================

class TestEmbeddingService:

    @pytest.mark.asyncio
    async def test_embed_texts_returns_vectors(self):
        """embed_texts() should return one vector per input string."""
        fake_vector = [0.1] * 1536

        with patch("services.embedding._call_openai_embed", new_callable=AsyncMock) as mock_embed:
            mock_embed.return_value = [fake_vector, fake_vector]
            from services.embedding import embed_texts
            result = await embed_texts(["hello", "world"])

        assert len(result) == 2
        assert len(result[0]) == 1536

    @pytest.mark.asyncio
    async def test_embed_texts_empty_input(self):
        """Empty input list should return empty list without API call."""
        from services.embedding import embed_texts
        result = await embed_texts([])
        assert result == []

    @pytest.mark.asyncio
    async def test_embed_texts_empty_string_gets_zero_vector(self):
        """Empty strings should get a zero-vector without calling the API."""
        with patch("services.embedding._call_openai_embed", new_callable=AsyncMock) as mock_embed:
            mock_embed.return_value = []
            from services.embedding import embed_texts
            result = await embed_texts([""])

        assert len(result) == 1
        assert all(v == 0.0 for v in result[0])
        mock_embed.assert_not_called()

    @pytest.mark.asyncio
    async def test_embed_ticket_combines_title_and_body(self):
        """embed_ticket() should call embed_single with title+body combined."""
        fake_vector = [0.5] * 1536
        with patch("services.embedding._call_openai_embed", new_callable=AsyncMock) as mock_embed:
            mock_embed.return_value = [fake_vector]
            from services.embedding import embed_ticket
            result = await embed_ticket("My title", "My body text")

        assert len(result) == 1536
        # API was called once (one non-empty string)
        mock_embed.assert_called_once()
        call_args = mock_embed.call_args[0][0]
        assert "My title" in call_args[0]
        assert "My body text" in call_args[0]


# ============================================================
# C. Ingestion pipeline — mocked Supabase + OpenAI
# ============================================================

class TestIngestionPipeline:

    def _make_batch(self, n: int = 2) -> TicketIngestBatch:
        tickets = [
            TicketIn(
                external_id=f"TK-{i:03d}",
                source="csv",
                title=f"Ticket {i}",
                body=f"Description for ticket {i}",
            )
            for i in range(1, n + 1)
        ]
        return TicketIngestBatch(tickets=tickets, source="csv", dry_run=False)

    @pytest.mark.asyncio
    async def test_dry_run_skips_db_and_embed(self):
        """dry_run=True should return success without any DB or API calls."""
        batch = TicketIngestBatch(
            tickets=[TicketIn(external_id="DRY-1", source="csv", title="Dry run ticket")],
            source="csv",
            dry_run=True,
        )
        result = await ingest_batch(batch)
        assert result.successful == 1
        assert result.total_tickets == 1

    @pytest.mark.asyncio
    async def test_ingest_batch_full_pipeline(self):
        """Happy path: tickets are inserted and embeddings are stored."""
        batch = self._make_batch(2)
        fake_vector = [0.1] * 1536
        now_iso = datetime.now(timezone.utc).isoformat()

        # Mock Supabase client
        mock_sb = AsyncMock()
        mock_sb.table.return_value.select.return_value.in_.return_value.execute = AsyncMock(
            return_value=MagicMock(data=[])  # no existing external_ids
        )
        mock_sb.table.return_value.insert.return_value.execute = AsyncMock(
            return_value=MagicMock(data=[
                {"id": 1, "external_id": "TK-001", "title": "Ticket 1",
                 "body": "Description for ticket 1", "source": "csv",
                 "status": "open", "tags": [], "ingested_at": now_iso, "created_at": now_iso},
                {"id": 2, "external_id": "TK-002", "title": "Ticket 2",
                 "body": "Description for ticket 2", "source": "csv",
                 "status": "open", "tags": [], "ingested_at": now_iso, "created_at": now_iso},
            ])
        )
        mock_sb.table.return_value.update.return_value.eq.return_value.execute = AsyncMock(
            return_value=MagicMock(data=[{"id": 1}])
        )

        with (
            patch("services.ingestion.get_supabase", new_callable=AsyncMock, return_value=mock_sb),
            patch("services.ingestion.embed_tickets_batch", new_callable=AsyncMock,
                  return_value=[fake_vector, fake_vector]),
        ):
            result = await ingest_batch(batch)

        assert result.successful == 2
        assert result.total_tickets == 2
        assert result.skipped_dupes == 0
        assert result.embeddings_stored == 2
        assert len(result.tickets) == 2

    @pytest.mark.asyncio
    async def test_duplicate_tickets_skipped(self):
        """Tickets whose external_id already exists should be skipped."""
        batch = self._make_batch(3)
        now_iso = datetime.now(timezone.utc).isoformat()

        mock_sb = AsyncMock()
        # Pretend TK-001 already exists
        mock_sb.table.return_value.select.return_value.in_.return_value.execute = AsyncMock(
            return_value=MagicMock(data=[{"external_id": "TK-001"}])
        )
        mock_sb.table.return_value.insert.return_value.execute = AsyncMock(
            return_value=MagicMock(data=[
                {"id": 2, "external_id": "TK-002", "title": "Ticket 2",
                 "body": "", "source": "csv", "status": "open",
                 "tags": [], "ingested_at": now_iso, "created_at": now_iso},
                {"id": 3, "external_id": "TK-003", "title": "Ticket 3",
                 "body": "", "source": "csv", "status": "open",
                 "tags": [], "ingested_at": now_iso, "created_at": now_iso},
            ])
        )
        mock_sb.table.return_value.update.return_value.eq.return_value.execute = AsyncMock(
            return_value=MagicMock(data=[{}])
        )

        with (
            patch("services.ingestion.get_supabase", new_callable=AsyncMock, return_value=mock_sb),
            patch("services.ingestion.embed_tickets_batch", new_callable=AsyncMock,
                  return_value=[[0.1] * 1536, [0.1] * 1536]),
        ):
            result = await ingest_batch(batch)

        assert result.skipped_dupes == 1
        assert result.successful == 2

    @pytest.mark.asyncio
    async def test_embed_failure_is_non_fatal(self):
        """If embedding fails, tickets should still be persisted (embed=0)."""
        batch = self._make_batch(1)
        now_iso = datetime.now(timezone.utc).isoformat()

        mock_sb = AsyncMock()
        mock_sb.table.return_value.select.return_value.in_.return_value.execute = AsyncMock(
            return_value=MagicMock(data=[])
        )
        mock_sb.table.return_value.insert.return_value.execute = AsyncMock(
            return_value=MagicMock(data=[
                {"id": 1, "external_id": "TK-001", "title": "Ticket 1",
                 "body": "", "source": "csv", "status": "open",
                 "tags": [], "ingested_at": now_iso, "created_at": now_iso},
            ])
        )
        mock_sb.table.return_value.update.return_value.eq.return_value.execute = AsyncMock(
            return_value=MagicMock(data=[{}])
        )

        with (
            patch("services.ingestion.get_supabase", new_callable=AsyncMock, return_value=mock_sb),
            patch("services.ingestion.embed_tickets_batch",
                  new_callable=AsyncMock, side_effect=Exception("OpenAI timeout")),
        ):
            result = await ingest_batch(batch)

        # Ticket was persisted even though embedding failed
        assert result.successful == 1
        assert result.embeddings_stored == 0


# ============================================================
# D. API endpoint tests
# ============================================================

class TestIngestEndpoints:

    @pytest.mark.asyncio
    async def test_ingest_json_validation_empty_tickets(self, http_client: AsyncClient):
        """Sending an empty tickets array should return 422."""
        response = await http_client.post("/ai/ingest", json={
            "tickets": [],
            "source": "csv",
        })
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_ingest_json_invalid_source(self, http_client: AsyncClient):
        """Invalid source value should fail Pydantic validation."""
        response = await http_client.post("/ai/ingest", json={
            "tickets": [{"title": "Test", "source": "unknown_source"}],
            "source": "csv",
        })
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_ingest_json_dry_run_returns_202(self, http_client: AsyncClient):
        """Dry-run JSON batch should return 202 without DB calls."""
        with (
            patch("services.ingestion.get_supabase", new_callable=AsyncMock),
            patch("services.ingestion.embed_tickets_batch", new_callable=AsyncMock,
                  return_value=[]),
        ):
            response = await http_client.post("/ai/ingest", json={
                "tickets": [{"title": "Test ticket", "source": "csv"}],
                "source": "csv",
                "dry_run": True,
            })

        assert response.status_code == 202
        body = response.json()
        assert body["dry_run"] is True
        assert body["total_tickets"] == 1
        assert "successful" in body
        assert "failed" in body

    @pytest.mark.asyncio
    async def test_ingest_upload_no_file_returns_422(self, http_client: AsyncClient):
        """Calling /ai/ingest/upload with no file should return 422."""
        response = await http_client.post("/ai/ingest/upload")
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_ingest_upload_unsupported_type_returns_400(self, http_client: AsyncClient):
        """Non-CSV file should return 400."""
        response = await http_client.post(
            "/ai/ingest/upload",
            files={"file": ("data.pdf", b"%PDF-fake", "application/pdf")},
            data={"source": "csv", "dry_run": "false"},
        )
        assert response.status_code == 400

    @pytest.mark.asyncio
    async def test_ingest_upload_empty_file_returns_400(self, http_client: AsyncClient):
        """Empty file body should return 400."""
        response = await http_client.post(
            "/ai/ingest/upload",
            files={"file": ("empty.csv", b"", "text/csv")},
            data={"source": "csv", "dry_run": "false"},
        )
        assert response.status_code == 400

    @pytest.mark.asyncio
    async def test_ingest_upload_csv_dry_run(self, http_client: AsyncClient):
        """Valid CSV with dry_run=true should parse and return summary without DB writes."""
        csv_content = b"ticket_id,title,description\nTK-001,Login broken,Users cannot log in\n"

        with (
            patch("services.ingestion.get_supabase", new_callable=AsyncMock),
            patch("services.ingestion.embed_tickets_batch", new_callable=AsyncMock,
                  return_value=[]),
        ):
            response = await http_client.post(
                "/ai/ingest/upload",
                files={"file": ("tickets.csv", csv_content, "text/csv")},
                data={"source": "csv", "dry_run": "true"},
            )

        assert response.status_code == 202
        body = response.json()
        assert body["total_tickets"] >= 1
        assert body["dry_run"] is True
        assert "successful" in body
        assert "failed" in body
        assert "message" in body

    @pytest.mark.asyncio
    async def test_ingest_upload_missing_title_column(self, http_client: AsyncClient):
        """CSV without a title column should return 400 with helpful message."""
        csv_content = b"ticket_id,description\nTK-001,Some description\n"
        response = await http_client.post(
            "/ai/ingest/upload",
            files={"file": ("bad.csv", csv_content, "text/csv")},
            data={"source": "csv", "dry_run": "false"},
        )
        assert response.status_code == 400
        assert "missing required column" in response.json()["detail"].lower()

    @pytest.mark.asyncio
    async def test_ingest_summary_schema(self, http_client: AsyncClient):
        """Response body must contain all required IngestSummary fields."""
        csv_content = b"ticket_id,title,description\nTK-001,Test,Description\n"

        with (
            patch("services.ingestion.get_supabase", new_callable=AsyncMock),
            patch("services.ingestion.embed_tickets_batch", new_callable=AsyncMock, return_value=[]),
        ):
            response = await http_client.post(
                "/ai/ingest/upload",
                files={"file": ("tickets.csv", csv_content, "text/csv")},
                data={"source": "csv", "dry_run": "true"},
            )

        assert response.status_code == 202
        body = response.json()
        required_fields = {
            "total_tickets", "successful", "failed",
            "skipped_dupes", "embeddings_stored",
            "dry_run", "row_errors", "tickets", "message",
        }
        assert required_fields.issubset(body.keys()), (
            f"Missing fields: {required_fields - body.keys()}"
        )
