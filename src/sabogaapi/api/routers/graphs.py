"""API endpoints for heterogeneous graph access."""

from fastapi import APIRouter

from sabogaapi.api.dependencies.core import DBSessionDep
from sabogaapi.graph import GraphProjector
from sabogaapi.services import GraphService

router = APIRouter(prefix="/graphs", tags=["graphs"])


@router.get("/heterogeneous")
async def get_heterogeneous_graph(db_session: DBSessionDep) -> dict:
    """Get the complete heterogeneous graph.

    Returns:
        The heterogeneous graph in dictionary format with nodes and edges
    """
    graph = await GraphService.load_heterogeneous_graph(db_session)

    if graph is None:
        # Build on-the-fly if not in database
        graph = await GraphService.build_heterogeneous_graph(db_session)

    return graph.to_dict()


@router.post("/heterogeneous/build")
async def build_and_save_heterogeneous_graph(db_session: DBSessionDep) -> dict:
    """Build and save the complete heterogeneous graph.

    Returns:
        Status and statistics about the built graph
    """
    graph = await GraphService.build_heterogeneous_graph(db_session)
    await GraphService.save_heterogeneous_graph(db_session, graph)

    stats = graph.get_statistics()
    return {
        "status": "success",
        "graph_statistics": stats,
    }


@router.get("/projected/{graph_type}")
async def get_projected_graph(graph_type: str, db_session: DBSessionDep) -> dict:
    """Get a projected graph by type.

    Args:
        graph_type: One of 'game-mechanic', 'game-category', 'game-designer',
                   'mechanic-mechanic', 'category-category', 'designer-designer'

    Returns:
        The projected graph in dictionary format
    """
    graph = await GraphService.load_projected_graph(db_session, graph_type)

    if graph is None:
        # Build on-the-fly if not in database
        hetero_graph = await GraphService.load_heterogeneous_graph(db_session)
        if hetero_graph is None:
            hetero_graph = await GraphService.build_heterogeneous_graph(db_session)

        if graph_type == "game-mechanic":
            graph = GraphProjector.project_game_to_game(hetero_graph, "mechanic")
        elif graph_type == "game-category":
            graph = GraphProjector.project_game_to_game(hetero_graph, "category")
        elif graph_type == "game-designer":
            graph = GraphProjector.project_game_to_game(hetero_graph, "designer")
        elif graph_type == "mechanic-mechanic":
            graph = GraphProjector.project_mechanic_to_mechanic(hetero_graph)
        elif graph_type == "category-category":
            graph = GraphProjector.project_category_to_category(hetero_graph)
        elif graph_type == "designer-designer":
            graph = GraphProjector.project_designer_to_designer(hetero_graph)
        else:
            return {
                "error": f"Unknown graph type: {graph_type}",
                "available_types": [
                    "game-mechanic",
                    "game-category",
                    "game-designer",
                    "mechanic-mechanic",
                    "category-category",
                    "designer-designer",
                ],
            }

    return graph.to_dict()


@router.post("/build-all")
async def build_and_save_all_graphs(db_session: DBSessionDep) -> dict:
    """Build and save all graphs (heterogeneous + all projections).

    This is a comprehensive operation that builds and stores:
    - The main heterogeneous graph
    - All 6 projected graphs

    Returns:
        Status and statistics about all built graphs
    """
    results = await GraphService.build_and_save_all(db_session)

    return {
        "status": "success",
        "graphs_built": results,
    }


@router.get("/")
async def get_all_graphs(db_session: DBSessionDep) -> dict:
    """Get all available graphs.

    Returns a dictionary containing:
    - heterogeneous: The complete heterogeneous graph
    - projected: All 6 projected graphs (game-mechanic, game-category, game-designer,
        mechanic-mechanic, category-category, designer-designer)
    - entity-networks: The entity-specific networks (categories, designers, families,
        mechanics, boardgames)
    """

    # Load or build heterogeneous graph
    hetero_graph = await GraphService.load_heterogeneous_graph(db_session)
    if hetero_graph is None:
        hetero_graph = await GraphService.build_heterogeneous_graph(db_session)

    # Prepare projected graphs
    projections = {}
    projection_types = {
        "game-mechanic": lambda g: GraphProjector.project_game_to_game(g, "mechanic"),
        "game-category": lambda g: GraphProjector.project_game_to_game(g, "category"),
        "game-designer": lambda g: GraphProjector.project_game_to_game(g, "designer"),
        "mechanic-mechanic": lambda g: GraphProjector.project_mechanic_to_mechanic(g),
        "category-category": lambda g: GraphProjector.project_category_to_category(g),
        "designer-designer": lambda g: GraphProjector.project_designer_to_designer(g),
    }

    for graph_type, projector_fn in projection_types.items():
        cached_graph = await GraphService.load_projected_graph(db_session, graph_type)
        if cached_graph is not None:
            projections[graph_type] = cached_graph.to_dict()
        else:
            # Build on-the-fly if not cached
            graph = projector_fn(hetero_graph)
            projections[graph_type] = graph.to_dict()

    return {
        "heterogeneous": hetero_graph.to_dict(),
        "projected": projections,
    }


@router.get("/list-available")
async def list_available_graphs() -> dict:
    """List all available graph types.

    Returns:
        List of available graph types
    """
    return {
        "available_graphs": [
            {
                "type": "heterogeneous",
                "description": (
                    "Complete heterogeneous graph with all node and edge types"
                ),
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
                "description": (
                    "Designer-to-designer collaborations through shared games"
                ),
            },
        ]
    }
