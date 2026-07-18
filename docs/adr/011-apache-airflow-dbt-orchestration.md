# ADR-011: Apache Airflow for dbt Pipeline Orchestration

## Status

Accepted

## Context

The dbt transformation pipeline (staging → bronze → silver → gold → analytics) must run on a regular schedule, respect inter-layer dependencies (silver cannot run before bronze), support manual triggers for ad-hoc reprocessing, and provide visibility into run history and failures. The orchestration layer must integrate with the existing Docker Compose stack without requiring a separate managed service.

## Decision

Use **Apache Airflow 2.9** (LocalExecutor, dedicated PostgreSQL metadata store) to schedule and execute the `dbt_lakehouse_pipeline` DAG on a **30-minute interval**.

DAG structure:

```
start → dbt_deps → bronze (run + test) → silver (run + test) → gold (run + test) → analytics (run + test) → end
```

Key decisions:

- **LocalExecutor** (not Celery/Kubernetes) — sufficient for single-node dev; no Redis or worker nodes required.
- **Custom Airflow image** (`container/airflow/Dockerfile`) pre-installs `dbt-spark[PyHive]` and `libsasl2` — dbt runs directly inside the Airflow worker process, not in a separate container.
- dbt project is **bind-mounted** at `/opt/airflow/dbt` — DAG picks up code changes without rebuilding the image.
- The `full_refresh` DAG param allows triggering a full rebuild of bronze/silver on demand.
- Each layer group uses `TaskGroup` for clean Airflow UI organization.
- Airflow metadata DB is a **dedicated PostgreSQL** instance (not shared with Conduktor).

In production: replace with MWAA (Managed Airflow) or Astronomer; same DAG code, different infrastructure.

## Alternatives considered

| Option                                  | Reason not chosen                                                                      |
| --------------------------------------- | -------------------------------------------------------------------------------------- |
| Prefect                                 | Excellent orchestration but adds another stack to operate; less mature dbt integration |
| Dagster                                 | Strong dbt integration but opinionated framework requiring code restructure            |
| Cron (native)                           | No UI, no retry logic, no dependency management, no parallelism                        |
| dbt Cloud                               | SaaS-only; paid; not suitable for local development                                    |
| Spark Structured Streaming (continuous) | dbt is a batch transformation tool — continuous streaming is not its execution model   |

## Consequences

### Positive

- Airflow UI (:8085) provides DAG graph view, task logs, run history, and manual trigger.
- `max_active_runs: 1` prevents overlapping runs that would cause silver merge conflicts.
- Task-level retry (`retries: 2, retry_delay: 5m`) handles transient Spark Thrift Server failures.
- The 30-minute schedule balances freshness vs. Spark cluster resource usage.

### Negative / trade-offs

- Airflow adds two additional containers (webserver + scheduler) plus a PostgreSQL instance.
- `airflow-init` one-shot container must complete before webserver/scheduler start — adds ~60 s to cold start.
- LocalExecutor serializes task execution — if a task hangs, it blocks subsequent tasks.

### Neutral / constraints

- `AIRFLOW__CORE__LOAD_EXAMPLES: "false"` — disables example DAGs to keep the UI clean.
- DAG file is at `container/airflow/dags/dbt_pipeline.py` — bind-mounted into the Airflow containers.

## Terminology Glossary

Use canonical definitions from [Terminology Glossary](../terminology-glossary.md) when describing platform components, data layers, and AI workflows.

## Structural Formatting Standard

This document follows the shared [Markdown Structure Standard](../markdown-structure-standard.md) for heading hierarchy, section order, procedure formatting, and link conventions.
