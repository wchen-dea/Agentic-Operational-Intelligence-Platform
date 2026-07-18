# ADR-012: Analytics/ML/LLM Layer Architecture

## Status

Accepted

## Context

The gold Iceberg layer (`gold_store_kpis`) provides daily KPI aggregations. Downstream ML models (store performance forecasting, customer churn prediction), LLM retrieval (semantic KPI search), and dimension-aware metric queries need further data products derived from gold. These downstream consumers require different access patterns: low-latency online feature serving, vector similarity search, and named metric queries by dimension.

## Decision

Implement a four-component analytics layer downstream of gold, all fed by dbt analytics models (`data_platform/dbt/models/analytics/`) plus graph projections (`data_platform/graph/`):

| Component          | Technology     | Role                                                                                                                              | Data source                                                          |
| ------------------ | -------------- | --------------------------------------------------------------------------------------------------------------------------------- | -------------------------------------------------------------------- |
| **Feature Store**  | Feast 0.40     | Offline (Iceberg analytics tables) + Online (Redis) feature serving                                                               | `iceberg.analytics.feat_store_performance`, `feat_customer_behavior` |
| **Vector Index**   | Qdrant 1.9     | KPI narrative embeddings (`store_kpi_narratives`) and metric description embeddings (`metric_definitions`) for AI semantic search | `iceberg.gold.gold_store_kpis`                                       |
| **Semantic Layer** | dbt MetricFlow | 9 named business metrics queryable by `store_id` × `kpi_date`                                                                     | `iceberg.gold.gold_store_kpis`                                       |
| **Graph Layer**    | Neo4j 5.23     | Relationship graph (`AVAILABLE_AT`, `WORKS_AT`, `VISITS`) and store KPI snapshot projection (`HAS_KPI_SNAPSHOT`)                 | ODS + `iceberg.gold.gold_store_kpis`                                 |

Feature engineering models (dbt analytics layer):

- `feat_store_performance` — rolling 7d/28d revenue, WoW growth, show-rate delta, overdue rate, reorder pressure.
- `feat_customer_behavior` — RFM (recency/frequency/monetary), appointment show rate, churn risk band.

Indexing pipeline (`data_platform/vector_index/indexer.py`):

- Reads gold KPI rows via Spark Thrift and converts them to narrative text.
- Resolves sources in order from `KPI_SOURCE_TABLES` (default: `warehouse.gold_store_kpis,iceberg.gold.gold_store_kpis`).
- Supports controlled fallback via `KPI_FALLBACK_MODE` (`sample` or `none`).
- Embeds with `sentence-transformers/all-MiniLM-L6-v2` (384-dim, cosine distance).
- Upserts to Qdrant collections; triggered via `make analytics-index`.

Graph projection pipeline:

- `data_platform/graph/sync_relationships.py` projects ODS-derived entity relationships.
- `data_platform/graph/sync_gold_kpis.py` projects gold KPI snapshots to `StoreKPI` nodes.
- Triggered via `make graph-sync`; validated via `make graph-check`.

## Alternatives considered

| Component      | Alternatives considered                        | Reason Feast/Qdrant/MetricFlow chosen                                                                                   |
| -------------- | ---------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------- |
| Feature Store  | AWS SageMaker Feature Store, Tecton, Hopsworks | Feast is open-source, Iceberg-native, Redis-backed; works without cloud                                                 |
| Vector DB      | ChromaDB, Pinecone, Weaviate, pgvector         | Qdrant: REST + gRPC, persistent volume, filter-combined search, local Docker; ChromaDB reserved for AI layer RAG corpus |
| Semantic Layer | Cube.dev, Looker, Metabase                     | dbt MetricFlow is already in the dbt project; no additional service                                                     |
| Graph Layer    | Amazon Neptune, JanusGraph, ArangoDB           | Neo4j has strong local ergonomics, Cypher readability, and direct relationship modeling for operational graph use cases |

## Consequences

### Positive

- Feast online store (Redis) serves features at < 5 ms p99 for ML inference.
- Qdrant enables semantic KPI search (`"stores with declining show rate"`) in the AI orchestrator without pre-specifying store IDs.
- MetricFlow metrics are queryable via `dbt sl query --metrics revenue_total --group-by store_id,kpi_date`.
- Neo4j relationship + KPI snapshot graph supports graph traversals without pre-joining ODS/lakehouse tables in each query.
- All four components read from ODS/lakehouse projections — they can be rebuilt by re-running `make dbt-run LAYER=analytics`, `make analytics-index`, then `make graph-sync`.

### Negative / trade-offs

- The vector indexer requires running Spark Thrift Server to read Iceberg gold data — adds a dependency on the lakehouse being healthy.
- Qdrant is not replicated in local dev — data is lost on container recreation (mitigated by `qdrant_data` volume).
- Feast materialization (`make analytics-materialize`) must be re-run after each dbt analytics run to keep online features fresh.
- Graph projection requires both MySQL ODS and Spark Thrift availability during `make graph-sync` execution.

### Neutral / constraints

- The `sentence-transformers` embedding model (~90 MB) is downloaded on first indexer run and cached in the container.
- Qdrant REST dashboard at `:6333/dashboard` provides a UI for inspecting collections and running test queries.
- `make analytics-materialize` is implemented to run against a prebuilt `feast-server` image with Java and pinned Spark runtime preinstalled (no runtime apt/pip installs in the Make target).
- `make graph-check` validates graph cardinalities for `AVAILABLE_AT`, `WORKS_AT`, `VISITS`, and `HAS_KPI_SNAPSHOT` after sync.

## Terminology Glossary

Use canonical definitions from [Terminology Glossary](../terminology-glossary.md) when describing platform components, data layers, and AI workflows.

## Structural Formatting Standard

This document follows the shared [Markdown Structure Standard](../markdown-structure-standard.md) for heading hierarchy, section order, procedure formatting, and link conventions.
