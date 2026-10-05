"""Stampa i prossimi passi aperti (per le sessioni di Claude Code): python -m app.passi"""

import sys

from app import passi
from app.db.connessione import connetti

if __name__ == "__main__":
    with connetti() as conn:
        print(passi.testo(passi.elenco(conn, anche_fatti=False)))
    sys.exit(0)
