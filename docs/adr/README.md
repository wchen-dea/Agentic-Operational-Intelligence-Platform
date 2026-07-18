# Architecture Decision Records

Key architectural decisions for the Agentic Operational Intelligence Platform, organized by functionality group.

See the architecture documents for full context:

- [Data Platform](../architecture-data-platform.md)
- [AI Systems](../architecture-ai-systems.md)
- [Local Development](../architecture-local.md)
- [Kubernetes / Production](../architecture-amazon-eks.md)
- [System Overview](../system-overview.md)

## Foundations and Standards

| Order | ADR                                                    | Title                                                   | Status   |
| ----- | ------------------------------------------------------ | ------------------------------------------------------- | -------- |
| 1     | [001](001-enterprise-source-integration-and-aurora-boundary.md) | Enterprise Source Integration Layer and Aurora Operational Boundary | Accepted |
| 2     | [002](002-canonical-avro-messaging-schema-registry.md) | Canonical Avro Messaging with Confluent Schema Registry | Accepted |
| 3     | [003](003-apache-iceberg-as-lakehouse-table-format.md) | Apache Iceberg as Lakehouse Table Format                | Accepted |
| 4     | [004](004-uv-python-dependency-management.md)          | uv for Python Dependency Management                     | Accepted |
| 5     | [005](005-documentation-governance-and-standards.md)   | Documentation Governance and Standards                  | Accepted |

## Data Pipeline Execution

| Order | ADR                                                    | Title                                                       | Status   |
| ----- | ------------------------------------------------------ | ----------------------------------------------------------- | -------- |
| 6     | [006](006-flink-for-canonical-stream-processing.md)    | Apache Flink for Canonical Stream Processing                | Accepted |
| 7     | [007](007-kafka-connect-jdbc-sink-mysql-ods.md)        | Kafka Connect JDBC Sink for MySQL ODS Write                 | Accepted |
| 8     | [008](008-debezium-cdc-mysql-ods-to-kafka.md)          | Debezium CDC from MySQL ODS to Kafka                        | Accepted |
| 9     | [009](009-spark-structured-streaming-iceberg-landing.md) | Apache Spark Structured Streaming for Iceberg Landing Layer | Accepted |
| 10    | [010](010-medallion-lakehouse-dbt-core.md)             | Medallion Lakehouse Transformations with dbt Core           | Accepted |
| 11    | [011](011-apache-airflow-dbt-orchestration.md)         | Apache Airflow for dbt Pipeline Orchestration               | Accepted |

## Analytics and Graph Projections

| Order | ADR                                         | Title                                                      | Status   |
| ----- | ------------------------------------------- | ---------------------------------------------------------- | -------- |
| 12    | [012](012-analytics-ml-llm-layer.md)        | Analytics/ML/LLM Layer Architecture                        | Accepted |
| 13    | [013](013-neo4j-graph-projection-layer.md)  | Neo4j Graph Projection Layer for Operational Relationships | Accepted |

## AI Platform and Orchestration

| Order | ADR                                          | Title                                                 | Status   |
| ----- | -------------------------------------------- | ----------------------------------------------------- | -------- |
| 14    | [014](014-fastapi-platform-api.md)           | FastAPI for the Platform API Layer                    | Accepted |
| 15    | [015](015-anthropic-claude-as-llm.md)        | Anthropic Claude as LLM Provider                      | Accepted |
| 16    | [016](016-persona-aware-orchestration.md)    | Persona-Aware Agent Orchestration                     | Accepted |
| 17    | [017](017-dag-orchestration-intent-routing.md) | DAG-Based Agent Orchestration with Intent Routing     | Accepted |
| 18    | [018](018-agent-skill-framework.md)          | Agent Skill Framework for Composable Capabilities     | Accepted |
| 19    | [019](019-hybrid-context-assembly.md)        | Hybrid Context Assembly (Streaming + Vector + Memory) | Accepted |
| 20    | [020](020-llmops-prompt-versioning.md)       | LLMOps — Prompt Versioning and A/B Experimentation    | Accepted |
| 21    | [021](021-token-cost-efficiency.md)          | Token Cost-Efficiency and LLM Usage Tracking          | Accepted |

## Operations and Access Interfaces

| Order | ADR                                         | Title                                                       | Status   |
| ----- | ------------------------------------------- | ----------------------------------------------------------- | -------- |
| 22    | [022](022-observability-llm-evaluation.md)  | Observability and LLM Evaluation Framework                  | Accepted |
| 23    | [023](023-api-key-authentication-rbac.md)   | API Key Authentication with RBAC                            | Accepted |
| 24    | [024](024-mcp-server-tool-integration.md)   | Model Context Protocol Server for External Tool Integration | Accepted |

