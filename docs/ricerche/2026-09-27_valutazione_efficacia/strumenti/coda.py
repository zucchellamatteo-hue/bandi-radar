"""Cosa resta da fare sui fascicoli. Uso: python3 coda.py A 25   |   python3 coda.py B 5   |   python3 coda.py conta
A: id senza preliminare.json (gruppi da N). B: id con preliminare che passa e senza scheda.json (gruppi da N,
dai piu' corti). Stampa un gruppo per riga."""
import json
import sys
from pathlib import Path

F = Path("/tmp/claude-1000/sp/schede/fascicoli")
PRENOTATI = Path("/tmp/claude-1000/sp/prenotati.txt")


def passa(p):
    return not (p.get("per_imprese") == "no" or p.get("edizione_in_corso") == "no" or p.get("stato") == "chiuso"
                or p.get("testo_bando") == "no")


prenotati = set(PRENOTATI.read_text().split()) if PRENOTATI.exists() else set()
a, b, fatti, fermati, rotti = [], [], 0, 0, 0
for d in sorted(F.iterdir(), key=lambda p: int(p.name)):
    pj = d / "preliminare.json"
    if not (d / "scheda.md").exists():
        continue
    if not pj.exists():
        a.append(d.name)
        continue
    try:
        p = json.loads(pj.read_text())
    except json.JSONDecodeError:
        rotti += 1
        continue
    if not passa(p) and not (d / "forza").exists():
        fermati += 1
    elif (d / "scheda.json").exists():
        fatti += 1
    else:
        b.append(d.name)

modo = sys.argv[1]
if modo == "conta":
    print(f"fascicoli {len(list(F.iterdir()))}; senza preliminare {len(a)}; fermati {fermati}; "
          f"schede fatte {fatti}; schede da fare {len(b)}; preliminari rotti {rotti}; prenotati {len(prenotati)}")
    sys.exit()
n = int(sys.argv[2])
ids = a if modo == "A" else [x for x in b if f"B{x}" not in prenotati]
if modo == "B":
    ids.sort(key=lambda x: (F / x / "scheda.md").stat().st_size)
gruppi = [ids[i:i + n] for i in range(0, len(ids), n)]
limite = int(sys.argv[3]) if len(sys.argv) > 3 else len(gruppi)
with PRENOTATI.open("a") as f:
    for g in gruppi[:limite]:
        print(", ".join(g))
        f.write(" ".join(f"{modo}{x}" for x in g) + "\n")
