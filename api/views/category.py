from rest_framework import viewsets

from .. import serializers

from .. import models


class CategoryViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = models.Category.objects.all().order_by("name")
    serializer_class = serializers.CategoryListSerializer
    lookup_field = "bgg_id"

    def get_queryset(self):
        queryset = super().get_queryset()
        if self.action == "retrieve":
            return queryset.prefetch_related("boardgames")
        return queryset

    def get_serializer_class(self):
        if self.action == "retrieve":
            return serializers.CategoryDetailSerializer
        return super().get_serializer_class()
