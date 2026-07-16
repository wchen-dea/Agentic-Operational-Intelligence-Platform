"""Skill abstractions and in-memory registry for tool-calling flows."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class SkillParameter:
    """Schema for one input parameter accepted by a skill."""

    name: str
    type: str
    description: str
    required: bool = True
    default: Any = None


@dataclass(frozen=True)
class SkillDescriptor:
    """Metadata and input schema for a skill."""

    name: str
    description: str
    parameters: list[SkillParameter] = field(default_factory=list)
    tags: list[str] = field(default_factory=list)


class Skill(ABC):
    """Base class for executable skills."""

    @property
    @abstractmethod
    def descriptor(self) -> SkillDescriptor:
        raise NotImplementedError

    @abstractmethod
    def execute(self, **kwargs: Any) -> Any:
        raise NotImplementedError


class SkillRegistry:
    """In-memory registry used by the tool-calling agent loop."""

    def __init__(self) -> None:
        self._skills: dict[str, Skill] = {}

    def register(self, skill: Skill) -> None:
        self._skills[skill.descriptor.name] = skill

    def invoke(self, name: str, **kwargs: Any) -> Any:
        skill = self._skills.get(name)
        if skill is None:
            raise KeyError(f"Unknown skill: {name}")
        return skill.execute(**kwargs)

    def to_tool_schemas(self, tags: list[str] | None = None) -> list[dict[str, Any]]:
        """Return OpenAI/Anthropic-compatible tool schemas."""
        tag_filter = set(tags or [])
        out: list[dict[str, Any]] = []
        for skill in self._skills.values():
            desc = skill.descriptor
            if tag_filter and not (set(desc.tags) & tag_filter):
                continue

            properties: dict[str, Any] = {}
            required: list[str] = []
            for p in desc.parameters:
                schema: dict[str, Any] = {"type": p.type, "description": p.description}
                if p.default is not None:
                    schema["default"] = p.default
                properties[p.name] = schema
                if p.required:
                    required.append(p.name)

            out.append(
                {
                    "name": desc.name,
                    "description": desc.description,
                    "input_schema": {
                        "type": "object",
                        "properties": properties,
                        "required": required,
                    },
                }
            )
        return out
