"""Declarative base común a todos los modelos.

Defaults de tabla a nivel MySQL: InnoDB + utf8mb4 para soportar caracteres
especiales en nombres de equipos/jugadores.

Los modelos sin índices propios heredan ``__table_args__`` por atributo. Los que
declaran índices deben usar la forma de tupla y agregar ``MYSQL_TABLE_KWARGS``
como último elemento, p. ej.::

    __table_args__ = (Index(...), MYSQL_TABLE_KWARGS)
"""

from sqlalchemy.orm import DeclarativeBase

# Kwargs de creación de tabla MySQL, reutilizables en modelos con índices.
MYSQL_TABLE_KWARGS = {
    "mysql_engine": "InnoDB",
    "mysql_charset": "utf8mb4",
    "mysql_collate": "utf8mb4_unicode_ci",
}


class Base(DeclarativeBase):
    __table_args__ = MYSQL_TABLE_KWARGS
