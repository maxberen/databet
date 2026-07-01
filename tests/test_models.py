"""Tests de integración del modelo contra MySQL.

Se ejecutan sólo si TEST_DATABASE_URL apunta a una base MySQL desechable
(p. ej. `betting_system_test`). Validan tipos UNSIGNED/JSON/DECIMAL/ENUM que
SQLite no replica, por eso no se mockea con SQLite.

    TEST_DATABASE_URL=mysql+pymysql://user:pass@127.0.0.1:3306/betting_system_test pytest
"""

import os
from decimal import Decimal

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from models import Base, Match, Odds, ScrapeSession, SessionStatus, Source, Sport, SourceType

TEST_DATABASE_URL = os.getenv("TEST_DATABASE_URL")

pytestmark = pytest.mark.skipif(
    not TEST_DATABASE_URL,
    reason="TEST_DATABASE_URL no configurada — se omiten los tests de integración MySQL.",
)


@pytest.fixture(scope="module")
def db():
    engine = create_engine(TEST_DATABASE_URL + "?charset=utf8mb4", future=True)
    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)
    SessionLocal = sessionmaker(bind=engine, expire_on_commit=False)
    session = SessionLocal()
    yield session
    session.close()
    Base.metadata.drop_all(engine)
    engine.dispose()


def test_full_roundtrip_source_match_odds(db):
    source = Source(
        name="Test API",
        base_url="https://example.com",
        type=SourceType.api,
        requires_auth=True,
    )
    db.add(source)
    db.commit()

    match = Match(
        source_id=source.id,
        sport=Sport.football,
        competition="Liga Test — Peñarol",  # acentos/utf8mb4
        home_team="Peñarol",
        away_team="Nacional",
        raw_data={"foo": "bar", "n": 1},
    )
    odds = Odds(
        match=match,
        source_id=source.id,
        home_win=Decimal("2.5000"),
        draw=Decimal("3.2000"),
        away_win=Decimal("2.8000"),
    )
    db.add(match)
    db.add(odds)
    db.commit()

    fetched = db.query(Match).filter(Match.id == match.id).one()
    assert fetched.home_team == "Peñarol"
    assert fetched.raw_data == {"foo": "bar", "n": 1}
    assert fetched.sport is Sport.football
    assert len(fetched.odds) == 1
    assert fetched.odds[0].home_win == Decimal("2.5000")


def test_scrape_session_status_enum(db):
    source = db.query(Source).first()
    log = ScrapeSession(source_id=source.id, status=SessionStatus.success, matches_found=3)
    db.add(log)
    db.commit()
    assert db.query(ScrapeSession).filter_by(id=log.id).one().status is SessionStatus.success
