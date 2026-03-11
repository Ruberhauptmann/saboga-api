"""High level graph operations used by API views."""

from .builder import GraphBuilder
from .projections import GraphProjector
from .storage import GraphStorageService
from .heterogeneous import HeterogeneousGraph, EdgeType


class GraphService:
    """Convenience layer combining build/project/storage logic."""

    @staticmethod
    def build_heterogeneous_graph() -> HeterogeneousGraph:
        return GraphBuilder.build_graph()

    @staticmethod
    def save_heterogeneous_graph(
        graph: HeterogeneousGraph, metadata: dict | None = None
    ):
        return GraphStorageService.save_heterogeneous_graph(graph, metadata)

    @staticmethod
    def load_heterogeneous_graph() -> HeterogeneousGraph | None:
        return GraphStorageService.load_heterogeneous_graph()

    @staticmethod
    def save_projected_graph(
        graph_type: str, graph: HeterogeneousGraph, metadata: dict | None = None
    ):
        return GraphStorageService.save_projected_graph(graph_type, graph, metadata)

    @staticmethod
    def load_projected_graph(graph_type: str) -> HeterogeneousGraph | None:
        return GraphStorageService.load_projected_graph(graph_type)

    @staticmethod
    def build_and_save_all() -> dict:
        return GraphStorageService.build_and_save_all_graphs()
