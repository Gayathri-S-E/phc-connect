"""Voice + multilingual endpoints. Google is replaced by fakes / httpx.MockTransport; no real Google traffic."""
import base64

import httpx
import pytest
import pytest_asyncio

from app.ai import safety
from app.ai.voice import (
    GoogleVoiceClient,
    SUPPORTED_LANGUAGES,
    VoiceError,
    VoiceMalformed,
    VoiceNotConfigured,
    VoiceRateLimited,
    VoiceRejected,
    VoiceTimeout,
    get_voice_client,
    resolve_language,
)
from app.core.config import settings
from app.core.security import create_access_token
from app.main import app

AUDIO = base64.b64encode(b"\x1aE\xdf\xa3" + b"x" * 400).decode()
SECRET_TEXT = "SECRET-PATIENT-TEXT-123"


class FakeVoice:
    def __init__(self, fail=None):
        self.fail, self.calls = fail, []

    def availability(self):
        return {"transcribe": True, "speak": True, "translate": True}

    async def transcribe(self, audio_base64, mime, locale):
        self.calls.append(("stt", mime, locale))
        if self.fail:
            raise self.fail
        return "எனக்கு காய்ச்சல்"

    async def synthesize(self, text, locale):
        self.calls.append(("tts", text, locale))
        if self.fail:
            raise self.fail
        return base64.b64encode(b"mp3bytes").decode()

    async def translate(self, text, target):
        self.calls.append(("tr", text, target))
        if self.fail:
            raise self.fail
        return "வணக்கம்", "en"


def use(v):
    app.dependency_overrides[get_voice_client] = lambda: v
    return v


@pytest.fixture(autouse=True)
def _clean():
    safety.rate_limiter.reset()
    yield
    safety.rate_limiter.reset()
    app.dependency_overrides.pop(get_voice_client, None)


@pytest_asyncio.fixture
async def H(seeded_data):
    u = seeded_data["doctor_user"]
    return {"Authorization": f"Bearer {create_access_token(u.id, extra_claims={'email': u.email})}"}


def stt_body(**kw):
    return {"audio_base64": AUDIO, "mime": "audio/webm;codecs=opus", "language": "ta", **kw}


# ----------------------------------------------------------------------------- endpoints
@pytest.mark.asyncio
async def test_all_endpoints_require_auth(async_client):
    use(FakeVoice())
    for path, body in (("transcribe", stt_body()), ("speak", {"text": "hi", "language": "en"}),
                       ("translate", {"text": "hi", "target_language": "ta"})):
        assert (await async_client.post(f"/api/v1/ai/voice/{path}", json=body)).status_code == 401
    assert (await async_client.get("/api/v1/ai/voice/capabilities")).status_code == 401


@pytest.mark.asyncio
async def test_happy_paths_and_language_locale_mapping(async_client, H):
    fake = use(FakeVoice())
    r = await async_client.post("/api/v1/ai/voice/transcribe", json=stt_body(language="ta-IN"), headers=H)
    assert r.status_code == 200, r.text
    assert r.json()["data"] == {"text": "எனக்கு காய்ச்சல்", "language": "ta", "locale": "ta-IN"}
    assert fake.calls[0] == ("stt", "audio/webm;codecs=opus", "ta-IN")
    r = await async_client.post("/api/v1/ai/voice/speak", json={"text": "Hello", "language": "HI"}, headers=H)
    d = r.json()["data"]
    assert r.status_code == 200 and d["locale"] == "hi-IN" and d["mime"] == "audio/mpeg"
    assert base64.b64decode(d["audio_base64"]) == b"mp3bytes"
    r = await async_client.post("/api/v1/ai/voice/translate", json={"text": "hello", "target_language": "ta"}, headers=H)
    assert r.json()["data"] == {"text": "வணக்கம்", "target_language": "ta", "detected_source_language": "en"}
    caps = (await async_client.get("/api/v1/ai/voice/capabilities", headers=H)).json()["data"]
    assert caps["languages"] == SUPPORTED_LANGUAGES and caps["speak"] is True


@pytest.mark.asyncio
async def test_language_validation(async_client, H):
    use(FakeVoice())
    for lang in ("fr", "ta-LK", "", "xx-YY"):
        r = await async_client.post("/api/v1/ai/voice/speak", json={"text": "hi", "language": lang}, headers=H)
        assert r.status_code == 422, lang
    r = await async_client.post("/api/v1/ai/voice/translate", json={"text": "hi", "target_language": "de"}, headers=H)
    assert r.status_code == 422
    assert resolve_language("en_in") == ("en", "en-IN") and resolve_language("Ta") == ("ta", "ta-IN")
    assert resolve_language(None) is None


