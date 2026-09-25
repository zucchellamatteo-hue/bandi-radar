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
MODALITA = {"html", "rss", "api", "browser", "sitemap"}
FREQUENZE = {"giornaliera", "tre_a_settimana", "settimanale", "quindicinale", "mensile"}
STATI = {"attiva", "da_verificare", "difficile", "esclusa"}

_ID_VALIDO = re.compile(r"^[a-z0-9_]+$")
_CAMPI_NOTI = {
    "id", "nome", "ente", "tipo", "territorio", "url", "modalita", "feed_url",
    "piattaforma", "frequenza", "stato", "verificato_il", "note", "ignora_robots", "richiesta", "pagina_ufficiale",
}
# Regole per trovare la pagina ufficiale del bando a partire dagli annunci della fonte (app/schede/pagina_ufficiale.py).
_REGOLE_PAGINA = {"campo", "escludi", "cerca", "segui_link", "documenti", "sostituisci"}


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
    ignora_robots: bool = False  # solo per decisione esplicita di Matteo, fonte per fonte
    richiesta: dict = field(default_factory=dict)  # metodo, intestazioni, corpo_json, corpo_form, url_modello; selettore per html/browser; ipv6; elenco per api
    pagina_ufficiale: dict = field(default_factory=dict)  # campo, escludi, cerca, segui_link, documenti (fonti/README.md)
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

    ignora_robots = voce.get("ignora_robots", False)
    if not isinstance(ignora_robots, bool):
        errori.append(f"{dove}: ignora_robots deve essere true o false")
    richiesta = voce.get("richiesta") or {}
    if not isinstance(richiesta, dict) or set(richiesta) - {"metodo", "intestazioni", "corpo_json", "corpo_form", "url_modello", "selettore", "ipv6", "elenco"}:
        errori.append(f"{dove}: richiesta ammette solo metodo, intestazioni, corpo_json, corpo_form, url_modello, selettore, ipv6, elenco")

    pagina_ufficiale = voce.get("pagina_ufficiale") or {}
    errori.extend(_controlla_pagina_ufficiale(pagina_ufficiale, dove))

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
            ignora_robots=ignora_robots,
            richiesta=richiesta,
            pagina_ufficiale=pagina_ufficiale,
            file=file,
        ),
        [],
    )


def _controlla_pagina_ufficiale(regole: object, dove: str) -> list[str]:
    if not isinstance(regole, dict):
        return [f"{dove}: pagina_ufficiale deve essere un blocco di campi"]
    errori = []
    if set(regole) - _REGOLE_PAGINA:
        errori.append(f"{dove}: pagina_ufficiale ammette solo {', '.join(sorted(_REGOLE_PAGINA))}")
    if "campo" in regole and not isinstance(regole["campo"], str):
        errori.append(f"{dove}: pagina_ufficiale.campo e' il nome di un campo dei dati grezzi (testo)")
    for chiave in ("escludi",):
        if chiave in regole and not (isinstance(regole[chiave], list) and all(isinstance(x, str) for x in regole[chiave])):
            errori.append(f"{dove}: pagina_ufficiale.{chiave} e' un elenco di testi")
    sostituisci = regole.get("sostituisci")
    if sostituisci is not None and not (isinstance(sostituisci, dict) and all(isinstance(k, str) and isinstance(v, str)
                                                                            for k, v in sostituisci.items())):
        errori.append(f"{dove}: pagina_ufficiale.sostituisci e' un elenco di coppie testo: testo")
    cerca = regole.get("cerca")
    if cerca is not None:
        if not isinstance(cerca, dict) or not str(cerca.get("url", "")).startswith("https://") or not cerca.get("link"):
            errori.append(f"{dove}: pagina_ufficiale.cerca vuole almeno url (https://...) e link")
        elif set(cerca) - {"url", "metodo", "corpo_form", "link"}:
            errori.append(f"{dove}: pagina_ufficiale.cerca ammette solo url, metodo, corpo_form, link")
    segui = regole.get("segui_link")
    if segui is not None and not (isinstance(segui, dict) and isinstance(segui.get("testi"), list) and segui["testi"]
                                  and not set(segui) - {"testi", "stesso_sito"}):
        errori.append(f"{dove}: pagina_ufficiale.segui_link vuole un elenco testi (e, se serve, stesso_sito: true)")
    if regole.get("documenti") not in (None, "plone_api"):
        errori.append(f"{dove}: pagina_ufficiale.documenti ammette solo plone_api")
    return errori


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
