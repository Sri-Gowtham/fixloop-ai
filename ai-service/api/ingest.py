"""
api/ingest.py
-------------
POST /ai/ingest          — JSON batch ingestion
POST /ai/ingest/upload   — CSV file upload ingestion

Both endpoints return an IngestSummary:
    {
        "total_tickets":  <int>,
        "successful":     <int>,
        "failed":         <int>,
        "skipped_dupes":  <int>,
        "embeddings_stored": <int>,
        "dry_run":        <bool>,
        "row_errors":     [...],
        "tickets":        [...],
        "message":        "..."
    }
"""

from __future__ import annotations

import structlog
from fastapi import APIRouter, File, Form, HTTPException, UploadFile, status
from pydantic import BaseModel, Field

from models.common import ItemStatus
from models.ticket import TicketIn, TicketIngestBatch, TicketOut
from services.ingestion import (
    IngestionResult,
    RowError,
    ingest_batch,
    parse_csv_file,
)

logger = structlog.get_logger(__name__)
router = APIRouter()


# ============================================================
# Response / error schemas
# ============================================================

class RowErrorOut(BaseModel):
    """Single failed CSV row reported in the response."""
    row_number: int
    error:      str
    raw_data:   dict = Field(default_factory=dict)


class IngestSummary(BaseModel):
    """
    Unified ingestion response returned by both endpoints.

    total_tickets   = rows presented for ingestion (after CSV parse)
    successful      = rows persisted to the database
    failed          = rows that could not be persisted (DB / validation error)
    skipped_dupes   = rows skipped because external_id already exists
    embeddings_stored = tickets that received an embedding vector
    """
    total_tickets:     int             = Field(..., description="Rows presented for ingestion")
    successful:        int             = Field(..., description="Rows persisted to Supabase")
    failed:            int             = Field(..., description="Rows that errored during insert")
    skipped_dupes:     int             = Field(0,   description="Duplicates skipped by external_id")
    embeddings_stored: int             = Field(0,   description="Tickets that received an embedding")
    dry_run:           bool            = Field(False)
    row_errors:        list[RowErrorOut] = Field(default_factory=list,
                                                 description="Parse/validation errors (non-fatal)")
    tickets:           list[TicketOut]   = Field(default_factory=list,
                                                 description="Persisted ticket stubs")
    message:           str             = Field("Ingestion complete")


# ============================================================
# Helpers
# ============================================================

def _result_to_summary(
    result: IngestionResult,
    parse_errors: list[RowError] | None = None,
    dry_run: bool = False,
) -> IngestSummary:
    """Convert an IngestionResult (internal) → IngestSummary (API response)."""
    all_errors = list(result.row_errors) + (parse_errors or [])
    failed = result.failed + len(parse_errors or [])

    return IngestSummary(
        total_tickets     = result.total_tickets + len(parse_errors or []),
        successful        = result.successful,
        failed            = failed,
        skipped_dupes     = result.skipped_dupes,
        embeddings_stored = result.embeddings_stored,
        dry_run           = dry_run,
        row_errors        = [
            RowErrorOut(
                row_number = e.row_number,
                error      = e.error,
                raw_data   = {k: str(v) for k, v in (e.raw_data or {}).items()},
            )
            for e in all_errors
        ],
        tickets = result.tickets,
        message = (
            "Dry run complete — no data written."
            if dry_run
            else f"Ingested {result.successful} ticket(s). "
                 f"{result.embeddings_stored} embedding(s) stored."
        ),
    )


# ============================================================
# POST /ai/ingest  —  JSON batch
# ============================================================

@router.post(
    "/ingest",
    response_model=IngestSummary,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Ingest tickets (JSON batch)",
    description=(
        "Accepts a batch of support tickets as a JSON array. "
        "Each ticket is validated, deduplicated by `external_id`, "
        "persisted to Supabase, and embedded via OpenAI "
        "`text-embedding-3-small`."
    ),
    responses={
        202: {"description": "Ingestion accepted — IngestSummary returned"},
        400: {"description": "Empty batch or request body validation error"},
        500: {"description": "Pipeline error — check row_errors for details"},
    },
)
async def ingest_json(
    batch: TicketIngestBatch,
    # user: dict = Depends(get_current_user),  # Enable when auth is wired
) -> IngestSummary:
    """
    Ingest a JSON batch of tickets.

    The response is always HTTP 202 with an IngestSummary.
    Individual row failures are reported in `row_errors` rather than
    raising a 500, so the caller can see exactly which tickets failed.
    """
    logger.info(
        "ingest_json_request",
        ticket_count=len(batch.tickets),
        source=batch.source,
        dry_run=batch.dry_run,
    )

    if not batch.tickets:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Batch contains no tickets.",
        )

    try:
        result = await ingest_batch(batch)
    except Exception as exc:
        logger.exception("ingest_batch_unhandled_error", error=str(exc))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ingestion pipeline error: {exc}",
        )

    return _result_to_summary(result, dry_run=batch.dry_run)


