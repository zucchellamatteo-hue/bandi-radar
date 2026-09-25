"""Servizio di raccolta: ogni ora controlla le fonti in scadenza; una volta al giorno ricalcola lo stato dei bandi;
il lunedi' mattina manda il riepilogo della settimana.
Gira come container 'raccolta' in Docker Compose."""

from __future__ import annotations

import os
import sys
import time
import traceback

from datetime import datetime

from app.notifiche.novita_settimana import invia_riepilogo
from app.raccolta.esegui import esegui

INTERVALLO_SECONDI = int(os.environ.get("RACCOLTA_INTERVALLO_SECONDI", "3600"))


def main() -> int:
    print(f"Raccolta avviata: controllo delle fonti in scadenza ogni {INTERVALLO_SECONDI} secondi.", flush=True)
    ultimo_stato = None
    while True:
        try:
            esegui()
        except Exception:  # noqa: BLE001 - il servizio non deve morire per un errore di un giro
            traceback.print_exc()
        adesso = datetime.now()
        if adesso.date() != ultimo_stato:   # una volta al giorno: stato dei bandi (aperto, chiuso, in arrivo) dalle date
            try:
                from app.db.connessione import connetti
                from app.schede.stato import aggiorna_stati

                with connetti() as conn:
                    print(f"Stati dei bandi ricalcolati: {aggiorna_stati(conn)} cambiati.", flush=True)
                ultimo_stato = adesso.date()
            except Exception:  # noqa: BLE001
                traceback.print_exc()
        if adesso.weekday() == 0 and adesso.hour >= 7:   # lunedi', dalle 7: invia una volta sola (controllo nel database)
            try:
                invia_riepilogo()
            except Exception:  # noqa: BLE001
                traceback.print_exc()
        time.sleep(INTERVALLO_SECONDI)


if __name__ == "__main__":
    sys.exit(main())
