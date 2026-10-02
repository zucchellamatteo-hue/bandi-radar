"""Rilegge dal disco i documenti il cui testo era stato tagliato a 200.000 caratteri (02/10/2026), con il limite nuovo
(app/schede/allegati.MASSIMO_TESTO). Nessuno scaricamento. Stampa i bandi proponibili e aperti toccati."""
import sys
from pathlib import Path

from app.db.connessione import connetti
from app.schede.allegati import CARTELLA, estrai_testo


def main() -> int:
    toccati, n = set(), 0
    with connetti() as conn:
        with conn.cursor() as cur:
            cur.execute("""SELECT a.id, a.bando_id, a.tipo, a.percorso_locale, length(a.testo_estratto) AS prima,
                                  (b.completezza = 'bando_ufficiale' AND b.stato IN ('aperto', 'in_arrivo')) AS importante
                           FROM allegati a JOIN bandi b ON b.id = a.bando_id
                           WHERE length(a.testo_estratto) >= 199990 AND a.percorso_locale IS NOT NULL""")
            righe = [dict(r) for r in cur.fetchall()]
        for r in righe:
            percorso = Path(CARTELLA) / r["percorso_locale"]
            if not percorso.exists():
                continue
            testo = estrai_testo(percorso, r["tipo"])
            if testo and len(testo) > r["prima"]:
                with conn.cursor() as cur:
                    cur.execute("UPDATE allegati SET testo_estratto = %s WHERE id = %s", (testo, r["id"]))
                conn.commit()
                n += 1
                if r["importante"]:
                    toccati.add(r["bando_id"])
    print(f"documenti riletti: {n} su {len(righe)}")
    print("BANDI", " ".join(map(str, sorted(toccati))))
    return 0


if __name__ == "__main__":
    sys.exit(main())
