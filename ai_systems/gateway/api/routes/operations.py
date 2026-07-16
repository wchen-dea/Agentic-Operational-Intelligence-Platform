from fastapi import APIRouter, Depends
from ai_systems.gateway.api.models import OperationalBriefRequest
from ai_systems.gateway.api.auth import require_auth, APIKeyRecord
from ai_systems.orchestration.orchestrator import Orchestrator, get_orchestrator

router = APIRouter(tags=["operations"])


@router.post("/operations/brief")
def operations_brief(
    req: OperationalBriefRequest,
    orchestrator: Orchestrator = Depends(get_orchestrator),
    auth: APIKeyRecord = Depends(require_auth),
):
    return orchestrator.get_operational_brief(
        store_id=req.store_id,
        region=req.region,
        persona=req.persona,
    )
