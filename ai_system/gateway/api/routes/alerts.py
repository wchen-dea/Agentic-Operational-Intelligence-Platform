from fastapi import APIRouter, Depends
from ai_system.gateway.api.auth import require_auth, APIKeyRecord
from ai_system.config.settings import settings
from ai_system.tools.fetch_kpi_tool import fetch_store_kpis
from ai_system.tools.alert_tool import detect_kpi_alerts_for_store

router = APIRouter(tags=["alerts"])


@router.get("/alerts/{store_id}")
def alerts(store_id: str, auth: APIKeyRecord = Depends(require_auth)):
    kpis = fetch_store_kpis(store_id=store_id)
    return {"store_id": store_id, "alerts": detect_kpi_alerts_for_store(kpis, settings.alert_rules_path)}
