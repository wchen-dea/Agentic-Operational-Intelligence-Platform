from fastapi import APIRouter, Depends
from services.api.models import KPIRequest
from services.api.auth import require_auth, APIKeyRecord
from ai_layer.agents.tools.fetch_kpi_tool import fetch_store_kpis

router = APIRouter(tags=["kpi"])


@router.post("/kpi")
def kpi(req: KPIRequest, auth: APIKeyRecord = Depends(require_auth)):
    return fetch_store_kpis(store_id=req.store_id, region=req.region)


@router.post("/kpi/enriched")
def kpi_enriched(req: KPIRequest, auth: APIKeyRecord = Depends(require_auth)):
    """Return KPIs enriched with semantic metadata (unit, direction, thresholds, anomaly flags)."""
    snapshot = fetch_store_kpis(store_id=req.store_id, region=req.region, enrich=True)
    return {
        "store_id": snapshot.store_id,
        "region": snapshot.region,
        "records": [r.to_dict() for r in snapshot.records],
        "anomalies": [r.to_dict() for r in snapshot.anomalous_records],
        "provenance": snapshot.provenance.to_dict(),
    }


@router.get("/kpi/catalog")
def kpi_catalog(auth: APIKeyRecord = Depends(require_auth)):
    """Return the machine-readable KPI catalog."""
    from data_platform.semantic_layer import _load_kpi_catalog

    catalog = _load_kpi_catalog()
    return {"kpis": list(catalog.values())}
