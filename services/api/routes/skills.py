from __future__ import annotations

from typing import Any

from fastapi import APIRouter
from pydantic import BaseModel, Field

from ai_layer.skills.registry import get_skill_registry

router = APIRouter(tags=["skills"])


class InvokeSkillRequest(BaseModel):
    params: dict[str, Any] = Field(default_factory=dict)


@router.get("/skills")
def list_skills() -> dict[str, Any]:
    """List all available agent skills with their tool schemas."""
    reg = get_skill_registry()
    return {"skills": reg.to_tool_schemas()}


@router.post("/skills/{skill_name}/invoke")
def invoke_skill(skill_name: str, req: InvokeSkillRequest) -> dict[str, Any]:
    """Invoke a skill by name with the given parameters."""
    reg = get_skill_registry()
    result = reg.invoke(skill_name, **req.params)
    return {"skill": skill_name, "result": result}
