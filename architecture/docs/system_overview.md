# System Overview

Target status: `agentic-operational-intelligence-platform`

This platform combines real-time operational KPI streams, alert detection, Hybrid RAG, and specialized agents to help store managers and executives monitor retail operations and improve promotion strategies.

Key architectural layers:

- **Agent Orchestration** — DAG-based execution with intent routing, multi-turn conversation, retry/fallback, and parallel tier processing
- **Agent Skills** — composable capabilities with LLM tool-calling export, agentic query loop, and per-skill observability
- **LLM Layer** — Anthropic Claude client with sync, async, streaming, vision, and tool-calling modes; multi-model routing (Haiku/Sonnet/Opus)
- **Hybrid Context** — unified assembly of streaming state, ChromaDB vector retrieval, and conversational memory
- **Guardrails** — prompt injection detection, PII scrubbing, output quality enforcement
- **Structured Output** — Pydantic-validated LLM response models for KPI insights, briefs, diagnoses, and recommendations
- **Observability** — metrics collection, LLM-as-judge evaluation, Prometheus `/metrics` export, and agent performance tracking
- **LLMOps** — versioned prompt registry with lifecycle management, A/B variant experimentation with statistical significance testing
- **Security** — API key authentication, RBAC (admin/operator/viewer), per-key rate limiting
- **MCP Server** — Model Context Protocol server exposing platform tools, resources, and prompts
- **Persistent Memory** — SQLite-backed session memory with TTL and cross-session knowledge accumulation

## Operational source systems

- AWS Aurora MySQL is the system of record for the sales order system.
- AWS Aurora MySQL is the system of record for the appointment application.
- AWS Aurora MySQL is the system of record for POS invoice activities.
- AWS Aurora MySQL is the system of record for work order activities.
- Inventory signals can be joined from Aurora MySQL tables or adjacent inventory services before KPI aggregation.

The preferred production pattern is CDC from Aurora MySQL into the real-time event pipeline, followed by streaming KPI aggregation and alerting.

## Reference architecture

```mermaid
flowchart LR
    A[AWS Aurora MySQL\nSales Orders\nAppointments\nPOS Invoices\nWork Orders] --> B[CDC Layer\nAWS DMS or Debezium]
    B --> C[Kafka or Amazon MSK Topics]
    C --> D[Flink or Databricks Streaming\nNormalization and KPI Aggregation]
    D --> E[Delta Lake Bronze Tables]
    E --> F[Delta Lake Silver Tables]
    F --> G[Delta Lake Gold KPI Tables]
    G --> H[Alert Detection and Dispatch]
    G --> I[Agentic Orchestrator]
    I --> J[Store Manager Briefs]
    I --> K[Executive Briefs]
```

## Agent orchestration architecture

```mermaid
flowchart TD
    Q[User Query] --> GR[Guardrails\nInjection Detection + PII Scrub]
    GR --> R[Intent Router]
    R --> DAG[DAG Builder]
    DAG --> CTX[Phase 0: Hybrid Context Assembly\nStreaming + Vector + Memory]
    CTX --> T0["Tier 0: KPI Agent | RAG Search"]
    T0 --> T1["Tier 1: Anomaly Agent"]
    T1 --> T2["Tier 2: Promotion Agent"]
    T2 --> T3["Tier 3: Recommendation Agent"]
    T3 --> RESP[Response Assembly + Execution Trace]
    RESP --> MEM[Session Memory Recording]

    subgraph Executor
        CTX
        T0
        T1
        T2
        T3
    end

    subgraph Cross-cutting
        RETRY[Retry + Fallback]
        OBS[Observability Tracker]
        SKILLS[Skill Registry]
        ROUTER[Model Router\nHaiku / Sonnet / Opus]
    end

    Executor --> RETRY
    Executor --> OBS
    Executor --> SKILLS
    Executor --> ROUTER
```

## LLM interaction modes

