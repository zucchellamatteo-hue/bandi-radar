"""Feedback sulle schede (05/10/2026): cartelle per gli agenti che rileggono i documenti e decidono.

Per ogni riga di `feedback` con stato 'nuovo' che ha problemi o un commento (i soli voti non servono agli agenti e
restano come sono) crea /out/feedback/<feedback_id>/ con:
  segnalazione.json  cosa dice chi scrive: ruolo e peso, voto, problemi, commento, versione giudicata e attuale.
                     NIENTE email, nome o utente_id: agli agenti non arriva nulla che identifichi una persona;
  scheda.json        la scheda attuale (bandi.dati['risposta']) piu' titolo, ente, url, stato, scadenza, chiuso_il;
  documenti.md       i documenti del bando, come li legge la scheda (ia.documenti_del_bando).
Il feedback passa a 'preso_in_carico' (gestito_da 'agente'): l'admin vede che e' in lavorazione.
Le cartelle gia' esportate (c'e' segnalazione.json) o con l'esito scritto si saltano; se pero' chi ha scritto ha
cambiato la segnalazione dopo l'esportazione (il feedback e' tornato 'nuovo'), la cartella vecchia va in
/out/feedback_vecchi/ e si riesporta.

  esporta_feedback.py [--prova]   # --prova: scrive le cartelle ma non tocca il database (il giro vero dopo
                                  # segna 'preso_in_carico' anche le cartelle scritte in prova)
"""

import json
import os
import shutil
import sys
import textwrap
import time
from datetime import date, datetime
from pathlib import Path

from app.db.connessione import connetti
from app.feedback import CATEGORIE, PESO
from app.schede import ia

OUT = Path("/out/feedback")
VECCHI = Path("/out/feedback_vecchi")
IMPORTATI = OUT / "importati.txt"


def spezza(testo: str) -> str:
    righe = []
    for r in testo.splitlines():
        righe.extend(textwrap.wrap(r, 180, break_long_words=True, replace_whitespace=False) or [""])
    return "\n".join(righe) + "\n"


def iso(x):
    return x.isoformat() if isinstance(x, (date, datetime)) else x


def documenti_md(conn, bando_id: int) -> str:
    documenti, avvertenze = ia.documenti_del_bando(conn, bando_id, ia.MASSIMO_TESTO_SCHEDA)
    parti = [f"# Documenti del bando {bando_id}", ""]
    if avvertenze:
        parti += ["Avvertenze sui documenti:", *(f"- {a}" for a in avvertenze), ""]
    if not documenti:
        parti.append("(nessun documento con testo)")
    for n, d in enumerate(documenti, 1):
        parti += [f"## Documento {n}: {d.get('nome') or '(senza nome)'}",
                  f"url: {d.get('url') or '-'}",
                  f"categoria: {d.get('categoria') or '-'}",
                  "", d.get("testo") or d.get("testo_estratto") or "(testo non disponibile)", ""]
    return spezza("\n".join(parti))


def togli_da_importati(feedback_id: int) -> None:
    if not IMPORTATI.exists():
        return
    righe = [r for r in IMPORTATI.read_text().split() if r != str(feedback_id)]
    IMPORTATI.write_text("".join(f"{r}\n" for r in righe))


