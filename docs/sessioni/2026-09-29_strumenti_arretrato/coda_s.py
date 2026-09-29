"""Coda dei lotti di smistamento. Uso: python3 coda_s.py N  -> stampa fino a N lotti liberi (e li prenota)."""
import sys
from pathlib import Path

S = Path("/tmp/claude-1000/ar/smista")
P = Path("/tmp/claude-1000/ar/prenotati_s.txt")
import fcntl

_blocco = open("/tmp/claude-1000/ar/coda_s.lock", "w")
fcntl.flock(_blocco, fcntl.LOCK_EX)
prenotati = set(P.read_text().split()) if P.exists() else set()
liberi = [f.stem for f in sorted(S.glob("lotto_*.md"))
          if f.stem not in prenotati and not f.with_suffix(".json").exists() and not f.with_suffix(".importato").exists()]
scelti = liberi[:int(sys.argv[1]) if len(sys.argv) > 1 else 1]
with P.open("a") as f:
    f.write(" ".join(scelti) + "\n")
print(" ".join(scelti))
