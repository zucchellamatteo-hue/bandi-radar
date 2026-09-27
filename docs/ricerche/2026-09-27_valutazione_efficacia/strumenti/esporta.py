"""Prepara i fascicoli per le schede compilate nella sessione di Claude Code del 26/09/2026 (senza API).

Usa esattamente le funzioni di app/schede/ia.py: stessi prompt, stessi documenti in ordine, stessi tagli.
Per ogni bando con pagina trovata, allegati cercati, senza scheda e senza controllo preliminare:
  /out/fascicoli/<id>/preliminare.md   messaggio del controllo preliminare (inizio dei documenti)
  /out/fascicoli/<id>/scheda.md        messaggio per la scheda (documenti completi)
Le istruzioni (uguali per tutti) vanno in /out/istruzioni_preliminare.md e /out/istruzioni_scheda.md.
Le righe lunghe si spezzano a 180 caratteri (solo per poterle leggere a pezzi, il testo non cambia).
Solo lettura del database.
"""

import os
import sys
import textwrap
from datetime import date
from pathlib import Path

from app.db.connessione import connetti
from app.schede import ia

OUT = Path("/out")


def spezza(testo: str) -> str:
    righe = []
    for r in testo.splitlines():
        righe.extend(textwrap.wrap(r, 180, break_long_words=True, replace_whitespace=False) or [""])
    return "\n".join(righe) + "\n"


def main() -> int:
    os.umask(0)   # gli agenti (utente ubuntu) devono poter scrivere i .json nelle cartelle create qui
    oggi = date.today()
    istr_pre, mod_pre = ia.leggi_prompt("prompt_preliminare.md")
    istr_pre = ia.riempi(istr_pre, {"data_oggi": oggi.isoformat()})
    istr_scheda, mod_scheda = ia.leggi_prompt("prompt_scheda.md")
    (OUT / "istruzioni_preliminare.md").write_text(istr_pre + "\n")
    (OUT / "istruzioni_scheda.md").write_text(istr_scheda + "\n")
    nuovi = 0
    with connetti() as conn:
        with conn.cursor() as cur:
            cur.execute("""SELECT * FROM bandi WHERE pagina_stato = 'trovata' AND allegati_cercati_il IS NOT NULL
                           AND dati IS NULL AND preliminare IS NULL ORDER BY id""")
            bandi = [dict(r) for r in cur.fetchall()]
        for b in bandi:
            cartella = OUT / "fascicoli" / str(b["id"])
            if (cartella / "scheda.md").exists():
                continue
            cartella.mkdir(parents=True, exist_ok=True)
            corti, _ = ia.documenti_del_bando(conn, b["id"], ia.MASSIMO_TESTO_PRELIMINARE)
            pre = ia.riempi(mod_pre, {"data_oggi": oggi.isoformat(), "titolo": b["titolo"], "url": b["url"],
                                      "documenti": corti})
            documenti, avvertenze = ia.documenti_del_bando(conn, b["id"], ia.MASSIMO_TESTO_SCHEDA)
            with conn.cursor() as cur:
                cur.execute("SELECT id, titolo FROM annunci WHERE bando_id = %s", (b["id"],))
                collegati = "; ".join(f"{x['id']} {x['titolo'][:80]}" for x in cur.fetchall())
            scheda = ia.riempi(mod_scheda, {
                "data_oggi": oggi.isoformat(), "titolo": b["titolo"], "ente": b["ente"], "territorio": b["territorio"],
                "url": b["url"], "pagina_motivo": b.get("pagina_motivo"), "annunci": collegati,
                "avvertenze_documenti": "\n".join(f"- {a}" for a in avvertenze) or "- nessuna", "documenti": documenti})
            (cartella / "preliminare.md").write_text(spezza(pre))
            (cartella / "scheda.md").write_text(spezza(scheda))
            nuovi += 1
    print(f"bandi pronti: {len(bandi)}; fascicoli nuovi: {nuovi}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
