# ADR-015: Agent Skill Framework for Composable Capabilities

## Status

Accepted

## Context

Agent capabilities (fetch KPIs, detect anomalies, search knowledge, generate narratives) were initially implemented as ad-hoc functions called directly from agent classes. This made skills hard to discover, test independently, version, or export as LLM tool schemas. A composable skill framework enables skills to be invoked uniformly — whether by an agent, an API caller, or via LLM tool-calling.

## Decision

Implement a `Skill` abstract base class (`ai_systems/skills/`) with a `SkillRegistry` singleton that:

- Exposes each skill via `invoke(name, **kwargs)` — uniform invocation interface.
- Exports all skills as LLM function-calling definitions via `to_tool_schemas()`.
- Auto-instruments every `invoke()` call with latency and success/failure metrics.
- Enables discovery by name or tag (`registry.list_by_tag("kpi")`).

Five built-in skills:

| Skill | Description | Tags |
|-------|-------------|------|
| `fetch_kpis` | Retrieves KPI metrics from MySQL ODS or SQLite | kpi, data, read |
| `detect_anomalies` | Evaluates KPIs against threshold rules in `kpi_thresholds.yaml` | anomaly, alerts |
| `semantic_search` | Hybrid ChromaDB + TF-IDF RRF search over the knowledge corpus | rag, search |
| `diagnose_signals` | Correlates KPI anomalies with operational events | diagnosis, analysis |
| `generate_narrative` | Produces persona-aware natural-language summaries | llm, generation |

## Alternatives considered

| Option | Reason not chosen |
|--------|------------------|
| Ad-hoc functions (no framework) | Non-discoverable; no uniform invocation; no auto-instrumentation |
| LangChain tools | Black-box; ties skills to LangChain's execution model; harder to test |
| OpenAI function definitions (static) | JSON-only; no Python type safety; no auto-instrumentation |

## Consequences

### Positive
- `to_tool_schemas()` generates the exact JSON schema expected by Claude's tools parameter — no manual schema maintenance.
- Skills are independently testable with `registry.invoke("fetch_kpis", store_id="245")`.
- Adding a new skill requires implementing `Skill.execute()` and calling `registry.register()` — no changes to existing agents.
- Auto-instrumented `skill_invocations_total` and `skill_duration_ms` metrics are emitted automatically.

### Negative / trade-offs
- The `SkillRegistry` is a singleton — skills must be stateless or accept all required state as parameters.
- Tool schema generation relies on Python type annotations — missing annotations produce malformed schemas.

### Neutral / constraints
- Skills are registered at startup in `ai_systems/gateway/api/app.py`; the registry is thread-safe.
