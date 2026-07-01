"""Cifrado simétrico de credenciales (Fernet) para la capa de aplicación.

Las credenciales de las fuentes (p. ej. la API key del piloto, o usuario/clave de
sitios privados en fases futuras) se guardan cifradas en la columna JSON
``sources.credentials`` — nunca en plain text.

    enc = encrypt_credentials({"api_key": "..."})   # -> str cifrado
    dec = decrypt_credentials(enc)                   # -> {"api_key": "..."}
"""

import json
from typing import Any

from cryptography.fernet import Fernet

from config.settings import settings


def _fernet() -> Fernet:
    if not settings.fernet_key:
        raise RuntimeError(
            "FERNET_KEY no configurada. Generar con: "
            'python -c "from cryptography.fernet import Fernet; '
            'print(Fernet.generate_key().decode())"'
        )
    return Fernet(settings.fernet_key.encode())


def encrypt_credentials(data: dict[str, Any]) -> str:
    """Serializa un dict a JSON y lo cifra. Devuelve un token Fernet (str)."""
    token = _fernet().encrypt(json.dumps(data).encode())
    return token.decode()


def decrypt_credentials(token: str) -> dict[str, Any]:
    """Descifra un token Fernet y devuelve el dict original."""
    raw = _fernet().decrypt(token.encode())
    return json.loads(raw.decode())
