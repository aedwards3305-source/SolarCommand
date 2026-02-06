"""Authentication and authorization helpers (MVP: API key auth)."""

from fastapi import Depends, HTTPException, Security, status
from fastapi.security import APIKeyHeader

from app.core.config import get_settings

api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)


async def verify_api_key(
    api_key: str | None = Security(api_key_header),
) -> str:
    """MVP auth: simple API key check. Replace with JWT in v2."""
    settings = get_settings()
    # In MVP, skip auth if no key is configured (local dev)
    if not getattr(settings, "api_key", None):
        return "dev"
    if api_key and api_key == settings.api_key:
        return api_key
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid or missing API key",
    )
