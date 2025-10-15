from sqlalchemy import select

from sabogaapi import models, schemas
from sabogaapi.api.dependencies.core import DBSessionDep


class SearchService:
    @staticmethod
    async def search(
        db_session: DBSessionDep, query: str, limit: int = 10
    ) -> list[schemas.SearchResult]:
        search_models: list[type[models.Base]] = [
            models.Boardgame,
            models.Category,
            models.Designer,
            models.Family,
            models.Mechanic,
        ]

        all_results: list[models.Base] = []

        for model in search_models:
            stmt = select(model).where(model.name.ilike(f"%{query}%")).limit(limit)
            result = await db_session.execute(stmt)
            rows = result.scalars().all()
            all_results.extend(rows)

        return [schemas.SearchResult.from_orm(row) for row in all_results]
