"""Observability and evaluation framework for the AI layer.

Provides:
- Structured metrics collection (latency, token usage, agent success rates)
- LLM output quality evaluation hooks
- Agent performance tracking
- Alert precision/recall measurement
- Prometheus-compatible /metrics export via prometheus_client
"""

from __future__ import annotations

import logging
import os
import time
from collections import defaultdict
from collections.abc import Callable
from contextlib import suppress
from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# prometheus_client integration (optional - falls back gracefully if absent)
# ---------------------------------------------------------------------------

_prom: Any = None
_PROM_REGISTRY: Any = None
_PROM_METRICS: dict[str, Any] = {}

try:
    import prometheus_client as _prom_module  # type: ignore[import]

    _prom = _prom_module

    _PROM_REGISTRY = _prom.CollectorRegistry(auto_describe=True)

    # --- Counters ---
    for _name, _desc, _labels in [
        ("agent_executions_total", "Total agent node executions", ["agent"]),
        ("agent_successes_total", "Total successful agent executions", ["agent"]),
        ("agent_failures_total", "Total failed agent executions", ["agent"]),
        ("agent_fallbacks_total", "Total agent fallback invocations", ["agent"]),
        ("agent_retries_total", "Total agent retry attempts", ["agent"]),
        ("llm_calls_total", "Total LLM API calls", ["model"]),
        ("llm_input_tokens_total", "Cumulative LLM input tokens", ["model"]),
        ("llm_output_tokens_total", "Cumulative LLM output tokens", ["model"]),
        ("eval_passed_total", "Total evaluations that passed", ["criteria"]),
        ("eval_failed_total", "Total evaluations that failed", ["criteria"]),
    ]:
        _PROM_METRICS[_name] = _prom.Counter(_name, _desc, _labels, registry=_PROM_REGISTRY)

    # --- Histograms ---
    for _name, _desc, _labels, _buckets in [
        (
            "agent_duration_ms",
            "Agent execution duration in milliseconds",
            ["agent"],
            [10, 50, 100, 250, 500, 1000, 2500, 5000, 10000, 30000],
        ),
        (
            "llm_call_duration_ms",
            "LLM API call duration in milliseconds",
            ["model"],
            [100, 250, 500, 1000, 2500, 5000, 10000, 30000, 60000],
        ),
        (
            "eval_score",
            "LLM output quality evaluation score (0-1)",
            ["criteria"],
            [0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0],
        ),
    ]:
        _PROM_METRICS[_name] = _prom.Histogram(_name, _desc, _labels, buckets=_buckets, registry=_PROM_REGISTRY)

    logger.debug("prometheus_client loaded - metrics will be exported via /metrics")

except ImportError:
    logger.info(
        "prometheus_client not installed - /metrics will use fallback text format. "
        "Install with: uv add prometheus-client"
    )


def _prom_labels(metric_name: str, labels: dict[str, str] | None) -> Any | None:
    """Return the prometheus metric object with labels applied, or None."""
    if _prom is None or not labels:
        return None
    m = _PROM_METRICS.get(metric_name)
    if m is None:
        return None
    try:
        return m.labels(**labels)
    except Exception:
        return None


@dataclass
class MetricPoint:
    name: str
    value: float
    labels: dict[str, str] = field(default_factory=dict)
    timestamp: float = field(default_factory=time.time)


