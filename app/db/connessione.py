"""Connessione a Postgres. I dati di accesso arrivano dalle variabili PG* dell'ambiente (docker-compose.yml)."""

from __future__ import annotations

import os

import psycopg
from psycopg.rows import dict_row


def connetti(autocommit: bool = False) -> psycopg.Connection:
    """Apre una connessione; le righe si leggono come dizionari (colonna -> valore)."""
    if not os.environ.get("PGHOST"):
        raise RuntimeError("PGHOST non impostata: servono le variabili PGHOST, PGUSER, PGPASSWORD, PGDATABASE.")
    return psycopg.connect(connect_timeout=5, autocommit=autocommit, row_factory=dict_row)
