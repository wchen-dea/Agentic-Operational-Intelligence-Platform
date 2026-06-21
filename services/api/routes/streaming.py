"""Streaming and async API routes.

Provides:
- ``POST /ask/stream`` — SSE endpoint that streams LLM tokens in real time
- ``POST /ask/async`` — async version of the /ask endpoint
- ``POST /ask/agentic`` — tool-calling agentic endpoint
"""

from __future__ import annotations

import json
import logging
import os

from fastapi import APIRouter
from sse_starlette.sse import EventSourceResponse

from services.api.models import AskRequest
from config.settings import settings

logger = logging.getLogger(__name__)

router = APIRouter(tags=["streaming"])


@router.post("/ask/stream")
async def ask_stream(req: AskRequest):
    """Stream the LLM response token-by-token via Server-Sent Events."""
    from ai_layer.llm import generate_stream
    from ai_layer.prompts import OPERATIONAL_BRIEF

    if not os.environ.get(settings.llm.api_key_env_var):
        async def fallback():
            yield {"data": json.dumps({"error": "LLM API key not configured"})}
        return EventSourceResponse(fallback())

    system = OPERATIONAL_BRIEF.system
    prompt = f"[{req.persona}] {req.question}"
    if req.store_id:
        prompt += f" (store: {req.store_id})"
    if req.region:
        prompt += f" (region: {req.region})"

    async def event_generator():
        try:
            async for chunk in generate_stream(prompt, system=system, max_tokens=512):
                yield {"data": json.dumps({"token": chunk})}
            yield {"data": json.dumps({"done": True})}
        except Exception as exc:
            logger.error("Stream error: %s", exc)
            yield {"data": json.dumps({"error": str(exc)})}

    return EventSourceResponse(event_generator())


@router.post("/ask/async")
async def ask_async(req: AskRequest):
    """Async (non-streaming) version of the /ask endpoint using the async LLM client."""
    from ai_layer.llm import generate_async
    from ai_layer.prompts import OPERATIONAL_BRIEF

    if not os.environ.get(settings.llm.api_key_env_var):
        return {"answer": "LLM API key not configured", "async": True}

    system = OPERATIONAL_BRIEF.system
    prompt = f"[{req.persona}] {req.question}"
    if req.store_id:
        prompt += f" (store: {req.store_id})"
    if req.region:
        prompt += f" (region: {req.region})"

    text = await generate_async(prompt, system=system, max_tokens=512)
    return {"answer": text, "persona": req.persona, "async": True}


@router.post("/ask/agentic")
async def ask_agentic(req: AskRequest):
    """Agentic endpoint where the LLM can autonomously invoke registered skills."""
    if not os.environ.get(settings.llm.api_key_env_var):
        return {"answer": "LLM API key not configured", "tool_calls": []}

    from ai_layer.tool_calling import agentic_query

    system = (
        "You are an operational intelligence assistant for a retail chain. "
        "Use the available tools to fetch KPIs, detect anomalies, and search "
        "the knowledge base before generating your answer. "
        f"Respond for the persona: {req.persona}."
    )
    prompt = req.question
    if req.store_id:
        prompt += f"\n\nContext: store_id={req.store_id}"
    if req.region:
        prompt += f"\n\nContext: region={req.region}"

    result = agentic_query(
        question=prompt,
        system=system,
        max_tokens=1024,
        max_tool_rounds=5,
    )
    return result
