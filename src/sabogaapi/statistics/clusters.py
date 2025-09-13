
from typing import Any

import community as community_louvain
import networkx as nx

from sabogaapi import models


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
    boardgames = await models.Boardgame.find({}, fetch_links=True).to_list()
    designers = await models.Designer.find().to_list()
    return build_designer_graph(boardgames, designers)
