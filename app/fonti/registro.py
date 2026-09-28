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
    "scorta",
}
# Regole per trovare la pagina ufficiale del bando a partire dagli annunci della fonte (app/schede/pagina_ufficiale.py).
_REGOLE_PAGINA = {"campo", "escludi", "cerca", "segui_link", "documenti", "sostituisci", "testo_dai_dati"}
# Lettura completa della fonte ("scorta": tutti i bandi ancora aperti, non solo le novita'), app/raccolta/scorta.py.
_CAMPI_SCORTA = {"url", "parametro", "inizio", "passo", "pagine", "corpo_json", "scadenza", "frequenza", "modalita",
                 "selettore", "senza_scadenza_mesi", "tutte_le_pagine"}


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
    scorta: dict = field(default_factory=dict)  # lettura completa: url, parametro, pagine, scadenza, modalita... (app/raccolta/scorta.py)
    file: str = ""  # nome del file YAML di provenienza

    @property
    def documenti_plone(self) -> bool:
        """Pagine e documenti del sito si leggono dall'API Plone/Volto (++api++): regola `documenti: plone_api` o,
        dal 27/09, qualunque fonte con piattaforma plone (Verona, La Spezia, Parma: l'HTML delle pagine e' vuoto)."""
        return self.pagina_ufficiale.get("documenti") == "plone_api" or self.piattaforma == "plone"

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
    scorta = voce.get("scorta") or {}
    errori.extend(_controlla_scorta(scorta, dove))

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
            scorta=scorta,
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
    if "testo_dai_dati" in regole and not isinstance(regole["testo_dai_dati"], str):
        errori.append(f"{dove}: pagina_ufficiale.testo_dai_dati e' il nome di un campo dei dati grezzi (testo)")
    if regole.get("documenti") not in (None, "plone_api"):
        errori.append(f"{dove}: pagina_ufficiale.documenti ammette solo plone_api")
    return errori


def _controlla_scorta(regole: object, dove: str) -> list[str]:
    if not isinstance(regole, dict):
        return [f"{dove}: scorta deve essere un blocco di campi"]
    errori = []
    if set(regole) - _CAMPI_SCORTA:
        errori.append(f"{dove}: scorta ammette solo {', '.join(sorted(_CAMPI_SCORTA))}")
    if "url" in regole and not str(regole["url"]).startswith(("http://", "https://")):
        errori.append(f"{dove}: scorta.url deve iniziare con http:// o https://")
    for chiave in ("inizio", "passo", "pagine", "senza_scadenza_mesi"):
        if chiave in regole and not (isinstance(regole[chiave], int) and not isinstance(regole[chiave], bool)
                                     and regole[chiave] >= (0 if chiave == "inizio" else 1)):
            errori.append(f"{dove}: scorta.{chiave} e' un numero intero")
    if isinstance(regole.get("pagine"), int) and regole["pagine"] > 1 and "parametro" not in regole \
            and "{pagina}" not in str(regole.get("url", "")) + str(regole.get("corpo_json", "")):
        errori.append(f"{dove}: scorta su piu' pagine vuole parametro oppure {{pagina}} in url o corpo_json")
    if "frequenza" in regole and regole["frequenza"] not in FREQUENZE:
        errori.append(f"{dove}: scorta.frequenza '{regole['frequenza']}' non ammessa")
    if "tutte_le_pagine" in regole and not isinstance(regole["tutte_le_pagine"], bool):
        errori.append(f"{dove}: scorta.tutte_le_pagine e' true o false")
    if "modalita" in regole and regole["modalita"] not in MODALITA:
        errori.append(f"{dove}: scorta.modalita '{regole['modalita']}' non ammessa")
    if "corpo_json" in regole and not isinstance(regole["corpo_json"], dict):
        errori.append(f"{dove}: scorta.corpo_json e' un blocco di campi")
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
