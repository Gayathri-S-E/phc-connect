"""Shared safety checks. These run in code, before and after the model, so they do not depend on the prompt."""
import re
import time
import uuid
from collections import defaultdict, deque
from typing import Any, Deque, Dict, Optional

from app.core.config import settings
from app.core.exceptions import AppException

# --------------------------------------------------------------------------- input validation
_CONTROL = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]")


def clean_user_message(text: Optional[str]) -> str:
    """Strip control characters, trim, and enforce the length limit."""
    cleaned = _CONTROL.sub("", text or "").strip()
    if not cleaned:
        raise AppException("Invalid Message", "Please type a message.", 422, "AI_EMPTY_MESSAGE")
    if len(cleaned) > settings.AI_MAX_MESSAGE_CHARS:
        raise AppException(
            "Message Too Long",
            f"Please keep messages under {settings.AI_MAX_MESSAGE_CHARS} characters.",
            422, "AI_MESSAGE_TOO_LONG",
        )
    return cleaned


# --------------------------------------------------------------------------- emergencies
# Deliberately broad on the patient side: a false alarm costs one screen, a miss can cost a life.
EMERGENCY_PATTERNS = [
    r"chest (pain|tightness|pressure)", r"heart attack", r"(can'?t|cannot|unable to) breathe",
    r"(difficulty|trouble|struggling) (in )?breathing", r"short(ness)? of breath", r"stroke",
    r"face (is )?droop", r"slurred speech", r"paraly(sis|zed)", r"unconscious", r"not responding",
    r"passed out", r"fainted", r"seizure", r"convulsion", r"heavy bleeding",
    r"bleeding (a lot|heavily|won'?t stop)", r"severe burn", r"poison", r"overdose", r"snake ?bite",
    r"suicid", r"kill myself", r"end my life", r"want to die", r"self[- ]harm", r"choking",
    r"severe allergic", r"anaphyla", r"coughing (up )?blood", r"vomiting blood",
    "நெஞ்சு வலி", "நெஞ்சுவலி", "சுவாசிக்க முடியவில்லை", "மூச்சு விட முடியவில்லை", "மயக்கம்", "மயங்கி",
    "அதிக ரத்தப்போக்கு", "வலிப்பு", "தற்கொலை", "பாம்பு கடி", "விஷம்",
    "सीने में दर्द", "सांस नहीं", "बेहोश", "दौरा", "आत्महत्या",
]
_EMERGENCY_RE = re.compile("|".join(EMERGENCY_PATTERNS), re.IGNORECASE)
_NEGATION_RE = re.compile(r"\b(no|not|without|never|don'?t have|do not have|denies?)\b.{0,20}$", re.IGNORECASE)


def detect_emergency(text: str) -> bool:
    for hit in _EMERGENCY_RE.finditer(text):
        # "no chest pain" is not an emergency report; only suppress when the hit is negated.
        if not _NEGATION_RE.search(text[max(0, hit.start() - 25):hit.start()]):
            return True
    return False