```mermaid
flowchart LR
    subgraph "ai_layer/llm.py"
        GEN[generate\nSync + Cache]
        TOOLS[generate_with_tools\nMulti-turn Tool Loop]
        STREAM[generate_stream\nSSE Async Generator]
        ASYNC[generate_async\nNon-blocking]
        VISION[generate_with_image\nMultimodal Vision]
    end

    subgraph "Model Router"
        HAIKU[Haiku\nClassification]
        SONNET[Sonnet\nGeneration]
        OPUS[Opus\nReasoning]
    end

    GEN --> SONNET
    TOOLS --> SONNET
    STREAM --> SONNET
    VISION --> SONNET
    HAIKU -.->|fallback| SONNET
    SONNET -.->|fallback| HAIKU
    OPUS -.->|fallback| SONNET
```

Reference implementation assets:

- Application settings: `config/settings.py`
- LLM client abstraction: `ai_layer/llm.py`
- Model router: `ai_layer/model_router.py`
- Guardrails: `ai_layer/guardrails.py`
- Structured output: `ai_layer/structured_output.py`
- Tool-calling loop: `ai_layer/tool_calling.py`
- Agent orchestration DAG: `ai_layer/orchestration/dag.py`
- Intent router: `ai_layer/orchestration/router.py`
- DAG executor with retry/fallback: `ai_layer/orchestration/executor.py`
- Skill registry and catalog: `ai_layer/skills/`
- Hybrid context assembler: `ai_layer/context.py`
- Persistent session memory: `ai_layer/memory/persistent_memory.py`
- A/B experimentation: `ai_layer/experimentation.py`
- Versioned prompt registry: `ai_layer/prompts.py`
- Observability and evaluation: `observability/evaluation.py`
- Auth and RBAC: `services/api/auth.py`
- MCP server: `services/mcp_server.py`
- Semantic KPI layer: `data_platform/semantic_layer.py`
- KPI data store: `data_platform/kpi_store.py`
- KPI catalog: `data_platform/kpi_catalog.yaml`
- Bronze landing tables: `data_platform/batch/databricks/bronze/README.md`
- Silver normalized tables: `data_platform/batch/databricks/silver/README.md`
- Bronze-to-silver notebook: `data_platform/batch/databricks/notebooks/bronze_to_silver_aurora_domains.ipynb`
- Sample AWS DMS to MSK task spec: `config/cdc/aws_dms_aurora_to_msk_task.example.json`
- Gold KPI tables: `data_platform/batch/databricks/gold/kpi_tables.sql`
- CI/CD pipeline: `.github/workflows/ci.yml`

## CDC naming conventions

- Kafka or MSK topic pattern: `retail_ops.aurora.<schema>.<table>`
- Bronze landing table pattern: `bronze.<table>_cdc`
- Silver normalized table pattern: `silver.<table>`
- Gold KPI table pattern: `gold.<business_subject>`

## Core domains

- Sales order activity
- Appointment activity
- POS invoice activity
- Inventory activity
- Work order activity
- Promotions and campaigns

## Primary user experiences

- Store Manager Copilot: localized operational diagnosis and immediate action recommendations
- Executive Copilot: regional and enterprise-level KPI rollups, promotion performance, and strategic recommendations

## Strategy adjustment workflows

- Under-performing store diagnosis: combines sales, conversion, inventory, and work-order stress signals.
- Branded upsell optimization: tracks branded revenue mix and suggests store coaching plus offer bundling.
- Promotion readiness alignment: checks inventory in-stock rate and service backlog before increasing demand.

## API surface

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/ask` | POST | Agentic Q&A with guardrails, intent routing, and DAG execution |
| `/ask/stream` | POST | SSE streaming Q&A with real-time token delivery |
| `/ask/async` | POST | Async non-blocking generation |
| `/ask/agentic` | POST | Tool-calling agentic queries |
| `/kpi` | POST | Fetch KPI metrics for a store or region |
| `/kpi/enriched` | POST | KPIs with semantic metadata and anomaly flags |
| `/kpi/catalog` | GET | Machine-readable KPI catalog |
| `/alerts/{store_id}` | GET | Retrieve active alerts for a store |
| `/operations/brief` | POST | Persona-aware operational brief |
| `/skills` | GET | List all registered agent skills with tool schemas |
| `/skills/{name}/invoke` | POST | Invoke a specific skill by name |
| `/usage` | GET | LLM token usage and cost tracking |
| `/metrics` | GET | Prometheus exposition format metrics |
| `/health` | GET | Health check |
