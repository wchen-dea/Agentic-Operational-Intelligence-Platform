from __future__ import annotations

import hashlib
import json
import logging
import os
import time
from collections import OrderedDict
from dataclasses import dataclass, field
from functools import lru_cache
from typing import Any

import anthropic

from ai_layer.model_router import TaskComplexity, get_model_router
from config.settings import settings

logger = logging.getLogger(__name__)


@dataclass
class LLMUsage:
    """Token usage and cost from a single LLM call."""

    input_tokens: int = 0
    output_tokens: int = 0
    cache_hit: bool = False
    duration_ms: float = 0.0
    model_id: str = field(default="")
    cost_input_per_m: float = field(default=3.0)  # $/M input tokens for this model
    cost_output_per_m: float = field(default=15.0)  # $/M output tokens for this model

    @property
    def total_tokens(self) -> int:
        return self.input_tokens + self.output_tokens

    @property
    def estimated_cost_usd(self) -> float:
        """Estimate cost using per-model pricing from ModelRouter catalog."""
        return (self.input_tokens * self.cost_input_per_m + self.output_tokens * self.cost_output_per_m) / 1_000_000


# Module-level usage accumulator - reset per request or read via get_session_usage()
_session_usage: list[LLMUsage] = []


def get_session_usage() -> list[LLMUsage]:
    """Return all LLM usage records since last reset."""
    return list(_session_usage)


def reset_session_usage() -> None:
    """Clear session usage records."""
    _session_usage.clear()


def get_session_cost_summary() -> dict[str, Any]:
    """Summarize total token usage and estimated cost for the current session."""
    usage = _session_usage
    total_input = sum(u.input_tokens for u in usage)
    total_output = sum(u.output_tokens for u in usage)
    cache_hits = sum(1 for u in usage if u.cache_hit)
    total_cost = sum(u.estimated_cost_usd for u in usage)
    return {
        "calls": len(usage),
        "cache_hits": cache_hits,
        "input_tokens": total_input,
        "output_tokens": total_output,
        "total_tokens": total_input + total_output,
        "estimated_cost_usd": round(total_cost, 6),
    }


# ---------------------------------------------------------------------------
# Response cache - avoids re-calling the LLM for identical prompt+system pairs
# ---------------------------------------------------------------------------


class _LRUCache:
    """Simple LRU cache for LLM responses keyed by prompt hash."""

    def __init__(self, max_size: int = 128) -> None:
        self._cache: OrderedDict[str, tuple[str, LLMUsage]] = OrderedDict()
        self._max_size = max_size

    def get(self, key: str) -> tuple[str, LLMUsage] | None:
        if key in self._cache:
            self._cache.move_to_end(key)
            return self._cache[key]
        return None

    def put(self, key: str, value: tuple[str, LLMUsage]) -> None:
        if key in self._cache:
            self._cache.move_to_end(key)
        else:
            if len(self._cache) >= self._max_size:
                self._cache.popitem(last=False)
        self._cache[key] = value


_response_cache = _LRUCache(max_size=128)


def _cache_key(prompt: str, system: str | None, max_tokens: int) -> str:
    """Deterministic hash for prompt + system + max_tokens."""
    raw = f"{system or ''}|{prompt}|{max_tokens}"
    return hashlib.sha256(raw.encode()).hexdigest()


@lru_cache(maxsize=1)
def _get_client() -> anthropic.Anthropic:
    api_key = os.environ.get(settings.llm.api_key_env_var)
    if not api_key:
        raise ValueError(f"Missing environment variable: {settings.llm.api_key_env_var}")
    return anthropic.Anthropic(api_key=api_key)


@lru_cache(maxsize=1)
def _get_async_client() -> anthropic.AsyncAnthropic:
    api_key = os.environ.get(settings.llm.api_key_env_var)
    if not api_key:
        raise ValueError(f"Missing environment variable: {settings.llm.api_key_env_var}")
    return anthropic.AsyncAnthropic(api_key=api_key)


def _extract_text(response: Any) -> str:
    """Safely extract text from an Anthropic response, handling multi-block content."""
    blocks = getattr(response, "content", None)
    if not isinstance(blocks, list):
        return ""
    parts = [blk.text for blk in blocks if hasattr(blk, "text") and isinstance(blk.text, str)]
    return "\n".join(parts).strip()


