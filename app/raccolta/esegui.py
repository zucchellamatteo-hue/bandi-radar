"""Esegue la raccolta: allinea la tabella fonti al registro, sceglie le fonti da controllare, le legge e salva.

Uso:
  python -m app.raccolta.esegui                 # tutte le fonti "in scadenza" secondo la loro frequenza
  python -m app.raccolta.esegui --fonte ID      # una sola fonte, subito
  python -m app.raccolta.esegui --tutte         # tutte, anche se non in scadenza
  python -m app.raccolta.esegui --prova ID      # legge una fonte e stampa gli annunci, senza database
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


def fonti_in_scadenza(conn, fonti: list[Fonte], adesso: datetime) -> list[Fonte]:
    """Le fonti da controllare adesso: non escluse, non in pausa, con un indirizzo, e l'ultimo controllo troppo vecchio."""
    with conn.cursor() as cur:
        cur.execute("SELECT id FROM fonti WHERE in_pausa")
        in_pausa = {r["id"] for r in cur.fetchall()}
        cur.execute("SELECT fonte_id, max(iniziato_il) AS ultimo FROM controlli GROUP BY fonte_id")
        ultimo = {r["fonte_id"]: r["ultimo"] for r in cur.fetchall()}
    scelte = []
    for f in fonti:
        if f.stato == "esclusa" or f.id in in_pausa or not f.indirizzo_da_controllare:
            continue
        intervallo = INTERVALLI[f.frequenza]
        if f.id not in ultimo or adesso - ultimo[f.id] >= intervallo:
            scelte.append(f)
    return scelte


def salva_lettura(conn, fonte: Fonte, lettura: Lettura, durata_ms: int) -> tuple[int, str]:
    """Salva annunci nuovi o cambiati e il controllo. Ritorna (novita, esito)."""
    novita = 0
    with conn.cursor() as cur:
        for a in lettura.annunci:
            cur.execute(
                """
                INSERT INTO annunci (fonte_id, url, titolo, riassunto, pubblicato_il, impronta, dati)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (fonte_id, url) DO UPDATE SET
                    titolo = EXCLUDED.titolo, riassunto = EXCLUDED.riassunto,
                    pubblicato_il = COALESCE(EXCLUDED.pubblicato_il, annunci.pubblicato_il),
                    impronta = EXCLUDED.impronta, dati = EXCLUDED.dati, aggiornato_il = now()
                WHERE annunci.impronta <> EXCLUDED.impronta
                RETURNING (xmax = 0) AS nuovo
                """,
                (fonte.id, a.url, a.titolo, a.riassunto, a.pubblicato_il, a.impronta,
                 psycopg.types.json.Jsonb(a.dati) if a.dati else None),
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
        if not lettura.annunci:
            if precedente and precedente["elementi"] > 0:
                esito = "struttura_cambiata"
                messaggio = f"risponde ma non si legge piu' nessun elemento (prima: {precedente['elementi']})"
            else:
                messaggio = messaggio or "nessun elemento (fonte vuota)"
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
            INSERT INTO controlli (fonte_id, durata_ms, esito, codice_http, byte, messaggio, elementi_letti, novita)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """,
            (fonte.id, durata_ms, esito, lettura.codice_http, lettura.byte, messaggio or None, len(lettura.annunci), novita),
        )
    conn.commit()
    return novita, esito


def salva_errore(conn, fonte: Fonte, esito: str, messaggio: str, durata_ms: int, codice: int | None = None) -> None:
    with conn.cursor() as cur:
        cur.execute(
            "INSERT INTO controlli (fonte_id, durata_ms, esito, codice_http, messaggio) VALUES (%s, %s, %s, %s, %s)",
            (fonte.id, durata_ms, esito, codice, messaggio[:500]),
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


def controlla_fonte(conn, fonte: Fonte, client: httpx.Client) -> str:
    inizio = time.monotonic()
    try:
        lettura = leggi_fonte(fonte, client)
    except NotImplementedError as exc:
        salva_errore(conn, fonte, "saltato", str(exc), int((time.monotonic() - inizio) * 1000))
        return f"saltato  {fonte.id}: {exc}"
    except NonPermesso as exc:
        salva_errore(conn, fonte, "saltato", str(exc), int((time.monotonic() - inizio) * 1000))
        return f"saltato  {fonte.id}: {exc}"
    except httpx.HTTPStatusError as exc:
        salva_errore(conn, fonte, "errore", f"HTTP {exc.response.status_code}", int((time.monotonic() - inizio) * 1000),
                     exc.response.status_code)
        return f"errore   {fonte.id}: HTTP {exc.response.status_code}"
    except Exception as exc:  # noqa: BLE001 - qualunque errore va registrato, la raccolta continua
        salva_errore(conn, fonte, "errore", f"{type(exc).__name__}: {exc}", int((time.monotonic() - inizio) * 1000))
        return f"errore   {fonte.id}: {type(exc).__name__}: {str(exc)[:120]}"
    durata = int((time.monotonic() - inizio) * 1000)
    novita, esito = salva_lettura(conn, fonte, lettura, durata)
    return f"{esito:<8} {fonte.id}: {len(lettura.annunci)} elementi, {novita} nuovi, {durata} ms"


def esegui(selezione: str | None = None, tutte: bool = False) -> int:
    fonti = carica_registro(CARTELLA_FONTI)
    with connetti() as conn:
        applica_migrazioni(conn)
        allinea_fonti(conn, fonti)
        if selezione:
            scelte = [f for f in fonti if f.id == selezione]
            if not scelte:
                print(f"Fonte '{selezione}' non trovata nel registro.", file=sys.stderr)
                return 2
        elif tutte:
            scelte = [f for f in fonti if f.stato != "esclusa" and f.indirizzo_da_controllare]
        else:
            scelte = fonti_in_scadenza(conn, fonti, datetime.now(timezone.utc))
        print(f"Fonti da controllare: {len(scelte)}")
        with nuovo_client() as client:
            for f in scelte:
                print(controlla_fonte(conn, f, client), flush=True)
                time.sleep(PAUSA_TRA_FONTI)
    return 0


def prova(selezione: str) -> int:
    """Legge una fonte e stampa cosa trova, senza toccare il database. Utile per tarare una voce del registro."""
    fonti = {f.id: f for f in carica_registro(CARTELLA_FONTI)}
    if selezione not in fonti:
        print(f"Fonte '{selezione}' non trovata.", file=sys.stderr)
        return 2
    with nuovo_client() as client:
        lettura = leggi_fonte(fonti[selezione], client)
    print(f"HTTP {lettura.codice_http}, {lettura.byte} byte, {len(lettura.annunci)} elementi")
    for a in lettura.annunci[:40]:
        data = a.pubblicato_il.date().isoformat() if a.pubblicato_il else "    -     "
        print(f"  {data}  {a.titolo[:90]}\n              {a.url}")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Raccolta: controlla le fonti e salva gli annunci.")
    parser.add_argument("--fonte", help="controlla solo questa fonte (id del registro)")
    parser.add_argument("--tutte", action="store_true", help="controlla tutte le fonti, anche se non in scadenza")
    parser.add_argument("--prova", metavar="ID", help="legge una fonte e stampa gli annunci, senza database")
    args = parser.parse_args(argv)
    if args.prova:
        return prova(args.prova)
    return esegui(args.fonte, args.tutte)


if __name__ == "__main__":
    sys.exit(main())
