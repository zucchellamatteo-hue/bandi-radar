"""Verifica automatica degli indirizzi del registro delle fonti.

Uso:  python -m app.fonti.verifica [--solo-controllo] [--tipo regione] [--stato attiva]

Per ogni fonte prova a scaricare l'indirizzo che l'osservatore userebbe e stampa una riga:
esito (OK / ERRORE), codice HTTP, tempo, dimensione, eventuale indirizzo finale dopo i redirect.
Nessuna IA: e' un controllo di raggiungibilita', il primo mattone dell'osservatore.
"""

from __future__ import annotations

import argparse
import sys
import time
from dataclasses import dataclass

import httpx

from app.fonti.registro import CARTELLA_FONTI, ErroreRegistro, Fonte, carica_registro

USER_AGENT = "BandiRadar/0.1 (+https://finanzagevolata.qiaro.it; raccolta bandi per imprese)"


@dataclass
class Esito:
    fonte: Fonte
    ok: bool
    codice: int | None
    secondi: float
    byte: int
    url_finale: str
    errore: str = ""


def controlla(fonte: Fonte, client: httpx.Client) -> Esito:
    indirizzo = fonte.indirizzo_da_controllare
    inizio = time.monotonic()
    try:
        risposta = client.get(indirizzo)
        secondi = time.monotonic() - inizio
        ok = risposta.status_code == 200 and len(risposta.content) > 0
        return Esito(fonte, ok, risposta.status_code, secondi, len(risposta.content), str(risposta.url))
    except httpx.HTTPError as exc:
        secondi = time.monotonic() - inizio
        return Esito(fonte, False, None, secondi, 0, indirizzo, errore=type(exc).__name__ + ": " + str(exc)[:120])


def verifica(fonti: list[Fonte], timeout: float = 20.0) -> list[Esito]:
    esiti: list[Esito] = []
    with httpx.Client(
        headers={"User-Agent": USER_AGENT, "Accept-Language": "it"},
        follow_redirects=True,
        timeout=timeout,
    ) as client:
        for fonte in fonti:
            esiti.append(controlla(fonte, client))
    return esiti


def _riga(esito: Esito) -> str:
    stato = "OK    " if esito.ok else "ERRORE"
    codice = f"{esito.codice:>3}" if esito.codice is not None else "  -"
    extra = esito.errore if esito.errore else ""
    if not extra and esito.url_finale.rstrip("/") != esito.fonte.indirizzo_da_controllare.rstrip("/"):
        extra = f"-> {esito.url_finale}"
    return f"{stato} {codice} {esito.secondi:5.1f}s {esito.byte:>8}B  {esito.fonte.id:<40} {extra}"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Verifica il registro delle fonti e la raggiungibilita' degli indirizzi.")
    parser.add_argument("--solo-controllo", action="store_true", help="controlla solo il formato dei file, senza scaricare nulla")
    parser.add_argument("--tipo", help="limita a un tipo (regione, camera, ...)")
    parser.add_argument("--stato", help="limita a uno stato (attiva, difficile, ...)")
    parser.add_argument("--timeout", type=float, default=20.0)
    args = parser.parse_args(argv)

    try:
        fonti = carica_registro(CARTELLA_FONTI)
    except ErroreRegistro as exc:
        print("Registro non valido:\n" + str(exc), file=sys.stderr)
        return 2

    if args.tipo:
        fonti = [f for f in fonti if f.tipo == args.tipo]
    if args.stato:
        fonti = [f for f in fonti if f.stato == args.stato]
    print(f"Registro valido: {len(fonti)} fonti selezionate.")
    if args.solo_controllo:
        return 0

    esiti = verifica([f for f in fonti if f.stato != "esclusa" and f.indirizzo_da_controllare], timeout=args.timeout)
    for esito in esiti:
        print(_riga(esito))
    falliti = [e for e in esiti if not e.ok]
    print(f"\nRaggiungibili: {len(esiti) - len(falliti)} su {len(esiti)}.")
    if falliti:
        print("Da rivedere: " + ", ".join(e.fonte.id for e in falliti))
    return 1 if falliti else 0


if __name__ == "__main__":
    sys.exit(main())
