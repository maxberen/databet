"""Admin UI (Streamlit) — Fase 1.

CRUD de fuentes + vistas read-only de matches/odds/sesiones + botón para ejecutar
el piloto. Lanzar con:

    streamlit run admin/ui/streamlit_app.py
"""

from __future__ import annotations

import sys
from pathlib import Path

# Permite ejecutar desde la raíz del repo sin instalar el paquete.
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

import pandas as pd
import streamlit as st

from agents.sources.the_odds_api import TheOddsApiAgent
from config.database import SessionLocal
from models.match import Match
from models.odds import Odds
from models.scrape_session import ScrapeSession
from models.source import Source, SourceType

st.set_page_config(page_title="databet — Admin", layout="wide")
st.title("databet — Panel de administración")


def get_db():
    return SessionLocal()


# --- Sección: Fuentes ------------------------------------------------------
st.header("Fuentes")

with get_db() as db:
    sources = db.query(Source).order_by(Source.id).all()
    rows = [
        {
            "id": s.id,
            "name": s.name,
            "type": s.type.value,
            "base_url": s.base_url,
            "is_active": bool(s.is_active),
            "requires_auth": bool(s.requires_auth),
        }
        for s in sources
    ]
if rows:
    st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)
else:
    st.info("No hay fuentes cargadas todavía.")

with st.expander("➕ Crear / actualizar fuente"):
    with st.form("source_form", clear_on_submit=False):
        name = st.text_input("Nombre", value="The Odds API")
        base_url = st.text_input("Base URL", value="https://api.the-odds-api.com")
        type_ = st.selectbox("Tipo", [t.value for t in SourceType], index=0)
        is_active = st.checkbox("Activa", value=True)
        requires_auth = st.checkbox("Requiere auth", value=True)
        submitted = st.form_submit_button("Guardar")
    if submitted:
        with get_db() as db:
            source = db.query(Source).filter(Source.name == name).first()
            if source is None:
                source = Source(name=name)
                db.add(source)
            source.base_url = base_url
            source.type = SourceType(type_)
            source.is_active = is_active
            source.requires_auth = requires_auth
            db.commit()
        st.success(f"Fuente '{name}' guardada.")
        st.rerun()

# --- Sección: ejecutar piloto ---------------------------------------------
st.header("Ejecutar piloto (The Odds API)")
if st.button("▶️ Ejecutar piloto ahora"):
    with get_db() as db:
        source = db.query(Source).filter(Source.type == SourceType.api).first()
        if source is None:
            st.error("No hay ninguna fuente de tipo 'api'. Creá una primero.")
        else:
            with st.spinner("Scrapeando..."):
                result = TheOddsApiAgent(source, db).run()
            if result.status.value == "success":
                st.success(f"OK — {result.matches_found} matches en sesión #{result.id}")
            else:
                st.error(f"Falló: {result.error_message}")

# --- Sección: matches + odds ----------------------------------------------
st.header("Últimos matches")
with get_db() as db:
    matches = db.query(Match).order_by(Match.scraped_at.desc()).limit(50).all()
    match_rows = [
        {
            "id": m.id,
            "sport": m.sport.value,
            "competition": m.competition,
            "home": m.home_team,
            "away": m.away_team,
            "datetime": m.match_datetime,
            "n_odds": len(m.odds),
        }
        for m in matches
    ]
st.dataframe(pd.DataFrame(match_rows), use_container_width=True, hide_index=True)

st.header("Últimas odds")
with get_db() as db:
    odds = db.query(Odds).order_by(Odds.id.desc()).limit(100).all()
    odds_rows = [
        {
            "match_id": o.match_id,
            "bookmaker": o.bookmaker,
            "home_win": float(o.home_win) if o.home_win is not None else None,
            "draw": float(o.draw) if o.draw is not None else None,
            "away_win": float(o.away_win) if o.away_win is not None else None,
            "p1": float(o.player1_win) if o.player1_win is not None else None,
            "p2": float(o.player2_win) if o.player2_win is not None else None,
        }
        for o in odds
    ]
st.dataframe(pd.DataFrame(odds_rows), use_container_width=True, hide_index=True)

# --- Sección: sesiones -----------------------------------------------------
st.header("Sesiones de scraping")
with get_db() as db:
    sessions = db.query(ScrapeSession).order_by(ScrapeSession.id.desc()).limit(30).all()
    session_rows = [
        {
            "id": s.id,
            "source_id": s.source_id,
            "status": s.status.value,
            "matches": s.matches_found,
            "started": s.started_at,
            "ended": s.ended_at,
            "error": s.error_message,
        }
        for s in sessions
    ]
st.dataframe(pd.DataFrame(session_rows), use_container_width=True, hide_index=True)
