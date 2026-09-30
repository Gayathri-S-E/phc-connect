"""Google Cloud voice/translation provider client (REST): Speech-to-Text, Text-to-Speech, Translation.

The only place that talks to those services. The API key comes from server settings and is sent in a header, never in
a URL, log line or response. Audio and text content are never logged (status codes only).
"""
import asyncio
import logging
from typing import Dict, Optional, Protocol, Tuple

import httpx

from app.core.config import settings

logger = logging.getLogger("app.ai.voice")


# --------------------------------------------------------------------------- languages
# Adding a language is one entry here: short code -> BCP-47 locale used by speech services.
# The short code is also the Translation API language code.
SUPPORTED_LANGUAGES: Dict[str, str] = {
    "en": "en-IN",
    "ta": "ta-IN",
    "hi": "hi-IN",
}


def resolve_language(value: Optional[str]) -> Optional[Tuple[str, str]]:
    """Accept 'ta' or 'ta-IN' (any case). Returns (short_code, locale) or None if unsupported."""
    if not value or not isinstance(value, str):
        return None
    v = value.strip().replace("_", "-").lower()
    short = v.split("-")[0]
    if short not in SUPPORTED_LANGUAGES:
        return None
    locale = SUPPORTED_LANGUAGES[short]
    if "-" in v and v != locale.lower():
        return None  # e.g. 'ta-LK' is not a supported locale
    return short, locale


# Browser MediaRecorder mime (codec parameters stripped) -> Speech-to-Text v1 encoding.
STT_ENCODINGS: Dict[str, str] = {
    "audio/webm": "WEBM_OPUS",
    "audio/ogg": "OGG_OPUS",
    "audio/wav": "LINEAR16",
    "audio/x-wav": "LINEAR16",
    "audio/wave": "LINEAR16",
}


def stt_encoding_for(mime: Optional[str]) -> Optional[str]:
    if not mime or not isinstance(mime, str):
        return None
    return STT_ENCODINGS.get(mime.split(";")[0].strip().lower())


# --------------------------------------------------------------------------- errors
class VoiceError(Exception):
    """Base error. `code` is safe to show to users; `detail` is for server logs only."""
    code = "AI_UNAVAILABLE"
    status_code = 502

    def __init__(self, detail: str = ""):
        super().__init__(detail)
        self.detail = detail


class VoiceNotConfigured(VoiceError):
    code = "AI_NOT_CONFIGURED"
    status_code = 503


class VoiceTimeout(VoiceError):
    code = "AI_TIMEOUT"
    status_code = 504


class VoiceRateLimited(VoiceError):
    code = "AI_PROVIDER_RATE_LIMITED"
    status_code = 429


class VoiceMalformed(VoiceError):
    code = "AI_MALFORMED_RESPONSE"
    status_code = 502


class VoiceRejected(VoiceError):
    """Provider refused the input (e.g. audio it cannot decode)."""
    code = "AI_INPUT_REJECTED"
    status_code = 422


# --------------------------------------------------------------------------- protocol + client
class VoiceClient(Protocol):
    async def transcribe(self, audio_base64: str, mime: str, locale: str) -> str: ...

    async def synthesize(self, text: str, locale: str) -> str: ...  # returns base64 MP3

    async def translate(self, text: str, target: str) -> Tuple[str, Optional[str]]: ...  # (text, detected source)


