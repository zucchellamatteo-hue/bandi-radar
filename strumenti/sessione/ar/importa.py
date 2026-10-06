"""Salva nel database di produzione i controlli preliminari e le schede compilati nella sessione del 28/09/2026.

Per ogni /out/fascicoli/<id>/:
  preliminare.json  -> bandi.preliminare (se vuoto);
  scheda.json       -> campi della scheda, come salva_scheda di app/schede/ia.py, con i controlli di verifica_scheda.
Valori fuori dagli elenchi ammessi, date e ore non valide: tolti prima di salvare e scritti in dati.problemi
(la scheda resta in coda a Matteo, come per l'API). Nessuna scheda di Matteo viene sovrascritta: si scrive solo
dove dati e' vuoto. Dopo, lo stato dei bandi si ricalcola dalle date.

  importa.py --prova    # controlla e conta, non scrive
"""

import json
import sys
from pathlib import Path

from app.db.connessione import connetti
from app.schede import campi, ia
from app.schede.stato import aggiorna_stati

OUT = Path("/out/fascicoli")
MODELLO = "claude-code (sessione del 28/09/2026, Opus, senza API)"
CAUSA = "scheda compilata nella sessione di Claude Code del 28/09/2026 (Opus, senza API)"


def main() -> int:
    prova = "--prova" in sys.argv
    conteggi = {"preliminari": 0, "schede": 0, "con_problemi": 0, "json_rotti": 0, "gia_fatte": 0}
    with connetti() as conn:
        for cartella in sorted(OUT.iterdir(), key=lambda p: int(p.name)):
            bando_id = int(cartella.name)
            with conn.cursor() as cur:
                cur.execute("SELECT id, url, dati, preliminare, da_aggiornare, scheda_il FROM bandi WHERE id = %s", (bando_id,))
                b = cur.fetchone()
            if not b:
                continue
            fp = cartella / "preliminare.json"
            if fp.exists() and b["preliminare"] is None:
                try:
                    pre = json.loads(fp.read_text())
                except json.JSONDecodeError:
                    print(f"[{bando_id}] preliminare.json non valido")
                    conteggi["json_rotti"] += 1
                    continue
                pre = {k: pre.get(k) for k in ia.SCHEMA_PRELIMINARE["properties"]}
                for k, s in ia.SCHEMA_PRELIMINARE["properties"].items():   # valori fuori elenco -> il "non so"
                    if "enum" in s and pre[k] not in s["enum"]:
                        pre[k] = "non_noto" if "non_noto" in s["enum"] else "incerto"
                pre["compilato_da"] = MODELLO
                pre = ia.firma(pre, "sessione")   # chi e quando, per la situazione del bando (bandi_situazione)
                if not prova:
                    with conn.cursor() as cur:
                        cur.execute("SELECT set_config('bandi_radar.causa', %s, true)", ("controllo preliminare: " + CAUSA,))
                        cur.execute("UPDATE bandi SET preliminare = %s WHERE id = %s", (json.dumps(pre), bando_id))
                    conn.commit()
                conteggi["preliminari"] += 1
            fs = cartella / "scheda.json"
            if not fs.exists():
                continue
            vecchio = b["dati"] is not None and b["scheda_il"] is not None and fs.stat().st_mtime <= b["scheda_il"].timestamp()
            if b["dati"] is not None and (not b["da_aggiornare"] or vecchio):
                conteggi["gia_fatte"] += 1
                continue
            try:
                grezza = json.loads(fs.read_text())
            except json.JSONDecodeError as exc:
                print(f"[{bando_id}] scheda.json non valido: {exc}")
                conteggi["json_rotti"] += 1
                continue
            scheda, tolti = ia.prepara_scheda(grezza)   # stessa pulizia dell'API (app/schede/ia.py)
            scheda["url"] = scheda.get("url") or b["url"]
            documenti, _ = ia.documenti_del_bando(conn, bando_id, ia.MASSIMO_TESTO_SCHEDA)
            problemi = tolti + ia.verifica_scheda(scheda, documenti)
            conteggi["schede"] += 1
            conteggi["con_problemi"] += bool(problemi)
            if prova:
                print(f"[{bando_id}] {len(problemi)} problemi: {'; '.join(problemi)[:300]}")
                continue
            valori = {c: scheda.get(c) for c in ia._COLONNE_SCHEDA}
            for c in ("vincoli", "linee", *ia._DETTAGLI_SCHEDA):
                valori[c] = json.dumps(valori[c]) if valori[c] is not None else None
            dati = {"risposta": scheda, "problemi": problemi, "costo_usd": 0, "modello": MODELLO,
                    "fonti": {f["campo"]: f["fonte"] for f in scheda.get("fonti") or [] if isinstance(f, dict) and "campo" in f},
                    "avvertenze": scheda.get("avvertenze") or []}
            assegnazioni = ", ".join(f"{c} = %s" for c in valori)
            try:
                with conn.cursor() as cur:
                    cur.execute("SELECT set_config('bandi_radar.causa', %s, true)", (CAUSA,))
                    cur.execute(f"UPDATE bandi SET {assegnazioni}, dati = %s, scheda_il = now(), da_aggiornare = NULL WHERE id = %s AND (dati IS NULL OR da_aggiornare IS NOT NULL)",
                                (*valori.values(), json.dumps(dati), bando_id))
                conn.commit()
            except Exception as exc:   # un valore che il database rifiuta: si segnala e si passa oltre
                conn.rollback()
                print(f"[{bando_id}] NON salvata: {type(exc).__name__}: {str(exc)[:200]}")
                conteggi["schede"] -= 1
                conteggi["json_rotti"] += 1
                continue
        if not prova:
            print(f"stati cambiati: {aggiorna_stati(conn)}")
    print(("PROVA: " if prova else "") + ", ".join(f"{k} {v}" for k, v in conteggi.items()))
    return 0


if __name__ == "__main__":
    sys.exit(main())
