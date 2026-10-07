"""Destinatari dei bandi gia' decisi, ricavati SENZA IA dai dati esistenti (07/10/2026, decisione di Matteo: i bandi per
associazioni ed enti senza scopo di lucro si mappano comunque, con priorita' bassa).

Dal 07/10 il controllo preliminare scrive `destinatari` (imprese, non_profit, enti_pubblici, persone_fisiche, altri) e
`agevolazione`; i bandi decisi prima hanno solo `per_imprese`. Questo script aggiunge `destinatari` dove e' sicuro e
"da_determinare" negli altri casi. NON cambia mai `per_imprese` (ne' chi ha deciso, ne' quando): aggiunge solo
`destinatari`, a volte `agevolazione: "no"`, e `destinatari_da` con la provenienza.

Regole (prudenti):
  - per_imprese "si"      -> ["imprese"] piu' le altre categorie ammesse dalla scheda (soggetti_ammessi);
  - per_imprese "incerto" -> ["da_determinare"] (per non trasformarlo in "si" o "no");
  - per_imprese "no"      -> si leggono il motivo del preliminare, "a chi si rivolge" e i soggetti della scheda:
      * enti di formazione, organismi di ricerca, confidi, ordini, partenariati (potrebbero essere imprese)
        -> ["da_determinare"];
      * gara, appalto, affidamento, elenco di fornitori o esperti, "non e' un bando" (nel motivo) -> agevolazione
        "no", [];
      * parole del non profit (associazioni, ETS/RUNTS, ONLUS, fondazioni, ASD/SSD, cooperative sociali, enti
        religiosi, volontariato...) senza negazioni vicine ("indirettamente", "esclusi", "tramite", "partner",
        "presso") -> ["non_profit", ...]; nominate solo con negazioni -> ["da_determinare"];
      * solo parole di enti pubblici e/o persone fisiche -> ["enti_pubblici"] / ["persone_fisiche"];
      * nessun indizio -> ["da_determinare"].

Uso (dopo che la PR con la migrazione 031 e' in produzione):
  /tmp/claude-1000/ar.sh deriva_destinatari.py            # PROVA: non scrive nulla, conta e salva /out/destinatari_prova.tsv
  /tmp/claude-1000/ar.sh deriva_destinatari.py --applica  # scrive nel database (solo i preliminari senza destinatari)
Poi: sudo -u deploy docker compose exec app python -m app.catena.situazione  (per_non_profit / fuori_target).
"""

from __future__ import annotations

import json
import re
import sys
from collections import Counter
from pathlib import Path

DA = "derivati senza IA dal preliminare e dalla scheda (script del 07/10/2026)"

_SOGGETTI = {"ente_terzo_settore": "non_profit", "ente_pubblico": "enti_pubblici", "persona_fisica": "persone_fisiche"}

NON_AGEVOLAZIONE = re.compile(
    r"appalt|affidament|\bgara\b|elenco (di )?(fornitori|operatori|esperti|professionisti)|"
    r"albo (dei|degli) (esperti|fornitori|professionisti|valutatori)|"
    r"non [eè]'? un bando|non bando|non [eè]'? un contributo|non [eè]'? un'agevolazione|avviso meteo|"
    r"avviso esplorativo|concorso (di idee|di progettazione|pubblico per)|indagine di mercato|ordinanza",
    re.IGNORECASE)
NON_PROFIT = re.compile(
    r"associazion|senza scopo di lucro|non a scopo di lucro|fini di lucro|\bnon[- ]?profit|\bno[- ]profit|"
    r"terzo settore|\bets\b|runts|onlus|fondazion|\bas[sd]\b|\bssd\b|sportive dilettantistiche|societ[aà] sportiv|"
    r"federazion\w* sportiv|cooperativ\w* social|impres\w* social|ecclesiastic|religios|parrocchi|diocesi|"
    r"volontariato|\bodv\b|\baps\b|promozione sociale|pro ?loco|enti? non commercial|"
    r"organizzazioni (sindacali|dei lavoratori|di categoria)|enti privati senza|comitat[oi] (di|per|organizzator)|"
    r"bande musicali", re.IGNORECASE)
ENTI_PUBBLICI = re.compile(
    r"\bcomun[ei]\b|enti? (pubblic|local|territorial)|soggetti pubblici|amministrazion\w* pubblic|\bprovince\b|"
    r"\bregioni\b|unioni? (di|dei) comuni|comunit[aà] montan|\basl\b|aziende sanitarie|universit|\bscuol|"
    r"istituti scolastici|istituzioni scolastiche|camere di commercio|\begato\b|consorzi di bonifica|enti parco|"
    r"\bats\b|ministeri", re.IGNORECASE)
PERSONE = re.compile(
    r"persone fisiche|\bpersone\b|cittadin|famiglie|nuclei familiari|student|neolaureat|neodiplomat|\bgiovani\b|"
    r"lavorator|disoccupat|residenti|privati cittadini|proprietari di (case|casa|abitazion|immobil|terren|alloggi)|"
    r"pensionat|anzian|dottorand|amministrazione di sostegno|inquilin|genitori|\bdonne\b|disabil|minorenn|"
    r"caregiver|\beredi\b|condomin|giovani coppie", re.IGNORECASE)
ALTRI = re.compile(
    r"organismi? (formativ|di formazione|di ricerca|di consulenza)|enti di formazione|enti accreditati|"
    r"istituti professionali|istituzioni formative|its academy|\bconfidi\b|ordini professionali|ordine degli|"
    r"partenariat", re.IGNORECASE)