EMERGENCY_REPLY = {
    "en": ("**This may be a medical emergency. Please get help right now.**\n\n"
           "- Call **108** (ambulance) or go to the nearest hospital emergency department immediately.\n"
           "- If someone is with you, ask them to stay with you and help you get there.\n"
           "- If you are thinking about harming yourself, call **108** or the Tele-MANAS helpline **14416** now.\n\n"
           "I have not contacted anyone for you. Please do not wait for an appointment or a reply here."),
    "ta": ("**இது மருத்துவ அவசரநிலையாக இருக்கலாம். உடனே உதவி பெறுங்கள்.**\n\n"
           "- உடனடியாக **108** ஆம்புலன்ஸை அழைக்கவும் அல்லது அருகிலுள்ள மருத்துவமனை அவசர சிகிச்சைப் பிரிவுக்குச் செல்லவும்.\n"
           "- அருகில் யாரேனும் இருந்தால், உங்களுடன் இருந்து உதவும்படி கேளுங்கள்.\n"
           "- உங்களைத் துன்புறுத்திக்கொள்ளும் எண்ணம் இருந்தால், உடனே **108** அல்லது Tele-MANAS **14416** ஐ அழைக்கவும்.\n\n"
           "நான் உங்களுக்காக யாரையும் தொடர்புகொள்ளவில்லை. சந்திப்பு முன்பதிவுக்காகவோ இங்கு பதிலுக்காகவோ காத்திருக்க வேண்டாம்."),
    "hi": ("**यह चिकित्सा आपातकाल हो सकता है। कृपया अभी मदद लें।**\n\n"
           "- तुरंत **108** एम्बुलेंस को कॉल करें या नज़दीकी अस्पताल के आपातकालीन विभाग में जाएँ।\n"
           "- यदि कोई पास है, तो उससे साथ रहने और पहुँचने में मदद करने को कहें।\n"
           "- यदि आप खुद को नुकसान पहुँचाने के बारे में सोच रहे हैं, तो अभी **108** या Tele-MANAS **14416** पर कॉल करें।\n\n"
           "मैंने आपके लिए किसी से संपर्क नहीं किया है। कृपया अपॉइंटमेंट या यहाँ जवाब का इंतज़ार न करें।"),
}

# --------------------------------------------------------------------------- prompt injection
INJECTION_PATTERNS = [
    r"ignore (all |any )?(the )?(previous|prior|above|earlier) (instructions|rules|prompts?)",
    r"disregard (all |any )?(the )?(previous|prior|above|system) (instructions|rules|prompts?)",
    r"(reveal|show|print|repeat|output|tell me) (me )?(your|the) (system|hidden|initial|original) (prompt|instructions?|rules)",
    r"what (are|is) your (system|hidden) (prompt|instructions)",
    r"you are now (in )?(developer|dev|admin|root|dan|jailbreak)",
    r"(developer|admin|debug|god) mode",
    r"act as (an? )?(admin|administrator|super ?admin|pharmacist|doctor|dho|another role)",
    r"i am (an? |the )?(admin|administrator|super ?admin|system|developer)\b",
    r"(override|bypass|disable) (the )?(safety|security|permission|role|restriction)s?",
    r"pretend (that )?(you have|to have) (access|permission)",
    r"</?(system|assistant|tool)>",
]
_INJECTION_RE = re.compile("|".join(INJECTION_PATTERNS), re.IGNORECASE)

INJECTION_REPLY = {
    "en": ("I can't change my role, reveal my internal instructions, or bypass access rules, and typing a request "
           "doesn't give me extra permissions. I'm happy to help with what your account is allowed to do. What would you like?"),
    "ta": ("என் பங்கை மாற்றவோ, உள் வழிமுறைகளை வெளியிடவோ, அணுகல் விதிகளைத் தவிர்க்கவோ என்னால் முடியாது. "
           "உங்கள் கணக்கிற்கு அனுமதிக்கப்பட்டவற்றில் உதவ மகிழ்ச்சி. என்ன வேண்டும்?"),
    "hi": ("मैं अपनी भूमिका नहीं बदल सकता, आंतरिक निर्देश नहीं बता सकता या पहुँच नियम नहीं तोड़ सकता। "
           "आपके खाते की अनुमति के भीतर मदद करने में खुशी होगी। आप क्या चाहते हैं?"),
}


def detect_injection(text: str) -> bool:
    return bool(_INJECTION_RE.search(text))


# --------------------------------------------------------------------------- tool-result hygiene
_MAX_STR = 600
_MAX_ITEMS = 25


