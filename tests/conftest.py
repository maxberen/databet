"""Fixtures compartidas para los tests."""

import pytest


@pytest.fixture
def football_event() -> dict:
    """Evento de fútbol con mercado h2h (3 outcomes) y 2 bookmakers."""
    return {
        "id": "abc123",
        "sport_key": "soccer_epl",
        "sport_title": "EPL",
        "commence_time": "2026-06-20T13:00:00Z",
        "home_team": "Arsenal",
        "away_team": "Manchester City",
        "bookmakers": [
            {
                "key": "betfair",
                "title": "Betfair",
                "markets": [
                    {
                        "key": "h2h",
                        "outcomes": [
                            {"name": "Arsenal", "price": 2.50},
                            {"name": "Manchester City", "price": 2.80},
                            {"name": "Draw", "price": 3.20},
                        ],
                    }
                ],
            },
            {
                "key": "pinnacle",
                "title": "Pinnacle",
                "markets": [
                    {
                        "key": "h2h",
                        "outcomes": [
                            {"name": "Arsenal", "price": 2.55},
                            {"name": "Manchester City", "price": 2.75},
                            {"name": "Draw", "price": 3.30},
                        ],
                    }
                ],
            },
        ],
    }


@pytest.fixture
def tennis_event() -> dict:
    """Evento de tenis con mercado h2h (2 outcomes, sin Draw)."""
    return {
        "id": "xyz789",
        "sport_key": "tennis_atp",
        "sport_title": "ATP",
        "commence_time": "2026-06-21T09:30:00Z",
        "home_team": "Novak Djokovic",
        "away_team": "Carlos Alcaraz",
        "bookmakers": [
            {
                "key": "betfair",
                "title": "Betfair",
                "markets": [
                    {
                        "key": "h2h",
                        "outcomes": [
                            {"name": "Novak Djokovic", "price": 1.90},
                            {"name": "Carlos Alcaraz", "price": 1.95},
                        ],
                    }
                ],
            }
        ],
    }
