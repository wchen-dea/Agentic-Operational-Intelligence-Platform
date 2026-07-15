"""OpenTelemetry distributed tracing configuration.

Provides automatic trace propagation across the FastAPI layer and manual
span instrumentation helpers for agent execution.

Quick start
-----------
Set environment variables:

    AOIP_OTEL__ENABLED=true
    AOIP_OTEL__ENDPOINT=http://otel-collector:4317   # gRPC OTLP
    AOIP_OTEL__SERVICE_NAME=aoip-api

The module degrades gracefully when ``opentelemetry-sdk`` is not installed -
all span context managers and decorators become no-ops so the application
continues to function without tracing infrastructure.
"""

from __future__ import annotations

import contextlib
import logging
from contextlib import contextmanager
from typing import Any, Generator

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Optional dependency - degrade gracefully if not installed
# ---------------------------------------------------------------------------

_otel_available = False
_tracer_provider: Any = None

try:
    from opentelemetry import trace as _otel_trace
    from opentelemetry.sdk.trace import TracerProvider
    from opentelemetry.sdk.trace.export import BatchSpanProcessor
    from opentelemetry.sdk.resources import Resource, SERVICE_NAME

    _otel_available = True
except ImportError:
    logger.info(
        "opentelemetry-sdk not installed - tracing disabled. "
        "Install with: uv add opentelemetry-sdk opentelemetry-exporter-otlp-proto-grpc "
        "opentelemetry-instrumentation-fastapi"
    )


def configure_tracing(
    endpoint: str | None = None,
    service_name: str = "aoip",
    sample_rate: float = 1.0,
) -> None:
    """Initialise the global TracerProvider.

    Call once on application startup (idempotent - subsequent calls are no-ops
    if the provider is already set).

    Args:
        endpoint:     OTLP gRPC collector endpoint, e.g. ``http://localhost:4317``.
                      When ``None`` the NoOp provider is used (spans are discarded).
        service_name: Logical service name reported in traces.
        sample_rate:  Fraction of traces to sample (1.0 = 100 %).
    """
    global _tracer_provider

    if not _otel_available:
        return

    if _tracer_provider is not None:
        return  # already configured

    resource = Resource.create({SERVICE_NAME: service_name})

    if endpoint:
        try:
            from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import (  # type: ignore[import]
                OTLPSpanExporter,
            )
            from opentelemetry.sdk.trace.sampling import TraceIdRatioBased

            sampler = TraceIdRatioBased(sample_rate) if sample_rate < 1.0 else None
            provider_kwargs: dict[str, Any] = {"resource": resource}
            if sampler:
                provider_kwargs["sampler"] = sampler

            provider = TracerProvider(**provider_kwargs)
            provider.add_span_processor(BatchSpanProcessor(OTLPSpanExporter(endpoint=endpoint)))
            _otel_trace.set_tracer_provider(provider)
            _tracer_provider = provider
            logger.info(
                "OpenTelemetry tracing enabled -> %s (service=%s, sample_rate=%.2f)",
                endpoint,
                service_name,
                sample_rate,
            )
        except Exception as exc:
            logger.warning("Could not configure OTLP exporter: %s", exc)
    else:
        # No collector configured - use NoOp provider (spans collected but not exported)
        provider = TracerProvider(resource=resource)
        _otel_trace.set_tracer_provider(provider)
        _tracer_provider = provider
        logger.debug("OpenTelemetry tracing using NoOp provider (no endpoint configured)")


def get_tracer(name: str = "aoip") -> Any:
    """Return a tracer for the given instrumentation scope."""
    if not _otel_available:
        return _NoOpTracer()
    from opentelemetry import trace

    return trace.get_tracer(name)


def instrument_fastapi(app: Any) -> None:
    """Apply FastAPI + ASGI automatic instrumentation."""
    if not _otel_available:
        return
    try:
        from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor  # type: ignore[import]

        FastAPIInstrumentor.instrument_app(app)
        logger.info("FastAPI OpenTelemetry instrumentation applied")
    except ImportError:
        logger.info(
            "opentelemetry-instrumentation-fastapi not installed - route-level spans won't be created automatically."
        )


@contextmanager
def agent_span(name: str, attributes: dict[str, Any] | None = None) -> Generator[Any, None, None]:
    """Context manager that wraps an agent execution in an OTel span.

    Usage::

        with agent_span("kpi_agent", {"store_id": "245"}) as span:
            result = kpi_agent.run(...)
    """
    if not _otel_available:
        yield None
        return

    tracer = get_tracer("aoip.agents")
    with tracer.start_as_current_span(name) as span:
        if attributes:
            for k, v in attributes.items():
                span.set_attribute(k, str(v))
        try:
            yield span
        except Exception as exc:
            from opentelemetry.trace import StatusCode

            span.set_status(StatusCode.ERROR, str(exc))
            raise


def current_trace_id() -> str:
    """Return the current trace ID as a hex string, or empty string if unavailable."""
    if not _otel_available:
        return ""
    try:
        from opentelemetry import trace

        ctx = trace.get_current_span().get_span_context()
        if ctx and ctx.is_valid:
            return format(ctx.trace_id, "032x")
    except Exception:
        pass
    return ""


# ---------------------------------------------------------------------------
# No-op fallback when opentelemetry is not installed
# ---------------------------------------------------------------------------


class _NoOpSpan:
    def set_attribute(self, key: str, value: Any) -> None: ...
    def set_status(self, *a: Any, **kw: Any) -> None: ...
    def __enter__(self) -> "_NoOpSpan":
        return self

    def __exit__(self, *a: Any) -> None: ...


class _NoOpTracer:
    @contextlib.contextmanager
    def start_as_current_span(self, name: str, **kw: Any) -> Generator[_NoOpSpan, None, None]:
        yield _NoOpSpan()
