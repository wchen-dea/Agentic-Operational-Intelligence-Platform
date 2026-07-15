# ADR-022: uv for Python Dependency Management

## Status

Accepted

## Context

The platform has a complex Python dependency graph spanning four dependency groups (base, dev, streaming, observability) across Python 3.12. Reproducible builds are critical for CI/CD (identical environments between developer machines and GitHub Actions runners) and Docker image builds.

## Decision

Use **[uv](https://docs.astral.sh/uv/)** (Astral) as the sole Python project manager and dependency resolver.

Key choices:
- `pyproject.toml` declares all dependencies and project metadata.
- `uv.lock` provides a complete, deterministic lock file (includes transitive dependencies with exact hashes).
- Docker builds use `uv sync --frozen` — fails if lock file is out of date.
- CI uses `uv sync --frozen --dev` — same lock file, reproducible across runners.
- Dependency groups isolate heavy extras:
  - `streaming` — `confluent-kafka`, `fastavro`, `authlib` (only needed for producer/consumer code)
  - `observability` — OTel SDK packages (optional, not required for core functionality)

```toml
[tool.uv]
package = false
```

`package = false` disables uv's package build mode — this is a scripts/services project, not a distributed package.

## Alternatives considered

| Option | Reason not chosen |
|--------|------------------|
| pip + requirements.txt | No lock file for transitive dependencies; slow resolution; no dependency groups |
| Poetry | 10–100× slower resolution than uv; lock file format incompatible with pip |
| Conda | Overkill for pure Python; adds non-Python packages; slower CI |
| Pipenv | Abandoned by community; slow; lock file issues |

## Consequences

### Positive
- uv resolves dependencies 10–100× faster than pip — `uv sync` completes in < 5 s after the cache is warm.
- `uv.lock` guarantees identical environments across developer machines, CI runners, and Docker builds.
- `uv sync --group streaming` installs only the streaming extras — keeps the base image lean.
- `uv python install 3.12` ensures the exact Python version is used even if the system Python differs.

### Negative / trade-offs
- `uv` is a relatively new tool — some IDE integrations (PyCharm, VS Code) require manual virtual environment pointing.
- `uv.lock` must be committed and kept up to date — `make install` should be run after any `pyproject.toml` change.

### Neutral / constraints
- The Makefile targets (`make install`, `make install-streaming`) abstract the uv command surface.
- In CI, `uv sync --frozen` is used to enforce the lock file; developers use `uv sync` (which updates the lock if needed).
