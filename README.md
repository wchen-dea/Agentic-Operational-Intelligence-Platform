# Agentic Operational Intelligence Platform

Production-shaped AI operations platform for store managers and executives to monitor real-time KPI and alert signals, diagnose root causes, and adjust commercial and operational strategies.

## Project Target Status

Current target status: `agentic-operational-intelligence-platform`

This repository is currently aligned to this target with:

- DAG-based agent orchestrator with intent routing, retry/fallback, and parallel tier execution
- Composable agent skill framework with LLM tool-calling export and per-skill observability
- Persona-aware responses for store managers and executives
- Real-time KPI coverage across sales orders, appointments, POS invoices, inventory, and work orders
- AWS Aurora MySQL as the operational source system for sales orders, appointments, POS invoices, and work orders
- Hybrid context assembly merging streaming state, vector retrieval, and session memory
- Observability and evaluation framework with metrics collection, LLM-as-judge evaluation, and Prometheus export
- LLMOps prompt registry with versioning, lifecycle management, and A/B variant experimentation
- Multi-model routing (Haiku/Sonnet/Opus) with automatic fallback on failure
- Guardrails for prompt injection detection, PII scrubbing, and output quality enforcement
- Structured LLM output via Pydantic-validated response models
- Server-Sent Events streaming and async generation endpoints
- MCP server exposing platform tools, resources, and prompts to any MCP-compatible client
- API key authentication with RBAC (admin/operator/viewer) and per-key rate limiting
- Persistent SQLite-backed session memory with TTL and cross-session knowledge accumulation
- Multimodal (vision) support for image-based KPI chart analysis
- CI/CD pipeline with lint, type checking, tests, coverage, and Docker smoke tests
- Operational strategy outputs for under-performing store diagnosis, branded upsell, and promotion adjustment

## Glossary

- Agentic Operational Intelligence Platform: Canonical product name for this repository and runtime system.
- agentic-operational-intelligence-platform: Canonical package/release identifier used in project metadata.
- Agentic Operational Intelligence Orchestrator: Canonical orchestration component that coordinates KPI, anomaly, promotion, and recommendation agents.
- Store manager persona: User role focused on local, real-time operational diagnosis and execution.
- Executive persona: User role focused on regional and enterprise KPI variance, prioritization, and strategy shifts.
- Operational brief: Persona-aware summary that combines KPI state, active alerts, diagnosis, and priority actions.
- KPI: Key Performance Indicator generated from real-time events across sales orders, appointments, POS invoices, inventory, and work orders.
- AWS Aurora MySQL: System of record for transactional sales-order, appointment, POS-invoice, and work-order applications feeding the real-time KPI pipeline.
- CDC topic naming convention: Kafka/MSK topics follow `retail_ops.aurora.<schema>.<table>`.
- Bronze table naming convention: Landed CDC records follow `bronze.<table>_cdc`.
- Silver table naming convention: Normalized operational tables follow `silver.<table>`.

## Current Capabilities

### API

- FastAPI service with 7 route modules: query, kpi, alerts, operations, skills, streaming, and health
- `POST /ask` — agentic Q&A with guardrails, intent routing, and DAG execution
- `POST /ask/stream` — SSE streaming Q&A with real-time token delivery
- `POST /ask/async` — async non-blocking generation
- `POST /ask/agentic` — tool-calling agentic queries
- `POST /kpi` — fetch KPI metrics for a store or region
- `POST /kpi/enriched` — KPIs with semantic metadata, anomaly flags, and descriptions
- `GET /kpi/catalog` — machine-readable KPI catalog (16 definitions)
- `GET /alerts/{store_id}` — retrieve active alerts for a store
- `POST /operations/brief` — persona-aware operational brief
- `GET /skills` — list all registered agent skills with tool schemas
- `POST /skills/{name}/invoke` — invoke a specific skill by name
- `GET /usage` — LLM token usage and cost tracking for the current session
- `GET /metrics` — Prometheus exposition format metrics export
- `GET /health` — health check
- API key authentication via `X-API-Key` header with RBAC and rate limiting

### Agent Orchestration

- DAG-based orchestrator with declarative agent dependency graph and topological tier execution
- Intent-based task router classifying queries into KPI, anomaly, promotion, brief, or general QA intents
- Per-intent subgraph extraction — only the required agents run for each query
- Multi-turn conversation support with session memory tracking
- Hybrid context assembly (streaming + vector + memory) wired into orchestrator Phase 0
- Configurable retry policies with exponential backoff and fallback handlers per agent node
- Parallel execution of independent agent nodes within each DAG tier
- Full execution tracing with per-node timing, attempt counts, and fallback usage in every API response

### Agent Skills

- Composable skill framework with `Skill` ABC, typed `SkillDescriptor`, and `SkillRegistry`
- Five built-in skills: `fetch_kpis`, `detect_anomalies`, `semantic_search`, `diagnose_signals`, `generate_narrative`
- `to_tool_schemas()` exports all skills as LLM function-calling definitions
- Agentic tool-calling loop via `agentic_query()` wiring skill registry into Claude's tools parameter
- Per-skill observability instrumentation (latency, success/failure metrics)
- Skills discoverable by name or tag; invocable via API or programmatically

