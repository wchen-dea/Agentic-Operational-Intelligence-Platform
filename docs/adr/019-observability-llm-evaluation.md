# ADR-019: Observability and LLM Evaluation Framework

## Status

Accepted

## Context

A production AI platform requires two distinct observability concerns: (1) infrastructure observability (latency, throughput, error rates) and (2) AI quality observability (is the LLM output grounded, relevant, and actionable?). Standard APM tools cover the first; a purpose-built LLM evaluation layer is required for the second.

## Decision

Implement a three-component observability stack:

**1. `MetricsCollector`** (`observability/metrics/`) — Prometheus-compatible counters, gauges, and histograms. Emitted automatically by the `DAGExecutor` on every agent node execution and by the `LLM` client on every API call. Exported at `GET /metrics` in Prometheus exposition format.

**2. `LLMEvaluator`** (`observability/evaluation.py`) — scores each LLM output on five criteria using rule-based checks first, then LLM-as-judge for ambiguous cases:
- **Groundedness** — key facts from context appear in response.
- **Relevance** — response addresses the stated question.
- **Persona fit** — tone and framing match the declared persona.
- **Conciseness** — response length within expected range.
- **Actionability** — at least one specific action item present.

**3. `AgentPerformanceTracker`** — records per-agent-node timing, retry counts, fallback usage, and token consumption. Automatically included in `execution_trace` in every API response.

OTel distributed tracing is optional (disabled by default). Enable via `AOIP_OTEL__ENABLED=true` + `AOIP_OTEL__ENDPOINT`.

## Alternatives considered

| Option | Reason not chosen |
|--------|------------------|
| Datadog / New Relic APM | SaaS cost; overkill for local dev; same metrics accessible via Prometheus |
| LangSmith evaluation | Tied to LangChain ecosystem; requires LangSmith account |
| Human evaluation only | Not scalable; no real-time feedback loop |
| RAGAS | Good for RAG-specific evaluation but not agent-level multi-criteria scoring |

## Consequences

### Positive
- `GET /metrics` produces Prometheus-scrapable output — connects to Grafana with zero code changes.
- LLM-as-judge evaluation degrades gracefully to rule-based when the API key is absent.
- `execution_trace` in every API response enables client-side performance debugging without server log access.
- 50+ metrics cover data freshness, AI quality, agent performance, LLM usage, skill execution, orchestration, guardrails, auth, and A/B experiments.

### Negative / trade-offs
- LLM-as-judge evaluation adds 1–2 API calls per response — increases latency and cost for evaluated requests.
- `MetricsCollector` is in-process — metrics are not shared across API replicas in horizontal scaling.

### Neutral / constraints
- OTel tracing spans wrap agent node execution automatically when `AOIP_OTEL__ENABLED=true`.
- The `AgentPerformanceTracker` is thread-safe and shared across concurrent request handlers.
