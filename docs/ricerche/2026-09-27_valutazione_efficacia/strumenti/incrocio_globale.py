"""I bandi 'persi' da una fonte sono arrivati da un'altra fonte? Confronto con TUTTI gli annunci del database,
per indirizzo (ripulito) o per titolo simile. Stampa per ogni perso il miglior candidato."""
import csv
import json
import re
import sys
from difflib import SequenceMatcher
from pathlib import Path
from urllib.parse import urlsplit

csv.field_size_limit(10**9)
BASE = Path("/tmp/claude-1000/sp/schede/valuta/fonti")
annunci = list(csv.DictReader(open("/tmp/claude-1000/sp/valuta/tutti_annunci.csv")))


def chiave_url(u):
    if not u:
        return ""
    p = urlsplit(u.strip())
    s = p.netloc.lower().removeprefix("www.")
    return s + p.path.rstrip("/").lower()


PAROLE_VUOTE = set("di del della dei degli delle per a al alla e ed il lo la le i gli un una in con da su anno bando avviso contributi".split())


def norm(t):
    t = re.sub(r"[^a-z0-9àèéìòù ]", " ", (t or "").lower())
    return " ".join(w for w in t.split() if w not in PAROLE_VUOTE)


per_url = {}
for a in annunci:
    for u in (a["url"], a["pagina_url"]):
        k = chiave_url(u)
        if k:
            per_url.setdefault(k, a)
titoli = [(norm(a["titolo"]), a) for a in annunci]

risultati = []
for d in sorted(BASE.iterdir()):
    v = None
    for nome in ("verdetto_finale.json", "verdetto.json"):
        try:
            v = json.loads((d / nome).read_text())
            break
        except Exception:  # noqa: BLE001
            continue
    if not v:
        continue
    for p in v.get("perimetro") or []:
        if p.get("esito") != "perso_non_raccolto":
            continue
        a = per_url.get(chiave_url(p.get("url")))
        come = "indirizzo"
        if not a:
            t = norm(p.get("titolo"))
            migliore, punteggio = None, 0.0
            parole = set(t.split())
            for tn, cand in titoli:
                if not parole & set(tn.split()):
                    continue
                r = SequenceMatcher(None, t, tn).ratio()
                if r > punteggio:
                    migliore, punteggio = cand, r
            if punteggio >= 0.72:
                a, come = migliore, f"titolo {punteggio:.2f}"
        risultati.append({"fonte": d.name, "titolo": p.get("titolo"), "url": p.get("url"),
                          "trovato_altrove": bool(a), "come": come if a else None,
                          "annuncio": a and {k: a[k] for k in ("id", "fonte_id", "titolo", "esito", "bando_id", "pagina", "scheda", "stato")}})

Path("/tmp/claude-1000/sp/valuta/incrocio_globale.json").write_text(json.dumps(risultati, indent=1, ensure_ascii=False))
tot = len(risultati)
altrove = [r for r in risultati if r["trovato_altrove"]]
print(f"persi_non_raccolti: {tot}; trovati in un'altra fonte: {len(altrove)}")
from collections import Counter
print("  di questi, con scheda:", sum(1 for r in altrove if r["annuncio"]["scheda"] == "t"),
      " rilevanti:", sum(1 for r in altrove if r["annuncio"]["esito"] == "rilevante"))
print("  persi davvero per fonte:", Counter(r["fonte"] for r in risultati if not r["trovato_altrove"]).most_common())
if "-v" in sys.argv:
    for r in altrove[:40]:
        print(f"  [{r['fonte']}] {r['titolo'][:60]} -> {r['annuncio']['fonte_id']} {r['annuncio']['titolo'][:60]} ({r['come']})")
