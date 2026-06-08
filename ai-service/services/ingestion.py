"""
services/ingestion.py
---------------------
Production ticket ingestion service for FixLoop AI.

Pipeline (per CSV upload):

  ┌─────────────┐    ┌──────────────┐    ┌────────────────────┐
  │  Parse CSV  │───▶│ Validate rows│───▶│ Dedup by external_id│
  └─────────────┘    └──────────────┘    └────────────────────┘
                                                   │
                                    ┌──────────────▼──────────────┐
                                    │  INSERT tickets (Supabase)  │
                                    └──────────────┬──────────────┘
                                                   │
                              ┌────────────────────▼────────────────────┐
                              │  Batch-embed (OpenAI) → update embeddings │
                              └─────────────────────────────────────────┘

Public API:
    parse_csv_file(content, source)  →  list[TicketIn], list[RowError]
    ingest_batch(batch)              →  IngestionResult
"""

from __future__ import annotations

import csv
import io
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Optional

import structlog
from pydantic import ValidationError

from models.ticket import TicketIn, TicketIngestBatch, TicketOut
from models.common import ItemStatus
from services.supabase_client import get_supabase
from services.embedding import embed_tickets_batch

logger = structlog.get_logger(__name__)

# ---------------------------------------------------------------------------
# CSV column aliases
# ---------------------------------------------------------------------------
# Maps canonical column names to the variants found in different exports.
# First match wins.
_COLUMN_ALIASES: dict[str, list[str]] = {
    "external_id":       ["ticket_id", "id", "external_id", "ticket_number"],
    "title":             ["title", "subject", "summary", "name"],
    "body":              ["description", "body", "content", "details", "message"],
    "source":            ["source", "channel_type", "platform"],
    "customer_id":       ["customer_id", "requester_id", "user_id", "account_id"],
    "customer_email":    ["customer_email", "requester_email", "email"],
    "severity":          ["severity", "priority", "impact"],
    "channel":           ["channel", "contact_channel", "type"],
    "tags":              ["tags", "labels", "categories"],
    "ticket_created_at": ["created_at", "ticket_created_at", "date", "created"],
}

# Columns that MUST be present (after alias resolution)
_REQUIRED_COLUMNS = {"title"}


# ---------------------------------------------------------------------------
# Data structures
# ---------------------------------------------------------------------------

@dataclass
class RowError:
    """Describes a single failed row during CSV parsing or validation."""
    row_number: int
    raw_data:   dict[str, Any]
    error:      str


@dataclass
class IngestionResult:
    """Returned by ingest_batch() after the full pipeline completes."""
    total_tickets:    int              = 0
    successful:       int              = 0
    failed:           int              = 0
    skipped_dupes:    int              = 0
    row_errors:       list[RowError]   = field(default_factory=list)
    tickets:          list[TicketOut]  = field(default_factory=list)
    embeddings_stored: int             = 0


# ---------------------------------------------------------------------------
# CSV parsing helpers
# ---------------------------------------------------------------------------

def _resolve_column(header: str, candidates: list[str]) -> str | None:
    """
    Return the first candidate column that exists in the CSV header row.
    Comparison is case-insensitive and strips surrounding whitespace.
    """
    norm = header.lower().strip()
    return next((c for c in candidates if c == norm), None)


def _build_column_map(headers: list[str]) -> dict[str, str]:
    """
    Build a mapping  canonical_field → csv_header  for a given CSV.

    For each canonical field, try each alias in priority order and return
    the first one that exists in the actual CSV headers.

    Returns only fields that could be resolved; missing optional fields are absent.
    """
    header_set = {h.lower().strip(): h for h in headers}  # normalised → original
    mapping: dict[str, str] = {}
    for canonical, aliases in _COLUMN_ALIASES.items():
        for alias in aliases:
            if alias.lower() in header_set:
                mapping[canonical] = header_set[alias.lower()]
                break
    return mapping


