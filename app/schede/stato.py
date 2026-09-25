"""Stato dei bandi (aperto, chiuso, in arrivo) calcolato dal sistema ogni giorno, dalle date della scheda.

L'IA estrae solo date e fatti (apertura, scadenza, "chiuso per esaurimento fondi" in `chiuso_il`); lo stato non lo
scrive lei, perche' la mattina dopo potrebbe gia' essere vecchio. Gira da solo una volta al giorno nel servizio
di raccolta (app/raccolta/demone.py); a mano:

  python -m app.schede.stato
"""

from __future__ import annotations

import sys
from datetime import date

from app.schede.campi import calcola_stato


def aggiorna_stati(conn, oggi: date | None = None) -> int:
    """Ricalcola lo stato di tutti i bandi; ritorna quanti sono cambiati. Il cambio resta nello storico delle versioni."""
    oggi = oggi or date.today()
    cambiati = 0
    with conn.cursor() as cur:
        cur.execute("SELECT id, data_apertura, scadenza, chiuso_il, stato FROM bandi")
        for b in cur.fetchall():
            nuovo = calcola_stato(b["data_apertura"], b["scadenza"], oggi, b["chiuso_il"])
            if nuovo != b["stato"]:
                cur.execute("SELECT set_config('bandi_radar.causa', %s, true)", (f"stato ricalcolato il {oggi.isoformat()}",))
                cur.execute("UPDATE bandi SET stato = %s, stato_calcolato_il = %s WHERE id = %s", (nuovo, oggi, b["id"]))
                cambiati += 1
    conn.commit()
    return cambiati


def main() -> int:
    from app.db.connessione import connetti
    from app.db.migrazioni import applica_migrazioni

    with connetti() as conn:
        applica_migrazioni(conn)
        print(f"Stati dei bandi cambiati oggi: {aggiorna_stati(conn)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
