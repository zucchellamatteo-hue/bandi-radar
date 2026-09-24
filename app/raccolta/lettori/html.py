"""Osservatore delle pagine HTML: scarica l'elenco, estrae i link candidati e li confronta con quelli gia' visti.

Niente IA: e' un confronto tra la pagina di oggi e quella di ieri. Ogni link nuovo con un titolo sensato
diventa un annuncio; se la pagina risponde ma non si legge piu' nessun link, e' cambiata la struttura.
"""

from __future__ import annotations

import hashlib
import re
from urllib.parse import urljoin, urlsplit

import httpx
from bs4 import BeautifulSoup

from app.fonti.registro import Fonte
from app.raccolta.date import leggi_data
from app.raccolta.modelli import Annuncio, Lettura
from app.raccolta.scarica import scarica

LUNGHEZZA_MINIMA_TITOLO = 18
_TESTI_GENERICI = re.compile(
    r"^(leggi( di piu'| tutto)?|vai( alla pagina)?|scopri( di piu')?|dettagli|apri|continua|home|privacy|cookie|"
    r"accedi|login|contatti|mappa del sito|torna su|scarica|download|prev|next|precedente|successivo)\b",
    re.IGNORECASE,
)
_ESTENSIONI_FILE = (".pdf", ".doc", ".docx", ".xls", ".xlsx", ".zip", ".p7m", ".odt", ".jpg", ".png")
_SPAZI = re.compile(r"\s+")


def _contenitore(pagina: BeautifulSoup):
    for tag in pagina(["script", "style", "noscript", "header", "footer", "nav", "aside", "form"]):
        tag.decompose()
    return pagina.find("main") or pagina.find(id=re.compile("content|main|contenuto", re.I)) or pagina.body or pagina


def estrai_link(html: str, url_pagina: str) -> list[Annuncio]:
    """Link candidati: dentro il contenuto, con testo lungo e non generico, non file, non ancore."""
    pagina = BeautifulSoup(html, "lxml")
    radice = _contenitore(pagina)
    host = urlsplit(url_pagina).netloc
    visti: set[str] = set()
    annunci: list[Annuncio] = []
    for a in radice.find_all("a", href=True):
        href = a["href"].strip()
        if not href or href.startswith(("#", "mailto:", "tel:", "javascript:")):
            continue
        url = urljoin(url_pagina, href).split("#")[0]
        if url in visti or url.rstrip("/") == url_pagina.rstrip("/"):
            continue
        testo = _SPAZI.sub(" ", a.get_text(" ")).strip()
        if len(testo) < LUNGHEZZA_MINIMA_TITOLO or _TESTI_GENERICI.match(testo):
            continue
        if url.lower().endswith(_ESTENSIONI_FILE) and urlsplit(url).netloc != host:
            continue
        visti.add(url)
        # Data: un <time> o una data scritta nel blocco che contiene il link.
        blocco = a.find_parent(["article", "li", "tr", "div"]) or a
        tempo = blocco.find("time")
        data = leggi_data(tempo.get("datetime") or tempo.get_text()) if tempo else leggi_data(blocco.get_text(" ")[:400])
        annunci.append(Annuncio(url=url, titolo=testo[:300], pubblicato_il=data))
    return annunci


def leggi(fonte: Fonte, client: httpx.Client) -> Lettura:
    risposta = scarica(client, fonte.url, accept="text/html")
    risposta.raise_for_status()
    annunci = estrai_link(risposta.text, str(risposta.url))
    impronta = hashlib.sha256(risposta.content).hexdigest()[:32]
    return Lettura(annunci=annunci, codice_http=risposta.status_code, byte=len(risposta.content), impronta_pagina=impronta)
