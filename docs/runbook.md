# AOIP Operations Runbook

This runbook is a procedure-first playbook for operating and recovering the local AOIP platform.

## 1) Operating Principles

- Run commands from repository root.
- Use exact command sequence; do not skip validation gates.
- Prefer targeted restarts over full stack restarts.
- Keep alerts actionable: no noisy probes, no stale rules.
- For destructive actions (volume deletion), confirm intent first.

## 2) Prerequisites

- Python 3.12+
- uv
- Docker Desktop (8+ GB RAM recommended)
- Maven 3.x (`brew install maven`) for Flink fat JAR build
- Optional local LLM: Ollama

Required environment file:

```bash
make env
```

## 3) Procedure A: First-Time Bootstrap

Goal: prepare all dependencies and build artifacts.

```bash
make install
make env
make flink-jar
```

Validation:

```bash
make ps
```

Pass criteria:

- Python environment is created.
- No missing dependency errors.
- Flink JAR exists and build completed successfully.

## 4) Procedure B: Standard Startup (Core)

Goal: start the platform in a stable baseline state.

```bash
make up
make ps
```

Validation:

```bash
curl --noproxy '*' -sf http://localhost:8000/health
curl --noproxy '*' -sf http://localhost:8081/subjects
curl --noproxy '*' -sf http://localhost:8083/connectors
curl --noproxy '*' -s -o /dev/null -w '%{http_code}\n' http://localhost:7474
```

Pass criteria:

- Core services are Up in `make ps`.
- API, Schema Registry, Kafka Connect, and Neo4j endpoints return healthy responses.

## 5) Procedure C: Full Pipeline Startup

Goal: bring up all major clusters and data/AI planes.

```bash
make up-full
make produce
make lake-up
make lake-stream
make dbt-deps
make dbt-run
make analytics-up
make analytics-materialize
make analytics-index
make graph-sync
```

Validation gate after startup:

```bash
make ps
curl --noproxy '*' -sf http://localhost:6333/healthz
curl --noproxy '*' -sf http://localhost:8085/health
curl --noproxy '*' -sf http://localhost:9090/api/v1/targets
curl --noproxy '*' -s -o /dev/null -w '%{http_code}\n' http://localhost:7474
```

Pass criteria:

- Qdrant, Airflow, Prometheus, and Neo4j endpoints respond.
- Prometheus targets are present and healthy.

## 6) Procedure D: Stage-by-Stage Operations

Use this when running or debugging one stage at a time.

### Stage 1: Source Event Production

```bash
make produce
make topics
```

### Stage 2: Flink Canonical -> Sink

```bash
make flink-up
make flink-run JOB=appointment
make flink-jobs
```

### Stage 3: Kafka Connect Sink -> MySQL ODS

```bash
make register-schemas
make register-connectors
curl --noproxy '*' -sf http://localhost:8083/connectors
```

### Stage 4: AI API Runtime

```bash
make dev
```

Quick checks:

```bash
curl --noproxy '*' -sf http://localhost:8000/health
curl -s -X POST http://localhost:8000/kpi/enriched -H 'Content-Type: application/json' -d '{"store_id":"245"}'
```

### Stage 5: Debezium CDC

```bash
make register-cdc
curl --noproxy '*' -sf http://localhost:8083/connectors/debezium-mysql-retail-ops/status
```

### Stage 6: Spark Streaming -> Iceberg Landing

```bash
make lake-stream
docker compose -f container/docker-compose.yaml logs --tail 120 spark-cdc-streaming
```

### Stage 7: dbt Transformations

```bash
make dbt-run
make dbt-test
```

### Stage 8: Feature + Vector Layer

```bash
make analytics-materialize
make analytics-index
```

Qdrant collection check:

```bash
curl -s --noproxy '*' http://localhost:6333/collections | cat
```

### Stage 9: Graph Relationships (Neo4j)

```bash
make graph-up
make graph-sync
make graph-check
```

Neo4j check:

```bash
curl --noproxy '*' -s -o /dev/null -w '%{http_code}\n' http://localhost:7474
```

Graph transform behavior:

- `make graph-sync` loads ODS-derived relationships (`AVAILABLE_AT`, `WORKS_AT`, `VISITS`).
- The same command also projects gold KPI snapshots from `iceberg.gold.gold_store_kpis` as `(:Store)-[:HAS_KPI_SNAPSHOT]->(:StoreKPI)`.

## 7) Procedure E: End-to-End Health Certification

Run this before demos, release validation, or major merges.

