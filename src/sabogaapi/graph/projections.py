"""Graph projections for creating node-type-specific graphs."""

from sabogaapi.graph import EdgeType, HeterogeneousGraph, NodeType


class GraphProjector:
    """Projects heterogeneous graphs to single-node-type graphs."""

    @staticmethod
    def create_or_count_edges(
        projected: HeterogeneousGraph,
        game1_id: str,
        game2_id: str,
        connection_type: str,
        edge_type: EdgeType,
    ) -> None:
        # Count how many shared connections
        existing_edge = False
        for (
            existing_source,
            existing_target,
            existing_attrs,
        ) in projected.get_edges_by_type(edge_type):
            if existing_source == game1_id and existing_target == game2_id:
                existing_attrs["count"] = existing_attrs.get("count", 1) + 1
                existing_edge = True
                break

        if not existing_edge:
            projected.add_edge(
                game1_id,
                game2_id,
                edge_type,
                attributes={"connection": connection_type, "count": 1},
            )

    def project_game_to_game(
        self,
        graph: HeterogeneousGraph,
        connection_type: str = "mechanic",
    ) -> HeterogeneousGraph:
        """Project graph to game-to-game connections.

        Creates edges between games that share mechanics or categories.

        Args:
            graph: The heterogeneous graph
            connection_type: 'mechanic', 'category', or 'designer'

        Returns:
            A projected graph with only game nodes and edges between them
        """
        projected = HeterogeneousGraph()

        # Add all game nodes
        game_nodes = graph.get_nodes_by_type(NodeType.GAME)
        for game_id, attrs in game_nodes:
            projected.add_node(
                game_id,
                NodeType.GAME,
                attrs["label"],
                attributes={
                    k: v for k, v in attrs.items() if k not in ("type", "label")
                },
            )

        # Create edges based on shared connections
        if connection_type == "mechanic":
            edge_type = EdgeType.HAS_MECHANIC
            connection_nodes = graph.get_nodes_by_type(NodeType.MECHANIC)
        elif connection_type == "category":
            edge_type = EdgeType.HAS_CATEGORY
            connection_nodes = graph.get_nodes_by_type(NodeType.CATEGORY)
        elif connection_type == "designer":
            edge_type = EdgeType.HAS_DESIGNER
            connection_nodes = graph.get_nodes_by_type(NodeType.DESIGNER)
        else:
            error_msg = f"Unknown connection_type: {connection_type}"
            raise ValueError(error_msg)

        # For each connection node, find all games connected to it
        for conn_id, _ in connection_nodes:
            incoming_edges = graph.get_incoming_edges(conn_id)
            game_ids = [
                source_id
                for source_id, _, _ in incoming_edges
                if source_id in {g[0] for g in game_nodes}
            ]

            # Create edges between all games sharing this connection
            for i, game1_id in enumerate(game_ids):
                for game2_id in game_ids[i + 1 :]:
                    if game1_id != game2_id:
                        self.create_or_count_edges(
                            projected,
                            game1_id,
                            game2_id,
                            connection_type,
                            edge_type,
                        )

        return projected

    @staticmethod
    def project_mechanic_to_mechanic(graph: HeterogeneousGraph) -> HeterogeneousGraph:
        """Project graph to mechanic-to-mechanic connections.

        Creates edges between mechanics that appear together in games.

        Args:
            graph: The heterogeneous graph

        Returns:
            A projected graph with only mechanic nodes
        """
        projected = HeterogeneousGraph()

        # Add all mechanic nodes
        mechanic_nodes = graph.get_nodes_by_type(NodeType.MECHANIC)
        for mechanic_id, attrs in mechanic_nodes:
            projected.add_node(
                mechanic_id,
                NodeType.MECHANIC,
                attrs["label"],
                attributes={
                    k: v for k, v in attrs.items() if k not in ("type", "label")
                },
            )

        # Create edges between mechanics that appear together
        game_nodes = graph.get_nodes_by_type(NodeType.GAME)

        for game_id, _ in game_nodes:
            neighbors = graph.get_neighbors(game_id, direction="outgoing")
            mechanics = [
                n
                for n in neighbors.get("outgoing", [])
                if n[1]["type"] == NodeType.MECHANIC.value
            ]
            mechanic_ids = [m[0] for m in mechanics]

            # Create edges between all mechanic pairs in this game
            for i, mech1_id in enumerate(mechanic_ids):
                for mech2_id in mechanic_ids[i + 1 :]:
                    if mech1_id != mech2_id:
                        # Find or update edge
                        edges = projected.get_edges_by_type(EdgeType.HAS_MECHANIC)
                        existing = next(
                            (e for e in edges if e[0] == mech1_id and e[1] == mech2_id),
                            None,
                        )
                        if existing:
                            existing[2]["count"] = existing[2].get("count", 1) + 1
                        else:
                            projected.add_edge(
                                mech1_id,
                                mech2_id,
                                EdgeType.HAS_MECHANIC,
                                attributes={"shared_games": 1},
                            )

        return projected

    @staticmethod
    def project_category_to_category(graph: HeterogeneousGraph) -> HeterogeneousGraph:
        """Project graph to category-to-category connections.

        Creates edges between categories that share games.

        Args:
            graph: The heterogeneous graph

        Returns:
            A projected graph with only category nodes
        """
        projected = HeterogeneousGraph()

        # Add all category nodes
        category_nodes = graph.get_nodes_by_type(NodeType.CATEGORY)
        for category_id, attrs in category_nodes:
            projected.add_node(
                category_id,
                NodeType.CATEGORY,
                attrs["label"],
                attributes={
                    k: v for k, v in attrs.items() if k not in ("type", "label")
                },
            )

        # Create edges between categories that share games
        game_nodes = graph.get_nodes_by_type(NodeType.GAME)

        for game_id, _ in game_nodes:
            neighbors = graph.get_neighbors(game_id, direction="outgoing")
            categories = [
                n
                for n in neighbors.get("outgoing", [])
                if n[1]["type"] == NodeType.CATEGORY.value
            ]
            category_ids = [c[0] for c in categories]

            # Create edges between all category pairs in this game
            for i, cat1_id in enumerate(category_ids):
                for cat2_id in category_ids[i + 1 :]:
                    if cat1_id != cat2_id:
                        edges = projected.get_edges_by_type(EdgeType.HAS_CATEGORY)
                        existing = next(
                            (e for e in edges if e[0] == cat1_id and e[1] == cat2_id),
                            None,
                        )
                        if existing:
                            existing[2]["count"] = existing[2].get("count", 1) + 1
                        else:
                            projected.add_edge(
                                cat1_id,
                                cat2_id,
                                EdgeType.HAS_CATEGORY,
                                attributes={"shared_games": 1},
                            )

        return projected

    @staticmethod
    def project_designer_to_designer(graph: HeterogeneousGraph) -> HeterogeneousGraph:
        """Project graph to designer-to-designer connections.

        Creates edges between designers that collaborate on games.

        Args:
            graph: The heterogeneous graph

        Returns:
            A projected graph with only designer nodes
        """
        projected = HeterogeneousGraph()

        # Add all designer nodes
        designer_nodes = graph.get_nodes_by_type(NodeType.DESIGNER)
        for designer_id, attrs in designer_nodes:
            projected.add_node(
                designer_id,
                NodeType.DESIGNER,
                attrs["label"],
                attributes={
                    k: v for k, v in attrs.items() if k not in ("type", "label")
                },
            )

        # Create edges between designers that collaborate
        game_nodes = graph.get_nodes_by_type(NodeType.GAME)

        for game_id, _ in game_nodes:
            neighbors = graph.get_neighbors(game_id, direction="outgoing")
            designers = [
                n
                for n in neighbors.get("outgoing", [])
                if n[1]["type"] == NodeType.DESIGNER.value
            ]
            designer_ids = [d[0] for d in designers]

            # Create edges between all designer pairs in this game
            for i, des1_id in enumerate(designer_ids):
                for des2_id in designer_ids[i + 1 :]:
                    if des1_id != des2_id:
                        edges = projected.get_edges_by_type(EdgeType.HAS_DESIGNER)
                        existing = next(
                            (e for e in edges if e[0] == des1_id and e[1] == des2_id),
                            None,
                        )
                        if existing:
                            existing[2]["count"] = existing[2].get("count", 1) + 1
                        else:
                            projected.add_edge(
                                des1_id,
                                des2_id,
                                EdgeType.HAS_DESIGNER,
                                attributes={"shared_games": 1},
                            )

        return projected
