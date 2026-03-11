"""Graph builder for constructing heterogeneous graphs from Django models."""

from django.db.models import Prefetch

from .heterogeneous import EdgeType, HeterogeneousGraph, NodeType
from .. import models


class GraphBuilder:
    """Builder for constructing heterogeneous graphs from the database."""

    @staticmethod
    def build_graph() -> HeterogeneousGraph:
        """Build a heterogeneous graph from database models.

        Returns:
            A populated :class:`HeterogeneousGraph` object
        """
        graph = HeterogeneousGraph()

        # prefetch many-to-many relationships to avoid n+1
        games = models.Boardgame.objects.prefetch_related(
            Prefetch("mechanics"),
            Prefetch("categories"),
            Prefetch("designers"),
        ).all()

        # add game nodes
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

        # mechanics, categories, designers
        for mechanic in models.Mechanic.objects.all():
            graph.add_node(
                node_id=f"mechanic-{mechanic.id}",
                node_type=NodeType.MECHANIC,
                label=mechanic.name,
                attributes={"bgg_id": mechanic.bgg_id},
            )

        for category in models.Category.objects.all():
            graph.add_node(
                node_id=f"category-{category.id}",
                node_type=NodeType.CATEGORY,
                label=category.name,
                attributes={"bgg_id": category.bgg_id},
            )

        for designer in models.Designer.objects.all():
            graph.add_node(
                node_id=f"designer-{designer.id}",
                node_type=NodeType.DESIGNER,
                label=designer.name,
                attributes={"bgg_id": designer.bgg_id},
            )

        # add edges between game and related entities
        for game in games:
            for mechanic in game.mechanics.all():
                graph.add_edge(
                    source_id=f"game-{game.id}",
                    target_id=f"mechanic-{mechanic.id}",
                    edge_type=EdgeType.HAS_MECHANIC,
                )
            for category in game.categories.all():
                graph.add_edge(
                    source_id=f"game-{game.id}",
                    target_id=f"category-{category.id}",
                    edge_type=EdgeType.HAS_CATEGORY,
                )
            for designer in game.designers.all():
                graph.add_edge(
                    source_id=f"game-{game.id}",
                    target_id=f"designer-{designer.id}",
                    edge_type=EdgeType.HAS_DESIGNER,
                )

        return graph
