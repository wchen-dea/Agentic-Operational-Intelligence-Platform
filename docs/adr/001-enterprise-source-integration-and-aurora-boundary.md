# ADR-001: Enterprise Source Integration Layer and Aurora Operational Boundary

## Status

Accepted

## Context

The platform ingestion layer must harmonize enterprise source systems into a canonical contract before downstream CDC, lakehouse, and AI processing. Upstream domains include ERP (for example SAP), CRM and appointment systems (for example Salesforce), workforce/HR systems (for example Workday and Kronos), vehicle inspection/service systems (including DynamoDB-backed inspection records), payment system (POS), and Enterprise master/reference data systems.

Data arrival patterns span real-time, near real-time, and batch cadences. The operational source of record for the platform must therefore provide:

- Low-latency CDC for event-oriented updates
- ACID transaction guarantees for operational integrity
- Relational join semantics for KPI derivation across domains
- Schema introspection for canonical Avro schema generation

In this project, synthetic producers mirror those enterprise source systems and cadence patterns, while MySQL is used as the consolidated operational source boundary for platform execution.

## Decision

Use **AWS Aurora MySQL** (or self-hosted MySQL 8.0) as the normalized operational boundary after enterprise-source integration. All KPI computation, CDC streaming, and analytics derive from this consolidated source boundary.

Domains hosted in Aurora MySQL:

- Sales order headers, line items, fees, taxes, and promotions
- Customer appointments and slot reservations
- POS invoice receipts, payments, and allocations
- Vehicle work orders with bay assignments and labour/parts costs
- Inventory snapshots with SKU-level stock and reorder data

This structure represents the normalized operational boundary after enterprise integration, not a claim that every upstream enterprise application is natively hosted in Aurora.

## Alternatives considered

| Option               | Reason not chosen                                                                                 |
| -------------------- | ------------------------------------------------------------------------------------------------- |
| PostgreSQL           | Less mature CDC tooling for AWS DMS; lower adoption in retail ERP ecosystems                      |
| MongoDB              | No binary-log CDC; change streams add operational complexity; not ACID across collections         |
| Snowflake / Redshift | OLAP systems — not designed as a system of record for transactional writes                        |
| DynamoDB             | No native binary-log CDC compatible with Debezium/DMS; limited JOIN semantics for KPI computation |

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

- MySQL ODS database (`retail_ops`) is populated by Kafka Connect JDBC Sink connectors, not written to directly by the application.
- Local DDL scripts live in `data_platform/ddl/`; Flyway or Liquibase can manage migrations in production.

## Terminology Glossary

Use canonical definitions from [Terminology Glossary](../terminology-glossary.md) when describing platform components, data layers, and AI workflows.

## Structural Formatting Standard

This document follows the shared [Markdown Structure Standard](../markdown-structure-standard.md) for heading hierarchy, section order, procedure formatting, and link conventions.
