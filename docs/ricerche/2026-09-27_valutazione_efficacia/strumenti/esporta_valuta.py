"""Pacchetti per la valutazione dell'efficacia, una cartella per fonte del campione (26/09/2026).

/out/valuta/fonti/<fonte>/
  smistamento.md   istruzioni + messaggio di smistamento, esattamente come li manderebbe app/schede/ia.py
                   (con l'inizio della pagina per gli annunci senza riassunto), su un campione di annunci della fonte
  preliminare_<bando>.md  -> si usano i fascicoli gia' pronti in /out/fascicoli/<bando>/ (qui solo l'elenco)
  bandi.json       bandi della fonte da valutare (al massimo 8): id, titolo, pagina, percorsi dei fascicoli
  radar.json       SOLO per il controllore: tutto quello che Bandi Radar sa della fonte (annunci, esiti, bandi)
Solo lettura del database; poche richieste di rete (inizio pagina), con le buone maniere del programma.
"""
import json
import os
import sys
from datetime import date
from pathlib import Path

from app.db.connessione import connetti
from app.schede import ia

OUT = Path("/out/valuta/fonti")
FASCICOLI = Path("/out/fascicoli")


def main() -> int:
    os.umask(0)
    campione = json.loads(Path("/out/valuta/campione_fonti.json").read_text())
    oggi = date.today()
    with connetti() as conn:
        for f in campione:
            cartella = OUT / f["id"]
            if (cartella / "radar.json").exists():
                continue
            cartella.mkdir(parents=True, exist_ok=True)
            with conn.cursor() as cur:
                cur.execute("""SELECT a.id, a.titolo, coalesce(a.riassunto, '') AS riassunto, a.url, a.pubblicato_il,
                                      a.trovato_il, a.bando_id, a.ruolo, s.esito, s.motivo, s.deciso_da
                               FROM annunci a LEFT JOIN smistamenti s ON s.annuncio_id = a.id
                               WHERE a.fonte_id = %s ORDER BY coalesce(a.pubblicato_il, a.trovato_il) DESC""", (f["id"],))
                annunci = [dict(r) for r in cur.fetchall()]
                cur.execute("SELECT ente, tipo, territorio FROM fonti WHERE id = %s", (f["id"],))
                fonte = dict(cur.fetchone())
            # campione per lo smistamento: rilevanti, da rivedere, non rilevanti, non smistati (i piu' recenti)
            quote = {"rilevante": 12, "da_rivedere": 8, "non_rilevante": 8, None: 4}
            scelti = []
            for esito, n in quote.items():
                scelti += [a for a in annunci if a["esito"] == esito][:n]
            scelti.sort(key=lambda a: a["id"])
            per_prompt = [{"id": a["id"], "titolo": a["titolo"], "riassunto": a["riassunto"][:1500], "url": a["url"],
                           "ente": fonte["ente"], "tipo_fonte": fonte["tipo"], "territorio": fonte["territorio"]}
                          for a in scelti]
            if per_prompt:
                ia.aggiungi_inizio_pagina(per_prompt)
                istruzioni, messaggio = ia.messaggio_smistamento(per_prompt, oggi)
                (cartella / "smistamento.md").write_text(
                    "# ISTRUZIONI DI SISTEMA\n\n" + istruzioni + "\n\n# MESSAGGIO\n\n" + messaggio + "\n")
            # bandi della fonte: prima quelli con scheda, poi quelli fermati dal preliminare, poi gli altri
            ids = sorted({a["bando_id"] for a in annunci if a["bando_id"]})
            bandi = []
            if ids:
                with conn.cursor() as cur:
                    cur.execute("""SELECT id, titolo, url, pagina_stato, pagina_motivo, stato, data_apertura, scadenza,
                                          completezza, preliminare, (dati IS NOT NULL) AS ha_scheda
                                   FROM bandi WHERE id = ANY(%s)""", (ids,))
                    bandi = [dict(r) for r in cur.fetchall()]
            bandi.sort(key=lambda b: (not b["ha_scheda"], b["preliminare"] is None, b["id"]))
            da_valutare = []
            for b in bandi:
                fasc = FASCICOLI / str(b["id"])
                if len(da_valutare) >= 8:
                    break
                da_valutare.append({
                    "id": b["id"], "titolo": b["titolo"], "pagina": b["url"], "pagina_stato": b["pagina_stato"],
                    "fascicolo_preliminare": str(fasc / "preliminare.md") if (fasc / "preliminare.md").exists() else None,
                    "fascicolo_scheda": str(fasc / "scheda.md") if (fasc / "scheda.md").exists() else None,
                    "ha_scheda": b["ha_scheda"]})
            (cartella / "bandi.json").write_text(json.dumps(da_valutare, indent=1, ensure_ascii=False, default=str))
            radar = {"fonte": {**f, **fonte}, "annunci_nel_campione_smistamento": [a["id"] for a in scelti],
                     "annunci": [{k: a[k] for k in ("id", "titolo", "url", "pubblicato_il", "trovato_il", "bando_id",
                                                    "ruolo", "esito", "motivo", "deciso_da")} for a in annunci[:400]],
                     "bandi": bandi}
            (cartella / "radar.json").write_text(json.dumps(radar, indent=1, ensure_ascii=False, default=str))
            print(f"{f['id']}: {len(annunci)} annunci, {len(scelti)} nel campione, {len(bandi)} bandi ({len(da_valutare)} da valutare)",
                  flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
