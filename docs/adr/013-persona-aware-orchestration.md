# ADR-013: Persona-Aware Agent Orchestration

## Status

Accepted

## Context

Store managers and executives have fundamentally different decision horizons, action authority, and information needs. A single undifferentiated response reduces relevance for both audiences. A store manager needs localized, actionable, immediate interventions; an executive needs regional variance, cross-store prioritization, and strategy-level recommendations.

## Decision

The orchestrator accepts a `persona` parameter (`store_manager` or `executive`) that shapes three aspects of every agent response:

1. **System prompt tone** — `store_manager`: operational, direct, local; `executive`: strategic, regional, prioritized.
2. **Recommendation framing** — `store_manager`: "coach staff on branded upsell script"; `executive`: "reallocate campaign budget to region 3".
3. **Priority action ownership** — `store_manager`: actions they can execute today; `executive`: decisions that require cross-store resource shifts.

The persona is passed through the entire DAG execution: context assembly → agents → recommendation agent → brief generation. Default: `store_manager`.

## Alternatives considered

| Option | Reason not chosen |
|--------|------------------|
| Post-hoc reformatting (single response, reformatted by role) | Loses nuance — the same facts require different framing at inference time, not post-processing |
| Hard-coded role-specific endpoints | Poor maintainability; adding a third persona requires new endpoints and duplicated logic |
| User preference learning (fine-tuned per user) | Requires feedback loop infrastructure not yet in place |

## Consequences

### Positive
- Adding a new persona (e.g., `regional_manager`) requires only updating the system prompt template and the recommendation agent's playbook selector.
- Persona context is included in the `PersistentSessionMemory` — multi-turn conversations maintain persona continuity.
- A/B experimentation (`ExperimentManager`) can test persona-differentiated prompt variants independently.

### Negative / trade-offs
- API consumers must explicitly specify persona or accept the `store_manager` default.
- Two personas require maintaining two prompt variants per agent — `PromptRegistry` manages these with semantic versioning.

### Neutral / constraints
- Persona is validated at the API layer — invalid persona values return HTTP 422 before reaching the orchestrator.
