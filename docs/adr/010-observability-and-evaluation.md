# ADR-010: Observability and LLM Evaluation Framework

## Status

Accepted

## Context

There was no structured way to measure agent performance, LLM output quality, or system-level health. Debugging slow responses or poor recommendations required manual log inspection.

## Decision

Add an observability and evaluation layer (`observability/evaluation.py`):

- **`MetricsCollector`** — counters, gauges, and histograms with a Prometheus-compatible interface. Exported via `GET /metrics` in Prometheus exposition format. In production, can also emit to Datadog or CloudWatch.
- **`LLMEvaluator`** — five rule-based quality criteria: groundedness (KPI reference coverage), actionability (action-verb density), conciseness (word count), relevance (question keyword overlap + intent alignment), and persona-fit (vocabulary markers for executive vs. store manager).
- **`evaluate_with_llm()`** — LLM-as-judge evaluation that sends the output to Claude for scoring; falls back to rule-based evaluation when no API key is available.
- **`AgentPerformanceTracker`** — records per-agent execution duration, retries, fallbacks, and per-LLM-call token usage.
- The `DAGExecutor` automatically emits metrics on every agent node execution.

## Consequences

- Every agent execution produces measurable latency and success/failure signals.
- LLM outputs can be scored automatically on each request for quality regression detection.
- The Prometheus `/metrics` endpoint enables Grafana dashboards and alerting without additional infrastructure.
- LLM-as-judge evaluation provides nuanced quality scores when an API key is available, with graceful degradation to rules.
- Token usage tracking enables cost monitoring and budget alerting.
- Adding new evaluation criteria requires implementing a new evaluator method — no changes to agents.
- Production deployments can scrape `/metrics` or connect `MetricsCollector` to an external metrics backend.
