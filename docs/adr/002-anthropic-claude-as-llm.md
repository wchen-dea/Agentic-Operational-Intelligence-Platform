# ADR-002: Anthropic Claude as LLM Provider

## Status

Accepted

## Context

The recommendation agent needs to generate natural-language operational briefs for store managers and executives. The LLM must support structured system prompts, produce concise actionable output, and integrate easily via a Python SDK.

## Decision

Use Anthropic Claude (via the `anthropic` Python SDK) as the LLM provider. The default model is `claude-sonnet-4-20250514`, configurable in `config/settings.py`. The platform supports multiple interaction modes:

- **`generate()`** — synchronous text generation with LRU response caching (128 entries) and token tracking
- **`generate_with_tools()`** — multi-turn tool-calling loop (up to 5 rounds) wiring agent skills into Claude's tools parameter
- **`generate_stream()`** — async SSE streaming via `client.messages.stream()`
- **`generate_async()`** — non-blocking async generation via `AsyncAnthropic`
- **`generate_with_image()`** — multimodal vision input accepting PNG, JPEG, GIF, and WebP images

A `ModelRouter` (`ai_layer/model_router.py`) selects the optimal model by task complexity:
- **Haiku** — classification, intent routing, simple lookups (lowest cost)
- **Sonnet** — generation, narratives, operational briefs (balanced)
- **Opus** — complex reasoning, multi-step analysis, evaluation (highest capability)

The router provides automatic fallback on rate limit or model failure.

## Consequences

- Requires `ANTHROPIC_API_KEY` environment variable for LLM-enhanced output.
- The system degrades gracefully: without the key, it returns structured template readouts.
- Vendor lock-in is minimal — the `ai_layer/llm.py` module abstracts all calls; swapping to another provider requires changing only that file.
- Token costs are tracked per-session via `LLMUsage` dataclass and exposed at `GET /usage`.
- Response caching avoids redundant API calls for identical prompts (saves ~30-50% in repeated queries).
- Model routing reduces costs by ~60% for classification tasks (Haiku vs. Sonnet).
