# ADR-017: LLMOps — Prompt Versioning and A/B Experimentation

## Status

Accepted

## Context

LLM prompt quality directly determines output relevance and persona fit. As the platform evolves, prompts need to be updated without breaking existing behaviour, rolled back if quality regresses, and A/B tested to validate improvements statistically. Without structured prompt management, prompts become scattered across agent files and impossible to version or roll back safely.

## Decision

Centralize all prompts in a versioned **`PromptRegistry`** (`ai_systems/prompts.py`) with lifecycle states:

```
draft → active → deprecated → retired
```

Each prompt entry carries: `name`, `version` (semantic), `text`, `status`, `metadata`, and `variants` (for A/B).

**`ExperimentManager`** (`ai_systems/experimentation.py`) provides:
- Deterministic traffic splitting by session ID (SHA-256 mod N) — consistent experience within a session.
- Per-variant metric collection (`mean_score`, `impressions_total`).
- Welch's t-test significance testing at configurable α-level.

Four active prompt templates:
- `operational_brief` — persona-aware brief generation.
- `kpi_explanation` — semantic KPI narrative for store managers.
- `anomaly_diagnosis` — root-cause analysis framing.
- `promotion_strategy` — branded upsell recommendation playbook.

## Alternatives considered

| Option | Reason not chosen |
|--------|------------------|
| Prompts hard-coded in agent files | No versioning; no rollback; scattered across codebase |
| LangSmith prompt hub | SaaS dependency; requires LangChain; adds external state |
| Git-tracked plain text files | No runtime lifecycle management; no A/B testing; no hot-swap |

## Consequences

### Positive
- Hot-swapping a prompt from `draft` to `active` requires no code deployment — only a registry update.
- A/B experiments produce statistically validated improvements before full rollout.
- `deprecated` prompts remain queryable for audit — no data loss on rollback.
- Prompt registry is exposed at `GET /usage` for runtime inspection.

### Negative / trade-offs
- The in-process registry is ephemeral — prompt changes do not survive API server restarts without persistence (future: PostgreSQL backend).
- A/B experiments require sufficient traffic volume to reach statistical significance — low-traffic deployments may not converge within a reasonable time window.

### Neutral / constraints
- Prompt registry is seeded at API startup in `services/api/app.py`.
- `ExperimentManager` significance threshold defaults to `α = 0.05` (95% confidence); configurable.
