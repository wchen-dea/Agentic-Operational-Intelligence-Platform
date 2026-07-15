"""Agentic tool-calling loop - lets the LLM autonomously invoke skills.

Wraps ``generate_with_tools`` with the skill registry so that Claude can
select and invoke any registered skill during a conversation turn.
"""

from __future__ import annotations

import logging
from typing import Any

from ai_system.core.core.llm import generate_with_tools
from ai_system.tools.registry import get_skill_registry

logger = logging.getLogger(__name__)


def _skill_executor(name: str, inputs: dict[str, Any]) -> Any:
    """Execute a skill by name via the registry."""
    registry = get_skill_registry()
    return registry.invoke(name, **inputs)


def agentic_query(
    question: str,
    system: str | None = None,
    max_tokens: int | None = None,
    max_tool_rounds: int = 5,
    tool_tags: list[str] | None = None,
) -> dict[str, Any]:
    """Run an agentic query where the LLM can invoke skills autonomously.

    The LLM receives all registered skill schemas (optionally filtered by
    ``tool_tags``) and can call them in a multi-turn loop until it produces
    a final text answer.

    Returns:
        Dict with ``answer``, ``tool_calls``, and ``usage``.
    """
    registry = get_skill_registry()
    tool_schemas = registry.to_tool_schemas(tags=tool_tags)

    if not tool_schemas:
        logger.warning("No tools available for agentic query; falling back to plain generation.")
        from ai_system.core.core.llm import generate as core.llm_generate

        return {
            "answer": llm_generate(question, system=system, max_tokens=max_tokens),
            "tool_calls": [],
            "usage": None,
        }

    result = generate_with_tools(
        prompt=question,
        tools=tool_schemas,
        tool_executor=_skill_executor,
        system=system,
        max_tokens=max_tokens,
        max_tool_rounds=max_tool_rounds,
    )

    return {
        "answer": result["text"],
        "tool_calls": result["tool_calls"],
        "usage": result["usage"],
    }
