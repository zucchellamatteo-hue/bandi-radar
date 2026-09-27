"""Salva nel database di produzione i controlli preliminari e le schede compilati nella sessione del 26/09/2026.

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
MODELLO = "claude-code (sessione del 26/09/2026, senza API)"
CAUSA = "scheda compilata nella sessione di Claude Code del 26/09/2026 (senza API)"


def vuoto(schema: dict):
    if schema.get("type") == "array":
        return []
    if schema.get("type") == "object":
        return {k: vuoto(v) for k, v in schema["properties"].items()}
    return None


def completa(dati: dict, schema: dict) -> dict:
    """Aggiunge le chiavi mancanti (vuote) e toglie quelle in piu', ricorsivamente sugli oggetti."""
    fuori = {}
    for k, s in schema["properties"].items():
        v = dati.get(k)
        if s.get("type") == "object" and isinstance(v, dict):
            fuori[k] = completa(v, s)
        elif v is None:
            fuori[k] = vuoto(s)
        else:
            fuori[k] = v
    return fuori


def pulisci(s: dict) -> list[str]:
    """Toglie i valori che il database o i filtri non possono accettare. Ritorna cosa e' stato tolto."""
    tolti = []
    for nome, ammessi in campi.VALORI_AMMESSI.items():
        v = s.get(nome)
        if isinstance(v, list):
            buoni = [x for x in v if x in ammessi]
            if len(buoni) != len(v):
                tolti.append(f"{nome}: tolti {[x for x in v if x not in ammessi]}")
                s[nome] = buoni
        elif v is not None and v not in ammessi:
            tolti.append(f"{nome}: tolto {v!r}")
            s[nome] = None
    if s.get("tipo_agevolazione") not in (None, *campi.TIPI_AGEVOLAZIONE, "misto"):
        tolti.append(f"tipo_agevolazione: tolto {s['tipo_agevolazione']!r}")
        s["tipo_agevolazione"] = None
    if s.get("tema") not in (None, *campi.TEMI):
        tolti.append(f"tema: tolto {s['tema']!r}")
        s["tema"] = None
    for nome in ("data_apertura", "scadenza", "chiuso_il"):
        if s.get(nome) is not None and ia._data(s[nome]) is None:
            tolti.append(f"{nome}: tolta data non valida {s[nome]!r}")
            s[nome] = None
    for nome in ("ora_apertura", "ora_scadenza"):
        if s.get(nome) is not None and not ia._ORA.match(str(s[nome])):
            tolti.append(f"{nome}: tolta ora non valida {s[nome]!r}")
            s[nome] = None
    for nome in campi.NUMERICI:
        v = s.get(nome)
        if v is not None and (not isinstance(v, (int, float)) or isinstance(v, bool) or v < 0 or v > ia._IMPORTO_MASSIMO):
            tolti.append(f"{nome}: tolto numero non plausibile {v!r}")
            s[nome] = None
    for nome in ("eta_impresa_min_mesi", "eta_impresa_max_mesi"):
        if isinstance(s.get(nome), float):
            s[nome] = round(s[nome])
    vincoli = s.get("vincoli") or {}
    for v in campi.VINCOLI:
        if vincoli.get(v) not in campi.STATI_VINCOLO:
            vincoli[v] = "non_noto"
    s["vincoli"] = vincoli
    if s.get("completezza") not in campi.COMPLETEZZA:
        tolti.append(f"completezza: {s.get('completezza')!r} sostituito con nessun_documento")
        s["completezza"] = "nessun_documento"
    return tolti


def main() -> int:
    prova = "--prova" in sys.argv
    conteggi = {"preliminari": 0, "schede": 0, "con_problemi": 0, "json_rotti": 0, "gia_fatte": 0}
    with connetti() as conn:
        for cartella in sorted(OUT.iterdir(), key=lambda p: int(p.name)):
            bando_id = int(cartella.name)
            with conn.cursor() as cur:
                cur.execute("SELECT id, url, dati, preliminare FROM bandi WHERE id = %s", (bando_id,))
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
                if not prova:
                    with conn.cursor() as cur:
                        cur.execute("SELECT set_config('bandi_radar.causa', %s, true)", ("controllo preliminare: " + CAUSA,))
                        cur.execute("UPDATE bandi SET preliminare = %s WHERE id = %s", (json.dumps(pre), bando_id))
                    conn.commit()
                conteggi["preliminari"] += 1
            fs = cartella / "scheda.json"
            if not fs.exists():
                continue
            if b["dati"] is not None:
                conteggi["gia_fatte"] += 1
                continue
            try:
                grezza = json.loads(fs.read_text())
            except json.JSONDecodeError as exc:
                print(f"[{bando_id}] scheda.json non valido: {exc}")
                conteggi["json_rotti"] += 1
                continue
            scheda = completa(grezza, ia.SCHEMA_SCHEDA)
            scheda["url"] = scheda.get("url") or b["url"]
            tolti = pulisci(scheda)
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
                    cur.execute(f"UPDATE bandi SET {assegnazioni}, dati = %s WHERE id = %s AND dati IS NULL",
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
