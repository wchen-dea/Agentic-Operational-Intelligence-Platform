# ADR-006: Apache Spark Structured Streaming for Iceberg Landing Layer

## Status

Accepted

## Context

CDC Kafka topics carry the full Debezium change-event history for all five ODS tables. This history must be ingested into the Iceberg lakehouse as an append-only landing layer, preserving the complete Debezium envelope (before/after/op/ts_ms) for downstream bronze dbt models to process. The ingestion must be fault-tolerant, resumable, and capable of writing partitioned Iceberg tables to MinIO.

## Decision

Use **Apache Spark Structured Streaming** (`pyspark`) with the **Iceberg Spark extensions** and **S3A connector** to read CDC topics and write to `iceberg.landing.*` tables in MinIO.

Implementation: `data_platform/spark/cdc_to_landing.py`

Key decisions:
- **Append mode** — every CDC event becomes a row; the landing table is the raw event log.
- **Iceberg table format** with `partition_by days(ingested_at)` — enables efficient time-range queries and partition pruning in bronze/silver.
- **Checkpoint** at `s3a://checkpoints/cdc/<table>` — enables exactly-once restart from any Kafka offset.
- **Iceberg REST catalog** (`http://iceberg-rest:8181`) manages all namespace and table metadata; Spark reads/writes go to MinIO via S3A.
- One streaming query per CDC topic; all run concurrently in the same SparkSession.
- Spark cluster: standalone (`spark://spark-master:7077`), replicated by EMR Serverless or Databricks in production.

## Alternatives considered

| Option | Reason not chosen |
|--------|------------------|
| Flink (same cluster as canonical jobs) | Mixed concern — canonical processing and landing are separate pipeline stages; adds resource contention |
| Kafka Connect S3 Sink | Writes raw Kafka bytes, not Iceberg tables; no partition management; no schema evolution |
| Databricks Auto Loader | Cloud-only; not available for local development; vendor lock-in |
| Direct Debezium → Iceberg (Kafka Connect Iceberg Sink) | Immature plugin; limited support for Iceberg REST catalog; no Spark-native optimization |

## Consequences

### Positive
- Exactly-once landing with Iceberg ACID transactions — no duplicate rows on restart.
- Iceberg time-travel allows replaying the landing table from any point in history.
- S3A + MinIO is API-compatible with AWS S3 — switching to S3 in production requires only endpoint and credential changes.
- Spark's native Iceberg integration supports schema evolution (new columns auto-added) without manual DDL.

### Negative / trade-offs
- Spark has a higher per-job memory footprint than Flink — requires 2–3 GB for the streaming job.
- Cold start takes 30–60 seconds for Spark to initialize and acquire executors.
- The `tabulario/spark-iceberg` image is ~4 GB — slow to pull on first use.

### Neutral / constraints
- `cdc_to_landing.py` creates the `iceberg.landing` namespace and tables if they don't exist on first run.
- Kafka bootstrap servers, Iceberg REST URL, and MinIO credentials are injected via environment variables — no hard-coded values.
