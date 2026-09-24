"""Migrazioni dello schema: file SQL numerati in app/db/migrazioni/, applicati una volta sola, in ordine.

Uso: python -m app.db.migrazioni
Viene lanciato all'avvio dei servizi (docker-compose.yml), cosi' il database e' sempre allineato al codice.
"""

from __future__ import annotations

import sys
from pathlib import Path

from app.db.connessione import connetti

CARTELLA = Path(__file__).resolve().parent / "migrazioni"


def applica_migrazioni(conn) -> list[str]:
    """Applica le migrazioni mancanti e ritorna i nomi di quelle applicate adesso."""
    applicate: list[str] = []
    with conn.cursor() as cur:
        cur.execute(
            "CREATE TABLE IF NOT EXISTS schema_migrazioni ("
            " nome text PRIMARY KEY, applicata_il timestamptz NOT NULL DEFAULT now())"
        )
        cur.execute("SELECT nome FROM schema_migrazioni")
        gia_fatte = {r["nome"] for r in cur.fetchall()}
        for percorso in sorted(CARTELLA.glob("*.sql")):
            if percorso.name in gia_fatte:
                continue
            cur.execute(percorso.read_text(encoding="utf-8"))
            cur.execute("INSERT INTO schema_migrazioni (nome) VALUES (%s)", (percorso.name,))
            applicate.append(percorso.name)
    conn.commit()
    return applicate


def main() -> int:
    with connetti() as conn:
        applicate = applica_migrazioni(conn)
    if applicate:
        print("Migrazioni applicate: " + ", ".join(applicate))
    else:
        print("Schema gia' aggiornato.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
