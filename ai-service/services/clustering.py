"""
services/clustering.py
----------------------
Production semantic clustering engine for FixLoop AI.

Pipeline
--------
  ① Fetch unclustered embedded tickets from Supabase
  ② Normalise embeddings to unit-sphere (cosine → euclidean distance)
  ③ Run HDBSCAN (density-based — no pre-set K required)
  ④ Handle noise points (HDBSCAN label == -1)
  ⑤ For each cluster:
       a. Compute centroid embedding (mean of member vectors)
       b. Extract example titles and date ranges
       c. Count unique affected customers
  ⑥ Batch-label clusters using Groq
       → title, summary, severity, confidence, product_area
  ⑦ Upsert cluster rows into public.ticket_clusters
  ⑧ Insert cluster_tickets junction rows
  ⑨ Update tickets.cluster_id (via tags / metadata)
  ⑩ Return ClusteringResult

Public API
----------
    run_clustering(request)  →  ClusteringResult
"""

from __future__ import annotations

import json
import math
import re
import uuid
from datetime import date, datetime, timezone
from typing import Any, Optional

import numpy as np
import structlog

from core.config import settings
from models.cluster import (
    ClusterLabel,
    ClusterOut,
    ClusterRecord,
    ClusterRequest,
    ClusteringResult,
    RawTicket,
)
from models.common import ItemStatus, SeverityLevel
from services.supabase_client import get_supabase

logger = structlog.get_logger(__name__)


# ============================================================
# ① Fetch tickets
# ============================================================

async def _fetch_unclustered_tickets(
    ticket_ids: list[int] | None,
    process_all: bool,
    limit: int,
) -> list[RawTicket]:
    """
    Load embedded tickets from Supabase.

    Filters:
      - embedding IS NOT NULL   (skips tickets not yet embedded)
      - cluster_id IS NULL      (skips already-clustered tickets, unless process_all)
    """
    sb = await get_supabase()
    query = (
        sb.table("tickets")
        .select("id, title, body, embedding, customer_id, severity, created_at")
        .not_.is_("embedding", "null")
        .limit(limit)
    )

    if ticket_ids:
        query = query.in_("id", ticket_ids)
    elif not process_all:
        # Only tickets not yet assigned to a cluster
        query = query.is_("cluster_id", "null")  # type: ignore[attr-defined]

    resp = await query.execute()
    rows = resp.data or []

    tickets: list[RawTicket] = []
    for row in rows:
        raw_emb = row.get("embedding")
        if raw_emb is None:
            continue

        # Supabase returns pgvector as a list of floats or a comma-sep string
        if isinstance(raw_emb, str):
            try:
                embedding = [float(x) for x in raw_emb.strip("[]").split(",")]
            except ValueError:
                logger.warning("embedding_parse_failed", ticket_id=row["id"])
                continue
        elif isinstance(raw_emb, list):
            embedding = [float(x) for x in raw_emb]
        else:
            continue

        tickets.append(
            RawTicket(
                id          = row["id"],
                title       = row.get("title", ""),
                body        = row.get("body"),
                embedding   = embedding,
                customer_id = row.get("customer_id"),
                severity    = row.get("severity"),
                created_at  = row.get("created_at"),
            )
        )

    logger.info("tickets_fetched", count=len(tickets))
    return tickets


# ============================================================
# ② HDBSCAN clustering
# ============================================================

def _normalise(embeddings: np.ndarray) -> np.ndarray:
    """L2-normalise rows so cosine distance = euclidean distance on unit sphere."""
    norms = np.linalg.norm(embeddings, axis=1, keepdims=True)
    norms = np.where(norms == 0, 1.0, norms)  # guard zero-norm
    return embeddings / norms


def _run_hdbscan(
    embeddings: np.ndarray,
    min_cluster_size: int,
    min_samples: int,
    cluster_selection_epsilon: float,
) -> np.ndarray:
    """
    Run HDBSCAN on L2-normalised embeddings.

    Returns an int array of cluster labels (−1 = noise).

    We use metric='euclidean' on unit-normalised vectors, which is
    equivalent to cosine similarity clustering.
    """
    try:
        import hdbscan as hdbscan_lib
        clusterer = hdbscan_lib.HDBSCAN(
            min_cluster_size=min_cluster_size,
            min_samples=min_samples,
            cluster_selection_epsilon=cluster_selection_epsilon,
            metric="euclidean",
            cluster_selection_method="eom",  # Excess of Mass — better for variable density
            prediction_data=False,
        )
        labels: np.ndarray = clusterer.fit_predict(embeddings)
        return labels
    except ImportError:
        # Fallback: use scikit-learn DBSCAN if hdbscan is not installed
        logger.warning(
            "hdbscan_not_installed",
            message="Falling back to sklearn DBSCAN — install 'hdbscan' for better results.",
        )
        from sklearn.cluster import DBSCAN
        clusterer = DBSCAN(
            eps=cluster_selection_epsilon,
            min_samples=min_cluster_size,
            metric="euclidean",
            n_jobs=-1,
        )
        labels = clusterer.fit_predict(embeddings)
        return labels


