"""Agent execution DAG — declarative graph of agent nodes and dependencies."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable


@dataclass
class RetryPolicy:
    """Retry configuration for an agent node."""

    max_retries: int = 2
    backoff_base_seconds: float = 0.5
    backoff_multiplier: float = 2.0
    retryable_exceptions: tuple[type[Exception], ...] = (Exception,)


@dataclass
class AgentNode:
    """A single node in the agent execution graph.

    Attributes:
        name: Unique agent identifier.
        run_fn: Callable that executes the agent. Receives the shared context dict
                and returns a result to be merged back.
        depends_on: Names of upstream nodes that must complete before this node runs.
        retry_policy: Retry configuration for this node.
        fallback_fn: Optional callable invoked when all retries are exhausted.
        optional: If True, failure does not abort the DAG.
    """

    name: str
    run_fn: Callable[[dict[str, Any]], Any]
    depends_on: list[str] = field(default_factory=list)
    retry_policy: RetryPolicy | None = None
    fallback_fn: Callable[[dict[str, Any], Exception], Any] | None = None
    optional: bool = False


class AgentDAG:
    """Directed acyclic graph of agent nodes with dependency tracking."""

    def __init__(self) -> None:
        self._nodes: dict[str, AgentNode] = {}

    def add_node(self, node: AgentNode) -> None:
        if node.name in self._nodes:
            raise ValueError(f"Duplicate node name: {node.name}")
        for dep in node.depends_on:
            if dep not in self._nodes:
                raise ValueError(
                    f"Node '{node.name}' depends on '{dep}' which has not been added yet. "
                    "Add nodes in topological order."
                )
        self._nodes[node.name] = node

    def get_node(self, name: str) -> AgentNode:
        return self._nodes[name]

    @property
    def nodes(self) -> dict[str, AgentNode]:
        return dict(self._nodes)

    def execution_order(self) -> list[list[str]]:
        """Return nodes grouped into execution tiers (parallelizable within each tier).

        Each tier contains nodes whose dependencies are all satisfied by prior tiers.
        """
        remaining = set(self._nodes.keys())
        completed: set[str] = set()
        tiers: list[list[str]] = []

        while remaining:
            tier = [
                name
                for name in remaining
                if all(dep in completed for dep in self._nodes[name].depends_on)
            ]
            if not tier:
                unresolved = {
                    name: self._nodes[name].depends_on
                    for name in remaining
                }
                raise ValueError(f"Cycle detected in DAG. Unresolved: {unresolved}")
            tiers.append(sorted(tier))
            completed.update(tier)
            remaining -= set(tier)

        return tiers

    def subgraph(self, target_nodes: list[str]) -> AgentDAG:
        """Return a new DAG containing only the target nodes and their transitive dependencies."""
        required: set[str] = set()
        stack = list(target_nodes)
        while stack:
            name = stack.pop()
            if name in required:
                continue
            if name not in self._nodes:
                raise ValueError(f"Unknown node: {name}")
            required.add(name)
            stack.extend(self._nodes[name].depends_on)

        sub = AgentDAG()
        for tier in self.execution_order():
            for name in tier:
                if name in required:
                    sub.add_node(self._nodes[name])
        return sub
