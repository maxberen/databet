"""Odds normalizadas por partido y fuente."""

from datetime import datetime
from decimal import Decimal
from typing import Optional

from sqlalchemy import DECIMAL, ForeignKey, Index, String, func
from sqlalchemy.dialects.mysql import BIGINT, INTEGER
from sqlalchemy.orm import Mapped, mapped_column, relationship

from models.base import MYSQL_TABLE_KWARGS, Base


class Odds(Base):
    __tablename__ = "odds"
    __table_args__ = (
        Index("idx_match_source", "match_id", "source_id"),
        MYSQL_TABLE_KWARGS,
    )

    id: Mapped[int] = mapped_column(BIGINT(unsigned=True), primary_key=True, autoincrement=True)
    match_id: Mapped[int] = mapped_column(
        BIGINT(unsigned=True), ForeignKey("matches.id"), nullable=False
    )
    source_id: Mapped[int] = mapped_column(
        INTEGER(unsigned=True), ForeignKey("sources.id"), nullable=False
    )
    scraped_at: Mapped[datetime] = mapped_column(server_default=func.current_timestamp())

    # Fútbol (3 outcomes)
    home_win: Mapped[Optional[Decimal]] = mapped_column(DECIMAL(10, 4), nullable=True)
    draw: Mapped[Optional[Decimal]] = mapped_column(DECIMAL(10, 4), nullable=True)
    away_win: Mapped[Optional[Decimal]] = mapped_column(DECIMAL(10, 4), nullable=True)

    # Tenis (2 outcomes)
    player1_win: Mapped[Optional[Decimal]] = mapped_column(DECIMAL(10, 4), nullable=True)
    player2_win: Mapped[Optional[Decimal]] = mapped_column(DECIMAL(10, 4), nullable=True)

    # Casa de apuestas concreta dentro de la fuente (The Odds API agrega varias).
    bookmaker: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)

    match: Mapped["Match"] = relationship(back_populates="odds")
