# ADR-006: uv for Python Dependency Management

## Status

Accepted

## Context

The project needs fast, deterministic dependency resolution and a single tool for virtual environment management, locking, and script execution. pip + venv is slow and lacks a lockfile; Poetry adds complexity.

## Decision

Use [uv](https://docs.astral.sh/uv/) as the sole Python project and dependency manager.

- `pyproject.toml` declares dependencies (PEP 621).
- `uv.lock` provides deterministic resolution.
- `uv sync --dev` replaces `pip install -r requirements.txt`.
- `uv run` replaces `python -m` or venv activation for script execution.
- `package = false` in `[tool.uv]` since this is an application, not a library.

## Consequences

- Developers need `uv` installed (single binary, no Python bootstrap required).
- Lock resolution is 10-100x faster than pip/Poetry.
- Docker builds use `COPY --from=ghcr.io/astral-sh/uv:latest` for zero-install in CI.
- No `requirements.txt` to maintain; dependencies live solely in `pyproject.toml`.
