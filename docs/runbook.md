# Runbook

## Prerequisites

- Python 3.12+
- [uv](https://docs.astral.sh/uv/) installed
- (Optional) Docker for containerized dev
- (Optional) `ANTHROPIC_API_KEY` in `.env` for LLM-enhanced output

## Local Development

```bash
# Install dependencies (including dev tools: pytest, pyright, ruff)
uv sync --dev

# Run the API server
uv run uvicorn services.api.app:app --reload --port 8000

# Run tests
uv run pytest -q

# Type checking
uv run pyright

# Linting
uv run ruff check .
```

## Docker Development

```bash
# From project root
docker compose -f container/docker-compose.yaml up --build
```

The app will be available at `http://localhost:8000` with hot-reload via bind mount.

## MCP Server

```bash
# Run the Model Context Protocol server (for Claude Desktop, VS Code Copilot, etc.)
uv run python -m services.mcp_server
```

## Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `ANTHROPIC_API_KEY` | No | Enables LLM-generated narrative briefs. Without it, structured template output is returned. |
| `AOIP_AUTH_DISABLED` | No | Set to `true` to bypass API key authentication in development. |
| `AOIP_API_KEY_ADMIN` | No | Register an admin API key at startup. |
| `AOIP_API_KEY_OPERATOR` | No | Register an operator API key at startup. |
| `AOIP_API_KEY_VIEWER` | No | Register a viewer API key at startup. |

Create a `.env` file at the project root:

```bash
ANTHROPIC_API_KEY=sk-ant-...
AOIP_AUTH_DISABLED=true
```

## API Quick Reference

### Ask (agentic Q&A)

```bash
curl -X POST http://localhost:8000/ask \
  -H "Content-Type: application/json" \
  -d '{"question":"Why are Phoenix sales down?","store_id":"245","persona":"executive"}'
```

### Streaming Q&A (SSE)

```bash
curl -N -X POST http://localhost:8000/ask/stream \
  -H "Content-Type: application/json" \
  -d '{"question":"Summarize store 245 KPIs","store_id":"245"}'
```

### Agentic Tool-calling Q&A

```bash
curl -X POST http://localhost:8000/ask/agentic \
  -H "Content-Type: application/json" \
  -d '{"question":"What KPIs are breaching thresholds for store 245?","store_id":"245"}'
```

### Operational Brief

```bash
curl -X POST http://localhost:8000/operations/brief \
  -H "Content-Type: application/json" \
  -d '{"store_id":"245","region":"Phoenix","persona":"store_manager"}'
```

### KPIs

```bash
# Standard KPIs
curl -X POST http://localhost:8000/kpi \
  -H "Content-Type: application/json" \
  -d '{"store_id":"245"}'

# Enriched KPIs (with semantic metadata and anomaly flags)
curl -X POST http://localhost:8000/kpi/enriched \
  -H "Content-Type: application/json" \
  -d '{"store_id":"245"}'

# KPI catalog (all 16 definitions)
curl http://localhost:8000/kpi/catalog
```

### Alerts

```bash
curl http://localhost:8000/alerts/245
```

### Skills

```bash
# List all available agent skills
curl http://localhost:8000/skills

# Invoke a skill by name
curl -X POST http://localhost:8000/skills/fetch_kpis/invoke \
  -H "Content-Type: application/json" \
  -d '{"params":{"store_id":"245"}}'
```

### Observability

```bash
# LLM token usage and cost
curl http://localhost:8000/usage

# Prometheus metrics
curl http://localhost:8000/metrics
```

### Health

```bash
curl http://localhost:8000/health
```

## Authentication

When `AOIP_AUTH_DISABLED` is not set to `true`, all endpoints require an API key:

```bash
curl -X POST http://localhost:8000/ask \
  -H "Content-Type: application/json" \
  -H "X-API-Key: your-api-key-here" \
  -d '{"question":"Revenue summary"}'
```

Roles and permissions:

| Role | Access |
|------|--------|
| `admin` | All endpoints including observability |
| `operator` | Query, KPI, alerts, operations, skills, streaming |
| `viewer` | KPI and alerts (read-only) |

## Testing

```bash
uv run pytest -q              # quick (150 tests)
uv run pytest -v              # verbose
uv run pytest --tb=short      # short tracebacks
uv run pytest --cov=ai_layer --cov=services --cov-report=term-missing  # with coverage
```

## CI/CD

The GitHub Actions CI pipeline (`.github/workflows/ci.yml`) runs on every push and PR to `main`:

1. **Lint** — `ruff check .` with GitHub output format
2. **Type check** — `pyright` with basic mode
3. **Tests** — `pytest -q --tb=short`
4. **Coverage** — `pytest --cov` with 60% minimum threshold
5. **Docker** — build image and smoke test on push to main

## Troubleshooting

| Symptom | Fix |
|---------|-----|
| `ModuleNotFoundError` | Run `uv sync --dev` |
| LLM returns structured text instead of narrative | Set `ANTHROPIC_API_KEY` in `.env` |
| Docker build fails | Ensure Docker daemon is running |
| Port 8000 in use | Kill existing process or use `--port 8001` |

## Deployment Notes

- For production, replace in-memory KPI store with Delta Lake / SQL Warehouse queries.
- Configure `config/settings.py` with real Aurora MySQL and MSK endpoints.
- Use AWS Secrets Manager for credentials (referenced by `password_secret_name` in settings).
- Replace `StreamingStateStore` in `ai_layer/context.py` with Redis or Kafka consumer for real-time state.
- Connect `MetricsCollector` in `observability/evaluation.py` to Prometheus, Datadog, or CloudWatch for production dashboards.
- Use `PromptRegistry` version pinning in production to prevent unintended prompt changes.
