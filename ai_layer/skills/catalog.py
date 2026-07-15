"""Concrete skill implementations wrapping existing tools."""

from __future__ import annotations

import os
from typing import Any

from ai_layer.agents.recommendation_agent import RecommendationAgent
from ai_layer.agents.tools.alert_tool import detect_kpi_alerts_for_store
from ai_layer.agents.tools.fetch_kpi_tool import fetch_store_kpis
from ai_layer.llm import generate as llm_generate
from ai_layer.prompts import OPERATIONAL_BRIEF
from ai_layer.rag.retrieval.hybrid_search import LocalHybridSearch
from ai_layer.skills import Skill, SkillDescriptor, SkillParameter
from config.settings import settings


class FetchKPISkill(Skill):
    """Retrieves current KPI metrics for a store or region."""

    @property
    def descriptor(self) -> SkillDescriptor:
        return SkillDescriptor(
            name="fetch_kpis",
            description="Retrieve current operational KPIs for a specific store or aggregated by region.",
            parameters=[
                SkillParameter(name="store_id", type="string", description="Store identifier", required=False),
                SkillParameter(
                    name="region", type="string", description="Region name for aggregated KPIs", required=False
                ),
            ],
            tags=["kpi", "data", "read"],
        )

    def execute(self, **kwargs: Any) -> dict[str, Any] | "StoreKPISnapshot":
        return fetch_store_kpis(
            store_id=kwargs.get("store_id"),
            region=kwargs.get("region"),
        )


class DetectAnomaliesSkill(Skill):
    """Detects threshold breaches and anomalies against KPI data."""

    def __init__(self, rules_path: str | None = None) -> None:
        self._rules_path = rules_path or settings.alert_rules_path

    @property
    def descriptor(self) -> SkillDescriptor:
        return SkillDescriptor(
            name="detect_anomalies",
            description="Evaluate KPI data against configured thresholds and return active alerts.",
            parameters=[
                SkillParameter(name="kpis", type="object", description="KPI dict to evaluate"),
            ],
            tags=["anomaly", "alert", "analysis"],
        )

    def execute(self, **kwargs: Any) -> list[dict[str, Any]]:
        kpis = kwargs.get("kpis", {})
        return detect_kpi_alerts_for_store(kpis, self._rules_path)


class SemanticSearchSkill(Skill):
    """Searches the RAG corpus for relevant business context."""

    def __init__(self, corpus_path: str | None = None) -> None:
        self._searcher = LocalHybridSearch(corpus_path or settings.rag_corpus_path)

    @property
    def descriptor(self) -> SkillDescriptor:
        return SkillDescriptor(
            name="semantic_search",
            description="Search the operational knowledge base for context relevant to a query.",
            parameters=[
                SkillParameter(name="query", type="string", description="Natural language search query"),
                SkillParameter(
                    name="top_k", type="number", description="Number of results to return", required=False, default=3
                ),
            ],
            tags=["rag", "retrieval", "context"],
        )

    def execute(self, **kwargs: Any) -> list[dict[str, Any]]:
        query = kwargs.get("query", "")
        top_k = int(kwargs.get("top_k", 3))
        return self._searcher.search(query, top_k=top_k)


class DiagnoseSignalsSkill(Skill):
    """Diagnoses operational signals and produces issue list with business impact."""

    @property
    def descriptor(self) -> SkillDescriptor:
        return SkillDescriptor(
            name="diagnose_signals",
            description="Analyze KPI and promotion signals to identify operational issues with business impact assessment.",
            parameters=[
                SkillParameter(name="kpis", type="object", description="Current KPI metrics"),
                SkillParameter(name="promotion", type="object", description="Promotion analysis results"),
            ],
            tags=["diagnosis", "analysis", "recommendation"],
        )

    def execute(self, **kwargs: Any) -> list[dict[str, str]]:
        agent = RecommendationAgent()
        return agent.diagnose_signals(
            kpis=kwargs.get("kpis", {}),
            promo=kwargs.get("promotion", {}),
        )


class GenerateNarrativeSkill(Skill):
    """Generates LLM-powered operational narrative from structured data."""

    @property
    def descriptor(self) -> SkillDescriptor:
        return SkillDescriptor(
            name="generate_narrative",
            description="Generate a natural-language operational brief using LLM from structured KPI/alert data.",
            parameters=[
                SkillParameter(name="readout", type="string", description="Structured operational readout text"),
                SkillParameter(
                    name="persona",
                    type="string",
                    description="Target persona (store_manager or executive)",
                    required=False,
                    default="store_manager",
                ),
            ],
            tags=["llm", "generation", "narrative"],
        )

    def execute(self, **kwargs: Any) -> str:
        readout = kwargs.get("readout", "")
        persona = kwargs.get("persona", "store_manager")

        if not os.environ.get(settings.llm.api_key_env_var):
            return readout

        user_prompt = OPERATIONAL_BRIEF.format_user(persona=persona, readout=readout)
        return llm_generate(user_prompt, system=OPERATIONAL_BRIEF.system)
