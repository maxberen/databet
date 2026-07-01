"""Clase base de agente de scraping.

Define el ciclo de vida común (abrir ScrapeSession → fetch → normalizar →
persistir → cerrar sesión) y deja ``fetch`` y ``normalize`` como puntos de
extensión por fuente. Las subclases de Fase 1 son API-based (httpx); las de
fases futuras serán browser-based (Playwright) reutilizando este mismo ciclo.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import datetime, timezone
from typing import Any

from sqlalchemy.orm import Session

from models.match import Match
from models.odds import Odds
from models.scrape_session import ScrapeSession, SessionStatus
from models.source import Source


class BaseAgent(ABC):
    """Orquesta una sesión de scraping para una ``Source`` concreta."""

    def __init__(self, source: Source, db: Session) -> None:
        self.source = source
        self.db = db

    # --- Puntos de extensión por fuente ------------------------------------

    @abstractmethod
    def fetch(self) -> list[dict[str, Any]]:
        """Obtiene los eventos crudos de la fuente."""

    @abstractmethod
    def normalize(self, raw_events: list[dict[str, Any]]) -> list[tuple[Match, list[Odds]]]:
        """Convierte eventos crudos en pares (Match, [Odds])."""

    # --- Ciclo de vida ------------------------------------------------------

    def run(self) -> ScrapeSession:
        """Ejecuta el scraping completo y registra el resultado en ScrapeSession."""
        session_log = ScrapeSession(
            source_id=self.source.id,
            started_at=datetime.now(timezone.utc).replace(tzinfo=None),
            status=SessionStatus.running,
        )
        self.db.add(session_log)
        self.db.commit()

        try:
            raw_events = self.fetch()
            normalized = self.normalize(raw_events)

            for match, _odds in normalized:
                # Las Odds cuelgan de match vía relationship → cascade.
                self.db.add(match)

            session_log.matches_found = len(normalized)
            session_log.status = SessionStatus.success
        except Exception as exc:  # noqa: BLE001 — se registra y re-lanza control al log
            self.db.rollback()
            # Re-cargar el log tras el rollback para poder actualizarlo.
            self.db.add(session_log)
            session_log.status = SessionStatus.failed
            session_log.error_message = f"{type(exc).__name__}: {exc}"
        finally:
            session_log.ended_at = datetime.now(timezone.utc).replace(tzinfo=None)
            self.db.commit()
            self.db.refresh(session_log)

        return session_log
