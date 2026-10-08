"""Punto 1 del piano del 03/10: scarica la pagina ufficiale DI OGGI dei bandi da ricontrollare (regole di chiusura +
proponibili senza stato + id dati a mano), una pagina per sito alla volta, robots.txt, User-Agent BandiRadar.
Scrive /out/stato/pagine/<id>.md: dati della scheda, testo di oggi, testo salvato prima. Non scrive nel database.
Uso: pagine_oggi.py [id ...]"""
import json
import os
import sys
import threading
import zlib
from collections import defaultdict
from pathlib import Path
from urllib.parse import urlsplit

import httpx

from app.db.connessione import connetti
from app.raccolta.scarica import NonPermesso, nuovo_client, scarica
from app.schede.allegati import Pausa, testo_html, testo_pdf

OUT = Path("/out/stato/pagine")


def main():
    os.umask(0)
    OUT.mkdir(parents=True, exist_ok=True)
    extra = [int(x) for x in sys.argv[1:] if x.isdigit()]
    regole = json.loads(Path("/out/stato/regole.json").read_text())
    with connetti() as conn, conn.cursor() as cur:
        cur.execute("""SELECT b.id, b.titolo, b.ente, b.url, b.stato, b.data_apertura, b.scadenza, b.chiuso_il, b.sintesi,
                              b.preliminare->>'motivo' AS motivo_pre,
                              (SELECT a.url FROM allegati a WHERE a.bando_id=b.id AND a.annuncio_id IS NULL AND a.tipo='pagina'
                               ORDER BY a.id DESC LIMIT 1) AS url_pagina,
                              (SELECT a.testo_estratto FROM allegati a WHERE a.bando_id=b.id AND a.annuncio_id IS NULL AND a.tipo='pagina'
                               ORDER BY a.id DESC LIMIT 1) AS testo_prima
                       FROM bandi b WHERE b.completezza='bando_ufficiale' AND coalesce(b.stato,'x') <> 'chiuso'
                         AND (b.stato IS NULL OR b.id = ANY(%s)) ORDER BY b.id""",
                    ([int(x) for x in regole] + extra,))
        bandi = [dict(r) for r in cur.fetchall()]
    per_sito = defaultdict(list)
    for b in bandi:
        if (OUT / f"{b['id']}.md").exists():
            continue
        u = b["url_pagina"] or b["url"]
        b["indirizzo"] = u
        per_sito[urlsplit(u or "").netloc].append(b)
    print("bandi:", len(bandi), "da scaricare:", sum(map(len, per_sito.values())), "siti:", len(per_sito))
    # un lavoratore per gruppo di siti: ogni sito e' letto da un solo lavoratore, una pagina alla volta
    gruppi = defaultdict(list)
    for sito, lista in per_sito.items():
        gruppi[zlib.crc32(sito.encode()) % 6].append(lista)

    def lavora(liste):
        client = nuovo_client()
        pausa = Pausa(client, minima=3.0)
        for lista in liste:
            for b in lista:
                oggi, esito = "", ""
                try:
                    pausa.attendi(b["indirizzo"])
                    r = scarica(client, b["indirizzo"])
                    esito = f"HTTP {r.status_code}"
                    if "pdf" in r.headers.get("content-type", ""):
                        oggi = testo_pdf(r.content) or ""
                    else:
                        oggi = testo_html(r.text) or ""
                except NonPermesso as e:
                    esito = f"non scaricata: {e}"
                except httpx.HTTPError as e:
                    esito = f"errore: {type(e).__name__} {e}"[:200]
                motivi = "; ".join(f"{x['regola']}: {x['testo'][:200]}" for x in regole.get(str(b["id"]), {}).get("regole", []))
                testo = (f"# Bando {b['id']}: {b['titolo']}\n\nEnte: {b['ente']}\nIndirizzo: {b['indirizzo']}\n"
                         f"Scheda: stato={b['stato']} apertura={b['data_apertura']} scadenza={b['scadenza']} chiuso_il={b['chiuso_il']}\n"
                         f"Motivo del controllo preliminare: {b['motivo_pre']}\n"
                         f"Perche' si ricontrolla: {motivi or 'scheda senza stato (nessuna data)'}\n\n"
                         f"Sintesi della scheda: {(b['sintesi'] or '')[:1200]}\n\n"
                         f"## Pagina ufficiale scaricata OGGI ({esito})\n\n{oggi[:25000]}\n\n"
                         f"## Pagina ufficiale salvata prima\n\n{(b['testo_prima'] or '(nessuna)')[:12000]}\n")
                (OUT / f"{b['id']}.md").write_text(testo)

    fili = [threading.Thread(target=lavora, args=(g,)) for g in gruppi.values()]
    for f in fili:
        f.start()
    for f in fili:
        f.join()
    print("scritte:", len(list(OUT.glob("*.md"))))


if __name__ == "__main__":
    main()
