"""DAG executor with retry, fallback, tier-parallel execution, and observability."""

from __future__ import annotations

import logging
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass, field
from typing import Any

from ai_layer.orchestration.dag import AgentDAG, AgentNode, RetryPolicy
from observability.evaluation import tracker

logger = logging.getLogger(__name__)

# Default retry policy applied when a node has none specified
_DEFAULT_RETRY = RetryPolicy(max_retries=2, backoff_base_seconds=0.5, backoff_multiplier=2.0)


@dataclass
class NodeResult:
    """Execution result for a single agent node."""

    name: str
    success: bool
    result: Any = None
    error: Exception | None = None
    attempts: int = 1
    duration_ms: float = 0.0
    used_fallback: bool = False


@dataclass
class ExecutionTrace:
    """Full execution trace of a DAG run."""

    node_results: dict[str, NodeResult] = field(default_factory=dict)
    total_duration_ms: float = 0.0
    tiers_executed: int = 0
    aborted: bool = False
    abort_reason: str | None = None


class DAGExecutor:
    """Executes an AgentDAG with retry logic, fallback handlers, and parallel tier execution.

    The executor walks the DAG tier by tier. Within each tier, independent nodes
    are executed in parallel using a thread pool. Failed nodes are retried according
    to their RetryPolicy. If all retries are exhausted, the fallback_fn (if any) is
    invoked. Non-optional node failures abort the remaining DAG execution.
    """

    def __init__(self, max_workers: int = 4) -> None:
        self._max_workers = max_workers

    def execute(self, dag: AgentDAG, context: dict[str, Any]) -> ExecutionTrace:
        """Run the full DAG against the shared context dict.

        Each node's run_fn receives `context` and its return value is stored
        under `context[node.name]` for downstream nodes.
        """
        trace = ExecutionTrace()
        start = time.perf_counter()
        tiers = dag.execution_order()

        for tier_idx, tier_names in enumerate(tiers):
            nodes = [dag.get_node(name) for name in tier_names]
            tier_results = self._execute_tier(nodes, context)

            for nr in tier_results:
                trace.node_results[nr.name] = nr
                if nr.success:
                    context[nr.name] = nr.result
                elif not dag.get_node(nr.name).optional:
                    trace.aborted = True
                    trace.abort_reason = (
                        f"Required node '{nr.name}' failed after {nr.attempts} attempts: {nr.error}"
                    )
                    break

            trace.tiers_executed = tier_idx + 1
            if trace.aborted:
                break

        trace.total_duration_ms = (time.perf_counter() - start) * 1000
        return trace

    def _execute_tier(
        self, nodes: list[AgentNode], context: dict[str, Any]
    ) -> list[NodeResult]:
        """Execute a tier of independent nodes, potentially in parallel."""
        if len(nodes) == 1:
            return [self._execute_node(nodes[0], context)]

        results: list[NodeResult] = []
        with ThreadPoolExecutor(max_workers=min(self._max_workers, len(nodes))) as pool:
            futures = {
                pool.submit(self._execute_node, node, context): node.name
                for node in nodes
            }
            for future in as_completed(futures):
                results.append(future.result())
        return results

    def _execute_node(self, node: AgentNode, context: dict[str, Any]) -> NodeResult:
        """Execute a single node with retry and fallback."""
        policy = node.retry_policy or _DEFAULT_RETRY
        last_error: Exception | None = None
        attempts = 0

        for attempt in range(1, policy.max_retries + 2):  # +2: initial + retries
            attempts = attempt
            start = time.perf_counter()
            try:
                result = node.run_fn(context)
                duration = (time.perf_counter() - start) * 1000
                nr = NodeResult(
                    name=node.name,
                    success=True,
                    result=result,
                    attempts=attempts,
                    duration_ms=duration,
                )
                tracker.record_execution(node.name, duration, success=True, attempts=attempts)
                return nr
            except policy.retryable_exceptions as exc:
                last_error = exc
                duration = (time.perf_counter() - start) * 1000
                logger.warning(
                    "Node '%s' failed attempt %d/%d (%.1fms): %s",
                    node.name, attempt, policy.max_retries + 1, duration, exc,
                )
                if attempt <= policy.max_retries:
                    backoff = policy.backoff_base_seconds * (policy.backoff_multiplier ** (attempt - 1))
                    time.sleep(backoff)

        # All retries exhausted — try fallback
        if node.fallback_fn is not None:
            try:
                fallback_result = node.fallback_fn(context, last_error)  # type: ignore[arg-type]
                nr = NodeResult(
                    name=node.name,
                    success=True,
                    result=fallback_result,
                    attempts=attempts,
                    duration_ms=0.0,
                    used_fallback=True,
                )
                tracker.record_execution(node.name, 0.0, success=True, used_fallback=True, attempts=attempts)
                return nr
            except Exception as fb_exc:
                logger.error("Fallback for node '%s' also failed: %s", node.name, fb_exc)
                last_error = fb_exc

        tracker.record_execution(node.name, 0.0, success=False, attempts=attempts)
        return NodeResult(
            name=node.name,
            success=False,
            error=last_error,
            attempts=attempts,
            duration_ms=0.0,
        )
