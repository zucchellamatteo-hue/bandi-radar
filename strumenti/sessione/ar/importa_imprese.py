"""Punto 2 del piano del 03/10: salva le decisioni "non per imprese" (/out/imprese/<id>.json): preliminare.per_imprese
= 'no' (il bando esce dai proponibili; la scheda resta nello storico) e un'avvertenza nella scheda. Uso: [--prova]"""
import json
import sys
from datetime import date
from pathlib import Path

from app.db.connessione import connetti

CART = Path("/out/imprese")
FATTI = CART / "importati.txt"


def main():
    prova = "--prova" in sys.argv
    fatti = set(FATTI.read_text().split()) if FATTI.exists() else set()
    conti = {}
    with connetti() as conn:
        for f in sorted(CART.glob("*.json"), key=lambda p: int(p.stem)):
            if f.stem in fatti:
                continue
            try:
                e = json.loads(f.read_text())
            except json.JSONDecodeError:
                print(f"[{f.stem}] json non valido")
                continue
            v = e.get("per_imprese")
            conti[v] = conti.get(v, 0) + 1
            if v == "no":
                bid = int(f.stem)
                print(f"[{bid}] NO: {e.get('motivo')}")
                if not prova:
                    with conn.cursor() as cur:
                        cur.execute("SELECT preliminare, dati FROM bandi WHERE id=%s", (bid,))
                        b = cur.fetchone()
                        pre = dict(b["preliminare"] or {})
                        pre["per_imprese"] = "no"
                        pre["motivo"] = ("Ricontrollo 03/10: non per imprese. " + (e.get("motivo") or ""))[:500]
                        dati = b["dati"] or {}
                        nota = (f"Ricontrollo dei beneficiari del {date.today():%d/%m/%Y}: non per imprese. "
                                f"{e.get('motivo') or ''} «{(e.get('citazione') or '')[:300]}»")
                        dati["avvertenze"] = [nota] + [a for a in (dati.get("avvertenze") or []) if not str(a).startswith("Ricontrollo dei beneficiari")]
                        cur.execute("SELECT set_config('bandi_radar.causa', 'ricontrollo dei beneficiari del 03/10: non per imprese', true)")
                        cur.execute("UPDATE bandi SET preliminare=%s, dati=%s WHERE id=%s", (json.dumps(pre), json.dumps(dati), bid))
                    conn.commit()
            if not prova:
                with FATTI.open("a") as out:
                    out.write(f"{f.stem}\n")
    print(("PROVA " if prova else "") + str(conti))


if __name__ == "__main__":
    main()
