"""Campione stratificato di fonti per la valutazione dell'efficacia (26/09/2026).

Strati: tipo di ente x modalita' di lettura (rss, api, html, browser). Per ogni strato: una fonte con annunci
rilevanti e una qualunque (anche con zero rilevanti: e' li' che si nascondono i bandi persi), scelte con un
ordine casuale fisso (md5). Poi una fonte per ogni piattaforma (CMS) non ancora coperta, e il catalogo nazionale.
"""
import csv
import hashlib
import json
from collections import defaultdict
from pathlib import Path

righe = list(csv.DictReader(open("/tmp/claude-1000/sp/fonti_stat.csv")))
for r in righe:
    for k in ("annunci", "rilevanti", "da_rivedere", "bandi"):
        r[k] = int(r[k])
    r["h"] = hashlib.md5(("valuta-" + r["id"]).encode()).hexdigest()

strati = defaultdict(list)
for r in righe:
    strati[(r["tipo"], r["modalita"])].append(r)

scelte = {}
for (tipo, modo), fonti in sorted(strati.items()):
    fonti.sort(key=lambda r: r["h"])
    con = [r for r in fonti if r["rilevanti"] > 0]
    if con:
        scelte[con[0]["id"]] = (con[0], f"strato {tipo}/{modo}, con rilevanti")
    altri = [r for r in fonti if r["id"] not in scelte]
    if altri:
        scelte[altri[0]["id"]] = (altri[0], f"strato {tipo}/{modo}, a caso")

coperte = {r["piattaforma"] for r, _ in scelte.values()}
per_piattaforma = defaultdict(list)
for r in righe:
    per_piattaforma[r["piattaforma"]].append(r)
for p, fonti in sorted(per_piattaforma.items()):
    if p and p not in coperte and len(fonti) >= 2:
        fonti.sort(key=lambda r: (-(r["rilevanti"] > 0), r["h"]))
        scelte[fonti[0]["id"]] = (fonti[0], f"piattaforma {p}")
        coperte.add(p)

for extra in ("incentivi_gov_ricerca",):
    r = next((r for r in righe if r["id"] == extra), None)
    if r:
        scelte[extra] = (r, "catalogo nazionale")

uscita = [{**{k: r[k] for k in ("id", "tipo", "modalita", "piattaforma", "territorio", "url", "annunci",
                                 "rilevanti", "da_rivedere", "bandi")}, "perche": perche}
          for r, perche in scelte.values()]
Path("/tmp/claude-1000/sp/valuta/campione_fonti.json").write_text(json.dumps(uscita, indent=1, ensure_ascii=False))
for u in uscita:
    print(f"{u['id']:45} {u['tipo']:10} {u['modalita']:7} {u['piattaforma']:24} ann {u['annunci']:4} ril {u['rilevanti']:3}  {u['perche']}")
print(len(uscita))