```bash
make ps
curl --noproxy '*' -sf http://localhost:8083/connectors/debezium-mysql-retail-ops/status
curl --noproxy '*' -sf http://localhost:8083/connectors/debezium-mysql-retail-ops/topics
docker compose -f container/docker-compose.yaml logs --tail 150 spark-cdc-streaming
curl --noproxy '*' -sf http://localhost:8085/health
curl -s --noproxy '*' http://localhost:6333/collections | cat
curl -s --noproxy '*' http://localhost:9090/api/v1/rules | head -c 1000
curl -s --noproxy '*' http://localhost:9090/api/v1/alerts | head -c 1000
curl --noproxy '*' -s -o /dev/null -w '%{http_code}\n' http://localhost:7474
```

Certification pass criteria:

- CDC connector status is RUNNING.
- Spark CDC stream logs show active streaming query.
- Airflow health endpoint is healthy.
- Qdrant contains expected collections.
- Neo4j Browser endpoint responds and graph sync completed.
- Prometheus rule groups load without YAML errors.
- Active alerts match real failures only.

## 8) Procedure F: Alert and Dashboard Operations

Major cluster monitoring uses:

- Prometheus config: `container/observability/prometheus.yml`
- Alert rules: `container/observability/alerts.yml`
- Blackbox modules: `container/observability/blackbox.yml`
- Grafana dashboards: `container/observability/grafana/provisioning/dashboards/`

### Apply observability config changes

```bash
docker compose -f container/docker-compose.yaml restart prometheus
docker compose -f container/docker-compose.yaml ps prometheus
curl -s --noproxy '*' http://localhost:9090/api/v1/rules | head -c 1000
curl -s --noproxy '*' http://localhost:9090/api/v1/targets | head -c 1000
curl -s --noproxy '*' http://localhost:9090/api/v1/alerts | head -c 1000
```

Pass criteria:

- Prometheus status is Up (not restart loop).
- Rules endpoint returns success and healthy groups.
- Targets endpoint shows healthy probes.
- Alerts endpoint has no false positives.

## 9) Incident Playbooks

### Incident 1: Prometheus restart loop after alert changes

Symptoms:

- Prometheus container repeatedly restarts.
- Rules endpoint unavailable.

Actions:

```bash
docker compose -f container/docker-compose.yaml logs --tail 120 prometheus | cat
```

If logs show YAML parse error in alerts file:

1. Fix indentation/quotes in `container/observability/alerts.yml`.
2. Restart Prometheus.
3. Re-check rules/targets/alerts endpoints.

### Incident 2: Kafka cluster degraded alert is firing

Actions:

```bash
curl --noproxy '*' -sf http://localhost:8083/connectors
curl --noproxy '*' -sf http://localhost:8081/subjects
docker compose -f container/docker-compose.yaml ps kafka-connect schema-registry
```

Recovery:

```bash
docker compose -f container/docker-compose.yaml restart kafka-connect schema-registry
```

### Incident 3: CDC RUNNING but landing is empty

Actions:

```bash
make lake-stream
docker compose -f container/docker-compose.yaml logs --tail 150 spark-cdc-streaming
docker exec container-minio-1 sh -lc 'ls -la /data/landing && ls -la /data/checkpoints'
```

Recovery:

- Ensure CDC topics are present and connector topics endpoint returns expected mappings.
- Keep stream process running; validate checkpoint activity.

### Incident 4: dbt layer fails to connect to Spark Thrift

Actions:

```bash
make ps
docker compose -f container/docker-compose.yaml logs --tail 150 spark-thriftserver
make dbt-run LAYER=bronze
```

Recovery:

- Ensure required namespaces exist: default, bronze, silver, gold, analytics.
- Re-run failed layer after Spark Thrift Server is healthy.

### Incident 5: Qdrant collections missing

Actions:

```bash
curl -s --noproxy '*' http://localhost:6333/collections | cat
make analytics-index
curl -s --noproxy '*' http://localhost:6333/collections | cat
```

Recovery:

- Confirm analytics source tables are available.
- If source data is sparse, verify indexer source selection config.

### Incident 6: Neo4j relationships missing

Actions:

```bash
make graph-up
make graph-sync
curl --noproxy '*' -s -o /dev/null -w '%{http_code}\n' http://localhost:7474
```

Recovery:

- Ensure MySQL ODS tables contain customer, employee, article_inventory data.
- Re-run `make graph-sync` after upstream ingestion catches up.

## 10) Controlled Restart and Shutdown

Targeted restarts:

```bash
docker compose -f container/docker-compose.yaml restart <service>
```

Core restart:

```bash
make restart
```

Full restart:

```bash
make restart-full
```

Shutdown:

```bash
make down
```

## 11) Rollback Procedure

Use when a config or code change introduces instability.

1. Revert the last known-bad change in git.
2. Restart only impacted services first.
3. Re-run Procedure E (End-to-End Health Certification).
4. If still failing, execute `make restart-full` and re-certify.

## 12) Reference Endpoints