def _extract_usage(response: Any) -> tuple[int, int]:
    """Extract input/output token counts from the API response."""
    usage = getattr(response, "usage", None)
    if usage is None:
        return 0, 0
    return getattr(usage, "input_tokens", 0), getattr(usage, "output_tokens", 0)


def generate(
    prompt: str,
    system: str | None = None,
    max_tokens: int | None = None,
    use_cache: bool = True,
    complexity: TaskComplexity | None = None,
    task_hint: str | None = None,
) -> str:
    """Generate text via the LLM with optional caching and token tracking.

    Args:
        prompt: User prompt text.
        system: Optional system prompt.
        max_tokens: Override the default max_tokens from settings.
        use_cache: If True, return cached response for identical prompts.
        complexity: Task complexity used to select the optimal model via
            ModelRouter (LOW->Haiku, MEDIUM->Sonnet, HIGH->Opus).  If None and
            task_hint is also None, falls back to ``settings.llm.model``.
        task_hint: Natural language description used to infer complexity when
            ``complexity`` is not supplied explicitly.
    """
    router = get_model_router()
    if complexity is not None or task_hint is not None:
        spec = router.select(complexity=complexity, task_hint=task_hint)
        model_id = spec.model_id
        cost_in = spec.cost_input_per_m
        cost_out = spec.cost_output_per_m
        effective_max_tokens = max_tokens or spec.max_tokens
    else:
        model_id = settings.llm.model
        cost_in = 3.0  # Sonnet default
        cost_out = 15.0
        effective_max_tokens = max_tokens or settings.llm.max_tokens

    # Check cache
    if use_cache:
        key = _cache_key(prompt, system, effective_max_tokens)
        cached = _response_cache.get(key)
        if cached is not None:
            text, original_usage = cached
            cache_usage = LLMUsage(
                input_tokens=0,
                output_tokens=0,
                cache_hit=True,
                duration_ms=0.0,
                model_id=original_usage.model_id,
                cost_input_per_m=original_usage.cost_input_per_m,
                cost_output_per_m=original_usage.cost_output_per_m,
            )
            _session_usage.append(cache_usage)
            logger.debug("LLM cache hit (saved ~%d tokens)", original_usage.total_tokens)
            return text

    client = _get_client()
    kwargs: dict[str, Any] = {
        "model": model_id,
        "max_tokens": effective_max_tokens,
        "temperature": settings.llm.temperature,
        "messages": [{"role": "user", "content": prompt}],
    }
    if system:
        kwargs["system"] = system

    start = time.perf_counter()
    try:
        response = client.messages.create(**kwargs)
        duration = (time.perf_counter() - start) * 1000
        text = _extract_text(response)
        if not text:
            raise RuntimeError("LLM response contained no text content.")

        input_tokens, output_tokens = _extract_usage(response)
        usage = LLMUsage(
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            cache_hit=False,
            duration_ms=duration,
            model_id=model_id,
            cost_input_per_m=cost_in,
            cost_output_per_m=cost_out,
        )
        _session_usage.append(usage)

        # Store in cache
        if use_cache:
            _response_cache.put(key, (text, usage))  # type: ignore[possibly-undefined]

        logger.info(
            "LLM call: %d input + %d output tokens (%.1fms, ~$%.6f)",
            input_tokens,
            output_tokens,
            duration,
            usage.estimated_cost_usd,
        )
        return text
    except anthropic.APIConnectionError as exc:
        logger.error("LLM connection error: %s", exc)
        raise
    except anthropic.RateLimitError as exc:
        logger.warning("LLM rate limit hit on model '%s': %s", model_id, exc)
        get_model_router().mark_failed(model_id.split("-")[1] if "-" in model_id else model_id)
        raise
    except anthropic.APIStatusError as exc:
        logger.error("LLM API error (status=%d): %s", exc.status_code, exc.message)
        raise


# ---------------------------------------------------------------------------
# Multimodal (vision) generation
# ---------------------------------------------------------------------------

_SUPPORTED_IMAGE_TYPES = {"image/png", "image/jpeg", "image/gif", "image/webp"}


