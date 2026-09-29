"""Arretrato del 28/09: lotti di annunci "da rivedere" per lo smistamento nella sessione (Opus, senza API).
Stesso messaggio del programma (ia.messaggio_smistamento, con l'inizio della pagina per chi non ha riassunto),
lotti da 20. Prima le fonti che contano: UE, nazionali, Camere, Regioni (esclusi i servizi myCIVIS di Bolzano).
  /out/smista/lotto_NNN.md    istruzioni + messaggio;   /out/smista/lotto_NNN.ids   gli id del lotto
"""
import os
import sys
import textwrap
from datetime import date
from pathlib import Path

from app.db.connessione import connetti
from app.schede import ia

OUT = Path("/out/smista")
TIPI = ("ue", "nazionale", "camera", "regione", "capoluogo", "provincia")
ESCLUSE = ("bolzano_civis_servizi",)
LIMITE = 5000


def spezza(testo: str) -> str:
    righe = []
    for r in testo.splitlines():
        righe.extend(textwrap.wrap(r, 180, break_long_words=True, replace_whitespace=False) or [""])
    return "\n".join(righe) + "\n"


def main() -> int:
    os.umask(0)
    OUT.mkdir(parents=True, exist_ok=True)
    with connetti() as conn, conn.cursor() as cur:
        cur.execute(
            """SELECT a.id, a.titolo, coalesce(a.riassunto, '') AS riassunto, a.url, f.ente, f.tipo AS tipo_fonte, f.territorio
               FROM annunci a JOIN smistamenti s ON s.annuncio_id = a.id JOIN fonti f ON f.id = a.fonte_id
               WHERE s.esito = 'da_rivedere' AND s.deciso_da = 'regole' AND f.tipo = ANY(%s) AND NOT (f.id = ANY(%s))
               ORDER BY array_position(%s, f.tipo), a.id""", (list(TIPI), list(ESCLUSE), list(TIPI)))
        annunci = [dict(r) for r in cur.fetchall()]
    fatti = {p.stem for p in OUT.glob("lotto_*.ids")}
    gia = {int(x) for p in OUT.glob("lotto_*.ids") for x in p.read_text().split()}
    annunci = [a for a in annunci if a["id"] not in gia]
    print(f"annunci da smistare: {len(annunci)}", flush=True)
    annunci = annunci[:LIMITE]   # 29/09: meta' dell'arretrato; senza scaricare l'inizio delle pagine (troppo lento)
    oggi = date.today()
    n0 = len(fatti)
    for n, lotto in enumerate(ia.lotti(annunci), start=n0):
        istruzioni, messaggio = ia.messaggio_smistamento(lotto, oggi)
        (OUT / f"lotto_{n:03d}.md").write_text(spezza("# ISTRUZIONI DI SISTEMA\n\n" + istruzioni + "\n\n# MESSAGGIO\n\n" + messaggio))
        (OUT / f"lotto_{n:03d}.ids").write_text(" ".join(str(a["id"]) for a in lotto) + "\n")
    print(f"lotti scritti: {len(ia.lotti(annunci))}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
