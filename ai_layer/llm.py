from __future__ import annotations

import logging
import os
from functools import lru_cache
from typing import Any

import anthropic

from config.settings import settings

logger = logging.getLogger(__name__)


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


def generate(prompt: str, system: str | None = None) -> str:
    client = _get_client()
    kwargs: dict[str, Any] = {
        "model": settings.llm.model,
        "max_tokens": settings.llm.max_tokens,
        "temperature": settings.llm.temperature,
        "messages": [{"role": "user", "content": prompt}],
    }
    if system:
        kwargs["system"] = system
    try:
        response = client.messages.create(**kwargs)
        text = _extract_text(response)
        if not text:
            raise RuntimeError("LLM response contained no text content.")
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
