from django.db import models


class BaseModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class Category(BaseModel):
    name = models.CharField(max_length=255)
    bgg_id = models.IntegerField(unique=True, db_index=True)
    type = models.CharField(max_length=50, default="category")

    class Meta:
        db_table = "categories"

    def __str__(self) -> str:  # pragma: no cover - simple repr
        return self.name


class Designer(BaseModel):
    name = models.CharField(max_length=255)
    bgg_id = models.IntegerField(unique=True, db_index=True)
    type = models.CharField(max_length=50, default="designer")

    class Meta:
        db_table = "designers"

    def __str__(self) -> str:  # pragma: no cover
        return self.name


class Family(BaseModel):
    name = models.CharField(max_length=255)
    bgg_id = models.IntegerField(unique=True, db_index=True)
    type = models.CharField(max_length=50, default="family")

    class Meta:
        db_table = "families"

    def __str__(self) -> str:  # pragma: no cover
        return self.name


class Mechanic(BaseModel):
    name = models.CharField(max_length=255)
    bgg_id = models.IntegerField(unique=True, db_index=True)
    type = models.CharField(max_length=50, default="mechanic")

    class Meta:
        db_table = "mechanics"

    def __str__(self) -> str:  # pragma: no cover
        return self.name


class Boardgame(BaseModel):
    bgg_id = models.IntegerField(unique=True, db_index=True)
    bgg_rank = models.IntegerField(null=True, db_index=True)

    name = models.CharField(max_length=1024, default="")
    bgg_geek_rating = models.FloatField(null=True, blank=True)
    bgg_average_rating = models.FloatField(null=True, blank=True)
    bgg_rank_volatility = models.FloatField(null=True, blank=True)
    bgg_rank_trend = models.FloatField(null=True, blank=True)
    bgg_geek_rating_volatility = models.FloatField(null=True, blank=True)
    bgg_geek_rating_trend = models.FloatField(null=True, blank=True)
    bgg_average_rating_volatility = models.FloatField(null=True, blank=True)
    bgg_average_rating_trend = models.FloatField(null=True, blank=True)
    mean_trend = models.FloatField(null=True, blank=True)

    description = models.TextField(null=True, blank=True)
    image_url = models.URLField(null=True, blank=True)
    thumbnail_url = models.URLField(null=True, blank=True)

    year_published = models.IntegerField(null=True, blank=True)
    minplayers = models.IntegerField(null=True, blank=True)
    maxplayers = models.IntegerField(null=True, blank=True)
    playingtime = models.IntegerField(null=True, blank=True)
    minplaytime = models.IntegerField(null=True, blank=True)
    maxplaytime = models.IntegerField(null=True, blank=True)

    type = models.CharField(max_length=50, default="boardgame")

    categories = models.ManyToManyField(Category, related_name="boardgames", blank=True)
    families = models.ManyToManyField(Family, related_name="boardgames", blank=True)
    mechanics = models.ManyToManyField(Mechanic, related_name="boardgames", blank=True)
    designers = models.ManyToManyField(Designer, related_name="boardgames", blank=True)

    class Meta:
        db_table = "boardgames"

    def __str__(self) -> str:  # pragma: no cover
        return self.name


class RankHistory(BaseModel):
    date = models.DateField(db_index=True)
    boardgame = models.ForeignKey(
        Boardgame, on_delete=models.CASCADE, related_name="bgg_rank_history"
    )
    bgg_rank = models.IntegerField(null=True, blank=True)
    bgg_geek_rating = models.FloatField(null=True, blank=True)
    bgg_average_rating = models.FloatField(null=True, blank=True)

    class Meta:
        db_table = "rank_history"
        indexes = [
            models.Index(
                fields=["boardgame", "date"], name="ix_rankhistory_boardgame_date"
            )
        ]


# JSON network and graph storage
class BoardgameNetwork(BaseModel):
    nodes = models.JSONField()
    edges = models.JSONField()

    class Meta:
        db_table = "boardgame_network"


class CategoryNetwork(BaseModel):
    nodes = models.JSONField()
    edges = models.JSONField()

    class Meta:
        db_table = "category_network"


class DesignerNetwork(BaseModel):
    nodes = models.JSONField()
    edges = models.JSONField()

    class Meta:
        db_table = "designer_network"


class FamilyNetwork(BaseModel):
    nodes = models.JSONField()
    edges = models.JSONField()

    class Meta:
        db_table = "family_network"


class MechanicNetwork(BaseModel):
    nodes = models.JSONField()
    edges = models.JSONField()

    class Meta:
        db_table = "mechanic_network"


class HeterogeneousGraphData(BaseModel):
    created_at = models.DateTimeField(db_index=True)
    updated_at = models.DateTimeField(null=True, blank=True)
    nodes = models.JSONField()
    edges = models.JSONField()
    meta = models.JSONField(default=dict)

    class Meta:
        db_table = "heterogeneous_graph"


class ProjectedGraphData(BaseModel):
    graph_type = models.CharField(max_length=255, db_index=True)
    created_at = models.DateTimeField(db_index=True)
    updated_at = models.DateTimeField(null=True, blank=True)
    nodes = models.JSONField()
    edges = models.JSONField()
    meta = models.JSONField(default=dict)

    class Meta:
        db_table = "projected_graphs"
