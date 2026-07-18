# Agentic Operational Intelligence Platform

AI operations platform for store managers and executives — real-time KPI monitoring, root-cause diagnosis, and commercial strategy recommendations powered by an agentic AI layer over a streaming Iceberg lakehouse.

## Pipeline architecture

The platform is composed of nine sequential, independently deployable pipeline stages:

At the ingestion boundary, the platform represents an enterprise integration layer that unifies source domains (ERP, CRM, workforce, vehicle inspection, MDM, and reference systems) into canonical topics across real-time, near real-time, and batch cadences. In this project, synthetic data generation is used to mirror those sourcing systems and preserve production-like canonical flows.

```
┌─────────────────────────────────────────────────────────────────────────────┐
│ Stage 1 · Ingestion                                                         │
│ Synthetic / real source-system events → 15 canonical Avro Kafka topics      │
│ data_platform/producer/   data_platform/schema/                             │
└───────────────────────────────────┬─────────────────────────────────────────┘
                                    │ CanonicalSalesforceCrm*, CanonicalSap*
                                    │ CanonicalTrendwell*, CanonicalKronos*
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│ Stage 2 · Flink Stream Processing                                           │
│ 14 PyFlink Table API jobs transform canonical topics → PDM Sink* topics     │
│ data_platform/flink_job/   Flink cluster (jobmanager + taskmanager :8082)   │
└───────────────────────────────────┬─────────────────────────────────────────┘
                                    │ SinkSalesOrder*, SinkAppointment*
                                    │ SinkWorkOrder*, SinkInventory*, …
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│ Stage 3 · Kafka Connect JDBC Sink → MySQL ODS                               │
│ JDBC Sink connectors write PDM Sink* topics → MySQL retail_ops tables        │
│ container/scripts/register_connectors.py   MySQL :3306                      │
└──────────────┬────────────────────────────────────────────────────────────┬─┘
               │ MySQL ODS                                                  │
               ▼                                                            │
┌──────────────────────────────────────────┐         Stage 5                │
│ Stage 4 · AI Systems (real-time path)    │                                 │
│ FastAPI + AI agents consume MySQL ODS    │                                 │
│ KPI queries, anomaly detection, briefs   │                                 │
│ ai_systems/gateway/api/   ai_systems/   :8000                               │
└──────────────────────────────────────────┘                                 │
                                                                              │
┌─────────────────────────────────────────────────────────────────────────────┤
│ Stage 5 · Debezium CDC → Kafka                                             │
│ Debezium connector captures MySQL ODS changes → CDC Kafka topics           │
│ container/scripts/register_cdc_connector.py                                │
│ Topics: cdc_<table>                                                         │
└───────────────────────────────────┬─────────────────────────────────────────┘
                                    │ CDC envelope: before/after/op/ts_ms
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│ Stage 6 · Spark Structured Streaming → MinIO Landing (Iceberg)             │
│ CDC topics → iceberg.landing.* (append-only, full Debezium envelope)       │
│ data_platform/spark/cdc_to_landing.py   MinIO :9000                        │
└───────────────────────────────────┬─────────────────────────────────────────┘
                                    │ iceberg.landing.*
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│ Stage 7 · dbt Lakehouse Transformations                                     │
│ landing → bronze (CDC flatten) → silver (MERGE/DELETE) → gold (KPIs)      │
│ data_platform/dbt/   Airflow :8085 schedules every 30 min                  │
└───────────────────────────────────┬─────────────────────────────────────────┘
                                    │ iceberg.gold.gold_store_kpis
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│ Stage 8 · Analytics / ML / LLM on Lakehouse                                │
│ ├─ analytics layer  feat_store_performance, feat_customer_behavior (dbt)   │
│ ├─ Feature Store    Feast offline: Iceberg  online: Redis :6566             │
│ ├─ Semantic Layer   dbt MetricFlow — 9 named metrics                       │
│ └─ Vector Index     Qdrant store_kpi_narratives + metric_definitions :6333  │
│ data_platform/feature_store/   data_platform/vector_index/                 │
└───────────────────────────────────┬─────────────────────────────────────────┘
                                    │ ODS + iceberg.gold.gold_store_kpis
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│ Stage 9 · Graph Projection (Neo4j)                                         │
│ ├─ ODS relationships: article-store, employee-store, customer-store         │
│ ├─ Gold projection: Store -> HAS_KPI_SNAPSHOT -> StoreKPI                   │
│ └─ Validation: make graph-check                                              │
│ data_platform/graph/   Neo4j :7474/:7687                                    │
└─────────────────────────────────────────────────────────────────────────────┘
```

