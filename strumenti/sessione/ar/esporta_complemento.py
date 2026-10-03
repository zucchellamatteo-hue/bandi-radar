"""Punti 4 e 6 del piano del 03/10, per le schede proponibili NON rifatte da capo: un solo passaggio degli agenti che
compila la forma dell'incentivo e, solo dove serve, i codici ATECO ricavati dalla descrizione dei settori e le
regioni/province scritte solo nel testo. Scrive /out/complemento/<id>/scheda.json e documenti.txt.
Uso: esporta_complemento.py [id ...]   (senza id: tutti i proponibili non chiusi che ne hanno bisogno)"""
import json
import os
import sys
from pathlib import Path

from app.db.connessione import connetti
from app.schede import forma_incentivo, ia

OUT = Path("/out/complemento")
CAMPI = ("id", "titolo", "ente", "territorio", "territorio_regioni", "territorio_province", "a_chi_si_rivolge",
         "requisiti", "codici_ateco", "codici_ateco_esclusi", "ateco_versione", "vincoli", "tipo_agevolazione",
         "tipi_agevolazione", "contributo_massimo", "percentuale", "fondo_perduto_massimo", "percentuale_fondo_perduto",
         "finanziamento_massimo", "spesa_minima", "spesa_massima", "intensita", "finanziamento", "linee", "sintesi")


def main() -> int:
    os.umask(0)
    ids = [int(x) for x in sys.argv[1:] if x.isdigit()]
    with connetti() as conn:
        with conn.cursor() as cur:
            cur.execute("""SELECT * FROM bandi WHERE completezza = 'bando_ufficiale' AND coalesce(stato, '') <> 'chiuso'
                           AND coalesce(preliminare->>'per_imprese', '') <> 'no' AND dati IS NOT NULL AND da_aggiornare IS NULL
                           AND (cardinality(%s::bigint[]) = 0 OR id = ANY(%s))
                           AND (forma_incentivo IS NULL OR forma_incentivo->'righe' = '[]'::jsonb
                                OR (vincoli->>'ateco' = 'vincolo' AND coalesce(cardinality(codici_ateco), 0) = 0)
                                OR (vincoli->>'territorio' = 'vincolo' AND coalesce(cardinality(territorio_regioni), 0) = 0
                                    AND coalesce(cardinality(territorio_province), 0) = 0))
                           ORDER BY id""", (ids, ids))
            bandi = [dict(r) for r in cur.fetchall()]
        fatti = []
        for b in bandi:
            d = OUT / str(b["id"])
            if (d / "complemento.json").exists():
                continue
            d.mkdir(parents=True, exist_ok=True)
            dati = {c: b.get(c) for c in CAMPI}
            vincoli = b.get("vincoli") or {}
            dati["serve"] = {
                "forma": not (b.get("forma_incentivo") or {}).get("righe"),
                "ateco": vincoli.get("ateco") == "vincolo" and not b.get("codici_ateco"),
                "territorio": vincoli.get("territorio") == "vincolo" and not b.get("territorio_regioni") and not b.get("territorio_province"),
            }
            dati["forma_ricavata"] = forma_incentivo.ricava(b)
            (d / "scheda.json").write_text(json.dumps(dati, ensure_ascii=False, indent=1, default=str))
            documenti, _ = ia.documenti_del_bando(conn, b["id"], ia.MASSIMO_TESTO_SCHEDA)
            (d / "documenti.txt").write_text("\n\n".join(f"===== {x.get('nome')}\n{x.get('testo')}" for x in documenti))
            fatti.append(b["id"])
    print("esportati", len(fatti), " ".join(map(str, fatti)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
