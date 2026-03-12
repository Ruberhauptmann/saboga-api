from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response

from . import models
from . import serializers

from django.db.models import Max

# graph utilities
from .graph.services import GraphService
from .graph.projections import GraphProjector

from . import serializers as s


class CategoryViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = models.Category.objects.all().order_by("name")
    serializer_class = serializers.CategorySerializer
    lookup_field = "bgg_id"


class GraphViewSet(viewsets.ViewSet):
    """Custom endpoints for graph data.

    All actions are registered under the `/graphs/` prefix.

    A serializer_class is provided so that DRF's Schema generator
    includes the viewset in the generated OpenAPI document.  Individual
    actions override it when they return a more specific structure.

    We also implement a minimal ``list`` method so that the DRF
    ``DefaultRouter`` will include ``/graphs/`` in the API root view.
    Without a list or retrieve method the router considers the viewset
    to have no top‑level link and omits it from the index page.
    """
    serializer_class = s.BaseGraphSerializer

    def list(self, request):
        # simple placeholder; users should call one of the named actions
        return Response(
            {
                "detail": "Graph endpoints are available under 'list-available', 'heterogeneous', or 'projected/<type>'",
            }
        )

    @action(detail=False, methods=["get"], serializer_class=s.BaseGraphSerializer)
    def heterogeneous(self, request):
        graph = GraphService.load_heterogeneous_graph()
        if graph is None:
            graph = GraphService.build_heterogeneous_graph()
        return Response(graph.to_dict())

    @action(detail=False, methods=["post"], url_path="heterogeneous/build", serializer_class=s.BuildGraphResultSerializer)
    def build_heterogeneous(self, request):
        graph = GraphService.build_heterogeneous_graph()
        GraphService.save_heterogeneous_graph(graph)
        return Response(
            {"status": "success", "graph_statistics": graph.get_statistics()}
        )

    @action(
        detail=False,
        methods=["get"],
        url_path=r"projected/(?P<graph_type>[^/.]+)",
        serializer_class=s.BaseGraphSerializer,
    )
    def projected(self, request, graph_type=None):
        graph = GraphService.load_projected_graph(graph_type)
        if graph is None:
            hetero = GraphService.load_heterogeneous_graph()
            if hetero is None:
                hetero = GraphService.build_heterogeneous_graph()

            if graph_type == "game-mechanic":
                graph = GraphProjector.project_game_to_game(hetero, "mechanic")
            elif graph_type == "game-category":
                graph = GraphProjector.project_game_to_game(hetero, "category")
            elif graph_type == "game-designer":
                graph = GraphProjector.project_game_to_game(hetero, "designer")
            elif graph_type == "mechanic-mechanic":
                graph = GraphProjector.project_mechanic_to_mechanic(hetero)
            elif graph_type == "category-category":
                graph = GraphProjector.project_category_to_category(hetero)
            elif graph_type == "designer-designer":
                graph = GraphProjector.project_designer_to_designer(hetero)
            else:
                return Response(
                    {
                        "error": f"Unknown graph type: {graph_type}",
                        "available_types": [
                            "game-mechanic",
                            "game-category",
                            "game-designer",
                            "mechanic-mechanic",
                            "category-category",
                            "designer-designer",
                        ],
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )
        return Response(graph.to_dict())

    @action(detail=False, methods=["post"], url_path="build-all", serializer_class=s.BuildAllGraphsResultSerializer)
    def build_all(self, request):
        results = GraphService.build_and_save_all()
        return Response({"status": "success", "graphs_built": results})

    @action(detail=False, methods=["get"], serializer_class=s.AllGraphsSerializer)
    def all(self, request):
        hetero = GraphService.load_heterogeneous_graph()
        if hetero is None:
            hetero = GraphService.build_heterogeneous_graph()

        projections = {}
        for graph_type, fn in {
            "game-mechanic": lambda g: GraphProjector.project_game_to_game(
                g, "mechanic"
            ),
            "game-category": lambda g: GraphProjector.project_game_to_game(
                g, "category"
            ),
            "game-designer": lambda g: GraphProjector.project_game_to_game(
                g, "designer"
            ),
            "mechanic-mechanic": lambda g: GraphProjector.project_mechanic_to_mechanic(
                g
            ),
            "category-category": lambda g: GraphProjector.project_category_to_category(
                g
            ),
            "designer-designer": lambda g: GraphProjector.project_designer_to_designer(
                g
            ),
        }.items():
            cached = GraphService.load_projected_graph(graph_type)
            projections[graph_type] = (
                cached.to_dict() if cached else fn(hetero).to_dict()
            )

        return Response(
            {
                "heterogeneous": hetero.to_dict(),
                "projected": projections,
            }
        )

    @action(detail=False, methods=["get"], serializer_class=s.AvailableGraphsResponseSerializer, url_path="list-available")
    def list_available(self, request):
        return Response(
            {
                "available_graphs": [
                    {
                        "type": "heterogeneous",
                        "description": "Complete heterogeneous graph with all node and edge types",
                    },
                    {
                        "type": "game-mechanic",
                        "description": "Game-to-game connections through shared mechanics",
                    },
                    {
                        "type": "game-category",
                        "description": "Game-to-game connections through shared categories",
                    },
                    {
                        "type": "game-designer",
                        "description": "Game-to-game connections through shared designers",
                    },
                    {
                        "type": "mechanic-mechanic",
                        "description": "Mechanic-to-mechanic connections through shared games",
                    },
                    {
                        "type": "category-category",
                        "description": "Category-to-category connections through shared games",
                    },
                    {
                        "type": "designer-designer",
                        "description": "Designer-to-designer collaborations through shared games",
                    },
                ]
            }
        )


class MetricsViewSet(viewsets.ViewSet):
    """A tiny collection of administrative metrics exposed over HTTP.

    The only current metric is the timestamp of the most recent
    ``RankHistory`` row.  We keep the implementation simple in order to
    make the value available in the DRF API and in OpenAPI documentation
    without pulling in the Prometheus instrumentation layer used by the
    old FastAPI service.
    """

    serializer_class = s.LatestRankHistoryTimestampSerializer

    @action(
        detail=False,
        methods=["get"],
        url_path="latest-rank-history",
        serializer_class=s.LatestRankHistoryTimestampSerializer,
    )
    def latest_rank_history(self, request):
        # compute the maximum ``date`` value using an aggregate query;
        # Django returns an aware ``datetime`` instance when timezone
        # support is enabled so the ``timestamp()`` call works correctly.
        max_date = models.RankHistory.objects.aggregate(
            max_date=Max("date")
        )["max_date"]
        if max_date is not None:
            timestamp = max_date.timestamp()
        else:
            timestamp = 0.0
        return Response({"latest_rank_history_timestamp": timestamp})


class BoardgameViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = models.Boardgame.objects.all().order_by("-bgg_rank")
    serializer_class = serializers.BoardgameListSerializer
    lookup_field = "bgg_id"

    def get_serializer_class(self):
        if self.action == "retrieve":
            return serializers.BoardgameDetailSerializer
        return super().get_serializer_class()

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
