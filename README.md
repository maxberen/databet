# databet

Plataforma de scraping y análisis de odds deportivas. Agrega probabilidades de múltiples fuentes para fútbol y tenis.

## Stack

| Capa | Tecnología |
|---|---|
| Scraping | Python 3.9 + httpx |
| Base de datos | MySQL 8 + SQLAlchemy + Alembic |
| API backend (local) | FastAPI + Uvicorn |
| API backend (producción) | PHP sin dependencias externas |
| Frontend | React + Vite + TanStack Query |

## Fuentes de odds

- **The Odds API** — REST API (key requerida, free tier 500 req/mes). Ligas europeas y sudamericanas.
- **ApostaLA** — Kambi public API. Fútbol y tenis latinoamericano.

## Estructura

```
agents/sources/     scrapers (the_odds_api.py, apostala.py)
api/                FastAPI backend (desarrollo local)
php-api/            API PHP para producción en cPanel
frontend/           React + Vite SPA
config/             settings (.env), conexión MySQL
models/             ORM: sources, matches, odds
scripts/            run_pilot.py, run_apostala.py
alembic/            migraciones MySQL
```

## Desarrollo local

### Requisitos
- Python 3.11+
- Node 18+
- MySQL 8

### Setup

```bash
# 1. Dependencias Python
pip install fastapi uvicorn sqlalchemy pymysql alembic pydantic pydantic-settings httpx python-jose python-dotenv

# 2. Variables de entorno
cp .env.example .env   # completar DATABASE_URL, ODDS_API_KEY, AUTH_*, JWT_SECRET

# 3. Migraciones
alembic upgrade head

# 4. Dependencias frontend
cd frontend && npm install
```

### Correr scrapers

```bash
python3 -m scripts.run_pilot
python3 -m scripts.run_apostala
```

### Iniciar servidores

```bash
# Backend (puerto 8000)
python3 -m uvicorn api.main:app --reload --port 8000

# Frontend (puerto 5173)
cd frontend && npm run dev
```

Accedé en `http://localhost:5173`

## Producción (cPanel)

- **URL**: https://databet.upload.com.py
- **Backend**: `php-api/` copiado a la raíz del subdominio
- **Frontend**: `frontend/dist/` buildado con `VITE_API_URL=https://databet.upload.com.py`
- **Base de datos**: MySQL en el servidor — `uploadf_databet`
- **Scrapers**: cron jobs con `python3.9`

### Deploy — actualizar servidor

```bash
# En el servidor
cd /home/uploadf/public_html/databet.upload.com.py
git pull origin main
cp php-api/_auth.php php-api/.htaccess php-api/login.php php-api/matches.php php-api/odds.php php-api/health.php .

# En local — rebuild frontend
echo 'VITE_API_URL=https://databet.upload.com.py' > frontend/.env.production
node frontend/node_modules/vite/bin/vite.js build
scp -r frontend/dist/* uploadf@databet.upload.com.py:/home/uploadf/public_html/databet.upload.com.py/
```

### Crons en producción

```
0 6 * * * cd /home/uploadf/public_html/databet.upload.com.py && python3.9 -m scripts.run_apostala >> /home/uploadf/databet_cron.log 2>&1
0 7 * * * cd /home/uploadf/public_html/databet.upload.com.py && python3.9 -m scripts.run_pilot >> /home/uploadf/databet_cron.log 2>&1
```

## Variables de entorno (.env)

```env
DATABASE_URL=mysql+pymysql://user:pass@127.0.0.1:3306/dbname
ODDS_API_KEY=...
TIMEZONE_OFFSET=-4
AUTH_USER=...
AUTH_SALT=...
AUTH_HASH=...
JWT_SECRET=...
```

## Autenticación

Usuario único configurado en `.env`. JWT HS256, expiración 12 horas. Rate limiting: 5 intentos fallidos → bloqueo 1 hora por IP (almacenado en tabla `rate_limits`).

## Endpoints API

```
POST /api/auth/login              → JWT token
GET  /api/matches/today?day=YYYY-MM-DD  → lista de partidos con odds agregadas
GET  /api/matches/{id}/odds       → detalle por bookmaker
GET  /api/health                  → health check
```

## Notas

- Los datetimes se almacenan en UTC y se convierten al offset configurado (`TIMEZONE_OFFSET`) en cada respuesta.
- La deduplicación usa el `MAX(id)` por `(home_team, away_team, match_datetime, source_id)` para mostrar siempre el scrape más reciente.
- El filtro de fecha usa rango UTC equivalente a la fecha local pedida, no `DATE()` directo.
