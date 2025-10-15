from typing import Any

import community as community_louvain
import networkx as nx
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from sabogaapi import models
from sabogaapi.database import sessionmanager


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
    boardgames: list[models.Boardgame], designers: list[models.Designer]
) -> nx.Graph:
    graph = nx.Graph()

    for d in designers:
        graph.add_node(d.bgg_id, label=d.name, size=1)

    for g in boardgames:
        d_ids = [int(d.bgg_id) for d in g.designers]  # type: ignore[attr-defined]
        for i in range(len(d_ids)):
            graph.nodes[d_ids[i]]["size"] += 3
            for j in range(i + 1, len(d_ids)):
                if graph.has_edge(d_ids[i], d_ids[j]):
                    graph[d_ids[i]][d_ids[j]]["weight"] += 1
                else:
                    graph.add_edge(d_ids[i], d_ids[j], weight=1)

    # Clustering
    partition = community_louvain.best_partition(graph, weight="weight")
    for n in graph.nodes:
        if graph.degree[n] == 0:
            partition[n] = -1  # isolated nodes

    pos = nx.spring_layout(graph, seed=42, weight="weight", k=0.2)

    for n, data in graph.nodes(data=True):
        data["x"] = float(pos[n][0])
        data["y"] = float(pos[n][1])
        data["cluster"] = partition[n]

    for _u, _v, data in graph.edges(data=True):
        data["size"] = data.get("weight", 1)
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
    boardgames: list[models.Boardgame], categories: list[models.Category]
) -> nx.Graph:
    graph = nx.Graph()

    for c in categories:
        graph.add_node(c.bgg_id, label=c.name, size=1)

    for g in boardgames:
        d_ids = [int(d.bgg_id) for d in g.categories]  # type: ignore[attr-defined]
        for i in range(len(d_ids)):
            graph.nodes[d_ids[i]]["size"] += 3
            for j in range(i + 1, len(d_ids)):
                if graph.has_edge(d_ids[i], d_ids[j]):
                    graph[d_ids[i]][d_ids[j]]["weight"] += 1
                else:
                    graph.add_edge(d_ids[i], d_ids[j], weight=1)

    # Clustering
    partition = community_louvain.best_partition(graph, weight="weight")
    for n in graph.nodes:
        if graph.degree[n] == 0:
            partition[n] = -1  # isolated nodes

    pos = nx.spring_layout(graph, seed=42, weight="weight", k=0.2)

    for n, data in graph.nodes(data=True):
        data["x"] = float(pos[n][0])
        data["y"] = float(pos[n][1])
        data["cluster"] = partition[n]

    for _u, _v, data in graph.edges(data=True):
        data["size"] = data.get("weight", 1)
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
    boardgames: list[models.Boardgame], families: list[models.Family]
) -> nx.Graph:
    graph = nx.Graph()

    for f in families:
        graph.add_node(f.bgg_id, label=f.name, size=1)

    for g in boardgames:
        d_ids = [int(f.bgg_id) for f in g.families]  # type: ignore[attr-defined]
        for i in range(len(d_ids)):
            graph.nodes[d_ids[i]]["size"] += 3
            for j in range(i + 1, len(d_ids)):
                if graph.has_edge(d_ids[i], d_ids[j]):
                    graph[d_ids[i]][d_ids[j]]["weight"] += 1
                else:
                    graph.add_edge(d_ids[i], d_ids[j], weight=1)

    # Clustering
    partition = community_louvain.best_partition(graph, weight="weight")
    for n in graph.nodes:
        if graph.degree[n] == 0:
            partition[n] = -1  # isolated nodes

    pos = nx.spring_layout(graph, seed=42, weight="weight", k=0.2)

    for n, data in graph.nodes(data=True):
        data["x"] = float(pos[n][0])
        data["y"] = float(pos[n][1])
        data["cluster"] = partition[n]

    for _u, _v, data in graph.edges(data=True):
        data["size"] = data.get("weight", 1)
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
    boardgames: list[models.Boardgame], mechanics: list[models.Mechanic]
) -> nx.Graph:
    graph = nx.Graph()

    for m in mechanics:
        graph.add_node(m.bgg_id, label=m.name, size=1)

    for g in boardgames:
        d_ids = [int(m.bgg_id) for m in g.mechanics]  # type: ignore[attr-defined]
        for i in range(len(d_ids)):
            graph.nodes[d_ids[i]]["size"] += 3
            for j in range(i + 1, len(d_ids)):
                if graph.has_edge(d_ids[i], d_ids[j]):
                    graph[d_ids[i]][d_ids[j]]["weight"] += 1
                else:
                    graph.add_edge(d_ids[i], d_ids[j], weight=1)

    # Clustering
    partition = community_louvain.best_partition(graph, weight="weight")
    for n in graph.nodes:
        if graph.degree[n] == 0:
            partition[n] = -1  # isolated nodes

    pos = nx.spring_layout(graph, seed=42, weight="weight", k=0.2)

    for n, data in graph.nodes(data=True):
        data["x"] = float(pos[n][0])
        data["y"] = float(pos[n][1])
        data["cluster"] = partition[n]

    for _u, _v, data in graph.edges(data=True):
        data["size"] = data.get("weight", 1)
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