def generate_with_image(
    prompt: str,
    image_data: str | bytes,
    media_type: str = "image/png",
    system: str | None = None,
    max_tokens: int | None = None,
) -> str:
    """Generate text from a prompt + image using Claude's vision capability.

    Args:
        prompt: User text prompt describing the analysis to perform.
        image_data: Base64-encoded image string, or raw bytes (will be b64-encoded).
        media_type: MIME type of the image. Must be png, jpeg, gif, or webp.
        system: Optional system prompt.
        max_tokens: Override the default max_tokens from settings.

    Returns:
        Generated text response from the LLM.

    Example::

        import base64
        with open("dashboard.png", "rb") as f:
            img_b64 = base64.b64encode(f.read()).decode()
        analysis = generate_with_image(
            "Identify any anomalies in this KPI dashboard chart.",
            image_data=img_b64,
            media_type="image/png",
        )
    """
    import base64

    if media_type not in _SUPPORTED_IMAGE_TYPES:
        raise ValueError(f"Unsupported image type '{media_type}'. Supported: {_SUPPORTED_IMAGE_TYPES}")

    # Accept raw bytes or base64 string
    if isinstance(image_data, bytes):
        image_b64 = base64.b64encode(image_data).decode("ascii")
    else:
        image_b64 = image_data

    effective_max_tokens = max_tokens or settings.llm.max_tokens
    client = _get_client()

    messages = [
        {
            "role": "user",
            "content": [
                {
                    "type": "image",
                    "source": {
                        "type": "base64",
                        "media_type": media_type,
                        "data": image_b64,
                    },
                },
                {
                    "type": "text",
                    "text": prompt,
                },
            ],
        }
    ]

    kwargs: dict[str, Any] = {
        "model": settings.llm.model,
        "max_tokens": effective_max_tokens,
        "temperature": settings.llm.temperature,
        "messages": messages,
    }
    if system:
        kwargs["system"] = system

    start = time.perf_counter()
    try:
        response = client.messages.create(**kwargs)
        duration = (time.perf_counter() - start) * 1000
        text = _extract_text(response)
        if not text:
            raise RuntimeError("LLM vision response contained no text content.")

        input_tokens, output_tokens = _extract_usage(response)
        usage = LLMUsage(
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            cache_hit=False,
            duration_ms=duration,
        )
        _session_usage.append(usage)

        logger.info(
            "LLM vision call: %d input + %d output tokens (%.1fms, ~$%.6f)",
            input_tokens,
            output_tokens,
            duration,
            usage.estimated_cost_usd,
        )
        return text
    except (anthropic.APIConnectionError, anthropic.RateLimitError, anthropic.APIStatusError) as exc:
        logger.error("LLM vision error: %s", exc)
        raise


# ---------------------------------------------------------------------------
# Tool / function-calling generation
# ---------------------------------------------------------------------------


def generate_with_tools(
    prompt: str,
    tools: list[dict[str, Any]],
    tool_executor: Any = None,
    system: str | None = None,
    max_tokens: int | None = None,
    max_tool_rounds: int = 5,
) -> dict[str, Any]:
    """Generate a response that may include tool-use calls.

    The LLM receives ``tools`` as Anthropic tool definitions.  If the model
    requests a tool call, ``tool_executor(name, input)`` is invoked and the
    result is sent back in a multi-turn loop (up to *max_tool_rounds* rounds).

    Returns a dict with ``text`` (final answer), ``tool_calls`` (list of
    calls made), and ``usage`` (LLMUsage).
    """
    effective_max_tokens = max_tokens or settings.llm.max_tokens

    client = _get_client()
    messages: list[dict[str, Any]] = [{"role": "user", "content": prompt}]

    kwargs: dict[str, Any] = {
        "model": settings.llm.model,
        "max_tokens": effective_max_tokens,
        "temperature": settings.llm.temperature,
        "tools": tools,
    }
    if system:
        kwargs["system"] = system

    tool_calls_log: list[dict[str, Any]] = []
    total_input = 0
    total_output = 0
    start = time.perf_counter()

    for _round in range(max_tool_rounds):
        kwargs["messages"] = messages
        try:
            response = client.messages.create(**kwargs)
        except (anthropic.APIConnectionError, anthropic.RateLimitError, anthropic.APIStatusError) as exc:
            logger.error("LLM tool-calling error: %s", exc)
            raise

        inp, out = _extract_usage(response)
        total_input += inp
        total_output += out

        # Process content blocks
        assistant_content = response.content
        messages.append({"role": "assistant", "content": assistant_content})

        # Check if the model wants to use tools
        if response.stop_reason != "tool_use":
            # Final text response
            text = _extract_text(response)
            break

        # Execute each tool call
        tool_results: list[dict[str, Any]] = []
        for block in assistant_content:
            if block.type != "tool_use":
                continue
            tool_name = block.name
            tool_input = block.input
            tool_calls_log.append({"name": tool_name, "input": tool_input})

            if tool_executor is not None:
                try:
                    result = tool_executor(tool_name, tool_input)
                except Exception as exc:
                    logger.warning("Tool %s failed: %s", tool_name, exc)
                    result = {"error": str(exc)}
            else:
                result = {"error": f"No executor for tool '{tool_name}'"}

            tool_results.append(
                {
                    "type": "tool_result",
                    "tool_use_id": block.id,
                    "content": json.dumps(result) if not isinstance(result, str) else result,
                }
            )

        messages.append({"role": "user", "content": tool_results})
    else:
        # Exhausted max rounds
        text = _extract_text(response)  # type: ignore[possibly-undefined]
        logger.warning("Tool-calling loop exhausted after %d rounds", max_tool_rounds)

    duration = (time.perf_counter() - start) * 1000
    usage = LLMUsage(
        input_tokens=total_input,
        output_tokens=total_output,
        cache_hit=False,
        duration_ms=duration,
    )
    _session_usage.append(usage)

    logger.info(
        "LLM tool-calling: %d rounds, %d tool calls, %d+%d tokens (%.1fms)",
        len(tool_calls_log),
        len(tool_calls_log),
        total_input,
        total_output,
        duration,
    )

    return {
        "text": text,  # type: ignore[possibly-undefined]
        "tool_calls": tool_calls_log,
        "usage": usage,
    }


