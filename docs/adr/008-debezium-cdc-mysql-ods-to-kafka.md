# ADR-008: Debezium CDC from MySQL ODS to Kafka

## Status

Accepted

## Context

The platform requires a second Kafka ingestion path that captures every change (INSERT/UPDATE/DELETE) that Kafka Connect JDBC Sink writes into MySQL ODS. This CDC stream feeds the Iceberg lakehouse (Spark Structured Streaming) and must preserve the full change history with operation type, before/after row state, and source metadata.

## Decision

Use a **Debezium MySQL source connector** (running inside the Kafka Connect cluster) to capture MySQL ODS binlog events and publish them as Debezium-envelope JSON to CDC Kafka topics.

Configuration:

- One connector instance covers all five ODS tables (`sales_orders`, `appointments`, `pos_invoices`, `work_orders`, `article_inventory`).
- Registered via `container/scripts/register_cdc_connector.py`.
- Topic naming (runtime): Debezium emits `dbz.retail_ops.<table>` and RegexRouter rewrites to `cdc_<table>`.
- Debezium envelope schema: `{ "before": {...}, "after": {...}, "op": "c|u|d|r", "ts_ms": 123, "source": {...} }`.
- `snapshot.mode: initial` — performs a one-time initial snapshot then switches to streaming.

## Alternatives considered

| Option                                          | Reason not chosen                                                                  |
| ----------------------------------------------- | ---------------------------------------------------------------------------------- |
| AWS DMS (production)                            | Same logical decision; DMS is the production equivalent — Debezium is used locally |
| Kafka Connect JDBC Source                       | Poll-based, not log-based; misses DELETEs; higher latency; no before-state         |
| Maxwell's Daemon                                | Less active community; limited SMT support; no Docker-native packaging             |
| Custom binlog reader (python-mysql-replication) | Manual offset tracking; no Schema Registry integration; fragile                    |

## Consequences

### Positive

- Captures DELETEs, not just upserts — essential for correct CDC merge in the silver layer.
- The `before` field enables auditing and bi-temporal modeling.
- `op` field (`c/u/d/r`) maps directly to dbt silver model CDC merge logic.
- Debezium handles MySQL GTID position tracking automatically; restarting the connector resumes from the last committed offset.
- Topic naming is normalized to `cdc_*` for local processing and consumed directly by Spark landing ingestion.

### Negative / trade-offs

- Requires `binlog_format=ROW`, `binlog_row_image=FULL`, and `gtid_mode=ON` in MySQL — these are set in the `mysql` service `command:` in Docker Compose.
- A Debezium connector holds a long-lived MySQL connection; MySQL must allow persistent replication connections.
- Initial snapshot can take minutes for large ODS tables — downstream Spark jobs should be started after the snapshot completes.

### Neutral / constraints

- The Debezium plugin is pre-installed in the Kafka Connect Docker image (`debezium/debezium-connector-mysql`).
- CDC topics are consumed only by Spark Structured Streaming (`data_platform/spark/cdc_to_landing.py`); the AI real-time path reads MySQL ODS directly, not the CDC topics.

## Terminology Glossary

Use canonical definitions from [Terminology Glossary](../terminology-glossary.md) when describing platform components, data layers, and AI workflows.

## Structural Formatting Standard

This document follows the shared [Markdown Structure Standard](../markdown-structure-standard.md) for heading hierarchy, section order, procedure formatting, and link conventions.
