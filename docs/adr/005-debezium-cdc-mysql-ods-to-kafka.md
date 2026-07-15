# ADR-005: Debezium CDC from MySQL ODS to Kafka

## Status

Accepted

## Context

The platform requires a second Kafka ingestion path that captures every change (INSERT/UPDATE/DELETE) that Kafka Connect JDBC Sink writes into MySQL ODS. This CDC stream feeds the Iceberg lakehouse (Spark Structured Streaming) and must preserve the full change history with operation type, before/after row state, and source metadata.

## Decision

Use a **Debezium MySQL source connector** (running inside the Kafka Connect cluster) to capture MySQL ODS binlog events and publish them as Debezium-envelope JSON to CDC Kafka topics.

Configuration:
- One connector instance covers all five ODS tables (`sales_orders`, `appointments`, `pos_invoices`, `work_orders`, `inventory_snapshots`).
- Registered via `container/scripts/register_cdc_connector.py`.
- Topic naming: `retail_ops.aurora.retail_ops.<table>` (mirrors the AWS DMS/MSK convention for production compatibility).
- Debezium envelope schema: `{ "before": {...}, "after": {...}, "op": "c|u|d|r", "ts_ms": 123, "source": {...} }`.
- `snapshot.mode: initial` — performs a one-time initial snapshot then switches to streaming.

## Alternatives considered

| Option | Reason not chosen |
|--------|------------------|
| AWS DMS (production) | Same logical decision; DMS is the production equivalent — Debezium is used locally |
| Kafka Connect JDBC Source | Poll-based, not log-based; misses DELETEs; higher latency; no before-state |
| Maxwell's Daemon | Less active community; limited SMT support; no Docker-native packaging |
| Custom binlog reader (python-mysql-replication) | Manual offset tracking; no Schema Registry integration; fragile |

## Consequences

### Positive
- Captures DELETEs, not just upserts — essential for correct CDC merge in the silver layer.
- The `before` field enables auditing and bi-temporal modeling.
- `op` field (`c/u/d/r`) maps directly to dbt silver model CDC merge logic.
- Debezium handles MySQL GTID position tracking automatically; restarting the connector resumes from the last committed offset.
- Topic naming is identical to the AWS DMS convention — switching to DMS in production requires only a Kafka topic rename or alias.

### Negative / trade-offs
- Requires `binlog_format=ROW`, `binlog_row_image=FULL`, and `gtid_mode=ON` in MySQL — these are set in the `mysql` service `command:` in Docker Compose.
- A Debezium connector holds a long-lived MySQL connection; MySQL must allow persistent replication connections.
- Initial snapshot can take minutes for large ODS tables — downstream Spark jobs should be started after the snapshot completes.

### Neutral / constraints
- The Debezium plugin is pre-installed in the Kafka Connect Docker image (`debezium/debezium-connector-mysql`).
- CDC topics are consumed only by Spark Structured Streaming (`cdc_to_landing.py`); the AI real-time path reads MySQL ODS directly, not the CDC topics.
