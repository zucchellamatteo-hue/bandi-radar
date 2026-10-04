"""Campione per verificare a mano la qualita' delle schede: N bandi proponibili aperti a caso, piu' id dati a mano.
Per ognuno scrive /out/verifica/<seme>/<id>/scheda.json (campi principali) e documenti.txt (i testi usati).
Uso: esporta_verifica.py N [seme] [id ...]   (02/10: seme 'verifica-02-10'; dal 03/10 esclusi i "non per imprese")"""
import json
import os
import sys
from pathlib import Path

from app.db.connessione import connetti

CAMPI = """id, titolo, ente, territorio, url, stato, data_apertura::text, scadenza::text, sintesi,
           a_chi_si_rivolge, cosa_finanzia, tipo_agevolazione, contributo_massimo, percentuale,
           codici_ateco, dimensioni_ammesse, territorio_regioni, preliminare->>'per_imprese' AS per_imprese,
           dati->'risposta' AS risposta_completa, dati->>'modello' AS autore, scheda_il::text"""


def main() -> int:
    os.umask(0)
    n = int(sys.argv[1]) if len(sys.argv) > 1 else 20
    seme = sys.argv[2] if len(sys.argv) > 2 else "verifica-02-10"
    extra = [int(x) for x in sys.argv[3:] if x.isdigit()]
    out = Path("/out/verifica") / seme
    with connetti() as conn, conn.cursor() as cur:
        cur.execute(f"""SELECT {CAMPI} FROM bandi WHERE completezza = 'bando_ufficiale'
                        AND stato IN ('aperto','prorogato','in_arrivo') AND dati IS NOT NULL
                        AND coalesce(preliminare->>'per_imprese', '') <> 'no'
                        ORDER BY md5(id::text || %s) LIMIT %s""", (seme, n))
        righe = list(cur.fetchall())
        cur.execute(f"SELECT {CAMPI} FROM bandi WHERE id = ANY(%s)", (extra,))
        righe += [r for r in cur.fetchall() if r["id"] not in {x["id"] for x in righe}]
        for r in righe:
            d = out / str(r["id"])
            d.mkdir(parents=True, exist_ok=True)
            (d / "scheda.json").write_text(json.dumps(dict(r), ensure_ascii=False, indent=1, default=str))
            cur.execute("""SELECT nome, url, testo_estratto FROM allegati WHERE bando_id = %s AND errore IS NULL
                           AND testo_estratto IS NOT NULL ORDER BY id""", (r["id"],))
            parti = [f"===== {x['nome']} ({x['url']})\n{x['testo_estratto']}" for x in cur.fetchall()]
            (d / "documenti.txt").write_text("\n\n".join(parti))
        print("esportati", len(righe), [r["id"] for r in righe])
    return 0


if __name__ == "__main__":
    sys.exit(main())
