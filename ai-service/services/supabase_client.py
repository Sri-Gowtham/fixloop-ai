"""
services/supabase_client.py
---------------------------
Supabase client singleton using the service-role key.
The service-role key bypasses Row Level Security — it is used
exclusively by the backend AI pipeline, never exposed to the browser.

Usage:
    from services.supabase_client import get_supabase
    sb = get_supabase()
    result = await sb.table("tickets").select("*").execute()
"""

from functools import lru_cache

import structlog
from supabase import AsyncClient, acreate_client

from core.config import settings

logger = structlog.get_logger(__name__)

_client: AsyncClient | None = None


async def get_supabase() -> AsyncClient:
    """
    Returns the shared Supabase AsyncClient.
    Initialised lazily on first call and re-used across requests.

    TODO: replace with connection-pool wrapper when traffic grows.
    """
    global _client
    if _client is None:
        logger.info("supabase_client_init", url=settings.SUPABASE_URL)
        _client = await acreate_client(
            settings.SUPABASE_URL,
            settings.SUPABASE_SERVICE_ROLE_KEY,
        )
    return _client