def build_boardgame_graph(  # noqa: C901, PLR0912
    boardgames: list[models.Boardgame],
    categories: list[models.Category],
    designers: list[models.Designer],
    families: list[models.Family],
    mechanics: list[models.Mechanic],
) -> nx.Graph:
    graph = nx.Graph()

    for g in boardgames:
        graph.add_node(g.bgg_id, label=g.name, size=1)

    for c in categories:
        g_ids = [int(g.bgg_id) for g in c.boardgames]  # type: ignore[attr-defined]
        for i in range(len(g_ids)):
            graph.nodes[g_ids[i]]["size"] += 3
            for j in range(i + 1, len(g_ids)):
                if graph.has_edge(g_ids[i], g_ids[j]):
                    graph[g_ids[i]][g_ids[j]]["weight"] += 1
                else:
                    graph.add_edge(g_ids[i], g_ids[j], weight=1)

    for d in designers:
        g_ids = [int(g.bgg_id) for g in d.boardgames]  # type: ignore[attr-defined]
        for i in range(len(g_ids)):
            graph.nodes[g_ids[i]]["size"] += 3
            for j in range(i + 1, len(g_ids)):
                if graph.has_edge(g_ids[i], g_ids[j]):
                    graph[g_ids[i]][g_ids[j]]["weight"] += 1
                else:
                    graph.add_edge(g_ids[i], g_ids[j], weight=1)

    for f in families:
        g_ids = [int(g.bgg_id) for g in f.boardgames]  # type: ignore[attr-defined]
        for i in range(len(g_ids)):
            graph.nodes[g_ids[i]]["size"] += 3
            for j in range(i + 1, len(g_ids)):
                if graph.has_edge(g_ids[i], g_ids[j]):
                    graph[g_ids[i]][g_ids[j]]["weight"] += 1
                else:
                    graph.add_edge(g_ids[i], g_ids[j], weight=1)

    for m in mechanics:
        g_ids = [int(g.bgg_id) for g in m.boardgames]  # type: ignore[attr-defined]
        for i in range(len(g_ids)):
            graph.nodes[g_ids[i]]["size"] += 3
            for j in range(i + 1, len(g_ids)):
                if graph.has_edge(g_ids[i], g_ids[j]):
                    graph[g_ids[i]][g_ids[j]]["weight"] += 1
                else:
                    graph.add_edge(g_ids[i], g_ids[j], weight=1)

    # Clustering
    partition = community_louvain.best_partition(graph, weight="weight")
    for n in graph.nodes:
        if graph.degree[n] == 0:
            partition[n] = -1  # isolated nodes

    pos = nx.spring_layout(graph, seed=42, weight="weight", k=0.2)

    for n, data in graph.nodes(data=True):
        data["x"] = float(pos[n][0])
        data["y"] = float(pos[n][1])
        data["cluster"] = partition[n]

    for _u, _v, data in graph.edges(data=True):
        data["size"] = data.get("weight", 1)
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