## Documentation

| Doc                                                                      | Contents                                                                                               |
| ------------------------------------------------------------------------ | ------------------------------------------------------------------------------------------------------ |
| [Data Platform Architecture](docs/architecture-data-platform.md)         | 8-stage data pipeline subset of the 9-stage platform · Kafka · Flink · MySQL ODS · Debezium · Spark · dbt · analytics/ML · Neo4j graph |
| [AI Systems Architecture](docs/architecture-ai-systems.md)               | Agents · LLM · RAG · orchestration · skills · guardrails · ADRs                                        |
| [Observability Architecture](docs/architecture-observability.md)         | Metrics catalog · LLM evaluation · distributed tracing                                                 |
| [Local Development Architecture](docs/architecture-local.md)             | Docker Compose services · startup sequence · resource limits · endpoints                               |
| [Kubernetes / Production Architecture](docs/architecture-amazon-eks.md)  | EKS layout · AWS managed services · HPA · secrets · production replacements                            |
| [System Overview](docs/system-overview.md)                               | 9-stage table · reference flowcharts · agent orchestration · implementation reference                  |
| [Frameworks and Design Patterns](docs/frameworks-and-design-patterns.md) | Technology stack by layer + concrete code-level pattern mapping                                        |
| [KPI Definitions](docs/kpi-definitions.md)                               | 16 business KPIs with units, direction, and alert thresholds                                           |
| [Copilot UI](docs/copilot-ui.md)                                         | Front-end integration guide · API priority order · auth                                                |
| [CI/CD Automation](docs/cicd-automation.md)                              | GitHub Actions pipeline · branch strategy · deployment · coverage gate                                 |
| [Runbook](docs/runbook.md)                                               | Setup · make targets · per-stage commands · API reference · troubleshooting                            |
| [ADRs](docs/adr/README.md)                                               | 24 architecture decision records across data platform, AI systems, and infrastructure                  |

## Quick start

```bash
make install        # create .venv and install all dependency groups
make env            # create .env
# local Ollama: AOIP_LLM__PROVIDER=ollama, AOIP_LLM__MODEL=llama3.1:8b
# production Anthropic: AOIP_LLM__PROVIDER=anthropic, ANTHROPIC_API_KEY=...
make up             # start core services only (app, redis, mysql, kafka, connect)
make up-full        # start full stack (lakehouse + airflow + analytics + flink)
make produce        # start synthetic Kafka producer (15 canonical topics)
make graph-sync      # sync article/store, employee/store, customer/store to Neo4j
make test           # run test suite
```

## LLM provider profiles

### Local development (Ollama)

```bash
AOIP_LLM__PROVIDER=ollama
AOIP_LLM__MODEL=llama3.2:latest
AOIP_LLM__OLLAMA_BASE_URL=http://localhost:11434
AOIP_LLM__OLLAMA_TIMEOUT_SECONDS=120
```

Start/check Ollama:

```bash
ollama serve
curl --noproxy '*' http://localhost:11434/api/tags
```

### Production (Anthropic)

```bash
AOIP_LLM__PROVIDER=anthropic
AOIP_LLM__MODEL=claude-sonnet-4-20250514
ANTHROPIC_API_KEY=<secret>
```

Notes:

- Ollama supports sync, async, and streaming generation in this project.
- Tool-calling falls back to plain generation when provider is Ollama.
- Image generation is Anthropic-only in the current implementation.

## Repo layout

