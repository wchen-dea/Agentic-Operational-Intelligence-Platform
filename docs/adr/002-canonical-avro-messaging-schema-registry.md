# ADR-002: Canonical Avro Messaging with Confluent Schema Registry

## Status

Accepted

## Context

The platform ingests data from five operational domains via a synthetic producer and real Aurora MySQL CDC. All 15 canonical Kafka topics must carry strongly typed, schema-versioned payloads that can be deserialized by downstream Flink jobs, Spark Streaming, and schema-aware tools like Conduktor. A consistent schema contract prevents silent data corruption across producer and consumer upgrades.

## Decision

Use **Apache Avro** as the wire format for all canonical Kafka topics, with schemas stored in and enforced by **Confluent Schema Registry** (running locally on port 8081; MSK Schema Registry in production).

- All schemas are defined in `data_platform/schema/*.avsc` (one per canonical topic).
- Schemas are registered at startup via `container/scripts/register_schemas.py`.
- The Schema Registry enforces **backward compatibility** by default (new fields must have defaults).
- The Flink Table API jobs consume topics using the `avro-confluent` format, which resolves schemas from the registry at job start.
- The `kda-dependencies-1.20.0.jar` (built via `container/flink/pom.xml`) bundles `flink-sql-connector-kafka` and `flink-sql-avro-confluent-registry`.

Topic naming convention: `Canonical<Domain><Entity>` (e.g. `CanonicalSalesforceCrmAppointment`).

## Alternatives considered

| Option | Reason not chosen |
|--------|------------------|
| JSON | No schema enforcement; silently drops/adds fields; 3–5× larger payload than Avro |
| Protobuf | Less mature Confluent Schema Registry support; Java-centric tooling; more complex Python SDK |
| Parquet | A columnar storage format, not a streaming message format |
| Schema-less (raw JSON) | Incompatible with Flink's typed Table API; no compile-time contract |

## Consequences

### Positive
- Avro binary encoding is 2–5× smaller than JSON — reduces Kafka storage and network cost.
- Schema Registry acts as a contract between producer and consumer; breaking changes are rejected at publish time.
- Conduktor UI displays field names and types natively for Avro topics.
- Schema evolution (adding nullable fields) is backward compatible with no consumer code changes.

### Negative / trade-offs
- Schemas must be registered before the first message is produced; `schema-registry-init` is a startup dependency.
- The `avro-confluent` Flink format requires the Confluent JAR (`flink-sql-avro-confluent-registry`) — this is not bundled in the base Flink image.
- Schema Registry adds a network round-trip per schema fetch (mitigated by client-side caching).

### Neutral / constraints
- Each Avro schema file maps 1:1 to a canonical topic (`<file>.avsc` → `Canonical<Name>-value` subject).
- Local development uses the same Schema Registry API as production MSK Schema Registry; no code changes needed between environments.
