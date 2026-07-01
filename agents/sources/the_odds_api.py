"""Agente piloto: The Odds API (REST).

Valida el modelo de datos de Fase 1 sin pelear anti-bot. Consulta el mercado
``h2h`` (head-to-head / 1X2) para uno o más deportes y normaliza los eventos a
Match/Odds.

Docs: https://the-odds-api.com/liveapi/guides/v4/
"""

from __future__ import annotations

from typing import Any

import httpx
from sqlalchemy.orm import Session

from agents.base_agent import BaseAgent
from config.settings import settings
from models.match import Match, Sport
from models.odds import Odds
from models.source import Source
from normalizer.normalizer import normalize_event

# sport_key de The Odds API → Sport del modelo.
# El free tier garantiza soccer; el tenis (si está disponible en el plan) usa
# claves como "tennis_atp_*". Ver Verificación en el plan.
DEFAULT_SPORT_KEYS: dict[str, Sport] = {
    # Fútbol europeo
    "soccer_epl": Sport.football,
    "soccer_italy_serie_a": Sport.football,
    "soccer_germany_dfb_pokal": Sport.football,
    # Fútbol sudamericano
    "soccer_conmebol_copa_libertadores": Sport.football,
    "soccer_conmebol_copa_sudamericana": Sport.football,
    "soccer_brazil_serie_b": Sport.football,
    # Tenis
    "tennis_wta_bad_homburg_open": Sport.tennis,
}


class TheOddsApiAgent(BaseAgent):
    def __init__(
        self,
        source: Source,
        db: Session,
        sport_keys: dict[str, Sport] | None = None,
        regions: str = "eu",
        timeout: float = 20.0,
    ) -> None:
        super().__init__(source, db)
        self.sport_keys = sport_keys or DEFAULT_SPORT_KEYS
        self.regions = regions
        self.timeout = timeout
        # Mapeo evento→deporte resuelto durante fetch, usado luego en normalize.
        self._event_sport: dict[int, Sport] = {}

    def _api_key(self) -> str:
        if not settings.odds_api_key:
            raise RuntimeError("ODDS_API_KEY no configurada en el entorno (.env).")
        return settings.odds_api_key

    def fetch(self) -> list[dict[str, Any]]:
        api_key = self._api_key()
        all_events: list[dict[str, Any]] = []

        with httpx.Client(base_url=settings.odds_api_base_url, timeout=self.timeout) as client:
            for sport_key, sport in self.sport_keys.items():
                resp = client.get(
                    f"/v4/sports/{sport_key}/odds",
                    params={
                        "apiKey": api_key,
                        "regions": self.regions,
                        "markets": "h2h",
                        "oddsFormat": "decimal",
                    },
                )
                resp.raise_for_status()
                events = resp.json()
                for event in events:
                    # Recordamos el deporte por identidad del dict para normalize().
                    self._event_sport[id(event)] = sport
                    all_events.append(event)

        return all_events

    def normalize(
        self, raw_events: list[dict[str, Any]]
    ) -> list[tuple[Match, list[Odds]]]:
        results: list[tuple[Match, list[Odds]]] = []
        for event in raw_events:
            sport = self._event_sport.get(id(event), Sport.football)
            results.append(normalize_event(event, sport, self.source.id))
        return results