- API: http://localhost:8000
- Schema Registry: http://localhost:8081
- Flink Dashboard: http://localhost:8082
- Kafka Connect: http://localhost:8083
- Airflow UI: http://localhost:8085
- Conduktor: http://localhost:8086
- Prometheus: http://localhost:9090
- Grafana: http://localhost:3000
- Qdrant: http://localhost:6333/dashboard
- Feast Server: http://localhost:6566
- Neo4j Browser: http://localhost:7474

## 13) Monitoring Guide (Platform, UI, and curl)

Use this matrix during daily operations and incident triage. For each platform, first open the UI for context, then run the curl check for a binary health signal.

| Platform        | What to monitor                                         | UI                              | curl check                                                                     | Healthy signal                                                     |
| --------------- | ------------------------------------------------------- | ------------------------------- | ------------------------------------------------------------------------------ | ------------------------------------------------------------------ |
| AOIP API        | API readiness and auth/runtime wiring                   | http://localhost:8000/docs      | `curl --noproxy '*' -sf http://localhost:8000/health`                          | HTTP 200 with health payload                                       |
| Schema Registry | Avro schema availability and compatibility path         | http://localhost:8081           | `curl --noproxy '*' -sf http://localhost:8081/subjects`                        | JSON array returned                                                |
| Kafka Connect   | Connector lifecycle, task failures, and rebalance churn | http://localhost:8083           | `curl --noproxy '*' -sf http://localhost:8083/connectors`                      | Connector list returned                                            |
| Flink           | JobManager status, running jobs, and failed restarts    | http://localhost:8082           | `curl --noproxy '*' -sf http://localhost:8082/overview`                        | JSON overview with task slots/job stats                            |
| Airflow         | Scheduler heartbeat and webserver health                | http://localhost:8085           | `curl --noproxy '*' -sf http://localhost:8085/health`                          | JSON status for metadatabase/scheduler                             |
| Conduktor       | Kafka control plane UX availability                     | http://localhost:8086           | `curl --noproxy '*' -s -o /dev/null -w '%{http_code}\n' http://localhost:8086` | HTTP 200/302                                                       |
| Prometheus      | Rule eval health, scrape stability, active alerts       | http://localhost:9090           | `curl --noproxy '*' -sf http://localhost:9090/api/v1/targets`                  | `"status":"success"` and healthy targets                           |
| Grafana         | Dashboard server and data source rendering path         | http://localhost:3000           | `curl --noproxy '*' -sf http://localhost:3000/api/health`                      | JSON with `"database":"ok"`                                        |
| Qdrant          | Vector DB liveness and collection serving               | http://localhost:6333/dashboard | `curl --noproxy '*' -sf http://localhost:6333/healthz`                         | `ok` response                                                      |
| Feast Server    | Feature-serving endpoint reachability                   | http://localhost:6566           | `curl --noproxy '*' -s -o /dev/null -w '%{http_code}\n' http://localhost:6566` | HTTP response code returned (typically 200/404 depending on route) |
| Neo4j           | Graph service readiness and relationship query surface  | http://localhost:7474           | `curl --noproxy '*' -s -o /dev/null -w '%{http_code}\n' http://localhost:7474` | HTTP 200/302                                                       |

Monitoring workflow:

1. Open the UI and confirm the control plane loads.
2. Run the curl check and confirm the healthy signal.
3. If curl fails but UI loads, inspect auth/proxy mismatch.
4. If both fail, restart only the affected service and re-check.

## 14) Key Environment Variables

- AOIP_LLM\_\_PROVIDER: `ollama` or `anthropic`
- AOIP_LLM\_\_MODEL: provider model id
- ANTHROPIC_API_KEY: required for anthropic provider
- AOIP_LLM\_\_OLLAMA_BASE_URL: required for ollama provider
- AOIP_LLM\_\_OLLAMA_TIMEOUT_SECONDS: ollama HTTP timeout
- AOIP_AUTH_DISABLED: disable auth for local development when `true`
- AOIP_NEO4J\_\_URI: Neo4j Bolt URI (for example `bolt://neo4j:7687`)
- AOIP_NEO4J\_\_USERNAME: Neo4j username
- NEO4J_PASSWORD: Neo4j password used by graph sync
- PRODUCE_INTERVAL: synthetic producer interval in seconds
- QDRANT_HOST: qdrant hostname override
- EMBEDDING_MODEL: sentence-transformers model name

## Terminology Glossary

Use canonical definitions from [Terminology Glossary](terminology-glossary.md) when describing platform components, data layers, and AI workflows.

## Structural Formatting Standard

This document follows the shared [Markdown Structure Standard](markdown-structure-standard.md) for heading hierarchy, section order, procedure formatting, and link conventions.
