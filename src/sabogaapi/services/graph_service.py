"""Async service wrapping graph build, projection and storage operations."""

from sqlalchemy import Delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from sabogaapi.graph import GraphBuilder, GraphProjector
from sabogaapi.graph.heterogeneous import EdgeType, HeterogeneousGraph, NodeType
from sabogaapi.models import HeterogeneousGraphData, ProjectedGraphData


class GraphService:
    """Service to build, load, save and project graphs using AsyncSession.

    This adapts the synchronous GraphBuilder/Projector to the async DB layer
    by running build operations inside `AsyncSession.run_sync` and using
    async ORM calls for persistence.
    """

    @staticmethod
    async def build_heterogeneous_graph(
        async_session: AsyncSession,
    ) -> HeterogeneousGraph:
        return await async_session.run_sync(
            lambda sync_s: GraphBuilder.build_graph(sync_s)
        )

    @staticmethod
    async def save_heterogeneous_graph(
        async_session: AsyncSession, graph: HeterogeneousGraph, meta: dict | None = None
    ) -> HeterogeneousGraphData:
        await async_session.execute(Delete(HeterogeneousGraphData))

        graph_dict = graph.to_dict()

        graph_data = HeterogeneousGraphData(
            nodes=graph_dict["nodes"], edges=graph_dict["edges"], meta=meta or {}
        )
        async_session.add(graph_data)
        await async_session.commit()
        return graph_data

    @staticmethod
    async def load_heterogeneous_graph(
        async_session: AsyncSession,
    ) -> HeterogeneousGraph | None:
        result = await async_session.execute(select(HeterogeneousGraphData))

        graph_data = result.scalars().first()
        if not graph_data:
            return None

        # Reconstruct HeterogeneousGraph
        from sabogaapi.graph import HeterogeneousGraph

        graph = HeterogeneousGraph()
        for node in graph_data.nodes:
            graph.add_node(
                node_id=node["id"],
                node_type=NodeType(node.get("type", "")),
                label=node.get("label", ""),
                attributes=node.get("attributes", {}),
            )
        for edge in graph_data.edges:
            graph.add_edge(
                source_id=edge["source"],
                target_id=edge["target"],
                edge_type=EdgeType(edge.get("type", "")),
                attributes=edge.get("attributes", {}),
            )

        return graph

    @staticmethod
    async def save_projected_graph(
        async_session: AsyncSession,
        graph_type: str,
        graph: HeterogeneousGraph,
        meta: dict | None = None,
    ) -> ProjectedGraphData:
        graph_dict = graph.to_dict()
        result = await async_session.execute(
            select(ProjectedGraphData).where(
                ProjectedGraphData.graph_type == graph_type
            )
        )
        existing = result.scalars().first()
        if existing:
            existing.nodes = graph_dict["nodes"]
            existing.edges = graph_dict["edges"]
            existing.meta = meta or {}
            await async_session.commit()
            return existing

        projected = ProjectedGraphData(
            graph_type=graph_type,
            nodes=graph_dict["nodes"],
            edges=graph_dict["edges"],
            meta=meta or {},
        )
        async_session.add(projected)
        await async_session.commit()
        return projected

    @staticmethod
    async def load_projected_graph(
        async_session: AsyncSession, graph_type: str
    ) -> HeterogeneousGraph | None:
        result = await async_session.execute(
            select(ProjectedGraphData).where(
                ProjectedGraphData.graph_type == graph_type
            )
        )
        graph_data = result.scalars().first()
        if not graph_data:
            return None

        graph = HeterogeneousGraph()
        for node in graph_data.nodes:
            graph.add_node(
                node_id=node["id"],
                node_type=NodeType(node.get("type", "")),
                label=node.get("label", ""),
                attributes=node.get("attributes", {}),
            )
        for edge in graph_data.edges:
            graph.add_edge(
                source_id=edge["source"],
                target_id=edge["target"],
                edge_type=EdgeType(edge.get("type", "")),
                attributes=edge.get("attributes", {}),
            )

        return graph

    @staticmethod
    async def build_and_save_all(async_session: AsyncSession) -> dict:
        hetero_graph = await GraphService.build_heterogeneous_graph(async_session)
        await GraphService.save_heterogeneous_graph(
            async_session,
            hetero_graph,
            meta={
                "total_nodes": hetero_graph.number_of_nodes(),
                "total_edges": hetero_graph.number_of_edges(),
            },
        )

        projections = {
            "game-mechanic": (
                GraphProjector.project_game_to_game(hetero_graph, "mechanic"),
                {"connection_type": "mechanic"},
            ),
            "game-category": (
                GraphProjector.project_game_to_game(hetero_graph, "category"),
                {"connection_type": "category"},
            ),
            "game-designer": (
                GraphProjector.project_game_to_game(hetero_graph, "designer"),
                {"connection_type": "designer"},
            ),
            "mechanic-mechanic": (
                GraphProjector.project_mechanic_to_mechanic(hetero_graph),
                {},
            ),
            "category-category": (
                GraphProjector.project_category_to_category(hetero_graph),
                {},
            ),
            "designer-designer": (
                GraphProjector.project_designer_to_designer(hetero_graph),
                {},
            ),
        }

        results = {
            "heterogeneous": {
                "nodes": hetero_graph.number_of_nodes(),
                "edges": hetero_graph.number_of_edges(),
            },
            "projections": {},
        }
        for graph_type, (proj_graph, meta) in projections.items():
            await GraphService.save_projected_graph(
                async_session,
                graph_type,
                proj_graph,
                meta={
                    **meta,
                    "total_nodes": proj_graph.number_of_nodes(),
                    "total_edges": proj_graph.number_of_edges(),
                },
            )
            results["projections"][graph_type] = {
                "nodes": proj_graph.number_of_nodes(),
                "edges": proj_graph.number_of_edges(),
            }

        return results
