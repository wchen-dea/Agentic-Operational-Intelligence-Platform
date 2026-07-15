# ADR-001: Aurora MySQL as Operational Source System

## Status

Accepted

## Context

The platform needs real-time access to transactional data across five operational domains: sales orders, appointments, POS invoices, work orders, and inventory snapshots. The source system must support sub-second CDC event emission, ACID transactions for operational integrity, and schema introspection for downstream Avro schema generation.

## Decision

Use **AWS Aurora MySQL** (or self-hosted MySQL 8.0) as the single system of record for all core operational domains. All KPI computation, CDC streaming, and analytics derive exclusively from this source.

Domains hosted in Aurora MySQL:
- Sales order headers, line items, fees, taxes, and promotions
- Customer appointments and slot reservations
- POS invoice receipts, payments, and allocations
- Vehicle work orders with bay assignments and labour/parts costs
- Inventory snapshots with SKU-level stock and reorder data

## Alternatives considered

| Option | Reason not chosen |
|--------|------------------|
| PostgreSQL | Less mature CDC tooling for AWS DMS; lower adoption in retail ERP ecosystems |
| MongoDB | No binary-log CDC; change streams add operational complexity; not ACID across collections |
| Snowflake / Redshift | OLAP systems — not designed as a system of record for transactional writes |
| DynamoDB | No native binary-log CDC compatible with Debezium/DMS; limited JOIN semantics for KPI computation |

## Consequences

### Positive
- Aurora MySQL binary log is directly compatible with AWS DMS, Debezium, and MSK Connect plugins.
- Read replicas absorb analytics load without impacting transactional performance.
- Avro schema generation is straightforward from MySQL `information_schema`.
- Self-hosted MySQL 8.0 provides a production-identical local development environment (`mysql:8.0` Docker image).

### Negative / trade-offs
- Schema changes in Aurora MySQL must be coordinated with downstream Avro schemas and bronze table DDL.
- CDC lag increases under heavy write load if binlog replication falls behind.
- `GTID_MODE=ON` and `ENFORCE_GTID_CONSISTENCY=ON` are required for Debezium — these must be set at cluster creation time in Aurora.

### Neutral / constraints
- MySQL ODS database (`retail_ops_sink`) is populated by Kafka Connect JDBC Sink connectors, not written to directly by the application.
- Local DDL scripts live in `data_platform/ddl/`; Flyway or Liquibase can manage migrations in production.
