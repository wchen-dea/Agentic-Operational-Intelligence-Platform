# Terminology Glossary

This glossary defines canonical terms used across AOIP documentation. Use these terms consistently in architecture docs, ADRs, runbooks, and UI/API references.

| Term            | Canonical meaning                                                                              |
| --------------- | ---------------------------------------------------------------------------------------------- |
| AOIP            | Agentic Operational Intelligence Platform.                                                     |
| ODS             | Operational Data Store in MySQL populated from Kafka Connect sink topics.                      |
| CDC             | Change Data Capture from MySQL ODS into Kafka via Debezium.                                    |
| Landing         | Iceberg `landing` schema containing raw CDC-normalized datasets.                               |
| Bronze          | dbt layer with standardized, lightly cleaned canonical records.                                |
| Silver          | dbt conformed layer for business-ready entities and joins.                                     |
| Gold            | dbt business KPI layer (`gold_store_kpis`) used by analytics and AI consumers.                 |
| Analytics Layer | dbt feature-oriented models (for example `feat_store_performance`, `feat_customer_behavior`).  |
| Semantic Layer  | MetricFlow semantic definitions over gold models.                                              |
| Feature Store   | Feast registry and online serving/materialization workflow.                                    |
| Vector Index    | Qdrant collections built from KPI narratives and metric definitions.                           |
| Graph Layer     | Neo4j graph projection built from ODS relationships and gold KPI snapshots.                    |
| Graph Sync      | End-to-end Neo4j refresh process (`make graph-sync`) combining ODS and gold projections.       |
| Graph Check     | Cypher validation workflow (`make graph-check`) that verifies relationship cardinalities.       |
| KPI             | Key Performance Indicator used for operational decisions and alerting.                         |
| RAG             | Retrieval-Augmented Generation combining vector and lexical retrieval context for LLM prompts. |
| Skill           | Reusable callable capability exposed through the AOIP tool/skill framework.                    |
| Agent           | Role-specialized reasoning component (KPI, anomaly, promotion, recommendation).                |
| Orchestrator    | DAG-based execution engine that routes intent and coordinates agent nodes.                     |
| Blackbox Probe  | Prometheus probe executed through blackbox-exporter for HTTP/TCP reachability and latency.     |
| Cluster Health  | Availability and latency state of major platform planes: Kafka, Flink, Spark, Airflow.         |
| Materialization | Feast operation that pushes offline feature values into the online store.                      |

## Glossary Usage Rules

- Use the canonical term exactly as listed when writing new documentation.
- Prefer one canonical term per concept; avoid synonym drift across docs.
- If a new platform concept is introduced, update this glossary first, then reference it from other documents.
- Keep domain abbreviations expanded at first mention in each document.

## Terminology Glossary

This document is the canonical terminology glossary for AOIP.

## Structural Formatting Standard

This document follows the shared [Markdown Structure Standard](markdown-structure-standard.md) for heading hierarchy, section order, procedure formatting, and link conventions.
