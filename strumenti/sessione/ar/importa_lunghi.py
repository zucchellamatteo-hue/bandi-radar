"""Salva le schede dei bandi lunghissimi scritte in due passaggi (/out/lunghi/<id>/scheda.json), con la stessa pulizia
e gli stessi controlli delle altre schede (ia.prepara_scheda, ia.verifica_scheda sui documenti completi). La versione
precedente resta nello storico. Uso: importa_lunghi.py [--prova]"""
import json
import sys
from pathlib import Path

from app.db.connessione import connetti
from app.schede import ia
from app.schede.stato import aggiorna_stati

OUT = Path("/out/lunghi")
MODELLO = "claude-code (sessione del 06/10/2026, scheda in due passaggi, senza API)"
CAUSA = "scheda rifatta in due passaggi (bando lunghissimo: indice dei documenti, poi gli articoli che servono)"


def main() -> int:
    prova = "--prova" in sys.argv
    fatti = OUT / "importati.txt"
    gia = set(fatti.read_text().split()) if fatti.exists() else set()
    with connetti() as conn:
        for cartella in sorted(p for p in OUT.iterdir() if p.is_dir() and p.name.isdigit()):
            fs = cartella / "scheda.json"
            if cartella.name in gia or not fs.exists():
                continue
            bando_id = int(cartella.name)
            try:
                grezza = json.loads(fs.read_text())
            except json.JSONDecodeError as exc:
                print(f"[{bando_id}] scheda.json non valido: {exc}")
                continue
            with conn.cursor() as cur:
                cur.execute("SELECT url FROM bandi WHERE id = %s", (bando_id,))
                b = cur.fetchone()
                cur.execute("""SELECT nome, url, tipo, categoria, testo_estratto, testo_estratto AS testo, errore FROM allegati
                               WHERE bando_id = %s AND annuncio_id IS NULL""", (bando_id,))
                documenti = [dict(r) for r in cur.fetchall()]
            scheda, tolti = ia.prepara_scheda(grezza)
            scheda["url"] = scheda.get("url") or b["url"]
            problemi = tolti + ia.verifica_scheda(scheda, documenti)
            print(f"[{bando_id}] {len(problemi)} problemi: {'; '.join(problemi)[:400]}")
            if prova:
                continue
            valori = {c: scheda.get(c) for c in ia._COLONNE_SCHEDA}
            for c in ("vincoli", "linee", *ia._DETTAGLI_SCHEDA):
                valori[c] = json.dumps(valori[c]) if valori[c] is not None else None
            dati = {"risposta": scheda, "problemi": problemi, "costo_usd": 0, "modello": MODELLO,
                    "fonti": {f["campo"]: f["fonte"] for f in scheda.get("fonti") or [] if isinstance(f, dict) and "campo" in f},
                    "avvertenze": scheda.get("avvertenze") or []}
            with conn.cursor() as cur:
                cur.execute("SELECT set_config('bandi_radar.causa', %s, true)", (CAUSA,))
                cur.execute(f"UPDATE bandi SET {', '.join(f'{c} = %s' for c in valori)}, dati = %s, scheda_il = now(), "
                            "da_aggiornare = NULL WHERE id = %s", (*valori.values(), json.dumps(dati), bando_id))
            conn.commit()
            with fatti.open("a") as f:
                f.write(f"{bando_id}\n")
        if not prova:
            print(f"stati cambiati: {aggiorna_stati(conn)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
