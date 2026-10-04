"""Feedback sulle schede (05/10/2026): salva gli esiti degli agenti (/out/feedback/<id>/esito.json).

  corretto  -> le correzioni vanno nella scheda con app.feedback.applica_correzioni (stessa pulizia delle schede,
               storico delle versioni con la causa "feedback <id>: ..."); feedback 'corretto' con la risposta;
  rifare    -> bandi.da_aggiornare = "feedback <id>: <motivo>": la scheda rientra nel giro normale (esporta.py);
               feedback 'corretto' con la risposta;
  respinto  -> feedback 'respinto' con la risposta.
In tutti i casi l'esito intero va in feedback.analisi. Un errore (valore non ammesso, campo sconosciuto, scheda
cambiata nel frattempo) non salva niente: il feedback resta 'preso_in_carico' e l'esito si puo' correggere e
reimportare. Gli importati finiscono in /out/feedback/importati.txt; le regole proposte dagli agenti si stampano e
si aggiungono in /out/feedback/regole_proposte.md, da riportare a Matteo.

  importa_feedback.py [--prova]   # --prova: controlla e dice cosa farebbe, non scrive
"""

import json
import sys
from datetime import date
from pathlib import Path

from app.db.connessione import connetti
from app.feedback import CATEGORIE, ErroreFeedback, applica_correzioni, gestisci

OUT = Path("/out/feedback")
FATTI = OUT / "importati.txt"
REGOLE = OUT / "regole_proposte.md"
ESITI = ("corretto", "respinto", "rifare")
RAGIONE = ("si", "no", "in_parte")


def valida(e) -> list[str]:
    """Gli errori di formato dell'esito (vuoto se va bene)."""
    if not isinstance(e, dict):
        return ["non e' un oggetto JSON"]
    errori = []
    if e.get("esito") not in ESITI:
        errori.append(f"esito {e.get('esito')!r} non ammesso")
    if not isinstance(e.get("risposta"), str) or not e["risposta"].strip():
        errori.append("manca la risposta per chi ha segnalato")
    if not isinstance(e.get("problemi"), list):
        errori.append("problemi deve essere un elenco")
    else:
        for p in e["problemi"]:
            if not isinstance(p, dict) or p.get("categoria") not in CATEGORIE or p.get("ha_ragione") not in RAGIONE:
                errori.append(f"problema non valido: {str(p)[:120]}")
    if not isinstance(e.get("correzioni", []), list):
        errori.append("correzioni deve essere un elenco")
    else:
        for c in e.get("correzioni") or []:
            if not isinstance(c, dict) or not isinstance(c.get("campo"), str) or "valore" not in c:
                errori.append(f"correzione non valida: {str(c)[:120]}")
    if e.get("esito") == "rifare" and not (isinstance(e.get("rifare_motivo"), str) and e["rifare_motivo"].strip()):
        errori.append("esito 'rifare' senza rifare_motivo")
    if e.get("regola") is not None and not isinstance(e.get("regola"), str):
        errori.append("regola deve essere una frase o null")
    return errori


def correzioni_da_fare(esportata: dict, attuale: dict, correzioni: list[dict]) -> list[dict]:
    """Le correzioni ancora da applicare. Un campo cambiato dopo l'esportazione (un'altra segnalazione sullo stesso
    bando, una scheda rifatta) e' un conflitto, salvo che valga gia' il valore proposto."""
    restano = []
    for c in correzioni:
        campo = c["campo"]
        if attuale.get(campo) == c.get("valore"):
            continue                                   # gia' cosi'
        if attuale.get(campo) != esportata.get(campo):
            raise ErroreFeedback(f"il campo {campo} e' cambiato dopo l'esportazione: va riesaminato sulla scheda nuova")
        restano.append(c)
    return restano


