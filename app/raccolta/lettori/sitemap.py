"""Lettore delle sitemap XML: per i siti a pagina singola che non si lasciano leggere, la sitemap elenca
comunque tutte le pagine con la data dell'ultima modifica. Si tengono solo le pagine recenti e con un
indirizzo che parla di avvisi, bandi, contributi o novita'.
"""

from __future__ import annotations

import hashlib
import re
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta, timezone
from urllib.parse import unquote, urlsplit

import httpx

from app.fonti.registro import Fonte
from app.raccolta.date import leggi_data
from app.raccolta.modelli import Annuncio, Lettura
from app.raccolta.scarica import scarica

_NS = {"sm": "http://www.sitemaps.org/schemas/sitemap/0.9"}
PAROLE = re.compile(r"avvis|band|contribut|incentiv|agevolaz|notiz|novita|news|finanziam|voucher|impres|commerc", re.I)
GIORNI_RECENTI = 90
MASSIMO_SOTTOSITEMAP = 20


def _titolo_da_url(url: str) -> str:
    ultimo = [p for p in urlsplit(url).path.split("/") if p][-1:] or [url]
    testo = unquote(ultimo[0]).rsplit(".", 1)[0].replace("-", " ").replace("_", " ").strip()
    return (testo[:1].upper() + testo[1:]) if testo else url


def analizza_sitemap(contenuto: bytes, adesso: datetime) -> tuple[list[Annuncio], list[str]]:
    """Ritorna (annunci recenti e pertinenti, indirizzi di sotto-sitemap da leggere)."""
    contenuto = contenuto.lstrip(b" \t\r\n").removeprefix(b"\xef\xbb\xbf")
    radice = ET.fromstring(contenuto)
    limite = adesso - timedelta(days=GIORNI_RECENTI)
    figli = [s.findtext("sm:loc", default="", namespaces=_NS).strip() for s in radice.findall("sm:sitemap", _NS)]
    annunci: list[Annuncio] = []
    for u in radice.findall("sm:url", _NS):
        loc = (u.findtext("sm:loc", default="", namespaces=_NS) or "").strip()
        if not loc or not PAROLE.search(urlsplit(loc).path):
            continue
        data = leggi_data(u.findtext("sm:lastmod", default=None, namespaces=_NS))
        if data is not None and data < limite:
            continue
        annunci.append(Annuncio(url=loc, titolo=_titolo_da_url(loc), pubblicato_il=data))
    return annunci, [f for f in figli if f]


def leggi(fonte: Fonte, client: httpx.Client) -> Lettura:
    adesso = datetime.now(timezone.utc)
    da_leggere = [fonte.indirizzo_da_controllare]
    letti: set[str] = set()
    annunci: list[Annuncio] = []
    byte = 0
    impronta = hashlib.sha256()
    while da_leggere and len(letti) < MASSIMO_SOTTOSITEMAP:
        url = da_leggere.pop(0)
        if url in letti:
            continue
        letti.add(url)
        risposta = scarica(client, url, accept="application/xml, text/xml", ignora_robots=fonte.ignora_robots)
        risposta.raise_for_status()
        byte += len(risposta.content)
        impronta.update(risposta.content)
        trovati, figli = analizza_sitemap(risposta.content, adesso)
        annunci.extend(trovati)
        da_leggere.extend(figli)
    visti: set[str] = set()
    unici = [a for a in annunci if not (a.url in visti or visti.add(a.url))]
    return Lettura(annunci=unici, codice_http=200, byte=byte, impronta_pagina=impronta.hexdigest()[:32])
