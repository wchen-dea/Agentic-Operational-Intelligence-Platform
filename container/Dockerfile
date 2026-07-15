FROM python:3.12-slim

COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /usr/local/bin/

WORKDIR /app

# Install production + streaming dependencies into a deterministic venv
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev --group streaming

# Copy application source
COPY . .

# Create a non-root user and hand ownership over
RUN addgroup --system --gid 1001 appgroup \
 && adduser  --system --uid 1001 --gid 1001 --no-create-home appuser \
 && chown -R appuser:appgroup /app

USER appuser

EXPOSE 8000

# Health-check uses stdlib only — no extra curl dependency required
HEALTHCHECK --interval=30s --timeout=5s --start-period=20s --retries=3 \
    CMD python -c \
        "import urllib.request, sys; \
         r=urllib.request.urlopen('http://localhost:8000/health',timeout=4); \
         sys.exit(0 if r.status==200 else 1)"

CMD ["/app/.venv/bin/uvicorn", "ai_systems.gateway.api.app:app", "--host", "0.0.0.0", "--port", "8000"]
