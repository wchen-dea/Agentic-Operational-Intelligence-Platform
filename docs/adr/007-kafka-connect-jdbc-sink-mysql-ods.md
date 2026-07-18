# ADR-007: Kafka Connect JDBC Sink for MySQL ODS Write

## Status

Accepted

## Context

The Flink stream processing layer produces approximately 50 PDM Sink Kafka topics, one per MySQL ODS table. These topics carry Avro-encoded records representing the current state of each domain entity. The ODS write mechanism must be idempotent, schema-aware, and require no custom consumer code per table.

## Decision

Use **Kafka Connect JDBC Sink connectors** (Confluent JDBC Sink plugin) to write all PDM Sink topics directly into MySQL `retail_ops` tables.

Key configuration decisions:

- One connector instance per Sink topic (registered via `container/scripts/register_connectors.py`).
- `auto.create: false` — tables are pre-created by DDL scripts in `data_platform/ddl/`; the connector does not manage schema.
- `insert.mode: upsert` — idempotent writes using the topic record key as the primary key.
- **ChangeCase SMT** (`jcustenborder/kafka-connect-transform-common`) converts Avro camelCase field names to MySQL snake_case automatically — no manual field mapping per connector.
- Field name overrides for ambiguous camelCase (e.g. `VIN`, `MVIArticleIndicator`) use `ReplaceField$Value` transforms prepended before ChangeCase.

The Kafka Connect cluster runs on port 8083 in both local Docker and MSK Connect (production).

## Alternatives considered

| Option                           | Reason not chosen                                                                              |
| -------------------------------- | ---------------------------------------------------------------------------------------------- |
| Direct DB writes from Flink      | Couples Flink to MySQL; loses Kafka as durable buffer; adds DB connection pooling to every job |
| Debezium JDBC Sink               | Less mature than Confluent JDBC Sink; fewer SMT options                                        |
| Custom Python consumer per table | N × consumer processes to maintain; no built-in dead-letter queue                              |
| Kafka Streams sink connector     | Java-only; adds another JVM process                                                            |

## Consequences

### Positive

- Zero custom consumer code — adding a new ODS table requires only a new DDL file and a connector registration call.
- SMT pipeline (ChangeCase → ReplaceField) eliminates manual field mapping for ~50 tables.
- Kafka Connect provides built-in dead-letter queue (`_dlq_connect_errors` topic), retry policies, and connector restart.
- Connector status is observable via the Kafka Connect REST API and Conduktor UI.

### Negative / trade-offs

- `auto.create: false` means DDL changes must be applied to MySQL before connector registration or the connector will fail.
- Upsert mode requires a primary key on every sink table — tables without PKs must use `insert.mode: insert` with idempotency handled by the application.
- The Confluent JDBC Sink plugin must be pre-installed in the Kafka Connect image (`confluent-hub install confluentinc/kafka-connect-jdbc`).

### Neutral / constraints

- Connector configs are built programmatically in `container/scripts/register_connectors.py` — adding a new table requires one new entry in that script, not a new JSON file.
- Local Kafka Connect uses the same plugin as MSK Connect; configs are environment-variable-parameterized for portability.

## Terminology Glossary

Use canonical definitions from [Terminology Glossary](../terminology-glossary.md) when describing platform components, data layers, and AI workflows.

## Structural Formatting Standard

This document follows the shared [Markdown Structure Standard](../markdown-structure-standard.md) for heading hierarchy, section order, procedure formatting, and link conventions.