class MetricsCollector:
    """Dual-write metrics collector.

    Every ``increment``, ``gauge``, and ``observe`` call:
    1. Updates the in-process dicts (backward-compatible ``snapshot()`` + tests).
    2. When ``prometheus_client`` is installed, also updates the Prometheus
       registry so ``/metrics`` exports real Prometheus exposition text.
    """

    def __init__(self) -> None:
        self._counters: dict[str, float] = defaultdict(float)
        self._gauges: dict[str, float] = {}
        self._histograms: dict[str, list[float]] = defaultdict(list)
        self._points: list[MetricPoint] = []

    # ------------------------------------------------------------------
    # Write methods
    # ------------------------------------------------------------------

    def increment(self, name: str, value: float = 1.0, labels: dict[str, str] | None = None) -> None:
        key = self._key(name, labels)
        self._counters[key] += value
        self._points.append(MetricPoint(name=name, value=value, labels=labels or {}))
        # Prometheus side-channel
        pml = _prom_labels(name, labels)
        if pml is not None:
            with suppress(Exception):
                pml.inc(value)

    def gauge(self, name: str, value: float, labels: dict[str, str] | None = None) -> None:
        key = self._key(name, labels)
        self._gauges[key] = value
        self._points.append(MetricPoint(name=name, value=value, labels=labels or {}))
        # Prometheus side-channel (Gauge type)
        pml = _prom_labels(name, labels)
        if pml is not None:
            with suppress(Exception):
                pml.set(value)

    def observe(self, name: str, value: float, labels: dict[str, str] | None = None) -> None:
        key = self._key(name, labels)
        self._histograms[key].append(value)
        self._points.append(MetricPoint(name=name, value=value, labels=labels or {}))
        # Prometheus side-channel (Histogram type)
        pml = _prom_labels(name, labels)
        if pml is not None:
            with suppress(Exception):
                pml.observe(value)

    # ------------------------------------------------------------------
    # Read methods
    # ------------------------------------------------------------------

    def get_counter(self, name: str, labels: dict[str, str] | None = None) -> float:
        return self._counters.get(self._key(name, labels), 0.0)

    def get_gauge(self, name: str, labels: dict[str, str] | None = None) -> float | None:
        return self._gauges.get(self._key(name, labels))

    def get_histogram(self, name: str, labels: dict[str, str] | None = None) -> list[float]:
        return self._histograms.get(self._key(name, labels), [])

    def snapshot(self) -> dict[str, Any]:
        """Return a dict snapshot of all in-process metrics (backward compat)."""
        return {
            "counters": dict(self._counters),
            "gauges": dict(self._gauges),
            "histograms": {k: _histogram_stats(v) for k, v in self._histograms.items()},
        }

    def generate_latest_text(self) -> tuple[str, str]:
        """Return ``(body, content_type)`` suitable for the ``/metrics`` HTTP endpoint.

        Uses ``prometheus_client.generate_latest()`` when available; falls back to
        manually rendered Prometheus exposition text from the in-process snapshot.
        """
        if _prom is not None and _PROM_REGISTRY is not None:
            try:
                body = _prom.generate_latest(_PROM_REGISTRY).decode("utf-8")
                return body, _prom.CONTENT_TYPE_LATEST
            except Exception as exc:
                logger.warning("prometheus_client generate_latest failed: %s", exc)

        # Fallback: render snapshot as Prometheus text format
        return self._format_snapshot_as_prometheus(), "text/plain; version=0.0.4"

    def _format_snapshot_as_prometheus(self) -> str:
        snap = self.snapshot()
        lines: list[str] = []
        for key, value in snap.get("counters", {}).items():
            name, label_str = _split_metric_key(key)
            pname = _sanitize_prom_name(name)
            prom_labels = _to_prom_label_str(label_str)
            lines.append(f"# TYPE {pname} counter")
            lines.append(f"{pname}{prom_labels} {value}")
        for key, value in snap.get("gauges", {}).items():
            name, label_str = _split_metric_key(key)
            pname = _sanitize_prom_name(name)
            prom_labels = _to_prom_label_str(label_str)
            lines.append(f"# TYPE {pname} gauge")
            lines.append(f"{pname}{prom_labels} {value}")
        for key, stats in snap.get("histograms", {}).items():
            name, label_str = _split_metric_key(key)
            pname = _sanitize_prom_name(name)
            prom_labels = _to_prom_label_str(label_str)
            lines.append(f"# TYPE {pname} summary")
            lines.append(f"{pname}_count{prom_labels} {stats.get('count', 0)}")
            lines.append(f"{pname}_sum{prom_labels} {stats.get('sum', 0.0)}")
        lines.append("")
        return "\n".join(lines)

    @staticmethod
    def _key(name: str, labels: dict[str, str] | None) -> str:
        if not labels:
            return name
        label_str = ",".join(f"{k}={v}" for k, v in sorted(labels.items()))
        return f"{name}{{{label_str}}}"


