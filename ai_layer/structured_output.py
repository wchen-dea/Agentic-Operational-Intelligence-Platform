"""Structured LLM output - Pydantic-validated responses from the LLM.

Provides typed response models and a ``generate_structured`` function that
constrains the LLM to output JSON conforming to a Pydantic schema.  Uses
Anthropic's tool_use mechanism to enforce structure.
"""

from __future__ import annotations

import json
import logging
from typing import Any, TypeVar

from pydantic import BaseModel, ValidationError

from ai_layer.llm import generate, LLMUsage, _session_usage, _get_client, _extract_usage, settings
import time

logger = logging.getLogger(__name__)

T = TypeVar("T", bound=BaseModel)


# ---------------------------------------------------------------------------
# Response models - typed alternatives to free-form text
# ---------------------------------------------------------------------------


class KPIInsight(BaseModel):
    """A single insight about a KPI metric."""

    metric: str
    value: float
    status: str  # "healthy", "warning", "critical"
    explanation: str
    recommended_action: str


class OperationalBriefResponse(BaseModel):
    """Structured operational brief returned by the LLM."""

    summary: str
    key_findings: list[KPIInsight]
    priority_actions: list[str]
    risk_level: str  # "low", "medium", "high"
    confidence: float  # 0.0 to 1.0


class AnomalyDiagnosisResponse(BaseModel):
    """Structured anomaly diagnosis."""

    anomaly_summary: str
    root_causes: list[str]
    affected_kpis: list[str]
    severity: str  # "low", "medium", "high", "critical"
    recommended_actions: list[str]


class PromotionRecommendation(BaseModel):
    """Structured promotion recommendation."""

    recommendation: str
    rationale: str
    expected_impact: str
    target_kpis: list[str]
    time_horizon: str


# ---------------------------------------------------------------------------
# Structured generation via tool_use
# ---------------------------------------------------------------------------


def _pydantic_to_tool_schema(model: type[BaseModel], name: str, description: str) -> dict[str, Any]:
    """Convert a Pydantic model to an Anthropic tool definition."""
    schema = model.model_json_schema()
    # Remove $defs and adjust refs for Anthropic compatibility
    properties = schema.get("properties", {})
    required = schema.get("required", [])
    return {
        "name": name,
        "description": description,
        "input_schema": {
            "type": "object",
            "properties": properties,
            "required": required,
        },
    }


def generate_structured(
    prompt: str,
    response_model: type[T],
    system: str | None = None,
    max_tokens: int | None = None,
    tool_name: str = "structured_response",
    tool_description: str = "Provide your response in structured JSON format.",
) -> T:
    """Generate a structured response validated against a Pydantic model.

    Uses Anthropic's tool_use to force the LLM to produce JSON that conforms
    to the ``response_model`` schema.

    Args:
        prompt: User prompt.
        response_model: Pydantic model class to validate against.
        system: Optional system prompt.
        max_tokens: Override default max_tokens.
        tool_name: Name for the tool definition sent to Claude.
        tool_description: Description for the tool definition.

    Returns:
        A validated instance of ``response_model``.

    Raises:
        ValueError: If the LLM output cannot be parsed or validated.
    """
    effective_max_tokens = max_tokens or settings.llm.max_tokens
    tool = _pydantic_to_tool_schema(response_model, tool_name, tool_description)

    client = _get_client()
    kwargs: dict[str, Any] = {
        "model": settings.llm.model,
        "max_tokens": effective_max_tokens,
        "temperature": settings.llm.temperature,
        "tools": [tool],
        "tool_choice": {"type": "tool", "name": tool_name},
        "messages": [{"role": "user", "content": prompt}],
    }
    if system:
        kwargs["system"] = system

    start = time.perf_counter()
    try:
        response = client.messages.create(**kwargs)
        duration = (time.perf_counter() - start) * 1000
        inp, out = _extract_usage(response)

        usage = LLMUsage(
            input_tokens=inp,
            output_tokens=out,
            cache_hit=False,
            duration_ms=duration,
        )
        _session_usage.append(usage)

        # Extract tool_use block
        for block in response.content:
            if block.type == "tool_use" and block.name == tool_name:
                raw = block.input
                try:
                    return response_model.model_validate(raw)
                except ValidationError as ve:
                    logger.warning("Structured output validation failed: %s", ve)
                    raise ValueError(f"LLM output failed validation: {ve}") from ve

        raise ValueError("LLM did not produce a tool_use response block.")
    except (ValueError, RuntimeError):
        raise
    except Exception as exc:
        logger.error("Structured generation failed: %s", exc)
        raise ValueError(f"Structured generation error: {exc}") from exc


def parse_llm_json(text: str, response_model: type[T]) -> T:
    """Parse and validate JSON from an LLM text response (fallback for non-tool-use).

    Attempts to extract JSON from the text (handles markdown code fences)
    and validates it against the Pydantic model.
    """
    # Try to extract JSON from markdown code blocks
    import re

    json_match = re.search(r"```(?:json)?\s*\n(.*?)\n```", text, re.DOTALL)
    if json_match:
        json_str = json_match.group(1)
    else:
        # Try to find raw JSON object
        brace_start = text.find("{")
        brace_end = text.rfind("}")
        if brace_start >= 0 and brace_end > brace_start:
            json_str = text[brace_start : brace_end + 1]
        else:
            raise ValueError("No JSON found in LLM output.")

    try:
        data = json.loads(json_str)
        return response_model.model_validate(data)
    except (json.JSONDecodeError, ValidationError) as exc:
        raise ValueError(f"Failed to parse structured output: {exc}") from exc