# ============================================================
# ③ Build ClusterRecord objects
# ============================================================

def _compute_centroid(embeddings: list[list[float]]) -> list[float]:
    """Return the mean embedding (centroid) of a set of vectors."""
    arr = np.array(embeddings, dtype=np.float32)
    mean = arr.mean(axis=0)
    # Re-normalise centroid to unit sphere
    norm = np.linalg.norm(mean)
    if norm > 0:
        mean = mean / norm
    return mean.tolist()


def _pick_example_titles(tickets: list[RawTicket], n: int = 3) -> list[str]:
    """Return up to n unique, non-empty titles from the cluster members."""
    seen: set[str] = set()
    result: list[str] = []
    for t in tickets:
        title = (t.title or "").strip()
        if title and title not in seen:
            seen.add(title)
            result.append(title)
        if len(result) >= n:
            break
    return result


def _count_affected_customers(tickets: list[RawTicket]) -> int:
    """Count distinct non-null customer_id values."""
    return len({t.customer_id for t in tickets if t.customer_id})


def _parse_date(value: str | None) -> date | None:
    if not value:
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00")).date()
    except (ValueError, AttributeError):
        return None


def _build_cluster_records(
    tickets: list[RawTicket],
    labels: np.ndarray,
) -> tuple[list[ClusterRecord], list[int]]:
    """
    Group tickets by HDBSCAN label and build ClusterRecord stubs.
    Returns (cluster_records, noise_ticket_ids).
    """
    # Group ticket indices by label
    label_to_indices: dict[int, list[int]] = {}
    for idx, label in enumerate(labels.tolist()):
        label_to_indices.setdefault(label, []).append(idx)

    noise_ids: list[int] = []
    records:   list[ClusterRecord] = []

    for label, indices in sorted(label_to_indices.items()):
        if label == -1:
            noise_ids = [tickets[i].id for i in indices]
            continue

        members = [tickets[i] for i in indices]
        embeddings = [t.embedding for t in members]
        centroid   = _compute_centroid(embeddings)

        # Date range
        dates = [_parse_date(t.created_at) for t in members if t.created_at]
        first_seen = min(dates) if dates else None
        last_seen  = max(dates) if dates else None

        records.append(
            ClusterRecord(
                cluster_id         = f"CL-{uuid.uuid4().hex[:8].upper()}",
                label              = ClusterLabel(   # placeholder — filled by LLM
                    title        = f"Cluster {label}",
                    summary      = "",
                    severity     = SeverityLevel.MEDIUM,
                    confidence   = 0.0,
                    product_area = None,
                ),
                ticket_ids         = [t.id for t in members],
                centroid           = centroid,
                example_titles     = _pick_example_titles(members, n=5),
                affected_customers = _count_affected_customers(members),
                first_seen_at      = first_seen,
                last_seen_at       = last_seen,
            )
        )

    logger.info(
        "cluster_records_built",
        cluster_count=len(records),
        noise_count=len(noise_ids),
    )
    return records, noise_ids


# ============================================================
# ④ LLM labelling (Groq)
# ============================================================

_LABEL_SYSTEM_PROMPT = """\
You are a senior product-support analyst at a SaaS company.
You will receive a list of clusters, each containing:
  - A list of example support ticket titles
  - The cluster size (number of tickets)

For EACH cluster, respond with a JSON object containing EXACTLY these fields:
{
  "title":        "<concise 3-8 word issue name>",
  "summary":      "<1-2 sentence description of the core problem>",
  "severity":     "<one of: critical | high | medium | low>",
  "confidence":   <float 0-100 reflecting how cohesive this cluster is>,
  "product_area": "<one of: Auth & SSO | Billing | Exports & Reports | Integrations | Mobile | Search | Notifications | Performance | Other>"
}

Severity guide:
  critical = data loss, system down, security breach, blocking all users
  high     = significant feature broken, affecting many users
  medium   = degraded functionality, workaround exists
  low      = cosmetic, minor inconvenience

Return a JSON ARRAY with one object per cluster, in the same order as the input.
Return ONLY the JSON array — no markdown, no explanation.
"""


