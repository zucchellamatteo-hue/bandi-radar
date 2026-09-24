"""Oggetti scambiati tra lettori e raccolta."""

from __future__ import annotations

import hashlib
from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class Annuncio:
    """Un elemento trovato in una fonte: link, titolo e, se ci sono, riassunto e data."""

    url: str
    titolo: str
    riassunto: str | None = None
    pubblicato_il: datetime | None = None
    dati: dict = field(default_factory=dict)

    @property
    def impronta(self) -> str:
        base = (self.titolo.strip() + "\n" + (self.riassunto or "").strip()).encode("utf-8")
        return hashlib.sha256(base).hexdigest()[:32]


@dataclass
class Lettura:
    """Risultato della lettura di una fonte."""

    annunci: list[Annuncio]
    codice_http: int | None = None
    byte: int = 0
    impronta_pagina: str | None = None   # hash del contenuto scaricato
    messaggio: str = ""
