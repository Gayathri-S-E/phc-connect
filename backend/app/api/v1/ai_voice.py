"""Voice + multilingual endpoints (Google Speech-to-Text, Text-to-Speech, Translation).

Authenticated users only, rate limited per user, size limited. Audio and text content are never logged or stored.
When Google is not configured these answer 503 AI_NOT_CONFIGURED; they never fabricate transcripts or audio."""
import base64
import binascii
from typing import Awaitable, Callable, Tuple, TypeVar

from fastapi import APIRouter, Depends

from app.ai import safety
from app.ai.voice import (
    STT_ENCODINGS,
    SUPPORTED_LANGUAGES,
    VoiceClient,
    VoiceError,
    get_voice_client,
    resolve_language,
    stt_encoding_for,
)
from app.api.deps import AuthenticatedUserContext, get_current_user
from app.core.config import settings
from app.core.exceptions import AppException
from app.schemas.ai_voice import (
    VoiceCapabilities,
    VoiceSpeakRequest,
    VoiceSpeakResponse,
    VoiceTranscribeRequest,
    VoiceTranscribeResponse,
    VoiceTranslateRequest,
    VoiceTranslateResponse,
)
from app.schemas.common import DataResponse

router = APIRouter(prefix="/ai/voice", tags=["Voice and multilingual (Google)"])

T = TypeVar("T")
_MIN_AUDIO_BYTES = 200  # anything smaller cannot be speech


def _language(value: str) -> Tuple[str, str]:
    resolved = resolve_language(value)
    if not resolved:
        raise AppException("Unsupported Language",
                           f"Language is not supported. Supported: {', '.join(sorted(SUPPORTED_LANGUAGES))}.",
                           422, "UNSUPPORTED_LANGUAGE", extra={"supported": sorted(SUPPORTED_LANGUAGES)})
    return resolved


def _limit_rate(user: AuthenticatedUserContext, op: str) -> None:
    safety.rate_limiter.check(f"voice:{op}:{user.id}", limit=settings.AI_VOICE_RATE_LIMIT_PER_MINUTE)


def _text(value: str) -> str:
    cleaned = value.replace("\x00", "").strip()
    if not cleaned:
        raise AppException("Empty Text", "Text must not be empty.", 422, "VOICE_EMPTY_TEXT")
    if len(cleaned) > settings.AI_VOICE_MAX_TEXT_CHARS:
        raise AppException("Text Too Long", f"Text must be at most {settings.AI_VOICE_MAX_TEXT_CHARS} characters.",
                           413, "VOICE_TEXT_TOO_LONG")
    return cleaned


async def _call(fn: Callable[[], Awaitable[T]]) -> T:
    try:
        return await fn()
    except VoiceError as exc:
        messages = {
            "AI_NOT_CONFIGURED": "Voice services are not set up on this server yet.",
            "AI_TIMEOUT": "The voice service took too long. Please try again.",
            "AI_PROVIDER_RATE_LIMITED": "The voice service is busy. Please try again in a moment.",
            "AI_INPUT_REJECTED": "The voice service could not process that input.",
        }
        detail = messages.get(exc.code, "The voice service is unavailable. Please try again.")
        raise AppException("Voice Service Unavailable" if exc.status_code >= 500 else "Voice Request Failed", detail,
                           exc.status_code, exc.code, extra={"retryable": exc.status_code in (429, 502, 504)})


@router.get("/capabilities", response_model=DataResponse[VoiceCapabilities])
async def voice_capabilities(current_user: AuthenticatedUserContext = Depends(get_current_user),
                             voice: VoiceClient = Depends(get_voice_client)):
    """What is usable right now, so the UI can hide controls up front instead of failing on click."""
    avail = voice.availability() if hasattr(voice, "availability") else {"transcribe": True, "speak": True, "translate": True}
    return DataResponse(data=VoiceCapabilities(
        **avail, languages=SUPPORTED_LANGUAGES,
        max_audio_base64_chars=settings.AI_VOICE_MAX_AUDIO_BASE64_CHARS,
        max_text_chars=settings.AI_VOICE_MAX_TEXT_CHARS,
        accepted_audio_mime=sorted(STT_ENCODINGS)))


@router.post("/transcribe", response_model=DataResponse[VoiceTranscribeResponse])
async def transcribe(payload: VoiceTranscribeRequest,
                     current_user: AuthenticatedUserContext = Depends(get_current_user),
                     voice: VoiceClient = Depends(get_voice_client)):
    _limit_rate(current_user, "stt")
    short, locale = _language(payload.language)
    if len(payload.audio_base64) > settings.AI_VOICE_MAX_AUDIO_BASE64_CHARS:
        raise AppException("Audio Too Large", "Recording is too long. Please record a shorter message.",
                           413, "VOICE_AUDIO_TOO_LARGE")
    if not stt_encoding_for(payload.mime):
        raise AppException("Unsupported Audio", "This audio format is not supported.", 415, "VOICE_UNSUPPORTED_AUDIO",
                           extra={"accepted": sorted(STT_ENCODINGS)})
    try:
        raw = base64.b64decode(payload.audio_base64, validate=True)
    except (binascii.Error, ValueError):
        raise AppException("Invalid Audio", "Audio must be valid base64.", 422, "VOICE_INVALID_AUDIO")
    if len(raw) < _MIN_AUDIO_BYTES:
        raise AppException("Invalid Audio", "The recording is empty or too short.", 422, "VOICE_INVALID_AUDIO")
    text = await _call(lambda: voice.transcribe(payload.audio_base64, payload.mime, locale))
    return DataResponse(data=VoiceTranscribeResponse(text=text, language=short, locale=locale))


@router.post("/speak", response_model=DataResponse[VoiceSpeakResponse])
async def speak(payload: VoiceSpeakRequest,
                current_user: AuthenticatedUserContext = Depends(get_current_user),
                voice: VoiceClient = Depends(get_voice_client)):
    _limit_rate(current_user, "tts")
    short, locale = _language(payload.language)
    text = _text(payload.text)
    audio = await _call(lambda: voice.synthesize(text, locale))
    return DataResponse(data=VoiceSpeakResponse(audio_base64=audio, mime="audio/mpeg", language=short, locale=locale))


@router.post("/translate", response_model=DataResponse[VoiceTranslateResponse])
async def translate(payload: VoiceTranslateRequest,
                    current_user: AuthenticatedUserContext = Depends(get_current_user),
                    voice: VoiceClient = Depends(get_voice_client)):
    _limit_rate(current_user, "translate")
    short, _ = _language(payload.target_language)
    text = _text(payload.text)
    out, detected = await _call(lambda: voice.translate(text, short))
    return DataResponse(data=VoiceTranslateResponse(text=out, target_language=short, detected_source_language=detected))
