"""Optional Google Vertex AI forecasting hook.

WHAT IS REAL: the interface, the config selection, the clean failure mode and `VertexEndpointBackend`, a REST client
for a deployed Vertex AI endpoint (`:predict`, service-account bearer token from app.integrations.google.auth).
WHAT IS NOT: no model is trained or deployed by this repo. The endpoint you deploy must accept
`{"instances": [{"series": [floats], "horizon_days": int}]}` and return `{"predictions": [[floats]]}` (or
`[{"forecast": [floats]}]`). Anything else is rejected as malformed; no prediction is ever fabricated.

Selection: env FORECAST_BACKEND = "local" (default, statistical model in forecast_federation_service) | "vertex".
"""
import logging
import os
from dataclasses import dataclass
from typing import List, Protocol, Sequence, runtime_checkable

from fastapi import status

import httpx

from app.core.exceptions import AppException
from app.integrations.google import auth as google_auth
from app.integrations.google.errors import GoogleError

logger = logging.getLogger("app.vertex")


class VertexNotConfigured(AppException):
    def __init__(self, detail: str = "Vertex AI forecasting backend is not configured."):
        super().__init__(title="Vertex AI Not Configured", detail=detail,
                         status_code=status.HTTP_501_NOT_IMPLEMENTED, error_code="VERTEX_NOT_CONFIGURED")


@dataclass
class VertexForecast:
    daily_forecast: List[float]
    model: str


@runtime_checkable
class VertexForecastBackend(Protocol):
    async def forecast(self, series: Sequence[float], horizon_days: int) -> VertexForecast: ...


class VertexEndpointBackend:
    def __init__(self, project: str, location: str, endpoint_id: str, timeout: float = 30.0,
                 transport: "httpx.AsyncBaseTransport | None" = None, token_provider=None):
        self.url = (f"https://{location}-aiplatform.googleapis.com/v1/projects/{project}/locations/{location}"
                    f"/endpoints/{endpoint_id}:predict")
        self.model = f"vertex:{endpoint_id}"
        self.timeout, self._transport = timeout, transport
        self._token = token_provider or google_auth.get_access_token

    async def forecast(self, series: Sequence[float], horizon_days: int) -> VertexForecast:
        try:
            token = await self._token()
        except GoogleError as exc:
            raise VertexNotConfigured(f"Google credentials unavailable: {exc}") from exc
        body = {"instances": [{"series": [float(x) for x in series], "horizon_days": int(horizon_days)}]}
        try:
            async with httpx.AsyncClient(timeout=self.timeout, transport=self._transport) as client:
                resp = await client.post(self.url, json=body, headers={"Authorization": f"Bearer {token}"})
        except httpx.TimeoutException:
            raise AppException("Vertex Timeout", "The Vertex AI forecast timed out.", 504, "VERTEX_TIMEOUT")
        except httpx.HTTPError:
            raise AppException("Vertex Unavailable", "Vertex AI could not be reached.", 502, "VERTEX_UNAVAILABLE")
        if resp.status_code != 200:
            logger.error("Vertex predict failed: status=%s", resp.status_code)  # status only, never the body
            raise AppException("Vertex Error", "Vertex AI rejected the forecast request.",
                               429 if resp.status_code == 429 else 502, "VERTEX_ERROR")
        try:
            pred = resp.json()["predictions"][0]
            values = pred.get("forecast") if isinstance(pred, dict) else pred
            out = [float(v) for v in values]
        except (KeyError, IndexError, TypeError, ValueError, AttributeError):
            raise AppException("Vertex Malformed", "Vertex AI returned an unexpected response.", 502, "VERTEX_MALFORMED")
        if len(out) != horizon_days or any(v < 0 for v in out):
            raise AppException("Vertex Malformed", "Vertex AI returned an invalid forecast.", 502, "VERTEX_MALFORMED")
        return VertexForecast(daily_forecast=out, model=self.model)


class UnconfiguredVertexBackend:
    def __init__(self, reason: str):
        self.reason = reason

    async def forecast(self, series: Sequence[float], horizon_days: int) -> VertexForecast:
        raise VertexNotConfigured(self.reason)


def get_vertex_backend() -> VertexForecastBackend:
    """Dependency seam (tests/production replace it). Currently always the not-configured stub."""
    selected = os.environ.get("FORECAST_BACKEND", "local").strip().lower()
    if selected != "vertex":
        return UnconfiguredVertexBackend("FORECAST_BACKEND is not 'vertex'; only the local statistical model is active.")
    missing = [k for k in ("VERTEX_PROJECT", "VERTEX_LOCATION", "VERTEX_ENDPOINT_ID") if not os.environ.get(k)]
    if missing:
        return UnconfiguredVertexBackend(f"Missing Vertex configuration: {', '.join(missing)}.")
    if not google_auth.is_configured():
        return UnconfiguredVertexBackend("Vertex needs a Google service account (GOOGLE_APPLICATION_CREDENTIALS).")
    return VertexEndpointBackend(os.environ["VERTEX_PROJECT"], os.environ["VERTEX_LOCATION"], os.environ["VERTEX_ENDPOINT_ID"])