@pytest.mark.asyncio
async def test_size_and_input_limits(async_client, H, monkeypatch):
    fake = use(FakeVoice())
    monkeypatch.setattr(settings, "AI_VOICE_MAX_AUDIO_BASE64_CHARS", 1000)
    big = "A" * 1001
    assert (await async_client.post("/api/v1/ai/voice/transcribe", json=stt_body(audio_base64=big), headers=H)).status_code == 413
    monkeypatch.undo()
    assert (await async_client.post("/api/v1/ai/voice/transcribe", json=stt_body(mime="audio/mp4"), headers=H)).status_code == 415
    assert (await async_client.post("/api/v1/ai/voice/transcribe", json=stt_body(audio_base64="!!!notb64"), headers=H)).status_code == 422
    tiny = base64.b64encode(b"abc").decode()
    assert (await async_client.post("/api/v1/ai/voice/transcribe", json=stt_body(audio_base64=tiny), headers=H)).status_code == 422
    long_text = "x" * (settings.AI_VOICE_MAX_TEXT_CHARS + 1)
    assert (await async_client.post("/api/v1/ai/voice/speak", json={"text": long_text, "language": "en"}, headers=H)).status_code == 413
    assert (await async_client.post("/api/v1/ai/voice/speak", json={"text": "   ", "language": "en"}, headers=H)).status_code == 422
    assert (await async_client.post("/api/v1/ai/voice/translate", json={"text": long_text, "target_language": "ta"}, headers=H)).status_code == 413
    assert fake.calls == []  # nothing reached the provider


@pytest.mark.asyncio
async def test_rate_limit(async_client, H, monkeypatch):
    monkeypatch.setattr(settings, "AI_VOICE_RATE_LIMIT_PER_MINUTE", 2)
    use(FakeVoice())
    body = {"text": "hi", "language": "en"}
    assert (await async_client.post("/api/v1/ai/voice/speak", json=body, headers=H)).status_code == 200
    assert (await async_client.post("/api/v1/ai/voice/speak", json=body, headers=H)).status_code == 200
    assert (await async_client.post("/api/v1/ai/voice/speak", json=body, headers=H)).status_code == 429


@pytest.mark.asyncio
@pytest.mark.parametrize("exc,status,code", [
    (VoiceNotConfigured("x"), 503, "AI_NOT_CONFIGURED"),
    (VoiceTimeout("x"), 504, "AI_TIMEOUT"),
    (VoiceRateLimited("x"), 429, "AI_PROVIDER_RATE_LIMITED"),
    (VoiceRejected("x"), 422, "AI_INPUT_REJECTED"),
    (VoiceMalformed("x"), 502, "AI_MALFORMED_RESPONSE"),
    (VoiceError("x"), 502, "AI_UNAVAILABLE"),
])
async def test_provider_errors_map_to_http(async_client, H, exc, status, code):
    use(FakeVoice(fail=exc))
    r = await async_client.post("/api/v1/ai/voice/speak", json={"text": "hi", "language": "en"}, headers=H)
    assert r.status_code == status, r.text
    assert code in r.text


@pytest.mark.asyncio
async def test_not_configured_end_to_end_is_503_and_never_fakes(async_client, H, monkeypatch):
    monkeypatch.setattr(settings, "GOOGLE_CLOUD_API_KEY", "")
    app.dependency_overrides.pop(get_voice_client, None)
    for path, body in (("transcribe", stt_body()), ("speak", {"text": "hi", "language": "en"}),
                       ("translate", {"text": "hi", "target_language": "ta"})):
        r = await async_client.post(f"/api/v1/ai/voice/{path}", json=body, headers=H)
        assert r.status_code == 503 and "AI_NOT_CONFIGURED" in r.text, path
        assert "audio_base64" not in r.text and "transcript" not in r.text
    caps = (await async_client.get("/api/v1/ai/voice/capabilities", headers=H)).json()["data"]
    assert (caps["transcribe"], caps["speak"], caps["translate"]) == (False, False, False)


