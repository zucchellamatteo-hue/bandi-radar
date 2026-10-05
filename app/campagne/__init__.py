"""Campagne di lancio (05/10/2026): quali imprese della mappatura di Matteo beneficerebbero dei bandi recenti.

Le imprese arrivano ANONIME (strumenti/anagrafiche/esporta_profili.py: codice casuale e dati di categoria). Per
ognuna si cercano i bandi proponibili aperti o in arrivo con la scheda fatta negli ultimi N giorni, con lo stesso
abbinamento a regole di catalogo e area impresa, e si prepara una bozza di testo con i bandi e il beneficio
massimo. Matteo scarica il CSV e lo completa sul suo computer (codice -> impresa) per un canale consentito: lettera,
o email solo a chi ha dato il consenso (docs/ricerche/2026-10-05_marketing_prospect_regole.md). Niente IA.
"""

from __future__ import annotations

import csv
import io
import json
from collections import Counter, defaultdict
from datetime import date

from app.abbinamento import catalogo, regole
from app.abbinamento.profilo import Profilo

MASSIMO_PROSPETTI = 20_000
# Per scegliere i bandi da citare l'importo conta fino a un tetto credibile per la dimensione dell'impresa: un
# "fino a 10 milioni" non convince una micro impresa piu' di un "fino a 50.000 euro" della sua regione.
TETTO_PER_DIMENSIONE = {"micro": 100_000, "piccola": 300_000, "media": 1_000_000, "grande": 5_000_000}
BANDI_NEL_TESTO = 3


class ErroreCampagna(ValueError):
    pass


def _euro(n) -> str:
    return f"{float(n):,.0f} €".replace(",", ".") if n else ""


def importo(b: dict):
    """Il beneficio massimo leggibile del bando: fondo perduto o contributo massimo, altrimenti il prestito."""
    return b.get("fondo_perduto_massimo") or b.get("contributo_massimo") or b.get("finanziamento_massimo")


def crea(conn, nome: str, giorni: int, profili: list[dict], chi: str) -> int:
    """Salva la campagna e i profili (controllati come i profili di Bandi Radar: niente dati identificativi)."""
    if not profili:
        raise ErroreCampagna("Il file non contiene profili.")
    if len(profili) > MASSIMO_PROSPETTI:
        raise ErroreCampagna(f"Troppi profili ({len(profili)}): al massimo {MASSIMO_PROSPETTI} per campagna.")
    validi, errori = [], []
    for i, p in enumerate(profili):
        try:
            prof = Profilo.model_validate({**(p.get("profilo") or {}), "codice": p.get("codice")})
            validi.append((prof.codice, prof.model_dump_json()))
        except Exception as exc:  # noqa: BLE001 - si riportano i primi errori leggibili
            if len(errori) < 5:
                errori.append(f"profilo {i + 1} ({p.get('codice')}): {str(exc).splitlines()[-1][:160]}")
    if errori and len(validi) < len(profili) * 0.9:
        raise ErroreCampagna("Troppi profili non validi: " + "; ".join(errori))
    with conn.cursor() as cur:
        cur.execute("INSERT INTO campagne (nome, giorni, creata_da, riepilogo) VALUES (%s, %s, %s, %s) RETURNING id",
                    ((nome or "Campagna").strip()[:120], max(1, min(giorni, 365)), chi,
                     json.dumps({"scartati": len(profili) - len(validi), "errori": errori})))
        cid = cur.fetchone()["id"]
        cur.executemany("INSERT INTO prospetti (campagna_id, codice, profilo) VALUES (%s, %s, %s) ON CONFLICT DO NOTHING",
                        [(cid, c, j) for c, j in validi])
    return cid


def bandi_recenti(conn, giorni: int) -> list[dict]:
    """Bandi proponibili aperti o in arrivo con la scheda fatta (o rifatta) negli ultimi N giorni."""
    with conn.cursor() as cur:
        cur.execute("SELECT id FROM bandi WHERE scheda_il > now() - make_interval(days => %s)", (giorni,))
        recenti = {r["id"] for r in cur.fetchall()}
    return [b for b in catalogo.carica_bandi(conn) if b["id"] in recenti and catalogo.proponibile(b)
            and b.get("stato") in ("aperto", "in_arrivo")]


