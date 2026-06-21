from functools import lru_cache
from typing import Any

from config.settings import settings
from ai_layer.agents.kpi_agent import KPIAgent
from ai_layer.agents.anomaly_agent import AnomalyAgent
from ai_layer.agents.promotion_agent import PromotionAgent
from ai_layer.agents.recommendation_agent import RecommendationAgent
from ai_layer.rag.retrieval.hybrid_search import LocalHybridSearch


class Orchestrator:
    def __init__(self):
        self.kpi_agent = KPIAgent()
        self.anomaly_agent = AnomalyAgent(settings.alert_rules_path)
        self.promotion_agent = PromotionAgent()
        self.recommendation_agent = RecommendationAgent()
        self.search = LocalHybridSearch(settings.rag_corpus_path)

    def answer(
        self,
        question: str,
        store_id: str | None = None,
        region: str | None = None,
        persona: str = "store_manager",
    ) -> dict[str, Any]:
        kpis = self.kpi_agent.run(store_id=store_id, region=region)
        alerts = self.anomaly_agent.run(kpis)
        context_docs = self.search.search(question, top_k=3)
        promotion = self.promotion_agent.run(kpis, context_docs)
        answer = self.recommendation_agent.run(kpis, alerts, promotion, context_docs, persona=persona)
        operational_brief = self.recommendation_agent.build_operational_brief(
            kpis,
            alerts,
            promotion,
            context_docs,
            persona=persona,
        )
        return {
            "question": question,
            "persona": persona,
            "scope": {"store_id": store_id, "region": region},
            "kpis": kpis,
            "alerts": alerts,
            "retrieved_context": context_docs,
            "promotion_analysis": promotion,
            "operational_brief": operational_brief,
            "answer": answer,
        }

    def get_operational_brief(
        self,
        store_id: str | None = None,
        region: str | None = None,
        persona: str = "store_manager",
    ) -> dict[str, Any]:
        question = "Provide an operational KPI and alert brief for strategy adjustment."
        result = self.answer(
            question=question,
            store_id=store_id,
            region=region,
            persona=persona,
        )
        return {
            "question": question,
            "persona": persona,
            "scope": result["scope"],
            "kpis": result["kpis"],
            "alerts": result["alerts"],
            "operational_brief": result["operational_brief"],
        }


@lru_cache(maxsize=1)
def get_orchestrator() -> Orchestrator:
    return Orchestrator()