def _coerce_severity(raw: str | None) -> str | None:
    """
    Map common priority/severity strings to our SeverityLevel enum values.
    Returns None for unrecognised values (field becomes optional NULL).
    """
    if not raw:
        return None
    mapping = {
        "urgent": "critical",
        "critical": "critical",
        "high": "high",
        "medium": "medium",
        "normal": "medium",
        "low": "low",
        "1": "critical",
        "2": "high",
        "3": "medium",
        "4": "low",
        "p1": "critical",
        "p2": "high",
        "p3": "medium",
        "p4": "low",
    }
    return mapping.get(raw.strip().lower())


def _coerce_datetime(raw: str | None) -> datetime | None:
    """
    Try several common datetime formats and return a UTC-aware datetime.
    Returns None if parsing fails (non-fatal — field is optional).
    """
    if not raw or not raw.strip():
        return None

    raw = raw.strip()
    formats = [
        "%Y-%m-%dT%H:%M:%SZ",
        "%Y-%m-%dT%H:%M:%S",
        "%Y-%m-%dT%H:%M:%S%z",
        "%Y-%m-%d %H:%M:%S",
        "%Y-%m-%d",
        "%m/%d/%Y %H:%M:%S",
        "%m/%d/%Y",
        "%d-%m-%Y",
    ]
    for fmt in formats:
        try:
            dt = datetime.strptime(raw, fmt)
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            return dt
        except ValueError:
            continue

    logger.debug("datetime_parse_failed", raw=raw)
    return None


def _coerce_tags(raw: str | None) -> list[str]:
    """
    Parse a comma/pipe/semicolon-separated tag string into a list.
    """
    if not raw or not raw.strip():
        return []
    for sep in (",", "|", ";"):
        if sep in raw:
            return [t.strip() for t in raw.split(sep) if t.strip()]
    return [raw.strip()] if raw.strip() else []


def _row_to_ticket_in(
    row: dict[str, str],
    col_map: dict[str, str],
    source_override: str,
    row_number: int,
) -> tuple[TicketIn | None, RowError | None]:
    """
    Convert a single CSV row dict into a TicketIn model.

    Returns (TicketIn, None) on success or (None, RowError) on failure.
    """
    def get(canonical: str) -> str | None:
        header = col_map.get(canonical)
        if header is None:
            return None
        return row.get(header, "").strip() or None

    # Determine source: row-level overrides batch-level override
    raw_source = get("source") or source_override
    valid_sources = {"csv", "zendesk", "intercom", "logs", "manual"}
    source = raw_source.lower() if raw_source and raw_source.lower() in valid_sources else "csv"

    raw_data: dict[str, Any] = dict(row)
    try:
        ticket = TicketIn(
            external_id       = get("external_id"),
            source            = source,
            title             = get("title") or "",  # validated below
            body              = get("body"),
            customer_id       = get("customer_id"),
            customer_email    = get("customer_email"),
            severity          = _coerce_severity(get("severity")),
            channel           = get("channel"),
            tags              = _coerce_tags(get("tags")),
            ticket_created_at = _coerce_datetime(get("ticket_created_at")),
        )
        return ticket, None
    except ValidationError as exc:
        error_msg = "; ".join(
            f"{e['loc']}: {e['msg']}" for e in exc.errors()
        )
        return None, RowError(row_number=row_number, raw_data=raw_data, error=error_msg)
    except Exception as exc:
        return None, RowError(row_number=row_number, raw_data=raw_data, error=str(exc))


# ---------------------------------------------------------------------------
# Public: CSV parser
# ---------------------------------------------------------------------------

