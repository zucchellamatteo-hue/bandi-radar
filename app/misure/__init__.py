"""Misure nazionali sugli investimenti (05/10/2026, richiesta di Matteo): conto termico, iperammortamento e simili.

Non sono bandi: sono norme sempre aperte (o a sportello permanente) che danno un beneficio sugli investimenti e spesso
si sommano ai bandi. Hanno una scheda a parte, scritta e verificata a mano in app/misure/misure.yaml (come il registro
delle fonti: aggiungere una misura e' aggiungere una voce), e compaiono:
- nella pagina "Misure nazionali";
- nella scheda di un bando, come "si puo' sommare con", quando le spese del bando sono tra gli investimenti della
  misura e la misura e' cumulabile con un contributo a fondo perduto;
- nella bozza delle campagne, con il beneficio stimato in percentuale della spesa (indicativo).
"""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path

import yaml

FILE = Path(__file__).resolve().parent / "misure.yaml"
CUMULABILI = ("si", "nei_limiti")


@lru_cache(maxsize=1)
def _da_file(percorso: str, modificato: float) -> tuple[dict, ...]:
    dati = yaml.safe_load(Path(percorso).read_text(encoding="utf-8")) or {}
    return tuple(m for m in dati.get("misure") or [] if isinstance(m, dict) and m.get("id") and m.get("nome"))


def tutte(percorso: Path | None = None) -> list[dict]:
    p = percorso or FILE
    if not p.is_file():
        return []
    return [dict(m) for m in _da_file(str(p), p.stat().st_mtime)]


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
