"""Tests for the heterogeneous graph module."""

import pytest

from sabogaapi.graph import EdgeType, HeterogeneousGraph, NodeType


class TestHeterogeneousGraph:
    """Test HeterogeneousGraph class."""

    @pytest.fixture
    def graph(self):
        """Create a test graph."""
        return HeterogeneousGraph()

    def test_add_node(self, graph):
        """Test adding nodes to the graph."""
        graph.add_node(1, NodeType.GAME, "Catan")
        assert graph.number_of_nodes() == 1
        node_attrs = graph.get_node(1)
        assert node_attrs["label"] == "Catan"
        assert node_attrs["type"] == "game"

    def test_add_multiple_nodes(self, graph):
        """Test adding multiple nodes of different types."""
        graph.add_node(1, NodeType.GAME, "Catan")
        graph.add_node(2, NodeType.MECHANIC, "Resource Trading")
        graph.add_node(3, NodeType.CATEGORY, "Economic")

        assert graph.number_of_nodes() == 3
        assert graph.get_node(1)["type"] == "game"
        assert graph.get_node(2)["type"] == "mechanic"
        assert graph.get_node(3)["type"] == "category"

    def test_get_nodes_by_type(self, graph):
        """Test retrieving nodes by type."""
        graph.add_node(1, NodeType.GAME, "Catan")
        graph.add_node(2, NodeType.GAME, "Ticket to Ride")
        graph.add_node(3, NodeType.MECHANIC, "Resource Trading")

        games = graph.get_nodes_by_type(NodeType.GAME)
        assert len(games) == 2

        mechanics = graph.get_nodes_by_type(NodeType.MECHANIC)
        assert len(mechanics) == 1

    def test_add_edge(self, graph):
        """Test adding edges to the graph."""
        graph.add_node(1, NodeType.GAME, "Catan")
        graph.add_node(2, NodeType.MECHANIC, "Resource Trading")

        graph.add_edge(1, 2, EdgeType.HAS_MECHANIC)
        assert graph.number_of_edges() == 1

    def test_add_edge_nonexistent_node(self, graph):
        """Test that adding an edge with nonexistent nodes raises error."""
        graph.add_node(1, NodeType.GAME, "Catan")

        with pytest.raises(ValueError):
            graph.add_edge(1, 999, EdgeType.HAS_MECHANIC)

    def test_get_outgoing_edges(self, graph):
        """Test retrieving outgoing edges."""
        graph.add_node(1, NodeType.GAME, "Catan")
        graph.add_node(2, NodeType.MECHANIC, "Resource Trading")
        graph.add_node(3, NodeType.MECHANIC, "Building")

        graph.add_edge(1, 2, EdgeType.HAS_MECHANIC)
        graph.add_edge(1, 3, EdgeType.HAS_MECHANIC)

        outgoing = graph.get_outgoing_edges(1)
        assert len(outgoing) == 2

    def test_get_incoming_edges(self, graph):
        """Test retrieving incoming edges."""
        graph.add_node(1, NodeType.GAME, "Catan")
        graph.add_node(2, NodeType.GAME, "Ticket to Ride")
        graph.add_node(3, NodeType.MECHANIC, "Resource Trading")

        graph.add_edge(1, 3, EdgeType.HAS_MECHANIC)
        graph.add_edge(2, 3, EdgeType.HAS_MECHANIC)

        incoming = graph.get_incoming_edges(3)
        assert len(incoming) == 2

    def test_get_edges_by_type(self, graph):
        """Test retrieving edges by type."""
        graph.add_node(1, NodeType.GAME, "Catan")
        graph.add_node(2, NodeType.MECHANIC, "Resource Trading")
        graph.add_node(3, NodeType.CATEGORY, "Economic")

        graph.add_edge(1, 2, EdgeType.HAS_MECHANIC)
        graph.add_edge(1, 3, EdgeType.HAS_CATEGORY)

        mechanics_edges = graph.get_edges_by_type(EdgeType.HAS_MECHANIC)
        assert len(mechanics_edges) == 1

        category_edges = graph.get_edges_by_type(EdgeType.HAS_CATEGORY)
        assert len(category_edges) == 1

    def test_get_neighbors(self, graph):
        """Test retrieving neighboring nodes."""
        graph.add_node(1, NodeType.GAME, "Catan")
        graph.add_node(2, NodeType.MECHANIC, "Resource Trading")
        graph.add_node(3, NodeType.CATEGORY, "Economic")

        graph.add_edge(1, 2, EdgeType.HAS_MECHANIC)
        graph.add_edge(1, 3, EdgeType.HAS_CATEGORY)

        neighbors = graph.get_neighbors(1)
        assert len(neighbors["outgoing"]) == 2
        assert len(neighbors.get("incoming", [])) == 0

    def test_get_statistics(self, graph):
        """Test graph statistics."""
        graph.add_node(1, NodeType.GAME, "Catan")
        graph.add_node(2, NodeType.GAME, "Ticket to Ride")
        graph.add_node(3, NodeType.MECHANIC, "Resource Trading")
        graph.add_node(4, NodeType.CATEGORY, "Economic")

        graph.add_edge(1, 3, EdgeType.HAS_MECHANIC)
        graph.add_edge(2, 3, EdgeType.HAS_MECHANIC)
        graph.add_edge(1, 4, EdgeType.HAS_CATEGORY)

        stats = graph.get_statistics()
        assert stats["total_nodes"] == 4
        assert stats["total_edges"] == 3
        assert stats["nodes_by_type"]["game"] == 2
        assert stats["nodes_by_type"]["mechanic"] == 1
        assert stats["nodes_by_type"]["category"] == 1
        assert stats["edges_by_type"]["has_mechanic"] == 2
        assert stats["edges_by_type"]["has_category"] == 1

    def test_to_dict(self, graph):
        """Test converting graph to dictionary."""
        graph.add_node(1, NodeType.GAME, "Catan")
        graph.add_node(2, NodeType.MECHANIC, "Resource Trading")
        graph.add_edge(1, 2, EdgeType.HAS_MECHANIC)

        graph_dict = graph.to_dict()
        assert len(graph_dict["nodes"]) == 2
        assert len(graph_dict["edges"]) == 1
        assert graph_dict["nodes"][0]["type"] == "game"
        assert graph_dict["edges"][0]["type"] == "has_mechanic"

    def test_get_networkx_graph(self, graph):
        """Test accessing the underlying NetworkX graph."""
        graph.add_node(1, NodeType.GAME, "Catan")
        graph.add_node(2, NodeType.MECHANIC, "Resource Trading")
        graph.add_edge(1, 2, EdgeType.HAS_MECHANIC)

        nx_graph = graph.get_networkx_graph()
        assert nx_graph.number_of_nodes() == 2
        assert nx_graph.number_of_edges() == 1
        assert nx_graph.nodes[1]["label"] == "Catan"

    def test_node_attributes(self, graph):
        """Test adding and retrieving node attributes."""
        graph.add_node(
            1,
            NodeType.GAME,
            "Catan",
            attributes={"year": 1995, "rating": 7.5},
        )
        node = graph.get_node(1)
        assert node["year"] == 1995
        assert node["rating"] == 7.5

    def test_edge_attributes(self, graph):
        """Test adding and retrieving edge attributes."""
        graph.add_node(1, NodeType.GAME, "Catan")
        graph.add_node(2, NodeType.MECHANIC, "Resource Trading")
        graph.add_edge(1, 2, EdgeType.HAS_MECHANIC, attributes={"strength": 0.9})

        edges = graph.get_edges_by_type(EdgeType.HAS_MECHANIC)
        assert edges[0][2]["strength"] == 0.9
