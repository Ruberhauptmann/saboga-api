"""Service for managing graph storage and retrieval."""

import datetime

from sqlalchemy.orm import Session

from sabogaapi.graph import GraphBuilder, HeterogeneousGraph
from sabogaapi.graph.projections import GraphProjector
from sabogaapi.models import HeterogeneousGraphData, ProjectedGraphData


class GraphStorageService:
    """Service for storing and retrieving graphs from the database."""

    @staticmethod
    def save_heterogeneous_graph(
        session: Session,
        graph: HeterogeneousGraph,
        metadata: dict | None = None,
    ) -> HeterogeneousGraphData:
        """Save a heterogeneous graph to the database.

        Args:
            session: SQLAlchemy session
            graph: The HeterogeneousGraph to save
            metadata: Optional metadata to store with the graph

        Returns:
            The created HeterogeneousGraphData record
        """
        graph_dict = graph.to_dict()

        # Check if a graph already exists and update it
        existing = session.query(HeterogeneousGraphData).first()
        if existing:
            existing.nodes = graph_dict["nodes"]
            existing.edges = graph_dict["edges"]
            existing.meta = metadata or {}
            existing.updated_at = datetime.datetime.now(tz=datetime.UTC)
            session.commit()
            return existing

        # Create new record
        graph_data = HeterogeneousGraphData(
            nodes=graph_dict["nodes"],
            edges=graph_dict["edges"],
            meta=metadata or {},
        )
        session.add(graph_data)
        session.commit()
        return graph_data

    @staticmethod
    def load_heterogeneous_graph(session: Session) -> HeterogeneousGraph | None:
        """Load the heterogeneous graph from the database.

        Args:
            session: SQLAlchemy session

        Returns:
            The loaded HeterogeneousGraph or None if not found
        """
        graph_data = session.query(HeterogeneousGraphData).first()
        if not graph_data:
            return None

        graph = HeterogeneousGraph()

        # Add nodes
        for node in graph_data.nodes:
            graph.add_node(
                node_id=node["id"],
                node_type=node["type"],
                label=node["label"],
                attributes=node.get("attributes", {}),
            )

        # Add edges
        for edge in graph_data.edges:
            graph.add_edge(
                source_id=edge["source"],
                target_id=edge["target"],
                edge_type=edge["type"],
                attributes=edge.get("attributes", {}),
            )

        return graph

    @staticmethod
    def save_projected_graph(
        session: Session,
        graph_type: str,
        graph: HeterogeneousGraph,
        metadata: dict | None = None,
    ) -> ProjectedGraphData:
        """Save a projected graph to the database.

        Args:
            session: SQLAlchemy session
            graph_type: Type of projection (e.g., 'game-game', 'mechanic-mechanic')
            graph: The projected HeterogeneousGraph
            metadata: Optional metadata to store with the graph

        Returns:
            The created ProjectedGraphData record
        """
        graph_dict = graph.to_dict()

        # Check if this graph type already exists
        existing = (
            session.query(ProjectedGraphData)
            .filter(ProjectedGraphData.graph_type == graph_type)
            .first()
        )

        if existing:
            existing.nodes = graph_dict["nodes"]
            existing.edges = graph_dict["edges"]
            existing.meta = metadata or {}
            existing.updated_at = datetime.now(tz=datetime.UTC)
            session.commit()
            return existing

        # Create new record
        projected = ProjectedGraphData(
            graph_type=graph_type,
            nodes=graph_dict["nodes"],
            edges=graph_dict["edges"],
            meta=metadata or {},
        )
        session.add(projected)
        session.commit()
        return projected

    @staticmethod
    def load_projected_graph(
        session: Session,
        graph_type: str,
    ) -> HeterogeneousGraph | None:
        """Load a projected graph from the database.

        Args:
            session: SQLAlchemy session
            graph_type: Type of projection to load

        Returns:
            The loaded HeterogeneousGraph or None if not found
        """
        graph_data = (
            session.query(ProjectedGraphData)
            .filter(ProjectedGraphData.graph_type == graph_type)
            .first()
        )

        if not graph_data:
            return None

        graph = HeterogeneousGraph()

        # Add nodes
        for node in graph_data.nodes:
            graph.add_node(
                node_id=node["id"],
                node_type=node["type"],
                label=node["label"],
                attributes=node.get("attributes", {}),
            )

        # Add edges
        for edge in graph_data.edges:
            graph.add_edge(
                source_id=edge["source"],
                target_id=edge["target"],
                edge_type=edge["type"],
                attributes=edge.get("attributes", {}),
            )

        return graph

    @staticmethod
    def build_and_save_all_graphs(session: Session) -> dict:
        """Build and save all graphs (heterogeneous + projections).

        Args:
            session: SQLAlchemy session

        Returns:
            Dictionary with information about what was saved
        """
        # Build main heterogeneous graph
        hetero_graph = GraphBuilder.build_graph(session)
        GraphStorageService.save_heterogeneous_graph(
            session,
            hetero_graph,
            metadata={
                "total_nodes": hetero_graph.number_of_nodes(),
                "total_edges": hetero_graph.number_of_edges(),
            },
        )

        # Build and save projections
        projections = {
            "game-mechanic": (
                GraphProjector.project_game_to_game(hetero_graph, "mechanic"),
                {"connection_type": "mechanic"},
            ),
            "game-category": (
                GraphProjector.project_game_to_game(hetero_graph, "category"),
                {"connection_type": "category"},
            ),
            "game-designer": (
                GraphProjector.project_game_to_game(hetero_graph, "designer"),
                {"connection_type": "designer"},
            ),
            "mechanic-mechanic": (
                GraphProjector.project_mechanic_to_mechanic(hetero_graph),
                {},
            ),
            "category-category": (
                GraphProjector.project_category_to_category(hetero_graph),
                {},
            ),
            "designer-designer": (
                GraphProjector.project_designer_to_designer(hetero_graph),
                {},
            ),
        }

        results = {
            "heterogeneous": {
                "nodes": hetero_graph.number_of_nodes(),
                "edges": hetero_graph.number_of_edges(),
            },
            "projections": {},
        }

        for graph_type, (proj_graph, meta) in projections.items():
            GraphStorageService.save_projected_graph(
                session,
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
