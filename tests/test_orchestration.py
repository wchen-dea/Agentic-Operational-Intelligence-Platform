"""Tests for the orchestration layer: DAG, router, and executor."""

from ai_layer.orchestration.dag import AgentDAG, AgentNode, RetryPolicy
from ai_layer.orchestration.router import IntentRouter, Intent
from ai_layer.orchestration.executor import DAGExecutor


class TestAgentDAG:
    def test_execution_order_linear(self):
        dag = AgentDAG()
        dag.add_node(AgentNode(name="a", run_fn=lambda ctx: None))
        dag.add_node(AgentNode(name="b", run_fn=lambda ctx: None, depends_on=["a"]))
        dag.add_node(AgentNode(name="c", run_fn=lambda ctx: None, depends_on=["b"]))
        tiers = dag.execution_order()
        assert tiers == [["a"], ["b"], ["c"]]

    def test_execution_order_parallel_tier(self):
        dag = AgentDAG()
        dag.add_node(AgentNode(name="a", run_fn=lambda ctx: None))
        dag.add_node(AgentNode(name="b", run_fn=lambda ctx: None))
        dag.add_node(AgentNode(name="c", run_fn=lambda ctx: None, depends_on=["a", "b"]))
        tiers = dag.execution_order()
        assert tiers == [["a", "b"], ["c"]]

    def test_subgraph_extracts_transitive_deps(self):
        dag = AgentDAG()
        dag.add_node(AgentNode(name="kpi", run_fn=lambda ctx: None))
        dag.add_node(AgentNode(name="rag", run_fn=lambda ctx: None))
        dag.add_node(AgentNode(name="anomaly", run_fn=lambda ctx: None, depends_on=["kpi"]))
        dag.add_node(AgentNode(name="promo", run_fn=lambda ctx: None, depends_on=["kpi", "rag"]))
        sub = dag.subgraph(["anomaly"])
        assert set(sub.nodes.keys()) == {"kpi", "anomaly"}


class TestIntentRouter:
    def test_kpi_intent(self):
        router = IntentRouter()
        result = router.classify("What is the revenue for store 42?")
        assert result.intent == Intent.KPI_QUERY
        assert "kpi" in result.required_agents

    def test_anomaly_intent(self):
        router = IntentRouter()
        result = router.classify("Are there any active alerts or threshold breaches?")
        assert result.intent == Intent.ANOMALY_CHECK

    def test_promotion_intent(self):
        router = IntentRouter()
        result = router.classify("How is the current promotion campaign performing?")
        assert result.intent == Intent.PROMOTION_ANALYSIS

    def test_operational_brief_intent(self):
        router = IntentRouter()
        result = router.classify("Give me an operational summary for my store")
        assert result.intent == Intent.OPERATIONAL_BRIEF

    def test_general_fallback(self):
        router = IntentRouter()
        result = router.classify("Hello, how are you today?")
        assert result.intent == Intent.GENERAL_QA
        assert result.confidence < 0.5


class TestDAGExecutor:
    def test_successful_execution(self):
        dag = AgentDAG()
        dag.add_node(AgentNode(name="a", run_fn=lambda ctx: 10))
        dag.add_node(AgentNode(name="b", run_fn=lambda ctx: ctx["a"] * 2, depends_on=["a"]))

        executor = DAGExecutor()
        ctx: dict = {}
        trace = executor.execute(dag, ctx)

        assert not trace.aborted
        assert ctx["a"] == 10
        assert ctx["b"] == 20
        assert trace.node_results["a"].success
        assert trace.node_results["b"].success

    def test_retry_on_failure(self):
        call_count = {"n": 0}

        def flaky(ctx):
            call_count["n"] += 1
            if call_count["n"] < 3:
                raise ValueError("transient")
            return "ok"

        dag = AgentDAG()
        dag.add_node(
            AgentNode(
                name="flaky",
                run_fn=flaky,
                retry_policy=RetryPolicy(max_retries=2, backoff_base_seconds=0.01),
            )
        )

        executor = DAGExecutor()
        trace = executor.execute(dag, {})
        assert trace.node_results["flaky"].success
        assert trace.node_results["flaky"].attempts == 3

    def test_fallback_on_exhausted_retries(self):
        dag = AgentDAG()
        dag.add_node(
            AgentNode(
                name="broken",
                run_fn=lambda ctx: 1 / 0,
                retry_policy=RetryPolicy(max_retries=0),
                fallback_fn=lambda ctx, exc: "fallback_value",
            )
        )

        executor = DAGExecutor()
        ctx: dict = {}
        trace = executor.execute(dag, ctx)
        assert ctx["broken"] == "fallback_value"
        assert trace.node_results["broken"].used_fallback

    def test_optional_node_failure_doesnt_abort(self):
        dag = AgentDAG()
        dag.add_node(AgentNode(name="required", run_fn=lambda ctx: "ok"))
        dag.add_node(
            AgentNode(
                name="optional_fail",
                run_fn=lambda ctx: 1 / 0,
                depends_on=["required"],
                retry_policy=RetryPolicy(max_retries=0),
                optional=True,
            )
        )
        dag.add_node(
            AgentNode(
                name="after",
                run_fn=lambda ctx: "still_runs",
                depends_on=["required"],
            )
        )

        executor = DAGExecutor()
        ctx: dict = {}
        trace = executor.execute(dag, ctx)
        assert not trace.aborted
        assert ctx.get("after") == "still_runs"
        assert not trace.node_results["optional_fail"].success
