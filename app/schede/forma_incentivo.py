"""Forma dell'incentivo (richiesta di Matteo del 02/10/2026): di che aiuto si tratta (fondo perduto, finanziamento
agevolato, servizi...), con che quota della spesa e fino a quanto, anche diverso per gruppi di beneficiari.

Le schede nuove la compilano dai documenti (blocco `forma_incentivo`, app/schede/prompt_scheda.md). Per quelle scritte
prima, `ricava` la ricostruisce dai campi che la scheda ha gia' (tipi di agevolazione, percentuali, massimali, blocco
`finanziamento`, percentuali per dimensione, linee) e la segna come ricavata: la plancia lo dice, perche' e' meno
precisa di una lettura dei documenti."""
from __future__ import annotations

from decimal import Decimal

NOMI = {
    "fondo_perduto": "fondo perduto", "finanziamento_agevolato": "finanziamento agevolato",
    "credito_imposta": "credito d'imposta", "garanzia": "garanzia", "voucher": "voucher",
    "servizi": "servizi gratuiti", "premio": "premio", "contributo_interessi": "contributo in conto interessi",
    "altro": "altra forma",
}
DIMENSIONI = {"micro": "Micro imprese", "piccola": "Piccole imprese", "media": "Medie imprese", "grande": "Grandi imprese"}


def _num(v):
    if isinstance(v, bool):
        return None
    if isinstance(v, (int, float, Decimal)):
        return float(v)
    return None


def euro(v) -> str:
    return f"{_num(v):,.0f} €".replace(",", ".")


def percento(v) -> str:
    n = _num(v)
    return f"{n:g}%".replace(".", ",")


def _condizioni_prestito(fin: dict) -> str | None:
    parti = []
    tasso = {"zero": "tasso zero", "fisso": "tasso fisso", "variabile": "tasso variabile",
             "riferimento_ue": "tasso ridotto rispetto al riferimento UE"}.get(fin.get("tasso_tipo") or "")
    if fin.get("tasso_valore") is not None and fin.get("tasso_tipo") != "zero":
        tasso = f"{tasso or 'tasso'} {percento(fin['tasso_valore'])}"
    if tasso:
        parti.append(tasso)
    if fin.get("durata_mesi"):
        parti.append(f"durata {int(_num(fin['durata_mesi']))} mesi")
    if fin.get("preammortamento_mesi"):
        parti.append(f"preammortamento {int(_num(fin['preammortamento_mesi']))} mesi")
    if fin.get("garanzie_richieste"):
        parti.append(f"garanzie: {fin['garanzie_richieste']}")
    return ", ".join(parti) or fin.get("tasso_note") or None


def _forme(tipi: list[str], percentuale, massimale, b: dict) -> list[dict]:
    """Le forme di una riga. `percentuale` e `massimale` sono quelli della quota a fondo perduto (o dell'unica forma)."""
    fin = b.get("finanziamento") or {}
    forme = []
    unica = len(tipi) == 1
    for t in tipi:
        if t == "fondo_perduto":
            forme.append({"forma": t, "percentuale": percentuale, "massimale": massimale, "condizioni": None})
        elif t == "finanziamento_agevolato":
            forme.append({"forma": t, "percentuale": fin.get("percentuale_finanziamento") if not unica or percentuale is None
                          else percentuale, "massimale": b.get("finanziamento_massimo") or (massimale if unica else None),
                          "condizioni": _condizioni_prestito(fin)})
        elif t == "garanzia":
            copertura = fin.get("garanzia_pubblica_copertura")
            forme.append({"forma": t, "percentuale": None, "massimale": massimale if unica else None,
                          "condizioni": f"copre il {percento(copertura)} del prestito" if copertura is not None else None})
        else:
            forme.append({"forma": t, "percentuale": percentuale if unica else None,
                          "massimale": massimale if unica else None, "condizioni": None})
    return forme


def _tipi(b: dict) -> list[str]:
    tipi = [t for t in (b.get("tipi_agevolazione") or []) if t in NOMI]
    if not tipi and b.get("tipo_agevolazione") in NOMI:
        tipi = [b["tipo_agevolazione"]]
    # L'ordine conta per la lettura: prima il fondo perduto, poi il prestito.
    ordine = list(NOMI)
    return sorted(dict.fromkeys(tipi), key=ordine.index)


