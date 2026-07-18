# Copilot UI

User-facing interface for the Agentic Operational Intelligence Platform.

## Recommended implementation

- React or Next.js chat interface with SSE streaming support
- Store Manager dashboard: real-time KPI cards, alert timeline, work-order backlog
- Executive dashboard: regional KPI variance, cross-store prioritization
- Promotion panel: A/B experiment results, branded upsell recommendations
- Image upload for multimodal KPI chart analysis (vision API)

## API integration priority

Implement in order:

1. `POST /ask/stream` — real-time SSE streaming Q&A (progressive token display)
2. `POST /operations/brief` — persona-specific operational brief
3. `POST /ask` — standard agentic Q&A with intent routing and DAG execution
4. `POST /ask/agentic` — tool-calling queries with skill invocation
5. `POST /kpi/enriched` — KPIs with semantic metadata and anomaly flags
6. `GET /kpi/catalog` — drive dashboard card generation from KPI definitions
7. `GET /alerts/{store_id}` — alert timelines and active threshold breaches

## Authentication

Include `X-API-Key` in all requests (unless `AOIP_AUTH_DISABLED=true` for dev).

| Role | Access |
|------|--------|
| `admin` | Full access |
| `operator` | Query, KPI, alerts, operations, skills |
| `viewer` | KPI and alerts (read-only) |

## Analytics endpoints (optional)

- `GET http://localhost:6566/get-online-features` — Feast online feature serving for ML-driven widgets
- `GET http://localhost:6333/dashboard` — Qdrant collections for semantic search UI

