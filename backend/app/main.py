import time
import uuid
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware

from app.api.v1.health import router as health_router
from app.api.v1.router import api_router
from app.core.config import settings
from app.core.exceptions import register_exception_handlers
from app.core.logging import get_logger, setup_logging

setup_logging(log_level="DEBUG" if settings.DEBUG else "INFO")
logger = get_logger("app.main")


class RequestCorrelationMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        trace_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))
        request.state.trace_id = trace_id
        start_time = time.time()

        response = await call_next(request)

        duration = time.time() - start_time
        response.headers["X-Request-ID"] = trace_id
        response.headers["X-Response-Time"] = f"{duration:.4f}s"

        logger.info(
            f"[{request.method}] {request.url.path} - Status: {response.status_code} ({duration * 1000:.2f}ms) Trace: {trace_id}"
        )
        return response


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Initializing Smart Health & Supply Chain Resilience Backend...")
    yield
    logger.info("Shutting down backend gracefully.")


def create_application() -> FastAPI:
    app = FastAPI(
        title=settings.APP_NAME,
        version="1.0.0",
        description="Production-grade backend for Smart Health, Primary Health Centers, and Pharmaceutical Supply Chain Resilience.",
        lifespan=lifespan,
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json",
    )

    # Middleware
    app.add_middleware(RequestCorrelationMiddleware)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.ALLOWED_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Exception Handlers (RFC 7807)
    register_exception_handlers(app)

    # Routers
    app.include_router(health_router)
    app.include_router(api_router)

    return app


app = create_application()
