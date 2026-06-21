import logging
import os
from functools import lru_cache

import anthropic

from config.settings import settings

logger = logging.getLogger(__name__)


@lru_cache(maxsize=1)
def _get_client() -> anthropic.Anthropic:
    api_key = os.environ.get(settings.llm.api_key_env_var)
    if not api_key:
        raise ValueError(f"Missing environment variable: {settings.llm.api_key_env_var}")
    return anthropic.Anthropic(api_key=api_key)


def generate(prompt: str, system: str | None = None) -> str:
    client = _get_client()
    kwargs = {
        "model": settings.llm.model,
        "max_tokens": settings.llm.max_tokens,
        "temperature": settings.llm.temperature,
        "messages": [{"role": "user", "content": prompt}],
    }
    if system:
        kwargs["system"] = system
    try:
        response = client.messages.create(**kwargs)
        return response.content[0].text
    except anthropic.APIConnectionError as e:
        logger.error("LLM connection error: %s", e)
        raise
    except anthropic.RateLimitError as e:
        logger.warning("LLM rate limit hit: %s", e)
        raise
    except anthropic.APIStatusError as e:
        logger.error("LLM API error (status=%d): %s", e.status_code, e.message)
        raise
