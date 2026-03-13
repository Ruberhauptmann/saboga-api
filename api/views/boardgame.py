from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from django.db.models import OuterRef, Subquery, F
import datetime
from .. import models
from .. import serializers
from ..statistics import forecast_game_ranking

from datetime import timedelta


class BoardgameViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = models.Boardgame.objects.all().order_by("-bgg_rank")
    lookup_field = "bgg_id"

    def get_serializer_class(self):
        if self.action == "retrieve":
            return serializers.BoardgameDetailSerializer
        return serializers.BoardgameListSerializer

    def retrieve(self, request, *args, **kwargs):
        # 1. Get the base boardgame instance
        instance = self.get_object()

        # 2. Extract and parse query parameters
        start_date_str = request.query_params.get("start_date")
        end_date_str = request.query_params.get("end_date")
        mode = request.query_params.get("mode", "auto")

        # Fallback to last 30 days if no dates provided
        try:
            end_date = (
                datetime.datetime.strptime(end_date_str, "%Y-%m-%d").date()
                if end_date_str
                else datetime.datetime.now().date()
            )
            start_date = (
                datetime.datetime.strptime(start_date_str, "%Y-%m-%d").date()
                if start_date_str
                else end_date - timedelta(days=30)
            )
        except ValueError:
            return Response(
                {"error": "Invalid date format. Use YYYY-MM-DD."}, status=400
            )

        # 3. Determine Downsampling Mode
        date_diff = (end_date - start_date).days
        if mode == "auto":
            if date_diff <= 30:
                mode = "daily"
            elif date_diff <= 180:
                mode = "weekly"
            else:
                mode = "yearly"

        # 4. Fetch and Filter History
        history_qs = models.RankHistory.objects.filter(
            boardgame=instance, date__range=[start_date, end_date]
        ).order_by("date")

        history = list(history_qs)

        # 5. Apply Downsampling Logic
        if mode == "weekly":
            history = history[::7]
        elif mode == "yearly":
            seen_years = set()
            yearly_history = []
            for rh in reversed(history):
                if rh.date.year not in seen_years:
                    yearly_history.append(rh)
                    seen_years.add(rh.date.year)
            history = sorted(yearly_history, key=lambda x: x.date)

        # 6. Serialize and Inject History
        serializer = self.get_serializer(instance)
        data = serializer.data

        # Manually add the processed history to the response
        data["bgg_rank_history"] = serializers.RankHistorySerializer(
            history, many=True
        ).data

        # Update current rank based on latest history point if available
        if history:
            data["bgg_rank"] = history[-1].bgg_rank

        return Response(data)

    @action(
        detail=True,
        methods=["get"],
        url_path="forecast",
        serializer_class=serializers.PredictionSerializer,
    )
    def forecast(self, request, bgg_id=None):
        game = self.get_object()

        rank_history = list(game.bgg_rank_history.all().order_by("date"))

        if not rank_history:
            return Response(
                {"detail": "No history data available for forecasting."}, status=404
            )

        try:
            predictions = forecast_game_ranking(rank_history)
            serializer = serializers.PredictionSerializer(predictions, many=True)
            return Response(serializer.data)

        except Exception as e:
            return Response({"detail": f"Forecasting failed: {e!s}"}, status=500)

    @action(
        detail=False,
        methods=["get"],
        url_path="rank-history",
        serializer_class=serializers.BoardgameRankHistorySerializer,
    )
    def rank_history(self, request):  #
        compare_to = request.query_params.get("compare_to")

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
