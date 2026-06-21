"""Central orchestrator brain — DAG-based agent execution with intent routing and retry/fallback."""

from functools import lru_cache
import logging
from typing import Any

from config.settings import settings
from ai_layer.agents.kpi_agent import KPIAgent
from ai_layer.agents.anomaly_agent import AnomalyAgent
from ai_layer.agents.promotion_agent import PromotionAgent
from ai_layer.agents.recommendation_agent import RecommendationAgent
from ai_layer.rag.retrieval.hybrid_search import LocalHybridSearch
from ai_layer.orchestration.dag import AgentDAG, AgentNode, RetryPolicy
from ai_layer.orchestration.router import IntentRouter, Intent
from ai_layer.orchestration.executor import DAGExecutor, ExecutionTrace

logger = logging.getLogger(__name__)


class Orchestrator:
    """Agent orchestrator that builds a DAG, routes by intent, and executes with retry/fallback."""

    def __init__(self) -> None:
        self.kpi_agent = KPIAgent()
        self.anomaly_agent = AnomalyAgent(settings.alert_rules_path)
        self.promotion_agent = PromotionAgent()
        self.recommendation_agent = RecommendationAgent()
        self.search = LocalHybridSearch(settings.rag_corpus_path)
        self.router = IntentRouter()
        self.executor = DAGExecutor(max_workers=4)

    # ------------------------------------------------------------------
    # DAG construction
    # ------------------------------------------------------------------

    def _build_dag(self) -> AgentDAG:
        """Build the full agent execution DAG.

        Execution tiers:
            Tier 0: kpi, rag_search  (independent, parallelizable)
            Tier 1: anomaly          (depends on kpi)
            Tier 2: promotion        (depends on kpi, rag_search)
            Tier 3: recommendation   (depends on kpi, anomaly, promotion, rag_search)
        """
        dag = AgentDAG()

        dag.add_node(AgentNode(
            name="kpi",
            run_fn=self._run_kpi,
            retry_policy=RetryPolicy(max_retries=2, backoff_base_seconds=0.3),
            fallback_fn=self._fallback_kpi,
        ))

        dag.add_node(AgentNode(
            name="rag_search",
            run_fn=self._run_rag_search,
            retry_policy=RetryPolicy(max_retries=1, backoff_base_seconds=0.2),
            fallback_fn=self._fallback_rag,
            optional=True,
        ))

        dag.add_node(AgentNode(
            name="anomaly",
            run_fn=self._run_anomaly,
            depends_on=["kpi"],
            retry_policy=RetryPolicy(max_retries=1),
            optional=True,
        ))

        dag.add_node(AgentNode(
            name="promotion",
            run_fn=self._run_promotion,
            depends_on=["kpi", "rag_search"],
            retry_policy=RetryPolicy(max_retries=1),
            optional=True,
        ))

        dag.add_node(AgentNode(
            name="recommendation",
            run_fn=self._run_recommendation,
            depends_on=["kpi", "anomaly", "promotion", "rag_search"],
            retry_policy=RetryPolicy(max_retries=1),
            fallback_fn=self._fallback_recommendation,
            optional=True,
        ))

        return dag

    # ------------------------------------------------------------------
    # Agent run functions (adapters between DAG context and agent APIs)
    # ------------------------------------------------------------------

    def _run_kpi(self, ctx: dict[str, Any]) -> dict[str, Any]:
        return self.kpi_agent.run(
            store_id=ctx.get("store_id"),
            region=ctx.get("region"),
        )

    def _run_rag_search(self, ctx: dict[str, Any]) -> list[dict[str, Any]]:
        return self.search.search(ctx.get("question", ""), top_k=3)

    def _run_anomaly(self, ctx: dict[str, Any]) -> list[dict[str, Any]]:
        kpis = ctx.get("kpi", {})
        return self.anomaly_agent.run(kpis)

    def _run_promotion(self, ctx: dict[str, Any]) -> dict[str, Any]:
        kpis = ctx.get("kpi", {})
        context_docs = ctx.get("rag_search", [])
        return self.promotion_agent.run(kpis, context_docs)

    def _run_recommendation(self, ctx: dict[str, Any]) -> str:
        kpis = ctx.get("kpi", {})
        alerts = ctx.get("anomaly", [])
        promo = ctx.get("promotion", {})
        context_docs = ctx.get("rag_search", [])
        persona = ctx.get("persona", "store_manager")
        return self.recommendation_agent.run(kpis, alerts, promo, context_docs, persona=persona)

    # ------------------------------------------------------------------
    # Fallback handlers
    # ------------------------------------------------------------------

    def _fallback_kpi(self, ctx: dict[str, Any], error: Exception) -> dict[str, Any]:
        logger.warning("KPI agent fallback triggered: %s", error)
        return {"store_id": ctx.get("store_id"), "region": ctx.get("region"), "_fallback": True}

    def _fallback_rag(self, ctx: dict[str, Any], error: Exception) -> list[dict[str, Any]]:
        logger.warning("RAG search fallback triggered: %s", error)
        return []

    def _fallback_recommendation(self, ctx: dict[str, Any], error: Exception) -> str:
        logger.warning("Recommendation agent fallback triggered: %s", error)
        return "Unable to generate recommendation at this time. Please review KPI data directly."

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def answer(
        self,
        question: str,
        store_id: str | None = None,
        region: str | None = None,
        persona: str = "store_manager",
    ) -> dict[str, Any]:
        """Route the question by intent, build the appropriate DAG subgraph, and execute."""

        # Phase 1: Intent classification + routing
        route = self.router.classify(question)
        logger.info("Intent: %s (confidence=%.2f), agents=%s", route.intent, route.confidence, route.required_agents)

        # Phase 2: Build DAG and extract subgraph for this intent
        full_dag = self._build_dag()
        dag = full_dag.subgraph(route.required_agents)

        # Phase 3: Execute DAG with shared context
        ctx: dict[str, Any] = {
            "question": question,
            "store_id": store_id,
            "region": region,
            "persona": persona,
            "intent": route.intent.value,
        }
        trace = self.executor.execute(dag, ctx)

        # Phase 4: Assemble response from execution results
        kpis = ctx.get("kpi", {})
        alerts = ctx.get("anomaly", [])
        context_docs = ctx.get("rag_search", [])
        promotion = ctx.get("promotion", {})
        answer_text = ctx.get("recommendation", "")

        # Build operational brief if recommendation agent was involved
        operational_brief = None
        if "recommendation" in route.required_agents:
            operational_brief = self.recommendation_agent.build_operational_brief(
                kpis, alerts, promotion, context_docs, persona=persona,
            )

        return {
            "question": question,
            "persona": persona,
            "intent": route.intent.value,
            "intent_confidence": route.confidence,
            "scope": {"store_id": store_id, "region": region},
            "kpis": kpis,
            "alerts": alerts,
            "retrieved_context": context_docs,
            "promotion_analysis": promotion,
            "operational_brief": operational_brief,
            "answer": answer_text,
            "execution_trace": _summarize_trace(trace),
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
            "intent": result["intent"],
            "scope": result["scope"],
            "kpis": result["kpis"],
            "alerts": result["alerts"],
            "operational_brief": result["operational_brief"],
            "execution_trace": result["execution_trace"],
        }


def _summarize_trace(trace: ExecutionTrace) -> dict[str, Any]:
    """Produce a serializable summary of the execution trace."""
    return {
        "total_duration_ms": round(trace.total_duration_ms, 1),
        "tiers_executed": trace.tiers_executed,
        "aborted": trace.aborted,
        "abort_reason": trace.abort_reason,
        "nodes": {
            name: {
                "success": nr.success,
                "attempts": nr.attempts,
                "duration_ms": round(nr.duration_ms, 1),
                "used_fallback": nr.used_fallback,
                "error": str(nr.error) if nr.error else None,
            }
            for name, nr in trace.node_results.items()
        },
    }


@lru_cache(maxsize=1)
def get_orchestrator() -> Orchestrator:
    return Orchestrator()
