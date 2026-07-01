"""Normaliza eventos crudos de The Odds API al modelo estándar (Match + Odds).

Funciones puras: construyen objetos ORM en memoria sin commitear, por lo que se
testean sin base de datos. La persistencia es responsabilidad del agente.

Formato de evento de The Odds API v4 (mercado h2h)::

    {
      "sport_title": "EPL",
      "commence_time": "2023-10-08T13:00:00Z",
      "home_team": "Arsenal",
      "away_team": "Manchester City",
      "bookmakers": [
        {"key": "betfair", "title": "Betfair", "markets": [
          {"key": "h2h", "outcomes": [
            {"name": "Arsenal", "price": 2.5},
            {"name": "Manchester City", "price": 2.8},
            {"name": "Draw", "price": 3.2}
          ]}
        ]}
      ]
    }

En tenis no hay outcome ``Draw``; ``home_team``/``away_team`` son los jugadores.
"""

from datetime import datetime
from decimal import Decimal
from typing import Any, Optional

from models.match import Match, Sport
from models.odds import Odds

# Nombre del outcome de empate en The Odds API.
_DRAW_NAME = "Draw"


def _parse_commence_time(value: Optional[str]) -> Optional[datetime]:
    """Convierte un timestamp ISO-8601 (con 'Z') a datetime naive (UTC)."""
    if not value:
        return None
    dt = datetime.fromisoformat(value.replace("Z", "+00:00"))
    # Columna DATETIME sin tz: guardamos el instante UTC como naive.
    return dt.replace(tzinfo=None)


def _price_to_decimal(price: Any) -> Optional[Decimal]:
    if price is None:
        return None
    # Pasar por str evita errores de binario flotante en DECIMAL(10,4).
    return Decimal(str(price))


def _h2h_outcomes(bookmaker: dict[str, Any]) -> dict[str, Any]:
    """Devuelve {nombre_outcome: price} del mercado h2h de un bookmaker."""
    for market in bookmaker.get("markets", []):
        if market.get("key") == "h2h":
            return {o["name"]: o.get("price") for o in market.get("outcomes", [])}
    return {}


def normalize_event(
    raw_event: dict[str, Any],
    sport: Sport,
    source_id: int,
) -> tuple[Match, list[Odds]]:
    """Normaliza un evento crudo a un Match con sus Odds (una fila por bookmaker).

    Las Odds quedan vinculadas al Match vía relationship, así un solo
    ``session.add(match)`` persiste todo en cascada.
    """
    home = raw_event.get("home_team")
    away = raw_event.get("away_team")

    match = Match(
        source_id=source_id,
        sport=sport,
        competition=raw_event.get("sport_title"),
        home_team=home,
        away_team=away,
        match_datetime=_parse_commence_time(raw_event.get("commence_time")),
        raw_data=raw_event,
    )

    odds_list: list[Odds] = []
    for bookmaker in raw_event.get("bookmakers", []):
        prices = _h2h_outcomes(bookmaker)
        if not prices:
            continue

        if sport is Sport.football:
            odds = Odds(
                source_id=source_id,
                bookmaker=bookmaker.get("title") or bookmaker.get("key"),
                home_win=_price_to_decimal(prices.get(home)),
                away_win=_price_to_decimal(prices.get(away)),
                draw=_price_to_decimal(prices.get(_DRAW_NAME)),
            )
        else:  # tenis: home/away = player1/player2
            odds = Odds(
                source_id=source_id,
                bookmaker=bookmaker.get("title") or bookmaker.get("key"),
                player1_win=_price_to_decimal(prices.get(home)),
                player2_win=_price_to_decimal(prices.get(away)),
            )

        odds.match = match  # vincula vía relationship (cascade)
        odds_list.append(odds)

    return match, odds_list
