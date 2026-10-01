"""Doppioni dubbi da decidere in sessione (02/10/2026), con le stesse istruzioni dell'API (app/schede/prompt_doppione.md).
Solo le coppie che le regole del regista non decidono. Lotti da 20 coppie:
  /out/doppioni/lotto_NNN.md   istruzioni + coppie;   /out/doppioni/lotto_NNN.ids   id degli annunci
Risposta attesa in lotto_NNN.json: {"risposte": [{"annuncio_id": 123, "stesso": true, "motivo": "..."}]}
"""
import os
import sys
from pathlib import Path

from app.catena import regista
from app.db.connessione import connetti
from app.schede import ia

OUT = Path("/out/doppioni")


def main() -> int:
    os.umask(0)
    OUT.mkdir(parents=True, exist_ok=True)
    gia = {int(x) for p in OUT.glob("lotto_*.ids") for x in p.read_text().split()}
    with connetti() as conn:
        dubbi = [d for d in regista._dubbi_aperti(conn)
                 if regista.decisione_regole(d) is None and d["annuncio_id"] not in gia]
    istruzioni, modello = ia.leggi_prompt("prompt_doppione.md")
    istruzioni = istruzioni.replace("Rispondi solo con il JSON richiesto: `stesso` (vero o falso) e `motivo` (una frase, al massimo 25 parole).",
                                    "Per OGNI coppia del lotto rispondi con `annuncio_id` (il numero della coppia), `stesso` (vero o falso) "
                                    "e `motivo` (una frase, al massimo 25 parole).")
    n = len(list(OUT.glob("lotto_*.ids")))
    for i in range(0, len(dubbi), 20):
        gruppo = dubbi[i:i + 20]
        n += 1
        parti = [f"# ISTRUZIONI\n\n{istruzioni}\n\nScrivi il file JSON {{\"risposte\": [{{\"annuncio_id\": 123, \"stesso\": true, "
                 f"\"motivo\": \"...\"}}]}} con una risposta per ogni coppia.\n"]
        for d in gruppo:
            parti.append(f"\n---\n\n## COPPIA annuncio_id = {d['annuncio_id']}\n\n" + ia.riempi(modello, {
                "titolo_annuncio": d["titolo"], "fonte_annuncio": d["fonte"], "ente_annuncio": d["ente"],
                "url_annuncio": d["url"], "testo_annuncio": (d["riassunto"] or "")[:2500],
                "titolo_bando": d["bando_titolo"], "ente_bando": d["bando_ente"], "url_bando": d["bando_url"],
                "testo_bando": (d["bando_sintesi"] or d["bando_riassunto"] or "")[:2500]}))
        (OUT / f"lotto_{n:03d}.md").write_text("".join(parti))
        (OUT / f"lotto_{n:03d}.ids").write_text(" ".join(str(d["annuncio_id"]) for d in gruppo))
    print(f"coppie da decidere: {len(dubbi)}; lotti scritti: {(len(dubbi) + 19) // 20}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