```text
ai_systems/
  agents/            KPI, anomaly, promotion, recommendation agents
  alerting/          Alert engine, channels, and KPI threshold rules
  config/            Runtime settings (Aurora MySQL, CDC, LLM, Redis)
  core/              LLM client, guardrails, model router, prompt registry, typed outputs
  experimentation/   A/B prompt experimentation manager
  gateway/
    api/             FastAPI (routes: query, kpi, alerts, operations, skills, streaming, health)
    mcp/server.py    MCP server entrypoint
    scheduler/       Daily summary job
  orchestration/     DAG engine, intent router, executor with retry/fallback
  retrieval/         Hybrid context assembler, semantic search, session memory
  skills.py          Skill ABC and shared skill contracts
  tools/             Alert/KPI tools, registry, and tool-calling helpers
data_platform/
  kpi_catalog.yaml   Machine-readable KPI definitions (16 KPIs)
  kpi_store.py       SQLite-backed KPI data store
  semantic_layer.py  Typed KPI records with anomaly detection
  schema/            Avro schemas for 5 canonical topic domains
  ddl/               MySQL DDL init scripts (retail_ops)
  producer/          Synthetic Avro message producer (15 topics)
    mdm/             Master-data batch runner (Airflow-triggered)
    transaction/     Transaction real-time runner (FK preflight)
    topics/
      mdm/           Master topic generators
      transaction/   Transaction topic generators
  spark/             PySpark Structured Streaming — CDC → MinIO landing (Iceberg)
  dbt/               dbt Core project — staging → bronze → silver → gold → analytics
    models/
      staging/       Views over iceberg.landing (source declarations)
      bronze/        CDC envelope flattening, append-only
      silver/        CDC merge, current-state tables
      gold/          KPI aggregations (gold_store_kpis)
      analytics/     Feature engineering (rolling windows, RFM, churn risk)
      semantic/      MetricFlow semantic models + 9 named metrics
    macros/          generate_schema_name, delete_cdc_rows
  feature_store/     Feast — offline: Iceberg analytics; online: Redis
  vector_index/      Qdrant indexer — store_kpi_narratives, metric_definitions
  graph/             Neo4j relationship sync (article-store, employee-store, customer-store)
  flink_job/         14 PyFlink jobs (canonical → PDM sink topics)
    start_flink_job.sh        submit one pipeline
    start_flink_job_all.py    submit all 14
observability/       Metrics, LLM evaluator, agent performance tracker
tests/               Unit tests (agents, orchestration, API, data, AI gaps)
docs/                Runbook + 22 ADRs + architecture references
Makefile             All dev workflows — run `make help`
container/
  docker-compose.yaml  Full local stack (~30 services)
  Dockerfile           Platform API image
  flink/Dockerfile     Flink cluster image (PyFlink + Iceberg connector JAR)
  flink/pom.xml        Maven build for the Kafka + Avro fat JAR
  airflow/Dockerfile   Airflow image (dbt-spark pre-installed)
  airflow/dags/        dbt_pipeline.py — schedules bronze→silver→gold→analytics
```

## Local stack

All dev workflows go through `make`. Run `make help` for the full reference.

### Infrastructure

```bash
make up                               # start core services
make up-full                          # start full stack
make produce                          # start synthetic Avro producer (15 canonical topics)
make down                             # stop all containers
```

### Flink cluster

```bash
make flink-jar                        # build Kafka + Avro connector fat JAR (Maven)
make flink-up                         # start JobManager + TaskManager
make flink-run JOB=appointment        # submit one pipeline
make flink-submit                     # submit all 14 pipelines
```

### Iceberg lakehouse

```bash
make lake-up                          # MinIO + Iceberg REST + Spark cluster + Thrift Server
make lake-stream                      # CDC → landing Spark streaming job
make dbt-deps && make dbt-run         # install packages then run full dbt DAG
make dbt-run LAYER=analytics          # run single layer
```

### Airflow

```bash
make airflow-up                       # build + start (webserver + scheduler)
make airflow-trigger                  # fire dbt_lakehouse_pipeline manually
```

`mdm_daily_processing` runs once daily and is the only supported scheduler for
`data_platform.producer.mdm.master_batch`.

`data_platform.producer.transaction.realtime` performs a startup preflight that:

- Loads canonical IDs already produced by MDM topics.
- Rebinds transaction FK pools to those canonical IDs.
- Validates sampled transaction records for FK existence.
- Enforces customer-store consistency (`customerIdentifier` must match `siteNumber`).

