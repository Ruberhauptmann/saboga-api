from typing import ClassVar

from rest_framework import serializers

from . import models


class CategoryListSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Category
        fields: ClassVar[list[str]] = ["id", "name", "bgg_id", "type"]


class DesignerListSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Category
        fields: ClassVar[list[str]] = ["id", "name", "bgg_id", "type"]


class FamilyListSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Family
        fields: ClassVar[list[str]] = ["id", "name", "bgg_id", "type"]


class MechanicListSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Mechanic
        fields: ClassVar[list[str]] = ["id", "name", "bgg_id", "type"]


class RankHistorySerializer(serializers.ModelSerializer):
    class Meta:
        model = models.RankHistory
        fields: ClassVar[list[str]] = [
            "id",
            "date",
            "bgg_rank",
            "bgg_geek_rating",
            "bgg_average_rating",
        ]


class BoardgameSimpleSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Boardgame
        fields: ClassVar[list[str]] = ["id", "name", "bgg_id", "bgg_rank"]


class BoardgameListSerializer(serializers.ModelSerializer):
    categories = CategoryListSerializer(many=True, read_only=True)
    designers = DesignerListSerializer(many=True, read_only=True)
    families = FamilyListSerializer(many=True, read_only=True)
    mechanics = MechanicListSerializer(many=True, read_only=True)

    class Meta:
        model = models.Boardgame
        fields: ClassVar[list[str]] = [
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
            "thumbnail_url",
            "year_published",
        ]


class BoardgameRankHistorySerializer(BoardgameListSerializer):
    """Inherits from the List serializer but adds the annotated
    historical and difference fields.
    """

    # Annotated fields from the queryset
    past_rank = serializers.IntegerField(read_only=True)
    past_geek_rating = serializers.FloatField(read_only=True)
    past_avg_rating = serializers.FloatField(read_only=True)

    # Calculated difference fields
    bgg_rank_change = serializers.IntegerField(read_only=True)
    bgg_geek_rating_change = serializers.FloatField(read_only=True)
    bgg_average_rating_change = serializers.FloatField(read_only=True)

    class Meta(BoardgameListSerializer.Meta):
        # Add the new fields to the existing list
        fields: ClassVar[list[str]] = [
            *BoardgameListSerializer.Meta.fields,
            "past_rank",
            "past_geek_rating",
            "past_avg_rating",
            "bgg_rank_change",
            "bgg_geek_rating_change",
            "bgg_average_rating_change",
        ]


class BoardgameDetailSerializer(BoardgameListSerializer):
    bgg_rank_history = RankHistorySerializer(many=True, read_only=True)

    class Meta(BoardgameListSerializer.Meta):
        model = models.Boardgame
        fields: ClassVar[list[str]] = [
            *BoardgameListSerializer.Meta.fields,
            "description",
            "image_url",
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
        fields: ClassVar[list[str]] = ["id", "nodes", "edges"]


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


class CategoryDetailSerializer(CategoryListSerializer):
    boardgames = BoardgameSimpleSerializer(many=True, read_only=True)

    class Meta(CategoryListSerializer.Meta):
        model = models.Category
        fields: ClassVar[list[str]] = [
            *CategoryListSerializer.Meta.fields,
            "boardgames",
        ]


class DesignerDetailSerializer(DesignerListSerializer):
    boardgames = BoardgameSimpleSerializer(many=True, read_only=True)

    class Meta(DesignerListSerializer.Meta):
        model = models.Designer
        fields: ClassVar[list[str]] = [
            *DesignerListSerializer.Meta.fields,
            "boardgames",
        ]


class FamilyDetailSerializer(FamilyListSerializer):
    boardgames = BoardgameSimpleSerializer(many=True, read_only=True)

    class Meta(FamilyListSerializer.Meta):
        model = models.Family
        fields: ClassVar[list[str]] = [
            *FamilyListSerializer.Meta.fields,
            "boardgames",
        ]


class MechanicDetailSerializer(MechanicListSerializer):
    boardgames = BoardgameSimpleSerializer(many=True, read_only=True)

    class Meta(MechanicListSerializer.Meta):
        model = models.Mechanic
        fields: ClassVar[list[str]] = [
            *MechanicListSerializer.Meta.fields,
            "boardgames",
        ]


class SearchResultSerializer(serializers.Serializer):
    type = serializers.CharField()
    # Use a generic field or point to specific serializers
    data = serializers.JSONField()


class PredictionSerializer(serializers.Serializer):
    date = serializers.DateTimeField()
    bgg_rank = serializers.IntegerField()
    bgg_rank_confidence_interval = serializers.ListField(
        child=serializers.FloatField(), min_length=2, max_length=2
    )
    bgg_average_rating = serializers.FloatField()
    bgg_average_rating_confidence_interval = serializers.ListField(
        child=serializers.FloatField(), min_length=2, max_length=2
    )
    bgg_geek_rating = serializers.FloatField()
    bgg_geek_rating_confidence_interval = serializers.ListField(
        child=serializers.FloatField(), min_length=2, max_length=2
    )
