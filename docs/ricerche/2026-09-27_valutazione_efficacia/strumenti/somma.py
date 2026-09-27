"""Somma dei verdetti della valutazione: perimetro, smistamento, preliminare, schede; per fase e per strato."""
import json
from collections import Counter, defaultdict
from pathlib import Path

BASE = Path("/tmp/claude-1000/sp/schede/valuta/fonti")
campione = {f["id"]: f for f in json.loads(Path("/tmp/claude-1000/sp/valuta/campione_fonti.json").read_text())}


def carica(p):
    try:
        return json.loads(p.read_text())
    except Exception:  # noqa: BLE001
        return None


per = Counter()
per_strato = defaultdict(Counter)
smi = Counter()
pre = Counter()
schede = []
mancanti = []
fonti_fatte = 0
osservazioni = []
persi_elenco = []
for fid, f in campione.items():
    d = BASE / fid
    v = carica(d / "verdetto_finale.json") or carica(d / "verdetto.json")
    if not v:
        mancanti.append(fid)
        continue
    fonti_fatte += 1
    strato = f"{f['tipo']}/{f['modalita']}"
    for p in v.get("perimetro") or []:
        e = p.get("esito", "?")
        per[e] += 1
        per_strato[strato][e] += 1
        if str(e).startswith("perso"):
            persi_elenco.append((fid, e, p.get("titolo", "")[:80], p.get("spiegazione", "")[:160]))
    for s in v.get("smistamento") or []:
        smi["valutati"] += 1
        for chi in ("regole", "haiku", "opus"):
            g = s.get(f"errore_{chi}", "nessuno")
            smi[f"{chi}_{g}"] += 1
    for b in v.get("preliminare") or []:
        pre["valutati"] += 1
        for chi in ("produzione", "haiku_nuovo", "opus"):
            g = b.get(f"errore_{chi}", "nessuno")
            pre[f"{chi}_{g}"] += 1
    osservazioni += [f"{fid}: {o}" for o in v.get("osservazioni") or []]
    for g in d.glob("giudizio_scheda_*.json"):
        x = carica(g)
        if x:
            gravi = Counter(c.get("gravita") for c in x.get("campi") or [] if c.get("sonnet") in ("sbagliato", "mancante"))
            gravi_o = Counter(c.get("gravita") for c in x.get("campi") or [] if c.get("opus") in ("sbagliato", "mancante"))
            schede.append((x.get("bando"), x.get("voto_sonnet"), x.get("voto_opus"), gravi.get("grave", 0), gravi_o.get("grave", 0),
                           (x.get("sintesi") or "")[:300]))

print(f"Fonti con verdetto: {fonti_fatte}/{len(campione)}; mancanti: {mancanti}\n")
tot = sum(per.values())
print("PERIMETRO (bandi per imprese trovati sul sito dall'esploratore):", tot)
for k, n in per.most_common():
    print(f"  {k:28} {n:4}  {100*n/max(tot,1):.0f}%")
print("\nPer strato:")
for s, c in sorted(per_strato.items()):
    t = sum(c.values())
    ok = c.get("trovato_con_scheda", 0) + c.get("fermato_giustamente", 0)
    print(f"  {s:22} bandi {t:3}  ok {ok:3}  persi {t-ok:3}   {dict(c)}")
print("\nPersi (dettaglio):")
for x in persi_elenco:
    print("  ", " | ".join(x))
print("\nSMISTAMENTO:", smi["valutati"], "annunci")
for chi in ("regole", "haiku", "opus"):
    print(f"  {chi:8} gravi {smi[chi+'_grave']:3}  medi {smi[chi+'_medio']:3}  lievi {smi[chi+'_lieve']:3}")
print("\nPRELIMINARE:", pre["valutati"], "bandi")
for chi in ("produzione", "haiku_nuovo", "opus"):
    print(f"  {chi:12} gravi (bando buono fermato) {pre[chi+'_grave']:3}  medi (bando da fermare passato) {pre[chi+'_medio']:3}")
print("\nSCHEDE:", len(schede))
if schede:
    vs = [s[1] for s in schede if isinstance(s[1], (int, float))]
    vo = [s[2] for s in schede if isinstance(s[2], (int, float))]
    print(f"  voto medio Sonnet {sum(vs)/len(vs):.2f}  Opus {sum(vo)/len(vo):.2f}")
    print(f"  schede con errori gravi: Sonnet {sum(1 for s in schede if s[3])}  Opus {sum(1 for s in schede if s[4])}")
    for s in schede:
        print(f"  bando {s[0]}: Sonnet {s[1]} Opus {s[2]} gravi S{s[3]}/O{s[4]} — {s[5]}")
print("\nOSSERVAZIONI:")
for o in osservazioni:
    print("  -", o[:300])
