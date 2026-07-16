# Agentic Operational Intelligence Platform

AI operations platform for store managers and executives — real-time KPI monitoring, root-cause diagnosis, and commercial strategy recommendations powered by an agentic AI layer over a streaming Iceberg lakehouse.

## Pipeline architecture

The platform is composed of eight sequential, independently deployable pipeline stages:

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
│ Topics: retail_ops.aurora.retail_ops.<table>                               │
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
└─────────────────────────────────────────────────────────────────────────────┘
```

## Documentation

| Doc | Contents |
|-----|----------|
| [Data Platform Architecture](docs/architecture_data_platform.md) | 8-stage pipeline · Kafka · Flink · MySQL ODS · Debezium · Spark · dbt Iceberg lakehouse · analytics/ML |
| [AI Systems Architecture](docs/architecture_ai_systems.md) | Agents · LLM · RAG · orchestration · skills · guardrails · ADRs |
| [Observability Architecture](docs/architecture_observability.md) | Metrics catalog · LLM evaluation · distributed tracing |
| [Local Development Architecture](docs/architecture_local.md) | Docker Compose services · startup sequence · resource limits · endpoints |
| [Kubernetes / Production Architecture](docs/architecture_amazon_eks.md) | EKS layout · AWS managed services · HPA · secrets · production replacements |
| [System Overview](docs/system_overview.md) | 8-stage table · reference flowcharts · agent orchestration · implementation reference |
| [KPI Definitions](docs/kpi_definitions.md) | 16 business KPIs with units, direction, and alert thresholds |
| [Copilot UI](docs/copilot_ui.md) | Front-end integration guide · API priority order · auth |
| [CI/CD Automation](docs/cicd_automation.md) | GitHub Actions pipeline · branch strategy · deployment · coverage gate |
| [Runbook](docs/runbook.md) | Setup · make targets · per-stage commands · API reference · troubleshooting |
| [ADRs](docs/adr/README.md) | 22 architecture decision records across data platform, AI systems, and infrastructure |

## Quick start

```bash
make install        # create .venv and install all dependency groups
make env            # create .env — add ANTHROPIC_API_KEY
make up             # start all infrastructure services
make produce        # start synthetic Kafka producer (15 canonical topics)
make test           # run test suite
```

## Repo layout

```text
ai_systems/
  agents/            KPI, anomaly, promotion, recommendation agents
  orchestration/     DAG engine, intent router, executor with retry/fallback
  skills/            Skill ABC, built-in skill catalog, singleton registry
  rag/               ChromaDB + TF-IDF hybrid search retriever
  memory/            Persistent SQLite-backed session memory
  context.py         Hybrid context assembler (streaming + vector + memory)
  experimentation.py A/B prompt experimentation with significance testing
  guardrails.py      Prompt injection detection, PII scrubbing, output validation
  llm.py             Anthropic Claude client (sync/async/stream/vision/tools)
  model_router.py    Multi-model routing (Haiku/Sonnet/Opus) with fallback
  prompts.py         Versioned prompt registry with lifecycle management
  structured_output.py  Pydantic-validated LLM response models
  tool_calling.py    Agentic tool-calling loop
config/              Runtime settings (Aurora MySQL, CDC, LLM, Redis)
ai_systems/gateway/
  api/               FastAPI (routes: query, kpi, alerts, operations, skills, streaming, health)
  mcp/server.py      MCP server entrypoint
  scheduler/         Daily summary job
data_platform/
  kpi_catalog.yaml   Machine-readable KPI definitions (16 KPIs)
  kpi_store.py       SQLite-backed KPI data store
  semantic_layer.py  Typed KPI records with anomaly detection
  schema/            Avro schemas for 5 canonical topic domains
  ddl/               MySQL DDL init scripts (retail_ops)
  producer/          Synthetic Avro message producer (15 topics)
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
  flink_job/         14 PyFlink jobs (canonical → PDM sink topics)
    start_flink_job.sh        submit one pipeline
    start_flink_job_all.py    submit all 14
alerts/              Alert engine, threshold config, MS Teams dispatch
observability/       Metrics, LLM evaluator, agent performance tracker
tests/               Unit tests (agents, orchestration, API, data, AI gaps)
docs/                Runbook + 12 ADRs + architecture diagram
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
make up                               # start all services (Kafka, MySQL, Redis, app, Conduktor…)
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

### Analytics layer

```bash
make analytics-up                     # start Qdrant + Feast feature server
make analytics-materialize            # push analytics features to Redis
make analytics-index                  # build Qdrant vector indexes from gold
```

### Local API development

```bash
make dev                              # FastAPI hot-reload on port 8000
make test && make lint && make typecheck
```

## Service endpoints

| Service | URL | Credentials |
|---------|-----|-------------|
| Platform API | http://localhost:8000 | `X-API-Key` header |
| Conduktor | http://localhost:8086 | admin@conduktor.io / admin |
| Schema Registry | http://localhost:8081 | — |
| Flink Dashboard | http://localhost:8082 | — |
| Kafka Connect | http://localhost:8083 | — |
| Airflow UI | http://localhost:8085 | admin / admin |
| Spark Master | http://localhost:4040 | — |
| Iceberg REST | http://localhost:8181 | — |
| MinIO Console | http://localhost:9001 | minioadmin / minioadmin |
| Qdrant | http://localhost:6333/dashboard | — |
| Feast Server | http://localhost:6566 | — |

## Data conventions

| Concept | Convention |
|---------|------------|
| CDC Kafka topic | `retail_ops.aurora.retail_ops.<table>` |
| Iceberg landing | `iceberg.landing.<table>` (Spark-managed, append-only) |
| Iceberg bronze | `iceberg.bronze.<table>` (CDC flattened, append) |
| Iceberg silver | `iceberg.silver.<table>` (current state, merge + delete) |
| Iceberg gold | `iceberg.gold.gold_store_kpis` (daily KPI aggregation) |
| Iceberg analytics | `iceberg.analytics.feat_*` (ML feature tables) |
| Feast online | Redis DB 1 (feature key: `store_id` or `customer_id`) |
| Qdrant collections | `store_kpi_narratives`, `metric_definitions` |

## Design intent

Built around an open-source, locally-runnable data lakehouse — swap components for cloud-managed equivalents as you scale:

| Local (this repo) | Production equivalent |
|---|---|
| Kafka (KRaft, 3 brokers) | AWS MSK / Confluent Cloud |
| Flink standalone cluster | AWS Managed Flink / Databricks |
| Spark + MinIO (Iceberg) | AWS EMR + S3 + Glue Catalog |
| dbt-spark (Thrift Server) | Databricks SQL / dbt Cloud |
| Airflow (LocalExecutor) | MWAA / Astronomer |
| Redis (online features) | DynamoDB / AWS ElastiCache |
| Qdrant (vector search) | OpenSearch / Pinecone |
| Feast (feature store) | AWS SageMaker Feature Store |
| ChromaDB (RAG) | AWS OpenSearch / pgvector |
