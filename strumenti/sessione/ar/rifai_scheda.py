"""Rifa' solo la scheda (non il controllo preliminare) di alcuni bandi, con i documenti di adesso. Uso: rifai_scheda.py ID ...
Sposta il vecchio fascicolo, scrive il nuovo scheda.md e il preliminare.json dal database (cosi' la coda li da' alla
Fase B), e azzera `dati` nel database (la versione precedente resta nello storico; completezza resta finche' la
scheda nuova non arriva, quindi il bando non sparisce dal catalogo)."""
import json
import os
import shutil
import sys
import textwrap
import time
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
    os.umask(0)
    ids = [int(x) for x in sys.argv[1:] if x.isdigit()]
    _, mod_scheda = ia.leggi_prompt("prompt_scheda.md")
    oggi = date.today()
    fatti = []
    prenotati = OUT / "prenotati.txt"
    togli = set()
    with connetti() as conn:
        for bando_id in ids:
            with conn.cursor() as cur:
                cur.execute("SELECT * FROM bandi WHERE id = %s AND preliminare IS NOT NULL", (bando_id,))
                b = cur.fetchone()
            if not b:
                continue
            b = dict(b)
            cartella = OUT / "fascicoli" / str(bando_id)
            if cartella.exists():
                (OUT / "fascicoli_vecchi").mkdir(exist_ok=True)
                shutil.move(str(cartella), str(OUT / "fascicoli_vecchi" / f"{bando_id}_lungo_{int(time.time())}"))
            cartella.mkdir(parents=True)
            documenti, avvertenze = ia.documenti_del_bando(conn, bando_id, ia.MASSIMO_TESTO_SCHEDA)
            with conn.cursor() as cur:
                cur.execute("SELECT id, titolo FROM annunci WHERE bando_id = %s", (bando_id,))
                collegati = "; ".join(f"{x['id']} {x['titolo'][:80]}" for x in cur.fetchall())
            scheda = ia.riempi(mod_scheda, {
                "data_oggi": oggi.isoformat(), "titolo": b["titolo"], "ente": b["ente"], "territorio": b["territorio"],
                "url": b["url"], "pagina_motivo": b.get("pagina_motivo"), "annunci": collegati,
                "avvertenze_documenti": "\n".join(f"- {a}" for a in avvertenze) or "- nessuna", "documenti": documenti})
            (cartella / "scheda.md").write_text(spezza(scheda))
            (cartella / "preliminare.md").write_text("(controllo preliminare gia' fatto)\n")
            (cartella / "preliminare.json").write_text(json.dumps(b["preliminare"], ensure_ascii=False))
            with conn.cursor() as cur:
                cur.execute("SELECT set_config('bandi_radar.causa', 'scheda da rifare: testo dei documenti non piu'' tagliato', true)")
                cur.execute("UPDATE bandi SET dati = NULL WHERE id = %s", (bando_id,))
            conn.commit()
            fatti.append(bando_id)
            togli |= {f"A{bando_id}", f"B{bando_id}"}
    righe = [" ".join(x for x in r.split() if x not in togli) for r in prenotati.read_text().splitlines()]
    prenotati.write_text("\n".join(r for r in righe if r) + "\n")
    print(f"schede da rifare: {len(fatti)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
