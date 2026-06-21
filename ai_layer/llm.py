from __future__ import annotations

import hashlib
import logging
import os
import time
from collections import OrderedDict
from dataclasses import dataclass
from functools import lru_cache
from typing import Any

import anthropic

from config.settings import settings

logger = logging.getLogger(__name__)


@dataclass
class LLMUsage:
    """Token usage from a single LLM call."""

    input_tokens: int = 0
    output_tokens: int = 0
    cache_hit: bool = False
    duration_ms: float = 0.0

    @property
    def total_tokens(self) -> int:
        return self.input_tokens + self.output_tokens

    @property
    def estimated_cost_usd(self) -> float:
        """Estimate cost using Claude Sonnet pricing ($3/M input, $15/M output)."""
        return (self.input_tokens * 3.0 + self.output_tokens * 15.0) / 1_000_000


# Module-level usage accumulator — reset per request or read via get_session_usage()
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
# Response cache — avoids re-calling the LLM for identical prompt+system pairs
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
) -> str:
    """Generate text via the LLM with optional caching and token tracking.

    Args:
        prompt: User prompt text.
        system: Optional system prompt.
        max_tokens: Override the default max_tokens from settings.
        use_cache: If True, return cached response for identical prompts.
    """
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
            )
            _session_usage.append(cache_usage)
            logger.debug("LLM cache hit (saved ~%d tokens)", original_usage.total_tokens)
            return text

    client = _get_client()
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
        )
        _session_usage.append(usage)

        # Store in cache
        if use_cache:
            _response_cache.put(key, (text, usage))  # type: ignore[possibly-undefined]

        logger.info(
            "LLM call: %d input + %d output tokens (%.1fms, ~$%.6f)",
            input_tokens, output_tokens, duration, usage.estimated_cost_usd,
        )
        return text
    except anthropic.APIConnectionError as exc:
        logger.error("LLM connection error: %s", exc)
        raise
    except anthropic.RateLimitError as exc:
        logger.warning("LLM rate limit hit: %s", exc)
        raise
    except anthropic.APIStatusError as exc:
        logger.error("LLM API error (status=%d): %s", exc.status_code, exc.message)
        raise
        raise
