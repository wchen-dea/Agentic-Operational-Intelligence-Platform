"""Structured JSON logging with per-request correlation IDs.

Replaces the default Python logging text formatter with a JSON formatter so
that log lines can be ingested by ELK, CloudWatch Logs Insights, or any
structured log aggregator without additional parsing.

Every log record emitted during a request automatically includes the
correlation ID injected by ``CorrelationIdMiddleware``.

Quick start
-----------
Call ``configure_logging()`` once before your FastAPI ``app`` is created::

    from observability.logging_config import configure_logging
    configure_logging(level="INFO", json_format=True)

The ``CorrelationIdMiddleware`` must be added to the FastAPI app to populate
the correlation ID context variable for incoming requests::

    from observability.logging_config import CorrelationIdMiddleware
    app.add_middleware(CorrelationIdMiddleware)

Outgoing responses will include the ``X-Correlation-ID`` header so callers
can correlate client-side logs with server-side traces.
"""

from __future__ import annotations

import json
import logging
import time
import traceback
import uuid
from contextvars import ContextVar
from typing import Any

# ---------------------------------------------------------------------------
# Correlation ID context variable - populated by CorrelationIdMiddleware
# ---------------------------------------------------------------------------

correlation_id: ContextVar[str] = ContextVar("correlation_id", default="")


def get_correlation_id() -> str:
    """Return the current request's correlation ID (empty string outside requests)."""
    return correlation_id.get("")


# ---------------------------------------------------------------------------
# JSON log formatter
# ---------------------------------------------------------------------------


class JsonFormatter(logging.Formatter):
    """Emit each log record as a single-line JSON object.

    Fields emitted:
    - ``ts``             ISO-8601 UTC timestamp
    - ``level``          Log level name
    - ``logger``         Logger name (module path)
    - ``msg``            Formatted log message
    - ``correlation_id`` Request correlation ID (empty string if not in a request)
    - ``exc``            Exception traceback (only present when exc_info is set)
    - ``extra``          Any extra fields attached by the caller
    """

    _RESERVED = {
        "msg",
        "args",
        "levelname",
        "name",
        "pathname",
        "filename",
        "module",
        "exc_info",
        "exc_text",
        "stack_info",
        "lineno",
        "funcName",
        "created",
        "msecs",
        "relativeCreated",
        "thread",
        "threadName",
        "processName",
        "process",
        "message",
    }

    def format(self, record: logging.LogRecord) -> str:
        data: dict[str, Any] = {
            "ts": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(record.created)),
            "level": record.levelname,
            "logger": record.name,
            "msg": record.getMessage(),
            "correlation_id": correlation_id.get(""),
        }

        if record.exc_info:
            data["exc"] = traceback.format_exception(*record.exc_info)

        # Include any extra fields passed via logger.info("...", extra={...})
        extra = {k: v for k, v in record.__dict__.items() if k not in self._RESERVED and not k.startswith("_")}
        if extra:
            data["extra"] = extra

        try:
            return json.dumps(data, default=str)
        except Exception:
            # Fallback - should never happen but defensive
            return json.dumps({"ts": data["ts"], "level": "ERROR", "msg": "log serialisation failed"})


# ---------------------------------------------------------------------------
# Logging configuration
# ---------------------------------------------------------------------------


def configure_logging(
    level: str = "INFO",
    json_format: bool = True,
) -> None:
    """Configure root logger with JSON or text formatting.

    This replaces all existing handlers on the root logger so it should be
    called once, early in the application startup.

    Args:
        level:       Logging level string (DEBUG, INFO, WARNING, ERROR).
        json_format: When True (default) use ``JsonFormatter``; when False use
                     a human-readable text format (useful for local development).
    """
    handler = logging.StreamHandler()

    if json_format:
        handler.setFormatter(JsonFormatter())
    else:
        handler.setFormatter(
            logging.Formatter(
                fmt="%(asctime)s [%(levelname)s] %(name)s - %(message)s",
                datefmt="%Y-%m-%dT%H:%M:%S",
            )
        )

    root = logging.getLogger()
    root.handlers.clear()
    root.addHandler(handler)
    root.setLevel(getattr(logging, level.upper(), logging.INFO))

    # Silence noisy third-party loggers
    for noisy in ("httpx", "httpcore", "urllib3", "botocore", "boto3", "chromadb", "anthropic"):
        logging.getLogger(noisy).setLevel(logging.WARNING)


# ---------------------------------------------------------------------------
# FastAPI / Starlette middleware
# ---------------------------------------------------------------------------


class CorrelationIdMiddleware:
    """ASGI middleware that injects a correlation ID into every request.

    Priority order for the correlation ID:
    1. Existing ``X-Correlation-ID`` header from the caller (enables end-to-end tracing).
    2. New UUID generated for this request.

    The chosen ID is:
    - Set in ``correlation_id`` context variable (visible to all log records).
    - Echoed back in the ``X-Correlation-ID`` response header.
    """

    def __init__(self, app: Any) -> None:
        self.app = app

    async def __call__(self, scope: Any, receive: Any, send: Any) -> None:
        if scope["type"] not in ("http", "websocket"):
            await self.app(scope, receive, send)
            return

        # Extract or generate correlation ID
        headers = dict(scope.get("headers", []))
        corr = headers.get(b"x-correlation-id", b"").decode() or str(uuid.uuid4())
        token = correlation_id.set(corr)

        async def send_with_header(message: Any) -> None:
            if message["type"] == "http.response.start":
                headers_list = list(message.get("headers", []))
                headers_list.append((b"x-correlation-id", corr.encode()))
                message = {**message, "headers": headers_list}
            await send(message)

        try:
            await self.app(scope, receive, send_with_header)
        finally:
            correlation_id.reset(token)
