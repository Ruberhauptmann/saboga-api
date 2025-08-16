from collections import defaultdict
from itertools import combinations
from typing import Any

from sabogaapi import models, schemas
from sabogaapi.logger import configure_logger
from sabogaapi.models import Boardgame, Designer

logger = configure_logger()


class DesignerService:
    @staticmethod
    async def read_all_designers() -> list[schemas.Designer]:
        designer_list = await models.Designer.find().to_list()
        return [schemas.Designer(**designer.model_dump()) for designer in designer_list]

    @staticmethod
    async def get_designer_network() -> dict[str, list[dict[str, Any]]]:
        boardgames_cursor = Boardgame.find({}, fetch_links=True)

        edges_dict = defaultdict(list)
        designer_ids_set = set()

        async for bg in boardgames_cursor:
            bgg_id = bg.bgg_id
            designers = [d.bgg_id for d in bg.designers]
            for a, b in combinations(sorted(designers), 2):
                edges_dict[(a, b)].append(bgg_id)
            designer_ids_set.update(designers)

        print(designer_ids_set, flush=True)

        designers_list = await Designer.find(
            {"bgg_id": {"$in": list(designer_ids_set)}},
        ).to_list()

        print(designers_list, flush=True)

        designer_lookup = {
            d.bgg_id: {"bgg_id": d.bgg_id, "name": d.name} for d in designers_list
        }

        nodes = [
            {"id": designer_lookup[did]["bgg_id"], "name": designer_lookup[did]["name"]}
            for did in designer_ids_set
        ]
        edges = [
            {
                "source": designer_lookup[a]["bgg_id"],
                "target": designer_lookup[b]["bgg_id"],
                "bgg_ids": w,
                "weight": len(w),
            }
            for (a, b), w in edges_dict.items()
        ]

        return {"nodes": nodes, "edges": edges}
