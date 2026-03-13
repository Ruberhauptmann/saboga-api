from rest_framework import serializers

from . import models


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Category
        fields = ["id", "name", "bgg_id", "type"]


class DesignerSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Designer
        fields = ["id", "name", "bgg_id", "type"]


class FamilySerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Family
        fields = ["id", "name", "bgg_id", "type"]


class MechanicSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Mechanic
        fields = ["id", "name", "bgg_id", "type"]


class RankHistorySerializer(serializers.ModelSerializer):
    class Meta:
        model = models.RankHistory
        fields = ["id", "date", "bgg_rank", "bgg_geek_rating", "bgg_average_rating"]


class BoardgameListSerializer(serializers.ModelSerializer):
    categories = CategorySerializer(many=True, read_only=True)
    designers = DesignerSerializer(many=True, read_only=True)
    families = FamilySerializer(many=True, read_only=True)
    mechanics = MechanicSerializer(many=True, read_only=True)

    class Meta:
        model = models.Boardgame
        fields = [
            "id",
            "bgg_id",
            "bgg_rank",
            "name",
            "bgg_geek_rating",
            "bgg_average_rating",
            "bgg_rank_trend",
            "mean_trend",
            "categories",
            "designers",
            "families",
            "mechanics",
        ]

class BoardgameRankHistorySerializer(BoardgameListSerializer):
    """
    Inherits from the List serializer but adds the annotated
    historical and difference fields.
    """
    # Annotated fields from the queryset
    past_rank = serializers.IntegerField(read_only=True)
    past_geek_rating = serializers.FloatField(read_only=True)
    past_avg_rating = serializers.FloatField(read_only=True)

    # Calculated difference fields
    rank_diff = serializers.IntegerField(read_only=True)
    geek_rating_diff = serializers.FloatField(read_only=True)
    avg_rating_diff = serializers.FloatField(read_only=True)

    class Meta(BoardgameListSerializer.Meta):
        # Add the new fields to the existing list
        fields = BoardgameListSerializer.Meta.fields + [
            "past_rank", "past_geek_rating", "past_avg_rating",
            "rank_diff", "geek_rating_diff", "avg_rating_diff"
        ]


class BoardgameDetailSerializer(BoardgameListSerializer):
    bgg_rank_history = RankHistorySerializer(many=True, read_only=True)

    class Meta(BoardgameListSerializer.Meta):
        model = models.Boardgame
        fields = BoardgameListSerializer.Meta.fields + [
            "description",
            "image_url",
            "thumbnail_url",
            "year_published",
            "minplayers",
            "maxplayers",
            "playingtime",
            "minplaytime",
            "maxplaytime",
            "bgg_rank_history",
        ]


class NetworkSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.BoardgameNetwork
        fields = ["id", "nodes", "edges"]


# Graph response serializers used by GraphViewSet
class BaseGraphSerializer(serializers.Serializer):
    """Generic schema for a graph dictionary returned from the service."""
    nodes = serializers.ListField(child=serializers.DictField())
    edges = serializers.ListField(child=serializers.DictField())


class AvailableGraphSerializer(serializers.Serializer):
    type = serializers.CharField()
    description = serializers.CharField()


class AvailableGraphsResponseSerializer(serializers.Serializer):
    available_graphs = AvailableGraphSerializer(many=True)


class BuildGraphResultSerializer(serializers.Serializer):
    status = serializers.CharField()
    graph_statistics = serializers.DictField()


class BuildAllGraphsResultSerializer(serializers.Serializer):
    status = serializers.CharField()
    graphs_built = serializers.DictField()


class AllGraphsSerializer(serializers.Serializer):
    heterogeneous = BaseGraphSerializer()
    projected = serializers.DictField(child=BaseGraphSerializer())


class LatestRankHistoryTimestampSerializer(serializers.Serializer):
    """Simple container used by the metrics endpoint."""

    latest_rank_history_timestamp = serializers.FloatField()
