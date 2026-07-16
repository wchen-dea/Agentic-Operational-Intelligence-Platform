# ADR-011: Anthropic Claude as LLM Provider

## Status

Accepted

## Context

The AI layer needs an LLM to generate natural-language operational briefs, classify user intent (KPI / anomaly / promotion / brief / QA), and power multi-turn tool-calling agent loops. The LLM must support structured system prompts, produce concise actionable output, integrate via a Python SDK with async and streaming support, and degrade gracefully when the API key is absent.

## Decision

Use **Anthropic Claude** (via the `anthropic` Python SDK) as the primary LLM provider. Default model: `claude-sonnet-4-20250514`, configurable in `ai_systems/config/settings.py` via `AOIP_LLM__MODEL`.

The `ai_systems/core/llm.py` module implements five interaction modes:
- **`generate()`** — synchronous text generation with SHA-256 LRU cache (128 entries).
- **`generate_with_tools()`** — multi-turn tool-calling loop (up to 5 rounds) wiring agent skills into Claude's `tools` parameter.
- **`generate_stream()`** — async SSE streaming via `client.messages.stream()`.
- **`generate_async()`** — non-blocking async generation via `AsyncAnthropic`.
- **`generate_with_image()`** — multimodal vision input (PNG, JPEG, GIF, WebP).

**Model routing** (`ai_systems/core/model_router.py`) selects the optimal model by task complexity:
- **Haiku** — intent classification, simple lookups (lowest latency, lowest cost).
- **Sonnet** — operational briefs, recommendation generation (balanced).
- **Opus** — complex multi-step reasoning, edge cases (highest capability).

## Alternatives considered

| Option | Reason not chosen |
|--------|------------------|
| OpenAI GPT-4o | Comparable capability; Claude chosen for tool-calling reliability and instruction following in structured output tasks |
| Google Gemini 1.5 Pro | Strong multimodal; Python SDK less mature at decision time |
| Meta Llama 3 (self-hosted) | Requires GPU infrastructure; higher operational cost for equivalent quality |
| Mistral (cloud) | Less strong on structured output and instruction following for retail domain tasks |

## Consequences

### Positive
- Vendor lock-in is minimal — `ai_systems/core/llm.py` abstracts all calls; swapping to another provider requires changing only that file and `ai_systems/config/settings.py`.
- Graceful degradation: without `ANTHROPIC_API_KEY`, the platform returns structured template output instead of failing.
- Response caching avoids redundant API calls for identical prompts (~30–50% cost reduction in repeated queries).
- Model routing reduces costs by ~60% for classification tasks (Haiku vs. Sonnet).
- Tool-calling loop supports up to 5 rounds — sufficient for all current agent skill chains.

### Negative / trade-offs
- Requires `ANTHROPIC_API_KEY` for LLM-enhanced output — CI tests set `AOIP_AUTH_DISABLED=true` and test without the key.
- Claude API rate limits (RPM/TPM) may require backoff logic under high load — the `ModelRouter` provides automatic fallback but not exponential backoff yet.
- Vision input requires image bytes in the request body — large images increase latency and token cost.

### Neutral / constraints
- Token costs are tracked per-session via `LLMUsage` dataclass and exposed at `GET /usage`.
- The `LLMSettings` in `ai_systems/config/settings.py` exposes `provider`, `model`, `max_tokens`, `temperature`, and `api_key_env_var` — all overridable without code changes.
