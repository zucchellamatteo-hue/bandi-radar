"""Il profilo d'impresa anonimo: formato e controlli (docs/PROFILO_IMPRESA.md).

E' lo stesso formato che arrivera' da Qiaro / Contract to Cash via API e dallo script delle anagrafiche di Matteo:
cambia solo chi lo manda. Tutti i campi sono facoltativi tranne il codice: se un dato manca, l'abbinamento non lo
inventa e il bando che pone quel vincolo risulta "da verificare".

Privacy (piano §2 e §8): niente nomi, codici fiscali, partite IVA, email o telefoni. Il codice e' scelto da Matteo e
la corrispondenza con l'impresa resta solo sul suo lato. Per i soci si chiede solo il risultato (impresa femminile
o giovanile si' o no), mai i dati delle persone.
"""

from __future__ import annotations

import re
from datetime import date
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from app.abbinamento import ateco
from app.abbinamento.territorio import PROVINCE, regione_della_provincia
from app.schede.campi import CATEGORIE_SPESA, FORME_GIURIDICHE, REGIONI, REQUISITI_SPECIALI, TEMI

SOGGETTI_PROFILO = ("impresa", "libero_professionista", "ente_terzo_settore")
REQUISITI_PROFILO = tuple(r for r in REQUISITI_SPECIALI if r != "altro")

# Cose che non devono mai entrare in bandinQiaro: codice fiscale, partita IVA, email, telefono.
_CODICE_FISCALE = re.compile(r"\b[A-Z]{6}\d{2}[A-Z]\d{2}[A-Z]\d{3}[A-Z]\b", re.IGNORECASE)
_PARTITA_IVA = re.compile(r"(?<!\d)\d{11}(?!\d)")
_EMAIL = re.compile(r"[\w.+-]+@[\w-]+\.[\w.]+")
_TELEFONO = re.compile(r"(?<!\d)(\+39)?\s?3\d{2}[\s.]?\d{6,7}(?!\d)")


def _niente_dati_personali(testo: str | None, campo: str) -> str | None:
    if testo is None:
        return None
    for regola, cosa in ((_CODICE_FISCALE, "un codice fiscale"), (_PARTITA_IVA, "una partita IVA"),
                         (_EMAIL, "un indirizzo email"), (_TELEFONO, "un numero di telefono")):
        if regola.search(testo):
            raise ValueError(f"{campo}: sembra contenere {cosa}. I profili sono anonimi: toglilo.")
    return testo


class Sede(BaseModel):
    model_config = ConfigDict(extra="forbid")

    tipo: Literal["legale", "operativa", "legale_e_operativa"] = "legale_e_operativa"
    regione: str | None = None          # sigla: LOM, EMR, BZ... (si ricava dalla provincia se manca)
    provincia: str | None = None        # sigla: MI, BO...
    comune: str | None = Field(None, max_length=80)

    @field_validator("provincia")
    @classmethod
    def _provincia(cls, v: str | None) -> str | None:
        if v in (None, ""):
            return None
        v = v.strip().upper()
        if v not in PROVINCE:
            raise ValueError(f"provincia sconosciuta: {v}")
        return v

    @field_validator("regione")
    @classmethod
    def _regione(cls, v: str | None) -> str | None:
        if v in (None, ""):
            return None
        if v not in REGIONI:
            raise ValueError(f"regione sconosciuta: {v} (usa le sigle: {', '.join(REGIONI)})")
        return v

    @model_validator(mode="after")
    def _coerenza(self) -> "Sede":
        dalla_provincia = regione_della_provincia(self.provincia)
        if dalla_provincia and self.regione and self.regione != dalla_provincia:
            raise ValueError(f"la provincia {self.provincia} non è in {self.regione}")
        self.regione = self.regione or dalla_provincia
        return self


