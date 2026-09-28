from typing import Any, Dict, Optional
from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError


class AppException(Exception):
    """Base application exception mapping to RFC 7807 problem details."""
    def __init__(
        self,
        title: str,
        detail: str,
        status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR,
        error_code: str = "INTERNAL_SERVER_ERROR",
        extra: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(detail)
        self.title = title
        self.detail = detail
        self.status_code = status_code
        self.error_code = error_code
        self.extra = extra or {}


class AuthenticationException(AppException):
    def __init__(self, detail: str = "Could not validate authentication credentials."):
        super().__init__(
            title="Authentication Failed",
            detail=detail,
            status_code=status.HTTP_401_UNAUTHORIZED,
            error_code="AUTHENTICATION_FAILED",
        )


class PermissionDeniedException(AppException):
    def __init__(self, detail: str = "You do not have permission to perform this action."):
        super().__init__(
            title="Permission Denied",
            detail=detail,
            status_code=status.HTTP_403_FORBIDDEN,
            error_code="PERMISSION_DENIED",
        )


class ResourceNotFoundException(AppException):
    def __init__(self, resource: str, resource_id: str | None = None):
        detail = f"{resource} was not found."
        if resource_id:
            detail = f"{resource} with identifier '{resource_id}' was not found."
        super().__init__(
            title="Resource Not Found",
            detail=detail,
            status_code=status.HTTP_404_NOT_FOUND,
            error_code="RESOURCE_NOT_FOUND",
        )


class ConflictException(AppException):
    def __init__(self, detail: str):
        super().__init__(
            title="Resource Conflict",
            detail=detail,
            status_code=status.HTTP_409_CONFLICT,
            error_code="RESOURCE_CONFLICT",
        )


class BadRequestException(AppException):
    def __init__(self, detail: str):
        super().__init__(
            title="Bad Request",
            detail=detail,
            status_code=status.HTTP_400_BAD_REQUEST,
            error_code="BAD_REQUEST",
        )


def register_exception_handlers(app: FastAPI) -> None:
    """Register RFC 7807 problem details exception handlers on the FastAPI app."""

    @app.exception_handler(AppException)
    async def app_exception_handler(request: Request, exc: AppException) -> JSONResponse:
        trace_id = getattr(request.state, "trace_id", "unknown")
        content = {
            "type": f"https://api.smarthealth.gov/errors/{exc.error_code.lower()}",
            "title": exc.title,
            "status": exc.status_code,
            "detail": exc.detail,
            "code": exc.error_code,
            "instance": str(request.url.path),
            "trace_id": trace_id,
        }
        if exc.extra:
            content.update(exc.extra)
        return JSONResponse(status_code=exc.status_code, content=content)

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
        trace_id = getattr(request.state, "trace_id", "unknown")
        errors = []
        for error in exc.errors():
            errors.append({
                "field": ".".join(str(loc) for loc in error.get("loc", [])),
                "message": error.get("msg", ""),
                "type": error.get("type", ""),
            })
        content = {
            "type": "https://api.smarthealth.gov/errors/validation-error",
            "title": "Validation Error",
            "status": status.HTTP_422_UNPROCESSABLE_ENTITY,
            "detail": "Request payload validation failed.",
            "code": "VALIDATION_ERROR",
            "instance": str(request.url.path),
            "invalid_params": errors,
            "trace_id": trace_id,
        }
        return JSONResponse(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, content=content)

    @app.exception_handler(Exception)
    async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
        trace_id = getattr(request.state, "trace_id", "unknown")
        # In production, do not leak raw exception details
        content = {
            "type": "https://api.smarthealth.gov/errors/internal-server-error",
            "title": "Internal Server Error",
            "status": status.HTTP_500_INTERNAL_SERVER_ERROR,
            "detail": "An unexpected error occurred. Please contact system support with the trace_id.",
            "code": "INTERNAL_SERVER_ERROR",
            "instance": str(request.url.path),
            "trace_id": trace_id,
        }
        return JSONResponse(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, content=content)
