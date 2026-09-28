"""Esegue la raccolta: allinea la tabella fonti al registro, sceglie le fonti da controllare, le legge e salva.

Uso:
  python -m app.raccolta.esegui                 # tutte le fonti "in scadenza" secondo la loro frequenza
  python -m app.raccolta.esegui --fonte ID      # una sola fonte, subito
  python -m app.raccolta.esegui --tutte         # tutte, anche se non in scadenza
  python -m app.raccolta.esegui --prova ID      # legge una fonte e stampa gli annunci, senza database
  python -m app.raccolta.esegui --scorta ID     # legge subito tutta la scorta di una fonte (vedi app/raccolta/scorta.py)
  python -m app.raccolta.esegui --prova ID --scorta   # la scorta, senza database

Oltre al controllo normale, le fonti con il blocco `scorta` nel registro vengono lette per intero la prima volta
e poi alla frequenza della scorta (di solito una volta al mese): gli annunci trovati cosi' non contano come novita'.
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from datetime import datetime, timedelta, timezone

import httpx
import psycopg

from app.db.connessione import connetti
from app.db.migrazioni import applica_migrazioni
from app.fonti.registro import CARTELLA_FONTI, Fonte, carica_registro
from app.raccolta.lettori import lettore_per
from app.raccolta.modelli import Lettura
from app.raccolta.scarica import NonPermesso, nuovo_client
from app.raccolta.scorta import leggi_scorta

# Ogni quanto controllare una fonte, per frequenza dichiarata nel registro (con un piccolo margine
# in meno, cosi' un controllo "giornaliero" lanciato ogni ora non slitta di un giorno).
INTERVALLI = {
    "giornaliera": timedelta(hours=23),
    "tre_a_settimana": timedelta(hours=55),
    "settimanale": timedelta(days=7) - timedelta(hours=1),
    "quindicinale": timedelta(days=14) - timedelta(hours=1),
    "mensile": timedelta(days=30) - timedelta(hours=1),
}
PAUSA_TRA_FONTI = 1.0  # secondi: un sito alla volta, senza fretta
MARGINE_DATA_FUTURA = timedelta(days=1)  # una "data di pubblicazione" oltre domani e' quasi sempre una scadenza


def allinea_fonti(conn, fonti: list[Fonte]) -> None:
    """Copia il registro YAML nella tabella fonti (inserisce le nuove, aggiorna le esistenti)."""
    with conn.cursor() as cur:
        for f in fonti:
            cur.execute(
                """
                INSERT INTO fonti (id, nome, ente, tipo, territorio, url, modalita, feed_url, piattaforma,
                                   frequenza, stato, verificato_il, note, aggiornata_il)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, now())
                ON CONFLICT (id) DO UPDATE SET
                    nome = EXCLUDED.nome, ente = EXCLUDED.ente, tipo = EXCLUDED.tipo, territorio = EXCLUDED.territorio,
                    url = EXCLUDED.url, modalita = EXCLUDED.modalita, feed_url = EXCLUDED.feed_url,
                    piattaforma = EXCLUDED.piattaforma, frequenza = EXCLUDED.frequenza, stato = EXCLUDED.stato,
                    verificato_il = EXCLUDED.verificato_il, note = EXCLUDED.note, aggiornata_il = now()
                """,
                (f.id, f.nome, f.ente, f.tipo, f.territorio, f.url or None, f.modalita, f.feed_url, f.piattaforma,
                 f.frequenza, f.stato, f.verificato_il, f.note),
            )
    conn.commit()


def fonti_in_scadenza(conn, fonti: list[Fonte], adesso: datetime, scorta: bool = False) -> list[Fonte]:
    """Le fonti da controllare adesso: non escluse, non in pausa, con un indirizzo, e l'ultimo controllo troppo vecchio.
    Con scorta=True: le fonti con il blocco `scorta` la cui ultima lettura completa e' piu' vecchia della sua frequenza."""
    with conn.cursor() as cur:
        cur.execute("SELECT id FROM fonti WHERE in_pausa")
        in_pausa = {r["id"] for r in cur.fetchall()}
        # Scorta: conta l'ultima riuscita; dopo un errore si riprova il giorno dopo, non a ogni giro.
        cur.execute("""SELECT fonte_id, max(iniziato_il) AS ultimo,
                              max(iniziato_il) FILTER (WHERE esito = 'ok') AS riuscito
                       FROM controlli WHERE tipo = %s GROUP BY fonte_id""", ("scorta" if scorta else "novita",))
        righe = {r["fonte_id"]: r for r in cur.fetchall()}
    scelte = []
    for f in fonti:
        if f.stato == "esclusa" or f.id in in_pausa or not f.indirizzo_da_controllare:
            continue
        if scorta and not f.scorta:
            continue
        riga = righe.get(f.id)
        if riga is None:
            scelte.append(f)
        elif not scorta:
            if adesso - riga["ultimo"] >= INTERVALLI[f.frequenza]:
                scelte.append(f)
        elif (riga["riuscito"] is None or adesso - riga["riuscito"] >= INTERVALLI[f.scorta.get("frequenza", "mensile")]) \
                and adesso - riga["ultimo"] >= INTERVALLI["giornaliera"]:
            scelte.append(f)
    return scelte


def data_di_pubblicazione(a, adesso: datetime) -> datetime | None:
    """Una data di pubblicazione nel futuro non e' credibile (Camera di Caserta: tutte al 30/10/2026, la scadenza
    di un bando letta nell'elenco): si tiene nei dati grezzi come `data_futura` e la pubblicazione resta vuota,
    cosi' la plancia non mostra una data dell'ultimo record sbagliata."""
    if a.pubblicato_il is not None and a.pubblicato_il > adesso + MARGINE_DATA_FUTURA:
        a.dati = {**(a.dati or {}), "data_futura": a.pubblicato_il.date().isoformat()}
        return None
    return a.pubblicato_il


def salva_lettura(conn, fonte: Fonte, lettura: Lettura, durata_ms: int, scorta: bool = False) -> tuple[int, str]:
    """Salva annunci nuovi o cambiati e il controllo. Ritorna (novita, esito).
    Con scorta=True (e alla prima lettura di una fonte) gli annunci nuovi sono segnati `da_scorta`: bandi gia'
    pubblicati, non novita'. Con scorta=True la pagina osservata non cambia: il confronto per la struttura cambiata
    resta tra controlli normali."""
    novita = 0
    adesso = datetime.now(timezone.utc)
    with conn.cursor() as cur:
        # La prima lettura di una fonte nuova trova bandi gia' pubblicati, non novita': come la scorta.
        cur.execute("SELECT 1 FROM pagine WHERE fonte_id = %s", (fonte.id,))
        da_scorta = scorta or cur.fetchone() is None
        for a in lettura.annunci:
            pubblicato_il = data_di_pubblicazione(a, adesso)
            cur.execute(
                """
                INSERT INTO annunci (fonte_id, url, titolo, riassunto, pubblicato_il, impronta, dati, da_scorta)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (fonte_id, url) DO UPDATE SET
                    titolo = EXCLUDED.titolo, riassunto = EXCLUDED.riassunto,
                    pubblicato_il = COALESCE(EXCLUDED.pubblicato_il, annunci.pubblicato_il),
                    impronta = EXCLUDED.impronta, dati = EXCLUDED.dati, aggiornato_il = now()
                WHERE annunci.impronta <> EXCLUDED.impronta
                RETURNING (xmax = 0) AS nuovo
                """,
                (fonte.id, a.url, a.titolo, a.riassunto, pubblicato_il, a.impronta,
                 psycopg.types.json.Jsonb(a.dati) if a.dati else None, da_scorta),
            )
            riga = cur.fetchone()
            if riga and riga["nuovo"]:
                novita += 1

        esito = "ok"
        messaggio = lettura.messaggio
        # Struttura cambiata = la fonte risponde ma non si legge piu' nulla, mentre prima si leggeva qualcosa.
        # Una fonte vuota fin dall'inizio (feed senza voci) e' solo "ok, vuota".
        cur.execute("SELECT elementi FROM pagine WHERE fonte_id = %s", (fonte.id,))
        precedente = cur.fetchone()
        if scorta:
            pass   # la scorta puo' essere vuota (nessun bando aperto) e non dice nulla sulla pagina osservata
        elif not lettura.annunci:
            if precedente and precedente["elementi"] > 0:
                esito = "struttura_cambiata"
                messaggio = f"risponde ma non si legge piu' nessun elemento (prima: {precedente['elementi']})"
            else:
                messaggio = messaggio or "nessun elemento (fonte vuota)"
        if not scorta:
            cur.execute(
                """
                INSERT INTO pagine (fonte_id, url, impronta, elementi, scaricata_il) VALUES (%s, %s, %s, %s, now())
                ON CONFLICT (fonte_id) DO UPDATE SET url = EXCLUDED.url, impronta = EXCLUDED.impronta,
                    elementi = EXCLUDED.elementi, scaricata_il = now()
                """,
                (fonte.id, fonte.indirizzo_da_controllare, lettura.impronta_pagina or "", len(lettura.annunci)),
            )
        cur.execute(
            """
            INSERT INTO controlli (fonte_id, durata_ms, esito, codice_http, byte, messaggio, elementi_letti, novita, tipo)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            """,
            (fonte.id, durata_ms, esito, lettura.codice_http, lettura.byte, messaggio or None, len(lettura.annunci), novita,
             "scorta" if scorta else "novita"),
        )
    conn.commit()
    return novita, esito


def salva_errore(conn, fonte: Fonte, esito: str, messaggio: str, durata_ms: int, codice: int | None = None,
                 scorta: bool = False) -> None:
    with conn.cursor() as cur:
        cur.execute(
            "INSERT INTO controlli (fonte_id, durata_ms, esito, codice_http, messaggio, tipo) VALUES (%s, %s, %s, %s, %s, %s)",
            (fonte.id, durata_ms, esito, codice, ("scorta: " if scorta else "") + messaggio[:500],
             "scorta" if scorta else "novita"),
        )
    conn.commit()


def leggi_fonte(fonte: Fonte, client: httpx.Client) -> Lettura:
    lettore = lettore_per(fonte)
    if lettore is None:
        raise NotImplementedError(f"modalita' '{fonte.modalita}' non ancora disponibile")
    if fonte.richiesta.get("ipv6"):
        with nuovo_client(ipv6=True) as client_ipv6:
            return lettore(fonte, client_ipv6)
    return lettore(fonte, client)


def leggi_tutta(fonte: Fonte, client: httpx.Client) -> Lettura:
    """La scorta della fonte: tutte le pagine, con il lettore normale (app/raccolta/scorta.py)."""
    return leggi_scorta(fonte, client, leggi_fonte)


def controlla_fonte(conn, fonte: Fonte, client: httpx.Client, scorta: bool = False) -> str:
    inizio = time.monotonic()
    tipo = "scorta   " if scorta else ""
    try:
        lettura = leggi_tutta(fonte, client) if scorta else leggi_fonte(fonte, client)
    except (NotImplementedError, NonPermesso) as exc:
        salva_errore(conn, fonte, "saltato", str(exc), int((time.monotonic() - inizio) * 1000), scorta=scorta)
        return f"saltato  {tipo}{fonte.id}: {exc}"
    except httpx.HTTPStatusError as exc:
        salva_errore(conn, fonte, "errore", f"HTTP {exc.response.status_code}", int((time.monotonic() - inizio) * 1000),
                     exc.response.status_code, scorta=scorta)
        return f"errore   {tipo}{fonte.id}: HTTP {exc.response.status_code}"
    except Exception as exc:  # noqa: BLE001 - qualunque errore va registrato, la raccolta continua
        salva_errore(conn, fonte, "errore", f"{type(exc).__name__}: {exc}", int((time.monotonic() - inizio) * 1000),
                     scorta=scorta)
        return f"errore   {tipo}{fonte.id}: {type(exc).__name__}: {str(exc)[:120]}"
    durata = int((time.monotonic() - inizio) * 1000)
    novita, esito = salva_lettura(conn, fonte, lettura, durata, scorta=scorta)
    return f"{esito:<8} {tipo}{fonte.id}: {len(lettura.annunci)} elementi, {novita} nuovi, {durata} ms"


def esegui(selezione: str | None = None, tutte: bool = False, scorta: bool = False) -> int:
    """Il giro della raccolta. Senza argomenti: prima le scorte da leggere (prima volta o frequenza della scorta
    superata), poi i controlli normali in scadenza."""
    fonti = carica_registro(CARTELLA_FONTI)
    with connetti() as conn:
        applica_migrazioni(conn)
        allinea_fonti(conn, fonti)
        scorte: list[Fonte] = []
        if selezione:
            scelte = [f for f in fonti if f.id == selezione]
            if not scelte:
                print(f"Fonte '{selezione}' non trovata nel registro.", file=sys.stderr)
                return 2
            if scorta:
                if not scelte[0].scorta:
                    print(f"La fonte '{selezione}' non ha il blocco scorta nel registro.", file=sys.stderr)
                    return 2
                scorte, scelte = scelte, []
        elif tutte:
            scelte = [f for f in fonti if f.stato != "esclusa" and f.indirizzo_da_controllare]
        else:
            adesso = datetime.now(timezone.utc)
            scorte = fonti_in_scadenza(conn, fonti, adesso, scorta=True)
            scelte = fonti_in_scadenza(conn, fonti, adesso)
        print(f"Fonti da controllare: {len(scelte)}" + (f"; scorte da leggere: {len(scorte)}" if scorte else ""))
        with nuovo_client() as client:
            for f in scorte:
                print(controlla_fonte(conn, f, client, scorta=True), flush=True)
                time.sleep(PAUSA_TRA_FONTI)
            for f in scelte:
                print(controlla_fonte(conn, f, client), flush=True)
                time.sleep(PAUSA_TRA_FONTI)
    return 0


def prova(selezione: str, scorta: bool = False, quanti: int = 40) -> int:
    """Legge una fonte e stampa cosa trova, senza toccare il database. Utile per tarare una voce del registro."""
    fonti = {f.id: f for f in carica_registro(CARTELLA_FONTI)}
    if selezione not in fonti:
        print(f"Fonte '{selezione}' non trovata.", file=sys.stderr)
        return 2
    if scorta and not fonti[selezione].scorta:
        print(f"La fonte '{selezione}' non ha il blocco scorta nel registro.", file=sys.stderr)
        return 2
    with nuovo_client() as client:
        lettura = leggi_tutta(fonti[selezione], client) if scorta else leggi_fonte(fonti[selezione], client)
    print(f"HTTP {lettura.codice_http}, {lettura.byte} byte, {len(lettura.annunci)} elementi. {lettura.messaggio}")
    for a in lettura.annunci[:quanti]:
        data = a.pubblicato_il.date().isoformat() if a.pubblicato_il else "    -     "
        print(f"  {data}  {a.titolo[:90]}\n              {a.url}")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Raccolta: controlla le fonti e salva gli annunci.")
    parser.add_argument("--fonte", help="controlla solo questa fonte (id del registro)")
    parser.add_argument("--tutte", action="store_true", help="controlla tutte le fonti, anche se non in scadenza")
    parser.add_argument("--prova", metavar="ID", help="legge una fonte e stampa gli annunci, senza database")
    parser.add_argument("--scorta", nargs="?", const=True, metavar="ID",
                        help="legge tutta la scorta di una fonte (con --prova: senza database)")
    parser.add_argument("--quanti", type=int, default=40, help="con --prova: quanti annunci stampare")
    args = parser.parse_args(argv)
    if args.prova:
        return prova(args.prova, scorta=bool(args.scorta), quanti=args.quanti)
    if isinstance(args.scorta, str):
        return esegui(args.scorta, scorta=True)
    return esegui(args.fonte, args.tutte)


if __name__ == "__main__":
    sys.exit(main())
