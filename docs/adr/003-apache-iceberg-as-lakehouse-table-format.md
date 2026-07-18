# ADR-003: Apache Iceberg as Lakehouse Table Format

## Status

Accepted

## Context

The lakehouse needs a table format that supports ACID transactions (for CDC merge in silver), schema evolution (for adding new ODS columns without rewriting history), time-travel queries (for replaying history), and efficient data skipping via partition pruning. The format must work with Spark, dbt, and the Flink ecosystem, and be backed by S3-compatible object storage.

## Decision

Use **Apache Iceberg** (version 1.5.x) as the table format for all lakehouse layers (landing, bronze, silver, gold, analytics). All tables are managed via an **Iceberg REST catalog** (`tabulario/iceberg-rest:1.6.1`) backed by **MinIO** (`minio/minio`).

Catalog configuration:

- Catalog type: `rest` — standard REST catalog protocol, cloud-agnostic.
- `io-impl`: `org.apache.iceberg.aws.s3.S3FileIO` — writes to MinIO via the S3A protocol.
- Warehouse: `s3a://warehouse/` — all table data in a single MinIO bucket.
- `path-style-access: true` — required for MinIO (not AWS S3, which uses virtual-hosted-style).

For production: replace the REST catalog with AWS Glue Catalog (`GlueCatalog`), Nessie, or Apache Polaris; replace MinIO with S3.

## Alternatives considered

| Option              | Reason not chosen                                                                            |
| ------------------- | -------------------------------------------------------------------------------------------- |
| Delta Lake          | Apache Spark-only; limited support outside Databricks/EMR; no standard REST catalog API      |
| Apache Hudi         | Complex compaction operations; slower query performance vs Iceberg; smaller ecosystem        |
| Parquet files (raw) | No ACID; no schema evolution; no partition pruning metadata; requires manual file management |
| ORC                 | Limited Python/dbt ecosystem; Hive-centric; no standard catalog API                          |

## Consequences

### Positive

- Iceberg MERGE-on-READ (MOR) enables efficient upserts in the silver layer without full table rewrites.
- Schema evolution (add nullable column) is a metadata-only operation — no data files are rewritten.
- Time-travel (`AS OF TIMESTAMP` / `VERSION AS OF snapshot_id`) supports debugging, auditing, and reprocessing.
- Partition evolution — changing partition strategy does not require data migration.
- Standard REST catalog protocol means the same dbt profile and Spark config work against Glue, Nessie, or Polaris.

### Negative / trade-offs

- Small file problem — streaming appends create many small Parquet files; `REWRITE DATA FILES` compaction must be scheduled.
- Iceberg REST catalog is stateful — catalog data is stored in MinIO, which must be durable (not ephemeral Docker volume).
- `expire_snapshots` must be run regularly on bronze tables to prevent unbounded metadata growth.

### Neutral / constraints

- All dbt models use `file_format: iceberg` configured globally in `data_platform/dbt/dbt_project.yml`.
- The Iceberg REST catalog listens on port 8181 locally; all Spark and dbt connections point to `http://iceberg-rest:8181`.

## Terminology Glossary

Use canonical definitions from [Terminology Glossary](../terminology-glossary.md) when describing platform components, data layers, and AI workflows.

## Structural Formatting Standard

This document follows the shared [Markdown Structure Standard](../markdown-structure-standard.md) for heading hierarchy, section order, procedure formatting, and link conventions.
