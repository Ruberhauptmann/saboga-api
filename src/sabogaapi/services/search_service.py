from itertools import chain

from sabogaapi import models, schemas


class SearchService:
    @staticmethod
    async def search(query: str, limit: int = 10) -> list[schemas.SearchResult]:
        """Search.

        Args:
            query (str): Search query.
            limit (int, optional): Limit for results. Defaults to 10.

        Returns:
            list[schemas.SearchResult]: List of search results.

        """
        search_models = [
            models.Boardgame,
            models.Category,
            models.Designer,
            models.Family,
            models.Mechanic,
        ]
        results = [
            await model.find({"name": {"$regex": query, "$options": "i"}})
            .limit(limit)
            .to_list()
            for model in search_models
        ]
        return [
            schemas.SearchResult(**result.model_dump())
            for result in list(chain(*results))
        ]
