"""Observability and evaluation framework for the AI layer.

Provides:
- Structured metrics collection (latency, token usage, agent success rates)
- LLM output quality evaluation hooks
- Agent performance tracking
- Alert precision/recall measurement
"""

from __future__ import annotations

import time
from collections import defaultdict
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable


@dataclass
class MetricPoint:
    name: str
    value: float
    labels: dict[str, str] = field(default_factory=dict)
    timestamp: float = field(default_factory=time.time)


class MetricsCollector:
    """In-process metrics collector.

    In production, this would emit to Prometheus/Datadog/CloudWatch.
    Provides the same interface for local dev and testing.
    """

    def __init__(self) -> None:
        self._counters: dict[str, float] = defaultdict(float)
        self._gauges: dict[str, float] = {}
        self._histograms: dict[str, list[float]] = defaultdict(list)
        self._points: list[MetricPoint] = []

    def increment(self, name: str, value: float = 1.0, labels: dict[str, str] | None = None) -> None:
        key = self._key(name, labels)
        self._counters[key] += value
        self._points.append(MetricPoint(name=name, value=value, labels=labels or {}))

    def gauge(self, name: str, value: float, labels: dict[str, str] | None = None) -> None:
        key = self._key(name, labels)
        self._gauges[key] = value
        self._points.append(MetricPoint(name=name, value=value, labels=labels or {}))

    def observe(self, name: str, value: float, labels: dict[str, str] | None = None) -> None:
        key = self._key(name, labels)
        self._histograms[key].append(value)
        self._points.append(MetricPoint(name=name, value=value, labels=labels or {}))

    def get_counter(self, name: str, labels: dict[str, str] | None = None) -> float:
        return self._counters.get(self._key(name, labels), 0.0)

    def get_gauge(self, name: str, labels: dict[str, str] | None = None) -> float | None:
        return self._gauges.get(self._key(name, labels))

    def get_histogram(self, name: str, labels: dict[str, str] | None = None) -> list[float]:
        return self._histograms.get(self._key(name, labels), [])

    def snapshot(self) -> dict[str, Any]:
        return {
            "counters": dict(self._counters),
            "gauges": dict(self._gauges),
            "histograms": {k: _histogram_stats(v) for k, v in self._histograms.items()},
        }

    @staticmethod
    def _key(name: str, labels: dict[str, str] | None) -> str:
        if not labels:
            return name
        label_str = ",".join(f"{k}={v}" for k, v in sorted(labels.items()))
        return f"{name}{{{label_str}}}"


def _histogram_stats(values: list[float]) -> dict[str, float]:
    if not values:
        return {"count": 0, "sum": 0.0, "min": 0.0, "max": 0.0, "avg": 0.0}
    return {
        "count": len(values),
        "sum": sum(values),
        "min": min(values),
        "max": max(values),
        "avg": sum(values) / len(values),
    }


# ---------------------------------------------------------------------------
# LLM Evaluation
# ---------------------------------------------------------------------------


@dataclass
class EvalResult:
    """Result of an LLM output quality evaluation."""

    score: float  # 0.0 - 1.0
    passed: bool
    criteria: str
    details: str = ""


class EvalCriteria(str, Enum):
    GROUNDEDNESS = "groundedness"
    ACTIONABILITY = "actionability"
    RELEVANCE = "relevance"
    CONCISENESS = "conciseness"
    PERSONA_FIT = "persona_fit"