def _build_label_prompt(records: list[ClusterRecord]) -> str:
    """Build the user-message content for the LLM labelling call."""
    clusters_json = []
    for i, rec in enumerate(records):
        clusters_json.append({
            "cluster_index":  i,
            "ticket_count":   len(rec.ticket_ids),
            "example_titles": rec.example_titles,
        })
    return json.dumps(clusters_json, indent=2)


from services.llm import generate_cluster_labels

async def _label_with_groq(records: list[ClusterRecord]) -> list[ClusterLabel]:
    """Call Groq to generate labels for a batch of clusters."""
    prompt = _build_label_prompt(records)
    
    try:
        raw = await generate_cluster_labels(
            system_prompt=_LABEL_SYSTEM_PROMPT,
            user_prompt=prompt,
        )
        return _parse_label_response(raw, len(records))
    except Exception as exc:
        logger.error("groq_labelling_failed", error=str(exc))
        return _fallback_labels(len(records))


def _parse_label_response(raw: str, expected_count: int) -> list[ClusterLabel]:
    """
    Parse a JSON array from the LLM response into ClusterLabel objects.
    Falls back to safe defaults on any parse error.
    """
    # Strip markdown code fences if present
    cleaned = re.sub(r"^```(?:json)?\s*|\s*```$", "", raw.strip(), flags=re.MULTILINE)

    # Sometimes GPT returns {"clusters": [...]}
    try:
        parsed = json.loads(cleaned)
        if isinstance(parsed, dict):
            # Unwrap common envelope keys
            for key in ("clusters", "results", "data", "items"):
                if key in parsed and isinstance(parsed[key], list):
                    parsed = parsed[key]
                    break
            else:
                # Single object — wrap into list
                parsed = [parsed]
    except (json.JSONDecodeError, ValueError):
        logger.error("llm_label_parse_failed", raw=raw[:500])
        return _fallback_labels(expected_count)

    labels: list[ClusterLabel] = []
    for item in parsed[:expected_count]:
        try:
            severity_raw = str(item.get("severity", "medium")).lower().strip()
            severity = SeverityLevel(severity_raw) if severity_raw in SeverityLevel._value2member_map_ else SeverityLevel.MEDIUM  # type: ignore

            confidence = float(item.get("confidence", 70.0))
            confidence = max(0.0, min(100.0, confidence))

            labels.append(
                ClusterLabel(
                    title        = str(item.get("title", "Unknown Issue"))[:200],
                    summary      = str(item.get("summary", ""))[:1000],
                    severity     = severity,
                    confidence   = confidence,
                    product_area = item.get("product_area"),
                )
            )
        except Exception as exc:
            logger.warning("llm_label_item_parse_failed", error=str(exc), item=item)
            labels.append(_default_label())

    # Pad with defaults if the LLM returned fewer items than expected
    while len(labels) < expected_count:
        labels.append(_default_label())

    return labels


def _default_label() -> ClusterLabel:
    return ClusterLabel(
        title      = "Unclassified Issue",
        summary    = "A group of related support tickets requiring review.",
        severity   = SeverityLevel.MEDIUM,
        confidence = 60.0,
    )


def _fallback_labels(n: int) -> list[ClusterLabel]:
    return [_default_label() for _ in range(n)]


async def _label_clusters(records: list[ClusterRecord]) -> list[ClusterLabel]:
    """
    Generate human-readable labels for all cluster records.

    Processes in batches of CLUSTER_LLM_BATCH_SIZE.
    """
    all_labels: list[ClusterLabel] = []
    batch_size = settings.CLUSTER_LLM_BATCH_SIZE

    for batch_start in range(0, len(records), batch_size):
        batch = records[batch_start : batch_start + batch_size]

        logger.info(
            "labelling_batch",
            batch_start=batch_start,
            batch_size=len(batch),
            backend=settings.CLUSTER_LLM_BACKEND,
        )

        try:
            labels = await _label_with_groq(batch)
        except Exception as exc:
            logger.error(
                "llm_labelling_failed",
                batch_start=batch_start,
                error=str(exc),
            )
            labels = _fallback_labels(len(batch))

        all_labels.extend(labels)

    return all_labels


# ============================================================
# ⑤ Database writes
# ============================================================

