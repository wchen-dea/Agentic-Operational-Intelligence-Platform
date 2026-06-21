from fastapi import APIRouter, Depends
from services.api.models import AskRequest
from ai_layer.agents.orchestrator import Orchestrator, get_orchestrator

router = APIRouter(tags=["query"])


@router.post("/ask")
def ask(req: AskRequest, orchestrator: Orchestrator = Depends(get_orchestrator)):
    return orchestrator.answer(
        req.question,
        store_id=req.store_id,
        region=req.region,
        persona=req.persona,
    )
