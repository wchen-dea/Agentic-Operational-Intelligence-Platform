# ADR-013: Neo4j Graph Projection Layer for Operational Relationships

## Status

Accepted

## Context

The platform already provides relational and analytical paths (MySQL ODS, Iceberg gold/analytics, Feast, Qdrant, MetricFlow), but several operational questions are graph-native:

- Which articles are available at stores with rising customer visits?
- Which employees are connected to stores with persistent service gaps?
- Which relationship neighborhoods correlate with KPI snapshot changes over time?

Answering these with repeated SQL joins across ODS and gold adds query complexity and slows iterative investigations. The project needs a graph projection that is easy to traverse and can be refreshed from canonical operational data.

## Decision

Adopt **Neo4j 5.x** as a dedicated graph projection layer and materialize relationship-focused entities from ODS and gold.

Projection model:

- `(:Article)-[:AVAILABLE_AT]->(:Store)` from inventory and article/store mappings.
- `(:Employee)-[:WORKS_AT]->(:Store)` from workforce and work-order linkages.
- `(:Customer)-[:VISITS]->(:Store)` from appointment, sales-order, and work-order activity.
- `(:Store)-[:HAS_KPI_SNAPSHOT]->(:StoreKPI)` from `iceberg.gold.gold_store_kpis`.

Implementation:

- `data_platform/graph/sync_relationships.py` for ODS relationship projection.
- `data_platform/graph/sync_gold_kpis.py` for gold KPI snapshot projection.
- `make graph-sync` runs both projections.
- `make graph-check` validates key relationship cardinalities.

Runtime integration:

- Neo4j service runs in local compose with browser on `:7474` and Bolt on `:7687`.
- Application and sync scripts read `AOIP_NEO4J__URI`, `AOIP_NEO4J__USERNAME`, and `NEO4J_PASSWORD`.

## Alternatives considered

| Option                        | Reason not chosen                                                                 |
| ----------------------------- | --------------------------------------------------------------------------------- |
| PostgreSQL recursive CTEs     | Works for limited traversals but becomes difficult to maintain for multi-hop use |
| Amazon Neptune                | Strong managed option but adds cloud dependency for local-first development      |
| JanusGraph                    | Flexible but higher operational overhead and weaker local ergonomics             |
| Repeated SQL join projections | Duplicates logic per query and slows analyst iteration for graph-style questions |

## Consequences

### Positive

- Operational investigations can use relationship traversals without repeatedly rebuilding complex SQL joins.
- Graph and lakehouse remain decoupled; graph can be rebuilt deterministically from ODS and gold.
- Relationship cardinality checks in `make graph-check` make graph refresh regressions visible quickly.

### Negative / trade-offs

- Adds one more stateful service to operate (`neo4j_data` volume lifecycle, credentials, health checks).
- Projection jobs introduce additional pipeline runtime and dependency on both ODS and Spark Thrift availability.

### Neutral / constraints

- Neo4j is a projection layer, not a source of truth; ODS and gold remain authoritative.
- Graph refresh cadence is currently command-driven (`make graph-sync`), not event-driven streaming.

## Terminology Glossary

Use canonical definitions from [Terminology Glossary](../terminology-glossary.md) when describing platform components, data layers, and AI workflows.

## Structural Formatting Standard

This document follows the shared [Markdown Structure Standard](../markdown-structure-standard.md) for heading hierarchy, section order, procedure formatting, and link conventions.