### LLM Layer

- Anthropic Claude client abstraction with response caching (128-entry LRU), token tracking, and session cost summary
- `generate()` — standard text generation with cache
- `generate_with_tools()` — multi-turn tool-calling loop (up to 5 rounds)
- `generate_stream()` — async SSE streaming generation
- `generate_async()` — async non-blocking generation
- `generate_with_image()` — multimodal vision input (PNG, JPEG, GIF, WebP)
- Multi-model routing: Haiku (classification) → Sonnet (generation) → Opus (reasoning) with automatic fallback
- Structured LLM output via Pydantic models: `KPIInsight`, `OperationalBriefResponse`, `AnomalyDiagnosisResponse`, `PromotionRecommendation`

### Hybrid Context

- `HybridContextAssembler` merges streaming state, vector/keyword retrieval, and session memory into a unified `ContextWindow`
- `SessionMemory` with sliding-window eviction for multi-turn conversational coherence
- `PersistentSessionMemory` (SQLite-backed) survives process restarts with TTL and cross-session knowledge accumulation
- `StreamingStateStore` with TTL-based cache for real-time KPI snapshots and alerts

### Guardrails

- Input validation: prompt injection detection (7 regex patterns), PII scrubbing (SSN, credit card, email, phone), length limits
- Output validation: blocked content patterns, hallucinated KPI detection, quality checks
- Wired into `/ask` endpoint — prompt injection returns HTTP 400, PII is scrubbed transparently

### Observability and Evaluation

- `MetricsCollector` with counters, gauges, and histograms (Prometheus-compatible interface)
- `GET /metrics` endpoint exporting Prometheus exposition format
- `LLMEvaluator` with rule-based quality scoring for groundedness, actionability, conciseness, relevance, and persona-fit
- `evaluate_with_llm()` — LLM-as-judge evaluation with rule-based fallback
- `AgentPerformanceTracker` recording agent duration, retries, fallbacks, and LLM token usage
- Automatic metrics emission from DAG executor on every agent node execution

### LLMOps

- Centralized `PromptRegistry` with semantic versioning and lifecycle states (draft → active → deprecated → retired)
- Runtime API: `get()`, `register()`, `deprecate()`, `retire()`, `names()`, `versions()`, filtered `list_prompts()`
- A/B variant experimentation via `ExperimentManager`: deterministic traffic splitting, per-variant metric collection, Welch's t-test significance testing
- Four prompt templates: `operational_brief`, `kpi_explanation`, `anomaly_diagnosis`, `promotion_strategy`

### Security

- API key authentication via `X-API-Key` header with SHA-256 hashing
- RBAC with three roles: admin (full access), operator (query + operations), viewer (read-only KPI/alerts)
- Per-key sliding-window rate limiting (configurable per minute)
- Environment-based key registration (`AOIP_API_KEY_ADMIN`, `AOIP_API_KEY_OPERATOR`, `AOIP_API_KEY_VIEWER`)
- Dev bypass via `AOIP_AUTH_DISABLED=true`

### MCP Server

- Model Context Protocol server exposing 5 tools, 2 resources, and 2 prompts
- Tools: `get_store_kpis`, `get_region_kpis`, `get_enriched_kpis`, `detect_alerts`, `search_knowledge_base`
- Resources: `kpi://catalog`, `config://thresholds`
- Prompts: `operational_brief`, `anomaly_investigation`
- Compatible with Claude Desktop, VS Code Copilot, and any MCP client

### Data Platform

- Typed semantic KPI layer (`KPIRecord`, `StoreKPISnapshot`) with anomaly flags and LLM-ready summaries
- Machine-readable KPI catalog (16 KPIs with unit, direction, thresholds, descriptions)
- SQLite-backed queryable KPI data store with `KPIDataSource` protocol
- Hybrid RAG with ChromaDB vector search + TF-IDF keyword search and reciprocal rank fusion
- Domain and persona metadata filtering on RAG corpus
- Enriched JSON schemas for 5 domains (appointment, sales order, POS invoice, work order, inventory)
- Enriched alert rules with unit, direction, description, and remediation guidance
- Streaming KPI aggregator logic with cross-domain operational metrics
- Bronze, silver, and gold Databricks ingestion assets for Aurora MySQL modeling
- Sample AWS DMS to Kafka/MSK CDC task spec

### CI/CD

- GitHub Actions workflow: lint (ruff), type check (pyright), test (pytest), coverage gate (60%)
- Docker image build and smoke test on push to main
- pyright basic mode type checking with workspace-wide configuration
- ruff linting with Python 3.12 target

## Source Systems

The current project target assumes the following operating model:

- AWS Aurora MySQL stores transactional data for the sales order system, appointment application, POS invoice activities, and work order activities.
- Inventory signals may be sourced from Aurora MySQL or a downstream inventory service, but are modeled as part of the same operational KPI layer.
- Change data capture from Aurora MySQL should feed the real-time event stream that drives KPI aggregation, anomaly detection, and executive/store-manager alerts.

