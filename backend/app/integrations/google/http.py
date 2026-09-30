"""Shared REST transport for the Google integrations: retry once on transient failures, never log bodies or secrets."""
import asyncio
import logging
from typing import Any, Dict, Optional

import httpx

from app.integrations.google.errors import (
    GoogleError, GoogleRateLimited, GoogleRejected, GoogleTimeout,
)

logger = logging.getLogger("app.integrations.google.http")


async def request_json(method: str, url: str, *, headers: Dict[str, str], json_body: Any = None,
                       params: Optional[Dict[str, Any]] = None, timeout: float = 15.0,
                       transport: Optional[httpx.AsyncBaseTransport] = None) -> Any:
    last: Optional[GoogleError] = None
    for attempt in range(2):
        try:
            async with httpx.AsyncClient(timeout=timeout, transport=transport) as client:
                resp = await client.request(method, url, json=json_body, params=params, headers=headers)
        except httpx.TimeoutException:
            last = GoogleTimeout("provider timeout")
        except httpx.HTTPError as exc:
            last = GoogleError(f"network error: {type(exc).__name__}")
        else:
            if resp.status_code == 200:
                try:
                    return resp.json() if resp.content else {}
                except ValueError:
                    raise GoogleError("invalid json") from None
            if resp.status_code == 429:
                last = GoogleRateLimited("provider rate limit")
            elif resp.status_code >= 500:
                last = GoogleError(f"provider status {resp.status_code}")
            else:
                logger.error("Google API rejected request: status=%s", resp.status_code)
                raise GoogleRejected(f"provider status {resp.status_code}", resp.status_code)
        if attempt == 0:
            await asyncio.sleep(0.4)
    assert last is not None
    raise last
