from fastapi import FastAPI
from services.api.routes.query import router as query_router
from services.api.routes.kpi import router as kpi_router
from services.api.routes.alerts import router as alerts_router
from services.api.routes.operations import router as operations_router
from config.settings import settings

app = FastAPI(title=settings.app_name)

app.include_router(query_router)
app.include_router(kpi_router)
app.include_router(alerts_router)
app.include_router(operations_router)


@app.get("/health")
def health():
    return {"status": "ok", "app": settings.app_name}
