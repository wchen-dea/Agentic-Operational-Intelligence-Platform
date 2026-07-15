# ADR-020: API Key Authentication with RBAC

## Status

Accepted

## Context

The platform API exposes sensitive operational data (KPIs, alerts, agent recommendations) and must control access. Different callers have different authority: a BI dashboard should read KPIs but not trigger agentic operations; an admin should access all endpoints including usage and metrics.

## Decision

Implement **API key authentication** with **three RBAC roles** applied globally via FastAPI middleware (`services/api/auth.py`):

| Role | Access |
|------|--------|
| `admin` | All endpoints including `/usage`, `/metrics`, and all mutation operations |
| `operator` | Query, KPI, alerts, operations, skills, and streaming endpoints |
| `viewer` | KPI and alerts (read-only) |

Implementation details:
- API keys are passed via `X-API-Key` header.
- Keys are stored as SHA-256 hashes in the auth module — never in plaintext.
- Keys are registered at startup via environment variables: `AOIP_API_KEY_ADMIN`, `AOIP_API_KEY_OPERATOR`, `AOIP_API_KEY_VIEWER`.
- **Per-key sliding-window rate limiting** — configurable requests-per-minute; returns HTTP 429 on violation.
- Auth bypass: `AOIP_AUTH_DISABLED=true` skips all authentication (dev/test only).

## Alternatives considered

| Option | Reason not chosen |
|--------|------------------|
| OAuth2 / JWT | Adds authorization server dependency; overkill for API-to-API consumption |
| mTLS | Complex certificate management; not browser-friendly |
| IP allowlisting | Fragile in cloud/container environments; not scalable |
| No authentication | Unacceptable for operational data exposure |

## Consequences

### Positive
- `AOIP_AUTH_DISABLED=true` enables frictionless local development and CI testing without key management.
- SHA-256 key hashing ensures that even if the auth module is compromised, plaintext keys are not exposed.
- Rate limiting protects against runaway clients and cost overruns from LLM-heavy endpoints.
- RBAC allows giving BI tools `viewer` access without exposing agentic endpoints.

### Negative / trade-offs
- Key rotation requires updating environment variables and restarting the API — no hot-swap without a shared key store.
- In-memory rate limiting is per-process — in horizontal scaling, limits are not enforced across replicas (requires Redis-backed rate limiter).

### Neutral / constraints
- Auth metrics (`auth_requests_total`, `auth_rejected_total`, `rate_limit_exceeded_total`) are emitted to `MetricsCollector` on every request.
- The auth layer is the outermost middleware — unauthenticated requests never reach routing or agents.
