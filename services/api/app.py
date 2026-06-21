import logging

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse, PlainTextResponse

from services.api.routes.query import router as query_router
from services.api.routes.kpi import router as kpi_router
from services.api.routes.alerts import router as alerts_router
from services.api.routes.operations import router as operations_router
from services.api.routes.skills import router as skills_router
from services.api.routes.streaming import router as streaming_router
from config.settings import settings

logger = logging.getLogger(__name__)

app = FastAPI(title=settings.app_name)

app.include_router(query_router)
app.include_router(kpi_router)
app.include_router(alerts_router)
app.include_router(operations_router)
app.include_router(skills_router)
app.include_router(streaming_router)


@app.get("/health")
def health():
    return {"status": "ok", "app": settings.app_name}


@app.get("/usage", tags=["observability"])
def usage():
    """Return LLM token usage and estimated cost for the current process."""
    from ai_layer.llm import get_session_cost_summary
    return get_session_cost_summary()


@app.get("/metrics", tags=["observability"])
def prometheus_metrics():
    """Export metrics in Prometheus exposition format."""
    from observability.evaluation import get_metrics_collector

    collector = get_metrics_collector()
    snap = collector.snapshot()
    lines: list[str] = []

    # Counters
    for key, value in snap.get("counters", {}).items():
        name, labels = _parse_metric_key(key)
        prom_name = _sanitize_name(name)
        lines.append(f"# TYPE {prom_name} counter")
        lines.append(f"{prom_name}{labels} {value}")

    # Gauges
    for key, value in snap.get("gauges", {}).items():
        name, labels = _parse_metric_key(key)
        prom_name = _sanitize_name(name)
        lines.append(f"# TYPE {prom_name} gauge")
        lines.append(f"{prom_name}{labels} {value}")

    # Histograms (exported as summary-style)
    for key, stats in snap.get("histograms", {}).items():
        name, labels = _parse_metric_key(key)
        prom_name = _sanitize_name(name)
        lines.append(f"# TYPE {prom_name} summary")
        lines.append(f"{prom_name}_count{labels} {stats.get('count', 0)}")
        lines.append(f"{prom_name}_sum{labels} {stats.get('sum', 0.0)}")

    lines.append("")  # trailing newline
    return PlainTextResponse("\n".join(lines), media_type="text/plain; version=0.0.4")


def _parse_metric_key(key: str) -> tuple[str, str]:
    """Parse 'name{k=v,k2=v2}' into ('name', '{k=v,k2=v2}')."""
    if "{" in key:
        idx = key.index("{")
        return key[:idx], key[idx:]
    return key, ""


def _sanitize_name(name: str) -> str:
    """Sanitize metric name for Prometheus (alphanumeric + underscore)."""
    return "".join(c if c.isalnum() or c == "_" else "_" for c in name)


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):
    logger.exception("Unhandled error on %s %s", request.method, request.url.path)
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error", "path": request.url.path},
    )
