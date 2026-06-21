from fastapi import APIRouter
from services.api.models import KPIRequest
from ai_layer.agents.tools.fetch_kpi_tool import fetch_store_kpis

router = APIRouter(tags=["kpi"])


@router.post("/kpi")
def kpi(req: KPIRequest):
    return fetch_store_kpis(store_id=req.store_id, region=req.region)
