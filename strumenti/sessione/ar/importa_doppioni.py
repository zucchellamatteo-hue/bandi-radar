"""Applica le decisioni sui doppioni prese in sessione (lotti in /out/doppioni). Come l'IA del regista: da = 'ia'.
Salta le coppie gia' decise nel frattempo (dal regista o da Matteo)."""
import json
import sys
from pathlib import Path

from app.catena.regista import evento
from app.db.connessione import connetti
from app.schede.bandi import decidi_collegamento

OUT = Path("/out/doppioni")


def main() -> int:
    conteggi = {"stesso": 0, "diverso": 0, "gia_decisi": 0, "rotti": 0}
    with connetti() as conn:
        for fj in sorted(OUT.glob("lotto_*.json")):
            if (OUT / (fj.stem + ".importato")).exists():
                continue
            try:
                risposte = json.loads(fj.read_text())["risposte"]
            except (json.JSONDecodeError, KeyError):
                print(f"{fj.name}: JSON non valido")
                conteggi["rotti"] += 1
                continue
            ids = {int(x) for x in (OUT / (fj.stem + ".ids")).read_text().split()}
            for r in risposte:
                a = int(r.get("annuncio_id", 0))
                if a not in ids:
                    continue
                with conn.cursor() as cur:
                    cur.execute("""SELECT bando_id FROM bandi_dubbi WHERE annuncio_id = %s AND decisione IS NULL
                                   ORDER BY somiglianza DESC NULLS LAST LIMIT 1""", (a,))
                    riga = cur.fetchone()
                if not riga:
                    conteggi["gia_decisi"] += 1
                    continue
                stesso = bool(r.get("stesso"))
                motivo = "IA (sessione): " + str(r.get("motivo") or "")[:200]
                bando = decidi_collegamento(conn, a, riga["bando_id"] if stesso else None, "ia", motivo)
                with conn.cursor() as cur:
                    evento(cur, "annuncio", a, "doppione", f"{'stesso' if stesso else 'diverso'} (ia)", f"bando {bando}: {motivo}")
                conn.commit()
                conteggi["stesso" if stesso else "diverso"] += 1
            (OUT / (fj.stem + ".importato")).write_text("")
    print(conteggi)
    return 0


if __name__ == "__main__":
    sys.exit(main())
