import logging

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from services.api.routes.query import router as query_router
from services.api.routes.kpi import router as kpi_router
from services.api.routes.alerts import router as alerts_router
from services.api.routes.operations import router as operations_router
from services.api.routes.skills import router as skills_router
from config.settings import settings

logger = logging.getLogger(__name__)

app = FastAPI(title=settings.app_name)

app.include_router(query_router)
app.include_router(kpi_router)
app.include_router(alerts_router)
app.include_router(operations_router)
app.include_router(skills_router)


@app.get("/health")
def health():
    return {"status": "ok", "app": settings.app_name}


@app.get("/usage", tags=["observability"])
def usage():
    """Return LLM token usage and estimated cost for the current process."""
    from ai_layer.llm import get_session_cost_summary
    return get_session_cost_summary()


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):
    logger.exception("Unhandled error on %s %s", request.method, request.url.path)
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error", "path": request.url.path},
    )
