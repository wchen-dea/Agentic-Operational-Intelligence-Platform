# ADR-003: CDC to Kafka/MSK for Real-Time Ingestion

## Status

Accepted

## Context

KPI computation and alerting must reflect operational changes within seconds of occurrence. Batch polling is too slow for store-manager real-time diagnosis use cases.

## Decision

Use change data capture (CDC) from Aurora MySQL into Kafka or Amazon MSK as the primary ingestion pattern. AWS DMS is the default connector; Debezium is an alternative.

Topic naming convention: `retail_ops.aurora.<schema>.<table>`

## Consequences

- Sub-minute event latency from source commit to bronze landing.
- Kafka/MSK provides durable, replayable event log for reprocessing.
- Requires operational investment in connector monitoring and topic management.
- Schema registry is recommended for forward/backward compatibility.
- The sample DMS task spec lives at `config/cdc/aws_dms_aurora_to_msk_task.example.json`.
