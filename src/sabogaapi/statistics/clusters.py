from collections.abc import Iterable, Sequence
from typing import Any, TypeVar

import networkx as nx
import numpy as np
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from sabogaapi import models
from sabogaapi.database import sessionmanager

T = TypeVar("T", bound=models.Base)

BASE_NODE_SIZE = 1
BASE_EDGE_SIZE = 0.01


def build_edges(graph: nx.Graph, items: Sequence[T]) -> nx.Graph:
    for item in items:
        g_ids = [int(g.bgg_id) for g in item.boardgames]  # type: ignore[attr-defined]
        for i in range(len(g_ids)):
            graph.nodes[g_ids[i]]["size"] += 1
            for j in range(i + 1, len(g_ids)):
                if graph.has_edge(g_ids[i], g_ids[j]):
                    graph[g_ids[i]][g_ids[j]]["weight"] += 1
                else:
                    graph.add_edge(g_ids[i], g_ids[j], weight=1)

    return graph


def build_communities(
    graph: nx.Graph, min_weight: int
) -> tuple[Iterable, dict[Any, int]]:
    edges_to_remove = [
        (u, v) for u, v, d in graph.edges(data=True) if d["weight"] < min_weight
    ]
    graph.remove_edges_from(edges_to_remove)
    graph.remove_nodes_from(list(nx.isolates(graph)))

    communities = nx.community.greedy_modularity_communities(graph, weight="weight")
    node_to_comm = {node: i for i, comm in enumerate(communities) for node in comm}

    for _, comm in enumerate(communities):
        if len(comm) <= 2:
            for node in comm:
                node_to_comm[node] = -1

    return communities, node_to_comm


def graph_to_dict(graph: nx.Graph) -> dict[str, Any]:
    return {
        "nodes": [
            {
                "id": str(n),
                "label": graph.nodes[n].get("label", str(n)),
                "x": graph.nodes[n]["x"],
                "y": graph.nodes[n]["y"],
                "size": graph.nodes[n]["size"],
                "cluster": graph.nodes[n]["cluster"],
            }
            for n in graph.nodes
        ],
        "edges": [
            {
                "id": f"{u}-{v}",
                "label": d["label"],
                "source": str(u),
                "target": str(v),
                "size": d["size"],
            }
            for u, v, d in graph.edges(data=True)
        ],
    }


def build_designer_graph(
    boardgames: Sequence[models.Boardgame], designers: Sequence[models.Designer]
) -> nx.Graph:
    graph = nx.Graph()

    for d in designers:
        graph.add_node(d.bgg_id, label=d.name, size=1)

    graph = build_edges(graph, boardgames)

    communities, node_to_comm = build_communities(graph, min_weight=2)

    supergraph = nx.cycle_graph(len(communities))
    superpos = nx.spring_layout(supergraph, scale=5, seed=429)

    centers = list(superpos.values())

    pos = {}
    for center, comm in zip(centers, communities, strict=False):
        if len(comm) <= 2:
            k = 0.1
            scale = 0.1
        elif len(comm) <= 5:
            k = 0.5
            scale = 0.2
        elif len(comm) <= 20:
            k = 1.0
            scale = 1.0
        else:
            k = 2.0
            scale = 1.0

        pos.update(
            nx.spring_layout(
                nx.subgraph(graph, comm),
                center=center,
                seed=1430,
                k=k,
                scale=scale,
                iterations=50,
            )
        )

    for n, data in graph.nodes(data=True):
        data["x"] = float(pos[n][0])
        data["y"] = float(pos[n][1])
        data["cluster"] = node_to_comm[n]
        data["label"] = f"{data.get('label')} ({data.get('size') - 1})"
        data["size"] = BASE_NODE_SIZE * np.log1p(data.get("size"))

    for _u, _v, data in graph.edges(data=True):
        data["size"] = BASE_EDGE_SIZE * np.log1p(data.get("weight"))
        data["label"] = str(data.get("weight", 1))

    return graph


async def construct_designer_network() -> nx.Graph:
    """Construct a graph from designer data."""
    async with sessionmanager.session() as db_session:
        result_bg = await db_session.execute(
            select(models.Boardgame).options(selectinload(models.Boardgame.designers))
        )
        boardgames = result_bg.scalars().all()

        result_d = await db_session.execute(select(models.Designer))
        designers = result_d.scalars().all()
    return build_designer_graph(boardgames, designers)


