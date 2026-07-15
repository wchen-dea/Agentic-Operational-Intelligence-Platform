# Architecture Decision Records

Key architectural decisions for the Agentic Operational Intelligence Platform, ordered by pipeline stage.

See the architecture documents for full context:
- [Data Platform](../architecture_data_platform.md)
- [AI Systems](../architecture_ai_systems.md)
- [Local Development](../architecture_local.md)
- [Kubernetes / Production](../architecture_amazon_eks.md)
- [System Overview](../system_overview.md)

## Data Platform (Stages 1–7)

| ADR | Title | Status |
|-----|-------|--------|
| [001](001-aurora-mysql-as-source-system.md) | Aurora MySQL as Operational Source System | Accepted |
| [002](002-canonical-avro-messaging-schema-registry.md) | Canonical Avro Messaging with Confluent Schema Registry | Accepted |
| [003](003-flink-for-canonical-stream-processing.md) | Apache Flink for Canonical Stream Processing | Accepted |
| [004](004-kafka-connect-jdbc-sink-mysql-ods.md) | Kafka Connect JDBC Sink for MySQL ODS Write | Accepted |
| [005](005-debezium-cdc-mysql-ods-to-kafka.md) | Debezium CDC from MySQL ODS to Kafka | Accepted |
| [006](006-spark-structured-streaming-iceberg-landing.md) | Apache Spark Structured Streaming for Iceberg Landing Layer | Accepted |
| [007](007-apache-iceberg-as-lakehouse-table-format.md) | Apache Iceberg as Lakehouse Table Format | Accepted |
| [008](008-medallion-lakehouse-dbt-core.md) | Medallion Lakehouse Transformations with dbt Core | Accepted |
| [009](009-apache-airflow-dbt-orchestration.md) | Apache Airflow for dbt Pipeline Orchestration | Accepted |
| [010](010-analytics-ml-llm-layer.md) | Analytics/ML/LLM Layer Architecture | Accepted |

## AI Systems (Stage 4)

| ADR | Title | Status |
|-----|-------|--------|
| [011](011-anthropic-claude-as-llm.md) | Anthropic Claude as LLM Provider | Accepted |
| [012](012-fastapi-platform-api.md) | FastAPI for the Platform API Layer | Accepted |
| [013](013-persona-aware-orchestration.md) | Persona-Aware Agent Orchestration | Accepted |
| [014](014-dag-orchestration-intent-routing.md) | DAG-Based Agent Orchestration with Intent Routing | Accepted |
| [015](015-agent-skill-framework.md) | Agent Skill Framework for Composable Capabilities | Accepted |
| [016](016-hybrid-context-assembly.md) | Hybrid Context Assembly (Streaming + Vector + Memory) | Accepted |
| [017](017-llmops-prompt-versioning.md) | LLMOps — Prompt Versioning and A/B Experimentation | Accepted |
| [018](018-token-cost-efficiency.md) | Token Cost-Efficiency and LLM Usage Tracking | Accepted |

## Observability and Infrastructure

| ADR | Title | Status |
|-----|-------|--------|
| [019](019-observability-llm-evaluation.md) | Observability and LLM Evaluation Framework | Accepted |
| [020](020-api-key-authentication-rbac.md) | API Key Authentication with RBAC | Accepted |
| [021](021-mcp-server-tool-integration.md) | Model Context Protocol Server for External Tool Integration | Accepted |
| [022](022-uv-python-dependency-management.md) | uv for Python Dependency Management | Accepted |


## Index

| ADR | Title | Status |
|-----|-------|--------|
| [001](001-aurora-mysql-as-source-system.md) | Aurora MySQL as operational source system | Accepted |
| [002](002-anthropic-claude-as-llm.md) | Anthropic Claude as LLM provider | Accepted |
| [003](003-cdc-to-kafka-msk-ingestion.md) | CDC to Kafka/MSK for real-time ingestion | Accepted |
| [004](004-medallion-lakehouse-architecture.md) | Medallion lakehouse (bronze/silver/gold) | Accepted |
| [005](005-persona-aware-agent-orchestration.md) | Persona-aware agent orchestration | Accepted |
| [006](006-uv-for-dependency-management.md) | uv for Python dependency management | Accepted |
| [007](007-agent-skill-framework.md) | Agent skill framework for composable capabilities | Accepted |
| [008](008-dag-orchestration-with-intent-routing.md) | DAG-based orchestration with intent routing | Accepted |
| [009](009-hybrid-context-assembly.md) | Hybrid context assembly (streaming + vector + memory) | Accepted |
| [010](010-observability-and-evaluation.md) | Observability and LLM evaluation framework | Accepted |
| [011](011-llmops-prompt-versioning.md) | LLMOps prompt versioning and lifecycle | Accepted |
| [012](012-token-cost-efficiency.md) | Token cost-efficiency and LLM usage tracking | Accepted |
