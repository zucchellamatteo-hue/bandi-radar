"""Campione per verificare a mano la qualita' delle schede: N bandi proponibili aperti a caso.
Per ognuno scrive /out/verifica/<id>/scheda.json (campi principali) e documenti.txt (i testi usati).
Uso: esporta_verifica.py N"""
import json
import os
import sys
from pathlib import Path

from app.db.connessione import connetti

OUT = Path("/out/verifica")


def main() -> int:
    os.umask(0)
    n = int(sys.argv[1]) if len(sys.argv) > 1 else 20
    with connetti() as conn, conn.cursor() as cur:
        cur.execute("""SELECT id, titolo, ente, territorio, url, stato, data_apertura::text, scadenza::text, sintesi,
                              a_chi_si_rivolge, cosa_finanzia, tipo_agevolazione, contributo_massimo, percentuale,
                              codici_ateco, dimensioni_ammesse, dati->'risposta' AS risposta_completa, dati->>'modello' AS autore
                       FROM bandi WHERE completezza = 'bando_ufficiale' AND stato IN ('aperto','prorogato','in_arrivo')
                       ORDER BY md5(id::text || 'verifica-02-10') LIMIT %s""", (n,))
        righe = cur.fetchall()
        for r in righe:
            d = OUT / str(r["id"])
            d.mkdir(parents=True, exist_ok=True)
            (d / "scheda.json").write_text(json.dumps(dict(r), ensure_ascii=False, indent=1, default=str))
            cur.execute("""SELECT nome, url, testo_estratto FROM allegati WHERE bando_id = %s AND errore IS NULL
                           AND testo_estratto IS NOT NULL ORDER BY id""", (r["id"],))
            parti = [f"===== {nome} ({url})\n{testo}" for nome, url, testo in (tuple(x.values()) for x in cur.fetchall())]
            (d / "documenti.txt").write_text("\n\n".join(parti))
        print("esportati", len(righe), [r["id"] for r in righe])
    return 0


if __name__ == "__main__":
    sys.exit(main())
