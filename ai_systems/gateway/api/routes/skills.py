from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field

from ai_systems.gateway.api.auth import require_auth, APIKeyRecord
from ai_systems.tools.registry import get_skill_registry

router = APIRouter(tags=["skills"])


class InvokeSkillRequest(BaseModel):
    params: dict[str, Any] = Field(default_factory=dict)


@router.get("/skills")
def list_skills(auth: APIKeyRecord = Depends(require_auth)) -> dict[str, Any]:
    """List all available agent skills with their tool schemas."""
    reg = get_skill_registry()
    return {"skills": reg.to_tool_schemas()}


@router.post("/skills/{skill_name}/invoke")
def invoke_skill(
    skill_name: str,
    req: InvokeSkillRequest,
    auth: APIKeyRecord = Depends(require_auth),
) -> dict[str, Any]:
    """Invoke a skill by name with the given parameters."""
    reg = get_skill_registry()
    result = reg.invoke(skill_name, **req.params)
    return {"skill": skill_name, "result": result}