class Profilo(BaseModel):
    """Il profilo anonimo. `requisiti`: solo quelli noti (vero/falso); un requisito assente vuol dire "non lo so"."""
    model_config = ConfigDict(extra="forbid")

    codice: str = Field(..., pattern=r"^[A-Za-z0-9._-]{1,40}$")
    soggetto: Literal["impresa", "libero_professionista", "ente_terzo_settore"] | None = "impresa"
    da_costituire: bool = False
    forma_giuridica: str | None = None
    sedi: list[Sede] = Field(default_factory=list, max_length=20)
    ateco: list[str] = Field(default_factory=list, max_length=10)     # il primo e' il principale
    ateco_versione: Literal["2007", "2025"] = "2025"
    attivita: str | None = Field(None, max_length=500)                 # descrizione libera, per l'IA piu' avanti
    dimensione: Literal["micro", "piccola", "media", "grande"] | None = None
    dipendenti: float | None = Field(None, ge=0)
    fatturato: float | None = Field(None, ge=0)                        # euro, ultimo bilancio
    totale_bilancio: float | None = Field(None, ge=0)                  # euro
    data_costituzione: date | None = None
    requisiti: dict[str, bool] = Field(default_factory=dict)
    temi: list[str] = Field(default_factory=list)
    categorie_spesa: list[str] = Field(default_factory=list)
    importo_progetto: float | None = Field(None, ge=0)
    note: str | None = Field(None, max_length=500)                     # promemoria di Matteo, niente dati personali

    @field_validator("codice")
    @classmethod
    def _codice(cls, v: str) -> str:
        if _CODICE_FISCALE.search(v) or _PARTITA_IVA.search(v):
            raise ValueError("il codice sembra un codice fiscale o una partita IVA: usa un codice interno (es. C001)")
        return v

    @field_validator("attivita", "note")
    @classmethod
    def _testi(cls, v: str | None, info) -> str | None:
        return _niente_dati_personali(v, info.field_name)

    @field_validator("forma_giuridica")
    @classmethod
    def _forma(cls, v: str | None) -> str | None:
        if v and v not in FORME_GIURIDICHE:
            raise ValueError(f"forma giuridica non ammessa: {v}")
        return v or None

    @field_validator("ateco")
    @classmethod
    def _ateco(cls, v: list[str]) -> list[str]:
        codici = []
        for c in v:
            if not c or not c.strip():
                continue
            n = ateco.normalizza(c)
            if not n or len(n) == 1:
                raise ValueError(f"codice ATECO non valido: {c} (es. 62.01.00)")
            codici.append(n)
        return codici

    @field_validator("requisiti")
    @classmethod
    def _requisiti(cls, v: dict[str, bool]) -> dict[str, bool]:
        sconosciuti = set(v) - set(REQUISITI_PROFILO)
        if sconosciuti:
            raise ValueError(f"requisiti sconosciuti: {', '.join(sorted(sconosciuti))}")
        return v

    @field_validator("temi")
    @classmethod
    def _temi(cls, v: list[str]) -> list[str]:
        if set(v) - set(TEMI):
            raise ValueError(f"temi sconosciuti: {', '.join(sorted(set(v) - set(TEMI)))}")
        return v

    @field_validator("categorie_spesa")
    @classmethod
    def _spese(cls, v: list[str]) -> list[str]:
        if set(v) - set(CATEGORIE_SPESA):
            raise ValueError(f"categorie di spesa sconosciute: {', '.join(sorted(set(v) - set(CATEGORIE_SPESA)))}")
        return v

    @model_validator(mode="after")
    def _costituzione(self) -> "Profilo":
        if self.da_costituire and self.data_costituzione:
            raise ValueError("un'impresa da costituire non ha la data di costituzione")
        if self.data_costituzione and self.data_costituzione > date.today():
            raise ValueError("la data di costituzione è nel futuro")
        return self

    def per_regole(self) -> dict:
        """Il dizionario che usano le regole (app/abbinamento/regole.py)."""
        return self.model_dump(mode="python")