def analizza(conn, campagna_id: int, oggi: date | None = None) -> dict:
    """Abbina ogni impresa ai bandi recenti. Profili uguali si calcolano una volta sola."""
    with conn.cursor() as cur:
        cur.execute("SELECT * FROM campagne WHERE id = %s", (campagna_id,))
        camp = cur.fetchone()
        cur.execute("SELECT id, codice, profilo FROM prospetti WHERE campagna_id = %s", (campagna_id,))
        prospetti = cur.fetchall()
    bandi = bandi_recenti(conn, camp["giorni"])
    cache: dict[str, tuple] = {}
    aggiornamenti = []
    per_bando: Counter = Counter()
    for p in prospetti:
        chiave = json.dumps({k: v for k, v in p["profilo"].items() if k != "codice"}, sort_keys=True)
        if chiave not in cache:
            prof = Profilo.model_validate({**p["profilo"], "codice": p["codice"]}).per_regole()
            regioni = {s.get("regione") for s in prof.get("sedi") or []}
            tetto = TETTO_PER_DIMENSIONE.get(prof.get("dimensione") or "", 300_000)
            risultati = catalogo.abbina(bandi, prof, oggi)
            elenco = [{"bando_id": b["id"], "titolo": b["titolo"], "ente": b.get("ente"),
                       "scadenza": b["scadenza"].isoformat() if b.get("scadenza") else None, "importo": importo(b),
                       "percentuale": b.get("percentuale"), "livello": e.livello,
                       "locale": bool(regioni & set(b.get("territorio_regioni") or []))} for b, e in risultati]
            # Prima i compatibili, poi quelli della sua regione, poi l'importo (fino al tetto per la dimensione).
            elenco.sort(key=lambda x: (x["livello"] != regole.COMPATIBILE, not x["locale"],
                                       -min(float(x["importo"] or 0), tetto)))
            comp = [x for x in elenco if x["livello"] == regole.COMPATIBILE]
            cache[chiave] = (elenco[:10], len(comp), len(elenco) - len(comp),
                             max((float(x["importo"]) for x in comp if x["importo"]), default=None))
        elenco, n_comp, n_ver, massimo = cache[chiave]
        per_bando.update(x["bando_id"] for x in elenco if x["livello"] == regole.COMPATIBILE)
        aggiornamenti.append((json.dumps(elenco, default=str), n_comp, n_ver, massimo, p["id"]))
    with conn.cursor() as cur:
        cur.executemany("UPDATE prospetti SET bandi = %s, n_compatibili = %s, n_da_verificare = %s, beneficio_max = %s "
                        "WHERE id = %s", aggiornamenti)
        titoli = {b["id"]: b["titolo"] for b in bandi}
        riepilogo = {**(camp["riepilogo"] or {}), "bandi_considerati": len(bandi), "prospetti": len(prospetti),
                     "con_compatibili": sum(1 for a in aggiornamenti if a[1] > 0), "profili_diversi": len(cache),
                     "bandi_piu_utili": [{"bando_id": i, "titolo": titoli[i], "imprese": n} for i, n in per_bando.most_common(15)]}
        cur.execute("UPDATE campagne SET stato = 'pronta', riepilogo = %s WHERE id = %s", (json.dumps(riepilogo), campagna_id))
    return riepilogo