def descrivi(riga: dict) -> str:
    """Una riga in una frase: "fondo perduto 30% (fino a 50.000 €) + finanziamento agevolato 70%"."""
    parti = []
    for f in riga.get("forme") or []:
        testo = NOMI.get(f.get("forma"), f.get("forma") or "")
        if f.get("percentuale") is not None:
            testo += f" {percento(f['percentuale'])}"
        if f.get("massimale") is not None:
            testo += f" (fino a {euro(f['massimale'])})"
        parti.append(testo)
    return " + ".join(parti)


def ricava(b: dict) -> dict | None:
    """La forma dell'incentivo ricostruita dai campi della scheda; None se la scheda non dice nemmeno il tipo d'aiuto."""
    tipi = _tipi(b)
    if not tipi:
        return None
    # La percentuale base, non la massima con le maggiorazioni (che vanno nelle note): verifica del 02/10, bando 1008.
    base = (b.get("intensita") or {}).get("percentuale_base")
    massima = b.get("percentuale_fondo_perduto") if b.get("percentuale_fondo_perduto") is not None else b.get("percentuale")
    perc_fp = base if base is not None else massima
    mass_fp = b.get("fondo_perduto_massimo") or b.get("contributo_massimo")
    righe = []
    linee = [l for l in (b.get("linee") or []) if isinstance(l, dict)
             and any(l.get(k) is not None for k in ("percentuale", "contributo_massimo", "fondo_perduto_massimo"))]
    per_dim = {d: v for d, v in ((b.get("intensita") or {}).get("per_dimensione") or {}).items()
               if v is not None and d in DIMENSIONI}
    if linee:
        for l in linee:
            tipi_l = [t for t in (l.get("tipi_agevolazione") or []) if t in NOMI] or tipi
            righe.append({"per_chi": l.get("nome") or "Linea", "forme": _forme(
                tipi_l, l.get("percentuale") if l.get("percentuale") is not None and _num(l.get("percentuale")) != _num(massima)
                else perc_fp,
                l.get("fondo_perduto_massimo") or l.get("contributo_massimo") or mass_fp, b),
                "spesa_minima": l.get("spesa_minima"), "spesa_massima": l.get("spesa_massima"),
                "agevolazione_massima": None, "note": l.get("a_chi_si_rivolge")})
    elif per_dim and len(set(per_dim.values())) > 1:
        for d, v in per_dim.items():
            righe.append({"per_chi": DIMENSIONI[d], "forme": _forme(tipi, v, mass_fp, b),
                          "spesa_minima": b.get("spesa_minima"), "spesa_massima": b.get("spesa_massima"),
                          "agevolazione_massima": None, "note": None})
    else:
        righe.append({"per_chi": "Tutti i beneficiari", "forme": _forme(tipi, perc_fp, mass_fp, b),
                      "spesa_minima": b.get("spesa_minima"), "spesa_massima": b.get("spesa_massima"),
                      "agevolazione_massima": None, "note": None})
    maggiorazioni = [m for m in ((b.get("intensita") or {}).get("maggiorazioni") or []) if isinstance(m, dict)]
    note = None
    if maggiorazioni:
        note = "Maggiorazioni: " + "; ".join(
            f"{(m.get('motivo') or 'altro').replace('_', ' ')}"
            + (f" +{percento(m['punti_percentuali'])}" if m.get("punti_percentuali") is not None else "")
            + (f" ({m['note']})" if m.get("note") else "") for m in maggiorazioni)
    if len(righe) == 1:
        descrizione = descrivi(righe[0])
        descrizione = descrizione[:1].upper() + descrizione[1:]
    else:
        descrizione = ("Cambia per linea: vedi la tabella." if linee else "Cambia con la dimensione dell'impresa: vedi la tabella.")
    return {"descrizione": descrizione, "righe": righe, "note": note, "ricavata": True}


def per_la_plancia(b: dict) -> dict | None:
    """Quella compilata dai documenti, se c'e'; altrimenti quella ricavata dai campi."""
    fi = b.get("forma_incentivo")
    if isinstance(fi, dict) and (fi.get("righe") or fi.get("descrizione")):
        return {**fi, "ricavata": False}
    return ricava(b)
