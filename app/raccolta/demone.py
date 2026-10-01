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

from datetime import datetime, timezone

from app.notifiche.novita_settimana import invia_riepilogo
from app.raccolta.esegui import esegui

INTERVALLO_SECONDI = int(os.environ.get("RACCOLTA_INTERVALLO_SECONDI", "3600"))


def main() -> int:
    print(f"Raccolta avviata: controllo delle fonti in scadenza ogni {INTERVALLO_SECONDI} secondi.", flush=True)
    ultimo_stato = None
    # Ogni sistema registra inizio, fine ed esito (tabella esecuzioni, pagina Supervisione della plancia: app/sistemi.py).
    from app.sistemi import esecuzione

    while True:
        try:
            with esecuzione("raccolta") as e:
                inizio = datetime.now(timezone.utc)   # il database confronta in UTC (02/10: prima contava sempre 0)
                esegui()
                e.riepilogo = riepilogo_raccolta(inizio)
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

                with esecuzione("stato_bandi") as e, connetti() as conn:
                    cambiati = aggiorna_stati(conn)
                    e.riepilogo = f"{cambiati} bandi cambiati di stato"
                    print(f"Stati dei bandi ricalcolati: {cambiati} cambiati.", flush=True)
                ultimo_stato = adesso.date()
            except Exception:  # noqa: BLE001
                traceback.print_exc()
        if adesso.weekday() == 0 and adesso.hour >= 7 and not riepilogo_gia_inviato():   # lunedi', dalle 7, una volta sola
            try:
                with esecuzione("email_settimana") as e:
                    e.riepilogo = invia_riepilogo()
            except Exception:  # noqa: BLE001
                traceback.print_exc()
        time.sleep(INTERVALLO_SECONDI)


def riepilogo_raccolta(inizio: datetime) -> str:
    from app.db.connessione import connetti

    with connetti() as conn, conn.cursor() as cur:
        cur.execute("""SELECT count(*) AS controlli, count(*) FILTER (WHERE esito <> 'ok') AS errori,
                              coalesce(sum(novita), 0) AS novita FROM controlli WHERE iniziato_il >= %s""", (inizio,))
        r = cur.fetchone()
    return f"{r['controlli']} fonti controllate, {r['novita']} annunci nuovi, {r['errori']} errori"


def riepilogo_gia_inviato() -> bool:
    """Il riepilogo di questa settimana e' gia' partito? (cosi' l'esecuzione si registra una volta sola)."""
    from datetime import date

    from app.db.connessione import connetti

    chiave = date.today().isocalendar()
    with connetti() as conn, conn.cursor() as cur:
        cur.execute("SELECT 1 FROM notifiche_inviate WHERE nome = 'novita_settimana' AND chiave = %s",
                    (f"{chiave.year}-W{chiave.week:02d}",))
        return cur.fetchone() is not None


if __name__ == "__main__":
    sys.exit(main())
