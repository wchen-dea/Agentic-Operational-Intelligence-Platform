"""Streaming and async API routes.

All three routes now run the full orchestrator DAG (KPI enrichment, anomaly
detection, promotion analysis, recommendation generation) before delivering
results.  Previously /ask/stream and /ask/async bypassed the DAG and called
the LLM directly, producing responses without any operational context.

- ``POST /ask/stream``  - SSE endpoint; runs DAG in a thread then streams the
                          recommendation text token-by-token.
- ``POST /ask/async``   - Non-blocking DAG execution via asyncio.to_thread.
- ``POST /ask/agentic`` - Tool-calling agentic endpoint (unchanged).
"""

from __future__ import annotations

import asyncio
import json
import logging
import os

from fastapi import APIRouter, Depends
from sse_starlette.sse import EventSourceResponse

from ai_systems.gateway.api.models import AskRequest
from ai_systems.gateway.api.auth import require_auth, APIKeyRecord
from ai_systems.config.settings import settings

logger = logging.getLogger(__name__)

router = APIRouter(tags=["streaming"])


@router.post("/ask/stream")
async def ask_stream(req: AskRequest, auth: APIKeyRecord = Depends(require_auth)):
    """Stream an orchestrator DAG response token-by-token via Server-Sent Events.

    The full DAG (KPI -> anomaly -> promotion -> recommendation) runs in a thread
    pool via ``asyncio.to_thread`` so the async event loop stays unblocked.
    The recommendation narrative is then emitted word-by-word as SSE tokens,
    followed by a final ``done`` event carrying the structured metadata.
    """
    from ai_systems.orchestration.orchestrator import get_orchestrator

    orchestrator = get_orchestrator()

    async def event_generator():
        try:
            # Run the full DAG synchronously in a thread pool
            result: dict = await asyncio.to_thread(
                orchestrator.answer,
                req.question,
                store_id=req.store_id,
                region=req.region,
                persona=req.persona,
                session_id=req.session_id,
            )

            # Stream the recommendation narrative word-by-word
            recommendation: str = result.get("recommendation", "")
            words = recommendation.split()
            for i, word in enumerate(words):
                token = word + (" " if i < len(words) - 1 else "")
                yield {"data": json.dumps({"token": token})}

            # Final event with structured metadata (no full KPI dict to keep payload small)
            trace = result.get("execution_trace", {})
            yield {
                "data": json.dumps(
                    {
                        "done": True,
                        "store_id": result.get("store_id"),
                        "region": result.get("region"),
                        "alert_count": len(result.get("anomalies", [])),
                        "intent": result.get("intent"),
                        "execution_ms": trace.get("total_duration_ms") if isinstance(trace, dict) else None,
                        "cost_usd": result.get("usage", {}).get("estimated_cost_usd"),
                    }
                )
            }
        except Exception as exc:
            logger.exception("Stream error: %s", exc)
            yield {"data": json.dumps({"error": "Stream failed - see server logs"})}

    return EventSourceResponse(event_generator())


@router.post("/ask/async")
async def ask_async(req: AskRequest, auth: APIKeyRecord = Depends(require_auth)):
    """Run the full orchestrator DAG asynchronously (non-blocking).

    Uses ``asyncio.to_thread`` so the synchronous DAG executor does not block
    the async event loop.  Returns the same structured response as ``POST /ask``.
    """
    from ai_systems.orchestration.orchestrator import get_orchestrator

    orchestrator = get_orchestrator()
    result = await asyncio.to_thread(
        orchestrator.answer,
        req.question,
        store_id=req.store_id,
        region=req.region,
        persona=req.persona,
        session_id=req.session_id,
    )
    result["async"] = True
    return result


@router.post("/ask/agentic")
async def ask_agentic(req: AskRequest, auth: APIKeyRecord = Depends(require_auth)):
    """Agentic endpoint where the LLM can autonomously invoke registered skills."""
    if not os.environ.get(settings.llm.api_key_env_var):
        return {"answer": "LLM API key not configured", "tool_calls": []}

    from ai_systems.tools.calling import agentic_query

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

    result = await asyncio.to_thread(
        agentic_query,
        question=prompt,
        system=system,
        max_tokens=1024,
        max_tool_rounds=5,
    )
    return result


@router.post("/ask/stream")
async def ask_stream(req: AskRequest, auth: APIKeyRecord = Depends(require_auth)):
    """Stream the LLM response token-by-token via Server-Sent Events."""
    from ai_systems.core.llm import generate_stream
    from ai_systems.core.prompts import OPERATIONAL_BRIEF

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
async def ask_async(req: AskRequest, auth: APIKeyRecord = Depends(require_auth)):
    """Async (non-streaming) version of the /ask endpoint using the async LLM client."""
    from ai_systems.core.llm import generate_async
    from ai_systems.core.prompts import OPERATIONAL_BRIEF

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
async def ask_agentic(req: AskRequest, auth: APIKeyRecord = Depends(require_auth)):
    """Agentic endpoint where the LLM can autonomously invoke registered skills."""
    if not os.environ.get(settings.llm.api_key_env_var):
        return {"answer": "LLM API key not configured", "tool_calls": []}

    from ai_systems.tools.calling import agentic_query

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
