"""Servizio di raccolta: ogni ora controlla le fonti in scadenza e porta avanti la catena dei bandi (smistamento,
deduplica, pagina ufficiale, allegati e, con la chiave API, l'IA con la Batch API: app/schede/ia.py, ciclo_catena);
una volta al giorno ricalcola lo stato dei bandi; ogni mattina dalle 7 manda a Matteo il rapporto SEO/GEO
(app/notifiche/rapporto_seo.py, RAPPORTO_SEO: giornaliero, settimanale o spento); il lunedi' mattina manda il riepilogo
della settimana e prepara le email per le imprese (app/notifiche/email_imprese.py).
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
        try:                                            # rapporto SEO/GEO: ogni giorno (o il lunedi') dalle 7, una volta sola
            from app.notifiche import rapporto_seo

            if rapporto_seo.da_inviare(adesso) and not rapporto_seo.gia_inviato_adesso(adesso.date()):
                with esecuzione("rapporto_seo") as e:
                    e.riepilogo = rapporto_seo.invia_rapporto(oggi=adesso.date())
        except Exception:  # noqa: BLE001
            traceback.print_exc()
        if adesso.weekday() == 0 and adesso.hour >= 7:   # poi le email per le imprese, anche loro una volta sola
            try:
                email_imprese_della_settimana()
            except Exception:  # noqa: BLE001 - un errore qui non deve fermare la raccolta
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


def email_imprese_della_settimana() -> str | None:
    """Prepara le email settimanali per le imprese (una volta a settimana, registrata in notifiche_inviate) e avvisa
    Matteo se ce ne sono da approvare. Ritorna il riepilogo, o None se questa settimana e' gia' stato fatto."""
    from datetime import date

    from app import utenti
    from app.db.connessione import connetti
    from app.notifiche.email_imprese import prepara, settimana_iso
    from app.notifiche.novita_settimana import gia_inviato, registra_invio

    settimana = settimana_iso(date.today())
    with connetti() as conn:
        if gia_inviato(conn, "email_imprese", settimana):
            return None
        conteggi = prepara(conn)
        with conn.cursor() as cur:
            cur.execute("SELECT count(*) AS n FROM email_imprese WHERE stato = 'da_approvare'")
            da_approvare = cur.fetchone()["n"]
        avviso = ""
        destinatario = os.environ.get("EMAIL_MATTEO")
        if da_approvare and destinatario:
            avviso = "; avviso a Matteo: " + utenti.manda(
                destinatario, f"bandinQiaro: {da_approvare} email per le imprese da approvare",
                f"{da_approvare} email per le imprese da approvare: {utenti.sito_url()}/imprese\n")
        riepilogo = (f"{conteggi['create']} email preparate per {conteggi['imprese']} imprese, "
                     f"{da_approvare} da approvare{avviso}")
        registra_invio(conn, "email_imprese", settimana, riepilogo[:500])
    print(f"Email imprese {settimana}: {riepilogo}", flush=True)
    return riepilogo


if __name__ == "__main__":
    sys.exit(main())
