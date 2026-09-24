"""Lettore dei feed RSS 2.0, RSS 1.0 (RDF) e Atom, con la sola libreria standard."""

from __future__ import annotations

import xml.etree.ElementTree as ET

import hashlib

import httpx

from app.fonti.registro import Fonte
from app.raccolta.date import leggi_data
from app.raccolta.modelli import Annuncio, Lettura
from app.raccolta.scarica import scarica
from app.raccolta.testo import pulisci_html

_NS = {
    "atom": "http://www.w3.org/2005/Atom",
    "rdf": "http://www.w3.org/1999/02/22-rdf-syntax-ns#",
    "rss1": "http://purl.org/rss/1.0/",
    "dc": "http://purl.org/dc/elements/1.1/",
    "content": "http://purl.org/rss/1.0/modules/content/",
}


def _testo(el, *percorsi: str) -> str | None:
    for p in percorsi:
        trovato = el.find(p, _NS)
        if trovato is not None:
            if trovato.text and trovato.text.strip():
                return trovato.text.strip()
            href = trovato.get("href")
            if href:
                return href.strip()
    return None


def _radice(contenuto: bytes):
    """Legge l'XML tollerando spazi o righe vuote prima della dichiarazione e piccoli errori (con lxml)."""
    contenuto = contenuto.lstrip(b" \t\r\n").removeprefix(b"\xef\xbb\xbf")
    try:
        return ET.fromstring(contenuto)
    except ET.ParseError:
        from lxml import etree

        radice = etree.fromstring(contenuto, etree.XMLParser(recover=True, huge_tree=True))
        if radice is None:
            raise
        return ET.fromstring(etree.tostring(radice))


def analizza_feed(contenuto: bytes) -> list[Annuncio]:
    radice = _radice(contenuto)
    tag = radice.tag.split("}")[-1].lower()
    annunci: list[Annuncio] = []

    if tag == "feed":  # Atom
        for voce in radice.findall("atom:entry", _NS):
            link = None
            for l in voce.findall("atom:link", _NS):
                if l.get("rel") in (None, "alternate"):
                    link = l.get("href")
                    break
            titolo = _testo(voce, "atom:title")
            if not (link and titolo):
                continue
            annunci.append(Annuncio(
                url=link, titolo=titolo,
                riassunto=pulisci_html(_testo(voce, "atom:summary", "atom:content")),
                pubblicato_il=leggi_data(_testo(voce, "atom:published", "atom:updated")),
            ))
        return annunci

    # RSS 2.0 (channel/item) oppure RSS 1.0 (rdf:RDF/item nel namespace rss1)
    voci = radice.findall("./channel/item") or radice.findall("rss1:item", _NS) or radice.findall("item")
    for voce in voci:
        link = _testo(voce, "link", "rss1:link", "guid")
        titolo = _testo(voce, "title", "rss1:title")
        if not (link and titolo):
            continue
        annunci.append(Annuncio(
            url=link, titolo=titolo,
            riassunto=pulisci_html(_testo(voce, "description", "rss1:description", "content:encoded")),
            pubblicato_il=leggi_data(_testo(voce, "pubDate", "dc:date")),
        ))
    return annunci


def leggi(fonte: Fonte, client: httpx.Client) -> Lettura:
    risposta = scarica(client, fonte.indirizzo_da_controllare, accept="application/rss+xml, application/atom+xml, application/xml, text/xml", ignora_robots=fonte.ignora_robots)
    risposta.raise_for_status()
    annunci = analizza_feed(risposta.content)
    return Lettura(annunci=annunci, codice_http=risposta.status_code, byte=len(risposta.content),
                   impronta_pagina=hashlib.sha256(risposta.content).hexdigest()[:32])
