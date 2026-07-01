"""Agente para aposta.la (motor Kambi) — sin autenticación.

Estrategia: una sola llamada al endpoint starting-within por deporte
que devuelve todos los partidos de las próximas 24 horas con betOffers
incluidos. Excluye esports y apuestas especiales (ganador de torneo, etc.).
"""

from __future__ import annotations

from datetime import datetime, timezone, timedelta
from decimal import Decimal
from typing import Any

import httpx
from sqlalchemy.orm import Session

from agents.base_agent import BaseAgent
from models.match import Match, Sport
from models.odds import Odds
from models.source import Source

BASE_URL = "https://us.offering-api.kambicdn.com/offering/v2018/betplayintpy"

BASE_PARAMS: dict[str, Any] = {
    "channel_id": 1,
    "client_id": 200,
    "lang": "es_PY",
    "market": "PY",
    "useCombined": "true",
}

# termKeys de grupos a excluir (esports, apuestas especiales de torneo)
EXCLUDED_TERM_KEYS = {
    "esports_football",
    "esports_basketball",
    "esports",
    "apostala_especiales",
}

# Tags de evento que indican que NO es un partido normal
EXCLUDED_EVENT_TAGS = {"COMPETITION"}

BOOKMAKER_NAME = "ApostaLA"

_TYPE_ONE = "OT_ONE"
_TYPE_TWO = "OT_TWO"


def _to_decimal(value: int | None) -> Decimal | None:
    if value is None:
        return None
    return Decimal(str(value)) / Decimal("1000")


def _parse_start(value: str | None) -> datetime | None:
    if not value:
        return None
    return datetime.fromisoformat(value.replace("Z", "+00:00")).replace(tzinfo=None)


def _main_offer(offers: list[dict]) -> dict | None:
    for o in offers:
        if "MAIN" in o.get("tags", []) and o.get("betOfferType", {}).get("englishName") == "Match":
            return o
    return None


def _is_real_match(event: dict) -> bool:
    """Descarta apuestas especiales (ganador de torneo, goleador, etc.)."""
    tags = set(event.get("tags", []))
    if tags & EXCLUDED_EVENT_TAGS:
        return False
    # Verificar que ningún nivel del path sea esports
    for path in event.get("path", []):
        if path.get("termKey") in EXCLUDED_TERM_KEYS:
            return False
    # Debe tener homeName y awayName (partidos reales)
    return bool(event.get("homeName") and event.get("awayName"))


class ApostaLAAgent(BaseAgent):
    def __init__(
        self,
        source: Source,
        db: Session,
        hours_ahead: int = 24,
        timeout: float = 30.0,
    ) -> None:
        super().__init__(source, db)
        self.hours_ahead = hours_ahead
        self.timeout = timeout

    def _time_params(self) -> dict:
        now = datetime.now(timezone.utc)
        to = now + timedelta(hours=self.hours_ahead)
        fmt = lambda d: d.strftime("%Y%m%dT%H%M%S") + "-0000"
        return {"from": fmt(now), "to": fmt(to)}

    def fetch(self) -> list[dict[str, Any]]:
        results: list[dict[str, Any]] = []
        time_params = self._time_params()

        with httpx.Client(base_url=BASE_URL, timeout=self.timeout) as client:
            for sport_path, sport_enum in [("football", Sport.football), ("tennis", Sport.tennis)]:
                url = f"/listView/{sport_path}/all/all/all/starting-within.json"
                resp = client.get(url, params={**BASE_PARAMS, **time_params})
                resp.raise_for_status()

                for raw in resp.json().get("events", []):
                    ev = raw.get("event", {})
                    if not _is_real_match(ev):
                        continue
                    offer = _main_offer(raw.get("betOffers", []))
                    if not offer:
                        continue
                    results.append({**ev, "_offer": offer, "_sport": sport_enum})

        return results

    def normalize(
        self, raw_events: list[dict[str, Any]]
    ) -> list[tuple[Match, list[Odds]]]:
        out: list[tuple[Match, list[Odds]]] = []
        for ev in raw_events:
            offer = ev["_offer"]
            sport: Sport = ev["_sport"]

            outcomes = offer.get("outcomes", [])
            by_type = {o["type"]: o for o in outcomes}
            by_label = {o["label"]: o for o in outcomes}

            match = Match(
                source_id=self.source.id,
                sport=sport,
                competition=ev.get("group", ""),
                home_team=ev.get("homeName", ""),
                away_team=ev.get("awayName", ""),
                match_datetime=_parse_start(ev.get("start")),
                raw_data={k: v for k, v in ev.items() if not k.startswith("_")},
            )

            if sport is Sport.football:
                odds = Odds(
                    source_id=self.source.id,
                    bookmaker=BOOKMAKER_NAME,
                    home_win=_to_decimal(by_label.get("1", {}).get("odds")),
                    draw=_to_decimal(by_label.get("X", {}).get("odds")),
                    away_win=_to_decimal(by_label.get("2", {}).get("odds")),
                )
            else:
                p1 = by_type.get(_TYPE_ONE, {})
                p2 = by_type.get(_TYPE_TWO, {})
                odds = Odds(
                    source_id=self.source.id,
                    bookmaker=BOOKMAKER_NAME,
                    player1_win=_to_decimal(p1.get("odds")),
                    player2_win=_to_decimal(p2.get("odds")),
                )

            odds.match = match
            out.append((match, [odds]))

        return out
