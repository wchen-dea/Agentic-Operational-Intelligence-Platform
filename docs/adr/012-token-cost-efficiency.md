# ADR-012: Token Cost-Efficiency and LLM Usage Tracking

## Status

Accepted

## Context

Every LLM call costs money — Claude Sonnet charges ~$3 per million input tokens and ~$15 per million output tokens. Without controls, the platform can incur unnecessary spend through:

- **Redundant calls**: identical questions within the same session produce identical answers but are billed again.
- **Oversized prompts**: agents dump full KPI dictionaries, all alerts, and verbose context documents into the prompt even when most data is irrelevant.
- **Unbounded output**: the default `max_tokens` (1024) is used everywhere, even for short operational briefs that rarely exceed 300 tokens.
- **No visibility**: operators have no way to see how many tokens a request consumed or what it cost.

As the platform scales to more users and higher query volumes, unmanaged token usage becomes a significant operational cost risk.

## Decision

Implement a layered cost-efficiency strategy in `ai_layer/llm.py`, `ai_layer/agents/recommendation_agent.py`, and `ai_layer/agents/orchestrator.py`:

### 1. LRU Response Cache (`ai_layer/llm.py`)

- SHA-256 key derived from `system + prompt + max_tokens`.
- 128-entry in-process cache; identical requests return instantly with zero token cost.
- Callers can bypass the cache via `use_cache=False` when freshness matters.

### 2. Per-Call Token Tracking (`ai_layer/llm.py`)

- `LLMUsage` dataclass records `input_tokens`, `output_tokens`, `cache_hit`, `duration_ms`, and `estimated_cost_usd` for every `generate()` call.
- Session-level accumulators (`get_session_usage()`, `get_session_cost_summary()`) aggregate across all calls within a request.
- `reset_session_usage()` is called at the start of each orchestrator `answer()` invocation to scope tracking per request.

### 3. Compact Prompt Construction (`ai_layer/agents/recommendation_agent.py`)

- `_build_compact_readout()` sends only anomalous KPI signals, caps alerts at 5, truncates context docs to 100 characters each, and omits playbook text.
- Full verbose readout is preserved as `_build_full_readout()` for the non-LLM fallback path.
- Estimated input token reduction: 40–60% per recommendation call.

### 4. Intent-Aware `max_tokens` Scaling

- `generate()` accepts an optional `max_tokens` override so each agent can right-size output.
- Recommendation agent uses `max_tokens=512` instead of the global default of 1024.
- Other agents can specify their own limits as needed.

### 5. Cost Visibility Endpoints

- `GET /usage` returns cumulative process-level token usage and estimated cost.
- Every `/ask` response includes a `token_usage` field with call count, cache hit count, total tokens, and estimated cost in USD.

## Consequences

- **Cost reduction**: ~40–60% fewer input tokens (compact readout), ~50% fewer output tokens (reduced max_tokens), and 100% savings on cache-hit queries.
- **Model routing**: the `ModelRouter` (`ai_layer/model_router.py`) further reduces costs by routing classification/extraction tasks to Haiku (~12x cheaper than Sonnet) and reserving Opus for complex reasoning.
- **Operational visibility**: teams can monitor per-request cost at `GET /usage` and system-wide metrics at `GET /metrics` (Prometheus format).
- **Cache trade-off**: cached responses may serve stale data when underlying KPIs change between calls. The `use_cache=False` escape hatch mitigates this.
- **In-process cache only**: the LRU cache is not shared across workers or pods. A distributed cache (Redis) can be added later if hit rates justify it.
- **Pricing assumptions**: cost estimates hard-code Claude Sonnet rates. If the model changes (see ADR-002), pricing constants in `LLMUsage` must be updated.
