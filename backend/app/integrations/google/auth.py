"""Service-account OAuth2 access tokens (used by BigQuery, later Vertex AI).

Credentials come from GOOGLE_SERVICE_ACCOUNT_JSON (inline JSON) or GOOGLE_APPLICATION_CREDENTIALS (path to a JSON
file). Tokens are cached per scope set until shortly before expiry. The blocking refresh runs in a worker thread.
Nothing here is ever logged or returned to clients.
"""
import asyncio
import json
import logging
from datetime import datetime, timedelta, timezone
from typing import Dict, Iterable, Optional, Tuple

from app.core.config import settings
from app.integrations.google.errors import GoogleError, NotConfigured

logger = logging.getLogger("app.integrations.google.auth")

CLOUD_PLATFORM_SCOPE = "https://www.googleapis.com/auth/cloud-platform"
BIGQUERY_SCOPE = "https://www.googleapis.com/auth/bigquery"

_cache: Dict[Tuple[str, ...], Tuple[str, datetime]] = {}
_lock = asyncio.Lock()
_SKEW = timedelta(seconds=120)


def is_configured() -> bool:
    return bool(settings.GOOGLE_SERVICE_ACCOUNT_JSON.strip() or settings.GOOGLE_APPLICATION_CREDENTIALS.strip())


def _load_info() -> dict:
    inline = settings.GOOGLE_SERVICE_ACCOUNT_JSON.strip()
    try:
        if inline:
            return json.loads(inline)
        path = settings.GOOGLE_APPLICATION_CREDENTIALS.strip()
        if not path:
            raise NotConfigured("no service-account credentials set")
        with open(path, "r", encoding="utf-8") as fh:
            return json.load(fh)
    except NotConfigured:
        raise
    except (OSError, ValueError) as exc:
        raise NotConfigured(f"service-account credentials unreadable: {type(exc).__name__}") from None


def _refresh_blocking(scopes: Tuple[str, ...]) -> Tuple[str, datetime]:
    from google.auth.transport.requests import Request
    from google.oauth2 import service_account

    info = _load_info()
    try:
        creds = service_account.Credentials.from_service_account_info(info, scopes=list(scopes))
        creds.refresh(Request())
    except NotConfigured:
        raise
    except ValueError:
        raise NotConfigured("service-account JSON is invalid") from None
    except Exception as exc:  # google.auth.exceptions.*, requests errors
        logger.error("Google token refresh failed: %s", type(exc).__name__)
        raise GoogleError(f"token refresh failed: {type(exc).__name__}") from None
    expiry = creds.expiry.replace(tzinfo=timezone.utc) if creds.expiry else datetime.now(timezone.utc) + timedelta(minutes=50)
    return creds.token, expiry


async def get_access_token(scopes: Iterable[str] = (CLOUD_PLATFORM_SCOPE,)) -> str:
    """Return a valid Bearer token for the scopes, refreshing (in a thread) when missing or near expiry."""
    if not is_configured():
        raise NotConfigured("no service-account credentials set")
    key = tuple(sorted(scopes))
    async with _lock:
        hit = _cache.get(key)
        if hit and hit[1] - _SKEW > datetime.now(timezone.utc):
            return hit[0]
        token, expiry = await asyncio.to_thread(_refresh_blocking, key)
        _cache[key] = (token, expiry)
        return token


def clear_cache() -> None:
    _cache.clear()
