# ADR-010: Observability and LLM Evaluation Framework

## Status

Accepted

## Context

There was no structured way to measure agent performance, LLM output quality, or system-level health. Debugging slow responses or poor recommendations required manual log inspection.

## Decision

Add an observability and evaluation layer (`observability/evaluation.py`):

- **`MetricsCollector`** — counters, gauges, and histograms with a Prometheus-compatible interface. In production, emits to Prometheus, Datadog, or CloudWatch.
- **`LLMEvaluator`** — rule-based quality scoring for groundedness (KPI reference coverage), actionability (action-verb density), and conciseness (word count).
- **`AgentPerformanceTracker`** — records per-agent execution duration, retries, fallbacks, and per-LLM-call token usage.
- The `DAGExecutor` automatically emits metrics on every agent node execution.

## Consequences

- Every agent execution produces measurable latency and success/failure signals.
- LLM outputs can be scored automatically on each request for quality regression detection.
- Token usage tracking enables cost monitoring and budget alerting.
- Adding new evaluation criteria requires implementing a new evaluator method — no changes to agents.
- Production deployments should connect `MetricsCollector` to an external metrics backend.
