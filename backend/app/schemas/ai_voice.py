from typing import Dict, List, Optional

from pydantic import BaseModel, Field


class VoiceTranscribeRequest(BaseModel):
    # Size is enforced in the endpoint (413) against settings.AI_VOICE_MAX_AUDIO_BASE64_CHARS.
    audio_base64: str = Field(..., min_length=1)
    mime: str = Field(..., min_length=1, max_length=100)
    language: str = Field("en", max_length=16)


class VoiceTranscribeResponse(BaseModel):
    text: str
    language: str
    locale: str


class VoiceSpeakRequest(BaseModel):
    text: str = Field(..., min_length=1)  # length enforced in the endpoint (413) against AI_VOICE_MAX_TEXT_CHARS
    language: str = Field("en", max_length=16)


class VoiceSpeakResponse(BaseModel):
    audio_base64: str
    mime: str = "audio/mpeg"
    language: str
    locale: str


class VoiceTranslateRequest(BaseModel):
    text: str = Field(..., min_length=1)
    target_language: str = Field(..., max_length=16)


class VoiceTranslateResponse(BaseModel):
    text: str
    target_language: str
    detected_source_language: Optional[str] = None


class VoiceCapabilities(BaseModel):
    transcribe: bool
    speak: bool
    translate: bool
    languages: Dict[str, str]
    max_audio_base64_chars: int
    max_text_chars: int
    accepted_audio_mime: List[str]