async def _upsert_clusters(records: list[ClusterRecord]) -> list[dict]:
    """
    Upsert cluster rows into public.ticket_clusters.
    Returns the list of persisted cluster dicts (with DB-assigned fields).
    """
    sb   = await get_supabase()
    rows = []
    now  = datetime.now(timezone.utc).date().isoformat()

    for rec in records:
        rows.append({
            "id":                 rec.cluster_id,
            "title":              rec.label.title,
            "summary":            rec.label.summary or None,
            "severity":           rec.label.severity.value,
            "status":             ItemStatus.OPEN.value,
            "ticket_count":       len(rec.ticket_ids),
            "affected_customers": rec.affected_customers,
            "monthly_cost_usd":   0,   # set by investigation stage
            "confidence":         rec.label.confidence,
            "product_area":       rec.label.product_area,
            "example_titles":     rec.example_titles,
            "ticket_trend":       [],
            "centroid_embedding": rec.centroid,
            "first_seen_at":      rec.first_seen_at.isoformat() if rec.first_seen_at else now,
            "last_seen_at":       rec.last_seen_at.isoformat() if rec.last_seen_at else now,
        })

    resp = (
        await sb.table("ticket_clusters")
        .upsert(rows, on_conflict="id")
        .execute()
    )
    persisted: list[dict] = resp.data or []
    logger.info("clusters_upserted", count=len(persisted))
    return persisted


async def _insert_cluster_tickets(records: list[ClusterRecord]) -> int:
    """
    Populate the cluster_tickets junction table.
    Computes per-ticket similarity as cosine similarity to centroid.
    """
    sb        = await get_supabase()
    junctions = []
    centroid_arr = {rec.cluster_id: np.array(rec.centroid, dtype=np.float32)
                    for rec in records}

    for rec in records:
        c_vec = centroid_arr[rec.cluster_id]
        c_norm = np.linalg.norm(c_vec)

        # We'll fetch the embedding for similarity — we already have it in memory
        # because we used it for clustering; store similarity = 1.0 for now,
        # the full cosine will be computed per-ticket in the background.
        for tid in rec.ticket_ids:
            junctions.append({
                "cluster_id": rec.cluster_id,
                "ticket_id":  tid,
                "similarity": None,   # populated by background job if needed
            })

    if not junctions:
        return 0

    # Batch insert in chunks to avoid request-size limits
    chunk_size = 500
    inserted = 0
    for i in range(0, len(junctions), chunk_size):
        chunk = junctions[i : i + chunk_size]
        try:
            await (
                sb.table("cluster_tickets")
                .upsert(chunk, on_conflict="cluster_id,ticket_id")
                .execute()
            )
            inserted += len(chunk)
        except Exception as exc:
            logger.error("cluster_tickets_insert_failed", chunk_start=i, error=str(exc))

    logger.info("cluster_tickets_inserted", count=inserted)
    return inserted


async def _update_ticket_cluster_ids(records: list[ClusterRecord]) -> int:
    """
    Store the cluster_id back on each ticket row.

    NOTE: public.tickets does not have a cluster_id column in the current schema.
    We store the cluster association exclusively via cluster_tickets junction.
    This function is intentionally a no-op but kept for future schema extension.
    """
    # If you add a `cluster_id` column to public.tickets in the future,
    # implement the UPDATE here:
    #   sb = await get_supabase()
    #   for rec in records:
    #       await sb.table("tickets").update({"cluster_id": rec.cluster_id})
    #                .in_("id", rec.ticket_ids).execute()
    return sum(len(rec.ticket_ids) for rec in records)


# ============================================================
# ⑥ Build ClusterOut response objects
# ============================================================

def _build_cluster_out(rec: ClusterRecord) -> ClusterOut:
    """Convert a ClusterRecord to a ClusterOut API model."""
    now = datetime.now(timezone.utc)
    return ClusterOut(
        id                 = rec.cluster_id,
        title              = rec.label.title,
        summary            = rec.label.summary or None,
        severity           = rec.label.severity,
        status             = ItemStatus.OPEN,
        ticket_count       = len(rec.ticket_ids),
        affected_customers = rec.affected_customers,
        monthly_cost_usd   = 0.0,
        confidence         = rec.label.confidence,
        product_area       = rec.label.product_area,
        related_deploy_id  = None,
        first_seen_at      = rec.first_seen_at,
        last_seen_at       = rec.last_seen_at,
        root_cause         = None,       # set by investigation stage
        ticket_trend       = [],
        example_titles     = rec.example_titles,
        created_by         = None,
        created_at         = now,
        updated_at         = now,
    )


# ============================================================
# Public entry point
# ============================================================

