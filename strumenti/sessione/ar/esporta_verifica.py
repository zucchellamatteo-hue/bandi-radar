"""Bandi da verificare con l'IA in sessione (secondo controllo, ISTRUZIONI_VERIFICA_IA.md).
Per ognuno scrive /out/verifica/<cartella>/<id>/scheda.json (campi principali) e documenti.txt (i testi usati).

Uso:
  esporta_verifica.py N [seme] [id ...]          N proponibili a caso (campione), piu' id dati a mano
  esporta_verifica.py --prossimi N CARTELLA      i prossimi N proponibili senza secondo controllo, scadenza piu' vicina
                                                 prima (08/10, procedura nuova del regista): esclusi quelli con
                                                 bandi.secondo_controllo e quelli gia' verificati in /out/verifica/*/
(02/10: seme 'verifica-02-10'; dal 03/10 esclusi i "non per imprese"; dal 08/10 i proponibili dalla situazione)"""
import json
import os
import sys
from pathlib import Path

from app.db.connessione import connetti

CAMPI = """b.id, b.titolo, b.ente, b.territorio, b.url, b.stato, b.data_apertura::text, b.scadenza::text, b.sintesi,
           b.a_chi_si_rivolge, b.cosa_finanzia, b.tipo_agevolazione, b.contributo_massimo, b.percentuale,
           b.codici_ateco, b.dimensioni_ammesse, b.territorio_regioni, b.preliminare->>'per_imprese' AS per_imprese,
           b.dati->'risposta' AS risposta_completa, b.dati->>'modello' AS autore, b.scheda_il::text"""


def gia_verificati() -> set[int]:
    return {int(p.parent.name) for p in Path("/out/verifica").glob("*/*/verifica_ia.json") if p.parent.name.isdigit()}


def scrivi(cur, righe: list[dict], out: Path) -> None:
    for r in righe:
        d = out / str(r["id"])
        d.mkdir(parents=True, exist_ok=True)
        (d / "scheda.json").write_text(json.dumps(dict(r), ensure_ascii=False, indent=1, default=str))
        cur.execute("""SELECT nome, url, testo_estratto FROM allegati WHERE bando_id = %s AND errore IS NULL
                       AND testo_estratto IS NOT NULL ORDER BY id""", (r["id"],))
        parti = [f"===== {x['nome']} ({x['url']})\n{x['testo_estratto']}" for x in cur.fetchall()]
        (d / "documenti.txt").write_text("\n\n".join(parti))


def main() -> int:
    os.umask(0)
    with connetti() as conn, conn.cursor() as cur:
        if sys.argv[1:2] == ["--prossimi"]:
            n, out = int(sys.argv[2]), Path("/out/verifica") / sys.argv[3]
            cur.execute("SELECT 1 FROM information_schema.columns WHERE table_name = 'bandi' AND column_name = 'secondo_controllo'")
            senza = "AND b.secondo_controllo IS NULL" if cur.fetchone() else ""
            cur.execute(f"""SELECT {CAMPI} FROM bandi_situazione s JOIN bandi b ON b.id = s.id
                            WHERE s.situazione = 'proponibile' {senza} AND NOT b.id = ANY(%s)
                            ORDER BY b.scadenza NULLS LAST, b.id LIMIT %s""", (sorted(gia_verificati()), n))
            righe = [dict(r) for r in cur.fetchall()]
        else:
            n = int(sys.argv[1]) if len(sys.argv) > 1 else 20
            seme = sys.argv[2] if len(sys.argv) > 2 else "verifica-02-10"
            extra = [int(x) for x in sys.argv[3:] if x.isdigit()]
            out = Path("/out/verifica") / seme
            cur.execute(f"""SELECT {CAMPI} FROM bandi_situazione s JOIN bandi b ON b.id = s.id
                            WHERE s.situazione = 'proponibile' ORDER BY md5(b.id::text || %s) LIMIT %s""", (seme, n))
            righe = [dict(r) for r in cur.fetchall()]
            cur.execute(f"SELECT {CAMPI} FROM bandi b WHERE b.id = ANY(%s)", (extra,))
            righe += [dict(r) for r in cur.fetchall() if r["id"] not in {x["id"] for x in righe}]
        scrivi(cur, righe, out)
        print("esportati", len(righe), [r["id"] for r in righe])
    return 0


if __name__ == "__main__":
    sys.exit(main())
