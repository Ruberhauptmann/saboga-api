from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import (
    BoardgameViewSet,
    CategoryViewSet,
    GraphViewSet,
    DesignerViewSet,
    FamilyViewSet,
    MechanicViewSet,
    SearchView,
)

router = DefaultRouter()
router.register("boardgames", BoardgameViewSet, basename="boardgame")
router.register("categories", CategoryViewSet, basename="category")
router.register("designers", DesignerViewSet, basename="designer")
router.register("families", FamilyViewSet, basename="family")
router.register("mechanics", MechanicViewSet, basename="mechanic")
router.register("graphs", GraphViewSet, basename="graph")

urlpatterns = [
    path("", include(router.urls)),
    path("search/", SearchView.as_view(), name="global-search"),
]
