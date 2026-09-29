"""Toglie dalle prenotazioni gli id B senza scheda.json (agenti fermati a meta'), cosi' tornano in coda."""
import fcntl
from pathlib import Path

F = Path("/tmp/claude-1000/ar/fascicoli")
P = Path("/tmp/claude-1000/ar/prenotati.txt")
_blocco = open("/tmp/claude-1000/ar/coda.lock", "w")
fcntl.flock(_blocco, fcntl.LOCK_EX)
tenuti, liberati = [], []
for x in P.read_text().split():
    if x.startswith("B") and not (F / x[1:] / "scheda.json").exists():
        liberati.append(x)
    else:
        tenuti.append(x)
P.write_text(" ".join(tenuti) + "\n")
print(f"liberati {len(liberati)}: {' '.join(liberati)}")