async def parse_csv_file(
    content: bytes,
    source: str = "csv",
) -> tuple[list[TicketIn], list[RowError]]:
    """
    Parse a CSV file into validated TicketIn objects.

    Accepts UTF-8 or latin-1 encoded files. Automatically resolves
    column aliases (ticket_id → external_id, description → body, etc.).

    Args:
        content: Raw bytes of the uploaded CSV file.
        source:  Source label to apply when no source column is present.

    Returns:
        Tuple of (valid_tickets, row_errors).
        Row errors are non-fatal — the caller decides whether to abort or continue.

    Raises:
        ValueError: If the file cannot be parsed as CSV at all (e.g., binary file).
    """
    # Decode: try UTF-8 first, fall back to latin-1
    try:
        text = content.decode("utf-8-sig")  # handles BOM
    except UnicodeDecodeError:
        text = content.decode("latin-1")

    # Sniff dialect (comma / tab / semicolon)
    try:
        dialect = csv.Sniffer().sniff(text[:4096], delimiters=",\t;|")
    except csv.Error:
        dialect = csv.excel  # default comma

    reader = csv.DictReader(io.StringIO(text), dialect=dialect)

    if reader.fieldnames is None:
        raise ValueError("CSV file has no header row or is empty.")

    headers = [str(h) for h in reader.fieldnames]
    col_map = _build_column_map(headers)

    logger.info(
        "csv_parse_start",
        detected_headers=headers,
        resolved_columns=list(col_map.keys()),
    )

    # Validate required columns are present
    missing_required = _REQUIRED_COLUMNS - set(col_map.keys())
    if missing_required:
        raise ValueError(
            f"CSV is missing required column(s): {missing_required}. "
            f"Detected headers: {headers}."
        )

    tickets:    list[TicketIn]  = []
    row_errors: list[RowError]  = []

    for row_number, row in enumerate(reader, start=2):  # row 1 = header
        ticket, error = _row_to_ticket_in(row, col_map, source, row_number)
        if ticket:
            tickets.append(ticket)
        else:
            row_errors.append(error)  # type: ignore[arg-type]

    logger.info(
        "csv_parse_complete",
        total_rows=row_number if tickets or row_errors else 0,
        valid=len(tickets),
        errors=len(row_errors),
    )

    return tickets, row_errors


# ---------------------------------------------------------------------------
# Public: core ingestion pipeline
# ---------------------------------------------------------------------------

