"""Tests for significant AI gaps 7-14: multi-turn conversation, MCP server,
auth/RBAC, CI/CD, model routing, LLM-as-judge, context assembly, observability export."""

import os
import pytest
from unittest.mock import patch

# ---------------------------------------------------------------------------
# 7. Multi-turn conversation (SessionMemory in orchestrator)
# ---------------------------------------------------------------------------
from ai_systems.retrieval.context import SessionMemory, StreamingStateStore, HybridContextAssembler


def test_session_memory_add_and_retrieve():
    mem = SessionMemory()
    sid = "test-session-1"
    mem.add_turn(sid, "user", "What is revenue?")
    mem.add_turn(sid, "assistant", "Revenue is $1.2M")
    turns = mem.get_history(sid)
    assert len(turns) == 2
    assert turns[0]["role"] == "user"
    assert turns[1]["role"] == "assistant"


def test_session_memory_separate_sessions():
    mem = SessionMemory()
    mem.add_turn("s1", "user", "Q1")
    mem.add_turn("s2", "user", "Q2")
    assert len(mem.get_history("s1")) == 1
    assert len(mem.get_history("s2")) == 1
    assert mem.get_history("s3") == []


def test_session_memory_max_turns():
    mem = SessionMemory(max_turns=3)
    for i in range(5):
        mem.add_turn("s1", "user", f"msg-{i}")
    turns = mem.get_history("s1")
    assert len(turns) == 3
    assert turns[0]["content"] == "msg-2"


# ---------------------------------------------------------------------------
# 7b. StreamingStateStore
# ---------------------------------------------------------------------------


def test_streaming_state_store():
    store = StreamingStateStore()
    store.update("req-1", {"status": "streaming", "tokens": 50})
    state = store.get("req-1")
    assert state is not None
    assert state["status"] == "streaming"
    assert state["tokens"] == 50
    store.update("req-1", {"status": "complete", "tokens": 200})
    assert store.get("req-1")["status"] == "complete"


def test_streaming_state_store_missing():
    store = StreamingStateStore()
    assert store.get("nonexistent") is None


# ---------------------------------------------------------------------------
# 7c. HybridContextAssembler
# ---------------------------------------------------------------------------


def test_context_assembler_returns_context_window():
    mem = SessionMemory()
    store = StreamingStateStore()
    assembler = HybridContextAssembler(streaming_store=store, memory=mem)
    ctx = assembler.assemble(query="How is revenue trending?")
    assert hasattr(ctx, "retrieval")
    assert hasattr(ctx, "streaming")
    assert isinstance(ctx.retrieval, list)


def test_context_assembler_with_session():
    mem = SessionMemory()
    mem.add_turn("s1", "user", "Prior question")
    store = StreamingStateStore()
    assembler = HybridContextAssembler(streaming_store=store, memory=mem)
    ctx = assembler.assemble(query="Follow up question", session_id="s1")
    assert len(ctx.memory) == 1


# ---------------------------------------------------------------------------
# 8. MCP server (import test)
# ---------------------------------------------------------------------------


def test_mcp_server_importable():
    """MCP server module should be importable."""
    import ai_systems.gateway.mcp.server  # noqa: F401


# ---------------------------------------------------------------------------
# 9. Auth / RBAC
# ---------------------------------------------------------------------------
from ai_systems.gateway.api.auth import (
    APIKeyRecord,
    register_api_key,
    _check_rbac,
    _DEFAULT_KEYS,
    _hash_key,
)


def test_register_api_key():
    _DEFAULT_KEYS.clear()
    register_api_key("test-key-1", role="operator", tenant="test")
    h = _hash_key("test-key-1")
    assert h in _DEFAULT_KEYS
    assert _DEFAULT_KEYS[h].role == "operator"


def test_rbac_admin_allows_all():
    assert _check_rbac("admin", ["kpi"]) is True
    assert _check_rbac("admin", ["observability"]) is True
    assert _check_rbac("admin", ["query"]) is True