# ---------------------------------------------------------------------------
# Async streaming generation
# ---------------------------------------------------------------------------


async def generate_stream(
    prompt: str,
    system: str | None = None,
    max_tokens: int | None = None,
):
    """Async generator that yields text chunks as they arrive from the LLM.

    Usage::

        async for chunk in generate_stream("Summarize KPIs"):
            print(chunk, end="")
    """
    effective_max_tokens = max_tokens or settings.llm.max_tokens
    client = _get_async_client()

    kwargs: dict[str, Any] = {
        "model": settings.llm.model,
        "max_tokens": effective_max_tokens,
        "temperature": settings.llm.temperature,
        "messages": [{"role": "user", "content": prompt}],
    }
    if system:
        kwargs["system"] = system

    start = time.perf_counter()
    total_output = 0

    try:
        async with client.messages.stream(**kwargs) as stream:
            async for text in stream.text_stream:
                total_output += len(text.split())  # rough token proxy
                yield text

        # Record usage after stream completes
        duration = (time.perf_counter() - start) * 1000
        final = await stream.get_final_message()
        inp, out = _extract_usage(final)
        usage = LLMUsage(
            input_tokens=inp,
            output_tokens=out,
            cache_hit=False,
            duration_ms=duration,
        )
        _session_usage.append(usage)
        logger.info(
            "LLM stream: %d input + %d output tokens (%.1fms)",
            inp,
            out,
            duration,
        )
    except (anthropic.APIConnectionError, anthropic.RateLimitError, anthropic.APIStatusError) as exc:
        logger.error("LLM stream error: %s", exc)
        raise


async def generate_async(
    prompt: str,
    system: str | None = None,
    max_tokens: int | None = None,
) -> str:
    """Async (non-streaming) LLM generation using the AsyncAnthropic client."""
    effective_max_tokens = max_tokens or settings.llm.max_tokens
    client = _get_async_client()

    kwargs: dict[str, Any] = {
        "model": settings.llm.model,
        "max_tokens": effective_max_tokens,
        "temperature": settings.llm.temperature,
        "messages": [{"role": "user", "content": prompt}],
    }
    if system:
        kwargs["system"] = system

    start = time.perf_counter()
    try:
        response = await client.messages.create(**kwargs)
        duration = (time.perf_counter() - start) * 1000
        text = _extract_text(response)
        if not text:
            raise RuntimeError("LLM async response contained no text content.")

        inp, out = _extract_usage(response)
        usage = LLMUsage(
            input_tokens=inp,
            output_tokens=out,
            cache_hit=False,
            duration_ms=duration,
        )
        _session_usage.append(usage)
        logger.info(
            "LLM async: %d input + %d output tokens (%.1fms, ~$%.6f)",
            inp,
            out,
            duration,
            usage.estimated_cost_usd,
        )
        return text
    except (anthropic.APIConnectionError, anthropic.RateLimitError, anthropic.APIStatusError) as exc:
        logger.error("LLM async error: %s", exc)
        raise
