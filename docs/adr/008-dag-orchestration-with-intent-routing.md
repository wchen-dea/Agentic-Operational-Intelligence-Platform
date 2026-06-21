# ADR-008: DAG-Based Agent Orchestration with Intent Routing

## Status

Accepted

## Context

The original orchestrator ran all agents in a fixed linear sequence regardless of the user's query. This wasted compute for simple KPI lookups that did not need promotion analysis or recommendation generation. There was no retry logic, no fallback handling, and no visibility into per-agent execution performance.

## Decision

Replace the linear pipeline with a DAG-based orchestrator (`ai_layer/orchestration/`):

- **`AgentDAG`** — declarative graph of agent nodes with typed dependencies, enabling topological tier ordering and subgraph extraction.
- **`IntentRouter`** — classifies user queries into intents (KPI, anomaly, promotion, brief, general QA) and maps each intent to the minimum required agent subgraph.
- **`DAGExecutor`** — walks the DAG tier by tier with parallel execution of independent nodes, configurable `RetryPolicy` (exponential backoff), and fallback handlers.
- Every API response includes an `execution_trace` with per-node timing, attempt counts, and fallback usage.

## Consequences

- Queries that only need KPIs skip promotion and recommendation agents entirely.
- Independent agents (e.g., KPI + RAG search) execute in parallel within the same tier.
- Transient failures are retried with backoff before triggering fallbacks.
- Non-optional agent failures abort the DAG; optional agent failures degrade gracefully.
- Execution traces enable performance debugging and SLA monitoring.
