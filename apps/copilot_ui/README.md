# Copilot UI Module

## Target Status Alignment

This module should implement the user-facing experience for `agentic-operational-intelligence-platform`.

## Recommended Implementation

- React or Next.js chat interface with SSE streaming support
- Store Manager dashboard widgets (real-time KPI cards, alert timeline)
- Executive rollup cards (regional KPI variance, cross-store prioritization)
- Promotion recommendation panel with A/B experiment results
- Image upload for multimodal KPI chart analysis

## API Integration Priority

Implement these API flows in order:

1. `POST /ask/stream` for real-time SSE streaming Q&A (progressive token display).
2. `POST /operations/brief` for persona-specific operational readouts.
3. `POST /ask` for standard agentic Q&A with intent routing and DAG execution.
4. `POST /ask/agentic` for tool-calling agentic queries with skill invocation.
5. `POST /kpi/enriched` for KPIs with semantic metadata and anomaly flags.
6. `GET /kpi/catalog` for KPI definitions (drive dashboard card generation).
7. `GET /alerts/{store_id}` for alert timelines.

## Authentication

All API requests require an `X-API-Key` header (unless `AOIP_AUTH_DISABLED=true` is set for development). The UI should store the API key securely and include it in all requests.

Roles: `admin` (full access), `operator` (query + operations), `viewer` (read-only KPI/alerts).
3. `POST /kpi` and `GET /alerts/{store_id}` for drill-down support widgets.
