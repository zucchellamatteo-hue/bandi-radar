"""Province e regioni: sigle delle province (come nella scheda, territorio_province) -> sigla della regione
(come nel registro delle fonti e in territorio_regioni). Bolzano e Trento sono Province autonome: sigle BZ e TN
anche come "regione"."""

from __future__ import annotations

import re
import unicodedata

PROVINCE: dict[str, str] = {
    # Abruzzo
    "AQ": "ABR", "CH": "ABR", "PE": "ABR", "TE": "ABR",
    # Basilicata
    "MT": "BAS", "PZ": "BAS",
    # Province autonome
    "BZ": "BZ", "TN": "TN",
    # Calabria
    "CS": "CAL", "CZ": "CAL", "KR": "CAL", "RC": "CAL", "VV": "CAL",
    # Campania
    "AV": "CAM", "BN": "CAM", "CE": "CAM", "NA": "CAM", "SA": "CAM",
    # Emilia-Romagna
    "BO": "EMR", "FC": "EMR", "FE": "EMR", "MO": "EMR", "PC": "EMR", "PR": "EMR", "RA": "EMR", "RE": "EMR", "RN": "EMR",
    # Friuli Venezia Giulia
    "GO": "FVG", "PN": "FVG", "TS": "FVG", "UD": "FVG",
    # Lazio
    "FR": "LAZ", "LT": "LAZ", "RI": "LAZ", "RM": "LAZ", "VT": "LAZ",
    # Liguria
    "GE": "LIG", "IM": "LIG", "SP": "LIG", "SV": "LIG",
    # Lombardia
    "BG": "LOM", "BS": "LOM", "CO": "LOM", "CR": "LOM", "LC": "LOM", "LO": "LOM", "MB": "LOM", "MI": "LOM", "MN": "LOM",
    "PV": "LOM", "SO": "LOM", "VA": "LOM",
    # Marche
    "AN": "MAR", "AP": "MAR", "FM": "MAR", "MC": "MAR", "PU": "MAR",
    # Molise
    "CB": "MOL", "IS": "MOL",
    # Piemonte
    "AL": "PIE", "AT": "PIE", "BI": "PIE", "CN": "PIE", "NO": "PIE", "TO": "PIE", "VB": "PIE", "VC": "PIE",
    # Puglia
    "BA": "PUG", "BR": "PUG", "BT": "PUG", "FG": "PUG", "LE": "PUG", "TA": "PUG",
    # Sardegna (dal 2025 anche le nuove province: si tengono le sigle vecchie e le nuove)
    "CA": "SAR", "NU": "SAR", "OR": "SAR", "SS": "SAR", "SU": "SAR", "OT": "SAR", "OG": "SAR", "VS": "SAR", "CI": "SAR",
    "GL": "SAR", "MD": "SAR",
    # Sicilia
    "AG": "SIC", "CL": "SIC", "CT": "SIC", "EN": "SIC", "ME": "SIC", "PA": "SIC", "RG": "SIC", "SR": "SIC", "TP": "SIC",
    # Toscana
    "AR": "TOS", "FI": "TOS", "GR": "TOS", "LI": "TOS", "LU": "TOS", "MS": "TOS", "PI": "TOS", "PO": "TOS", "PT": "TOS",
    "SI": "TOS",
    # Umbria
    "PG": "UMB", "TR": "UMB",
    # Valle d'Aosta
    "AO": "VDA",
    # Veneto
    "BL": "VEN", "PD": "VEN", "RO": "VEN", "TV": "VEN", "VE": "VEN", "VI": "VEN", "VR": "VEN",
}

NOMI_REGIONI: dict[str, str] = {
    "ABR": "Abruzzo", "BAS": "Basilicata", "BZ": "Provincia di Bolzano", "CAL": "Calabria", "CAM": "Campania",
    "EMR": "Emilia-Romagna", "FVG": "Friuli Venezia Giulia", "LAZ": "Lazio", "LIG": "Liguria", "LOM": "Lombardia",
    "MAR": "Marche", "MOL": "Molise", "PIE": "Piemonte", "PUG": "Puglia", "SAR": "Sardegna", "SIC": "Sicilia",
    "TN": "Provincia di Trento", "TOS": "Toscana", "UMB": "Umbria", "VDA": "Valle d'Aosta", "VEN": "Veneto",
}


def regione_della_provincia(sigla: str | None) -> str | None:
    return PROVINCE.get((sigla or "").strip().upper())


def nome_comune(nome: str | None) -> str:
    """Forma confrontabile del nome di un comune: minuscole, senza accenti, senza "comune di", spazi semplici."""
    testo = unicodedata.normalize("NFKD", nome or "").encode("ascii", "ignore").decode().lower()
    testo = re.sub(r"^\s*(comune|citta|citta metropolitana)\s+di\s+", "", testo)
    return re.sub(r"[^a-z0-9]+", " ", testo).strip()
