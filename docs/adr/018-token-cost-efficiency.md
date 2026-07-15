# ADR-018: Token Cost-Efficiency and LLM Usage Tracking

## Status

Accepted

## Context

LLM API costs are proportional to token consumption. Without active cost management, complex multi-agent queries can consume thousands of tokens per request, making the platform economically unviable at scale. Cost controls must be transparent (visible to operators), retroactive (tracking historical spend), and proactive (reducing tokens before they are sent).

## Decision

Implement a four-layer token cost strategy:

1. **SHA-256 LRU response cache** (128 entries, in `ai_systems/llm.py`) — identical prompts (same text + model) return cached responses; zero API cost for cache hits. Cache key = SHA-256(model + prompt_text).

2. **Model routing** (`ai_systems/model_router.py`) — routes classification tasks to Haiku (~6× cheaper than Sonnet); reserves Sonnet for generation; uses Opus only for complex reasoning. Reduces cost by ~60% for intent classification workloads.

3. **Dynamic `max_tokens` caps** — each output type is capped at the minimum sufficient length:
   - Intent classification: 50 tokens.
   - KPI insight: 300 tokens.
   - Operational brief: 800 tokens.
   - Anomaly diagnosis: 500 tokens.

4. **Per-call `LLMUsage` tracking** — every `generate*()` call records `input_tokens`, `output_tokens`, `model`, and `estimated_cost_usd` (using Anthropic's published per-token pricing). Session totals exposed at `GET /usage`; per-call metrics emitted to `MetricsCollector`.

## Alternatives considered

| Option | Reason not chosen |
|--------|------------------|
| Semantic cache (vector similarity) | Higher false-positive risk (slightly different prompts returning stale responses); implementation complexity |
| Hard token budget per session | Poor UX — truncates responses mid-generation |
| Batch API (async, 50% discount) | Incompatible with real-time SSE streaming requirement |

## Consequences

### Positive
- Cache hit rate of 30–50% observed in repeated queries (same store, same question, different session).
- Cost transparency: `GET /usage` returns session-level breakdown by model and call count.
- Prometheus metrics (`llm_estimated_cost_usd`, `llm_cache_hits_total`) enable cost dashboards in Grafana.
- Haiku routing for classification saves ~$0.004 per request vs. Sonnet.

### Negative / trade-offs
- LRU cache is in-process — not shared across API replicas; horizontal scaling requires a shared cache (Redis with TTL).
- Cost estimates use published pricing at build time — actual invoiced costs may differ due to volume discounts or pricing changes.

### Neutral / constraints
- Cache is cleared on API server restart — intentional, to avoid serving stale responses after prompt updates.
- Token prices are hard-coded in `ai_systems/llm.py`; update when Anthropic changes pricing.
