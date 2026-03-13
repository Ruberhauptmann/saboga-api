from rest_framework.views import APIView
from rest_framework.response import Response
from .. import models, serializers


class SearchView(APIView):
    def get(self, request):
        query = request.query_params.get("query", "")
        if not query:
            return Response({"boardgames": [], "categories": []})

        boardgames = models.Boardgame.objects.filter(name__icontains=query)[:10]
        categories = models.Category.objects.filter(name__icontains=query)[:10]

        results = [
            {"type": "boardgame", "data": serializers.BoardgameListSerializer(bg).data}
            for bg in boardgames
        ] + [
            {"type": "category", "data": serializers.CategoryListSerializer(cat).data}
            for cat in categories
        ]

        serializer = serializers.SearchResultSerializer(results, many=True)
        return Response(serializer.data)
