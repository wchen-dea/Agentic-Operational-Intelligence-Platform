# ADR-002: Anthropic Claude as LLM Provider

## Status

Accepted

## Context

The recommendation agent needs to generate natural-language operational briefs for store managers and executives. The LLM must support structured system prompts, produce concise actionable output, and integrate easily via a Python SDK.

## Decision

Use Anthropic Claude (via the `anthropic` Python SDK) as the LLM provider. The model is configurable in `config/settings.py` and defaults to `claude-sonnet-4-20250514`.

## Consequences

- Requires `ANTHROPIC_API_KEY` environment variable for LLM-enhanced output.
- The system degrades gracefully: without the key, it returns structured template readouts.
- Vendor lock-in is minimal — the `ai_layer/llm.py` module abstracts the call; swapping to another provider requires changing only that file.
- Token costs scale with usage; the `max_tokens` and `temperature` settings control spend and output style.
