"""Articoli del blog (per le sessioni di Claude Code).

    python -m app.articoli                      # elenco con stato, parole e collegamenti
    python -m app.articoli carica FILE.json     # carica articoli in BOZZA (FILE "-" = da stdin); salta gli slug gia' presenti

Il file e' una lista di oggetti con titolo, slug, sommario, corpo (Markdown), fonti [{nome, url}], bando_id o misura_id.
"""

import json
import sys

from app import articoli
from app.db.connessione import connetti
from app.db.migrazioni import applica_migrazioni

if __name__ == "__main__":
    with connetti() as conn:
        if len(sys.argv) >= 3 and sys.argv[1] == "carica":
            testo = sys.stdin.read() if sys.argv[2] == "-" else open(sys.argv[2], encoding="utf-8").read()
            applica_migrazioni(conn)
            chi = sys.argv[3] if len(sys.argv) > 3 else "Claude (sessione)"
            try:
                esiti = articoli.carica(conn, json.loads(testo), chi)
            except articoli.ErroreArticoli as e:
                conn.rollback()
                print("Errore, niente caricato:", e)
                sys.exit(1)
            conn.commit()
            for slug, esito in esiti:
                print(f"/blog/{slug}: {esito}")
        else:
            for a in articoli.elenco(conn):
                legame = (f" · bando n. {a['bando_id']}" if a["bando_id"] else "") + (f" · misura {a['misura_id']}" if a["misura_id"] else "")
                print(f"#{a['id']} [{a['stato']}] /blog/{a['slug']} · {articoli.parole(a['corpo'])} parole{legame}\n  {a['titolo']}")
    sys.exit(0)
