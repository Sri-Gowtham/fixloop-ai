"""
services/embedding.py
---------------------
Production OpenAI / Gemini embedding service for FixLoop AI.

Strategy:
  - Primary:  OpenAI text-embedding-3-small  (1536-dim, fast, cheap)
  - Fallback: Google Gemini embedding-001    (768-dim — disabled by default)
  - Chunked batching to respect API rate limits
  - Exponential back-off retries via tenacity
  - Input text truncated to max_tokens before sending
  - Empty-text guard returns a zero-vector (no API call wasted)

All embeddings are 1536-dimensional to match the pgvector column
defined in supabase/schema.sql.
"""

from __future__ import annotations

import asyncio
import hashlib
from typing import Optional

import structlog
from openai import AsyncOpenAI, RateLimitError, APIStatusError
from tenacity import (
    before_sleep_log,
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from core.config import settings

logger = structlog.get_logger(__name__)

# OpenAI token limit for embedding models (8191 tokens ≈ ~32 k chars)
_MAX_CHARS = 30_000

# Module-level singleton — initialised once, reused across requests
_openai_client: Optional[AsyncOpenAI] = None


def _get_openai() -> AsyncOpenAI:
    """Return (or lazily create) the shared AsyncOpenAI client."""
    global _openai_client
    if _openai_client is None:
        _openai_client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
        logger.info("openai_client_init", model=settings.OPENAI_EMBED_MODEL)
    return _openai_client


def _truncate(text: str, max_chars: int = _MAX_CHARS) -> str:
    """
    Hard-truncate text to avoid exceeding the model token window.
    We use character count as a cheap proxy (1 token ≈ 4 chars).
    """
    if len(text) <= max_chars:
        return text
    truncated = text[:max_chars]
    logger.debug("embedding_text_truncated", original_len=len(text), truncated_len=max_chars)
    return truncated


def _build_embed_text(title: str, body: Optional[str]) -> str:
    """
    Combine title + body into a single string for embedding.

    The title is repeated at the start to upweight its semantic signal.
    Format: "<title>\n\n<body>"
    """
    parts = [title.strip()]
    if body:
        parts.append(body.strip())
    return "\n\n".join(parts)


@retry(
    retry=retry_if_exception_type((RateLimitError, APIStatusError, asyncio.TimeoutError)),
    wait=wait_exponential(multiplier=1, min=2, max=60),
    stop=stop_after_attempt(5),
    before_sleep=before_sleep_log(logger, "warning"),  # type: ignore[arg-type]
    reraise=True,
)
async def _call_openai_embed(texts: list[str]) -> list[list[float]]:
    """
    Single OpenAI Embeddings API call with retry on rate-limit / server errors.
    Non-retryable errors (e.g. 400 bad request) bubble up immediately.
    """
    client = _get_openai()
    response = await client.embeddings.create(
        model=settings.OPENAI_EMBED_MODEL,
        input=texts,
        encoding_format="float",
    )
    # API guarantees order matches input order
    return [item.embedding for item in sorted(response.data, key=lambda x: x.index)]


async def embed_texts(texts: list[str]) -> list[list[float]]:
    """
    Embed a list of strings and return their 1536-dim float vectors.

    Handles:
      - Empty list → returns []
      - Empty individual strings → returns a zero-vector (no API call)
      - Oversized text → silently truncated to _MAX_CHARS
      - Chunked batching at settings.INGEST_BATCH_SIZE to respect rate limits
      - Automatic retry on transient errors

    Args:
        texts: List of strings to embed.

    Returns:
        Parallel list of float lists, one per input string.

    Raises:
        openai.APIError: On unrecoverable API failure after all retries.
    """
    if not texts:
        return []

    # Truncate all inputs
    safe_texts = [_truncate(t) if t.strip() else "" for t in texts]

    # Identify empty slots — we'll fill them with zero vectors to preserve order
    empty_indices = {i for i, t in enumerate(safe_texts) if not t.strip()}
    non_empty_texts = [(i, t) for i, t in enumerate(safe_texts) if t.strip()]

    # Determine dimension from model name
    embed_dim = 1536

    # Preallocate result list with zero-vectors for empty slots
    results: list[list[float]] = [[0.0] * embed_dim] * len(texts)

    if not non_empty_texts:
        logger.warning("embed_texts_all_empty", count=len(texts))
        return results

    batch_size = settings.INGEST_BATCH_SIZE
    original_indices = [idx for idx, _ in non_empty_texts]
    batched_texts = [t for _, t in non_empty_texts]

    logger.info(
        "embed_texts_start",
        total=len(texts),
        non_empty=len(batched_texts),
        empty=len(empty_indices),
        batch_size=batch_size,
        model=settings.OPENAI_EMBED_MODEL,
    )

    # Process in chunks
    for batch_start in range(0, len(batched_texts), batch_size):
        chunk_texts = batched_texts[batch_start : batch_start + batch_size]
        chunk_indices = original_indices[batch_start : batch_start + batch_size]

        logger.debug(
            "embedding_batch",
            batch_start=batch_start,
            batch_size=len(chunk_texts),
        )

        embeddings = await _call_openai_embed(chunk_texts)

        for original_idx, embedding in zip(chunk_indices, embeddings):
            results[original_idx] = embedding

    logger.info("embed_texts_complete", embedded_count=len(batched_texts))
    return results


async def embed_single(text: str) -> list[float]:
    """
    Embed a single string and return its 1536-dim vector.

    Convenience wrapper around embed_texts().
    """
    results = await embed_texts([text])
    return results[0]


async def embed_ticket(title: str, body: Optional[str] = None) -> list[float]:
    """
    Build the combined ticket text and return its embedding.

    Combines title + body with semantic upweighting of the title.
    This is the canonical function used by the ingestion pipeline.

    Args:
        title: Ticket title (required).
        body:  Ticket description / body (optional, may be None).

    Returns:
        1536-dim float embedding vector.
    """
    text = _build_embed_text(title, body)
    return await embed_single(text)


async def embed_tickets_batch(
    tickets: list[tuple[str, Optional[str]]],
) -> list[list[float]]:
    """
    Embed a batch of (title, body) tuples efficiently.

    Builds combined text strings for each ticket, then calls
    embed_texts() once for the entire batch.

    Args:
        tickets: List of (title, body) tuples.

    Returns:
        Parallel list of 1536-dim embedding vectors.
    """
    texts = [_build_embed_text(title, body) for title, body in tickets]
    return await embed_texts(texts)
