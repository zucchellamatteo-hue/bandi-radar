"""Misure nazionali sugli investimenti (05/10/2026, richiesta di Matteo): conto termico, iperammortamento e simili.

Non sono bandi: sono norme sempre aperte (o a sportello permanente) che danno un beneficio sugli investimenti e spesso
si sommano ai bandi. Hanno una scheda a parte, scritta e verificata a mano in app/misure/misure.yaml (come il registro
delle fonti: aggiungere una misura e' aggiungere una voce), e compaiono:
- nella pagina "Misure nazionali";
- nella scheda di un bando, come "si puo' sommare con", quando le spese del bando sono tra gli investimenti della
  misura e la misura e' cumulabile con un contributo a fondo perduto;
- nella bozza delle campagne, con il beneficio stimato in percentuale della spesa (indicativo).

Ogni misura aperta ha anche degli "esempi" (06/10/2026, richiesta di Matteo): un caso pratico per ciascun profilo tipo
di impresa (profili_esempio in testa al file: ufficio, negozio, hotel, artigiano, manifattura, logistica...) con
l'interesse per quel profilo. Arrivano all'API ordinati per interesse e con il nome del profilo.
"""

from __future__ import annotations

from datetime import date, timedelta
from functools import lru_cache
from pathlib import Path

import yaml

FILE = Path(__file__).resolve().parent / "misure.yaml"
CUMULABILI = ("si", "nei_limiti")
INTERESSI = ("alto", "medio", "basso", "nullo")      # in quest'ordine nella pagina


@lru_cache(maxsize=1)
def _da_file(percorso: str, modificato: float) -> tuple[tuple[dict, ...], tuple[dict, ...]]:
    dati = yaml.safe_load(Path(percorso).read_text(encoding="utf-8")) or {}
    voci = tuple(m for m in dati.get("misure") or [] if isinstance(m, dict) and m.get("id") and m.get("nome"))
    profili = tuple(p for p in dati.get("profili_esempio") or [] if isinstance(p, dict) and p.get("id"))
    return voci, profili


def _carica(percorso: Path | None) -> tuple[tuple[dict, ...], tuple[dict, ...]]:
    p = percorso or FILE
    if not p.is_file():
        return (), ()
    return _da_file(str(p), p.stat().st_mtime)


def profili_esempio(percorso: Path | None = None) -> list[dict]:
    """I profili tipo di impresa usati negli esempi delle misure (id, nome, descrizione)."""
    return [dict(p) for p in _carica(percorso)[1]]


def _esempi(m: dict, nomi: dict[str, str]) -> list[dict]:
    """Esempi della misura con il nome del profilo, dal piu' al meno interessante (copie: la cache resta intatta)."""
    ordine = {v: i for i, v in enumerate(INTERESSI)}
    esempi = [dict(e) | {"profilo_nome": nomi.get(e.get("profilo"), e.get("profilo"))}
              for e in m.get("esempi") or [] if isinstance(e, dict)]
    return sorted(esempi, key=lambda e: ordine.get(e.get("interesse"), len(INTERESSI)))


def tutte(percorso: Path | None = None) -> list[dict]:
    voci, profili = _carica(percorso)
    nomi = {p["id"]: p.get("nome") or p["id"] for p in profili}
    return [dict(m) | ({"esempi": _esempi(m, nomi)} if m.get("esempi") else {}) for m in voci]


def una(misura_id: str, percorso: Path | None = None) -> dict | None:
    return next((m for m in tutte(percorso) if m["id"] == misura_id), None)


def _adatta_al_profilo(m: dict, profilo: dict | None) -> bool:
    if not profilo:
        return True
    soggetto = "aspirante_imprenditore" if profilo.get("da_costituire") else (profilo.get("soggetto") or "impresa")
    if m.get("soggetti_ammessi") and soggetto not in m["soggetti_ammessi"] and soggetto != "aspirante_imprenditore":
        return False
    dim = profilo.get("dimensione")
    return not (dim and m.get("dimensioni_ammesse") and dim not in m["dimensioni_ammesse"])


