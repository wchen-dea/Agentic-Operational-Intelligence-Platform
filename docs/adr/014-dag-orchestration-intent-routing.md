# ADR-014: DAG-Based Agent Orchestration with Intent Routing

## Status

Accepted

## Context

Early versions of the platform used a fixed sequential pipeline (KPI → Anomaly → Promotion → Recommendation) for every query. This approach executes unnecessary agents for simple questions (e.g., a KPI lookup runs the full promotion + recommendation pipeline) and cannot parallelize independent agent tiers.

## Decision

Replace the fixed pipeline with a declarative **`AgentDAG`** with three components:

1. **`IntentRouter`** (`ai_system/orchestration/router.py`) — classifies query intent using two-phase matching:
   - Phase 1: rule-based regex keyword matching (fast, no API call).
   - Phase 2 (future): LLM-based classification for ambiguous queries.
   - Output: `{intent, confidence, required_agents}`.

2. **`DAGBuilder`** — extracts the minimal agent subgraph for the intent:
   - `kpi_query` → [kpi, rag_search]
   - `anomaly_check` → [kpi, anomaly, rag_search]
   - `operational_brief` → [kpi, anomaly, promotion, recommendation, rag_search]

3. **`DAGExecutor`** (`ai_system/orchestration/executor.py`) — executes tiers in topological order:
   - Independent nodes within a tier run in parallel (via `asyncio.gather`).
   - Per-node retry with exponential backoff (`RetryPolicy`).
   - Circuit breaker: aborts if a tier fails after all retries exhausted.
   - Full `execution_trace` in every API response (per-node timing, attempts, fallback flag).

## Alternatives considered

| Option | Reason not chosen |
|--------|------------------|
| Fixed sequential pipeline | Runs unnecessary agents; cannot parallelize; tight coupling |
| LangChain agent loop | Black-box execution; limited observability; hard to test deterministically |
| LangGraph | Excellent but adds heavy dependency; custom DAG gives full control over retry/fallback/trace |
| ReAct loop (single LLM agent) | Unpredictable tool selection; higher token cost; harder to evaluate |

## Consequences

### Positive
- A simple KPI query avoids running promotion and recommendation agents — ~60% token cost reduction.
- Parallel tier execution reduces wall-clock time for complex briefs by running independent agents concurrently.
- `execution_trace` in every response enables observability, debugging, and performance regression detection.
- Each agent node is independently testable via its `run()` method without the full DAG.

### Negative / trade-offs
- Declarative DAG requires upfront dependency specification — incorrect dependency declaration causes silent correctness bugs.
- Phase 1 intent routing (regex) can misclassify ambiguous queries — Phase 2 (LLM classification) is planned but not yet implemented.

### Neutral / constraints
- DAG nodes are defined in `ai_system/orchestration/dag.py` with `AgentNode(name, dependencies, agent)`.
- The executor emits `agent_duration_ms`, `agent_executions_total`, and `agent_failures_total` metrics on every node execution.
