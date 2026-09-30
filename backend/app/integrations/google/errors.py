"""Errors shared by the Google integrations. `code` is safe to show to users; `detail` is for server logs only."""
from app.core.exceptions import AppException


class GoogleError(Exception):
    code = "GOOGLE_UNAVAILABLE"
    status_code = 502

    def __init__(self, detail: str = "", http_status: int = 0):
        super().__init__(detail)
        self.detail = detail
        self.http_status = http_status


class NotConfigured(GoogleError):
    code = "AI_NOT_CONFIGURED"
    status_code = 503


class GoogleTimeout(GoogleError):
    code = "GOOGLE_TIMEOUT"
    status_code = 504


class GoogleRateLimited(GoogleError):
    code = "GOOGLE_RATE_LIMITED"
    status_code = 429


class GoogleRejected(GoogleError):
    code = "GOOGLE_REQUEST_REJECTED"
    status_code = 502


def to_app_exception(exc: GoogleError, service: str) -> AppException:
    if isinstance(exc, NotConfigured):
        return AppException("Not Configured", f"{service} is not configured on this server.", 503, exc.code)
    return AppException("Google Service Error", f"{service} request failed.", exc.status_code, exc.code)
