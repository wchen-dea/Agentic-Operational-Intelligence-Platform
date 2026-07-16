# Runbook

## Prerequisites

- Python 3.12+
- [uv](https://docs.astral.sh/uv/) installed
- Docker Desktop (≥ 8 GB RAM allocated recommended)
- Maven 3.x (`brew install maven`) — for building the Flink connector JAR
- [Ollama](https://ollama.com/) installed (local LLM development only)
- LLM provider configuration in `.env`:
  - Local dev (Ollama): `AOIP_LLM__PROVIDER=ollama`
  - Production (Anthropic): `AOIP_LLM__PROVIDER=anthropic` and `ANTHROPIC_API_KEY=...`

## First-time setup

```bash
make install        # create .venv and install all dependency groups
make env            # create .env
make flink-jar      # build the Kafka + Avro fat JAR (Maven, ~40 MB, one-time)
```

Example `.env` snippets:

```bash
# Local development (Ollama)
AOIP_LLM__PROVIDER=ollama
AOIP_LLM__MODEL=llama3.1:8b
AOIP_LLM__OLLAMA_BASE_URL=http://localhost:11434
AOIP_LLM__OLLAMA_TIMEOUT_SECONDS=120

# Production (Anthropic)
AOIP_LLM__PROVIDER=anthropic
ANTHROPIC_API_KEY=your-key
AOIP_LLM__MODEL=claude-sonnet-4-20250514
```

## LLM provider profiles

### Local development profile (Ollama)

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

### Production profile (Anthropic)

```bash
AOIP_LLM__PROVIDER=anthropic
AOIP_LLM__MODEL=claude-sonnet-4-20250514
ANTHROPIC_API_KEY=<secret>
```

Notes:

- Ollama supports sync, async, and streaming generation in this project.
- Tool-calling falls back to plain generation when provider is Ollama.
- Image generation is Anthropic-only in the current implementation.

## Start the full platform

```bash
make up             # start all infrastructure (Kafka, MySQL, Redis, Conduktor, app, etc.)
make produce        # start synthetic Avro message producer (15 canonical topics)
```

## Pipeline stage reference

The platform has eight ordered stages. Each can be started and debugged independently.

### Stage 1 — Ingestion (source events → canonical Avro topics)

```bash
make produce                                # all 15 topics at 0.5 s interval
PRODUCE_INTERVAL=2 make produce             # slower rate
make topics                                 # verify topics exist
# Conduktor: http://localhost:8086  Schema Registry: http://localhost:8081
```

Topics produced: `CanonicalSalesforceCrmAppointment`, `CanonicalSapSalesorderDetail`, `CanonicalTrendwellVehivleInspection`, `CanonicalKronosCrewtime`, `CanonicalWarehouseInventorySnapshot`, and 10 more.

### Stage 2 — Flink (canonical → PDM Sink topics)

```bash
make flink-jar                              # build connector fat JAR (Maven, once)
make flink-up                               # start JobManager + TaskManager :8082
make flink-run JOB=appointment              # submit one pipeline
make flink-submit                           # submit all 14 pipelines
make flink-jobs && make flink-cancel JOB_ID=<id>
```

Sink topics: `SinkAppointment`, `SinkSalesOrder`, `SinkWorkOrder`, `SinkArticleInventory`, and 40+ more.

### Stage 3 — Kafka Connect JDBC Sink (Sink topics → MySQL ODS)

```bash
make register-schemas                       # register Avro schemas
make register-connectors                    # JDBC Sink connectors → MySQL retail_ops tables
# Kafka Connect: http://localhost:8083  MySQL: localhost:3306
```

### Stage 4 — AI Systems (real-time from MySQL ODS)

```bash
make dev                                    # FastAPI :8000 with hot-reload
curl -X POST http://localhost:8000/kpi/enriched \
     -H "Content-Type: application/json" -d '{"store_id":"245"}'
curl -X POST http://localhost:8000/ask \
     -H "Content-Type: application/json" \
     -d '{"question":"Why are Phoenix sales down?","store_id":"245"}'
```

### Stage 5 — Debezium CDC (MySQL ODS → CDC Kafka topics)

```bash
make register-cdc                           # register Debezium source connector
# CDC topics: retail_ops.aurora.retail_ops.{sales_orders,appointments,
#             pos_invoices,work_orders,article_inventory}
```

### Stage 6 — Spark Streaming → MinIO Landing (Iceberg)

```bash
make lake-up                                # MinIO + Iceberg REST + Spark cluster
make lake-stream                            # start cdc_to_landing.py
# Landing tables: iceberg.landing.{sales_orders,appointments,…}
# MinIO: http://localhost:9001  Iceberg REST: http://localhost:8181
```

### Stage 7 — dbt Lakehouse (landing → bronze → silver → gold → analytics)

```bash
make dbt-deps && make dbt-run               # full pipeline
make dbt-run LAYER=bronze/silver/gold/analytics  # single layer
make dbt-test                               # data quality tests
make airflow-up                             # scheduler every 30 min
# Airflow: http://localhost:8085  (admin / admin)
```

### Stage 8 — Analytics / ML / LLM on Lakehouse

```bash
make analytics-up                           # Qdrant + Feast feature server
make analytics-materialize                  # push features to Redis
make analytics-index                        # build Qdrant vector indexes
# Qdrant: http://localhost:6333/dashboard  Feast: http://localhost:6566
```

## Service endpoints

| Service | URL | Credentials |
|---------|-----|-------------|
| Platform API | http://localhost:8000 | — |
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

## Flink cluster + canonical topic processing

```bash
make flink-up                       # start Flink JobManager + TaskManager
make flink-run JOB=appointment      # submit a single pipeline
make flink-submit                   # submit all 14 pipelines
make flink-jobs                     # list running Flink jobs (REST API)
make flink-cancel JOB_ID=<id>       # cancel a running job
make logs-flink-jm                  # tail JobManager logs
```

Available pipelines: `appointment article crewtime customer employee inventory kronos_hours sales_order sales_order_receipt site vehicle vehicle_inspection voucher work_order`

You can also submit a single pipeline directly:

```bash
data_platform/flink_job/start_flink_job.sh appointment
data_platform/flink_job/start_flink_job.sh --list   # show all available
```

## Iceberg lakehouse (Spark Streaming + dbt)

```bash
make lake-up            # start MinIO + Iceberg REST + Spark cluster + Spark Thrift Server
make lake-stream        # start CDC → landing Spark Structured Streaming job
make dbt-deps           # install dbt packages (first time)
make dbt-run            # run full dbt pipeline: staging → bronze → silver → gold
make dbt-run LAYER=silver           # run a single layer
make dbt-test           # run dbt data quality tests
```

## Airflow orchestration

```bash
make airflow-up         # build + init + start Airflow (webserver + scheduler)
make airflow-trigger    # manually trigger the dbt_lakehouse_pipeline DAG
make logs-airflow       # tail scheduler + webserver logs
make airflow-down       # stop Airflow
```

The `dbt_lakehouse_pipeline` DAG runs every 30 minutes:
`start → dbt deps → bronze (run + test) → silver (run + test) → gold (run + test) → analytics (run + test) → end`

## Analytics layer (Feature Store + Semantic Layer + Vector Index)

```bash
# Start Qdrant vector DB and Feast online feature server
make analytics-up

# Build analytics feature tables (requires dbt to have run gold first)
make dbt-run LAYER=analytics

# Register Feast feature views and materialize to Redis
make analytics-materialize

# Build Qdrant vector indexes (store KPI narratives + metric definitions)
make analytics-index

# Dry-run: preview index payloads without upserting to Qdrant
make analytics-index-dry

# Stop analytics services
make analytics-down
```

**Analytics components:**

| Component | Description |
|-----------|-------------|
| `feat_store_performance` | Per-store rolling 7d/28d revenue, WoW growth, show-rate delta, overdue rate, reorder pressure |
| `feat_customer_behavior` | Per-customer RFM (recency/frequency/monetary), appointment show rate, churn risk band |
| Semantic models | 9 named MetricFlow metrics: `revenue_total`, `appointment_show_rate`, `refund_rate`, etc. |
| `store_kpi_narratives` | Qdrant collection — KPI text narratives embedded for semantic search |
| `metric_definitions` | Qdrant collection — metric descriptions embedded for AI reasoning |

## Kafka / Schema management

```bash
make topics             # list all Kafka topics (non-internal)
make register-schemas   # register Avro schemas into Schema Registry
make register-connectors # register JDBC Sink connectors for all PDM tables
make register-cdc       # register the Debezium CDC connector
```

## Local development (API + AI layer)

```bash
make dev                # run FastAPI with hot-reload on port 8000
make mcp                # run the MCP server
make test               # run test suite
make test-cov           # tests with coverage report
make lint               # ruff lint check
make fmt                # ruff auto-format
make typecheck          # pyright type check
```

## Environment variables

| Variable | Required | Description |
|----------|----------|-------------|
| `AOIP_LLM__PROVIDER` | Yes | LLM backend selector: `ollama` (local) or `anthropic` (prod) |
| `AOIP_LLM__MODEL` | Yes | Model ID for selected provider |
| `ANTHROPIC_API_KEY` | Conditional | Required when `AOIP_LLM__PROVIDER=anthropic` |
| `AOIP_LLM__OLLAMA_BASE_URL` | Conditional | Required when `AOIP_LLM__PROVIDER=ollama` (default: `http://localhost:11434`) |
| `AOIP_LLM__OLLAMA_TIMEOUT_SECONDS` | No | Ollama HTTP timeout seconds (default: `120`) |
| `AOIP_AUTH_DISABLED` | No | `true` to skip API key auth in dev |
| `AOIP_API_KEY_ADMIN` | No | Register admin API key at startup |
| `AOIP_API_KEY_OPERATOR` | No | Register operator API key at startup |
| `AOIP_API_KEY_VIEWER` | No | Register viewer API key at startup |
| `PRODUCE_INTERVAL` | No | Producer burst interval in seconds (default: 0.5) |
| `QDRANT_HOST` | No | Qdrant hostname (default: `qdrant`) |
| `EMBEDDING_MODEL` | No | Sentence-transformers model for vector indexing (default: `all-MiniLM-L6-v2`) |

## API Quick Reference

### Ask (agentic Q&A)

```bash
curl -X POST http://localhost:8000/ask \
  -H "Content-Type: application/json" \
  -d '{"question":"Why are Phoenix sales down?","store_id":"245","persona":"executive"}'
```

### Streaming Q&A (SSE)

```bash
curl -N -X POST http://localhost:8000/ask/stream \
  -H "Content-Type: application/json" \
  -d '{"question":"Summarize store 245 KPIs","store_id":"245"}'
```

### Operational Brief

```bash
curl -X POST http://localhost:8000/operations/brief \
  -H "Content-Type: application/json" \
  -d '{"store_id":"245","region":"Phoenix","persona":"store_manager"}'
```

### KPIs

```bash
curl -X POST http://localhost:8000/kpi/enriched -H "Content-Type: application/json" -d '{"store_id":"245"}'
curl http://localhost:8000/kpi/catalog
curl http://localhost:8000/alerts/245
curl http://localhost:8000/metrics
curl http://localhost:8000/health
```

## Authentication

When `AOIP_AUTH_DISABLED` is not set to `true`, pass `X-API-Key` on every request:

```bash
curl -X POST http://localhost:8000/ask \
  -H "X-API-Key: your-key" \
  -H "Content-Type: application/json" \
  -d '{"question":"Revenue summary"}'
```

| Role | Access |
|------|--------|
| `admin` | All endpoints |
| `operator` | Query, KPI, alerts, operations, skills, streaming |
| `viewer` | KPI and alerts (read-only) |

## Testing

```bash
make test               # quick run
make test-cov           # with coverage report (40% minimum gate)
uv run pytest -v tests/test_ai_gaps.py   # single file
```

### LLM smoke tests

Quick provider smoke test through the project LLM wrapper:

```bash
AOIP_LLM__PROVIDER=ollama \
AOIP_LLM__MODEL=llama3.2:latest \
AOIP_LLM__OLLAMA_BASE_URL=http://localhost:11434 \
python - <<'PY'
from ai_systems.core.llm import generate
print(generate('Reply with exactly: ollama_smoke_ok'))
PY
```

API-level smoke test (after `make dev`):

```bash
curl -X POST http://localhost:8000/ask \
  -H "Content-Type: application/json" \
  -d '{"question":"Reply with exactly: api_smoke_ok","store_id":"245"}'
```

## Conduktor not responding

```bash
make conduktor-health   # check health endpoint
make conduktor-restart  # restart the container (clears frozen HTTP thread pool)
```

## Troubleshooting

| Symptom | Fix |
|---------|-----|
| `docker compose up` fails with `.env not found` | Run `make env` |
| Broker containers stuck `starting` | Volumes may have corrupted Raft metadata; run `make down` then wipe broker volumes: `docker volume rm $(docker volume ls -q \| grep broker)` then `make up` |
| Conduktor shows unhealthy | Run `make conduktor-restart` — autoheal also handles this automatically |
| `ModuleNotFoundError` | Run `make install` |
| Ollama calls fail with connection refused | Start Ollama (`ollama serve`) and verify `AOIP_LLM__OLLAMA_BASE_URL` |
| Anthropic calls fail with missing key | Set `ANTHROPIC_API_KEY` and `AOIP_LLM__PROVIDER=anthropic` |
| LLM output looks degraded in Ollama mode | Use a stronger Ollama model or switch provider to Anthropic |
| Port 8000 in use | Kill existing process or run `make dev` with `--port 8001` |

## Deployment Notes

- Configure `ai_systems/config/settings.py` with real Aurora MySQL and MSK endpoints.
- Use AWS Secrets Manager for credentials (referenced by `password_secret_name` in settings).
- Replace MinIO with AWS S3; replace Iceberg REST catalog with AWS Glue Catalog or Nessie.
- Replace `StreamingStateStore` with Redis or a Kafka consumer for real-time state.
- Connect `MetricsCollector` in `observability/evaluation.py` to Prometheus/Grafana for production dashboards.
- Use MWAA or Astronomer Cloud for production Airflow deployment.
- Use `PromptRegistry` version pinning in production to prevent unintended prompt changes.
