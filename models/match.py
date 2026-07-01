"""Partidos del día (fútbol y tenis)."""

import enum
from datetime import datetime
from typing import Any, Optional

from sqlalchemy import Enum, ForeignKey, Index, String, func
from sqlalchemy.dialects.mysql import BIGINT, INTEGER, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship

from models.base import MYSQL_TABLE_KWARGS, Base


class Sport(str, enum.Enum):
    football = "football"
    tennis = "tennis"


class Match(Base):
    __tablename__ = "matches"
    __table_args__ = (
        Index("idx_sport_date", "sport", "match_datetime"),
        Index("idx_scraped", "scraped_at"),
        MYSQL_TABLE_KWARGS,
    )

    id: Mapped[int] = mapped_column(BIGINT(unsigned=True), primary_key=True, autoincrement=True)
    source_id: Mapped[int] = mapped_column(
        INTEGER(unsigned=True), ForeignKey("sources.id"), nullable=False
    )
    sport: Mapped[Sport] = mapped_column(Enum(Sport, native_enum=True), nullable=False)
    competition: Mapped[Optional[str]] = mapped_column(String(150), nullable=True)
    # home_team / away_team funcionan como player1 / player2 en tenis.
    home_team: Mapped[Optional[str]] = mapped_column(String(150), nullable=True)
    away_team: Mapped[Optional[str]] = mapped_column(String(150), nullable=True)
    match_datetime: Mapped[Optional[datetime]] = mapped_column(nullable=True)
    scraped_at: Mapped[datetime] = mapped_column(server_default=func.current_timestamp())
    raw_data: Mapped[Optional[dict[str, Any]]] = mapped_column(JSON, nullable=True)

    odds: Mapped[list["Odds"]] = relationship(
        back_populates="match", cascade="all, delete-orphan"
    )


# Import tardío para resolver la anotación "Odds" en relationship.
from models.odds import Odds  # noqa: E402
