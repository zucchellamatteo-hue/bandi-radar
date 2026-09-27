"""Numeri finali della valutazione: perimetro sui bandi APERTI o IN ARRIVO (con l'incrocio su tutto il database),
smistamento, preliminare, schede."""
import json
from collections import Counter, defaultdict
from pathlib import Path

BASE = Path("/tmp/claude-1000/sp/schede/valuta/fonti")
campione = {f["id"]: f for f in json.loads(Path("/tmp/claude-1000/sp/valuta/campione_fonti.json").read_text())}
altrove = {(r["fonte"], r["titolo"]): r for r in json.loads(Path("/tmp/claude-1000/sp/valuta/incrocio_globale.json").read_text())}


def j(p):
    try:
        return json.loads(p.read_text())
    except Exception:  # noqa: BLE001
        return None


def chiave(t):
    return (t or "").lower().strip()[:60]


aperti = Counter()
aperti_strato = defaultdict(Counter)
tutti = Counter()
smi = Counter()
pre = Counter()
schede = []
elenco_aperti_persi = []
for fid, f in campione.items():
    d = BASE / fid
    v = j(d / "verdetto_finale.json")
    e = j(d / "esploratore.json") or {}
    stati = {}
    for b in e.get("bandi") or []:
        stati[chiave(b.get("titolo"))] = b.get("stato")
        stati[(b.get("url") or "").rstrip("/")] = b.get("stato")
    if not v:
        continue
    strato = f"{f['tipo']}/{f['modalita']}"
    for p in v.get("perimetro") or []:
        esito = p.get("esito", "?")
        if esito == "perso_non_raccolto" and altrove.get((fid, p.get("titolo")), {}).get("trovato_altrove"):
            a = altrove[(fid, p.get("titolo"))]["annuncio"]
            esito = "trovato_altrove_con_scheda" if a["scheda"] == "t" else "trovato_altrove_senza_scheda"
        stato = stati.get((p.get("url") or "").rstrip("/")) or stati.get(chiave(p.get("titolo"))) or "non_noto"
        tutti[esito] += 1
        if stato in ("aperto", "in_arrivo"):
            aperti[esito] += 1
            aperti_strato[strato][esito] += 1
            if esito.startswith("perso") or esito == "trovato_altrove_senza_scheda":
                elenco_aperti_persi.append((strato, fid, esito, (p.get("titolo") or "")[:70]))
    for s in v.get("smistamento") or []:
        smi["n"] += 1
        for chi in ("regole", "haiku", "opus"):
            smi[(chi, s.get(f"errore_{chi}", "nessuno"))] += 1
    for b in v.get("preliminare") or []:
        pre["n"] += 1
        for chi in ("produzione", "haiku_nuovo", "opus"):
            pre[(chi, b.get(f"errore_{chi}", "nessuno"))] += 1
    for g in d.glob("giudizio_scheda_*.json"):
        x = j(g)
        if x:
            gs = sum(1 for c in x.get("campi") or [] if c.get("gravita") == "grave" and c.get("sonnet") in ("sbagliato", "mancante"))
            go = sum(1 for c in x.get("campi") or [] if c.get("gravita") == "grave" and c.get("opus") in ("sbagliato", "mancante"))
            schede.append((x.get("bando"), x.get("voto_sonnet"), x.get("voto_opus"), gs, go))

OK = ("trovato_con_scheda", "trovato_altrove_con_scheda")


def riga(c):
    t = sum(c.values())
    ok = sum(c[k] for k in OK)
    return t, ok


t, ok = riga(aperti)
print(f"BANDI APERTI O IN ARRIVO sui siti del campione: {t}; con scheda in Bandi Radar: {ok} ({100*ok/max(t,1):.0f}%)")
for k, n in aperti.most_common():
    print(f"   {k:32} {n:4}")
print("\nPer strato (aperti o in arrivo): totale / con scheda")
for s, c in sorted(aperti_strato.items()):
    tt, oo = riga(c)
    print(f"   {s:22} {tt:3} / {oo:3}   {dict(c)}")
print("\nTutti (anche chiusi di recente):", dict(tutti))
print(f"\nSMISTAMENTO {smi['n']} annunci: errori medi+gravi -> "
      + ", ".join(f"{chi} {smi[(chi,'medio')]+smi[(chi,'grave')]} (gravi {smi[(chi,'grave')]})" for chi in ("regole", "haiku", "opus")))
print(f"PRELIMINARE {pre['n']} bandi: " + ", ".join(
    f"{chi}: fermati per errore {pre[(chi,'grave')]}, passati per errore {pre[(chi,'medio')]}" for chi in ("produzione", "haiku_nuovo", "opus")))
if schede:
    vs = [s[1] for s in schede]; vo = [s[2] for s in schede]
    print(f"SCHEDE {len(schede)}: voto Sonnet {sum(vs)/len(vs):.2f}, Opus {sum(vo)/len(vo):.2f}; "
          f"schede con errori gravi Sonnet {sum(1 for s in schede if s[3])}, Opus {sum(1 for s in schede if s[4])}; "
          f"errori gravi totali Sonnet {sum(s[3] for s in schede)}, Opus {sum(s[4] for s in schede)}")
print("\nAperti persi (dettaglio):")
for x in sorted(elenco_aperti_persi):
    print("  ", " | ".join(x))
