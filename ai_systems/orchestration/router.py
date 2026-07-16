"""Intent-based task router - classifies user intent and selects the agent subgraph.

Two-phase classification
-------------------------
Phase 1  Fast regex keyword matching (no external calls).  If the score
         exceeds ``_LLM_FALLBACK_THRESHOLD`` the result is returned immediately.
Phase 2  LLM-based classification (Claude Haiku) invoked only for ambiguous
         queries where regex confidence is below the threshold.  The LLM is
         given the five intent labels and asked to respond with a compact JSON
         object.  Falls back to the regex result if the LLM call fails or the
         response cannot be parsed.
"""

from __future__ import annotations

import json
import logging
import os
import re
from dataclasses import dataclass, field
from enum import Enum
from typing import Any

logger = logging.getLogger(__name__)

# Confidence below this level triggers the LLM fallback classifier.
_LLM_FALLBACK_THRESHOLD = 0.40


class Intent(str, Enum):
    """Recognized user intents mapped to agent subgraphs."""

    KPI_QUERY = "kpi_query"
    ANOMALY_CHECK = "anomaly_check"
    PROMOTION_ANALYSIS = "promotion_analysis"
    OPERATIONAL_BRIEF = "operational_brief"
    GENERAL_QA = "general_qa"


@dataclass
class RouteResult:
    """Outcome of intent classification."""

    intent: Intent
    confidence: float
    required_agents: list[str]
    metadata: dict[str, Any] = field(default_factory=dict)


# Keyword patterns for rule-based intent classification
_INTENT_PATTERNS: list[tuple[Intent, list[str]]] = [
    (
        Intent.KPI_QUERY,
        [
            r"\bkpi\b",
            r"\bmetric\b",
            r"\brevenue\b",
            r"\bconversion\b",
            r"\bshow.?rate\b",
            r"\bstockout\b",
            r"\binventory\b",
            r"\bcycle.?time\b",
            r"\binvoice.?capture\b",
        ],
    ),
    (
        Intent.ANOMALY_CHECK,
        [
            r"\balert\b",
            r"\banomaly\b",
            r"\bthreshold\b",
            r"\bbreach\b",
            r"\bwarning\b",
            r"\bcritical\b",
            r"\bspike\b",
            r"\bdrop\b",
        ],
    ),
    (
        Intent.PROMOTION_ANALYSIS,
        [
            r"\bpromotion\b",
            r"\bpromo\b",
            r"\bcampaign\b",
            r"\bdiscount\b",
            r"\bupsell\b",
            r"\bbrand(?:ed)?.?mix\b",
        ],
    ),
    (
        Intent.OPERATIONAL_BRIEF,
        [
            r"\bbrief\b",
            r"\bsummary\b",
            r"\boperational\b",
            r"\bdigest\b",
            r"\boverview\b",
            r"\bstatus\b",
            r"\breadout\b",
        ],
    ),
]

# Maps each intent to the minimum set of agent nodes required
_INTENT_AGENT_MAP: dict[Intent, list[str]] = {
    Intent.KPI_QUERY: ["kpi", "rag_search"],
    Intent.ANOMALY_CHECK: ["kpi", "anomaly", "rag_search"],
    Intent.PROMOTION_ANALYSIS: ["kpi", "anomaly", "promotion", "rag_search"],
    Intent.OPERATIONAL_BRIEF: ["kpi", "anomaly", "promotion", "recommendation", "rag_search"],
    Intent.GENERAL_QA: ["kpi", "anomaly", "promotion", "recommendation", "rag_search"],
}

_LLM_CLASSIFICATION_PROMPT = """\
You are a classifier for a retail operations intelligence platform.
Classify the user query into exactly one of these intents:

  kpi_query          - asking about specific KPI values or metrics
  anomaly_check      - asking about alerts, anomalies, thresholds, or unusual patterns
  promotion_analysis - asking about promotions, campaigns, branded mix, or discounts
  operational_brief  - asking for a full summary, readout, overview, or status update
  general_qa         - any other operational question

User query: "{query}"

Respond with valid JSON only (no extra text):
{{"intent": "<one of the five values>", "confidence": <0.0-1.0>, "reasoning": "<one sentence>"}}"""


