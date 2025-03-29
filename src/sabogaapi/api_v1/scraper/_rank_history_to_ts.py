from typing import List

from pydantic import BaseModel

from sabogaapi.api_v1.database import init_db
from sabogaapi.api_v1.models import Boardgame, RankHistory, RankHistorySingleGame


class BoardgameBGGIDs(BaseModel):
    bgg_id: int
    bgg_rank_history: List[RankHistorySingleGame]


async def convert_rank_history_to_ts() -> None:
    await init_db()

    step_size = 500
    step_count = 0

    while True:
        boardgames = (
            await Boardgame.find_all()
            .sort("+bgg_id")
            .skip(step_count * step_size)
            .limit(step_size)
            .project(BoardgameBGGIDs)
            .to_list()
        )
        step_count += 1

        print(boardgames[-1].bgg_id, flush=True)

        if len(boardgames) == 0:
            break

        rank_history_list = []
        for boardgame in boardgames:
            rank_history_document = boardgame.bgg_rank_history
            for entry in rank_history_document:
                rank_history_list.append(
                    RankHistory(
                        bgg_id=boardgame.bgg_id,
                        date=entry.date,
                        bgg_rank=entry.bgg_rank,
                        bgg_geek_rating=entry.bgg_geek_rating,
                        bgg_average_rating=entry.bgg_average_rating,
                    )
                )

        await RankHistory.insert_many(rank_history_list)
        print("Inserted", flush=True)
