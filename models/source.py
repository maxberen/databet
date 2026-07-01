"""Fuentes configuradas desde el admin y su protocolo de scraping."""

import enum
from datetime import datetime
from typing import Any, Optional

from sqlalchemy import Enum, ForeignKey, String, func
from sqlalchemy.dialects.mysql import INTEGER, JSON, TINYINT
from sqlalchemy.orm import Mapped, mapped_column, relationship

from models.base import Base


class SourceType(str, enum.Enum):
    """Discriminador de implementación del agente.

    - ``api``: la fuente expone una API REST (p. ej. The Odds API). No usa los
      campos de SourceProtocol.
    - ``browser``: la fuente se scrapea con Playwright; usa SourceProtocol.
    """

    api = "api"
    browser = "browser"


class Source(Base):
    __tablename__ = "sources"

    id: Mapped[int] = mapped_column(INTEGER(unsigned=True), primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    base_url: Mapped[str] = mapped_column(String(255), nullable=False)
    type: Mapped[SourceType] = mapped_column(
        Enum(SourceType, native_enum=True),
        default=SourceType.browser,
        nullable=False,
    )
    is_active: Mapped[bool] = mapped_column(TINYINT(1), default=1, nullable=False)
    requires_auth: Mapped[bool] = mapped_column(TINYINT(1), default=0, nullable=False)
    # JSON cifrado en capa app (config.crypto). Nunca plain text.
    credentials: Mapped[Optional[str]] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(server_default=func.current_timestamp())
    updated_at: Mapped[Optional[datetime]] = mapped_column(
        server_default=func.current_timestamp(),
        onupdate=func.current_timestamp(),
    )

    protocol: Mapped[Optional["SourceProtocol"]] = relationship(
        back_populates="source",
        cascade="all, delete-orphan",
        uselist=False,
    )


class SourceProtocol(Base):
    """Protocolo de navegación/login por fuente. Opcional para fuentes ``api``."""

    __tablename__ = "source_protocols"

    id: Mapped[int] = mapped_column(INTEGER(unsigned=True), primary_key=True, autoincrement=True)
    source_id: Mapped[int] = mapped_column(
        INTEGER(unsigned=True), ForeignKey("sources.id"), nullable=False
    )
    login_flow: Mapped[Optional[dict[str, Any]]] = mapped_column(JSON, nullable=True)
    odds_navigation: Mapped[Optional[dict[str, Any]]] = mapped_column(JSON, nullable=True)
    selector_map: Mapped[Optional[dict[str, Any]]] = mapped_column(JSON, nullable=True)
    rate_limit_ms: Mapped[int] = mapped_column(default=1500, nullable=False)
    requires_captcha: Mapped[bool] = mapped_column(TINYINT(1), default=0, nullable=False)
    captcha_service: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    human_profile: Mapped[Optional[dict[str, Any]]] = mapped_column(JSON, nullable=True)
    session_max_minutes: Mapped[int] = mapped_column(default=30, nullable=False)
    notes: Mapped[Optional[str]] = mapped_column(String(1000), nullable=True)

    source: Mapped["Source"] = relationship(back_populates="protocol")
