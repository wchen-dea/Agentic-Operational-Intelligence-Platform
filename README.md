# Agentic Operational Intelligence Platform

Production-shaped AI operations platform for store managers and executives to monitor real-time KPI and alert signals, diagnose root causes, and adjust commercial and operational strategies.

## Project Target Status

Current target status: `agentic-operational-intelligence-platform`

This repository is currently aligned to this target with:

- Agent orchestration for KPI analysis, anomaly detection, promotion reasoning, and recommendation generation
- Persona-aware responses for store managers and executives
- Real-time KPI coverage across sales orders, appointments, POS invoices, inventory, and work orders
- AWS Aurora MySQL as the operational source system for sales orders, appointments, POS invoices, and work orders
- Operational strategy outputs for under-performing store diagnosis, branded upsell, and promotion adjustment

## Glossary

- Agentic Operational Intelligence Platform: Canonical product name for this repository and runtime system.
- agentic-operational-intelligence-platform: Canonical package/release identifier used in project metadata.
- Agentic Operational Intelligence Orchestrator: Canonical orchestration component that coordinates KPI, anomaly, promotion, and recommendation agents.
- Store manager persona: User role focused on local, real-time operational diagnosis and execution.
- Executive persona: User role focused on regional and enterprise KPI variance, prioritization, and strategy shifts.
- Operational brief: Persona-aware summary that combines KPI state, active alerts, diagnosis, and priority actions.
- KPI: Key Performance Indicator generated from real-time events across sales orders, appointments, POS invoices, inventory, and work orders.
- AWS Aurora MySQL: System of record for transactional sales-order, appointment, POS-invoice, and work-order applications feeding the real-time KPI pipeline.
- CDC topic naming convention: Kafka/MSK topics follow `retail_ops.aurora.<schema>.<table>`.
- Bronze table naming convention: Landed CDC records follow `bronze.<table>_cdc`.
- Silver table naming convention: Normalized operational tables follow `silver.<table>`.

## Current Capabilities

- FastAPI service with `/ask`, `/kpi`, `/alerts`, and `/operations/brief` endpoints
- Agentic operational intelligence orchestrator with KPI, anomaly, promotion, and recommendation agents
- Lightweight hybrid RAG implementation using local JSONL documents
- Streaming KPI aggregator logic with cross-domain operational metrics
- Source-system assumption that sales orders, appointments, POS invoices, and work orders originate from AWS Aurora MySQL
- Aurora MySQL and CDC connection placeholders in `config/source_connections.example.yaml` and `config/settings.py`
- Bronze, silver, and gold Databricks ingestion assets for Aurora MySQL modeling
- Databricks PySpark notebook for bronze-to-silver normalization in `data_platform/batch/databricks/notebooks/bronze_to_silver_aurora_domains.ipynb`
- Sample AWS DMS to Kafka/MSK CDC task spec in `config/cdc/aws_dms_aurora_to_msk_task.example.json`
- Sample alert rules in YAML
- Sample schemas for sales orders, appointments, POS invoices, and work orders
- Unit tests for KPI and agent flows

## Source Systems

The current project target assumes the following operating model:

- AWS Aurora MySQL stores transactional data for the sales order system, appointment application, POS invoice activities, and work order activities.
- Inventory signals may be sourced from Aurora MySQL or a downstream inventory service, but are modeled as part of the same operational KPI layer.
- Change data capture from Aurora MySQL should feed the real-time event stream that drives KPI aggregation, anomaly detection, and executive/store-manager alerts.

CDC naming conventions used by the reference assets:

- Kafka/MSK topic: `retail_ops.aurora.<schema>.<table>`
- Bronze landing table: `bronze.<table>_cdc`
- Silver normalized table: `silver.<table>`
- Gold KPI rollup table: `gold.store_realtime_kpis`

## AI Operational Intelligence Focus

This project is designed for two decision personas:

- Store managers: real-time diagnosis for local under-performance, inventory constraints, service backlog, and conversion blockers.
- Company executives: regional KPI variance monitoring, cross-store prioritization, and strategy shifts for promotion and margin improvement.

The AI layer combines KPI signals and alerts across:

- Sales order system on AWS Aurora MySQL
- Appointment application on AWS Aurora MySQL
- POS invoice activities on AWS Aurora MySQL
- Inventory health signals
- Work order activities on AWS Aurora MySQL

The resulting recommendations help teams:

- Diagnose under-performing stores quickly
- Increase branded upsell mix using targeted scripts and bundles
- Adjust store-level promotions based on inventory and operations readiness
- Improve execution quality before scaling campaign spend

## Quick start

```bash
uv sync --dev
uv run uvicorn services.api.app:app --reload --port 8000
```

### Generate persona-aware operational brief

```bash
curl -X POST http://localhost:8000/operations/brief \
  -H "Content-Type: application/json" \
  -d '{"store_id":"245","region":"Phoenix","persona":"executive"}'
```

Then try:

```bash
curl -X POST http://localhost:8000/ask \
  -H "Content-Type: application/json" \
  -d '{"question":"Why are Phoenix sales down today and what promotion should we adjust?","store_id":"245","region":"Phoenix"}'
```

## Repo Layout

```text
ai_layer/        RAG, agents, prompts, memory, evaluation
config/          runtime settings and Aurora MySQL / CDC placeholders
services/        API and runtime processors
data_platform/   schemas, streaming jobs, Databricks SQL placeholders
alerts/          alert rule definitions and dispatch channels
observability/   metrics and dashboard placeholders
tests/           unit tests
```

## Design Intent

The project is intentionally implementation-ready and extensible. Replace in-memory/local components with enterprise services as you scale:

- AWS DMS, Debezium, or application CDC from Aurora MySQL into Kafka/MSK for real-time topics
- AWS Managed Service for Apache Flink or Databricks Structured Streaming for KPI computation
- Delta Lake for bronze/silver/gold KPI tables
- Databricks Vector Search, OpenSearch, Azure AI Search, or pgvector for vector retrieval
- Teams/Jira/ServiceNow for alert and incident workflow integration
