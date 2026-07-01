"""Autenticación JWT con rate limiting por IP.

- Un único usuario configurado en .env
- 5 intentos fallidos → suspensión 1 hora
- Token JWT con expiración de 12 horas
"""

from __future__ import annotations

import hashlib
from collections import defaultdict
from datetime import datetime, timedelta, timezone
from typing import Optional

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt

from config.settings import settings

# --- Rate limiter en memoria ---
# { ip: {"attempts": int, "locked_until": datetime | None} }
_rate_data: dict[str, dict] = defaultdict(lambda: {"attempts": 0, "locked_until": None})

MAX_ATTEMPTS = 5
LOCKOUT_MINUTES = 60
TOKEN_EXPIRE_HOURS = 12

_bearer = HTTPBearer()


def _check_password(password: str) -> bool:
    h = hashlib.sha256((settings.auth_salt + password).encode()).hexdigest()
    return h == settings.auth_hash


def rate_check(ip: str) -> None:
    """Lanza 429 si la IP está suspendida."""
    state = _rate_data[ip]
    if state["locked_until"] and datetime.now(timezone.utc) < state["locked_until"]:
        remaining = int((state["locked_until"] - datetime.now(timezone.utc)).total_seconds() / 60)
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"Cuenta suspendida. Intentá en {remaining} minutos.",
        )
    # Si el bloqueo expiró, resetear
    if state["locked_until"] and datetime.now(timezone.utc) >= state["locked_until"]:
        state["attempts"] = 0
        state["locked_until"] = None


def register_failed(ip: str) -> None:
    state = _rate_data[ip]
    state["attempts"] += 1
    if state["attempts"] >= MAX_ATTEMPTS:
        state["locked_until"] = datetime.now(timezone.utc) + timedelta(minutes=LOCKOUT_MINUTES)


def register_success(ip: str) -> None:
    _rate_data[ip] = {"attempts": 0, "locked_until": None}


def create_token(email: str) -> str:
    expire = datetime.now(timezone.utc) + timedelta(hours=TOKEN_EXPIRE_HOURS)
    return jwt.encode(
        {"sub": email, "exp": expire},
        settings.jwt_secret,
        algorithm="HS256",
    )


def login(email: str, password: str, ip: str) -> str:
    """Valida credenciales y devuelve JWT. Lanza HTTPException si falla."""
    rate_check(ip)

    if email != settings.auth_user or not _check_password(password):
        register_failed(ip)
        state = _rate_data[ip]
        remaining = MAX_ATTEMPTS - state["attempts"]
        if remaining > 0:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=f"Credenciales incorrectas. Intentos restantes: {remaining}.",
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=f"Demasiados intentos. Cuenta suspendida por {LOCKOUT_MINUTES} minutos.",
            )

    register_success(ip)
    return create_token(email)


def require_auth(credentials: HTTPAuthorizationCredentials = Depends(_bearer)) -> str:
    """Dependencia FastAPI: valida el Bearer token en cada request protegido."""
    try:
        payload = jwt.decode(credentials.credentials, settings.jwt_secret, algorithms=["HS256"])
        email: Optional[str] = payload.get("sub")
        if not email:
            raise ValueError
        return email
    except (JWTError, ValueError):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token inválido o expirado.",
            headers={"WWW-Authenticate": "Bearer"},
        )