def main() -> int:
    prova = "--prova" in sys.argv
    os.umask(0)
    OUT.mkdir(parents=True, exist_ok=True)
    esportati: dict[int, list[int]] = {}      # bando_id -> feedback esportati ora
    titoli: dict[int, str] = {}
    saltati = senza_scheda = 0
    with connetti() as conn:
        with conn.cursor() as cur:
            cur.execute("""SELECT f.id, f.bando_id, f.versione, f.ruolo, f.voto, f.problemi, f.commento, f.aggiornato_il,
                                  b.versione AS versione_attuale, b.titolo, b.ente, b.url, b.stato, b.scadenza,
                                  b.chiuso_il, b.dati
                           FROM feedback f JOIN bandi b ON b.id = f.bando_id
                           WHERE f.stato = 'nuovo'
                             AND (jsonb_array_length(f.problemi) > 0 OR nullif(btrim(f.commento), '') IS NOT NULL)
                           ORDER BY f.bando_id, f.id""")
            righe = [dict(r) for r in cur.fetchall()]
        for f in righe:
            cartella = OUT / str(f["id"])
            fs, fe = cartella / "segnalazione.json", cartella / "esito.json"
            if fs.exists() or fe.exists():
                # Gia' esportato. Se la segnalazione e' cambiata dopo (il feedback e' tornato 'nuovo') si riesporta.
                riferimento = fs if fs.exists() else fe
                if f["aggiornato_il"].timestamp() <= riferimento.stat().st_mtime:
                    # Cartella buona ma feedback ancora 'nuovo' (esportato con --prova, o interrotto prima di
                    # scrivere nel database): si segna soltanto.
                    if not prova:
                        with conn.cursor() as cur:
                            cur.execute("""UPDATE feedback SET stato = 'preso_in_carico', gestito_da = 'agente',
                                           gestito_il = now() WHERE id = %s AND stato = 'nuovo'""", (f["id"],))
                        conn.commit()
                    saltati += 1
                    continue
                VECCHI.mkdir(exist_ok=True)
                shutil.move(str(cartella), str(VECCHI / f"{f['id']}_{int(time.time())}"))
                togli_da_importati(f["id"])
            dati = f["dati"] or {}
            if not isinstance(dati.get("risposta"), dict):
                print(f"[{f['id']}] il bando {f['bando_id']} non ha piu' una scheda: lasciato 'nuovo'")
                senza_scheda += 1
                continue
            cartella.mkdir(parents=True, exist_ok=True)
            segnalazione = {
                "id": f["id"], "bando_id": f["bando_id"],
                "versione_giudicata": f["versione"], "versione_attuale": f["versione_attuale"],
                "ruolo": f["ruolo"], "peso": PESO.get(f["ruolo"], 1), "voto": f["voto"],
                "problemi": [{"categoria": p.get("categoria"), "nome": CATEGORIE.get(p.get("categoria"), p.get("categoria")),
                              "campo": p.get("campo"), "testo": p.get("testo")} for p in f["problemi"] or []],
                "commento": f["commento"],
            }
            scheda = {"bando_id": f["bando_id"], "titolo": f["titolo"], "ente": f["ente"], "url": f["url"],
                      "stato": f["stato"], "scadenza": iso(f["scadenza"]), "chiuso_il": iso(f["chiuso_il"]),
                      "versione": f["versione_attuale"], "risposta": dati["risposta"]}
            (cartella / "documenti.md").write_text(documenti_md(conn, f["bando_id"]))
            (cartella / "scheda.json").write_text(json.dumps(scheda, ensure_ascii=False, indent=1, default=str))
            # segnalazione.json per ultimo: la sua presenza dice "cartella completa"
            (cartella / "segnalazione.json").write_text(json.dumps(segnalazione, ensure_ascii=False, indent=1))
            if not prova:
                with conn.cursor() as cur:
                    cur.execute("""UPDATE feedback SET stato = 'preso_in_carico', gestito_da = 'agente', gestito_il = now()
                                   WHERE id = %s AND stato = 'nuovo'""", (f["id"],))
                conn.commit()
            esportati.setdefault(f["bando_id"], []).append(f["id"])
            titoli[f["bando_id"]] = (f["titolo"] or "")[:90]
    totale = sum(len(v) for v in esportati.values())
    print(("PROVA (database non toccato): " if prova else "")
          + f"segnalazioni esportate: {totale} su {len(esportati)} bandi; gia' esportate: {saltati}; "
            f"bandi senza scheda: {senza_scheda}")
    for bando_id, ids in esportati.items():
        insieme = f"  <- {len(ids)} segnalazioni sullo stesso bando: date le cartelle allo stesso agente" if len(ids) > 1 else ""
        print(f"  bando {bando_id} ({titoli[bando_id]}): feedback {', '.join(map(str, ids))}{insieme}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
