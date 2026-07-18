"""Module for query."""

from fastapi import APIRouter, Depends, HTTPException

from ai_systems.core.guardrails import validate_input
from ai_systems.gateway.api.auth import APIKeyRecord, require_auth
from ai_systems.gateway.api.models import AskRequest
from ai_systems.orchestration.orchestrator import Orchestrator, get_orchestrator

router = APIRouter(tags=["query"])


@router.post("/ask")
def ask(
    req: AskRequest,
    orchestrator: Orchestrator = Depends(get_orchestrator),  # noqa: B008
    auth: APIKeyRecord = Depends(require_auth),  # noqa: B008
):
    # Input guardrail
    guard = validate_input(req.question)
    if not guard.passed:
        raise HTTPException(
            status_code=400,
            detail={
                "error": "Input blocked by guardrails",
                "checks": guard.checks,
            },
        )

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