def build_category_graph(
    boardgames: Sequence[models.Boardgame], categories: Sequence[models.Category]
) -> nx.Graph:
    graph = nx.Graph()

    for c in categories:
        graph.add_node(c.bgg_id, label=c.name, size=1)

    graph = build_edges(graph, boardgames)

    communities, node_to_comm = build_communities(graph, min_weight=2)

    supergraph = nx.cycle_graph(len(communities))
    superpos = nx.spring_layout(supergraph, scale=3, seed=429)

    # Use the "supernode" positions as the center of each node cluster
    centers = list(superpos.values())
    pos = {}
    for center, comm in zip(centers, communities, strict=False):
        pos.update(nx.spring_layout(nx.subgraph(graph, comm), center=center, seed=1430))

    for n in graph.nodes:
        if graph.degree[n] == 0:
            node_to_comm[n] = -1  # isolated nodes

    for n, data in graph.nodes(data=True):
        data["x"] = float(pos[n][0])
        data["y"] = float(pos[n][1])
        data["cluster"] = node_to_comm[n]
        data["label"] = f"{data.get('label')} ({data.get('size') - 1})"
        data["size"] = BASE_NODE_SIZE * np.log1p(data.get("size"))

    for _u, _v, data in graph.edges(data=True):
        data["size"] = BASE_EDGE_SIZE * np.log1p(data.get("weight"))
        data["label"] = str(data.get("weight", 1))

    return graph


async def construct_category_network() -> nx.Graph:
    """Construct a graph from designer data."""
    async with sessionmanager.session() as db_session:
        result_bg = await db_session.execute(
            select(models.Boardgame).options(selectinload(models.Boardgame.categories))
        )
        boardgames = result_bg.scalars().all()

        result_c = await db_session.execute(select(models.Category))
        categories = result_c.scalars().all()
    return build_category_graph(boardgames, categories)


def build_family_graph(
    boardgames: Sequence[models.Boardgame], families: Sequence[models.Family]
) -> nx.Graph:
    graph = nx.Graph()

    for f in families:
        graph.add_node(f.bgg_id, label=f.name, size=1)

    graph = build_edges(graph, boardgames)

    communities = nx.community.greedy_modularity_communities(graph, weight="weight")
    node_to_comm = {node: i for i, comm in enumerate(communities) for node in comm}

    supergraph = nx.cycle_graph(len(communities))
    superpos = nx.spring_layout(supergraph, scale=3, seed=429)

    centers = list(superpos.values())
    pos = {}
    for center, comm in zip(centers, communities, strict=False):
        pos.update(nx.spring_layout(nx.subgraph(graph, comm), center=center, seed=1430))

    for n in graph.nodes:
        if graph.degree[n] == 0:
            node_to_comm[n] = -1  # isolated nodes

    for n, data in graph.nodes(data=True):
        data["x"] = float(pos[n][0])
        data["y"] = float(pos[n][1])
        data["cluster"] = node_to_comm[n]
        data["label"] = f"{data.get('label')} ({data.get('size') - 1})"
        data["size"] = BASE_NODE_SIZE * np.log1p(data.get("size"))

    for _u, _v, data in graph.edges(data=True):
        data["size"] = BASE_EDGE_SIZE * np.log1p(data.get("weight"))
        data["label"] = str(data.get("weight", 1))

    return graph


async def construct_family_network() -> nx.Graph:
    """Construct a graph from designer data."""
    async with sessionmanager.session() as db_session:
        result_bg = await db_session.execute(
            select(models.Boardgame).options(selectinload(models.Boardgame.families))
        )
        boardgames = result_bg.scalars().all()

        result_f = await db_session.execute(select(models.Family))
        families = result_f.scalars().all()

    return build_family_graph(boardgames, families)


def build_mechanic_graph(
    boardgames: Sequence[models.Boardgame], mechanics: Sequence[models.Mechanic]
) -> nx.Graph:
    graph = nx.Graph()

    for m in mechanics:
        graph.add_node(m.bgg_id, label=m.name, size=1)

    graph = build_edges(graph, boardgames)

    communities, node_to_comm = build_communities(graph, min_weight=10)

    for _, comm in enumerate(communities):
        if len(comm) <= 2:  # or <= 3 for 2-3 nodes
            for node in comm:
                node_to_comm[node] = -1

    supergraph = nx.cycle_graph(len(list(communities)))
    superpos = nx.spring_layout(supergraph, scale=3, seed=429)

    centers = list(superpos.values())

    pos = {}
    for center, comm in zip(centers, communities, strict=False):
        if len(comm) <= 2:
            k = 0.1
            scale = 0.1
        elif len(comm) <= 5:
            k = 0.5
            scale = 0.2
        else:
            k = 2.0
            scale = 1.0

        pos.update(
            nx.spring_layout(
                nx.subgraph(graph, comm),
                center=center,
                seed=1430,
                k=k,
                scale=scale,
                iterations=50,
            )
        )

    for n, data in graph.nodes(data=True):
        data["x"] = float(pos[n][0])
        data["y"] = float(pos[n][1])
        data["cluster"] = node_to_comm[n]
        data["label"] = f"{data.get('label')} ({data.get('size') - 1})"
        data["size"] = BASE_NODE_SIZE * np.log1p(data.get("size"))

    for _u, _v, data in graph.edges(data=True):
        data["size"] = BASE_EDGE_SIZE * np.log1p(data.get("weight"))
        data["label"] = str(data.get("weight", 1))

    return graph


