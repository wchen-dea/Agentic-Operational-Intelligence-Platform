"""Authentication, authorization, and rate limiting middleware.

Provides:
- API key authentication via ``X-API-Key`` header
- Role-based access control (RBAC) per endpoint tag
- Per-key rate limiting (sliding window)
- FastAPI dependency for injection into routes
"""

from __future__ import annotations

import hashlib
import logging
import time
from dataclasses import dataclass, field
from typing import Any

from fastapi import HTTPException, Request, Security
from fastapi.security import APIKeyHeader

from config.settings import settings

logger = logging.getLogger(__name__)

_api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)


# ---------------------------------------------------------------------------
# API key store (in-process; swap for DB/secrets manager in production)
# ---------------------------------------------------------------------------

@dataclass
class APIKeyRecord:
    """An API key with associated role and metadata."""

    key_hash: str
    role: str  # "admin", "operator", "viewer"
    tenant: str = "default"
    rate_limit_per_minute: int = 60
    enabled: bool = True


# Default keys for development — in production, load from env/DB
_DEFAULT_KEYS: dict[str, APIKeyRecord] = {}


def _hash_key(key: str) -> str:
    return hashlib.sha256(key.encode()).hexdigest()


def register_api_key(
    raw_key: str,
    role: str = "operator",
    tenant: str = "default",
    rate_limit_per_minute: int = 60,
) -> None:
    """Register an API key for authentication."""
    h = _hash_key(raw_key)
    _DEFAULT_KEYS[h] = APIKeyRecord(
        key_hash=h,
        role=role,
        tenant=tenant,
        rate_limit_per_minute=rate_limit_per_minute,
    )


def _lookup_key(raw_key: str) -> APIKeyRecord | None:
    h = _hash_key(raw_key)
    record = _DEFAULT_KEYS.get(h)
    if record and record.enabled:
        return record
    return None


# ---------------------------------------------------------------------------
# RBAC
# ---------------------------------------------------------------------------

# Role → allowed endpoint tags
_ROLE_PERMISSIONS: dict[str, set[str]] = {
    "admin": {"query", "kpi", "alerts", "operations", "skills", "streaming", "observability"},
    "operator": {"query", "kpi", "alerts", "operations", "skills", "streaming"},
    "viewer": {"kpi", "alerts"},
}


def _check_rbac(role: str, endpoint_tags: list[str]) -> bool:
    """Check if the role has access to any of the endpoint's tags."""
    allowed = _ROLE_PERMISSIONS.get(role, set())
    if not endpoint_tags:
        return True  # untagged endpoints are open
    return bool(set(endpoint_tags) & allowed)


# ---------------------------------------------------------------------------
# Rate limiting (sliding window per key)
# ---------------------------------------------------------------------------

_rate_windows: dict[str, list[float]] = {}


def _check_rate_limit(key_hash: str, limit_per_minute: int) -> bool:
    """Return True if the request is within the rate limit."""
    now = time.time()
    window = _rate_windows.setdefault(key_hash, [])
    # Evict entries older than 60 seconds
    cutoff = now - 60.0
    _rate_windows[key_hash] = [t for t in window if t > cutoff]
    window = _rate_windows[key_hash]

    if len(window) >= limit_per_minute:
        return False
    window.append(now)
    return True


# ---------------------------------------------------------------------------
# FastAPI dependency
# ---------------------------------------------------------------------------

async def require_auth(
    request: Request,
    api_key: str | None = Security(_api_key_header),
) -> APIKeyRecord:
    """FastAPI dependency that enforces authentication and RBAC.

    Usage::

        @router.post("/ask")
        def ask(req: AskRequest, auth: APIKeyRecord = Depends(require_auth)):
            ...

    To disable auth in development, set ``AOIP_AUTH_DISABLED=true``.
    """
    import os

    # Allow disabling auth for local dev
    if os.environ.get("AOIP_AUTH_DISABLED", "").lower() in ("true", "1", "yes"):
        return APIKeyRecord(key_hash="dev", role="admin", tenant="dev")

    if not api_key:
        raise HTTPException(status_code=401, detail="Missing X-API-Key header")

    record = _lookup_key(api_key)
    if record is None:
        raise HTTPException(status_code=401, detail="Invalid API key")

    # Rate limiting
    if not _check_rate_limit(record.key_hash, record.rate_limit_per_minute):
        raise HTTPException(
            status_code=429,
            detail=f"Rate limit exceeded ({record.rate_limit_per_minute}/min)",
        )

    # RBAC — check endpoint tags
    route = request.scope.get("route")
    tags = getattr(route, "tags", []) if route else []
    if not _check_rbac(record.role, tags):
        raise HTTPException(
            status_code=403,
            detail=f"Role '{record.role}' does not have access to this endpoint",
        )

    return record


# ---------------------------------------------------------------------------
# Initialization — register dev keys from environment
# ---------------------------------------------------------------------------

def init_auth_from_env() -> None:
    """Register API keys from environment variables.

    Set ``AOIP_API_KEY_ADMIN``, ``AOIP_API_KEY_OPERATOR``, or
    ``AOIP_API_KEY_VIEWER`` to register keys at startup.
    """
    import os

    for role in ("admin", "operator", "viewer"):
        env_var = f"AOIP_API_KEY_{role.upper()}"
        key = os.environ.get(env_var)
        if key:
            register_api_key(key, role=role)
            logger.info("Registered %s API key from %s", role, env_var)
