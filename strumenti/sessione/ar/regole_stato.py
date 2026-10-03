"""Punto 1 del piano del 03/10: regole senza IA sui proponibili non chiusi. Conta quanti ne prende ogni regola e
scrive /out/stato/regole.json (id -> regole con il frammento di testo). Non scrive nel database."""
import json
import os
import re
from collections import Counter, defaultdict
from datetime import date
from pathlib import Path

from app.db.connessione import connetti
from app.raccolta.date import leggi_data

OUT = Path("/out/stato")

FRASI = {
    "piattaforma_chiusa": r"piattaforma (?:e' |è |risulta |sar[aà] )?(?:chiusa|disattivata)",
    "termini_scaduti": r"termini (?:sono |risultano )?(?:scaduti|chiusi)|termine (?:e' |è )?scaduto",
    "sportello_chiuso": r"(?<!salvo )(?<!eventuale )chiusura (?:anticipata|dello sportello) (?:e' |è )?(?:stata )?disposta|si procede alla chiusura|sportell[oi] (?:e' |è |sono )chius|\bbando chiuso\b|opportunit[aà] scaduta|\bscaduto\b",
    "risorse_esaurite": r"(?:risorse|fondi|dotazione(?: finanziaria)?)[^.]{0,40}(?:sono|risultano|e'|è) esaurit[eai]|avvenuto esaurimento (?!della dotazione finanziaria sar)",
    "graduatoria_definitiva": r"graduatoria definitiva|elenco (?:definitivo )?dei beneficiari ammessi",
    "sospeso": r"\b(?:bando|avviso|misura|sportello|presentazione delle domande)\s+(?:e' |è |viene |risulta )?sospes[oa]",
    "non_piu_domande": r"non (?:e' |è )?(?:pi[uù]|piu') possibile presentare|non (?:sono |verranno )?(?:pi[uù]|piu') accettat|domande non pi[uù]",
}
FRASI = {k: re.compile(v, re.IGNORECASE) for k, v in FRASI.items()}
VECCHIO = re.compile(r"20(?:07|14)\s*[-/–]\s*20(?:13|20)|POR FESR 2014|PO FESR 2014|PSR 2014", re.IGNORECASE)
RECENTE = re.compile(r"\b(?:2025|2026)\b")
DATA_SCAD = re.compile(r"(?:entro (?:e non oltre )?(?:il |le ore \d{1,2}[:.]\d{2} del )|scadenza[^.]{0,30}?|fino al |termine ultimo[^.]{0,20}?)"
                       r"(\d{1,2}[/.-]\d{1,2}[/.-]\d{4}|\d{1,2}\s+[a-z]+\s+\d{4})", re.IGNORECASE)


def frammento(t, m):
    return re.sub(r"\s+", " ", t[max(0, m.start() - 120): m.end() + 120])


def main():
    os.umask(0)
    OUT.mkdir(exist_ok=True)
    oggi = date.today()
    conti, risultato = Counter(), defaultdict(list)
    with connetti() as conn, conn.cursor() as cur:
        cur.execute("""SELECT id, titolo, stato, scadenza, data_apertura FROM bandi
                       WHERE completezza='bando_ufficiale' AND coalesce(stato,'x') <> 'chiuso' ORDER BY id""")
        bandi = cur.fetchall()
        for b in bandi:
            cur.execute("""SELECT tipo, nome, categoria, testo_estratto FROM allegati WHERE bando_id=%s AND errore IS NULL
                           AND testo_estratto IS NOT NULL""", (b["id"],))
            docs = cur.fetchall()
            pagina = " ".join(d["testo_estratto"] for d in docs if d["tipo"] == "pagina")
            tutto = " ".join(d["testo_estratto"] for d in docs)
            # frasi di chiusura: sulla pagina ufficiale (testa e corpo)
            for k, rx in FRASI.items():
                if k == "graduatoria_definitiva" and b["scadenza"] is not None:
                    continue    # con una scadenza nota la graduatoria e' di solito una finestra precedente
                m = rx.search(pagina)
                if m:
                    risultato[b["id"]].append({"regola": "pagina_" + k, "testo": frammento(pagina, m)})
                    conti["pagina_" + k] += 1
            # date di chiusura gia' passate nella pagina, senza date future di chiusura
            passate, future = [], []
            for m in DATA_SCAD.finditer(pagina):
                d = leggi_data(m.group(1))
                if d:
                    (passate if d.date() < oggi else future).append((d.date(), frammento(pagina, m)))
            if passate and not future and b["scadenza"] is None:
                ultima = max(passate)
                if ultima[0].year >= 2015:
                    risultato[b["id"]].append({"regola": "pagina_data_passata", "testo": f"{ultima[0]}: {ultima[1]}"})
                    conti["pagina_data_passata"] += 1
            # programma vecchio senza anni recenti
            m = VECCHIO.search(b["titolo"] + " " + tutto)
            if m and not RECENTE.search(tutto):
                risultato[b["id"]].append({"regola": "programma_vecchio", "testo": frammento(b["titolo"] + " " + tutto, m)})
                conti["programma_vecchio"] += 1
            if not pagina:
                conti["senza_pagina"] += 1
        conti["bandi_esaminati"] = len(bandi)
        conti["bandi_presi_da_almeno_una_regola"] = len(risultato)
        conti["di_cui_senza_stato"] = sum(1 for b in bandi if b["id"] in risultato and b["stato"] is None)
    info = {b["id"]: {"titolo": b["titolo"], "stato": b["stato"], "scadenza": str(b["scadenza"])} for b in bandi}
    (OUT / "regole.json").write_text(json.dumps({str(k): {**info[k], "regole": v} for k, v in risultato.items()},
                                                ensure_ascii=False, indent=1))
    for k, v in sorted(conti.items()):
        print(f"{v:5d}  {k}")


if __name__ == "__main__":
    main()
