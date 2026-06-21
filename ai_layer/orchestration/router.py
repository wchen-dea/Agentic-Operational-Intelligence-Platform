"""Intent-based task router — classifies user intent and selects the agent subgraph."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from enum import Enum
from typing import Any


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
    (Intent.KPI_QUERY, [
        r"\bkpi\b", r"\bmetric\b", r"\brevenue\b", r"\bconversion\b",
        r"\bshow.?rate\b", r"\bstockout\b", r"\binventory\b",
        r"\bcycle.?time\b", r"\binvoice.?capture\b",
    ]),
    (Intent.ANOMALY_CHECK, [
        r"\balert\b", r"\banomaly\b", r"\bthreshold\b", r"\bbreach\b",
        r"\bwarning\b", r"\bcritical\b", r"\bspike\b", r"\bdrop\b",
    ]),
    (Intent.PROMOTION_ANALYSIS, [
        r"\bpromotion\b", r"\bpromo\b", r"\bcampaign\b", r"\bdiscount\b",
        r"\bupsell\b", r"\bbrand(?:ed)?.?mix\b",
    ]),
    (Intent.OPERATIONAL_BRIEF, [
        r"\bbrief\b", r"\bsummary\b", r"\boperational\b", r"\bdigest\b",
        r"\boverview\b", r"\bstatus\b", r"\breadout\b",
    ]),
]

# Maps each intent to the minimum set of agent nodes required
_INTENT_AGENT_MAP: dict[Intent, list[str]] = {
    Intent.KPI_QUERY: ["kpi", "rag_search"],
    Intent.ANOMALY_CHECK: ["kpi", "anomaly", "rag_search"],
    Intent.PROMOTION_ANALYSIS: ["kpi", "anomaly", "promotion", "rag_search"],
    Intent.OPERATIONAL_BRIEF: ["kpi", "anomaly", "promotion", "recommendation", "rag_search"],
    Intent.GENERAL_QA: ["kpi", "anomaly", "promotion", "recommendation", "rag_search"],
}


class IntentRouter:
    """Routes user queries to the appropriate agent execution subgraph.

    Uses a two-phase strategy:
    1. Rule-based keyword matching (fast, no external calls).
    2. Optional LLM-based classification for ambiguous queries (future).
    """

    def __init__(self, default_intent: Intent = Intent.GENERAL_QA) -> None:
        self._default_intent = default_intent

    def classify(self, query: str, context: dict[str, Any] | None = None) -> RouteResult:
        """Classify user intent and return the routing decision."""
        query_lower = query.lower()
        scores: dict[Intent, float] = {}

        for intent, patterns in _INTENT_PATTERNS:
            matches = sum(1 for p in patterns if re.search(p, query_lower))
            if matches:
                scores[intent] = matches / len(patterns)

        if scores:
            best_intent = max(scores, key=scores.get)  # type: ignore[arg-type]
            confidence = min(scores[best_intent] * 2.0, 1.0)  # scale up, cap at 1.0
        else:
            best_intent = self._default_intent
            confidence = 0.3

        # Context-based boosting
        if context:
            if context.get("has_active_alerts") and best_intent == Intent.KPI_QUERY:
                best_intent = Intent.ANOMALY_CHECK
                confidence = max(confidence, 0.6)

        return RouteResult(
            intent=best_intent,
            confidence=confidence,
            required_agents=_INTENT_AGENT_MAP[best_intent],
            metadata={"scores": scores},
        )

    def get_required_agents(self, intent: Intent) -> list[str]:
        """Return the agent names required for a given intent."""
        return _INTENT_AGENT_MAP.get(intent, _INTENT_AGENT_MAP[Intent.GENERAL_QA])