## Index

### Foundations and Standards

| Order | ADR                                               | Title                                                   | Status   |
| ----- | ------------------------------------------------- | ------------------------------------------------------- | -------- |
| 1     | [001](001-enterprise-source-integration-and-aurora-boundary.md) | Enterprise Source Integration Layer and Aurora Operational Boundary | Accepted |
| 2     | [002](002-canonical-avro-messaging-schema-registry.md) | Canonical Avro Messaging with Confluent Schema Registry | Accepted |
| 3     | [003](003-apache-iceberg-as-lakehouse-table-format.md) | Apache Iceberg as Lakehouse Table Format                | Accepted |
| 4     | [004](004-uv-python-dependency-management.md)     | uv for Python Dependency Management                     | Accepted |
| 5     | [005](005-documentation-governance-and-standards.md) | Documentation Governance and Standards                  | Accepted |

### Data Pipeline Execution

| Order | ADR                                               | Title                                                       | Status   |
| ----- | ------------------------------------------------- | ----------------------------------------------------------- | -------- |
| 6     | [006](006-flink-for-canonical-stream-processing.md) | Apache Flink for Canonical Stream Processing                | Accepted |
| 7     | [007](007-kafka-connect-jdbc-sink-mysql-ods.md)   | Kafka Connect JDBC Sink for MySQL ODS Write                 | Accepted |
| 8     | [008](008-debezium-cdc-mysql-ods-to-kafka.md)     | Debezium CDC from MySQL ODS to Kafka                        | Accepted |
| 9     | [009](009-spark-structured-streaming-iceberg-landing.md) | Apache Spark Structured Streaming for Iceberg Landing Layer | Accepted |
| 10    | [010](010-medallion-lakehouse-dbt-core.md)        | Medallion Lakehouse Transformations with dbt Core           | Accepted |
| 11    | [011](011-apache-airflow-dbt-orchestration.md)    | Apache Airflow for dbt Pipeline Orchestration               | Accepted |

### Analytics and Graph Projections

| Order | ADR                                               | Title                                                      | Status   |
| ----- | ------------------------------------------------- | ---------------------------------------------------------- | -------- |
| 12    | [012](012-analytics-ml-llm-layer.md)              | Analytics/ML/LLM Layer Architecture                        | Accepted |
| 13    | [013](013-neo4j-graph-projection-layer.md)        | Neo4j Graph Projection Layer for Operational Relationships | Accepted |

### AI Platform and Orchestration

| Order | ADR                                               | Title                                                 | Status   |
| ----- | ------------------------------------------------- | ----------------------------------------------------- | -------- |
| 14    | [014](014-fastapi-platform-api.md)                | FastAPI for the Platform API Layer                    | Accepted |
| 15    | [015](015-anthropic-claude-as-llm.md)             | Anthropic Claude as LLM Provider                      | Accepted |
| 16    | [016](016-persona-aware-orchestration.md)         | Persona-Aware Agent Orchestration                     | Accepted |
| 17    | [017](017-dag-orchestration-intent-routing.md)    | DAG-Based Agent Orchestration with Intent Routing     | Accepted |
| 18    | [018](018-agent-skill-framework.md)               | Agent Skill Framework for Composable Capabilities     | Accepted |
| 19    | [019](019-hybrid-context-assembly.md)             | Hybrid Context Assembly (Streaming + Vector + Memory) | Accepted |
| 20    | [020](020-llmops-prompt-versioning.md)            | LLMOps — Prompt Versioning and A/B Experimentation    | Accepted |
| 21    | [021](021-token-cost-efficiency.md)               | Token Cost-Efficiency and LLM Usage Tracking          | Accepted |

### Operations and Access Interfaces

| Order | ADR                                               | Title                                                       | Status   |
| ----- | ------------------------------------------------- | ----------------------------------------------------------- | -------- |
| 22    | [022](022-observability-llm-evaluation.md)        | Observability and LLM Evaluation Framework                  | Accepted |
| 23    | [023](023-api-key-authentication-rbac.md)         | API Key Authentication with RBAC                            | Accepted |
| 24    | [024](024-mcp-server-tool-integration.md)         | Model Context Protocol (MCP) Server for External Tool Integration | Accepted |

## Terminology Glossary

Use canonical definitions from [Terminology Glossary](../terminology-glossary.md) when describing platform components, data layers, and AI workflows.

## Structural Formatting Standard

This document follows the shared [Markdown Structure Standard](../markdown-structure-standard.md) for heading hierarchy, section order, procedure formatting, and link conventions.
