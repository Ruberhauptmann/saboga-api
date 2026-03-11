"""Heterogeneous graph data structures and types."""

from enum import Enum
from typing import Any

import networkx as nx


class NodeType(str, Enum):
    """Types of nodes in the heterogeneous graph."""

    GAME = "game"
    MECHANIC = "mechanic"
    DESIGNER = "designer"
    CATEGORY = "category"


class EdgeType(str, Enum):
    """Types of edges in the heterogeneous graph."""

    HAS_MECHANIC = "has_mechanic"
    HAS_CATEGORY = "has_category"
    HAS_DESIGNER = "has_designer"


class HeterogeneousGraph:
    """A heterogeneous graph using NetworkX as the underlying representation.

    Supports multiple node and edge types with efficient querying and
    access to NetworkX's rich set of graph algorithms.
    """

    def __init__(self) -> None:
        """Initialize an empty heterogeneous graph."""
        self.graph = nx.DiGraph()

    def add_node(
        self,
        node_id: str,
        node_type: NodeType,
        label: str,
        attributes: dict[str, Any] | None = None,
    ) -> None:
        """Add a node to the graph.

        Args:
            node_id: Unique identifier for the node
            node_type: Type of the node
            label: Human-readable label for the node
            attributes: Optional dictionary of node attributes
        """
        attrs = attributes or {}
        self.graph.add_node(
            node_id,
            type=node_type.value,
            label=label,
            **attrs,
        )

    def add_edge(
        self,
        source_id: str,
        target_id: str,
        edge_type: EdgeType,
        attributes: dict[str, Any] | None = None,
    ) -> None:
        """Add an edge to the graph.

        Args:
            source_id: ID of the source node
            target_id: ID of the target node
            edge_type: Type of the edge
            attributes: Optional dictionary of edge attributes

        Raises:
            ValueError: If source or target node doesn't exist
        """
        if source_id not in self.graph.nodes:
            error_msg = f"Source node {source_id} does not exist in graph"
            raise ValueError(error_msg)
        if target_id not in self.graph.nodes:
            error_msg = f"Target node {target_id} does not exist in graph"
            raise ValueError(error_msg)

        attrs = attributes or {}
        self.graph.add_edge(
            source_id,
            target_id,
            edge_type=edge_type.value,
            **attrs,
        )

    def get_node(self, node_id: int) -> dict[str, Any] | None:
        """Get a node by its ID.

        Args:
            node_id: The node ID

        Returns:
            Node attributes dictionary or None if not found
        """
        if node_id in self.graph.nodes:
            return dict(self.graph.nodes[node_id])
        return None

    def get_nodes_by_type(
        self, node_type: NodeType
    ) -> list[tuple[str, dict[str, Any]]]:
        """Get all nodes of a specific type.

        Args:
            node_type: The type of nodes to retrieve

        Returns:
            List of (node_id, attributes) tuples
        """
        return [
            (node_id, dict(attrs))
            for node_id, attrs in self.graph.nodes(data=True)
            if attrs.get("type") == node_type.value
        ]

    def get_outgoing_edges(
        self, source_id: int
    ) -> list[tuple[int, int, dict[str, Any]]]:
        """Get all outgoing edges from a node.

        Args:
            source_id: The source node ID

        Returns:
            List of (source, target, attributes) tuples
        """
        return [
            (source_id, target_id, dict(attrs))
            for source_id, target_id, attrs in self.graph.out_edges(
                source_id, data=True
            )
        ]

    def get_incoming_edges(
        self, target_id: int
    ) -> list[tuple[int, int, dict[str, Any]]]:
        """Get all incoming edges to a node.

        Args:
            target_id: The target node ID

        Returns:
            List of (source, target, attributes) tuples
        """
        return [
            (source_id, target_id, dict(attrs))
            for source_id, target_id, attrs in self.graph.in_edges(target_id, data=True)
        ]

    def get_edges_by_type(
        self, edge_type: EdgeType
    ) -> list[tuple[int, int, dict[str, Any]]]:
        """Get all edges of a specific type.

        Args:
            edge_type: The type of edges to retrieve

        Returns:
            List of (source, target, attributes) tuples
        """
        return [
            (source_id, target_id, dict(attrs))
            for source_id, target_id, attrs in self.graph.edges(data=True)
            if attrs.get("edge_type") == edge_type.value
        ]

    def get_neighbors(
        self, node_id: int, direction: str = "both"
    ) -> dict[str, list[tuple[int, dict[str, Any]]]]:
        """Get neighboring nodes.

        Args:
            node_id: The node ID
            direction: 'outgoing', 'incoming', or 'both'

        Returns:
            Dictionary with 'outgoing' and/or 'incoming' keys containing
            (node_id, attributes) tuples
        """
        neighbors: dict[str, list[tuple[int, dict[str, Any]]]] = {}

        if direction in ("outgoing", "both"):
            neighbors["outgoing"] = [
                (target_id, dict(self.graph.nodes[target_id]))
                for target_id in self.graph.successors(node_id)
            ]

        if direction in ("incoming", "both"):
            neighbors["incoming"] = [
                (source_id, dict(self.graph.nodes[source_id]))
                for source_id in self.graph.predecessors(node_id)
            ]

        return neighbors

    def get_statistics(self) -> dict[str, Any]:
        """Get graph statistics.

        Returns:
            Dictionary containing graph statistics
        """
        nodes_by_type = {}
        for node_type in NodeType:
            nodes = self.get_nodes_by_type(node_type)
            if nodes:
                nodes_by_type[node_type.value] = len(nodes)

        edges_by_type = {}
        for edge_type in EdgeType:
            edges = self.get_edges_by_type(edge_type)
            if edges:
                edges_by_type[edge_type.value] = len(edges)

        return {
            "total_nodes": self.graph.number_of_nodes(),
            "total_edges": self.graph.number_of_edges(),
            "nodes_by_type": nodes_by_type,
            "edges_by_type": edges_by_type,
        }

    def to_dict(self) -> dict[str, Any]:
        """Convert graph to dictionary representation.

        Returns:
            Dictionary representation of the graph
        """
        nodes = [
            {
                "id": node_id,
                "type": attrs.get("type"),
                "label": attrs.get("label"),
                "attributes": {
                    k: v for k, v in attrs.items() if k not in ("type", "label")
                },
            }
            for node_id, attrs in self.graph.nodes(data=True)
        ]

        edges = [
            {
                "source": source_id,
                "target": target_id,
                "type": attrs.get("edge_type"),
                "attributes": {k: v for k, v in attrs.items() if k != "edge_type"},
            }
            for source_id, target_id, attrs in self.graph.edges(data=True)
        ]

        return {"nodes": nodes, "edges": edges}

    def get_networkx_graph(self) -> nx.DiGraph:
        """Get the underlying NetworkX DiGraph for advanced analysis.

        Returns:
            The underlying NetworkX DiGraph object
        """
        return self.graph

    def number_of_nodes(self) -> int:
        """Get the number of nodes in the graph."""
        return self.graph.number_of_nodes()

    def number_of_edges(self) -> int:
        """Get the number of edges in the graph."""
        return self.graph.number_of_edges()
