# databet — contexto para Claude

## Qué es esto

Sistema de scraping de odds deportivas con frontend React y dos backends:
- **Desarrollo**: FastAPI + Uvicorn en `localhost:8000`
- **Producción**: PHP en `https://databet.upload.com.py`

## Comandos frecuentes

```bash
# Scrapers
python3 -m scripts.run_pilot          # The Odds API
python3 -m scripts.run_apostala       # ApostaLA (Kambi)

# Backend local
python3 -m uvicorn api.main:app --reload --port 8000

# Frontend local
cd frontend && npm run dev

# Build producción
echo 'VITE_API_URL=https://databet.upload.com.py' > frontend/.env.production
node frontend/node_modules/vite/bin/vite.js build

# Deploy frontend al servidor
scp -r frontend/dist/* uploadf@databet.upload.com.py:/home/uploadf/public_html/databet.upload.com.py/

# Deploy PHP al servidor
ssh uploadf@databet.upload.com.py "cd /home/uploadf/public_html/databet.upload.com.py && git pull origin main && cp php-api/_auth.php php-api/.htaccess php-api/login.php php-api/matches.php php-api/odds.php php-api/health.php ."
```

## Servidor de producción

- **Host**: databet.upload.com.py (cPanel, uploadf)
- **Directorio**: `/home/uploadf/public_html/databet.upload.com.py`
- **Python**: `python3.9` (no `python3` que es 3.6)
- **DB**: `uploadf_databet` / usuario `uploadf_databet`
- **Log crons**: `/home/uploadf/databet_cron.log`

## Base de datos

- Local: `bets` en MySQL 127.0.0.1
- Producción: `uploadf_databet` en MySQL 127.0.0.1 del servidor
- Migraciones: `alembic upgrade head` (requiere Python 3.9+ en el servidor)
- Si alembic falla por versión Python, crear tablas con el SQL en README.md

## Arquitectura de datos

- `sources` → fuentes (The Odds API, ApostaLA)
- `matches` → partidos scrapeados (puede haber duplicados por re-scrape)
- `odds` → cuotas por bookmaker
- `rate_limits` → bloqueos de IP para auth (PHP lo crea automáticamente)

## Decisiones importantes

- **PHP para producción**: cPanel no soporta Python moderno ni procesos persistentes. La API PHP replica exactamente los 3 endpoints de FastAPI.
- **JWT manual en PHP**: sin composer, implementación HS256 propia en `php-api/_jwt.php`.
- **Authorization header en Apache**: requiere `RewriteRule .* - [E=HTTP_AUTHORIZATION:%{HTTP:Authorization}]` en `.htaccess`.
- **Timezone**: datetimes guardados en UTC, convertidos con `TIMEZONE_OFFSET` (default -4) en cada response. El filtro de fecha usa rango UTC, no `DATE()`.
- **Deduplicación**: `MAX(id)` por `(home, away, datetime, source_id)` → evita duplicados por re-scrape.
- **SHA-256 para passwords**: `hash('sha256', salt + password)`. No bcrypt (incompatibilidad passlib v5).

## Auth

- Usuario: configurado en `.env` como `AUTH_USER`
- Password hash: `SHA-256(AUTH_SALT + password)`
- JWT: HS256, 12h de expiración, secret en `JWT_SECRET`
- Rate limit: 5 intentos → 1h bloqueo por IP

## Frontend

- `frontend/src/api.js`: usa `VITE_API_URL` env var para la URL del backend
- Sin `VITE_API_URL` → fallback a `http://localhost:8000`
- Para producción crear `frontend/.env.production` antes de buildear
