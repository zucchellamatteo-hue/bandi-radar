"""Schede da rifare dopo la rilettura OCR (29/09/2026). Uso (via ar.sh): rifai.py [--prova] ID ID ...

Per ogni bando: sposta il vecchio fascicolo in fascicoli_vecchi/, toglie le prenotazioni della coda, e nel database
azzera preliminare e scheda (la versione precedente resta in bandi_versioni) cosi' esporta.py rifa' il fascicolo con
il testo nuovo e importa.py puo' salvare la scheda nuova. Solo bandi non chiusi e con pagina ufficiale trovata.
"""

import shutil
import sys
import time
from pathlib import Path

from app.db.connessione import connetti

OUT = Path("/out")


def main() -> int:
    prova = "--prova" in sys.argv
    ids = [int(x) for x in sys.argv[1:] if x.isdigit()]
    fatti = []
    with connetti() as conn:
        for bando_id in ids:
            with conn.cursor() as cur:
                cur.execute("""SELECT id, stato, dati IS NOT NULL AS scheda, preliminare IS NOT NULL AS pre FROM bandi
                               WHERE id = %s AND pagina_stato = 'trovata' AND stato IS DISTINCT FROM 'chiuso'""", (bando_id,))
                b = cur.fetchone()
            if not b or not (b["scheda"] or b["pre"]):
                continue
            fatti.append(bando_id)
            if prova:
                continue
            vecchia = OUT / "fascicoli" / str(bando_id)
            if vecchia.exists():
                (OUT / "fascicoli_vecchi").mkdir(exist_ok=True)
                shutil.move(str(vecchia), str(OUT / "fascicoli_vecchi" / f"{bando_id}_{int(time.time())}"))
            with conn.cursor() as cur:
                cur.execute("SELECT set_config('bandi_radar.causa', 'testo dei PDF riletto con OCR: scheda da rifare', true)")
                cur.execute("UPDATE bandi SET preliminare = NULL, dati = NULL WHERE id = %s", (bando_id,))
            conn.commit()
    if not prova:
        prenotati = OUT / "prenotati.txt"
        togli = {f"{m}{i}" for i in fatti for m in "AB"}
        righe = [" ".join(x for x in r.split() if x not in togli) for r in prenotati.read_text().splitlines()]
        prenotati.write_text("\n".join(r for r in righe if r) + "\n")
    print(("PROVA: " if prova else "") + f"bandi da rifare: {len(fatti)}: {' '.join(map(str, fatti))}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
