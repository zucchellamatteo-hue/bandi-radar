"""Arretrato del 28/09/2026: fascicoli per controllo preliminare e scheda, compilati nella sessione (Opus, senza API).

Stesse funzioni di app/schede/ia.py (prompt, documenti in ordine, tagli). In piu', come fara' il programma:
  - segnali di stato gratuiti (app/schede/segnali.py): i bandi con soli segnali di chiusura si fermano qui, con
    il preliminare scritto nel database (deciso_da: segnali), senza fascicolo;
  - fascicoli/<id>/aperto: i segnali dicono "aperto" (priorita' in coda) e contiene i motivi, per la seconda lettura.
"""

import json
import os
import sys
import textwrap
from datetime import date
from pathlib import Path

from app.db.connessione import connetti
from app.schede import ia
from app.schede.segnali import segnali_del_bando

OUT = Path("/out")


def spezza(testo: str) -> str:
    righe = []
    for r in testo.splitlines():
        righe.extend(textwrap.wrap(r, 180, break_long_words=True, replace_whitespace=False) or [""])
    return "\n".join(righe) + "\n"


def main() -> int:
    os.umask(0)
    oggi = date.today()
    istr_pre, mod_pre = ia.leggi_prompt("prompt_preliminare.md")
    istr_pre = ia.riempi(istr_pre, {"data_oggi": oggi.isoformat()})
    istr_scheda, mod_scheda = ia.leggi_prompt("prompt_scheda.md")
    (OUT / "istruzioni_preliminare.md").write_text(istr_pre + "\n")
    (OUT / "istruzioni_scheda.md").write_text(istr_scheda + "\n")
    nuovi = fermati = aperti = 0
    with connetti() as conn:
        with conn.cursor() as cur:
            # Dal 01/10 solo i bandi con il testo ufficiale tra i documenti (app/schede/documentazione.py).
            # Dal 02/10 anche i bandi gia' passati dal controllo preliminare (fatto dall'API) e in attesa della
            # scheda, e quelli con la scheda "da aggiornare" (documenti nuovi, proroghe): le schede si scrivono in
            # sessione finche' IA_SCHEDE_API non e' 1.
            cur.execute("""SELECT * FROM bandi WHERE pagina_stato = 'trovata' AND allegati_cercati_il IS NOT NULL
                           AND documentazione = 'bando'
                           AND unito_a IS NULL AND ((dati IS NULL) OR (dati IS NOT NULL AND da_aggiornare IS NOT NULL)) ORDER BY id""")
            bandi = [dict(r) for r in cur.fetchall()]
        for b in bandi:
            cartella = OUT / "fascicoli" / str(b["id"])
            in_lavorazione = (cartella / "scheda.md").exists() and not (cartella / "scheda.json").exists()
            if b["dati"] is None and (cartella / "scheda.md").exists():
                continue                      # gia' esportato: in lavorazione o da importare
            if b["dati"] is not None and in_lavorazione:
                continue                      # aggiornamento gia' esportato, l'agente ci sta lavorando
            if b["preliminare"] is not None:
                # anche i bandi solo non profit (07/10): in sessione si schedano, dopo quelli per imprese (coda.py)
                if not ia.passa_preliminare(b["preliminare"], non_profit=True)[0]:
                    continue
                if cartella.exists():
                    import shutil, time
                    (OUT / "fascicoli_vecchi").mkdir(exist_ok=True)
                    shutil.move(str(cartella), str(OUT / "fascicoli_vecchi" / f"{b['id']}_{int(time.time())}"))
                cartella.mkdir(parents=True)
                documenti, avvertenze = ia.documenti_del_bando(conn, b["id"], ia.MASSIMO_TESTO_SCHEDA)
                with conn.cursor() as cur:
                    cur.execute("SELECT id, titolo FROM annunci WHERE bando_id = %s", (b["id"],))
                    collegati = "; ".join(f"{x['id']} {x['titolo'][:80]}" for x in cur.fetchall())
                scheda = ia.riempi(mod_scheda, {
                    "data_oggi": oggi.isoformat(), "titolo": b["titolo"], "ente": b["ente"], "territorio": b["territorio"],
                    "url": b["url"], "pagina_motivo": b.get("pagina_motivo"), "annunci": collegati,
                    "avvertenze_documenti": "\n".join(f"- {a}" for a in avvertenze) or "- nessuna", "documenti": documenti})
                (cartella / "preliminare.md").write_text("(controllo preliminare gia' fatto)\n")
                (cartella / "preliminare.json").write_text(json.dumps(b["preliminare"], ensure_ascii=False))
                (cartella / "scheda.md").write_text(spezza(scheda))
                nuovi += 1
                continue
            if (cartella / "scheda.md").exists():
                continue
            s = segnali_del_bando(conn, b["id"], oggi)
            if s.stato == "chiuso":
                pre = ia.preliminare_dai_segnali(s)   # con chi e quando (deciso_da, deciso_il), come nel sistema
                with conn.cursor() as cur:
                    cur.execute("SELECT set_config('bandi_radar.causa', 'controllo preliminare: segnali gratuiti', true)")
                    cur.execute("UPDATE bandi SET preliminare = %s WHERE id = %s AND preliminare IS NULL",
                                (json.dumps(pre), b["id"]))
                conn.commit()
                fermati += 1
                continue
            cartella.mkdir(parents=True, exist_ok=True)
            if s.aperto:
                (cartella / "aperto").write_text("; ".join(s.aperto) + "\n")
                aperti += s.stato == "aperto"
            corti = ia.documenti_preliminare(conn, b["id"])
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
    print(f"bandi pronti: {len(bandi)}; fermati dai segnali (senza IA): {fermati}; fascicoli nuovi: {nuovi}, "
          f"di cui con segnali 'aperto': {aperti}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
