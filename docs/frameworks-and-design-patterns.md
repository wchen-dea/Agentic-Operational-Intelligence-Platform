# Frameworks and Design Patterns

This document lists the key frameworks/technologies and software design patterns used in the project, with concrete code locations.

## Frameworks and technologies

| Area                            | Framework / Technology           | Purpose in this project                                         | Main locations                                                                      |
| ------------------------------- | -------------------------------- | --------------------------------------------------------------- | ----------------------------------------------------------------------------------- |
| API layer                       | FastAPI + Uvicorn                | REST API, SSE streaming endpoints, auth-protected operations    | `ai_systems/gateway/api/app.py`, `ai_systems/gateway/api/routes/`                   |
| Validation and config           | Pydantic + pydantic-settings     | Typed config and request/response validation                    | `ai_systems/config/settings.py`, `ai_systems/gateway/api/models.py`                 |
| LLM integration                 | Anthropic Python SDK             | Text generation, tool-calling, streaming, vision                | `ai_systems/core/llm.py`                                                            |
| Tool protocol                   | MCP                              | Exposes AI tools for external tool consumers                    | `ai_systems/gateway/mcp/server.py`                                                  |
| Retrieval                       | ChromaDB + scikit-learn TF-IDF   | Hybrid semantic + sparse retrieval with fusion                  | `ai_systems/retrieval/hybrid_search.py`                                             |
| Cache and state                 | Redis                            | Streaming state and session-oriented data in distributed setups | `ai_systems/retrieval/context.py`, `ai_systems/config/settings.py`                  |
| Metrics                         | Prometheus client                | Metrics export and runtime counters/histograms                  | `observability/evaluation.py`, `ai_systems/gateway/api/app.py`                      |
| Tracing                         | OpenTelemetry                    | Optional distributed tracing for API paths                      | `observability/tracing.py`, `ai_systems/gateway/api/app.py`                         |
| Streaming backbone              | Apache Kafka + Schema Registry   | Canonical and sink topic transport with Avro schemas            | `data_platform/producer/`, `data_platform/schema/`, `container/docker-compose.yaml` |
| Stream processing               | Apache Flink (PyFlink Table API) | Canonical to sink topic transformations (14 jobs)               | `data_platform/flink_job/`                                                          |
| ODS sink                        | Kafka Connect JDBC Sink          | Writes sink topics into MySQL ODS tables                        | `container/scripts/register_connectors.py`                                          |
| CDC                             | Debezium                         | Captures MySQL ODS changes to Kafka CDC topics                  | `container/scripts/register_cdc_connector.py`                                       |
| Lakehouse ingest                | Spark Structured Streaming       | CDC to Iceberg landing ingestion                                | `data_platform/spark/cdc_to_landing.py`                                             |
| Transformations                 | dbt Core + MetricFlow            | Medallion modeling and semantic metric layer                    | `data_platform/dbt/`                                                                |
| Orchestration                   | Apache Airflow                   | Scheduled dbt pipeline execution                                | `container/airflow/dags/`                                                           |
| Table format and object storage | Apache Iceberg + MinIO           | Open table format with local object-store lakehouse             | `data_platform/dbt/models/`, `container/docker-compose.yaml`                        |
| Feature serving                 | Feast                            | Offline/online feature definitions and materialization          | `data_platform/feature_store/`                                                      |
| Vector index                    | Qdrant                           | KPI narrative and metric-definition vector indexing             | `data_platform/vector_index/`                                                       |
| Graph store                     | Neo4j                            | Store relationship graph and gold KPI snapshot projection       | `data_platform/graph/`                                                              |
| Testing and quality             | Pytest, Ruff, Pyright            | Tests, linting, and static type checking                        | `tests/`, `pyproject.toml`                                                          |
| Packaging and env               | uv + Docker Compose              | Python dependency/workflow management and local infra stack     | `pyproject.toml`, `compose.yaml`, `container/docker-compose.yaml`                   |

## Design patterns in use

| Pattern                            | How it is used                                                                                                       | Primary code references                                                       |
| ---------------------------------- | -------------------------------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------- |
| Registry pattern                   | Skills are registered and invoked by name through a central registry that also exports tool schemas                  | `ai_systems/skills.py`, `ai_systems/tools/registry.py`                        |
| Singleton pattern                  | Process-wide singleton instances are created for shared registries/orchestrator objects                              | `ai_systems/tools/registry.py`, `ai_systems/orchestration/orchestrator.py`    |
| Strategy pattern                   | Model selection strategy varies by task complexity and runtime model health                                          | `ai_systems/core/model_router.py`                                             |
| Factory pattern                    | Streaming store factory selects Redis-backed or in-process implementation from config                                | `ai_systems/retrieval/context.py`                                             |
| Circuit breaker                    | Per-node circuit breaker prevents repeated execution against failing DAG nodes                                       | `ai_systems/orchestration/executor.py`                                        |
| Retry with exponential backoff     | Node-level retry policy applies bounded retries with progressive delays                                              | `ai_systems/orchestration/dag.py`, `ai_systems/orchestration/executor.py`     |
| Fallback pattern                   | Node and model fallbacks provide degraded but available behavior when dependencies fail                              | `ai_systems/orchestration/executor.py`, `ai_systems/core/model_router.py`     |
| DAG / pipeline orchestration       | Agent execution graph is represented as explicit nodes with dependency tiers                                         | `ai_systems/orchestration/dag.py`, `ai_systems/orchestration/orchestrator.py` |
| Two-phase classification           | Fast regex classification followed by LLM fallback for ambiguous intent routing                                      | `ai_systems/orchestration/router.py`                                          |
| Facade pattern                     | Orchestrator exposes a simplified answer API while coordinating routing, context assembly, DAG execution, and memory | `ai_systems/orchestration/orchestrator.py`                                    |
| Dependency inversion via protocols | Session memory behavior is defined by protocol and consumed by assembler independently of concrete backend           | `ai_systems/retrieval/context.py`                                             |

## Notes

- Pattern names are used in the practical engineering sense based on current implementation.
- This document should be updated when core orchestration, retrieval, or infra components change.

## Terminology Glossary

Use canonical definitions from [Terminology Glossary](terminology-glossary.md) when describing platform components, data layers, and AI workflows.

## Structural Formatting Standard

This document follows the shared [Markdown Structure Standard](markdown-structure-standard.md) for heading hierarchy, section order, procedure formatting, and link conventions.