def _split_metric_key(key: str) -> tuple[str, str]:
    if "{" in key:
        idx = key.index("{")
        return key[:idx], key[idx:]
    return key, ""


def _to_prom_label_str(label_str: str) -> str:
    """Convert internal label format `{k=v}` to Prometheus format `{k="v"}`."""
    if not label_str:
        return ""
    inner = label_str.strip()
    if not (inner.startswith("{") and inner.endswith("}")):
        return ""
    inner = inner[1:-1].strip()
    if not inner:
        return ""

    parts: list[str] = []
    for item in inner.split(","):
        if "=" not in item:
            continue
        key, value = item.split("=", 1)
        key = key.strip()
        value = value.strip().replace("\\", "\\\\").replace('"', '\\"').replace("\n", "\\n")
        if key:
            parts.append(f'{key}="{value}"')

    if not parts:
        return ""
    return "{" + ",".join(parts) + "}"


def _sanitize_prom_name(name: str) -> str:
    return name.replace(".", "_").replace("-", "_")


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


class EvalCriteria(StrEnum):
    GROUNDEDNESS = "groundedness"
    ACTIONABILITY = "actionability"
    RELEVANCE = "relevance"
    CONCISENESS = "conciseness"
    PERSONA_FIT = "persona_fit"


class LLMEvaluator:
    """Evaluates LLM outputs against quality criteria.

    Supports both rule-based heuristics and LLM-as-judge evaluation.
    """

    def __init__(self) -> None:
        self._evaluators: dict[EvalCriteria, Callable[[str, dict[str, Any]], EvalResult]] = {
            EvalCriteria.GROUNDEDNESS: self._eval_groundedness,
            EvalCriteria.ACTIONABILITY: self._eval_actionability,
            EvalCriteria.CONCISENESS: self._eval_conciseness,
            EvalCriteria.RELEVANCE: self._eval_relevance,
            EvalCriteria.PERSONA_FIT: self._eval_persona_fit,
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
            "recommend",
            "action",
            "prioritize",
            "implement",
            "deploy",
            "review",
            "monitor",
            "escalate",
            "adjust",
            "launch",
            "reduce",
            "increase",
            "run",
            "execute",
            "shift",
            "push",
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

    def _eval_relevance(self, output: str, context: dict[str, Any]) -> EvalResult:
        """Check that output addresses the user's question/intent."""
        question = context.get("question", "")
        intent = context.get("intent", "")
        if not question:
            return EvalResult(
                score=0.5, passed=True, criteria=EvalCriteria.RELEVANCE, details="No question to evaluate against."
            )

        # Check keyword overlap between question and output
        q_words = set(question.lower().split()) - {
            "the",
            "a",
            "an",
            "is",
            "are",
            "what",
            "why",
            "how",
            "for",
            "and",
            "or",
            "to",
            "in",
            "of",
        }
        out_lower = output.lower()
        matched = sum(1 for w in q_words if w in out_lower)
        coverage = matched / max(len(q_words), 1)

        # Bonus for intent alignment
        intent_keywords = {
            "kpi_query": ["kpi", "metric", "revenue", "rate", "count"],
            "anomaly_check": ["alert", "anomal", "threshold", "breach", "warning"],
            "operational_brief": ["brief", "action", "priority", "recommend"],
            "promotion_analysis": ["promotion", "campaign", "branded", "mix"],
        }
        intent_bonus = 0.0
        for kw in intent_keywords.get(intent, []):
            if kw in out_lower:
                intent_bonus += 0.1
        intent_bonus = min(intent_bonus, 0.3)

        score = min(coverage + intent_bonus, 1.0)
        return EvalResult(
            score=score,
            passed=score >= 0.3,
            criteria=EvalCriteria.RELEVANCE,
            details=f"Question keyword coverage: {coverage:.0%}, intent bonus: {intent_bonus:.0%}.",
        )

    def _eval_persona_fit(self, output: str, context: dict[str, Any]) -> EvalResult:
        """Check that output tone and content match the target persona."""
        persona = context.get("persona", "store_manager")
        out_lower = output.lower()

        if persona == "executive":
            exec_markers = [
                "region",
                "strategic",
                "portfolio",
                "variance",
                "budget",
                "cross-store",
                "intervention",
                "reallocate",
                "roi",
            ]
            found = sum(1 for m in exec_markers if m in out_lower)
            score = min(found / 3.0, 1.0)
            details = f"Executive markers found: {found}/{len(exec_markers)}."
        else:
            ops_markers = [
                "store",
                "daily",
                "huddle",
                "team",
                "advisor",
                "coaching",
                "shift",
                "staffing",
                "checkout",
                "sku",
            ]
            found = sum(1 for m in ops_markers if m in out_lower)
            score = min(found / 3.0, 1.0)
            details = f"Store manager markers found: {found}/{len(ops_markers)}."

        return EvalResult(
            score=score,
            passed=score >= 0.3,
            criteria=EvalCriteria.PERSONA_FIT,
            details=details,
        )

    def evaluate_with_llm(
        self,
        output: str,
        context: dict[str, Any],
        criteria: list[EvalCriteria] | None = None,
    ) -> list[EvalResult]:
        """Evaluate using an LLM as judge (requires API key).

        Falls back to rule-based evaluation if LLM is unavailable.
        """
        from ai_systems.config.settings import settings

        if not os.environ.get(settings.llm.api_key_env_var):
            return self.evaluate(output, context, criteria)

        criteria = criteria or [EvalCriteria.GROUNDEDNESS, EvalCriteria.RELEVANCE, EvalCriteria.PERSONA_FIT]
        results: list[EvalResult] = []

        try:
            from ai_systems.core.llm import generate as llm_generate

            question = context.get("question", "N/A")
            persona = context.get("persona", "store_manager")
            kpi_names = ", ".join(context.get("kpis", {}).keys()) or "N/A"

            prompt = (
                f"Evaluate the following AI assistant response on a scale of 0.0 to 1.0 for each criterion.\n\n"
                f"USER QUESTION: {question}\n"
                f"TARGET PERSONA: {persona}\n"
                f"AVAILABLE KPIs: {kpi_names}\n\n"
                f"RESPONSE TO EVALUATE:\n{output[:1000]}\n\n"
                f"Score each criterion (0.0-1.0) and explain briefly:\n"
            )
            for c in criteria:
                prompt += f"- {c.value}: \n"
            prompt += "\nRespond in format: CRITERION: SCORE | EXPLANATION"

            llm_output = llm_generate(prompt, max_tokens=256)

            # Parse scores from LLM response
            for c in criteria:
                score = 0.5  # default
                details = ""
                for line in llm_output.split("\n"):
                    if c.value.lower() in line.lower():
                        parts = line.split("|")
                        try:
                            score_part = parts[0].split(":")[-1].strip()
                            score = float(score_part)
                            score = max(0.0, min(1.0, score))
                        except (ValueError, IndexError):
                            pass
                        details = parts[1].strip() if len(parts) > 1 else ""
                        break

                results.append(
                    EvalResult(
                        score=score,
                        passed=score >= 0.5,
                        criteria=c,
                        details=f"[LLM-judge] {details}",
                    )
                )

        except Exception as exc:
            logger.warning("LLM-as-judge failed, falling back to rules: %s", exc)
            return self.evaluate(output, context, criteria)

        return results


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


def get_metrics_collector() -> MetricsCollector:
    """Return the global metrics collector singleton."""
    return metrics
