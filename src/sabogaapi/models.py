import datetime

from sqlalchemy import JSON, Column, DateTime, ForeignKey, Index, Integer, String, Table
from sqlalchemy.orm import Mapped, mapped_column, relationship

from sabogaapi.database import Base

boardgame_category = Table(
    "boardgame_category",
    Base.metadata,
    Column("boardgame_id", ForeignKey("boardgames.id"), primary_key=True),
    Column("category_id", ForeignKey("categories.id"), primary_key=True),
)

boardgame_family = Table(
    "boardgame_family",
    Base.metadata,
    Column("boardgame_id", ForeignKey("boardgames.id"), primary_key=True),
    Column("family_id", ForeignKey("families.id"), primary_key=True),
)

boardgame_mechanic = Table(
    "boardgame_mechanic",
    Base.metadata,
    Column("boardgame_id", ForeignKey("boardgames.id"), primary_key=True),
    Column("mechanic_id", ForeignKey("mechanics.id"), primary_key=True),
)

boardgame_designer = Table(
    "boardgame_designer",
    Base.metadata,
    Column("boardgame_id", ForeignKey("boardgames.id"), primary_key=True),
    Column("designer_id", ForeignKey("designers.id"), primary_key=True),
)


class Boardgame(Base):
    __tablename__ = "boardgames"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    bgg_id: Mapped[int] = mapped_column(Integer, unique=True, index=True)
    bgg_rank: Mapped[int | None] = mapped_column(Integer, index=True)

    name: Mapped[str] = mapped_column(String, default="")
    bgg_geek_rating: Mapped[float | None]
    bgg_average_rating: Mapped[float | None]
    bgg_rank_volatility: Mapped[float | None]
    bgg_rank_trend: Mapped[float | None]
    bgg_geek_rating_volatility: Mapped[float | None]
    bgg_geek_rating_trend: Mapped[float | None]
    bgg_average_rating_volatility: Mapped[float | None]
    bgg_average_rating_trend: Mapped[float | None]
    mean_trend: Mapped[float | None]

    description: Mapped[str | None]
    image_url: Mapped[str | None]
    thumbnail_url: Mapped[str | None]

    year_published: Mapped[int | None]
    minplayers: Mapped[int | None]
    maxplayers: Mapped[int | None]
    playingtime: Mapped[int | None]
    minplaytime: Mapped[int | None]
    maxplaytime: Mapped[int | None]

    type: Mapped[str] = mapped_column(String, default="boardgame")

    bgg_rank_history: Mapped[list["RankHistory"]] = relationship(
        back_populates="boardgame",
        cascade="all, delete-orphan",
        lazy="noload",
    )

    # Relationships
    categories = relationship(
        "Category", secondary=boardgame_category, back_populates="boardgames"
    )
    families = relationship(
        "Family", secondary=boardgame_family, back_populates="boardgames"
    )
    mechanics = relationship(
        "Mechanic", secondary=boardgame_mechanic, back_populates="boardgames"
    )
    designers = relationship(
        "Designer", secondary=boardgame_designer, back_populates="boardgames"
    )


class Category(Base):
    __tablename__ = "categories"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String, nullable=False)
    bgg_id: Mapped[int] = mapped_column(Integer, unique=True, index=True)
    type: Mapped[str] = mapped_column(String, default="category")

    boardgames = relationship(
        "Boardgame", secondary=boardgame_category, back_populates="categories"
    )


class Designer(Base):
    __tablename__ = "designers"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String, nullable=False)
    bgg_id: Mapped[int] = mapped_column(Integer, unique=True, index=True)
    type: Mapped[str] = mapped_column(String, default="designer")

    boardgames = relationship(
        "Boardgame", secondary=boardgame_designer, back_populates="designers"
    )


class Family(Base):
    __tablename__ = "families"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String, nullable=False)
    bgg_id: Mapped[int] = mapped_column(Integer, unique=True, index=True)
    type: Mapped[str] = mapped_column(String, default="family")

    boardgames = relationship(
        "Boardgame", secondary=boardgame_family, back_populates="families"
    )


class Mechanic(Base):
    __tablename__ = "mechanics"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String, nullable=False)
    bgg_id: Mapped[int] = mapped_column(Integer, unique=True, index=True)
    type: Mapped[str] = mapped_column(String, default="mechanic")

    boardgames = relationship(
        "Boardgame", secondary=boardgame_mechanic, back_populates="mechanics"
    )


# --- Networks (JSON storage) ---
class BoardgameNetwork(Base):
    __tablename__ = "boardgame_network"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    nodes: Mapped[dict] = mapped_column(JSON)
    edges: Mapped[dict] = mapped_column(JSON)


class CategoryNetwork(Base):
    __tablename__ = "category_network"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    nodes: Mapped[dict] = mapped_column(JSON)
    edges: Mapped[dict] = mapped_column(JSON)


class DesignerNetwork(Base):
    __tablename__ = "designer_network"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    nodes: Mapped[dict] = mapped_column(JSON)
    edges: Mapped[dict] = mapped_column(JSON)


class FamilyNetwork(Base):
    __tablename__ = "family_network"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    nodes: Mapped[dict] = mapped_column(JSON)
    edges: Mapped[dict] = mapped_column(JSON)


class MechanicNetwork(Base):
    __tablename__ = "mechanic_network"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    nodes: Mapped[dict] = mapped_column(JSON)
    edges: Mapped[dict] = mapped_column(JSON)


class RankHistory(Base):
    __tablename__ = "rank_history"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    date: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True),
        default=datetime.datetime.now(datetime.UTC),
        index=True,
    )
    boardgame_id: Mapped[int] = mapped_column(
        ForeignKey("boardgames.id", ondelete="CASCADE"),
        index=True,
    )
    bgg_rank: Mapped[int | None]
    bgg_geek_rating: Mapped[float | None]
    bgg_average_rating: Mapped[float | None]

    boardgame: Mapped["Boardgame"] = relationship(back_populates="bgg_rank_history")

    __table_args__ = (Index("ix_rankhistory_boardgame_date", "boardgame_id", "date"),)


# --- Heterogeneous Graph Storage ---
class HeterogeneousGraphData(Base):
    __tablename__ = "heterogeneous_graph"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True),
        default=datetime.datetime.now(datetime.UTC),
        index=True,
    )
    updated_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True),
        default=datetime.datetime.now(datetime.UTC),
        onupdate=datetime.datetime.now(datetime.UTC),
    )
    nodes: Mapped[list[dict]] = mapped_column(JSON)
    edges: Mapped[list[dict]] = mapped_column(JSON)
    meta: Mapped[dict] = mapped_column(JSON, default={})


# --- Projected Graphs Storage ---
class ProjectedGraphData(Base):
    __tablename__ = "projected_graphs"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    graph_type: Mapped[str] = mapped_column(String, nullable=False, index=True)
    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True),
        default=datetime.datetime.now(datetime.UTC),
        index=True,
    )
    updated_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True),
        default=datetime.datetime.now(datetime.UTC),
        onupdate=datetime.datetime.now(datetime.UTC),
    )
    nodes: Mapped[list[dict]] = mapped_column(JSON)
    edges: Mapped[list[dict]] = mapped_column(JSON)
    meta: Mapped[dict] = mapped_column(JSON, default={})