class IntentRouter:
    """Routes user queries to the appropriate agent execution subgraph."""

    def __init__(
        self,
        default_intent: Intent = Intent.GENERAL_QA,
        llm_fallback_threshold: float = _LLM_FALLBACK_THRESHOLD,
    ) -> None:
        self._default_intent = default_intent
        self._llm_threshold = llm_fallback_threshold

    def classify(self, query: str, context: dict[str, Any] | None = None) -> RouteResult:
        """Classify user intent via regex (fast) with LLM fallback for ambiguous queries."""
        query_lower = query.lower()
        scores: dict[Intent, float] = {}

        for intent, patterns in _INTENT_PATTERNS:
            matches = sum(1 for p in patterns if re.search(p, query_lower))
            if matches:
                scores[intent] = matches / len(patterns)

        if scores:
            best_intent = max(scores, key=scores.get)  # type: ignore[arg-type]
            confidence = min(scores[best_intent] * 2.0, 1.0)
        else:
            best_intent = self._default_intent
            confidence = 0.3

        # Context-based boosting
        if context:
            if context.get("has_active_alerts") and best_intent == Intent.KPI_QUERY:
                best_intent = Intent.ANOMALY_CHECK
                confidence = max(confidence, 0.6)

        # Phase 2: LLM fallback for ambiguous / low-confidence queries
        if confidence < self._llm_threshold:
            llm_result = self._classify_with_llm(query, fallback_intent=best_intent, fallback_confidence=confidence)
            if llm_result is not None:
                logger.debug(
                    "LLM router upgraded '%s'->'%s' (%.2f->%.2f)",
                    best_intent.value,
                    llm_result.intent.value,
                    confidence,
                    llm_result.confidence,
                )
                return llm_result

        return RouteResult(
            intent=best_intent,
            confidence=confidence,
            required_agents=_INTENT_AGENT_MAP[best_intent],
            metadata={"scores": scores, "classifier": "regex"},
        )

    def _classify_with_llm(
        self,
        query: str,
        fallback_intent: Intent,
        fallback_confidence: float,
    ) -> RouteResult | None:
        """Call Haiku for a structured intent classification. Returns None on any failure."""
        from ai_systems.config.settings import settings

        if not os.environ.get(settings.llm.api_key_env_var):
            return None

        try:
            from ai_systems.core.llm import generate
            from ai_systems.core.model_router import TaskComplexity

            raw = generate(
                prompt=_LLM_CLASSIFICATION_PROMPT.format(query=query),
                max_tokens=128,
                use_cache=True,
                complexity=TaskComplexity.LOW,
                task_hint="classify intent",
            )
            # Extract the first JSON object from the response
            match = re.search(r"\{.*?\}", raw, re.DOTALL)
            if not match:
                logger.warning("LLM router: no JSON found in response: %s", raw[:200])
                return None

            parsed = json.loads(match.group())
            intent_str = parsed.get("intent", "").lower().strip()
            llm_confidence = float(parsed.get("confidence", 0.5))

            try:
                intent = Intent(intent_str)
            except ValueError:
                logger.warning("LLM router: unknown intent '%s'", intent_str)
                return None

            return RouteResult(
                intent=intent,
                confidence=min(llm_confidence, 1.0),
                required_agents=_INTENT_AGENT_MAP[intent],
                metadata={
                    "classifier": "llm",
                    "llm_reasoning": parsed.get("reasoning", ""),
                    "regex_fallback_intent": fallback_intent.value,
                    "regex_fallback_confidence": fallback_confidence,
                },
            )
        except Exception as exc:
            logger.warning("LLM intent classification failed, using regex result: %s", exc)
            return None

    def get_required_agents(self, intent: Intent) -> list[str]:
        """Return the agent names required for a given intent."""
        return _INTENT_AGENT_MAP.get(intent, _INTENT_AGENT_MAP[Intent.GENERAL_QA])
