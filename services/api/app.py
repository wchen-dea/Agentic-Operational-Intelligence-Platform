import logging
import os

from fastapi import Depends, FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, PlainTextResponse

from services.api.routes.query import router as query_router
from services.api.routes.kpi import router as kpi_router
from services.api.routes.alerts import router as alerts_router
from services.api.routes.operations import router as operations_router
from services.api.routes.skills import router as skills_router
from services.api.routes.streaming import router as streaming_router
from services.api.auth import init_auth_from_env, require_auth, APIKeyRecord
from observability.logging_config import configure_logging, CorrelationIdMiddleware
from config.settings import settings

# Configure structured logging before anything else
configure_logging(
    level=settings.logging.level,
    json_format=settings.logging.json_format,
)
logger = logging.getLogger(__name__)

app = FastAPI(title=settings.app_name)

# Correlation ID injection (must be first middleware so all log records carry the ID)
app.add_middleware(CorrelationIdMiddleware)

# CORS - restrict origins in production via AOIP_CORS_ORIGINS env var
_cors_origins = os.environ.get("AOIP_CORS_ORIGINS", "*").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=_cors_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["X-API-Key", "Content-Type", "Authorization", "X-Correlation-ID"],
)

app.include_router(query_router)
app.include_router(kpi_router)
app.include_router(alerts_router)
app.include_router(operations_router)
app.include_router(skills_router)
app.include_router(streaming_router)


@app.on_event("startup")
async def startup() -> None:
    """Load API keys from environment variables on process start."""
    init_auth_from_env()
    logger.info("Auth initialised")
    # Configure and apply OpenTelemetry tracing
    if settings.otel.enabled:
        from observability.tracing import configure_tracing, instrument_fastapi

        configure_tracing(
            endpoint=settings.otel.endpoint,
            service_name=settings.otel.service_name,
            sample_rate=settings.otel.traces_sample_rate,
        )
        instrument_fastapi(app)
        logger.info("OpenTelemetry tracing enabled")


@app.get("/health")
def health():
    """Public health-check - no auth required."""
    return {"status": "ok", "app": settings.app_name}


@app.get("/usage", tags=["observability"])
def usage(auth: APIKeyRecord = Depends(require_auth)):
    """Return LLM token usage and estimated cost for the current process."""
    from ai_layer.llm import get_session_cost_summary

    return get_session_cost_summary()


@app.get("/metrics", tags=["observability"])
def prometheus_metrics(auth: APIKeyRecord = Depends(require_auth)):
    """Export metrics in Prometheus exposition format.

    Returns prometheus_client output when the package is installed;
    falls back to a manually rendered text format otherwise.
    """
    from observability.evaluation import get_metrics_collector

    collector = get_metrics_collector()
    body, content_type = collector.generate_latest_text()
    return PlainTextResponse(body, media_type=content_type)


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):
    logger.exception("Unhandled error: %s %s", request.method, request.url.path)
    return JSONResponse(status_code=500, content={"detail": "Internal server error"})