class GoogleVoiceClient:
    def __init__(self, api_key: Optional[str] = None, timeout: Optional[float] = None,
                 transport: Optional[httpx.AsyncBaseTransport] = None,
                 stt_base: Optional[str] = None, tts_base: Optional[str] = None,
                 translate_base: Optional[str] = None, project: Optional[str] = None,
                 stt_enabled: Optional[bool] = None, tts_enabled: Optional[bool] = None,
                 translate_enabled: Optional[bool] = None):
        self.api_key = settings.GOOGLE_CLOUD_API_KEY if api_key is None else api_key
        self.project = settings.GOOGLE_CLOUD_PROJECT if project is None else project
        self.timeout = timeout or settings.AI_REQUEST_TIMEOUT_SECONDS
        self._transport = transport
        self.stt_base = (stt_base or settings.GOOGLE_STT_API_BASE).rstrip("/")
        self.tts_base = (tts_base or settings.GOOGLE_TTS_API_BASE).rstrip("/")
        self.translate_base = (translate_base or settings.GOOGLE_TRANSLATE_API_BASE).rstrip("/")
        self.stt_enabled = settings.GOOGLE_STT_ENABLED if stt_enabled is None else stt_enabled
        self.tts_enabled = settings.GOOGLE_TTS_ENABLED if tts_enabled is None else tts_enabled
        self.translate_enabled = settings.GOOGLE_TRANSLATE_ENABLED if translate_enabled is None else translate_enabled

    # -- availability (used by /capabilities and the guards below)
    def availability(self) -> Dict[str, bool]:
        ok = bool(self.api_key)
        return {"transcribe": ok and self.stt_enabled, "speak": ok and self.tts_enabled,
                "translate": ok and self.translate_enabled}

    def _require(self, feature: str, name: str) -> None:
        if not self.api_key:
            raise VoiceNotConfigured("GOOGLE_CLOUD_API_KEY is not set")
        if not self.availability()[feature]:
            raise VoiceNotConfigured(f"{name} is disabled by configuration")

    # -- operations
    async def transcribe(self, audio_base64: str, mime: str, locale: str) -> str:
        self._require("transcribe", "Speech-to-Text")
        encoding = stt_encoding_for(mime)
        if not encoding:
            raise VoiceRejected("unsupported audio mime type")
        config = {"encoding": encoding, "languageCode": locale, "enableAutomaticPunctuation": True,
                  "maxAlternatives": 1}
        body = {"config": config, "audio": {"content": audio_base64}}
        data = await self._post(f"{self.stt_base}/speech:recognize", body)
        if not isinstance(data, dict):
            raise VoiceMalformed("non-object response")
        parts = []
        for res in data.get("results") or []:
            alts = res.get("alternatives") or []
            if alts and isinstance(alts[0], dict) and alts[0].get("transcript"):
                parts.append(str(alts[0]["transcript"]).strip())
        return " ".join(p for p in parts if p)  # empty string == nothing intelligible heard (a real result)

    async def synthesize(self, text: str, locale: str) -> str:
        self._require("speak", "Text-to-Speech")
        body = {"input": {"text": text}, "voice": {"languageCode": locale},
                "audioConfig": {"audioEncoding": "MP3", "speakingRate": 0.95}}
        data = await self._post(f"{self.tts_base}/text:synthesize", body)
        audio = data.get("audioContent") if isinstance(data, dict) else None
        if not isinstance(audio, str) or not audio:
            raise VoiceMalformed("no audioContent")
        return audio

    async def translate(self, text: str, target: str) -> Tuple[str, Optional[str]]:
        self._require("translate", "Translation")
        body = {"q": text, "target": target, "format": "text"}
        data = await self._post(self.translate_base, body)
        try:
            item = data["data"]["translations"][0]
            out = item["translatedText"]
        except (KeyError, IndexError, TypeError):
            raise VoiceMalformed("no translations") from None
        if not isinstance(out, str) or not out.strip():
            raise VoiceMalformed("empty translation")
        return out, item.get("detectedSourceLanguage")

    # -- transport
    async def _post(self, url: str, body: dict):
        headers = {"x-goog-api-key": self.api_key, "Content-Type": "application/json"}
        if self.project:
            headers["x-goog-user-project"] = self.project
        last: Optional[VoiceError] = None
        for attempt in range(2):  # one retry for transient failures only
            try:
                async with httpx.AsyncClient(timeout=self.timeout, transport=self._transport) as client:
                    resp = await client.post(url, json=body, headers=headers)
            except httpx.TimeoutException:
                last = VoiceTimeout("provider timeout")
            except httpx.HTTPError as exc:
                last = VoiceError(f"network error: {type(exc).__name__}")
            else:
                if resp.status_code == 200:
                    try:
                        return resp.json()
                    except ValueError:
                        raise VoiceMalformed("invalid json") from None
                if resp.status_code == 429:
                    last = VoiceRateLimited("provider rate limit")
                elif resp.status_code >= 500:
                    last = VoiceError(f"provider status {resp.status_code}")
                else:
                    # 4xx: not retryable. Status only - never the body (may echo content) or the key.
                    logger.error("Google voice API rejected request: status=%s", resp.status_code)
                    if resp.status_code == 400:
                        raise VoiceRejected("provider status 400")
                    raise VoiceError(f"provider status {resp.status_code}")
            if attempt == 0:
                await asyncio.sleep(0.4)
        assert last is not None
        raise last


def get_voice_client() -> VoiceClient:
    """Dependency seam: tests replace this to inject a fake or a MockTransport-backed client."""
    return GoogleVoiceClient()