class LLMEvaluator:
    """Evaluates LLM outputs against quality criteria.

    Supports both rule-based heuristics and (future) LLM-as-judge evaluation.
    """

    def __init__(self) -> None:
        self._evaluators: dict[EvalCriteria, Callable[[str, dict[str, Any]], EvalResult]] = {
            EvalCriteria.GROUNDEDNESS: self._eval_groundedness,
            EvalCriteria.ACTIONABILITY: self._eval_actionability,
            EvalCriteria.CONCISENESS: self._eval_conciseness,
        }

    def evaluate(
        self, output: str, context: dict[str, Any], criteria: list[EvalCriteria] | None = None
    ) -> list[EvalResult]:
        criteria = criteria or list(self._evaluators.keys())
        results = []
        for c in criteria:
            evaluator = self._evaluators.get(c)
            if evaluator:
                results.append(evaluator(output, context))
        return results

    def _eval_groundedness(self, output: str, context: dict[str, Any]) -> EvalResult:
        """Check that output references KPIs/metrics present in context."""
        kpis = context.get("kpis", {})
        mentioned = sum(1 for k in kpis if k in output)
        total = max(len(kpis), 1)
        score = min(mentioned / total, 1.0)
        return EvalResult(
            score=score,
            passed=score >= 0.3,
            criteria=EvalCriteria.GROUNDEDNESS,
            details=f"Referenced {mentioned}/{total} KPI names in output.",
        )

    def _eval_actionability(self, output: str, context: dict[str, Any]) -> EvalResult:
        """Check for action-oriented language."""
        action_markers = [
            "recommend", "action", "prioritize", "implement", "deploy",
            "review", "monitor", "escalate", "adjust", "launch", "reduce",
            "increase", "run", "execute", "shift", "push",
        ]
        found = sum(1 for m in action_markers if m in output.lower())
        score = min(found / 3.0, 1.0)
        return EvalResult(
            score=score,
            passed=score >= 0.5,
            criteria=EvalCriteria.ACTIONABILITY,
            details=f"Found {found} action markers.",
        )

    def _eval_conciseness(self, output: str, context: dict[str, Any]) -> EvalResult:
        """Penalize overly verbose outputs."""
        word_count = len(output.split())
        if word_count <= 300:
            score = 1.0
        elif word_count <= 600:
            score = 0.7
        else:
            score = max(0.3, 1.0 - (word_count - 300) / 1000)
        return EvalResult(
            score=score,
            passed=score >= 0.5,
            criteria=EvalCriteria.CONCISENESS,
            details=f"Output is {word_count} words.",
        )


# ---------------------------------------------------------------------------
# Agent Performance Tracker
# ---------------------------------------------------------------------------


class AgentPerformanceTracker:
    """Tracks per-agent execution metrics for dashboards and alerts."""

    def __init__(self, metrics: MetricsCollector) -> None:
        self._metrics = metrics

    def record_execution(
        self,
        agent_name: str,
        duration_ms: float,
        success: bool,
        used_fallback: bool = False,
        attempts: int = 1,
    ) -> None:
        labels = {"agent": agent_name}
        self._metrics.observe("agent_duration_ms", duration_ms, labels)
        self._metrics.increment("agent_executions_total", labels=labels)
        if success:
            self._metrics.increment("agent_successes_total", labels=labels)
        else:
            self._metrics.increment("agent_failures_total", labels=labels)
        if used_fallback:
            self._metrics.increment("agent_fallbacks_total", labels=labels)
        if attempts > 1:
            self._metrics.increment("agent_retries_total", value=attempts - 1, labels=labels)

    def record_llm_call(
        self,
        model: str,
        input_tokens: int,
        output_tokens: int,
        duration_ms: float,
    ) -> None:
        labels = {"model": model}
        self._metrics.observe("llm_call_duration_ms", duration_ms, labels)
        self._metrics.increment("llm_input_tokens_total", value=input_tokens, labels=labels)
        self._metrics.increment("llm_output_tokens_total", value=output_tokens, labels=labels)
        self._metrics.increment("llm_calls_total", labels=labels)

    def record_eval(self, criteria: str, score: float, passed: bool) -> None:
        labels = {"criteria": criteria}
        self._metrics.observe("eval_score", score, labels)
        if passed:
            self._metrics.increment("eval_passed_total", labels=labels)
        else:
            self._metrics.increment("eval_failed_total", labels=labels)


# ---------------------------------------------------------------------------
# Singleton instances
# ---------------------------------------------------------------------------

metrics = MetricsCollector()
evaluator = LLMEvaluator()
tracker = AgentPerformanceTracker(metrics)
