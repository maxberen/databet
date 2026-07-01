# databet — Sistema de scraping de odds (Fase 1: Fundación)

Stack: **MySQL 8 · SQLAlchemy 2.0 (sync) · Alembic · httpx · Streamlit**.

La Fase 1 valida el modelo de datos end-to-end usando **The Odds API** (REST) como
fuente piloto, antes de invertir en la capa anti-bot (Playwright, stealth, proxies,
captcha) que recién hace falta para fuentes privadas en fases posteriores.

## Estructura

```
config/        settings (.env), engine MySQL, cifrado de credenciales
models/        modelos ORM (sources, source_protocols, matches, odds, scrape_sessions)
normalizer/    raw event (The Odds API) → Match + Odds (función pura)
agents/        BaseAgent + TheOddsApiAgent (piloto)
admin/ui/      panel Streamlit (CRUD fuentes, ejecutar piloto, ver datos)
scripts/       run_pilot.py (entry point CLI)
alembic/       migraciones MySQL
tests/         test_normalizer (sin DB) + test_models (integración MySQL)
core/, scheduler/   placeholders para Fases 2–3 (anti-bot, Celery)
```

## Setup

1. **Dependencias** (Poetry o pip):
   ```bash
   poetry install            # o: pip install -e .
   ```

2. **Infra** — MySQL 8 + (más adelante) Redis. Crear la base con utf8mb4:
   ```sql
   CREATE DATABASE betting_system CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
   ```

3. **Entorno** — copiar `.env.example` a `.env` y completar:
   ```bash
   cp .env.example .env
   # DATABASE_URL, ODDS_API_KEY (free en the-odds-api.com), FERNET_KEY
   python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
   ```

4. **Migraciones**:
   ```bash
   alembic upgrade head
   ```

## Ejecutar

```bash
# Piloto por CLI
python -m scripts.run_pilot

# Panel admin
streamlit run admin/ui/streamlit_app.py
```

## Tests

```bash
pytest                                   # tests del normalizer (sin DB)

# Integración contra MySQL (base desechable):
TEST_DATABASE_URL=mysql+pymysql://user:pass@127.0.0.1:3306/betting_system_test pytest
```

## Notas

- **The Odds API y tenis:** el free tier garantiza soccer; el tenis puede no estar
  disponible según el plan. El modelo soporta ambos; agregar la `sport_key` de tenis
  en `agents/sources/the_odds_api.py:DEFAULT_SPORT_KEYS` cuando esté disponible.
- **Credenciales** se guardan cifradas (Fernet) en `sources.credentials`, nunca en
  plain text.
- Fases siguientes: HumanBehaviorEngine + proxies + captcha (Fase 2), Celery + dashboard
  (Fase 3). Las carpetas `core/` y `scheduler/` ya están reservadas.
