"""Ejecuta el agente de aposta.la (Kambi) end-to-end desde la CLI.

Uso:
    python -m scripts.run_apostala

No requiere API key. Crea la fuente en la BD si no existe.
"""

from __future__ import annotations

from agents.sources.apostala import ApostaLAAgent
from config.database import SessionLocal
from models.source import Source, SourceType

SOURCE_NAME = "ApostaLA"
SOURCE_URL = "https://aposta.la"


def get_or_create_source(db) -> Source:
    source = db.query(Source).filter(Source.name == SOURCE_NAME).first()
    if source is None:
        source = Source(
            name=SOURCE_NAME,
            base_url=SOURCE_URL,
            type=SourceType.api,
            is_active=True,
            requires_auth=False,
        )
        db.add(source)
        db.commit()
        db.refresh(source)
    return source


def main() -> None:
    db = SessionLocal()
    try:
        source = get_or_create_source(db)
        agent = ApostaLAAgent(source, db)
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
