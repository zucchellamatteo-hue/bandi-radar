"""Lettura e controllo del registro delle fonti (cartella fonti/, file YAML).

Il registro e' un file di configurazione: qui si legge, si controlla che sia ben
formato e si espone come elenco di oggetti Fonte. Non si scarica nulla.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from datetime import date
from pathlib import Path

import yaml

CARTELLA_FONTI = Path(__file__).resolve().parents[2] / "fonti"

TIPI = {"ue", "nazionale", "regione", "camera", "capoluogo", "provincia", "fondazione", "contesto"}
MODALITA = {"html", "rss", "api", "browser"}
FREQUENZE = {"giornaliera", "tre_a_settimana", "settimanale", "quindicinale", "mensile"}
STATI = {"attiva", "da_verificare", "difficile", "esclusa"}

_ID_VALIDO = re.compile(r"^[a-z0-9_]+$")
_CAMPI_NOTI = {
    "id", "nome", "ente", "tipo", "territorio", "url", "modalita", "feed_url",
    "piattaforma", "frequenza", "stato", "verificato_il", "note",
}


@dataclass
class Fonte:
    id: str
    nome: str
    ente: str
    tipo: str
    territorio: str
    url: str
    modalita: str
    frequenza: str
    stato: str
    feed_url: str | None = None
    piattaforma: str | None = None
    verificato_il: date | None = None
    note: str = ""
    file: str = ""  # nome del file YAML di provenienza

    @property
    def indirizzo_da_controllare(self) -> str:
        """L'indirizzo che l'osservatore usa davvero: il feed/API se c'e', altrimenti la pagina."""
        if self.modalita in {"rss", "api"} and self.feed_url:
            return self.feed_url
        return self.url


class ErroreRegistro(ValueError):
    """Il registro contiene voci mal formate; il messaggio elenca tutti i problemi."""


def _testo(valore: object) -> str:
    return "" if valore is None else str(valore).strip()


def _controlla_voce(voce: dict, file: str, posizione: int) -> tuple[Fonte | None, list[str]]:
    errori: list[str] = []
    dove = f"{file}, voce {posizione} (id={voce.get('id', '?')})"

    sconosciuti = set(voce) - _CAMPI_NOTI
    if sconosciuti:
        errori.append(f"{dove}: campi non previsti: {', '.join(sorted(sconosciuti))}")

    valori = {campo: _testo(voce.get(campo)) for campo in _CAMPI_NOTI}
    for campo in ("id", "nome", "ente", "tipo", "territorio", "modalita", "frequenza", "stato"):
        if not valori[campo]:
            errori.append(f"{dove}: manca il campo obbligatorio '{campo}'")
    # L'indirizzo puo' mancare solo se la fonte non e' ancora stata verificata o e' stata scartata.
    if not valori["url"] and valori["stato"] in {"attiva", ""}:
        errori.append(f"{dove}: una fonte attiva deve avere url")

    if valori["id"] and not _ID_VALIDO.match(valori["id"]):
        errori.append(f"{dove}: id non valido (solo minuscole, numeri e _)")
    for campo, ammessi in (("tipo", TIPI), ("modalita", MODALITA), ("frequenza", FREQUENZE), ("stato", STATI)):
        if valori[campo] and valori[campo] not in ammessi:
            errori.append(f"{dove}: {campo} '{valori[campo]}' non ammesso (valori: {', '.join(sorted(ammessi))})")
    for campo in ("url", "feed_url"):
        if valori[campo] and not valori[campo].startswith(("http://", "https://")):
            errori.append(f"{dove}: {campo} deve iniziare con http:// o https://")
    if valori["modalita"] in {"rss", "api"} and not valori["feed_url"] and valori["stato"] == "attiva":
        errori.append(f"{dove}: modalita '{valori['modalita']}' richiede feed_url")

    verificato_il: date | None = None
    grezzo = voce.get("verificato_il")
    if isinstance(grezzo, date):
        verificato_il = grezzo
    elif _testo(grezzo):
        try:
            verificato_il = date.fromisoformat(_testo(grezzo))
        except ValueError:
            errori.append(f"{dove}: verificato_il deve essere una data AAAA-MM-GG")

    if errori:
        return None, errori
    return (
        Fonte(
            id=valori["id"],
            nome=valori["nome"],
            ente=valori["ente"],
            tipo=valori["tipo"],
            territorio=valori["territorio"],
            url=valori["url"],
            modalita=valori["modalita"],
            frequenza=valori["frequenza"],
            stato=valori["stato"],
            feed_url=valori["feed_url"] or None,
            piattaforma=valori["piattaforma"] or None,
            verificato_il=verificato_il,
            note=valori["note"],
            file=file,
        ),
        [],
    )


def carica_registro(cartella: Path = CARTELLA_FONTI) -> list[Fonte]:
    """Legge tutti i file *.yaml della cartella e ritorna le fonti, in ordine di file e posizione.

    Solleva ErroreRegistro se anche una sola voce e' mal formata o se due voci hanno lo stesso id.
    """
    fonti: list[Fonte] = []
    errori: list[str] = []
    visti: dict[str, str] = {}

    for percorso in sorted(cartella.glob("*.yaml")):
        try:
            contenuto = yaml.safe_load(percorso.read_text(encoding="utf-8")) or []
        except yaml.YAMLError as exc:
            posizione = getattr(exc, "problem_mark", None)
            riga = f" alla riga {posizione.line + 1}" if posizione is not None else ""
            errori.append(f"{percorso.name}: file YAML mal formato{riga} ({getattr(exc, 'problem', exc)}). "
                          "Un ':' seguito da spazio dentro un testo va messo tra virgolette.")
            continue
        if not isinstance(contenuto, list):
            errori.append(f"{percorso.name}: il file deve contenere un elenco di voci (righe che iniziano con '- ')")
            continue
        for posizione, voce in enumerate(contenuto, start=1):
            if not isinstance(voce, dict):
                errori.append(f"{percorso.name}, voce {posizione}: non e' una voce con campi")
                continue
            fonte, errori_voce = _controlla_voce(voce, percorso.name, posizione)
            errori.extend(errori_voce)
            if fonte is None:
                continue
            if fonte.id in visti:
                errori.append(f"{percorso.name}: id '{fonte.id}' gia' usato in {visti[fonte.id]}")
                continue
            visti[fonte.id] = percorso.name
            fonti.append(fonte)

    if errori:
        raise ErroreRegistro("\n".join(errori))
    return fonti
