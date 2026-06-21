from fastapi import APIRouter
from services.api.models import AskRequest
from ai_layer.agents.orchestrator import AgenticOperationalIntelligenceOrchestrator

router = APIRouter()
orchestrator = AgenticOperationalIntelligenceOrchestrator()


@router.post("/ask")
def ask(req: AskRequest):
    return orchestrator.answer(
        req.question,
        store_id=req.store_id,
        region=req.region,
        persona=req.persona,
    )
