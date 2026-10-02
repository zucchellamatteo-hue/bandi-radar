"""Forma dell'incentivo (02/10/2026) per le schede gia' scritte: solo quel blocco, letto dai documenti.

Per ogni bando proponibile aperto o in arrivo senza `forma_incentivo` compilata scrive /out/forma/<id>/:
  - scheda.json: i campi della scheda che servono (tipi, percentuali, massimali, finanziamento, intensita', linee)
    e la versione ricavata dai campi (app/schede/forma_incentivo.py), da controllare e correggere;
  - documenti.txt: i testi dei documenti, come per la scheda (ia.documenti_del_bando).
Le istruzioni per gli agenti sono in /out/forma/ISTRUZIONI.md. Uso: esporta_forma.py [N] [id ...]"""
import json
import os
import sys
from pathlib import Path

from app.db.connessione import connetti
from app.schede import forma_incentivo, ia

OUT = Path("/out/forma")
CAMPI = ("id", "titolo", "ente", "tipo_agevolazione", "tipi_agevolazione", "contributo_massimo", "percentuale",
         "fondo_perduto_massimo", "percentuale_fondo_perduto", "finanziamento_massimo", "spesa_minima", "spesa_massima",
         "intensita", "finanziamento", "linee", "sintesi")


def main() -> int:
    os.umask(0)
    numeri = [int(x) for x in sys.argv[1:] if x.isdigit()]
    limite = numeri[0] if len(numeri) == 1 else 10000
    ids = numeri if len(numeri) > 1 else None
    with connetti() as conn:
        with conn.cursor() as cur:
            if ids:
                cur.execute("SELECT * FROM bandi WHERE id = ANY(%s) ORDER BY id", (ids,))
            else:
                cur.execute("""SELECT * FROM bandi WHERE completezza = 'bando_ufficiale'
                               AND stato IN ('aperto', 'prorogato', 'in_arrivo')
                               AND (forma_incentivo IS NULL OR forma_incentivo->'righe' = '[]'::jsonb)
                               ORDER BY scadenza NULLS LAST, id LIMIT %s""", (limite,))
            bandi = [dict(r) for r in cur.fetchall()]
        fatti = []
        for b in bandi:
            d = OUT / str(b["id"])
            if (d / "forma.json").exists():
                continue
            d.mkdir(parents=True, exist_ok=True)
            dati = {c: b.get(c) for c in CAMPI}
            dati["ricavata"] = forma_incentivo.ricava(b)
            (d / "scheda.json").write_text(json.dumps(dati, ensure_ascii=False, indent=1, default=str))
            documenti, _ = ia.documenti_del_bando(conn, b["id"], ia.MASSIMO_TESTO_SCHEDA)
            (d / "documenti.txt").write_text("\n\n".join(f"===== {x.get('nome')}\n{x.get('testo')}" for x in documenti))
            fatti.append(b["id"])
    print("esportati", len(fatti), fatti[:50])
    return 0


if __name__ == "__main__":
    sys.exit(main())
