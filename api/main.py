"""FastAPI — API REST de databet.

Endpoints:
  GET /api/matches/today          → partidos del día con min/max odds agregadas
  GET /api/matches/{id}/odds      → detalle de odds por fuente para un partido
"""

from __future__ import annotations

from datetime import date, datetime, timedelta, timezone
from decimal import Decimal
from typing import Optional

from fastapi import Depends, FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from sqlalchemy import func

from api.auth import login, require_auth
from config.database import SessionLocal
from config.settings import settings
from models.match import Match, Sport
from models.odds import Odds
from models.source import Source

_LOCAL_OFFSET = timedelta(hours=settings.timezone_offset)


def _to_local(dt: datetime) -> datetime:
    """Convierte datetime UTC naive a hora local configurada (naive)."""
    return dt + _LOCAL_OFFSET

app = FastAPI(title="databet API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


# ---------- Schemas ----------------------------------------------------------

class LoginRequest(BaseModel):
    email: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class OddsRange(BaseModel):
    min: Optional[float]
    max: Optional[float]


class MatchSummary(BaseModel):
    id: int
    sport: str
    competition: str
    home_team: str
    away_team: str
    match_datetime: datetime
    sources_count: int
    home_win: OddsRange
    draw: Optional[OddsRange]
    away_win: OddsRange
    player1_win: Optional[OddsRange]
    player2_win: Optional[OddsRange]


class OddsDetail(BaseModel):
    source: str
    bookmaker: str
    home_win: Optional[float]
    draw: Optional[float]
    away_win: Optional[float]
    player1_win: Optional[float]
    player2_win: Optional[float]
    scraped_at: datetime


class MatchDetail(BaseModel):
    id: int
    sport: str
    competition: str
    home_team: str
    away_team: str
    match_datetime: datetime
    odds: list[OddsDetail]


# ---------- Helpers ----------------------------------------------------------

def _f(v: Decimal | None) -> float | None:
    return float(v) if v is not None else None


# ---------- Endpoints --------------------------------------------------------

@app.post("/api/auth/login", response_model=TokenResponse)
def do_login(body: LoginRequest, request: Request):
    token = login(body.email, body.password, request.client.host)
    return TokenResponse(access_token=token)


@app.get("/api/matches/today", response_model=list[MatchSummary])
def matches_today(day: Optional[str] = None, _: str = Depends(require_auth)):
    """
    Partidos del día con min/max odds de todas las fuentes.
    Deduplica: por cada (partido real, source) usa solo el scrape más reciente.
    Parámetro opcional ?day=YYYY-MM-DD para consultar otra fecha.
    """
    # Convertimos la fecha local pedida a un rango UTC.
    # Ej: fecha local 2026-06-30, offset=-4 → UTC [2026-06-30 04:00, 2026-07-01 04:00)
    if day:
        local_day = date.fromisoformat(day)
    else:
        # "hoy" según la hora local configurada
        local_now = datetime.now(timezone.utc) + _LOCAL_OFFSET
        local_day = local_now.date()

    utc_start = datetime(local_day.year, local_day.month, local_day.day) - _LOCAL_OFFSET
    utc_end = utc_start + timedelta(days=1)

    db = SessionLocal()
    try:
        # Subquery: match_id más reciente por (home, away, match_datetime, source_id)
        latest_per_source = (
            db.query(
                func.max(Match.id).label("match_id"),
            )
            .filter(Match.match_datetime >= utc_start, Match.match_datetime < utc_end)
            .group_by(
                Match.home_team,
                Match.away_team,
                Match.match_datetime,
                Match.source_id,
            )
            .subquery()
        )

        latest_ids = db.query(latest_per_source.c.match_id).scalar_subquery()

        rows = (
            db.query(
                Match.home_team,
                Match.away_team,
                Match.match_datetime,
                Match.sport,
                # Tomamos competencia y id del match más reciente de cualquier fuente
                func.max(Match.id).label("id"),
                func.max(Match.competition).label("competition"),
                func.count(func.distinct(Odds.bookmaker)).label("sources_count"),
                func.min(Odds.home_win).label("min_hw"),
                func.max(Odds.home_win).label("max_hw"),
                func.min(Odds.draw).label("min_draw"),
                func.max(Odds.draw).label("max_draw"),
                func.min(Odds.away_win).label("min_aw"),
                func.max(Odds.away_win).label("max_aw"),
                func.min(Odds.player1_win).label("min_p1"),
                func.max(Odds.player1_win).label("max_p1"),
                func.min(Odds.player2_win).label("min_p2"),
                func.max(Odds.player2_win).label("max_p2"),
            )
            .join(Odds, Odds.match_id == Match.id)
            .filter(Match.id.in_(latest_ids))
            .group_by(
                Match.home_team,
                Match.away_team,
                Match.match_datetime,
                Match.sport,
            )
            .order_by(Match.match_datetime)
            .all()
        )

        result = []
        for r in rows:
            is_tennis = r.sport == Sport.tennis
            result.append(MatchSummary(
                id=r.id,
                sport=r.sport.value,
                competition=r.competition,
                home_team=r.home_team,
                away_team=r.away_team,
                match_datetime=_to_local(r.match_datetime),
                sources_count=r.sources_count,
                home_win=OddsRange(min=_f(r.min_hw), max=_f(r.max_hw)),
                draw=OddsRange(min=_f(r.min_draw), max=_f(r.max_draw)) if not is_tennis else None,
                away_win=OddsRange(min=_f(r.min_aw), max=_f(r.max_aw)),
                player1_win=OddsRange(min=_f(r.min_p1), max=_f(r.max_p1)) if is_tennis else None,
                player2_win=OddsRange(min=_f(r.min_p2), max=_f(r.max_p2)) if is_tennis else None,
            ))
        return result
    finally:
        db.close()


@app.get("/api/matches/{match_id}/odds", response_model=MatchDetail)
def match_odds(match_id: int, _: str = Depends(require_auth)):
    """Detalle de odds por fuente para un partido. Usa el scrape más reciente por source."""
    db = SessionLocal()
    try:
        match = db.query(Match).filter(Match.id == match_id).first()
        if not match:
            raise HTTPException(status_code=404, detail="Partido no encontrado")

        # Todos los match_ids que representan el mismo partido real
        same_matches = (
            db.query(Match.id)
            .filter(
                Match.home_team == match.home_team,
                Match.away_team == match.away_team,
                Match.match_datetime == match.match_datetime,
            )
            .subquery()
        )

        # Por cada source, solo el match_id más reciente
        latest_per_source = (
            db.query(func.max(Match.id).label("match_id"))
            .filter(Match.id.in_(same_matches))
            .group_by(Match.source_id)
            .subquery()
        )

        rows = (
            db.query(Odds, Source.name)
            .join(Source, Source.id == Odds.source_id)
            .filter(Odds.match_id.in_(db.query(latest_per_source.c.match_id)))
            .order_by(Source.name, Odds.bookmaker)
            .all()
        )

        odds_list = [
            OddsDetail(
                source=source_name,
                bookmaker=o.bookmaker,
                home_win=_f(o.home_win),
                draw=_f(o.draw),
                away_win=_f(o.away_win),
                player1_win=_f(o.player1_win),
                player2_win=_f(o.player2_win),
                scraped_at=_to_local(o.scraped_at),
            )
            for o, source_name in rows
        ]

        return MatchDetail(
            id=match.id,
            sport=match.sport.value,
            competition=match.competition,
            home_team=match.home_team,
            away_team=match.away_team,
            match_datetime=_to_local(match.match_datetime),
            odds=odds_list,
        )
    finally:
        db.close()


@app.get("/api/health")
def health():
    return {"status": "ok", "time": datetime.now(timezone.utc).isoformat()}
