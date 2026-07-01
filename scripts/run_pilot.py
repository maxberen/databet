"""Ejecuta el agente piloto (The Odds API) end-to-end desde la CLI.

Uso:
    python -m scripts.run_pilot

Requisitos: .env con DATABASE_URL y ODDS_API_KEY, y migraciones aplicadas
(`alembic upgrade head`). Crea la fuente piloto si no existe.
"""

from __future__ import annotations

from agents.sources.the_odds_api import TheOddsApiAgent
from config.database import SessionLocal
from config.settings import settings
from models.source import Source, SourceType

PILOT_SOURCE_NAME = "The Odds API"


def get_or_create_pilot_source(db) -> Source:
    source = db.query(Source).filter(Source.name == PILOT_SOURCE_NAME).first()
    if source is None:
        source = Source(
            name=PILOT_SOURCE_NAME,
            base_url=settings.odds_api_base_url,
            type=SourceType.api,
            is_active=True,
            requires_auth=True,
        )
        db.add(source)
        db.commit()
        db.refresh(source)
    return source


def main() -> None:
    db = SessionLocal()
    try:
        source = get_or_create_pilot_source(db)
        agent = TheOddsApiAgent(source, db)
        session_log = agent.run()
        print(
            f"Sesión #{session_log.id} -> {session_log.status.value} | "
            f"matches: {session_log.matches_found}"
            + (f" | error: {session_log.error_message}" if session_log.error_message else "")
        )
    finally:
        db.close()


if __name__ == "__main__":
    main()