# Il testo nomina il non profit ma per dire che non partecipa, che riceve solo indirettamente o che e' solo partner:
# si guarda vicino (40 caratteri prima e dopo) a ogni parola del non profit.
NEGAZIONE = re.compile(
    r"indirett|tramite|presso|partner|esclus[oiae]\b|non (possono|sono ammess|partecipa)|solo destinatari|diversi da|"
    r"\bnon (le|gli|alle|agli|ad|a|per) (associazion|ets|enti del|onlus|fondazion|organizzazion|cooperativ)",
    re.IGNORECASE)


def _non_profit_chiaro(testo: str) -> tuple[bool, bool]:
    """(nominato, nominato almeno una volta senza negazioni vicine)."""
    trovati = list(NON_PROFIT.finditer(testo))
    puliti = [m for m in trovati if not NEGAZIONE.search(testo[max(0, m.start() - 40):m.end() + 40])]
    return bool(trovati), bool(puliti)


def deriva(preliminare: dict, soggetti_ammessi: list | None, a_chi_si_rivolge: str | None) -> tuple[dict, str]:
    """Le chiavi da aggiungere al preliminare e la regola usata. Mai per_imprese."""
    per_imprese = preliminare.get("per_imprese")
    dalla_scheda = [_SOGGETTI[s] for s in (soggetti_ammessi or []) if s in _SOGGETTI]
    if per_imprese == "si":
        return {"destinatari": list(dict.fromkeys(["imprese", *dalla_scheda]))}, "per imprese"
    if per_imprese != "no":
        return {"destinatari": ["da_determinare"]}, "incerto"
    motivo = preliminare.get("motivo") or ""
    testo = " ".join(x for x in (motivo, a_chi_si_rivolge) if x)
    if ALTRI.search(testo):
        return {"destinatari": ["da_determinare"]}, "altri soggetti (forse imprese)"
    if NON_AGEVOLAZIONE.search(motivo) and not NON_PROFIT.search(motivo):
        return {"destinatari": [], "agevolazione": "no"}, "non e' un'agevolazione"
    nominato, chiaro = _non_profit_chiaro(testo)
    if nominato and not chiaro:
        return {"destinatari": ["da_determinare"]}, "non profit nominato con una negazione"
    # Le categorie in piu' (enti pubblici, persone) solo dal motivo del preliminare e dalla scheda: "a chi si
    # rivolge" e' lungo e nomina spesso chi riceve il servizio, non chi presenta la domanda.
    ep = bool(ENTI_PUBBLICI.search(motivo)) or "enti_pubblici" in dalla_scheda
    pf = bool(PERSONE.search(motivo)) or "persone_fisiche" in dalla_scheda
    if chiaro or "non_profit" in dalla_scheda:
        return {"destinatari": ["non_profit"] + ["enti_pubblici"] * ep + ["persone_fisiche"] * pf}, "non profit"
    if not ep and not pf:
        ep, pf = bool(ENTI_PUBBLICI.search(testo)), bool(PERSONE.search(testo))
    if ep or pf:
        return {"destinatari": ["enti_pubblici"] * ep + ["persone_fisiche"] * pf}, "enti pubblici o persone fisiche"
    return {"destinatari": ["da_determinare"]}, "nessun indizio"


def main() -> int:
    from app.db.connessione import connetti

    applica = "--applica" in sys.argv
    conti: Counter = Counter()
    righe = []
    with connetti() as conn:
        with conn.cursor() as cur:
            cur.execute("""SELECT id, titolo, preliminare, soggetti_ammessi, a_chi_si_rivolge FROM bandi
                           WHERE preliminare IS NOT NULL AND NOT (preliminare ? 'destinatari') ORDER BY id""")
            bandi = cur.fetchall()
        if applica:
            with conn.cursor() as cur:
                cur.execute("SELECT set_config('bandi_radar.causa', %s, true)", ("destinatari: " + DA,))
        for b in bandi:
            aggiunte, regola = deriva(b["preliminare"], b["soggetti_ammessi"], b["a_chi_si_rivolge"])
            conti[(b["preliminare"].get("per_imprese"), regola)] += 1
            righe.append(f"{b['id']}\t{b['preliminare'].get('per_imprese')}\t{regola}\t{json.dumps(aggiunte)}\t"
                         f"{(b['preliminare'].get('motivo') or '')[:200]}")
            if applica:
                with conn.cursor() as cur:
                    cur.execute("""UPDATE bandi SET preliminare = preliminare || %s::jsonb
                                   WHERE id = %s AND preliminare IS NOT NULL AND NOT (preliminare ? 'destinatari')""",
                                (json.dumps({**aggiunte, "destinatari_da": DA}), b["id"]))
        if applica:
            conn.commit()
    uscita = Path("/out/destinatari_prova.tsv") if Path("/out").is_dir() else Path("destinatari_prova.tsv")
    uscita.write_text("id\tper_imprese\tregola\taggiunte\tmotivo\n" + "\n".join(righe) + "\n")
    print(("SCRITTI" if applica else "PROVA (niente scritto)") + f": {len(bandi)} preliminari senza destinatari")
    for (pi, regola), n in sorted(conti.items(), key=lambda x: -x[1]):
        print(f"  {n:>6}  per_imprese={pi}: {regola}")
    print(f"Dettaglio: {uscita}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
