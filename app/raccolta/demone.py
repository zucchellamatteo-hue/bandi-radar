"""Servizio di raccolta: ogni ora controlla le fonti in scadenza e porta avanti la catena dei bandi (smistamento,
deduplica, pagina ufficiale, allegati e, con la chiave API, l'IA con la Batch API: app/schede/ia.py, ciclo_catena);
una volta al giorno ricalcola lo stato dei bandi; il lunedi' mattina manda il riepilogo della settimana.
CATENA_AUTOMATICA=0 nel .env spegne la catena (resta solo la raccolta).
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
        if os.environ.get("CATENA_AUTOMATICA", "1") != "0":
            try:
                from app.schede.ia import ciclo_catena

                ciclo_catena()
            except Exception:  # noqa: BLE001
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
