"""Module for operations."""

from fastapi import APIRouter, Depends

from ai_systems.gateway.api.auth import APIKeyRecord, require_auth
from ai_systems.gateway.api.models import OperationalBriefRequest
from ai_systems.orchestration.orchestrator import Orchestrator, get_orchestrator

router = APIRouter(tags=["operations"])


@router.post("/operations/brief")
def operations_brief(
    req: OperationalBriefRequest,
    orchestrator: Orchestrator = Depends(get_orchestrator),  # noqa: B008
    auth: APIKeyRecord = Depends(require_auth),  # noqa: B008
):
    return orchestrator.get_operational_brief(
        store_id=req.store_id,
        region=req.region,
        persona=req.persona,
    )