def test_rbac_viewer_blocks_mutations():
    assert _check_rbac("viewer", ["kpi"]) is True
    assert _check_rbac("viewer", ["query"]) is False


def test_rbac_operator_allowed():
    assert _check_rbac("operator", ["query"]) is True
    assert _check_rbac("operator", ["kpi"]) is True
    assert _check_rbac("operator", ["observability"]) is False


# ---------------------------------------------------------------------------
# 11. Model routing / fallback
# ---------------------------------------------------------------------------
from ai_systems.core.model_router import (
    ModelRouter,
    TaskComplexity,
    ModelSpec,
    get_model_router,
)


def test_model_router_selects_by_complexity():
    router = ModelRouter()
    low = router.select(TaskComplexity.LOW)
    assert low.name == "haiku"
    med = router.select(TaskComplexity.MEDIUM)
    assert med.name == "sonnet"
    high = router.select(TaskComplexity.HIGH)
    assert high.name == "opus"


def test_model_router_infers_complexity():
    router = ModelRouter()
    # Should infer HIGH for analysis keywords
    model = router.select(task_hint="diagnose the root cause of revenue drop")
    assert model.name in ("opus", "sonnet")
    # Should infer LOW for classification keywords
    model = router.select(task_hint="classify this intent as kpi or alert")
    assert model.name == "haiku"


def test_model_router_fallback_on_failure():
    router = ModelRouter()
    router.mark_failed("opus")
    model = router.select(TaskComplexity.HIGH)
    # Should fallback to sonnet or haiku
    assert model.name in ("sonnet", "haiku")


def test_model_router_fallback_all_failed():
    router = ModelRouter()
    router.mark_failed("opus")
    router.mark_failed("sonnet")
    router.mark_failed("haiku")
    # Should reset and return sonnet
    model = router.select(TaskComplexity.MEDIUM)
    assert model.name == "sonnet"


def test_model_router_recovery():
    router = ModelRouter()
    router.mark_failed("haiku")
    router.mark_recovered("haiku")
    model = router.select(TaskComplexity.LOW)
    assert model.name == "haiku"


def test_model_router_get_all_models():
    router = ModelRouter()
    router.mark_failed("opus")
    models = router.get_all_models()
    assert len(models) == 3
    opus = next(m for m in models if m["name"] == "opus")
    assert opus["available"] is False


def test_model_router_singleton():
    r1 = get_model_router()
    r2 = get_model_router()
    assert r1 is r2


# ---------------------------------------------------------------------------
# 12. LLM-as-judge evaluation
# ---------------------------------------------------------------------------
from observability.evaluation import LLMEvaluator, EvalCriteria


def test_eval_relevance_with_matching_question():
    ev = LLMEvaluator()
    result = ev.evaluate(
        "Revenue is $1.2M this week, up 5% from last week.",
        context={"question": "What is the revenue this week?", "intent": "kpi_query"},
        criteria=[EvalCriteria.RELEVANCE],
    )
    assert len(result) == 1
    assert result[0].criteria == EvalCriteria.RELEVANCE
    assert result[0].score > 0.0


def test_eval_relevance_without_question():
    ev = LLMEvaluator()
    result = ev.evaluate(
        "Some output text.",
        context={},
        criteria=[EvalCriteria.RELEVANCE],
    )
    assert result[0].score == 0.5  # fallback score


def test_eval_persona_fit_executive():
    ev = LLMEvaluator()
    result = ev.evaluate(
        "The regional variance shows a strategic opportunity to reallocate budget for better ROI.",
        context={"persona": "executive"},
        criteria=[EvalCriteria.PERSONA_FIT],
    )
    assert result[0].score > 0.3


