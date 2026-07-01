"""Log de sesiones de scraping."""

import enum
from datetime import datetime
from typing import Optional

from sqlalchemy import Enum, ForeignKey, String, Text
from sqlalchemy.dialects.mysql import INTEGER
from sqlalchemy.orm import Mapped, mapped_column

from models.base import Base


class SessionStatus(str, enum.Enum):
    running = "running"
    success = "success"
    failed = "failed"
    blocked = "blocked"


class ScrapeSession(Base):
    __tablename__ = "scrape_sessions"

    id: Mapped[int] = mapped_column(INTEGER(unsigned=True), primary_key=True, autoincrement=True)
    source_id: Mapped[int] = mapped_column(
        INTEGER(unsigned=True), ForeignKey("sources.id"), nullable=False
    )
    started_at: Mapped[Optional[datetime]] = mapped_column(nullable=True)
    ended_at: Mapped[Optional[datetime]] = mapped_column(nullable=True)
    status: Mapped[SessionStatus] = mapped_column(
        Enum(SessionStatus, native_enum=True), nullable=False
    )
    matches_found: Mapped[int] = mapped_column(default=0, nullable=False)
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    proxy_used: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
