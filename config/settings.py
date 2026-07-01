"""Configuración central leída desde el entorno (.env).

Usa pydantic-settings para validar y tipar las variables. Importar el singleton
``settings`` desde cualquier módulo:

    from config.settings import settings
    settings.database_url
"""

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # Base de datos
    database_url: str

    # The Odds API (fuente piloto)
    odds_api_key: str = ""
    odds_api_base_url: str = "https://api.the-odds-api.com"

    # Cifrado de credenciales en capa app
    fernet_key: str = ""

    # Zona horaria local (offset en horas respecto a UTC, ej. -4)
    timezone_offset: int = -4

    # Auth
    auth_user: str = ""
    auth_salt: str = ""
    auth_hash: str = ""
    jwt_secret: str = ""


@lru_cache
def get_settings() -> Settings:
    """Devuelve el singleton de settings (cacheado)."""
    return Settings()


settings = get_settings()
