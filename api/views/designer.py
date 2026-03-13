from rest_framework import viewsets

from .. import serializers

from .. import models


class DesignerViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = models.Designer.objects.all().order_by("name")
    serializer_class = serializers.DesignerListSerializer
    lookup_field = "bgg_id"

    def get_queryset(self):
        queryset = super().get_queryset()
        if self.action == "retrieve":
            return queryset.prefetch_related("boardgames")
        return queryset

    def get_serializer_class(self):
        if self.action == "retrieve":
            return serializers.DesignerDetailSerializer
        return super().get_serializer_class()
