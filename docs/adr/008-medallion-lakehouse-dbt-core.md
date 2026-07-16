# ADR-008: Medallion Lakehouse Transformations with dbt Core

## Status

Accepted

## Context

The Iceberg landing layer contains raw Debezium envelopes — not query-ready data. The platform needs a transformation layer that: (1) flattens CDC envelopes into typed columns (bronze), (2) applies CDC merge logic to produce current-state tables (silver), (3) aggregates per-store KPIs (gold), and (4) engineers ML features (analytics). Transformations must be version-controlled, testable, and incrementally updated.

## Decision

Use **dbt Core** (version 1.8, with `dbt-spark[PyHive]` adapter) for all lakehouse transformations. dbt connects to a **Spark Thrift Server** (HiveServer2-compatible, port 10000) that runs against the same Spark cluster as the CDC streaming job.

Layer materialization strategy:

| Layer | dbt materialization | Strategy | Key operation |
|-------|-------------------|----------|---------------|
| staging | view | — | Select from source, filter tombstones |
| bronze | incremental | append | Flatten `after_json`/`before_json`, tag `_cdc_op` |
| silver | incremental | merge | MERGE by PK + `delete_cdc_rows` post-hook for deletes |
| gold | table | full refresh | JOIN all silver entities into `gold_store_kpis` |
| analytics | table | full refresh | Rolling windows, RFM features from gold |

The `delete_cdc_rows` macro (in `data_platform/dbt/macros/cdc_merge.sql`) issues an Iceberg `DELETE FROM silver WHERE pk IN (SELECT pk FROM bronze WHERE _cdc_op = 'd')` post-hook.

Schema naming is controlled by `generate_schema_name.sql` — custom schemas map 1:1 to Iceberg namespaces (`iceberg.bronze`, `iceberg.silver`, etc.).

## Alternatives considered

| Option | Reason not chosen |
|--------|------------------|
| Custom Spark jobs (PySpark) | Verbose; no column lineage; no built-in testing framework; hard to onboard |
| Databricks SQL (Delta format) | Cloud-only; requires Databricks workspace; not local-dev-friendly |
| Apache Beam / Dataflow | Java-centric; high operational complexity for batch transformations |
| dbt + DuckDB | Excellent for local dev but DuckDB write-to-Iceberg support is limited; no production Spark cluster integration |

## Consequences

### Positive
- dbt tests (`not_null`, `unique`, `accepted_values`) enforce data quality at each layer boundary.
- Column lineage is queryable via `dbt docs generate` — every bronze/silver column traces back to a landing source field.
- `--select bronze` / `--select silver` runs individual layers independently for debugging.
- dbt incremental models skip already-processed records — silver runs complete in seconds for small deltas.
- The `data_platform/dbt/dbt_project.yml` global `+file_format: iceberg` applies Iceberg to all models without per-model config.

### Negative / trade-offs
- `dbt-spark[PyHive]` requires `libsasl2-dev` system library — this is pre-installed in the Airflow Docker image.
- Spark Thrift Server adds ~1 GB memory overhead beyond the Spark master/worker processes.
- dbt does not support native Iceberg `DELETE` — hard deletes in silver require the `delete_cdc_rows` post-hook macro.

### Neutral / constraints
- `data_platform/dbt/profiles.yml` is bind-mounted into the Airflow container at `/opt/airflow/dbt`.
- `dbt deps` must be run at least once to install `dbt-labs/dbt_utils` before any model runs.
