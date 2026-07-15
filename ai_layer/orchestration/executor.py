"""DAG executor with retry, fallback, per-node timeout, circuit breaker, and observability."""

from __future__ import annotations

import logging
import time
from concurrent.futures import Future, ThreadPoolExecutor, TimeoutError as FutureTimeoutError
from dataclasses import dataclass, field
from typing import Any

from ai_layer.orchestration.dag import AgentDAG, AgentNode, RetryPolicy
from observability.evaluation import tracker

logger = logging.getLogger(__name__)

# Default retry policy applied when a node has none specified
_DEFAULT_RETRY = RetryPolicy(max_retries=2, backoff_base_seconds=0.5, backoff_multiplier=2.0)

# ---------------------------------------------------------------------------
# Circuit breaker
# ---------------------------------------------------------------------------


@dataclass
class _CBState:
    failures: int = 0
    opened_at: float = 0.0


class CircuitBreaker:
    """Per-node circuit breaker with configurable threshold and cooldown.

    States:
        Closed  - normal operation; failures are counted.
        Open    - node is skipped immediately; entered when failures >= threshold.
        Half-open - after cooldown elapses, one probe is allowed through.
                    If it succeeds the breaker closes; if it fails it opens again.
    """

    def __init__(
        self,
        threshold: int = 3,
        cooldown_seconds: float = 60.0,
    ) -> None:
        self._threshold = threshold
        self._cooldown = cooldown_seconds
        self._states: dict[str, _CBState] = {}

    def is_open(self, name: str) -> bool:
        """Return True if the circuit is open and the cooldown has not elapsed."""
        state = self._states.get(name)
        if state is None or state.failures < self._threshold:
            return False
        elapsed = time.time() - state.opened_at
        if elapsed >= self._cooldown:
            # Cooldown elapsed - allow one half-open probe
            logger.info("Circuit breaker HALF-OPEN for node '%s' (elapsed %.1fs)", name, elapsed)
            return False
        return True

    def record_success(self, name: str) -> None:
        """Reset the breaker on a successful execution."""
        if name in self._states and self._states[name].failures >= self._threshold:
            logger.info("Circuit breaker CLOSED for node '%s' after successful probe", name)
        self._states.pop(name, None)

    def record_failure(self, name: str) -> None:
        """Increment failure count; trip the breaker when threshold is reached."""
        state = self._states.setdefault(name, _CBState())
        state.failures += 1
        if state.failures == self._threshold:
            state.opened_at = time.time()
            logger.warning(
                "Circuit breaker OPEN for node '%s' after %d failures",
                name,
                state.failures,
            )


# ---------------------------------------------------------------------------
# Execution result types
# ---------------------------------------------------------------------------


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
    circuit_open: bool = False
    timed_out: bool = False


@dataclass
class ExecutionTrace:
    """Full execution trace of a DAG run."""

    node_results: dict[str, NodeResult] = field(default_factory=dict)
    total_duration_ms: float = 0.0
    tiers_executed: int = 0
    aborted: bool = False
    abort_reason: str | None = None


# ---------------------------------------------------------------------------
# DAG Executor
# ---------------------------------------------------------------------------


class DAGExecutor:
    """Executes an AgentDAG with retry logic, fallback handlers, per-node timeout,
    circuit breaker, and parallel tier execution.

    Args:
        max_workers: Thread pool size for parallel tier execution.
        node_timeout_seconds: Maximum wall-clock seconds allowed for a single
            node attempt (not including retries).  ``None`` disables the timeout.
        circuit_breaker_threshold: Number of consecutive failures before a node's
            circuit is tripped.
        circuit_breaker_cooldown: Seconds to wait before allowing a half-open probe.
    """

    def __init__(
        self,
        max_workers: int = 4,
        node_timeout_seconds: float | None = 30.0,
        circuit_breaker_threshold: int = 3,
        circuit_breaker_cooldown: float = 60.0,
    ) -> None:
        self._max_workers = max_workers
        self._node_timeout = node_timeout_seconds
        self._circuit_breaker = CircuitBreaker(
            threshold=circuit_breaker_threshold,
            cooldown_seconds=circuit_breaker_cooldown,
        )

    def execute(self, dag: AgentDAG, context: dict[str, Any]) -> ExecutionTrace:
        """Run the full DAG against the shared context dict."""
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
                    trace.abort_reason = f"Required node '{nr.name}' failed after {nr.attempts} attempts: {nr.error}"
                    break

            trace.tiers_executed = tier_idx + 1
            if trace.aborted:
                break

        trace.total_duration_ms = (time.perf_counter() - start) * 1000
        return trace

    def _execute_tier(self, nodes: list[AgentNode], context: dict[str, Any]) -> list[NodeResult]:
        """Execute a tier of independent nodes in parallel with per-node timeout."""
        # Always use a pool so timeout applies uniformly to single-node tiers too
        results: list[NodeResult] = []
        with ThreadPoolExecutor(max_workers=min(self._max_workers, len(nodes))) as pool:
            future_to_node: dict[Future[NodeResult], AgentNode] = {
                pool.submit(self._execute_node, node, context): node for node in nodes
            }
            for future, node in future_to_node.items():
                try:
                    nr = future.result(timeout=self._node_timeout)
                    results.append(nr)
                except FutureTimeoutError:
                    logger.error("Node '%s' exceeded timeout of %.1fs", node.name, self._node_timeout)
                    self._circuit_breaker.record_failure(node.name)
                    tracker.record_execution(node.name, (self._node_timeout or 0) * 1000, success=False)
                    results.append(
                        NodeResult(
                            name=node.name,
                            success=False,
                            error=TimeoutError(f"Node '{node.name}' timed out after {self._node_timeout}s"),
                            attempts=1,
                            duration_ms=(self._node_timeout or 0) * 1000,
                            timed_out=True,
                        )
                    )
        return results

    def _execute_node(self, node: AgentNode, context: dict[str, Any]) -> NodeResult:
        """Execute a single node with circuit breaker check, retry, and fallback."""
        # Circuit breaker check - skip immediately if open
        if self._circuit_breaker.is_open(node.name):
            logger.warning("Circuit breaker OPEN: skipping node '%s'", node.name)
            tracker.record_execution(node.name, 0.0, success=False)
            return NodeResult(
                name=node.name,
                success=False,
                error=RuntimeError(f"Circuit breaker open for '{node.name}'"),
                attempts=0,
                circuit_open=True,
            )

        policy = node.retry_policy or _DEFAULT_RETRY
        last_error: Exception | None = None
        attempts = 0

        for attempt in range(1, policy.max_retries + 2):  # +2: initial + retries
            attempts = attempt
            start = time.perf_counter()
            try:
                result = node.run_fn(context)
                duration = (time.perf_counter() - start) * 1000
                self._circuit_breaker.record_success(node.name)
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
                    node.name,
                    attempt,
                    policy.max_retries + 1,
                    duration,
                    exc,
                )
                if attempt <= policy.max_retries:
                    backoff = policy.backoff_base_seconds * (policy.backoff_multiplier ** (attempt - 1))
                    time.sleep(backoff)

        # All retries exhausted - record failure in circuit breaker
        self._circuit_breaker.record_failure(node.name)

        # Try fallback
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