### Analytics layer

```bash
make analytics-up                     # start Qdrant + Feast feature server
make analytics-materialize            # apply Feast + materialize features to Redis (prebuilt runtime)
make analytics-index                  # build Qdrant vector indexes from gold
```

### Graph relationships (Neo4j)

```bash
make graph-up                         # start Neo4j
make graph-sync                       # sync ODS relationships + gold KPI snapshots to Neo4j
make graph-check                      # print Cypher counts by relationship type
make graph-down                       # stop Neo4j
```

Notes:

- `analytics-materialize` now uses the prebuilt `feast-server` image (Java + pinned Spark runtime baked in) and no longer installs apt/pip dependencies at runtime.
- `vector-indexer` resolves KPI sources in order from `KPI_SOURCE_TABLES` (default: `warehouse.gold_store_kpis,iceberg.gold.gold_store_kpis`) and falls back to deterministic sample rows only when `KPI_FALLBACK_MODE=sample`.

### Local API development

```bash
make dev                              # FastAPI hot-reload on port 8000
make test && make lint && make typecheck
```

## Service endpoints

| Service         | URL                             | Credentials                |
| --------------- | ------------------------------- | -------------------------- |
| Platform API    | http://localhost:8000           | `X-API-Key` header         |
| Conduktor       | http://localhost:8086           | admin@conduktor.io / admin |
| Schema Registry | http://localhost:8081           | —                          |
| Flink Dashboard | http://localhost:8082           | —                          |
| Kafka Connect   | http://localhost:8083           | —                          |
| Airflow UI      | http://localhost:8085           | admin / admin              |
| Spark Master    | http://localhost:4040           | —                          |
| Iceberg REST    | http://localhost:8181           | —                          |
| MinIO Console   | http://localhost:9001           | minioadmin / minioadmin    |
| Qdrant          | http://localhost:6333/dashboard | —                          |
| Feast Server    | http://localhost:6566           | —                          |
| Neo4j Browser   | http://localhost:7474           | neo4j / neo4j              |

## Data conventions

| Concept            | Convention                                               |
| ------------------ | -------------------------------------------------------- |
| CDC Kafka topic    | `cdc_<table>`                                            |
| Iceberg landing    | `iceberg.landing.<table>` (Spark-managed, append-only)   |
| Iceberg bronze     | `iceberg.bronze.<table>` (CDC flattened, append)         |
| Iceberg silver     | `iceberg.silver.<table>` (current state, merge + delete) |
| Iceberg gold       | `iceberg.gold.gold_store_kpis` (daily KPI aggregation)   |
| Iceberg analytics  | `iceberg.analytics.feat_*` (ML feature tables)           |
| Feast online       | Redis DB 1 (feature key: `store_id` or `customer_id`)    |
| Qdrant collections | `store_kpi_narratives`, `metric_definitions`             |

## Design intent

Built around an open-source, locally-runnable data lakehouse — swap components for cloud-managed equivalents as you scale:

| Local (this repo)         | Production equivalent          |
| ------------------------- | ------------------------------ |
| Kafka (KRaft, 3 brokers)  | AWS MSK / Confluent Cloud      |
| Flink standalone cluster  | AWS Managed Flink / Databricks |
| Spark + MinIO (Iceberg)   | AWS EMR + S3 + Glue Catalog    |
| dbt-spark (Thrift Server) | Databricks SQL / dbt Cloud     |
| Airflow (LocalExecutor)   | MWAA / Astronomer              |
| Redis (online features)   | DynamoDB / AWS ElastiCache     |
| Qdrant (vector search)    | OpenSearch / Pinecone          |
| Feast (feature store)     | AWS SageMaker Feature Store    |
| ChromaDB (RAG)            | AWS OpenSearch / pgvector      |

## Terminology Glossary

Use canonical definitions from [Terminology Glossary](docs/terminology-glossary.md) when describing platform components, data layers, and AI workflows.

## Structural Formatting Standard

This document follows the shared [Markdown Structure Standard](docs/markdown-structure-standard.md) for heading hierarchy, section order, procedure formatting, and link conventions.
