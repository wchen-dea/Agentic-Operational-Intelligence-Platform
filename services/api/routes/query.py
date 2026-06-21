from fastapi import APIRouter, Depends, HTTPException
from services.api.models import AskRequest
from ai_layer.agents.orchestrator import Orchestrator, get_orchestrator
from ai_layer.guardrails import validate_input

router = APIRouter(tags=["query"])


@router.post("/ask")
def ask(req: AskRequest, orchestrator: Orchestrator = Depends(get_orchestrator)):
    # Input guardrail
    guard = validate_input(req.question)
    if not guard.passed:
        raise HTTPException(status_code=400, detail={
            "error": "Input blocked by guardrails",
            "checks": guard.checks,
        })

    result = orchestrator.answer(
        guard.sanitized_text or req.question,
        store_id=req.store_id,
        region=req.region,
        persona=req.persona,
        session_id=req.session_id,
    )

    # Include guardrail metadata if warnings were raised
    if guard.checks:
        result["guardrails"] = {"input_checks": guard.checks}

    return result