def sanitize_tool_data(value: Any, depth: int = 0) -> Any:
    """Bound size and strip control characters. Free text in records is untrusted data, never instructions."""
    if depth > 6:
        return None
    if isinstance(value, str):
        v = _CONTROL.sub("", value)
        return v if len(v) <= _MAX_STR else v[:_MAX_STR] + "...[truncated]"
    if isinstance(value, dict):
        return {str(k): sanitize_tool_data(v, depth + 1) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [sanitize_tool_data(v, depth + 1) for v in list(value)[:_MAX_ITEMS]]
    if isinstance(value, uuid.UUID):
        return str(value)
    if hasattr(value, "isoformat"):
        return value.isoformat()
    if hasattr(value, "value") and not isinstance(value, (int, float, bool)):
        return value.value
    return value


# --------------------------------------------------------------------------- output guard
_ACTION_VERBS = r"(?:booked|cancell?ed|rescheduled|saved|finali[sz]ed|submitted|created|ordered|referred|updated|sent)"
_SUCCESS_CLAIM = re.compile(
    r"\bi(?:'ve| have| just| already)?\s+(?:now\s+)?" + _ACTION_VERBS + r"\b"
    r"|\bsuccessfully\s+" + _ACTION_VERBS + r"\b"
    r"|\b(?:is|are) now (?:booked|confirmed|cancell?ed)\b",
    re.IGNORECASE,
)

NO_FAKE_SUCCESS_NOTE = {
    "en": "Nothing has been changed yet. Please use the Confirm button below the request to proceed, or Cancel to stop.",
    "ta": "இன்னும் எதுவும் மாற்றப்படவில்லை. தொடர கீழே உள்ள உறுதிப்படுத்து பொத்தானைப் பயன்படுத்தவும், அல்லது நிறுத்த ரத்து செய்யவும்.",
    "hi": "अभी कुछ भी नहीं बदला गया है। आगे बढ़ने के लिए नीचे पुष्टि बटन का उपयोग करें, या रोकने के लिए रद्द करें।",
}
NO_ACTION_NOTE = {
    "en": "I haven't completed any action in Med2Us in this reply. I can only make a change after you confirm a request I prepare for you.",
    "ta": "இந்த பதிலில் Med2Us இல் நான் எந்த நடவடிக்கையும் முடிக்கவில்லை. நான் தயாரிக்கும் கோரிக்கையை நீங்கள் உறுதிப்படுத்திய பின்பே மாற்றம் செய்ய முடியும்.",
    "hi": "इस उत्तर में मैंने Med2Us में कोई कार्रवाई पूरी नहीं की है। मैं तभी बदलाव कर सकता हूँ जब आप मेरी तैयार की गई अनुरोध की पुष्टि करें।",
}


def guard_success_claims(reply: str, language: str, executed_this_turn: bool, pending_this_turn: bool) -> str:
    """The model can never execute anything, so it must never sound as if it did."""
    if executed_this_turn or not _SUCCESS_CLAIM.search(reply):
        return reply
    note = (NO_FAKE_SUCCESS_NOTE if pending_this_turn else NO_ACTION_NOTE).get(language, NO_ACTION_NOTE["en"])
    return f"{reply}\n\n{note}"


# --------------------------------------------------------------------------- rate limiting
class SlidingWindowLimiter:
    """Per-process limiter. With several workers each enforces its own window; see the implementation report."""

    def __init__(self) -> None:
        self._hits: Dict[str, Deque[float]] = defaultdict(deque)

    def check(self, key: str, limit: Optional[int] = None, window: float = 60.0) -> None:
        limit = limit or settings.AI_RATE_LIMIT_PER_MINUTE
        now = time.monotonic()
        q = self._hits[key]
        while q and now - q[0] > window:
            q.popleft()
        if len(q) >= limit:
            retry = max(1, int(window - (now - q[0])))
            raise AppException(
                "Too Many Requests",
                f"You're sending messages very quickly. Please wait about {retry} seconds and try again.",
                429, "AI_RATE_LIMITED", extra={"retry_after_seconds": retry},
            )
        q.append(now)

    def reset(self) -> None:
        self._hits.clear()


rate_limiter = SlidingWindowLimiter()