def test_eval_persona_fit_store_manager():
    ev = LLMEvaluator()
    result = ev.evaluate(
        "Your store's daily checkout rate has improved. Coaching the team on upsell during the shift could help.",
        context={"persona": "store_manager"},
        criteria=[EvalCriteria.PERSONA_FIT],
    )
    assert result[0].score > 0.3


def test_eval_all_criteria():
    ev = LLMEvaluator()
    results = ev.evaluate(
        "Revenue is strong at $1.2M for the store this daily period.",
        context={
            "question": "How is revenue?",
            "intent": "kpi_query",
            "persona": "store_manager",
            "kpis": {"revenue_total": 1200000},
        },
    )
    criteria_names = {r.criteria for r in results}
    assert EvalCriteria.GROUNDEDNESS in criteria_names
    assert EvalCriteria.RELEVANCE in criteria_names
    assert EvalCriteria.PERSONA_FIT in criteria_names


def test_eval_llm_judge_fallback_without_api_key():
    """Without an API key, evaluate_with_llm should fall back to rule-based."""
    ev = LLMEvaluator()
    with patch.dict(os.environ, {}, clear=False):
        # Ensure no API key
        env = os.environ.copy()
        env.pop("ANTHROPIC_API_KEY", None)
        with patch.dict(os.environ, env, clear=True):
            results = ev.evaluate_with_llm(
                "Test output",
                context={"question": "test"},
            )
            assert len(results) > 0


# ---------------------------------------------------------------------------
# 13. HybridContextAssembler integration
# ---------------------------------------------------------------------------


def test_context_assembler_rag_retrieval():
    mem = SessionMemory()
    store = StreamingStateStore()
    assembler = HybridContextAssembler(streaming_store=store, memory=mem)
    ctx = assembler.assemble(query="work order cycle time")
    assert ctx.retrieval is not None
    assert isinstance(ctx.retrieval, list)


def test_context_assembler_streaming_state():
    mem = SessionMemory()
    store = StreamingStateStore()
    store.update("alerts:store-42", {"severity": "high", "kpi": "revenue"})
    assembler = HybridContextAssembler(streaming_store=store, memory=mem)
    ctx = assembler.assemble(query="Any anomalies?", store_id="store-42")
    assert "active_alerts" in ctx.streaming


# ---------------------------------------------------------------------------
# 14. Observability / Prometheus export
# ---------------------------------------------------------------------------
from observability.evaluation import get_metrics_collector


def test_metrics_collector_singleton():
    c1 = get_metrics_collector()
    c2 = get_metrics_collector()
    assert c1 is c2


def test_metrics_collector_counter_and_snapshot():
    collector = get_metrics_collector()
    collector.increment("test_counter", labels={"env": "test"})
    snap = collector.snapshot()
    assert "test_counter{env=test}" in snap["counters"]


def test_metrics_collector_gauge():
    collector = get_metrics_collector()
    collector.gauge("test_gauge", 42.0, labels={"env": "test"})
    snap = collector.snapshot()
    assert snap["gauges"]["test_gauge{env=test}"] == 42.0


def test_metrics_collector_histogram():
    collector = get_metrics_collector()
    collector.observe("test_hist", 1.5, labels={"env": "test"})
    collector.observe("test_hist", 2.5, labels={"env": "test"})
    snap = collector.snapshot()
    hist = snap["histograms"]["test_hist{env=test}"]
    assert hist["count"] == 2
    assert hist["avg"] == 2.0


def test_prometheus_metrics_endpoint():
    """The /metrics endpoint should return Prometheus exposition format."""
    from fastapi.testclient import TestClient
    from ai_systems.gateway.api.app import app

    client = TestClient(app)
    # Seed a metric via the collector so it appears in the output
    collector = get_metrics_collector()
    collector.increment("agent_executions_total", labels={"agent": "kpi"})

    resp = client.get("/metrics")
    assert resp.status_code == 200
    assert "text/plain" in resp.headers["content-type"]
    body = resp.text
    assert "agent_executions_total" in body
    assert "# TYPE" in body
