# Runbook

## Prerequisites

- Python 3.11+
- [uv](https://docs.astral.sh/uv/) installed
- (Optional) Docker for containerized dev
- (Optional) `ANTHROPIC_API_KEY` in `.env` for LLM-enhanced output

## Local Development

```bash
# Install dependencies
uv sync --dev

# Run the API server
uv run uvicorn services.api.app:app --reload --port 8000

# Run tests
uv run pytest -q
```

## Docker Development

```bash
# From project root
docker compose -f container/docker-compose.yaml up --build
```

The app will be available at `http://localhost:8000` with hot-reload via bind mount.

## Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `ANTHROPIC_API_KEY` | No | Enables LLM-generated narrative briefs. Without it, structured template output is returned. |

Create a `.env` file at the project root:

```bash
ANTHROPIC_API_KEY=sk-ant-...
```

## API Quick Reference

### Ask (agentic Q&A)

```bash
curl -X POST http://localhost:8000/ask \
  -H "Content-Type: application/json" \
  -d '{"question":"Why are Phoenix sales down?","store_id":"245","persona":"executive"}'
```

### Operational Brief

```bash
curl -X POST http://localhost:8000/operations/brief \
  -H "Content-Type: application/json" \
  -d '{"store_id":"245","region":"Phoenix","persona":"store_manager"}'
```

### KPIs

```bash
curl -X POST http://localhost:8000/kpi \
  -H "Content-Type: application/json" \
  -d '{"store_id":"245"}'
```

### Alerts

```bash
curl http://localhost:8000/alerts/245
```

### Health

```bash
curl http://localhost:8000/health
```

## Testing

```bash
uv run pytest -q           # quick
uv run pytest -v           # verbose
uv run pytest --tb=short   # short tracebacks
```

## Troubleshooting

| Symptom | Fix |
|---------|-----|
| `ModuleNotFoundError` | Run `uv sync --dev` |
| LLM returns structured text instead of narrative | Set `ANTHROPIC_API_KEY` in `.env` |
| Docker build fails | Ensure Docker daemon is running |
| Port 8000 in use | Kill existing process or use `--port 8001` |

## Deployment Notes

- For production, replace in-memory KPI store with Delta Lake / SQL Warehouse queries.
- Configure `config/source_connections.example.yaml` with real Aurora MySQL and MSK endpoints.
- Use AWS Secrets Manager for credentials (referenced by `password_secret_name` in settings).
