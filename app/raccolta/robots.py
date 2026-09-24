"""Lettura di robots.txt con le regole moderne (caratteri jolly * e $, vince la regola piu' lunga, a parita' vince Allow).

La libreria standard non capisce i caratteri jolly e sbaglia su molti siti italiani: per questo un lettore nostro.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from urllib.parse import urlsplit


@dataclass
class Regole:
    allow: list[str] = field(default_factory=list)
    disallow: list[str] = field(default_factory=list)
    crawl_delay: float | None = None


def _regex(modello: str) -> re.Pattern:
    parti = [re.escape(p) for p in modello.split("*")]
    testo = ".*".join(parti)
    if testo.endswith(re.escape("$")):
        testo = testo[: -len(re.escape("$"))] + "$"
    return re.compile("^" + testo)


def analizza(testo: str, user_agent: str) -> Regole:
    """Estrae le regole per il nostro User-Agent (per nome, altrimenti il gruppo '*')."""
    gruppi: dict[str, Regole] = {}
    agenti_correnti: list[str] = []
    ultimo_era_agente = False
    nome = user_agent.split("/")[0].lower()
    for riga in testo.splitlines():
        riga = riga.split("#", 1)[0].strip()
        if not riga or ":" not in riga:
            continue
        chiave, valore = (x.strip() for x in riga.split(":", 1))
        chiave = chiave.lower()
        if chiave == "user-agent":
            if not ultimo_era_agente:
                agenti_correnti = []
            agenti_correnti.append(valore.lower())
            gruppi.setdefault(valore.lower(), Regole())
            ultimo_era_agente = True
            continue
        ultimo_era_agente = False
        for a in agenti_correnti:
            r = gruppi[a]
            if chiave == "allow" and valore:
                r.allow.append(valore)
            elif chiave == "disallow" and valore:
                r.disallow.append(valore)
            elif chiave == "crawl-delay":
                try:
                    r.crawl_delay = float(valore)
                except ValueError:
                    pass
    for a, r in gruppi.items():
        if a != "*" and a in nome:
            return r
    return gruppi.get("*", Regole())


def permesso(regole: Regole, url: str) -> bool:
    parti = urlsplit(url)
    percorso = parti.path or "/"
    if parti.query:
        percorso += "?" + parti.query
    migliore_lunghezza, esito = -1, True
    for lista, valore in ((regole.allow, True), (regole.disallow, False)):
        for modello in lista:
            if _regex(modello).match(percorso):
                if len(modello) > migliore_lunghezza or (len(modello) == migliore_lunghezza and valore):
                    migliore_lunghezza, esito = len(modello), valore
    return esito