async def construct_mechanic_network() -> nx.Graph:
    """Construct a graph from designer data."""
    async with sessionmanager.session() as db_session:
        result_bg = await db_session.execute(
            select(models.Boardgame).options(selectinload(models.Boardgame.mechanics))
        )
        boardgames = result_bg.scalars().all()

        result_m = await db_session.execute(select(models.Mechanic))
        mechanics = result_m.scalars().all()

    return build_mechanic_graph(boardgames, mechanics)


def build_boardgame_graph(  # noqa: C901
    boardgames: Sequence[models.Boardgame],
    categories: Sequence[models.Category],
    designers: Sequence[models.Designer],
    families: Sequence[models.Family],
    mechanics: Sequence[models.Mechanic],
) -> nx.Graph:
    graph = nx.Graph()

    for g in boardgames:
        graph.add_node(g.bgg_id, label=g.name, size=1)

    graph = build_edges(graph, categories)

    graph = build_edges(graph, designers)

    graph = build_edges(graph, families)

    graph = build_edges(graph, mechanics)

    graph = build_edges(graph, categories)

    min_weight = 10
    edges_to_remove = [
        (u, v) for u, v, d in graph.edges(data=True) if d["weight"] < min_weight
    ]
    graph.remove_edges_from(edges_to_remove)
    graph.remove_nodes_from(list(nx.isolates(graph)))

    communities = nx.community.greedy_modularity_communities(graph, weight="weight")
    node_to_comm = {node: i for i, comm in enumerate(communities) for node in comm}

    for _, comm in enumerate(communities):
        if len(comm) <= 2:  # or <= 3 for 2-3 nodes
            for node in comm:
                node_to_comm[node] = -1

    supergraph = nx.cycle_graph(len(communities))
    superpos = nx.spring_layout(supergraph, scale=20, seed=429)

    centers = list(superpos.values())

    pos = {}
    for center, comm in zip(centers, communities, strict=False):
        if len(comm) <= 2:
            k = 0.1
            scale = 0.1
        elif len(comm) <= 5:
            k = 0.5
            scale = 0.2
        elif len(comm) <= 20:
            k = 1.0
            scale = 1.0
        else:
            k = 2.0
            scale = 1.0

        pos.update(
            nx.spring_layout(
                nx.subgraph(graph, comm),
                center=center,
                seed=1430,
                k=k,
                scale=scale,
                iterations=50,
            )
        )

    for n, data in graph.nodes(data=True):
        data["x"] = float(pos[n][0])
        data["y"] = float(pos[n][1])
        data["cluster"] = node_to_comm[n]
        data["label"] = f"{data.get('label')} ({data.get('size') - 1})"
        data["size"] = BASE_NODE_SIZE * np.log1p(data.get("size"))

    for _u, _v, data in graph.edges(data=True):
        data["size"] = BASE_EDGE_SIZE * np.log1p(data.get("weight"))
        data["label"] = str(data.get("weight", 1))

    return graph


async def construct_boardgame_network() -> nx.Graph:
    """Construct a graph from designer data."""
    async with sessionmanager.session() as db_session:
        result_bg = await db_session.execute(select(models.Boardgame))
        boardgames = result_bg.scalars().all()

        result_c = await db_session.execute(
            select(models.Category).options(selectinload(models.Category.boardgames))
        )
        categories = result_c.scalars().all()

        result_d = await db_session.execute(
            select(models.Designer).options(selectinload(models.Designer.boardgames))
        )
        designers = result_d.scalars().all()

        result_f = await db_session.execute(
            select(models.Family).options(selectinload(models.Family.boardgames))
        )
        families = result_f.scalars().all()

        result_m = await db_session.execute(
            select(models.Mechanic).options(selectinload(models.Mechanic.boardgames))
        )
        mechanics = result_m.scalars().all()

    return build_boardgame_graph(boardgames, categories, designers, families, mechanics)