# ============================================================
# POST /ai/ingest/upload  —  CSV file upload
# ============================================================

_SUPPORTED_MIME_TYPES = {
    "text/csv",
    "application/csv",
    "text/plain",
    "application/octet-stream",  # browsers sometimes send this for .csv
    "application/vnd.ms-excel",  # Excel CSV variant
}

_MAX_BYTES = 200 * 1024 * 1024  # 200 MB


@router.post(
    "/ingest/upload",
    response_model=IngestSummary,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Ingest tickets (CSV file upload)",
    description=(
        "Upload a CSV file containing support tickets. "
        "Required columns: `title` (or `subject`). "
        "Optional columns: `ticket_id`, `description`, `source`, `created_at`, "
        "`customer_email`, `severity`, `channel`, `tags`. "
        "Column names are resolved via alias mapping — Zendesk, Intercom, "
        "and generic CSV exports are all accepted. "
        "Max file size: 200 MB."
    ),
    responses={
        202: {"description": "File accepted — IngestSummary returned"},
        400: {"description": "Unsupported file type, missing required columns, or empty file"},
        413: {"description": "File exceeds the 200 MB size limit"},
        500: {"description": "Pipeline error"},
    },
)
async def ingest_csv_upload(
    file:        UploadFile = File(...,   description="CSV file (UTF-8 or latin-1 encoded)"),
    source:      str        = Form("csv", description="Source label: csv | zendesk | intercom | logs | manual"),
    dry_run:     bool       = Form(False, description="Parse and validate only — do not persist or embed"),
    # user: dict = Depends(get_current_user),  # Enable when auth is wired
) -> IngestSummary:
    """
    Parse a CSV upload and run the full ingestion pipeline.

    The endpoint:
      1. Validates file size and MIME type.
      2. Calls parse_csv_file() — column alias resolution, row validation.
      3. Calls ingest_batch() — dedup, INSERT, embed, UPDATE.
      4. Returns IngestSummary with per-row error detail.
    """
    log = logger.bind(
        filename=file.filename,
        content_type=file.content_type,
        source=source,
        dry_run=dry_run,
    )
    log.info("ingest_upload_request")

    # ---- Guard: MIME type ----
    content_type = (file.content_type or "").split(";")[0].strip().lower()
    filename = (file.filename or "").lower()

    is_csv_by_name = filename.endswith(".csv") or filename.endswith(".txt")
    is_csv_by_type = content_type in _SUPPORTED_MIME_TYPES

    if not is_csv_by_name and not is_csv_by_type:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                f"Unsupported file type '{file.content_type}'. "
                "Please upload a CSV file (.csv or .txt)."
            ),
        )

    # ---- Read content ----
    content = await file.read()

    # ---- Guard: size ----
    if len(content) > _MAX_BYTES:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"File exceeds the 200 MB limit ({len(content) / 1_048_576:.1f} MB uploaded).",
        )

    if not content.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Uploaded file is empty.",
        )

    # ---- Parse CSV ----
    try:
        tickets, parse_errors = await parse_csv_file(content, source=source)
    except ValueError as exc:
        # e.g. missing required columns, binary file
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        )
    except Exception as exc:
        log.exception("csv_parse_unhandled_error", error=str(exc))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"CSV parsing error: {exc}",
        )

    log.info(
        "csv_parsed",
        valid_tickets=len(tickets),
        parse_errors=len(parse_errors),
    )

    # If all rows failed to parse, return early with the errors
    if not tickets and parse_errors:
        return IngestSummary(
            total_tickets = len(parse_errors),
            successful    = 0,
            failed        = len(parse_errors),
            dry_run       = dry_run,
            row_errors    = [
                RowErrorOut(
                    row_number = e.row_number,
                    error      = e.error,
                    raw_data   = {k: str(v) for k, v in (e.raw_data or {}).items()},
                )
                for e in parse_errors
            ],
            message = "All rows failed CSV validation. No tickets were ingested.",
        )

    # ---- Ingest pipeline ----
    batch = TicketIngestBatch(
        tickets     = tickets,
        source      = source,
        run_cluster = False,   # clustering is a separate step
        dry_run     = dry_run,
    )

    try:
        result = await ingest_batch(batch)
    except Exception as exc:
        log.exception("ingest_batch_unhandled_error", error=str(exc))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ingestion pipeline error: {exc}",
        )

    summary = _result_to_summary(result, parse_errors=parse_errors, dry_run=dry_run)

    log.info(
        "ingest_upload_complete",
        total=summary.total_tickets,
        successful=summary.successful,
        failed=summary.failed,
        embeddings=summary.embeddings_stored,
    )

    return summary
