"""Engine y session factory de SQLAlchemy (sync) para MySQL.

El pool_pre_ping es crítico en MySQL: el servidor cierra conexiones idle tras
``wait_timeout`` (8h por defecto). pool_pre_ping verifica la conexión antes de
usarla y pool_recycle la recicla preventivamente.
"""

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from config.settings import settings


def _with_charset(url: str) -> str:
    """Garantiza ?charset=utf8mb4 en la URL de conexión."""
    if "charset=" in url:
        return url
    sep = "&" if "?" in url else "?"
    return f"{url}{sep}charset=utf8mb4"


engine = create_engine(
    _with_charset(settings.database_url),
    pool_size=10,
    max_overflow=20,
    pool_recycle=3600,    # recicla conexiones antes del wait_timeout de MySQL
    pool_pre_ping=True,   # verifica la conexión antes de usarla
    future=True,
)

SessionLocal = sessionmaker(
    bind=engine,
    autoflush=False,
    autocommit=False,
    expire_on_commit=False,
    class_=Session,
)