def main() -> int:
    prova = "--prova" in sys.argv
    fatti = set(FATTI.read_text().split()) if FATTI.exists() else set()
    conti = {"corretto": 0, "respinto": 0, "rifare": 0, "errori": 0, "non_pronti": 0}
    regole = []
    with connetti() as conn:
        cartelle = sorted((p for p in OUT.iterdir() if p.is_dir() and p.name.isdigit()), key=lambda p: int(p.name)) \
            if OUT.exists() else []
        for cartella in cartelle:
            fid = int(cartella.name)
            fe = cartella / "esito.json"
            if str(fid) in fatti or not fe.exists():
                continue
            try:
                e = json.loads(fe.read_text())
                segnalazione = json.loads((cartella / "segnalazione.json").read_text())
                esportata = json.loads((cartella / "scheda.json").read_text()).get("risposta") or {}
            except (OSError, json.JSONDecodeError) as exc:
                print(f"[{fid}] file non leggibile: {exc}")
                conti["errori"] += 1
                continue
            errori = valida(e)
            if errori:
                print(f"[{fid}] esito.json non valido: {'; '.join(errori)}")
                conti["errori"] += 1
                continue
            bid = segnalazione["bando_id"]
            with conn.cursor() as cur:
                cur.execute("SELECT stato FROM feedback WHERE id = %s", (fid,))
                f = cur.fetchone()
                cur.execute("SELECT dati FROM bandi WHERE id = %s", (bid,))
                b = cur.fetchone()
            if not f or not b:
                print(f"[{fid}] feedback o bando {bid} non piu' nel database: saltato")
                conti["errori"] += 1
                continue
            if f["stato"] != "preso_in_carico":
                # 'nuovo': chi ha scritto ha cambiato la segnalazione dopo l'esportazione (esporta_feedback la riesporta);
                # 'corretto'/'respinto': l'admin l'ha gia' chiusa a mano.
                print(f"[{fid}] stato del feedback '{f['stato']}': esito non importato")
                conti["non_pronti"] += 1
                continue
            esito, risposta = e["esito"], e["risposta"].strip()
            correzioni = e.get("correzioni") or []
            try:
                attuale = ((b["dati"] or {}).get("risposta") or {}) if isinstance(b["dati"], dict) else {}
                da_fare = correzioni_da_fare(esportata, attuale, correzioni) if esito == "corretto" else []
                if prova:
                    altro = f", correzioni {[c['campo'] for c in da_fare]}" if esito == "corretto" else ""
                    altro += f", da_aggiornare: {e['rifare_motivo'][:100]}" if esito == "rifare" else ""
                    print(f"[{fid}] bando {bid}: {esito}{altro}")
                    conti[esito] += 1
                    if e.get("regola"):
                        regole.append((fid, bid, e["regola"].strip()))
                    continue
                if esito == "corretto" and da_fare:
                    problemi = applica_correzioni(conn, bid, da_fare, causa=f"feedback {fid}: {risposta[:150]}")
                    if problemi:
                        print(f"[{fid}] bando {bid}: controlli della scheda dopo la correzione: {'; '.join(problemi)[:300]}")
                elif esito == "corretto":
                    print(f"[{fid}] bando {bid}: 'corretto' senza correzioni da applicare (gia' a posto o nessuna proposta)")
                if esito == "rifare":
                    motivo = f"feedback {fid}: {e['rifare_motivo'].strip()}"[:500]
                    with conn.cursor() as cur:
                        cur.execute("SELECT set_config('bandi_radar.causa', %s, true)", (motivo[:300],))
                        cur.execute("UPDATE bandi SET da_aggiornare = %s WHERE id = %s", (motivo, bid))
                gestisci(conn, fid, "respinto" if esito == "respinto" else "corretto", risposta, "agente")
                with conn.cursor() as cur:
                    cur.execute("UPDATE feedback SET analisi = %s WHERE id = %s", (json.dumps(e, ensure_ascii=False), fid))
                conn.commit()
            except ErroreFeedback as exc:
                conn.rollback()
                print(f"[{fid}] bando {bid}: NON importato, resta 'preso_in_carico': {exc}")
                conti["errori"] += 1
                continue
            except Exception as exc:   # un valore che il database rifiuta: si segnala e si passa oltre
                conn.rollback()
                print(f"[{fid}] bando {bid}: NON importato ({type(exc).__name__}): {str(exc)[:200]}")
                conti["errori"] += 1
                continue
            conti[esito] += 1
            if e.get("regola"):
                regole.append((fid, bid, e["regola"].strip()))
            with FATTI.open("a") as out:
                out.write(f"{fid}\n")
    print(("PROVA (niente scritto): " if prova else "") + ", ".join(f"{k} {v}" for k, v in conti.items()))
    if regole:
        print("\nREGOLE PROPOSTE dagli agenti (da riportare a Matteo):")
        for fid, bid, r in regole:
            print(f"  - feedback {fid}, bando {bid}: {r}")
        if not prova:
            with REGOLE.open("a") as out:
                out.write(f"\n## {date.today():%d/%m/%Y}\n\n")
                out.writelines(f"- feedback {fid}, bando {bid}: {r}\n" for fid, bid, r in regole)
    return 0


if __name__ == "__main__":
    sys.exit(main())
