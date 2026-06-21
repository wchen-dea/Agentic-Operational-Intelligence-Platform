from fastapi import APIRouter, Depends
from services.api.models import OperationalBriefRequest
from ai_layer.agents.orchestrator import Orchestrator, get_orchestrator

router = APIRouter(tags=["operations"])


@router.post("/operations/brief")
def operations_brief(req: OperationalBriefRequest, orchestrator: Orchestrator = Depends(get_orchestrator)):
    return orchestrator.get_operational_brief(
        store_id=req.store_id,
        region=req.region,
        persona=req.persona,
    )
