"""Service layer for designer."""

from collections import defaultdict
from itertools import combinations
from typing import Any

from sabogaapi import models, schemas
from sabogaapi.logger import configure_logger
from sabogaapi.models import Boardgame, Designer

logger = configure_logger()


class DesignerService:
    """Service layer for designer."""

    @staticmethod
    async def read_all_designers() -> list[schemas.Designer]:
        """Read all designers.

        Returns:
            list[schemas.Designer]: List of designers.

        """
        designer_list = await models.Designer.find().to_list()
        return [schemas.Designer(**designer.model_dump()) for designer in designer_list]

    @staticmethod
    async def get_designer_network() -> schemas.DesignerNetwork:
        """Construct a graph from designer data.

        Returns:
            dict[str, list[dict[str, Any]]]: Dictionary with nodes and connections.

        """
        boardgames_cursor = Boardgame.find({}, fetch_links=True)

        edges_dict = defaultdict(list)
        designer_ids_set = set()

        async for bg in boardgames_cursor:
            bgg_id = bg.bgg_id
            designers = [d.bgg_id for d in bg.designers]
            for a, b in combinations(sorted(designers), 2):
                edges_dict[(a, b)].append(bgg_id)
            designer_ids_set.update(designers)

        designers_list = await Designer.find(
            {"bgg_id": {"$in": list(designer_ids_set)}},
        ).to_list()

        designer_lookup = {
            d.bgg_id: {"bgg_id": d.bgg_id, "name": d.name} for d in designers_list
        }

        nodes = [
            schemas.DesignerNode(
                id=str(designer_lookup[did]["bgg_id"]),
                label=designer_lookup[did]["name"],
                x=1,
                y=1,
                size=15,
            )
            for did in designer_ids_set
        ]

        edges = []
        edge_count = 0
        for (a, b), w in edges_dict.items():
            edge_count += 1
            edges.append(
                schemas.DesignerEdge(
                    id=f"e{edge_count}",
                    source=str(designer_lookup[a]["bgg_id"]),
                    target=str(designer_lookup[b]["bgg_id"]),
                    size=len(w),
                )
            )

        return schemas.DesignerNetwork(nodes=nodes, edges=edges)