def _nel_territorio(m: dict, bando: dict, profilo: dict | None) -> bool:
    """Misure solo per alcune regioni (es. ZES unica): servono il bando o l'impresa in quelle regioni."""
    regioni = set(m.get("regioni") or [])
    if not regioni:
        return True
    if profilo and profilo.get("sedi"):
        return bool(regioni & {s.get("regione") for s in profilo["sedi"]})
    return bool(regioni & set(bando.get("territorio_regioni") or []))


def cumulabili(bando: dict, profilo: dict | None = None, percorso: Path | None = None) -> list[dict]:
    """Le misure che si possono sommare al bando: stesse categorie di spesa, cumulabili con il fondo perduto, aperte,
    adatte al profilo (se c'e'). Ritorna una versione breve per la scheda."""
    spese = set(bando.get("categorie_spesa") or [])
    if not spese:
        return []
    uscita = []
    titolo = (bando.get("titolo") or "").lower()
    for m in tutte(percorso):
        # Il bando e' la misura stessa (es. la Nuova Sabatini nel catalogo): conta il nome senza la parte tra parentesi.
        if m["nome"].split("(")[0].strip().lower() in titolo:
            continue
        cum = (m.get("cumulabilita") or {}).get("con_fondo_perduto")
        if m.get("stato") != "aperto" or cum not in CUMULABILI:
            continue
        comuni = spese & set(m.get("categorie_spesa") or [])
        if not comuni or not _adatta_al_profilo(m, profilo) or not _nel_territorio(m, bando, profilo):
            continue
        uscita.append(breve(m) | {"spese_in_comune": sorted(comuni)})
    return uscita


def nuove_per_profilo(profilo: dict | None, oggi: date, giorni: int = 30, escluse: set[str] | frozenset = frozenset(),
                      percorso: Path | None = None) -> list[dict]:
    """Le misure aperte aggiunte negli ultimi `giorni` (campo aggiunta_il) adatte al profilo, senza quelle `escluse`
    (gia' segnalate): servono all'email del lunedi' delle imprese (07/10/2026). Versione breve, le piu' recenti prima."""
    uscita = []
    for m in tutte(percorso):
        aggiunta = m.get("aggiunta_il")
        if isinstance(aggiunta, str):
            try:
                aggiunta = date.fromisoformat(aggiunta)
            except ValueError:
                aggiunta = None
        if m.get("stato") != "aperto" or not isinstance(aggiunta, date) or m["id"] in escluse:
            continue
        if not (oggi - timedelta(days=giorni) < aggiunta <= oggi):
            continue
        if not _adatta_al_profilo(m, profilo) or not _nel_territorio(m, {}, profilo):
            continue
        uscita.append(breve(m) | {"sintesi": m.get("sintesi"), "aggiunta_il": aggiunta})
    return sorted(uscita, key=lambda m: m["aggiunta_il"], reverse=True)


def _divisioni(profilo: dict) -> set[int]:
    uscita = set()
    for c in profilo.get("ateco") or []:
        testa = str(c).strip()[:2]
        if testa.isdigit():
            uscita.add(int(testa))
    return uscita


def tipo_di_impresa(profilo: dict | None) -> str | None:
    """A quale dei profili_esempio somiglia l'impresa (07/10/2026), dai requisiti, dal codice ATECO e dalla dimensione.
    None se non si capisce: meglio nessun esempio che un esempio sbagliato."""
    if not profilo:
        return None
    req = profilo.get("requisiti") or {}
    div = _divisioni(profilo)
    grande = profilo.get("dimensione") in ("media", "grande") or (profilo.get("dipendenti") or 0) >= 50
    if req.get("startup_innovativa") or req.get("pmi_innovativa"):
        return "startup"
    if req.get("agricola") or div & {1, 2, 3}:
        return "agricola"
    if req.get("turistica") or div & {55, 56}:
        return "ristorazione_ricettivo"
    if div & {47}:
        return "negozio"
    if div & {49, 50, 51, 52, 53}:
        return "logistica"
    if div & set(range(10, 34)):
        if div & {10, 11} and not grande:
            return "agricola"   # trasformazione agroalimentare (cantina, caseificio, frantoio)
        return "manifattura" if grande else "artigiano"
    if req.get("artigiana") or div & {43, 95, 96}:
        return "artigiano"
    if div & ({58, 59, 60, 61, 62, 63, 64, 65, 66, 68, 69, 70, 71, 72, 73, 74, 77, 78, 79, 80, 81, 82} | {46}):
        return "ufficio_servizi"
    return None