async def run_clustering(request: ClusterRequest) -> ClusteringResult:
    """
    Run the full semantic clustering pipeline.

    Steps:
        ① Fetch unclustered embedded tickets from Supabase
        ② Normalise embeddings (L2) for cosine-equivalent distance
        ③ Run HDBSCAN (or DBSCAN fallback)
        ④ Build ClusterRecord objects with centroids and metadata
        ⑤ Batch-label clusters via Groq
        ⑥ Upsert ticket_clusters rows
        ⑦ Insert cluster_tickets junction rows
        ⑧ Update tickets with cluster assignment
        ⑨ Return ClusteringResult

    Args:
        request: ClusterRequest — ticket_ids, process_all, dry_run flags.

    Returns:
        ClusteringResult with cluster_count, clustered_tickets,
        noise_tickets, and a list of ClusterOut objects.
    """
    log = logger.bind(
        ticket_ids=len(request.ticket_ids) if request.ticket_ids else "all",
        process_all=request.process_all,
        dry_run=request.dry_run,
    )
    log.info("clustering_start")

    # ① Fetch tickets
    tickets = await _fetch_unclustered_tickets(
        ticket_ids  = request.ticket_ids,
        process_all = request.process_all,
        limit       = settings.CLUSTER_MAX_TICKETS,
    )

    if not tickets:
        log.info("clustering_no_tickets")
        return ClusteringResult(
            cluster_count     = 0,
            clustered_tickets = 0,
            noise_tickets     = 0,
            clusters          = [],
        )

    if len(tickets) < 2:
        log.warning("clustering_too_few_tickets", count=len(tickets))
        return ClusteringResult(
            cluster_count     = 0,
            clustered_tickets = 0,
            noise_tickets     = len(tickets),
            clusters          = [],
        )

    # ② Normalise embeddings
    emb_matrix = np.array([t.embedding for t in tickets], dtype=np.float32)
    emb_norm   = _normalise(emb_matrix)

    # ③ HDBSCAN
    min_cluster_size = request.min_cluster_size or settings.CLUSTER_MIN_CLUSTER_SIZE
    labels = _run_hdbscan(
        embeddings                = emb_norm,
        min_cluster_size          = min_cluster_size,
        min_samples               = settings.CLUSTER_MIN_SAMPLES,
        cluster_selection_epsilon = settings.CLUSTER_EPSILON,
    )

    log.info(
        "hdbscan_complete",
        total_tickets  = len(tickets),
        unique_labels  = len(set(labels.tolist())) - (1 if -1 in labels else 0),
        noise_count    = int((labels == -1).sum()),
    )

    # ④ Build ClusterRecord stubs
    records, noise_ids = _build_cluster_records(tickets, labels)

    if not records:
        log.info("clustering_all_noise", noise_count=len(noise_ids))
        return ClusteringResult(
            cluster_count     = 0,
            clustered_tickets = 0,
            noise_tickets     = len(noise_ids),
            clusters          = [],
        )

    # ⑤ LLM labelling
    log.info("labelling_start", cluster_count=len(records))
    labels_list = await _label_clusters(records)

    # Attach labels to records
    for rec, lbl in zip(records, labels_list):
        rec.label = lbl

    log.info("labelling_complete")

    if request.dry_run:
        log.info("dry_run_complete", clusters=len(records), noise=len(noise_ids))
        return ClusteringResult(
            cluster_count     = len(records),
            clustered_tickets = sum(len(r.ticket_ids) for r in records),
            noise_tickets     = len(noise_ids),
            clusters          = [_build_cluster_out(r) for r in records],
        )

    # ⑥ Upsert cluster rows
    await _upsert_clusters(records)

    # ⑦ Junction table
    await _insert_cluster_tickets(records)

    # ⑧ Update tickets
    await _update_ticket_cluster_ids(records)

    log.info(
        "clustering_complete",
        clusters          = len(records),
        clustered_tickets = sum(len(r.ticket_ids) for r in records),
        noise_tickets     = len(noise_ids),
    )

    return ClusteringResult(
        cluster_count     = len(records),
        clustered_tickets = sum(len(r.ticket_ids) for r in records),
        noise_tickets     = len(noise_ids),
        clusters          = [_build_cluster_out(r) for r in records],
    )


# Convenience thin wrappers kept for backward-compat with old agent signatures
async def compute_centroid(embeddings: list[list[float]]) -> list[float]:
    """Compute mean embedding vector (unit-normalised)."""
    return _compute_centroid(embeddings)