async def ingest_batch(batch: TicketIngestBatch) -> IngestionResult:
    """
    Persist a batch of TicketIn objects to Supabase and generate embeddings.

    Pipeline:
        1. Deduplicate against existing external_ids in public.tickets.
        2. INSERT new rows into public.tickets (status=open, no embedding yet).
        3. Batch-embed all new tickets using OpenAI.
        4. UPDATE each ticket row with its embedding vector.

    Args:
        batch: Validated TicketIngestBatch (tickets, source, dry_run flags).

    Returns:
        IngestionResult with counts and the list of persisted TicketOut objects.
    """
    result = IngestionResult(total_tickets=len(batch.tickets))

    log = logger.bind(
        ticket_count=len(batch.tickets),
        source=batch.source,
        dry_run=batch.dry_run,
    )
    log.info("ingest_batch_start")

    if batch.dry_run:
        log.info("ingest_dry_run", message="Dry-run mode: validation only, no DB writes.")
        result.successful = len(batch.tickets)
        return result

    sb = await get_supabase()

    # ----------------------------------------------------------------
    # Step 1: Resolve existing external_ids to detect duplicates
    # ----------------------------------------------------------------
    external_ids = [
        t.external_id for t in batch.tickets if t.external_id
    ]

    existing_external_ids: set[str] = set()
    if external_ids:
        dupe_resp = (
            await sb.table("tickets")
            .select("external_id")
            .in_("external_id", external_ids)
            .execute()
        )
        existing_external_ids = {
            row["external_id"] for row in (dupe_resp.data or [])
        }
        log.info("dupe_check", existing_count=len(existing_external_ids))

    # ----------------------------------------------------------------
    # Step 2: Build insert payloads, skipping duplicates
    # ----------------------------------------------------------------
    to_insert: list[dict] = []
    skipped = 0

    for ticket in batch.tickets:
        if ticket.external_id and ticket.external_id in existing_external_ids:
            skipped += 1
            continue

        row: dict = {
            "external_id":       ticket.external_id,
            "source":            ticket.source or batch.source,
            "title":             ticket.title,
            "body":              ticket.body,
            "customer_id":       ticket.customer_id,
            "customer_email":    str(ticket.customer_email) if ticket.customer_email else None,
            "severity":          ticket.severity.value if ticket.severity else None,
            "status":            ItemStatus.OPEN.value,
            "channel":           ticket.channel,
            "tags":              ticket.tags or [],
            "related_deploy_id": ticket.related_deploy_id,
            "ticket_created_at": ticket.ticket_created_at.isoformat() if ticket.ticket_created_at else None,
            "ingested_at":       datetime.now(timezone.utc).isoformat(),
        }
        to_insert.append(row)

    result.skipped_dupes = skipped
    log.info("ingest_deduplicated", to_insert=len(to_insert), skipped=skipped)

    if not to_insert:
        log.info("ingest_nothing_to_insert")
        result.failed = 0
        return result

    # ----------------------------------------------------------------
    # Step 3: INSERT tickets into Supabase
    # ----------------------------------------------------------------
    try:
        insert_resp = (
            await sb.table("tickets")
            .insert(to_insert)
            .execute()
        )
    except Exception as exc:
        log.error("ticket_insert_failed", error=str(exc))
        result.failed = len(to_insert)
        return result

    inserted_rows: list[dict] = insert_resp.data or []
    log.info("tickets_inserted", count=len(inserted_rows))

    if not inserted_rows:
        result.failed = len(to_insert)
        return result

    # ----------------------------------------------------------------
    # Step 4: Batch-embed inserted tickets
    # ----------------------------------------------------------------
    log.info("embedding_start", count=len(inserted_rows))

    ticket_pairs: list[tuple[str, str | None]] = [
        (row["title"], row.get("body")) for row in inserted_rows
    ]

    try:
        embeddings = await embed_tickets_batch(ticket_pairs)
    except Exception as exc:
        log.error("embedding_failed", error=str(exc))
        # Tickets are persisted but without embeddings — non-fatal.
        # They can be re-embedded by a background job later.
        embeddings = [None] * len(inserted_rows)  # type: ignore[list-item]

    # ----------------------------------------------------------------
    # Step 5: UPDATE each ticket row with its embedding vector
    # ----------------------------------------------------------------
    embed_success = 0
    embed_fail    = 0

    for row, embedding in zip(inserted_rows, embeddings):
        ticket_id = row["id"]

        if embedding is None:
            embed_fail += 1
            continue

        try:
            await (
                sb.table("tickets")
                .update({"embedding": embedding})
                .eq("id", ticket_id)
                .execute()
            )
            embed_success += 1
        except Exception as exc:
            log.warning(
                "embedding_update_failed",
                ticket_id=ticket_id,
                error=str(exc),
            )
            embed_fail += 1

    result.embeddings_stored = embed_success
    result.successful        = len(inserted_rows)
    result.failed            = 0  # inserts all succeeded; embed failures are soft

    # ----------------------------------------------------------------
    # Step 6: Build TicketOut list for the response
    # ----------------------------------------------------------------
    result.tickets = [
        TicketOut(
            id                = row["id"],
            external_id       = row.get("external_id"),
            source            = row.get("source", batch.source),
            title             = row["title"],
            body              = row.get("body"),
            customer_id       = row.get("customer_id"),
            customer_email    = row.get("customer_email"),
            severity          = row.get("severity"),
            status            = row.get("status", ItemStatus.OPEN.value),
            sentiment_score   = row.get("sentiment_score"),
            channel           = row.get("channel"),
            tags              = row.get("tags") or [],
            related_deploy_id = row.get("related_deploy_id"),
            embedding_ready   = embed_success > 0,
            ingested_at       = _parse_db_datetime(row.get("ingested_at")),
            ticket_created_at = _parse_db_datetime(row.get("ticket_created_at")),
            created_at        = _parse_db_datetime(row.get("created_at")),
        )
        for row in inserted_rows
    ]

    log.info(
        "ingest_batch_complete",
        successful=result.successful,
        skipped=result.skipped_dupes,
        embeddings_stored=result.embeddings_stored,
        embed_failures=embed_fail,
    )
    return result


# ---------------------------------------------------------------------------
# Private helpers
# ---------------------------------------------------------------------------

def _parse_db_datetime(value: str | None) -> datetime:
    """
    Parse a datetime string returned from Supabase into a datetime object.
    Returns epoch if value is None or unparseable (defensive fallback).
    """
    if not value:
        return datetime.now(timezone.utc)
    try:
        if value.endswith("Z"):
            value = value[:-1] + "+00:00"
        return datetime.fromisoformat(value)
    except (ValueError, TypeError):
        return datetime.now(timezone.utc)
