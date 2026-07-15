# ADR-003: Apache Flink for Canonical Stream Processing

## Status

Accepted

## Context

The platform needs to transform 15 canonical Avro topics (one per operational source entity) into approximately 50 PDM Sink topics (one per MySQL ODS table). Each transformation applies field mapping, type casting, and domain-specific business logic (e.g. extracting slot reservations from appointment payloads). The processing must be stateless, independently deployable, and observable via a web dashboard.

## Decision

Use **Apache Flink 1.20** with the **PyFlink Table API** for all canonical → PDM Sink topic transformations. Each of the 14 transformations is a self-contained Python module under `data_platform/flink_job/<domain>/`, with an entry point at `main.py`.

Architecture:
- **Flink standalone cluster** (one JobManager, one TaskManager with 14 task slots) runs locally via Docker Compose; AWS Managed Flink (KDA) in production.
- Each job reads from a canonical Avro topic via `avro-confluent` source table and writes to one or more `Sink*` topics via `avro-confluent` or JSON sink tables.
- Jobs are submitted via `data_platform/flink_job/start_flink_job.sh <name>` or `start_flink_job_all.py`.
- The connector fat JAR (`kda-dependencies-1.20.0.jar`) is built from `container/flink/pom.xml` and pre-loaded into `/opt/flink/lib/` in the Docker image.
- Job configuration (bootstrap servers, schema registry URL, topic names) is read from `application_properties_docker.json` / `application_properties_local.json`.

## Alternatives considered

| Option | Reason not chosen |
|--------|------------------|
| Kafka Streams (Java) | No Python support; requires Java expertise across the team |
| Spark Structured Streaming | Higher latency (micro-batch); overkill for stateless field mapping |
| Kafka Connect SMT (Single Message Transform) | Limited transformation expressiveness; no Python; no SQL aggregations |
| Custom consumer loop (Python + kafka-python) | No fault tolerance, checkpointing, or backpressure; manual offset management |
| dbt + Airflow (batch) | Adds minutes of latency; not real-time |

## Consequences

### Positive
- Flink provides exactly-once delivery semantics with Kafka offsets stored as checkpoints.
- PyFlink Table API enables SQL-like transformations without Java, keeping the team in a single language.
- The Flink Web Dashboard (:8082) shows running jobs, task graphs, checkpoints, and backpressure.
- Each job is independently deployable — adding a new domain requires one new `main.py` with no changes to existing jobs.
- Flink's built-in parallelism handles burst loads without manual scaling.

### Negative / trade-offs
- PyFlink builds require Python 3.11 (not 3.12) due to apache-flink's CPython ABI dependency — this is pinned in `container/flink/Dockerfile`.
- The Flink Docker image is large (~3 GB) due to the embedded JVM and PyFlink wheel.
- Job submission requires the cluster to be healthy first (`flink-jobmanager` must pass its health check).

### Neutral / constraints
- The connector JAR must be built via `make flink-jar` (Maven) before the Docker image is built — the JAR is not downloaded at Docker build time.
- Task slot count (`taskmanager.numberOfTaskSlots: 14`) must match the number of jobs to run them all concurrently.