def per_profilo(profilo: dict | None, percorso: Path | None = None) -> dict:
    """Le misure nazionali aperte adatte al profilo (soggetto, dimensione, regioni), per la pagina "I miei bandi":
    versione breve con la sintesi e, se il profilo somiglia a uno dei profili_esempio, l'esempio pratico per quel tipo
    di impresa. Prima quelle piu' interessanti per quel tipo."""
    tipo = tipo_di_impresa(profilo)
    nomi = {p["id"]: p.get("nome") or p["id"] for p in profili_esempio(percorso)}
    ordine = {v: i for i, v in enumerate(INTERESSI)}
    uscita = []
    for m in tutte(percorso):
        if m.get("stato") != "aperto" or not _adatta_al_profilo(m, profilo):
            continue
        regioni = set(m.get("regioni") or [])
        if regioni and profilo and not regioni & {s.get("regione") for s in profilo.get("sedi") or []}:
            continue
        esempio = next((e for e in m.get("esempi") or [] if e.get("profilo") == tipo), None) if tipo else None
        if esempio and esempio.get("interesse") == "nullo":
            continue   # per questo tipo di impresa la misura non serve
        uscita.append(breve(m) | {"sintesi": (m.get("sintesi") or "").strip(),
                                  "esempio": esempio and {"testo": " ".join(str(esempio.get("esempio") or "").split()),
                                                          "interesse": esempio.get("interesse")}})
    uscita.sort(key=lambda x: ordine.get((x["esempio"] or {}).get("interesse"), len(INTERESSI)))
    return {"tipo": tipo and {"id": tipo, "nome": nomi.get(tipo, tipo)}, "misure": uscita}


def breve(m: dict) -> dict:
    b = m.get("beneficio_stimato") or {}
    return {"id": m["id"], "nome": m["nome"], "tipo": m.get("tipo"), "ente": m.get("ente"),
            "beneficio_min": b.get("percentuale_min"), "beneficio_max": b.get("percentuale_max"),
            "nota_beneficio": b.get("nota"), "cumulo": (m.get("cumulabilita") or {}).get("regola"),
            "url_ufficiale": m.get("url_ufficiale")}


def frase_cumulo(misure: list[dict]) -> str:
    """Una riga per la bozza delle campagne: "Per gli stessi investimenti si puo' sommare ..." (stima indicativa)."""
    # Una sola misura, la piu' vantaggiosa: alcune non si sommano tra loro (conto termico e iperammortamento).
    misure = sorted(misure, key=lambda m: -(m.get("beneficio_max") or 0))[:1]
    parti = []
    for m in misure:
        if m.get("beneficio_min") is not None and m.get("beneficio_max") is not None:
            stima = (f"circa {m['beneficio_min']:g}%" if m["beneficio_min"] == m["beneficio_max"]
                     else f"circa {m['beneficio_min']:g}-{m['beneficio_max']:g}%")
            parti.append(f"{m['nome']} ({stima} della spesa non coperta dal bando)")
        else:
            parti.append(m["nome"])
    if not parti:
        return ""
    return ("Per gli stessi investimenti, nei limiti delle regole sul cumulo, si può sommare anche " + "; ".join(parti)
            + ". Stima indicativa, da verificare caso per caso.")