def segmenti(conn, campagna_id: int) -> list[dict]:
    """Imprese raggruppate per settore (divisione ATECO), regione e dimensione: dove la proposta e' piu' forte."""
    with conn.cursor() as cur:
        cur.execute("SELECT profilo, n_compatibili, beneficio_max FROM prospetti WHERE campagna_id = %s", (campagna_id,))
        righe = cur.fetchall()
    gruppi: dict[tuple, dict] = defaultdict(lambda: {"imprese": 0, "con_compatibili": 0, "bandi": 0, "beneficio": []})
    for r in righe:
        p = r["profilo"]
        sede = (p.get("sedi") or [{}])[0]
        chiave = ((p.get("ateco") or ["??"])[0][:2], sede.get("regione") or "?", p.get("dimensione") or "non nota")
        g = gruppi[chiave]
        g["imprese"] += 1
        g["con_compatibili"] += r["n_compatibili"] > 0
        g["bandi"] += r["n_compatibili"]
        if r["beneficio_max"]:
            g["beneficio"].append(float(r["beneficio_max"]))
    uscita = []
    for (div, reg, dim), g in gruppi.items():
        ben = sorted(g["beneficio"])
        uscita.append({"ateco": div, "regione": reg, "dimensione": dim, "imprese": g["imprese"],
                       "con_compatibili": g["con_compatibili"], "media_bandi": round(g["bandi"] / g["imprese"], 1),
                       "beneficio_mediano": ben[len(ben) // 2] if ben else None})
    uscita.sort(key=lambda x: (-x["con_compatibili"], -x["imprese"]))
    return uscita


def testo(prospetto: dict, sito: str, prezzo: int = 30, giorni_prova: int = 14) -> tuple[str, str]:
    """Bozza di lettera o newsletter (oggetto, testo). {RAGIONE_SOCIALE} lo sostituisce Matteo sul suo computer."""
    comp = [b for b in (prospetto.get("bandi") or []) if b["livello"] == regole.COMPATIBILE][:BANDI_NEL_TESTO]
    if not comp:
        return "", ""
    righe = []
    for b in comp:
        dettagli = []
        if b.get("importo"):
            dettagli.append(f"agevolazione fino a {_euro(b['importo'])}")
        if b.get("percentuale"):
            dettagli.append(f"{float(b['percentuale']):g}% delle spese")
        if b.get("scadenza"):
            dettagli.append(f"domande entro il {date.fromisoformat(b['scadenza']):%d/%m/%Y}")
        righe.append(f"- {b['titolo']} ({b.get('ente') or 'ente pubblico'})" + (f": {', '.join(dettagli)}" if dettagli else ""))
    altri = prospetto["n_compatibili"] - len(comp)
    oggetto = (f"{prospetto['n_compatibili']} bandi aperti adatti a {{RAGIONE_SOCIALE}}"
               if prospetto["n_compatibili"] > 1 else "Un bando aperto adatto a {RAGIONE_SOCIALE}")
    corpo = (
        "Gentile {RAGIONE_SOCIALE},\n\n"
        "analizzando i bandi pubblicati di recente da Unione europea, Stato, Regioni, Camere di commercio e Comuni, "
        "abbiamo trovato opportunità che, per settore, territorio e dimensione, sembrano adatte alla vostra impresa:\n\n"
        + "\n".join(righe) + "\n"
        + (f"\n…e altri {altri} bandi compatibili.\n" if altri > 0 else "")
        + "\nSono informazioni indicative, da verificare sul bando ufficiale insieme a voi.\n\n"
        f"Con Bandi Radar ricevete ogni settimana solo i bandi adatti alla vostra impresa, con schede chiare: "
        f"{prezzo} € al mese + IVA, con {giorni_prova} giorni di prova gratuita. "
        "Se un bando vi interessa, possiamo preparare e presentare la domanda per voi senza costi fissi: "
        "solo una percentuale del contributo, se viene concesso.\n\n"
        f"Per vedere i bandi della vostra impresa: {sito}/registrati\n\n"
        "Cordiali saluti\n{FIRMA}\n")
    return oggetto, corpo


def esporta_csv(conn, campagna_id: int, sito: str) -> str:
    """CSV per il computer di Matteo: codice, numeri, bandi e bozza del testo (solo imprese con bandi compatibili)."""
    from app.abbonamenti import giorni_prova

    with conn.cursor() as cur:
        cur.execute("""SELECT codice, bandi, n_compatibili, n_da_verificare, beneficio_max FROM prospetti
                       WHERE campagna_id = %s AND n_compatibili > 0 ORDER BY beneficio_max DESC NULLS LAST""", (campagna_id,))
        righe = [dict(r) for r in cur.fetchall()]
    uscita = io.StringIO()
    w = csv.writer(uscita, delimiter=";")
    w.writerow(["codice", "bandi_compatibili", "bandi_da_verificare", "beneficio_massimo_euro", "bandi", "oggetto", "testo"])
    for r in righe:
        oggetto, corpo = testo(r, sito, giorni_prova=giorni_prova())
        w.writerow([r["codice"], r["n_compatibili"], r["n_da_verificare"],
                    round(float(r["beneficio_max"])) if r["beneficio_max"] else "",
                    " | ".join(f"{b['bando_id']} {b['titolo'][:80]}" for b in (r["bandi"] or []) if b["livello"] == regole.COMPATIBILE),
                    oggetto, corpo])
    return uscita.getvalue()


def elenco(conn) -> list[dict]:
    with conn.cursor() as cur:
        cur.execute("""SELECT c.id, c.nome, c.giorni, c.stato, c.creata_il, c.riepilogo,
                              (SELECT count(*) FROM prospetti p WHERE p.campagna_id = c.id) AS prospetti
                       FROM campagne c ORDER BY c.id DESC""")
        return [dict(r) for r in cur.fetchall()]


def dettaglio(conn, campagna_id: int, sito: str) -> dict:
    from app.abbonamenti import giorni_prova

    with conn.cursor() as cur:
        cur.execute("SELECT * FROM campagne WHERE id = %s", (campagna_id,))
        c = cur.fetchone()
        if not c:
            raise ErroreCampagna("Campagna non trovata.")
        cur.execute("""SELECT codice, profilo, bandi, n_compatibili, n_da_verificare, beneficio_max FROM prospetti
                       WHERE campagna_id = %s AND n_compatibili > 0 ORDER BY beneficio_max DESC NULLS LAST LIMIT 1""",
                    (campagna_id,))
        esempio = cur.fetchone()
    bozza = testo(dict(esempio), sito, giorni_prova=giorni_prova()) if esempio else ("", "")
    return {**dict(c), "segmenti": segmenti(conn, campagna_id) if c["stato"] == "pronta" else [],
            "esempio": {"codice": esempio["codice"], "oggetto": bozza[0], "testo": bozza[1]} if esempio else None}
