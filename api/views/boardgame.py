from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from django.db.models import OuterRef, Subquery, F
import datetime
from .. import models
from .. import serializers


class BoardgameViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = models.Boardgame.objects.all().order_by("-bgg_rank")
    serializer_class = serializers.BoardgameListSerializer
    lookup_field = "bgg_id"

    def get_serializer_class(self):
        if self.action == "retrieve":
            return serializers.BoardgameDetailSerializer
        return super().get_serializer_class()

    @action(
        detail=False,
        methods=["get"],
        url_path="rank-history",
        serializer_class=serializers.BoardgameRankHistorySerializer,
    )
    def rank_history(self, request):#
        compare_to = request.query_params.get("compare_to")
        print(compare_to, flush=True)

        if compare_to is None:
            compare_to = (datetime.datetime.now() - datetime.timedelta(days=7)).date()
        else:
            try:
                compare_to = datetime.datetime.strptime(compare_to, "%Y-%m-%d").date()
            except ValueError:
                return Response(
                    {"detail": "Invalid date format. Use YYYY-MM-DD."},
                    status=400,
                )

        history_subquery = models.RankHistory.objects.filter(
            boardgame=OuterRef("pk"),
            date=compare_to,
        )

        objs = models.Boardgame.objects.annotate(
            past_rank=Subquery(history_subquery.values("bgg_rank")[:1]),
            past_geek_rating=Subquery(history_subquery.values("bgg_geek_rating")[:1]),
            past_avg_rating=Subquery(history_subquery.values("bgg_average_rating")[:1]),
            bgg_rank_change=F("bgg_rank") - F("past_rank"),
            bgg_geek_rating_change=F("bgg_geek_rating") - F("past_geek_rating"),
            bgg_average_rating_change=F("bgg_average_rating") - F("past_avg_rating"),
        ).order_by("past_rank")

        page = self.paginate_queryset(objs)

        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(objs, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=["get"])
    def trending(self, request):
        objs = models.Boardgame.objects.order_by("-bgg_rank_trend")[:5]
        serializer = self.get_serializer(objs, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=["get"])
    def declining(self, request):
        objs = models.Boardgame.objects.order_by("bgg_rank_trend")[:5]
        serializer = self.get_serializer(objs, many=True)
        return Response(serializer.data)
