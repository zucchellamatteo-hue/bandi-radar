"""Argomenti per i workflow di valutazione: le fonti del campione divise in N gruppi (uno per workflow)."""
import json
import sys
from pathlib import Path

N = int(sys.argv[1]) if len(sys.argv) > 1 else 4
BASE = Path("/tmp/claude-1000/sp/schede/valuta/fonti")
campione = json.loads(Path("/tmp/claude-1000/sp/valuta/campione_fonti.json").read_text())
voci = []
for f in campione:
    d = BASE / f["id"]
    bandi = json.loads((d / "bandi.json").read_text()) if (d / "bandi.json").exists() else []
    con_scheda = [b for b in bandi if b["ha_scheda"] and b["fascicolo_scheda"]]
    voci.append({"id": f["id"], "url": f["url"], "tipo": f["tipo"], "modalita": f["modalita"],
                 "dir": str(d), "smistamento": (d / "smistamento.md").exists(),
                 "n_bandi": len([b for b in bandi if b["fascicolo_scheda"]]),
                 "bando_scheda": con_scheda[0]["id"] if con_scheda else None})
gruppi = [voci[i::N] for i in range(N)]
print(json.dumps(gruppi[int(sys.argv[2])] if len(sys.argv) > 2 else gruppi, ensure_ascii=False))
