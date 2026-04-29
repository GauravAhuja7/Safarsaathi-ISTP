"""IMD JWT token manager — auto-generates and caches the bearer token."""
import asyncio
import logging
import time
from dataclasses import dataclass, field

import httpx

from app.config import settings

logger = logging.getLogger(__name__)

TOKEN_URL = "https://api.imd.gov.in/api/oauth/token.php"

# Refresh 5 minutes before actual expiry to avoid mid-request failures
REFRESH_BUFFER_SECS = 300


@dataclass
class _TokenCache:
    token: str = ""
    expires_at: float = 0.0
    _lock: asyncio.Lock = field(default_factory=asyncio.Lock, repr=False)

    def is_valid(self) -> bool:
        return bool(self.token) and time.time() < (self.expires_at - REFRESH_BUFFER_SECS)


_cache = _TokenCache()


async def get_token() -> str:
    """
    Return a valid JWT bearer token for the IMD API.
    Generates a new one if missing or expiring, otherwise returns cached.
    Raises RuntimeError if credentials are missing or IMD rejects them.
    """
    async with _cache._lock:
        if _cache.is_valid():
            return _cache.token

        if not settings.imd_email or not settings.imd_password:
            raise RuntimeError(
                "IMD_EMAIL and IMD_PASSWORD must be set in .env — "
                "get credentials from https://api.imd.gov.in"
            )

        logger.info("IMD: requesting new JWT token for %s", settings.imd_email)
        async with httpx.AsyncClient(timeout=15) as client:
            r = await client.post(
                TOKEN_URL,
                json={"email": settings.imd_email, "password": settings.imd_password},
                headers={"Content-Type": "application/json"},
            )

        if r.status_code != 200:
            raise RuntimeError(f"IMD token request failed: HTTP {r.status_code} — {r.text[:200]}")

        data = r.json()
        token = data.get("access_token")
        if not token:
            raise RuntimeError(f"IMD token response missing access_token: {data}")

        expires_in = int(data.get("expires_in", 3600))
        _cache.token = token
        _cache.expires_at = time.time() + expires_in
        logger.info("IMD: JWT obtained, valid for %ds", expires_in)
        return token


def imd_headers() -> dict:
    """Sync headers dict — call only after awaiting get_token()."""
    return {
        "X-API-KEY": settings.imd_api_key,
        "Authorization": f"Bearer {_cache.token}",
        "Accept": "application/json",
    }
