"""Error propagation graphs — map the cracks and find the golden joints.

When errors cascade through a system, they form cracks that propagate
from component to component.  This module builds directed graphs of
error propagation and identifies *golden joints* — the points where
repair effort is most effective.

Classes:
    CrackGraph  — Directed graph of error propagation between components.
    GoldenJoint — A repair point in the graph with impact score.

Functions:
    build_crack_graph    — Build a graph from error records.
    find_golden_joints   — Identify the most impactful repair points.
    shortest_crack_path  — Find the shortest error propagation path.
"""

from __future__ import annotations

from collections import defaultdict, deque
from dataclasses import dataclass, field
from typing import Any


@dataclass
class GoldenJoint:
    """A repair point where intervention is most effective.

    Attributes:
        component:   The node in the crack graph.
        impact:      How many downstream failures this joint prevents.
        error_count: Number of errors seen at this component.
        suggestion:  What to fix here.
    """

    component: str
    impact: float
    error_count: int
    suggestion: str = ""

    @property
    def is_high_impact(self) -> bool:
        """True if impact >= 3 downstream failures prevented."""
        return self.impact >= 3

    def __str__(self) -> str:
        return (
            f"GoldenJoint({self.component}, impact={self.impact:.1f}, "
            f"errors={self.error_count})"
        )


@dataclass
class CrackGraph:
    """Directed graph of error propagation between components.

    Nodes are component names (strings).  Edges represent error
    propagation: an edge from A to B means errors in A cause errors in B.

    Attributes:
        nodes:           Set of component names.
        edges:           Adjacency list: source → list of targets.
        error_counts:    Per-node count of errors observed.
        edge_weights:    (source, target) → number of propagations.
    """

    nodes: set[str] = field(default_factory=set)
    edges: dict[str, list[str]] = field(default_factory=lambda: defaultdict(list))
    error_counts: dict[str, int] = field(default_factory=lambda: defaultdict(int))
    edge_weights: dict[tuple[str, str], int] = field(default_factory=lambda: defaultdict(int))

    def add_node(self, name: str) -> None:
        """Add a component node."""
        self.nodes.add(name)

    def add_edge(self, source: str, target: str, weight: int = 1) -> None:
        """Add an error propagation edge.

        Args:
            source: Where the error originates.
            target: Where the error propagates to.
            weight: Number of times this propagation was observed.
        """
        self.add_node(source)
        self.add_node(target)
        if target not in self.edges[source]:
            self.edges[source].append(target)
        self.edge_weights[(source, target)] += weight

    def record_error(self, component: str, count: int = 1) -> None:
        """Record that an error occurred at a component."""
        self.add_node(component)
        self.error_counts[component] += count

    def downstream(self, component: str) -> set[str]:
        """Return all components reachable from *component*.

        Args:
            component: Starting node.

        Returns:
            Set of all downstream component names.

        Examples:
            >>> g = CrackGraph()
            >>> g.add_edge("A", "B")
            >>> g.add_edge("B", "C")
            >>> g.downstream("A") == {"B", "C"}
            True
        """
        visited: set[str] = set()
        queue = deque(self.edges.get(component, []))
        while queue:
            node = queue.popleft()
            if node not in visited:
                visited.add(node)
                queue.extend(self.edges.get(node, []))
        return visited

    def upstream(self, component: str) -> set[str]:
        """Return all components that can reach *component*.

        Args:
            component: Target node.

        Returns:
            Set of all upstream component names.
        """
        # Build reverse adjacency
        reverse: dict[str, list[str]] = defaultdict(list)
        for src, targets in self.edges.items():
            for tgt in targets:
                reverse[tgt].append(src)

        visited: set[str] = set()
        queue = deque(reverse.get(component, []))
        while queue:
            node = queue.popleft()
            if node not in visited:
                visited.add(node)
                queue.extend(reverse.get(node, []))
        return visited

    def __len__(self) -> int:
        return len(self.nodes)


def build_crack_graph(errors: list[dict[str, Any]]) -> CrackGraph:
    """Build a CrackGraph from a list of error records.

    Each error dict should have:
      - ``"source"``: Component where the error originated.
      - ``"target"`` (optional): Component the error propagated to.
      - ``"error_type"`` (optional): Type of error.
      - ``"weight"`` (optional, default 1): Propagation count.

    Args:
        errors: List of error record dicts.

    Returns:
        A populated CrackGraph.

    Examples:
        >>> graph = build_crack_graph([
        ...     {"source": "db", "target": "api", "error_type": "TimeoutError"},
        ...     {"source": "api", "target": "ui", "error_type": "ConnectionError"},
        ... ])
        >>> len(graph)
        3
        >>> "db" in graph.nodes
        True
    """
    graph = CrackGraph()
    for error in errors:
        source = error.get("source", "unknown")
        target = error.get("target")
        weight = error.get("weight", 1)

        graph.record_error(source)
        if target:
            graph.add_edge(source, target, weight)

    return graph


def find_golden_joints(graph: CrackGraph, top_n: int | None = None) -> list[GoldenJoint]:
    """Identify the most impactful repair points in the graph.

    A golden joint is a component where repair prevents the most
    downstream failures.  Impact is measured as the number of
    downstream components reachable from that node, weighted by
    their error counts.

    Args:
        graph: The crack graph to analyze.
        top_n: Return only the top N joints (None = all).

    Returns:
        List of GoldenJoint objects, sorted by impact (descending).

    Examples:
        >>> g = CrackGraph()
        >>> g.add_edge("A", "B"); g.add_edge("B", "C"); g.add_edge("B", "D")
        >>> g.record_error("A", 5); g.record_error("B", 3)
        >>> joints = find_golden_joints(g)
        >>> joints[0].component
        'A'
    """
    joints: list[GoldenJoint] = []
    for node in graph.nodes:
        downstream = graph.downstream(node)
        # Impact = sum of error counts in downstream nodes + own errors
        impact = graph.error_counts.get(node, 0)
        for ds_node in downstream:
            impact += graph.error_counts.get(ds_node, 0)

        joints.append(GoldenJoint(
            component=node,
            impact=impact,
            error_count=graph.error_counts.get(node, 0),
            suggestion=f"Add error handling at {node} to protect {len(downstream)} downstream components.",
        ))

    joints.sort(key=lambda j: j.impact, reverse=True)
    if top_n is not None:
        joints = joints[:top_n]
    return joints


def shortest_crack_path(
    graph: CrackGraph,
    source: str,
    target: str,
) -> list[str] | None:
    """Find the shortest error propagation path between two components.

    Uses BFS to find the minimum-hop path from *source* to *target*.

    Args:
        graph:  The crack graph.
        source: Starting component.
        target: Destination component.

    Returns:
        List of component names forming the shortest path, or None
        if no path exists.

    Examples:
        >>> g = CrackGraph()
        >>> g.add_edge("A", "B"); g.add_edge("B", "C"); g.add_edge("A", "C")
        >>> shortest_crack_path(g, "A", "C")
        ['A', 'C']
        >>> shortest_crack_path(g, "C", "A") is None
        True
    """
    if source not in graph.nodes or target not in graph.nodes:
        return None
    if source == target:
        return [source]

    # BFS
    visited: set[str] = {source}
    queue: deque[tuple[str, list[str]]] = deque([(source, [source])])

    while queue:
        current, path = queue.popleft()
        for neighbor in graph.edges.get(current, []):
            if neighbor == target:
                return path + [neighbor]
            if neighbor not in visited:
                visited.add(neighbor)
                queue.append((neighbor, path + [neighbor]))

    return None
