"""Osservatore delle pagine HTML: scarica l'elenco, estrae i link candidati e li confronta con quelli gia' visti.

Niente IA: e' un confronto tra la pagina di oggi e quella di ieri. Ogni link nuovo con un titolo sensato
diventa un annuncio; se la pagina risponde ma non si legge piu' nessun link, e' cambiata la struttura.
"""

from __future__ import annotations

import hashlib
import re
from datetime import datetime, timedelta, timezone
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
_SESSIONE = re.compile(r";jsessionid=[^?#]*", re.IGNORECASE)


_RUOLI_DI_CORNICE = re.compile("banner|contentinfo|navigation", re.I)


def _e_cornice(tag) -> bool:
    """Testata o pie' di pagina del sito: non contiene il contenuto principale."""
    return tag.find(["main", "article"]) is None


def _pulisci(pagina: BeautifulSoup) -> None:
    """Toglie cio' che non e' contenuto: script, menu, testata e pie' di pagina del sito (non quelli dentro le schede)."""
    for tag in pagina(["script", "style", "noscript"]):
        tag.decompose()
    # Un <nav> non chiuso bene (Camera di Torino) finisce per contenere tutta la pagina: si toglie solo se non ha dentro il contenuto.
    for tag in list(pagina.find_all("nav")):
        if not tag.decomposed and _e_cornice(tag):
            tag.decompose()
    for tag in list(pagina.find_all(["header", "footer", "aside", "div"], role=_RUOLI_DI_CORNICE)):
        if _e_cornice(tag):
            tag.decompose()
    corpo = pagina.body
    if corpo is not None:
        for figlio in list(corpo.find_all(["header", "footer"], recursive=False)):
            if _e_cornice(figlio):
                figlio.decompose()


def _contenitori(pagina: BeautifulSoup) -> list:
    """Prima il contenuto principale; se non da' nulla, tutta la pagina."""
    principale = pagina.find("main") or pagina.find(id=re.compile("^(content|main|contenuto|main-content|mainContent)$", re.I))
    corpo = pagina.body or pagina
    return [principale, corpo] if principale is not None and principale is not corpo else [corpo]


def estrai_link(html: str, url_pagina: str, selettore: str | None = None) -> list[Annuncio]:
    """Link candidati: dentro il contenuto, con testo lungo e non generico, non file, non ancore.

    Con `selettore` (CSS, dal campo richiesta.selettore del registro) si guardano solo le parti indicate:
    serve per le pagine dove menu e servizi del sito si mescolano all'elenco dei bandi.
    """
    pagina = BeautifulSoup(html, "lxml")
    _pulisci(pagina)
    radici = pagina.select(selettore) if selettore else _contenitori(pagina)
    if selettore:
        annunci: list[Annuncio] = []
        visti: set[str] = set()
        for radice in radici:
            for a in _link_in(radice, url_pagina):
                if a.url not in visti:
                    visti.add(a.url)
                    annunci.append(a)
        return annunci
    for radice in radici:
        annunci = _link_in(radice, url_pagina)
        if annunci:
            return annunci
    return []


def _titolo_della_scheda(a) -> str | None:
    riga = a.find_parent("tr")
    if riga is not None:
        # Tabelle "Oggetto | Scadenza | Dettaglio": il titolo e' la cella piu' lunga della riga.
        celle = [_SPAZI.sub(" ", c.get_text(" ")).strip() for c in riga.find_all(["td", "th"])]
        if celle:
            return max(celle, key=len)
    scheda = a.find_parent(["article", "li", "div", "tr", "section"])
    for _ in range(3):
        if scheda is None:
            return None
        titolo = scheda.find(["h1", "h2", "h3", "h4", "h5"])
        if titolo is not None:
            return _SPAZI.sub(" ", titolo.get_text(" ")).strip()
        scheda = scheda.find_parent(["article", "li", "div", "tr", "section"])
    return None


def _link_in(radice, url_pagina: str) -> list[Annuncio]:
    host = urlsplit(url_pagina).netloc
    visti: set[str] = set()
    annunci: list[Annuncio] = []
    for a in radice.find_all("a", href=True):
        href = a["href"].strip()
        if not href or href.startswith(("#", "mailto:", "tel:", "javascript:")):
            continue
        # Il codice di sessione (;jsessionid=...) cambia a ogni visita: senza toglierlo ogni link sembrerebbe nuovo.
        url = _SESSIONE.sub("", urljoin(url_pagina, href).split("#")[0])
        if url in visti or url.rstrip("/") == url_pagina.rstrip("/"):
            continue
        testo = _SPAZI.sub(" ", a.get_text(" ")).strip()
        if len(testo) < LUNGHEZZA_MINIMA_TITOLO or _TESTI_GENERICI.match(testo):
            # "Scopri di piu'", "Vai": il titolo e' nel titolo della scheda che contiene il link.
            testo = _titolo_della_scheda(a) or ""
            if len(testo) < LUNGHEZZA_MINIMA_TITOLO:
                continue
        if url.lower().endswith(_ESTENSIONI_FILE) and urlsplit(url).netloc != host:
            continue
        visti.add(url)
        # Data: un <time> o una data scritta nel blocco che contiene il link.
        blocco = a.find_parent(["article", "li", "tr", "div"]) or a
        tempo = blocco.find("time")
        data = leggi_data(tempo.get("datetime") or tempo.get_text()) if tempo else leggi_data(blocco.get_text(" ")[:400])
        dati: dict = {}
        if data is not None and data > datetime.now(timezone.utc) + timedelta(days=1):
            # Una data nel futuro non e' la pubblicazione: quasi sempre e' la scadenza scritta accanto al titolo.
            dati["scadenza"] = data.date().isoformat()
            data = None
        annunci.append(Annuncio(url=url, titolo=testo[:300], pubblicato_il=data, dati=dati))
    return annunci


def leggi(fonte: Fonte, client: httpx.Client) -> Lettura:
    extra = fonte.richiesta.get("intestazioni")
    if extra:
        risposta = client.get(fonte.url, headers={"Accept": "text/html", **extra})
    else:
        risposta = scarica(client, fonte.url, accept="text/html", ignora_robots=fonte.ignora_robots)
    risposta.raise_for_status()
    annunci = estrai_link(risposta.text, str(risposta.url), fonte.richiesta.get("selettore"))
    impronta = hashlib.sha256(risposta.content).hexdigest()[:32]
    return Lettura(annunci=annunci, codice_http=risposta.status_code, byte=len(risposta.content), impronta_pagina=impronta)
