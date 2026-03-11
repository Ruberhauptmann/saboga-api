"""Graph builder for constructing heterogeneous graphs from database models."""

from sqlalchemy.orm import Session

from sabogaapi.graph.heterogeneous import EdgeType, HeterogeneousGraph, NodeType


class GraphBuilder:
    """Builder for constructing heterogeneous graphs from the database."""

    @staticmethod
    def build_graph(session: Session) -> HeterogeneousGraph:
        """Build a heterogeneous graph from database models.

        Args:
            session: SQLAlchemy session

        Returns:
            A populated HeterogeneousGraph object
        """
        from sabogaapi.models import Boardgame, Category, Designer, Mechanic

        graph = HeterogeneousGraph()

        # Query and add games
        games = session.query(Boardgame).all()
        for game in games:
            graph.add_node(
                node_id=f"game-{game.id}",
                node_type=NodeType.GAME,
                label=game.name,
                attributes={
                    "bgg_id": game.bgg_id,
                    "year_published": game.year_published,
                    "bgg_average_rating": game.bgg_average_rating,
                    "image_url": game.image_url,
                    "thumbnail_url": game.thumbnail_url,
                },
            )

        # Query and add mechanic nodes
        mechanics = session.query(Mechanic).all()
        for mechanic in mechanics:
            graph.add_node(
                node_id=f"mechanic-{mechanic.id}",
                node_type=NodeType.MECHANIC,
                label=mechanic.name,
                attributes={"bgg_id": mechanic.bgg_id},
            )

        # Query and add category nodes
        categories = session.query(Category).all()
        for category in categories:
            graph.add_node(
                node_id=f"category-{category.id}",
                node_type=NodeType.CATEGORY,
                label=category.name,
                attributes={"bgg_id": category.bgg_id},
            )

        designers = session.query(Designer).all()
        for designer in designers:
            graph.add_node(
                node_id=f"designer-{designer.id}",
                node_type=NodeType.DESIGNER,
                label=designer.name,
                attributes={"bgg_id": designer.bgg_id},
            )

        # Add edges
        for game in games:
            # Add mechanic edges
            for mechanic in game.mechanics:
                graph.add_edge(
                    source_id=f"game-{game.id}",
                    target_id=f"mechanic-{mechanic.id}",
                    edge_type=EdgeType.HAS_MECHANIC,
                )

            # Add category edges
            for category in game.categories:
                graph.add_edge(
                    source_id=f"game-{game.id}",
                    target_id=f"category-{category.id}",
                    edge_type=EdgeType.HAS_CATEGORY,
                )

            # Add designer edges
            for designer in game.designers:
                graph.add_edge(
                    source_id=f"game-{game.id}",
                    target_id=f"designer-{designer.id}",
                    edge_type=EdgeType.HAS_DESIGNER,
                )

        return graph
