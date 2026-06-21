# System Overview

Target status: `agentic-operational-intelligence-platform`

This platform combines real-time operational KPI streams, alert detection, Hybrid RAG, and specialized agents to help store managers and executives monitor retail operations and improve promotion strategies.

Key architectural layers:

- **Agent Orchestration** — DAG-based execution with intent routing, retry/fallback, and parallel tier processing
- **Agent Skills** — composable capabilities with LLM tool-calling export and per-skill observability
- **Hybrid Context** — unified assembly of streaming state, vector retrieval, and conversational memory
- **Observability** — metrics collection, LLM output evaluation, and agent performance tracking
- **LLMOps** — versioned prompt registry with lifecycle management and A/B variant support

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
    Q[User Query] --> R[Intent Router]
    R --> DAG[DAG Builder]
    DAG --> T0["Tier 0: KPI Agent | RAG Search"]
    T0 --> T1["Tier 1: Anomaly Agent"]
    T1 --> T2["Tier 2: Promotion Agent"]
    T2 --> T3["Tier 3: Recommendation Agent"]
    T3 --> RESP[Response Assembly + Execution Trace]

    subgraph Executor
        T0
        T1
        T2
        T3
    end

    subgraph Cross-cutting
        RETRY[Retry + Fallback]
        OBS[Observability Tracker]
        SKILLS[Skill Registry]
    end

    Executor --> RETRY
    Executor --> OBS
    Executor --> SKILLS
```

Reference implementation assets:

- Application settings: `config/settings.py`
- Bronze landing tables: `data_platform/batch/databricks/bronze/README.md`
- Silver normalized tables: `data_platform/batch/databricks/silver/README.md`
- Bronze-to-silver notebook: `data_platform/batch/databricks/notebooks/bronze_to_silver_aurora_domains.ipynb`
- Sample AWS DMS to MSK task spec: `config/cdc/aws_dms_aurora_to_msk_task.example.json`
- Gold KPI tables: `data_platform/batch/databricks/gold/kpi_tables.sql`
- Agent orchestration DAG: `ai_layer/orchestration/dag.py`
- Intent router: `ai_layer/orchestration/router.py`
- DAG executor with retry/fallback: `ai_layer/orchestration/executor.py`
- Skill registry and catalog: `ai_layer/skills/`
- Hybrid context assembler: `ai_layer/context.py`
- Versioned prompt registry: `ai_layer/prompts.py`
- Observability and evaluation: `observability/evaluation.py`

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
| `/ask` | POST | Agentic Q&A with intent routing and DAG execution |
| `/kpi` | POST | Fetch KPI metrics for a store or region |
| `/alerts/{store_id}` | GET | Retrieve active alerts for a store |
| `/operations/brief` | POST | Persona-aware operational brief |
| `/skills` | GET | List all registered agent skills with tool schemas |
| `/skills/{name}/invoke` | POST | Invoke a specific skill by name |
| `/health` | GET | Health check |

## API surface

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/ask` | POST | Agentic Q&A with intent routing and DAG execution |
| `/kpi` | POST | Fetch KPI metrics for a store or region |
| `/alerts/{store_id}` | GET | Retrieve active alerts for a store |
| `/operations/brief` | POST | Persona-aware operational brief |
| `/skills` | GET | List all registered agent skills with tool schemas |
| `/skills/{name}/invoke` | POST | Invoke a specific skill by name |
| `/health` | GET | Health check |
