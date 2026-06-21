# ADR-011: LLMOps Prompt Versioning and Lifecycle Management

## Status

Accepted

## Context

Prompts were defined inline in agent code, making it impossible to track changes, run A/B experiments, or deprecate old prompts safely. Multiple modules duplicated the same system prompt strings.

## Decision

Centralize all prompts in a versioned `PromptRegistry` (`ai_layer/prompts.py`):

- **`PromptTemplate`** — frozen dataclass bundling system + user prompt strings with `version`, `lifecycle` (draft → active → deprecated → retired), `variant`, and metadata.
- **`PromptRegistry`** — stores templates keyed by `(name, version, variant)`. Full runtime API: `get()` with latest-active-version resolution, `register()`, `deprecate()`, `retire()`, `names()`, `versions()`, and filtered `list_prompts(lifecycle, variant)`.
- **A/B variant support** — multiple variants of the same prompt can coexist; callers select by variant name. The `ExperimentManager` (`ai_layer/experimentation.py`) provides deterministic traffic splitting, per-variant metric collection, and Welch's t-test statistical significance testing.
- Four prompt templates registered by default: `operational_brief`, `kpi_explanation`, `anomaly_diagnosis`, `promotion_strategy`.

## Consequences

- All prompt text lives in one file — changes are auditable via git diff.
- Version pinning in production prevents unintended prompt regressions.
- A/B experimentation is automated via `ExperimentManager`: create an experiment with traffic weights, assign variants deterministically by session, record quality scores, and test significance.
- Deprecated and retired prompts are excluded from latest-version resolution but remain accessible by explicit version.
- Adding new prompts requires only defining a `PromptTemplate` and calling `registry.register()`.
- The `retire()` method provides a stronger signal than `deprecate()` — retired prompts are fully hidden from `get()`.
