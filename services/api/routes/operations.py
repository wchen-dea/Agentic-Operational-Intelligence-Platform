from fastapi import APIRouter
from services.api.models import OperationalBriefRequest
from ai_layer.agents.orchestrator import AgenticOperationalIntelligenceOrchestrator

router = APIRouter()
orchestrator = AgenticOperationalIntelligenceOrchestrator()


@router.post("/operations/brief")
def operations_brief(req: OperationalBriefRequest):
    return orchestrator.get_operational_brief(
        store_id=req.store_id,
        region=req.region,
        persona=req.persona,
    )
