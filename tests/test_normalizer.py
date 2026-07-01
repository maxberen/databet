"""Tests del normalizer — funciones puras, sin base de datos."""

from decimal import Decimal

from models.match import Sport
from normalizer.normalizer import normalize_event


def test_football_event_maps_outcomes_to_columns(football_event):
    match, odds = normalize_event(football_event, Sport.football, source_id=1)

    assert match.sport is Sport.football
    assert match.competition == "EPL"
    assert match.home_team == "Arsenal"
    assert match.away_team == "Manchester City"
    assert match.match_datetime is not None
    assert match.raw_data == football_event

    # Una fila de odds por bookmaker.
    assert len(odds) == 2
    betfair = next(o for o in odds if o.bookmaker == "Betfair")
    assert betfair.home_win == Decimal("2.50")
    assert betfair.away_win == Decimal("2.80")
    assert betfair.draw == Decimal("3.20")
    # Columnas de tenis quedan vacías.
    assert betfair.player1_win is None
    assert betfair.player2_win is None
    # Vinculadas al match vía relationship.
    assert betfair.match is match


def test_tennis_event_maps_players_without_draw(tennis_event):
    match, odds = normalize_event(tennis_event, Sport.tennis, source_id=2)

    assert match.sport is Sport.tennis
    assert match.home_team == "Novak Djokovic"
    assert len(odds) == 1
    o = odds[0]
    assert o.player1_win == Decimal("1.90")
    assert o.player2_win == Decimal("1.95")
    # Columnas de fútbol quedan vacías en tenis.
    assert o.home_win is None
    assert o.draw is None
    assert o.away_win is None


def test_event_without_h2h_market_yields_no_odds(football_event):
    football_event["bookmakers"][0]["markets"][0]["key"] = "totals"
    football_event["bookmakers"][1]["markets"] = []
    match, odds = normalize_event(football_event, Sport.football, source_id=1)
    assert match.home_team == "Arsenal"
    assert odds == []


def test_commence_time_is_parsed_to_naive_utc(football_event):
    match, _ = normalize_event(football_event, Sport.football, source_id=1)
    assert match.match_datetime.tzinfo is None
    assert match.match_datetime.year == 2026
    assert match.match_datetime.hour == 13
