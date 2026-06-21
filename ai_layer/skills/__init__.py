"""Agent skill framework — composable, self-describing capabilities for agents.

A Skill is a discrete, reusable capability that an agent can invoke. Each skill
declares its name, description, input schema, and execution logic. This enables:
- Dynamic skill discovery and invocation
- LLM function-calling integration (skills → tool definitions)
- Per-skill observability and evaluation
- Cross-agent skill reuse
"""

from __future__ import annotations

import logging
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any

from observability.evaluation import tracker

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class SkillParameter:
    """Describes a single input parameter for a skill."""

    name: str
    type: str  # "string", "number", "boolean", "object", "array"
    description: str
    required: bool = True
    default: Any = None


@dataclass(frozen=True)
class SkillDescriptor:
    """Self-describing metadata for a skill (usable as LLM tool definition)."""

    name: str
    description: str
    parameters: list[SkillParameter] = field(default_factory=list)
    tags: list[str] = field(default_factory=list)

    def to_tool_schema(self) -> dict[str, Any]:
        """Convert to OpenAI/Anthropic function-calling tool schema."""
        properties = {}
        required = []
        for p in self.parameters:
            properties[p.name] = {"type": p.type, "description": p.description}
            if p.default is not None:
                properties[p.name]["default"] = p.default
            if p.required:
                required.append(p.name)

        return {
            "name": self.name,
            "description": self.description,
            "input_schema": {
                "type": "object",
                "properties": properties,
                "required": required,
            },
        }


class Skill(ABC):
    """Base class for agent skills."""

    @property
    @abstractmethod
    def descriptor(self) -> SkillDescriptor:
        """Return the skill's self-describing metadata."""
        ...

    @abstractmethod
    def execute(self, **kwargs: Any) -> Any:
        """Execute the skill with the given parameters."""
        ...

    def invoke(self, **kwargs: Any) -> Any:
        """Execute with observability instrumentation."""
        start = time.perf_counter()
        try:
            result = self.execute(**kwargs)
            duration = (time.perf_counter() - start) * 1000
            tracker.record_execution(
                f"skill:{self.descriptor.name}", duration, success=True
            )
            return result
        except Exception as e:
            duration = (time.perf_counter() - start) * 1000
            tracker.record_execution(
                f"skill:{self.descriptor.name}", duration, success=False
            )
            raise


class SkillRegistry:
    """Registry for discovering and invoking skills by name or tag."""

    def __init__(self) -> None:
        self._skills: dict[str, Skill] = {}

    def register(self, skill: Skill) -> None:
        name = skill.descriptor.name
        if name in self._skills:
            logger.warning("Overwriting skill: %s", name)
        self._skills[name] = skill

    def get(self, name: str) -> Skill:
        if name not in self._skills:
            available = ", ".join(sorted(self._skills.keys()))
            raise KeyError(f"Skill '{name}' not found. Available: {available}")
        return self._skills[name]

    def find_by_tag(self, tag: str) -> list[Skill]:
        return [s for s in self._skills.values() if tag in s.descriptor.tags]

    def list_all(self) -> list[SkillDescriptor]:
        return [s.descriptor for s in self._skills.values()]

    def to_tool_schemas(self, tags: list[str] | None = None) -> list[dict[str, Any]]:
        """Export all (or filtered) skills as LLM tool-calling schemas."""
        skills = self._skills.values()
        if tags:
            skills = [s for s in skills if any(t in s.descriptor.tags for t in tags)]
        return [s.descriptor.to_tool_schema() for s in skills]

    def invoke(self, name: str, **kwargs: Any) -> Any:
        """Look up and invoke a skill by name."""
        return self.get(name).invoke(**kwargs)
