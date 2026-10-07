"""Cosa resta da fare sui fascicoli. Uso: python3 coda.py A 25   |   python3 coda.py B 5   |   python3 coda.py conta
A: id senza preliminare.json (gruppi da N). B: id con preliminare che passa e senza scheda.json (gruppi da N,
prima quelli per imprese, poi i solo non profit; dai piu' corti). Stampa un gruppo per riga."""
import json
import sys
from pathlib import Path

F = Path("/tmp/claude-1000/ar/fascicoli")
PRENOTATI = Path("/tmp/claude-1000/ar/prenotati.txt")


IMPRESE = {"imprese"}


def non_profit(p):
    """Solo non profit (07/10): niente imprese tra i destinatari, ma associazioni, ETS, fondazioni... Come
    app/schede/ia.py (solo_non_profit): si schedano anche questi, dopo quelli per imprese."""
    d = p.get("destinatari")
    if isinstance(d, list) and "da_determinare" not in d:
        return "non_profit" in d and not (IMPRESE & set(d)) and "altri" not in d and p.get("agevolazione") != "no"
    return False


def per_imprese_no(p):
    d = p.get("destinatari")
    if isinstance(d, list) and "da_determinare" not in d:
        return p.get("agevolazione") == "no" or (bool(d) and not ({"imprese", "altri"} & set(d)))
    return p.get("per_imprese") == "no"


def passa(p):
    return not ((per_imprese_no(p) and not non_profit(p)) or p.get("edizione_in_corso") == "no"
                or p.get("stato") == "chiuso" or p.get("testo_bando") == "no")


import fcntl

_blocco = open("/tmp/claude-1000/ar/coda.lock", "w")
fcntl.flock(_blocco, fcntl.LOCK_EX)   # due agenti che chiedono insieme non ricevono gli stessi id
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

def solo_np(x):
    try:
        return non_profit(json.loads((F / x / "preliminare.json").read_text()))
    except (OSError, json.JSONDecodeError):
        return False


def priorita(x):   # prima i bandi che i segnali gratuiti danno per aperti
    return (0 if (F / x / "aperto").exists() else 1, int(x))


a.sort(key=priorita)
modo = sys.argv[1]
if modo == "conta":
    print(f"fascicoli {len(list(F.iterdir()))}; senza preliminare {len(a)}; fermati {fermati}; "
          f"schede fatte {fatti}; schede da fare {len(b)}; preliminari rotti {rotti}; prenotati {len(prenotati)}")
    sys.exit()
n = int(sys.argv[2])
ids = [x for x in (a if modo == "A" else b) if f"{modo}{x}" not in prenotati]
if modo == "B":
    # prima i bandi per imprese, poi quelli solo non profit (priorita' bassa, 07/10); dentro, gli aperti e i corti
    ids.sort(key=lambda x: (solo_np(x), priorita(x)[0], (F / x / "scheda.md").stat().st_size))
gruppi = [ids[i:i + n] for i in range(0, len(ids), n)]
limite = int(sys.argv[3]) if len(sys.argv) > 3 else len(gruppi)
with PRENOTATI.open("a") as f:
    for g in gruppi[:limite]:
        print(", ".join(g))
        f.write(" ".join(f"{modo}{x}" for x in g) + "\n")
