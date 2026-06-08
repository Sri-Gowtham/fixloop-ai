"""
api/deps.py
-----------
FastAPI dependency injection helpers.

Provides:
  - get_supabase_client  — injected Supabase AsyncClient
  - get_current_user     — validates Supabase JWT and returns user profile
  - require_role         — role-based access control factory

Usage in route handlers:
    @router.post("/ai/ingest")
    async def ingest(
        ...,
        sb:   AsyncClient = Depends(get_supabase_client),
        user: UserOut     = Depends(get_current_user),
    ): ...
"""

from __future__ import annotations

from functools import lru_cache
from typing import Annotated

import structlog
from fastapi import Depends, HTTPException, Security, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from services.supabase_client import get_supabase

logger = structlog.get_logger(__name__)

bearer_scheme = HTTPBearer(auto_error=False)


# ----------------------------------------------------------------
# Supabase client dependency
# ----------------------------------------------------------------
async def get_supabase_client():
    """Yield the shared Supabase AsyncClient (service-role)."""
    return await get_supabase()


# ----------------------------------------------------------------
# Auth dependency
# ----------------------------------------------------------------
async def get_current_user(
    credentials: Annotated[
        HTTPAuthorizationCredentials | None,
        Security(bearer_scheme),
    ] = None,
) -> dict:
    """
    Validate a Supabase-issued JWT and return the authenticated user's profile.

    TODO: implement JWT verification using supabase.auth.get_user(token)
          and look up public.users row for the returned uid.

    Raises:
        401 if no token or token is invalid.
    """
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing Bearer token",
        )

    token = credentials.credentials

    # TODO: verify token with Supabase and fetch user profile
    # sb = await get_supabase()
    # user_response = await sb.auth.get_user(token)
    # if user_response.user is None:
    #     raise HTTPException(status_code=401, detail="Invalid token")
    # return user_response.user

    raise NotImplementedError("get_current_user: JWT validation not yet implemented")


def require_role(*roles: str):
    """
    Dependency factory that enforces minimum role access.

    Usage:
        Depends(require_role("owner", "admin"))

    TODO: implement once get_current_user returns a UserOut with a role field.
    """
    async def _check(user: dict = Depends(get_current_user)) -> dict:
        # TODO: check user["role"] in roles, raise 403 if not
        raise NotImplementedError("require_role: not yet implemented")
    return _check