CDC naming conventions used by the reference assets:

- Kafka/MSK topic: `retail_ops.aurora.<schema>.<table>`
- Bronze landing table: `bronze.<table>_cdc`
- Silver normalized table: `silver.<table>`
- Gold KPI rollup table: `gold.store_realtime_kpis`

## AI Operational Intelligence Focus

This project is designed for two decision personas:

- Store managers: real-time diagnosis for local under-performance, inventory constraints, service backlog, and conversion blockers.
- Company executives: regional KPI variance monitoring, cross-store prioritization, and strategy shifts for promotion and margin improvement.

The AI layer combines KPI signals and alerts across:

- Sales order system on AWS Aurora MySQL
- Appointment application on AWS Aurora MySQL
- POS invoice activities on AWS Aurora MySQL
- Inventory health signals
- Work order activities on AWS Aurora MySQL

The resulting recommendations help teams:

- Diagnose under-performing stores quickly
- Increase branded upsell mix using targeted scripts and bundles
- Adjust store-level promotions based on inventory and operations readiness
- Improve execution quality before scaling campaign spend

## Quick start

```bash
uv sync --dev
uv run uvicorn services.api.app:app --reload --port 8000
```

### Run tests

```bash
uv run pytest -q              # 150 tests
uv run pyright                # type checking
uv run ruff check .           # linting
```

### Generate persona-aware operational brief

```bash
curl -X POST http://localhost:8000/operations/brief \
  -H "Content-Type: application/json" \
  -d '{"store_id":"245","region":"Phoenix","persona":"executive"}'
```

### Agentic Q&A

```bash
curl -X POST http://localhost:8000/ask \
  -H "Content-Type: application/json" \
  -d '{"question":"Why are Phoenix sales down today and what promotion should we adjust?","store_id":"245","region":"Phoenix"}'
```

### Streaming Q&A (SSE)

```bash
curl -N -X POST http://localhost:8000/ask/stream \
  -H "Content-Type: application/json" \
  -d '{"question":"Summarize store 245 KPIs","store_id":"245"}'
```

### MCP Server

```bash
uv run python -m services.mcp_server
```

## Repo Layout

```text
ai_layer/
  agents/            KPI, anomaly, promotion, recommendation agents
  orchestration/     DAG engine, intent router, DAG executor with retry/fallback
  skills/            Skill ABC, catalog of built-in skills, singleton registry
  rag/               ChromaDB + TF-IDF hybrid search retriever and corpus data
  memory/            Persistent SQLite-backed session memory
  context.py         Hybrid context assembler (streaming + vector + memory)
  experimentation.py A/B prompt experimentation with traffic splitting and significance testing
  guardrails.py      Input/output validation, prompt injection detection, PII scrubbing
  llm.py             Anthropic Claude client (sync, async, streaming, vision, tool-calling)
  model_router.py    Multi-model routing (Haiku/Sonnet/Opus) with fallback
  prompts.py         Versioned prompt registry with lifecycle management
  structured_output.py  Pydantic-validated structured LLM responses
  tool_calling.py    Agentic tool-calling loop wiring skills to Claude tools
config/              Runtime settings, Aurora MySQL / CDC placeholders
services/
  api/               FastAPI app with query, kpi, alerts, operations, skills, streaming routes
    auth.py          API key authentication, RBAC, and rate limiting
  mcp_server.py      Model Context Protocol server (5 tools, 2 resources, 2 prompts)
  scheduler/         Daily summary job
data_platform/
  kpi_catalog.yaml   Machine-readable KPI definitions (16 KPIs)
  kpi_store.py       SQLite-backed queryable KPI data store
  semantic_layer.py  Typed KPI records with anomaly detection and LLM-ready summaries
  schemas/           Enriched JSON schemas for 5 operational domains
  batch/             Databricks SQL and notebooks (bronze/silver/gold)
  streaming/         Flink KPI aggregator logic
alerts/              Alert engine, enriched threshold config, dispatch channels
observability/       Metrics collector, LLM evaluator, agent performance tracker
tests/               150 unit tests across agents, orchestration, API, data, and AI gaps
docs/                Runbook and 12 ADRs
.github/workflows/   CI/CD pipeline (lint, type check, test, Docker)
container/           Dockerfile and docker-compose.yaml
```

## Design Intent

The project is intentionally implementation-ready and extensible. Replace in-memory/local components with enterprise services as you scale:

- AWS DMS, Debezium, or application CDC from Aurora MySQL into Kafka/MSK for real-time topics
- AWS Managed Service for Apache Flink or Databricks Structured Streaming for KPI computation
- Delta Lake for bronze/silver/gold KPI tables
- Databricks Vector Search, OpenSearch, Azure AI Search, or pgvector for vector retrieval
- Redis or DynamoDB for persistent session memory (swap `PersistentSessionMemory` backend)
- Teams/Jira/ServiceNow for alert and incident workflow integration
- Prometheus/Grafana for production metrics (connect to `/metrics` endpoint)
