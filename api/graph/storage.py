"""Service for managing graph storage and retrieval using Django ORM."""

from typing import Optional

from django.utils import timezone

from . import HeterogeneousGraph
from .builder import GraphBuilder
from .projections import GraphProjector
from .. import models


class GraphStorageService:
    """Service for storing and retrieving graphs from the database."""

    @staticmethod
    def save_heterogeneous_graph(
        graph: HeterogeneousGraph, metadata: dict | None = None
    ) -> models.HeterogeneousGraphData:
        """Save a heterogeneous graph to the database.

        Args:
            graph: The :class:`HeterogeneousGraph` to save
            metadata: Optional metadata to store with the graph

        Returns:
            The created or updated :class:`HeterogeneousGraphData` record

        """
        graph_dict = graph.to_dict()
        existing = models.HeterogeneousGraphData.objects.first()
        if existing:
            existing.nodes = graph_dict["nodes"]
            existing.edges = graph_dict["edges"]
            existing.meta = metadata or {}
            existing.updated_at = timezone.now()
            existing.save()
            return existing

        return models.HeterogeneousGraphData.objects.create(
            nodes=graph_dict["nodes"],
            edges=graph_dict["edges"],
            meta=metadata or {},
            created_at=timezone.now(),
        )

    @staticmethod
    def load_heterogeneous_graph() -> Optional[HeterogeneousGraph]:
        """Load the heterogeneous graph from the database.

        Returns:
            The loaded :class:`HeterogeneousGraph` or ``None`` if not found

        """
        graph_data = models.HeterogeneousGraphData.objects.first()
        if not graph_data:
            return None

        graph = HeterogeneousGraph()
        for node in graph_data.nodes:
            graph.add_node(
                node_id=node["id"],
                node_type=node.get("type"),
                label=node.get("label"),
                attributes=node.get("attributes", {}),
            )
        for edge in graph_data.edges:
            graph.add_edge(
                source_id=edge["source"],
                target_id=edge["target"],
                edge_type=edge.get("type"),
                attributes=edge.get("attributes", {}),
            )
        return graph

    @staticmethod
    def save_projected_graph(
        graph_type: str, graph: HeterogeneousGraph, metadata: dict | None = None
    ) -> models.ProjectedGraphData:
        """Save a projected graph to the database.

        Args:
            graph_type: Type of projection (e.g. 'game-game', 'mechanic-mechanic')
            graph: The projected :class:`HeterogeneousGraph`
            metadata: Optional metadata to store with the graph

        Returns:
            The created or updated :class:`ProjectedGraphData` record

        """
        graph_dict = graph.to_dict()
        existing = models.ProjectedGraphData.objects.filter(
            graph_type=graph_type
        ).first()
        if existing:
            existing.nodes = graph_dict["nodes"]
            existing.edges = graph_dict["edges"]
            existing.meta = metadata or {}
            existing.updated_at = timezone.now()
            existing.save()
            return existing

        return models.ProjectedGraphData.objects.create(
            graph_type=graph_type,
            nodes=graph_dict["nodes"],
            edges=graph_dict["edges"],
            meta=metadata or {},
            created_at=timezone.now(),
        )

    @staticmethod
    def load_projected_graph(graph_type: str) -> Optional[HeterogeneousGraph]:
        """Load a projected graph from the database.

        Args:
            graph_type: The projection type

        Returns:
            The loaded :class:`HeterogeneousGraph` or ``None`` if not found

        """
        graph_data = models.ProjectedGraphData.objects.filter(
            graph_type=graph_type
        ).first()
        if not graph_data:
            return None

        graph = HeterogeneousGraph()
        for node in graph_data.nodes:
            graph.add_node(
                node_id=node["id"],
                node_type=node.get("type"),
                label=node.get("label"),
                attributes=node.get("attributes", {}),
            )
        for edge in graph_data.edges:
            graph.add_edge(
                source_id=edge["source"],
                target_id=edge["target"],
                edge_type=edge.get("type"),
                attributes=edge.get("attributes", {}),
            )
        return graph

    @staticmethod
    def build_and_save_all_graphs() -> dict:
        """Build and save every graph (heterogeneous + all projections).

        Returns:
            Summary dictionary with counts for each graph saved

        """
        hetero = GraphBuilder.build_graph()
        GraphStorageService.save_heterogeneous_graph(
            hetero,
            metadata={
                "total_nodes": hetero.number_of_nodes(),
                "total_edges": hetero.number_of_edges(),
            },
        )

        projections = {
            "game-mechanic": (
                GraphProjector.project_game_to_game(hetero, "mechanic"),
                {"connection_type": "mechanic"},
            ),
            "game-category": (
                GraphProjector.project_game_to_game(hetero, "category"),
                {"connection_type": "category"},
            ),
            "game-designer": (
                GraphProjector.project_game_to_game(hetero, "designer"),
                {"connection_type": "designer"},
            ),
            "mechanic-mechanic": (
                GraphProjector.project_mechanic_to_mechanic(hetero),
                {},
            ),
            "category-category": (
                GraphProjector.project_category_to_category(hetero),
                {},
            ),
            "designer-designer": (
                GraphProjector.project_designer_to_designer(hetero),
                {},
            ),
        }

        results: dict = {
            "heterogeneous": {
                "nodes": hetero.number_of_nodes(),
                "edges": hetero.number_of_edges(),
            },
            "projections": {},
        }

        for graph_type, (proj_graph, meta) in projections.items():
            GraphStorageService.save_projected_graph(
                graph_type,
                proj_graph,
                metadata={
                    **meta,
                    "total_nodes": proj_graph.number_of_nodes(),
                    "total_edges": proj_graph.number_of_edges(),
                },
            )
            results["projections"][graph_type] = {
                "nodes": proj_graph.number_of_nodes(),
                "edges": proj_graph.number_of_edges(),
            }

        return results
