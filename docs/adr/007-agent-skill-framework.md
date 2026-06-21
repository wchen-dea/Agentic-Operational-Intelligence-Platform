# ADR-007: Agent Skill Framework for Composable Capabilities

## Status

Accepted

## Context

Agents had hardcoded dependencies on specific tool functions, making it difficult to reuse capabilities across agents, expose them to LLM tool-calling, or instrument them individually. Adding a new capability required modifying agent code directly.

## Decision

Introduce a formal Skill abstraction (`ai_layer/skills/`) with:

- **`Skill` ABC** — each skill declares a `SkillDescriptor` (name, description, typed parameters, tags) and implements `execute()`.
- **`SkillRegistry`** — central catalog for discovering skills by name or tag, with `to_tool_schemas()` for LLM function-calling export.
- **Auto-instrumented `invoke()`** — every skill execution emits latency and success/failure metrics via the observability tracker.
- **API exposure** — `GET /skills` lists available tools; `POST /skills/{name}/invoke` executes any skill for debugging or external agent integration.

Five initial skills wrap existing tools: `fetch_kpis`, `detect_anomalies`, `semantic_search`, `diagnose_signals`, `generate_narrative`.

## Consequences

- New capabilities are added by implementing `Skill` and registering — zero changes to existing agents.
- LLM agents can autonomously select and invoke skills via function-calling schemas.
- Per-skill observability is automatic (latency, success rate, fallback usage).
- Agents can dynamically discover skills by tag (e.g., `registry.find_by_tag("analysis")`).
- Adds one level of indirection; direct tool calls remain available for performance-critical paths.
