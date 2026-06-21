# ADR-011: LLMOps Prompt Versioning and Lifecycle Management

## Status

Accepted

## Context

Prompts were defined inline in agent code, making it impossible to track changes, run A/B experiments, or deprecate old prompts safely. Multiple modules duplicated the same system prompt strings.

## Decision

Centralize all prompts in a versioned `PromptRegistry` (`ai_layer/prompts.py`):

- **`PromptTemplate`** — frozen dataclass bundling system + user prompt strings with `version`, `lifecycle` (draft → active → deprecated → retired), `variant`, and metadata.
- **`PromptRegistry`** — stores templates keyed by `(name, version, variant)`. Supports `get()` with latest-active-version resolution, `deprecate()` for lifecycle transitions, and `list_prompts()` for inventory.
- **A/B variant support** — multiple variants of the same prompt can coexist; callers select by variant name.
- Four prompt templates registered by default: `operational_brief`, `kpi_explanation`, `anomaly_diagnosis`, `promotion_strategy`.

## Consequences

- All prompt text lives in one file — changes are auditable via git diff.
- Version pinning in production prevents unintended prompt regressions.
- A/B experimentation is possible without code changes — register a new variant and route traffic.
- Deprecated prompts remain accessible but are excluded from latest-version resolution.
- Adding new prompts requires only defining a `PromptTemplate` and calling `registry.register()`.
