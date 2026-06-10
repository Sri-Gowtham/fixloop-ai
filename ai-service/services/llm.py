"""
services/llm.py
---------------
Unified single-provider LLM layer for FixLoop AI.
Uses Groq exclusively.
"""

from typing import Optional
from groq import AsyncGroq
import structlog
from tenacity import retry, stop_after_attempt, wait_exponential

from core.config import settings

logger = structlog.get_logger(__name__)

_groq_client: Optional[AsyncGroq] = None

def _get_groq() -> AsyncGroq:
    """Return (or lazily create) the shared AsyncGroq client."""
    global _groq_client
    if _groq_client is None:
        if not settings.GROQ_API_KEY:
            raise RuntimeError("GROQ_API_KEY is not set.")
        _groq_client = AsyncGroq(api_key=settings.GROQ_API_KEY)
    return _groq_client


@retry(stop=stop_after_attempt(3), wait=wait_exponential(min=2, max=30), reraise=True)
async def generate_cluster_labels(system_prompt: str, user_prompt: str) -> str:
    """Call Groq to generate labels for a batch of clusters."""
    client = _get_groq()
    resp = await client.chat.completions.create(
        model=settings.GROQ_MODEL,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user",   "content": user_prompt},
        ],
        temperature=0.2,
        response_format={"type": "json_object"},
    )
    return resp.choices[0].message.content or "[]"


@retry(stop=stop_after_attempt(3), wait=wait_exponential(min=2, max=30), reraise=True)
async def generate_investigation(system_prompt: str, user_prompt: str) -> str:
    """Call Groq to generate a root-cause investigation."""
    client = _get_groq()
    resp = await client.chat.completions.create(
        model=settings.GROQ_MODEL,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user",   "content": user_prompt},
        ],
        temperature=0.1,
        response_format={"type": "json_object"},
    )
    return resp.choices[0].message.content or "{}"


@retry(stop=stop_after_attempt(3), wait=wait_exponential(min=2, max=30), reraise=True)
async def generate_recommendation(system_prompt: str, user_prompt: str) -> str:
    """Call Groq to generate fix recommendations."""
    client = _get_groq()
    resp = await client.chat.completions.create(
        model=settings.GROQ_MODEL,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user",   "content": user_prompt},
        ],
        temperature=0.2,
        response_format={"type": "json_object"},
    )
    return resp.choices[0].message.content or "{}"