@pytest.mark.asyncio
async def test_content_is_never_logged(async_client, H, caplog):
    use(FakeVoice(fail=VoiceError(SECRET_TEXT)))
    with caplog.at_level("DEBUG"):
        await async_client.post("/api/v1/ai/voice/speak", json={"text": SECRET_TEXT, "language": "en"}, headers=H)
    assert SECRET_TEXT not in caplog.text


# ----------------------------------------------------------------------------- provider client
def _client(handler, key="k-secret", **kw):
    return GoogleVoiceClient(api_key=key, project="", timeout=5, transport=httpx.MockTransport(handler),
                             stt_base="https://stt.test/v1", tts_base="https://tts.test/v1",
                             translate_base="https://tr.test/v2", **kw)


@pytest.mark.asyncio
async def test_stt_request_shape_key_in_header_only():
    seen = {}

    def handler(req):
        seen.update(url=str(req.url), key=req.headers.get("x-goog-api-key"), body=req.content.decode())
        return httpx.Response(200, json={"results": [{"alternatives": [{"transcript": "hello there"}]},
                                                     {"alternatives": [{"transcript": "friend"}]}]})

    text = await _client(handler).transcribe(AUDIO, "audio/webm;codecs=opus", "hi-IN")
    assert text == "hello there friend"
    assert seen["url"] == "https://stt.test/v1/speech:recognize"
    assert seen["key"] == "k-secret" and "k-secret" not in seen["url"] and "key=" not in seen["url"]
    assert '"WEBM_OPUS"' in seen["body"] and '"hi-IN"' in seen["body"]
    # empty recognition is a genuine empty result, not an error
    assert await _client(lambda r: httpx.Response(200, json={})).transcribe(AUDIO, "audio/webm", "en-IN") == ""


@pytest.mark.asyncio
async def test_tts_and_translate_request_shape():
    seen = []

    def handler(req):
        seen.append((str(req.url), req.headers.get("x-goog-api-key"), req.content.decode()))
        if "synthesize" in str(req.url):
            return httpx.Response(200, json={"audioContent": "QUJD"})
        return httpx.Response(200, json={"data": {"translations": [{"translatedText": "नमस्ते", "detectedSourceLanguage": "en"}]}})

    c = _client(handler)
    assert await c.synthesize("Hello", "ta-IN") == "QUJD"
    assert await c.translate("Hello", "hi") == ("नमस्ते", "en")
    assert seen[0][0] == "https://tts.test/v1/text:synthesize" and '"ta-IN"' in seen[0][2] and '"MP3"' in seen[0][2]
    assert seen[1][0] == "https://tr.test/v2" and '"target":"hi"' in seen[1][2].replace(" ", "")
    assert all(k == "k-secret" and "k-secret" not in u for u, k, _ in seen)


@pytest.mark.asyncio
async def test_client_failure_modes():
    with pytest.raises(VoiceNotConfigured):
        await _client(lambda r: httpx.Response(200), key="").synthesize("a", "en-IN")
    with pytest.raises(VoiceNotConfigured):  # feature toggle off
        await _client(lambda r: httpx.Response(200), tts_enabled=False).synthesize("a", "en-IN")
    with pytest.raises(VoiceRejected):  # unsupported mime never sent
        await _client(lambda r: httpx.Response(200)).transcribe(AUDIO, "audio/mp4", "en-IN")
    with pytest.raises(VoiceRateLimited):
        await _client(lambda r: httpx.Response(429)).synthesize("a", "en-IN")
    with pytest.raises(VoiceRejected):
        await _client(lambda r: httpx.Response(400, json={"error": SECRET_TEXT})).synthesize("a", "en-IN")
    with pytest.raises(VoiceError) as ei:
        await _client(lambda r: httpx.Response(403)).synthesize("a", "en-IN")
    assert ei.value.code == "AI_UNAVAILABLE"
    with pytest.raises(VoiceMalformed):
        await _client(lambda r: httpx.Response(200, json={})).synthesize("a", "en-IN")
    with pytest.raises(VoiceMalformed):
        await _client(lambda r: httpx.Response(200, json={"data": {"translations": []}})).translate("a", "ta")

    def slow(req):
        raise httpx.ReadTimeout("t", request=req)

    with pytest.raises(VoiceTimeout):
        await _client(slow).synthesize("a", "en-IN")
    n = {"i": 0}

    def flaky(req):
        n["i"] += 1
        return httpx.Response(503) if n["i"] == 1 else httpx.Response(200, json={"audioContent": "QQ=="})

    assert await _client(flaky).synthesize("a", "en-IN") == "QQ=="  # one retry for transient errors
