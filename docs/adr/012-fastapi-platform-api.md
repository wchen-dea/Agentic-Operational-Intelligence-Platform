# ADR-012: FastAPI for the Platform API Layer

## Status

Accepted

## Context

The AI platform needs a REST API that exposes agentic query endpoints, KPI retrieval, alert dispatch, skill invocation, Prometheus metrics, and streaming (SSE) responses. The API must handle both synchronous and async execution paths, support real-time token streaming, and integrate with a Model Context Protocol (MCP) server for external tool consumers.

## Decision

Use **FastAPI 0.111** as the web framework for the platform API (`services/api/`), served by **Uvicorn** (ASGI).

Key design decisions:
- **7 route modules**: `query` (agentic), `kpi`, `alerts`, `operations`, `skills`, `streaming`, and `health`.
- **SSE streaming** via `sse-starlette` for `/ask/stream` — tokens are flushed incrementally as Claude generates them.
- **API key authentication + RBAC** middleware (admin / operator / viewer roles) applied globally via `HTTPBearer`.
- **Prometheus metrics** exported at `GET /metrics` via `prometheus-client` (Prometheus exposition format).
- **Pydantic models** for all request/response schemas — automatic OpenAPI docs at `/docs`.
- **`on_event("startup")`** initializes the orchestrator, skill registry, context assembler, and alert engine once at boot.

The MCP server (`services/mcp_server.py`) runs as a separate process alongside the FastAPI app, exposing 5 tools, 2 resources, and 2 prompts via the Model Context Protocol.

## Alternatives considered

| Option | Reason not chosen |
|--------|------------------|
| Flask | Synchronous-only without extensions; no built-in async support; no Pydantic integration |
| Django REST Framework | Heavy framework for a microservice; ORM not needed; startup time |
| gRPC | Not browser-friendly; no SSE support; harder to debug and test |
| Starlette (bare) | FastAPI is Starlette + automatic OpenAPI; no reason to use the lower-level API |

## Consequences

### Positive
- FastAPI + Pydantic generates `/docs` (Swagger) and `/redoc` automatically — no manual API documentation.
- Async endpoints handle concurrent LLM calls without blocking the event loop.
- SSE streaming delivers the first token to the client within milliseconds of Claude beginning generation.
- `TestClient` from `starlette.testclient` enables synchronous test execution without a running server.

### Negative / trade-offs
- `on_event("startup")` is deprecated in FastAPI 0.111+ — should migrate to `lifespan` context manager in a future release.
- Global state (orchestrator singleton, skill registry) means the API process is stateful — horizontal scaling requires shared state via Redis.
- Prometheus `prometheus-client` metrics are process-local — in multi-replica deployments, each replica exposes its own metrics (requires Prometheus federation or push gateway).

### Neutral / constraints
- Port 8000 (local) / configurable via `--port` in `make dev`.
- Auth bypass: `AOIP_AUTH_DISABLED=true` skips all authentication — used in tests and development.
