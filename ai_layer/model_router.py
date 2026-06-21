"""Model routing — selects the optimal model by task complexity and handles fallback.

Routes requests to the most cost-effective model:
- **Haiku** (fast/cheap): classification, intent routing, simple lookups
- **Sonnet** (balanced): generation, narratives, operational briefs
- **Opus** (powerful): complex reasoning, multi-step analysis, evaluation

Automatically falls back to the next-cheaper model on rate limit or error.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from enum import Enum
from typing import Any

logger = logging.getLogger(__name__)


class TaskComplexity(str, Enum):
    LOW = "low"       # classification, extraction, simple Q&A
    MEDIUM = "medium"  # generation, summarization, narratives
    HIGH = "high"      # multi-step reasoning, evaluation, analysis


@dataclass(frozen=True)
class ModelSpec:
    """Specification for an LLM model."""

    name: str
    model_id: str
    complexity: TaskComplexity
    max_tokens: int
    cost_input_per_m: float   # $/M input tokens
    cost_output_per_m: float  # $/M output tokens
    priority: int             # lower = preferred for its complexity tier


# Model catalog — add new models here
_MODEL_CATALOG: list[ModelSpec] = [
    ModelSpec(
        name="haiku",
        model_id="claude-haiku-4-20250514",
        complexity=TaskComplexity.LOW,
        max_tokens=4096,
        cost_input_per_m=0.25,
        cost_output_per_m=1.25,
        priority=1,
    ),
    ModelSpec(
        name="sonnet",
        model_id="claude-sonnet-4-20250514",
        complexity=TaskComplexity.MEDIUM,
        max_tokens=8192,
        cost_input_per_m=3.0,
        cost_output_per_m=15.0,
        priority=1,
    ),
    ModelSpec(
        name="opus",
        model_id="claude-opus-4-20250514",
        complexity=TaskComplexity.HIGH,
        max_tokens=4096,
        cost_input_per_m=15.0,
        cost_output_per_m=75.0,
        priority=1,
    ),
]

# Fallback order: Opus → Sonnet → Haiku
_FALLBACK_ORDER = ["opus", "sonnet", "haiku"]


class ModelRouter:
    """Routes requests to the optimal model based on task complexity."""

    def __init__(self, models: list[ModelSpec] | None = None) -> None:
        self._models = {m.name: m for m in (models or _MODEL_CATALOG)}
        self._failed: set[str] = set()  # Models currently in cooldown

    def select(
        self,
        complexity: TaskComplexity | None = None,
        task_hint: str | None = None,
    ) -> ModelSpec:
        """Select the best model for the given task.

        Args:
            complexity: Explicit complexity level.
            task_hint: Natural language hint (used to infer complexity if not provided).
        """
        if complexity is None:
            complexity = self._infer_complexity(task_hint or "")

        # Find matching models not in cooldown, sorted by priority
        candidates = [
            m for m in self._models.values()
            if m.complexity == complexity and m.name not in self._failed
        ]

        if candidates:
            return min(candidates, key=lambda m: m.priority)

        # Fallback: try cheaper models
        for name in _FALLBACK_ORDER:
            if name not in self._failed and name in self._models:
                model = self._models[name]
                logger.warning(
                    "No %s model available, falling back to %s",
                    complexity.value, model.name,
                )
                return model

        # Last resort: return sonnet (the default)
        logger.error("All models failed, forcing sonnet")
        self._failed.clear()  # Reset cooldowns
        return self._models.get("sonnet", _MODEL_CATALOG[1])

    def mark_failed(self, model_name: str) -> None:
        """Mark a model as temporarily unavailable (e.g., rate limited)."""
        self._failed.add(model_name)
        logger.warning("Model %s marked as failed, will fallback", model_name)

    def mark_recovered(self, model_name: str) -> None:
        """Remove a model from the failed set."""
        self._failed.discard(model_name)

    def reset(self) -> None:
        """Clear all failure states."""
        self._failed.clear()

    @staticmethod
    def _infer_complexity(task_hint: str) -> TaskComplexity:
        """Infer task complexity from a natural language description."""
        hint = task_hint.lower()

        # High complexity indicators
        high_keywords = [
            "analyze", "diagnose", "investigate", "evaluate", "compare",
            "root cause", "strategy", "multi-step", "reasoning", "why",
        ]
        if any(kw in hint for kw in high_keywords):
            return TaskComplexity.HIGH

        # Low complexity indicators
        low_keywords = [
            "classify", "extract", "intent", "route", "label", "categorize",
            "yes or no", "true or false", "which", "list",
        ]
        if any(kw in hint for kw in low_keywords):
            return TaskComplexity.LOW

        return TaskComplexity.MEDIUM

    def get_all_models(self) -> list[dict[str, Any]]:
        """Return all registered models with their status."""
        return [
            {
                "name": m.name,
                "model_id": m.model_id,
                "complexity": m.complexity.value,
                "cost_input_per_m": m.cost_input_per_m,
                "cost_output_per_m": m.cost_output_per_m,
                "available": m.name not in self._failed,
            }
            for m in self._models.values()
        ]


# Singleton
_router: ModelRouter | None = None


def get_model_router() -> ModelRouter:
    global _router
    if _router is None:
        _router = ModelRouter()
    return _router
