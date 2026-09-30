"""Google Gemini provider client (REST). The only place that talks to the AI provider.

The API key is read from server settings and sent in a header, never in a URL, log line or response.
"""
import asyncio
import logging
import os
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Protocol

import httpx

from app.core.config import settings

logger = logging.getLogger("app.ai.llm")


class LLMError(Exception):
    """Base error. `code` is safe to show to users; `detail` is for server logs only."""
    code = "AI_UNAVAILABLE"

    def __init__(self, detail: str = ""):
        super().__init__(detail)
        self.detail = detail


class LLMNotConfigured(LLMError):
    code = "AI_NOT_CONFIGURED"


class LLMTimeout(LLMError):
    code = "AI_TIMEOUT"


class LLMRateLimited(LLMError):
    code = "AI_PROVIDER_RATE_LIMITED"


class LLMBlocked(LLMError):
    code = "AI_RESPONSE_BLOCKED"


class LLMMalformed(LLMError):
    code = "AI_MALFORMED_RESPONSE"


@dataclass
class FunctionCall:
    name: str
    args: Dict[str, Any]


@dataclass
class LLMResult:
    text: str
    function_calls: List[FunctionCall] = field(default_factory=list)
    model_content: Optional[Dict[str, Any]] = None  # raw model turn, echoed back verbatim in the tool loop


class LLMClient(Protocol):
    async def generate(self, system: str, contents: List[Dict[str, Any]],
                       tools: List[Dict[str, Any]]) -> LLMResult: ...


class GeminiClient:
    def __init__(self, api_key: Optional[str] = None, model: Optional[str] = None,
                 base_url: Optional[str] = None, timeout: Optional[float] = None,
                 transport: Optional[httpx.AsyncBaseTransport] = None):
        self.api_key = settings.GEMINI_API_KEY if api_key is None else api_key
        self.model = model or settings.GEMINI_MODEL
        self.base_url = (base_url or settings.GEMINI_API_BASE).rstrip("/")
        self.timeout = timeout or settings.AI_REQUEST_TIMEOUT_SECONDS
        self._transport = transport

    async def generate(self, system: str, contents: List[Dict[str, Any]],
                       tools: List[Dict[str, Any]]) -> LLMResult:
        url, headers = await self._endpoint()

        body: Dict[str, Any] = {
            "systemInstruction": {"parts": [{"text": system}]},
            "contents": contents,
            "generationConfig": {"temperature": 0.3, "maxOutputTokens": 1500},
            "safetySettings": [
                # Health education legitimately discusses symptoms and medicines; block only high-severity output.
                {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_ONLY_HIGH"},
                {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
                {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
                {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
            ],
        }
        if tools:
            body["tools"] = [{"functionDeclarations": tools}]
            body["toolConfig"] = {"functionCallingConfig": {"mode": "AUTO"}}

        last: Optional[LLMError] = None
        for attempt in range(2):  # one retry for transient failures only
            try:
                async with httpx.AsyncClient(timeout=self.timeout, transport=self._transport) as client:
                    resp = await client.post(url, json=body, headers=headers)
            except httpx.TimeoutException:
                last = LLMTimeout("provider timeout")
            except httpx.HTTPError as exc:
                last = LLMError(f"network error: {type(exc).__name__}")
            else:
                if resp.status_code == 200:
                    return self._parse(resp.json())
                if resp.status_code == 429:
                    last = LLMRateLimited("provider rate limit")
                elif resp.status_code >= 500:
                    last = LLMError(f"provider status {resp.status_code}")
                else:
                    # 4xx (bad key, bad request): not retryable. Log status only, never the body or key.
                    logger.error("Gemini rejected request: status=%s", resp.status_code)
                    raise LLMError(f"provider status {resp.status_code}")
            if attempt == 0:
                await asyncio.sleep(0.4)
        assert last is not None
        raise last

    async def _endpoint(self):
        if not self.api_key:
            raise LLMNotConfigured("GEMINI_API_KEY is not set")
        return (f"{self.base_url}/models/{self.model}:generateContent",
                {"x-goog-api-key": self.api_key, "Content-Type": "application/json"})

    @staticmethod
    def _parse(data: Dict[str, Any]) -> LLMResult:
        if not isinstance(data, dict):
            raise LLMMalformed("non-object response")
        block = (data.get("promptFeedback") or {}).get("blockReason")
        if block:
            raise LLMBlocked(f"prompt blocked: {block}")
        candidates = data.get("candidates") or []
        if not candidates:
            raise LLMMalformed("no candidates")
        cand = candidates[0]
        if cand.get("finishReason") in ("SAFETY", "PROHIBITED_CONTENT", "BLOCKLIST", "SPII"):
            raise LLMBlocked(f"response blocked: {cand.get('finishReason')}")
        content = cand.get("content") or {}
        parts = content.get("parts") or []
        text = "".join(p.get("text", "") for p in parts if isinstance(p, dict) and not p.get("thought"))
        calls = [
            FunctionCall(name=p["functionCall"]["name"], args=dict(p["functionCall"].get("args") or {}))
            for p in parts if isinstance(p, dict) and isinstance(p.get("functionCall"), dict)
            and p["functionCall"].get("name")
        ]
        if not text.strip() and not calls:
            raise LLMMalformed("empty response")
        return LLMResult(text=text.strip(), function_calls=calls, model_content=content or None)


class VertexGeminiClient(GeminiClient):
    """Gemini through Vertex AI: authenticates with the Google service account (no API key), billed to the GCP project."""

    def __init__(self, project: Optional[str] = None, location: Optional[str] = None, model: Optional[str] = None,
                 timeout: Optional[float] = None, transport: Optional[httpx.AsyncBaseTransport] = None,
                 token_provider=None):
        super().__init__(api_key="vertex", model=model, timeout=timeout, transport=transport)
        self.project = project or settings.GOOGLE_CLOUD_PROJECT or os.environ.get("VERTEX_PROJECT", "")
        self.location = location or settings.GEMINI_VERTEX_LOCATION
        self._token_provider = token_provider

    async def _endpoint(self):
        from app.integrations.google import auth as google_auth
        from app.integrations.google.errors import GoogleError
        if not self.project:
            raise LLMNotConfigured("GOOGLE_CLOUD_PROJECT is not set")
        try:
            token = await (self._token_provider or google_auth.get_access_token)()
        except GoogleError as exc:
            raise LLMNotConfigured(f"Google service account unavailable: {exc}") from exc
        host = "aiplatform.googleapis.com" if self.location == "global" else f"{self.location}-aiplatform.googleapis.com"
        url = (f"https://{host}/v1/projects/{self.project}/locations/{self.location}"
               f"/publishers/google/models/{self.model}:generateContent")
        return url, {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}


def get_llm_client() -> LLMClient:
    """Dependency seam: tests replace this. auto = Vertex (service account) when configured, else the API key."""
    mode = (settings.GEMINI_BACKEND or "auto").lower()
    if mode == "vertex":
        return VertexGeminiClient()
    if mode == "auto":
        from app.integrations.google import auth as google_auth
        if google_auth.is_configured() and (settings.GOOGLE_CLOUD_PROJECT or os.environ.get("VERTEX_PROJECT")):
            return VertexGeminiClient()
    return GeminiClient()


def gemini_configured() -> bool:
    """True when the assistants can reach Gemini (Vertex service account, or an API key)."""
    return isinstance(get_llm_client(), VertexGeminiClient) or bool(settings.GEMINI_API_KEY)
