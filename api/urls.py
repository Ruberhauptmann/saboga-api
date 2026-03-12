from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import BoardgameViewSet, CategoryViewSet, GraphViewSet, MetricsViewSet

router = DefaultRouter()
router.register("boardgames", BoardgameViewSet, basename="boardgame")
router.register("categories", CategoryViewSet, basename="category")
router.register("graphs", GraphViewSet, basename="graph")

urlpatterns = [
    path("", include(router.urls)),
]
