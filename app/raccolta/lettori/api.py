"""Lettore delle API JSON e CSV. Una funzione per famiglia di piattaforma (campo `piattaforma` del registro),
piu' un lettore generico che cerca da solo titolo, link e data in qualunque JSON.
"""

from __future__ import annotations

import csv
import io
import json
from typing import Any
from urllib.parse import urljoin

import hashlib

import httpx

from app.fonti.registro import Fonte
from app.raccolta.date import leggi_data
from app.raccolta.modelli import Annuncio, Lettura
from app.raccolta.scarica import scarica
from app.raccolta.testo import pulisci_html

CHIAVI_TITOLO = ("titolo", "title", "titolo_bando", "nome", "denominazione", "oggetto", "name", "label")
CHIAVI_URL = ("url", "link", "@id", "href", "permalink", "url_bando", "pagina")
CHIAVI_RIASSUNTO = ("description", "descrizione", "riassunto", "summary", "excerpt", "contenuto", "abstract", "sottotitolo")
CHIAVI_DATA = ("effective", "published", "pubblicato_il", "data_notizia", "date", "data", "apertura_adesione",
               "data_pubblicazione", "modified", "created", "startDate", "data_apertura")


def _valore(d: dict, chiavi: tuple[str, ...]) -> Any:
    for k in chiavi:
        if k in d and d[k] not in (None, "", [], {}):
            return d[k]
    return None


def _come_testo(v: Any) -> str | None:
    """Estrae un testo da valori annidati tipici: {"rendered": ...}, {"ita-IT": ...}, [primo], ecc."""
    if v is None:
        return None
    if isinstance(v, str):
        return v.strip() or None
    if isinstance(v, (int, float)):
        return str(v)
    if isinstance(v, list):
        return _come_testo(v[0]) if v else None
    if isinstance(v, dict):
        for k in ("rendered", "ita-IT", "it", "url", "href", "@id", "value", "text"):
            if k in v:
                return _come_testo(v[k])
        for x in v.values():
            t = _come_testo(x)
            if t:
                return t
    return None


def da_record(record: dict, base_url: str) -> Annuncio | None:
    """Trasforma un record generico (dizionario) in Annuncio, cercando le chiavi note."""
    titolo = _come_testo(_valore(record, CHIAVI_TITOLO))
    if not titolo:
        return None
    url = _come_testo(_valore(record, CHIAVI_URL))
    if not url:
        ident = _come_testo(_valore(record, ("id", "codice_bando", "codice", "identifier", "UID")))
        if not ident:
            return None
        url = base_url + "#" + ident
    url = urljoin(base_url, url)
    data = _come_testo(_valore(record, CHIAVI_DATA))
    return Annuncio(
        url=url, titolo=pulisci_html(titolo, 300) or titolo,
        riassunto=pulisci_html(_come_testo(_valore(record, CHIAVI_RIASSUNTO))),
        pubblicato_il=leggi_data(data), dati=record,
    )


def _elenco_record(dati: Any) -> list[dict]:
    """Trova l'elenco di record in un JSON: la lista di dizionari piu' lunga, a qualunque livello."""
    migliore: list[dict] = []
    if isinstance(dati, list):
        if dati and all(isinstance(x, dict) for x in dati):
            migliore = dati
        for x in dati:
            cand = _elenco_record(x)
            if len(cand) > len(migliore):
                migliore = cand
    elif isinstance(dati, dict):
        for v in dati.values():
            cand = _elenco_record(v)
            if len(cand) > len(migliore):
                migliore = cand
    return migliore


def generico(dati: Any, base_url: str) -> list[Annuncio]:
    annunci = []
    for record in _elenco_record(dati):
        a = da_record(record, base_url)
        if a:
            annunci.append(a)
    return annunci


# ---- Famiglie con struttura nota -------------------------------------------------------------------

def plone(dati: dict, base_url: str) -> list[Annuncio]:
    """Plone REST API: {"items": [{"@id", "title", "description", "effective", ...}]}. Salta le cartelle."""
    annunci = []
    for it in dati.get("items", []):
        if it.get("@type") in ("Folder", "PNAnnouncementsContainer"):
            continue
        a = da_record(it, base_url)
        if a:
            annunci.append(a)
    return annunci


def wordpress(dati: list, base_url: str) -> list[Annuncio]:
    """WordPress REST: lista di {"link", "title": {"rendered"}, "date", "excerpt": {"rendered"}}."""
    return generico(dati, base_url)


def opencity(dati: dict, base_url: str) -> list[Annuncio]:
    """OpenCity (Trento): {"searchHits": [{"metadata": {"id", "name": {"ita-IT"}, "published", ...}, "data": {...}}]}."""
    annunci = []
    for hit in dati.get("searchHits", []):
        meta = hit.get("metadata", {})
        record = {"title": meta.get("name"), "published": meta.get("published"), "modified": meta.get("modified"),
                  "id": meta.get("id"), "link": meta.get("link") or meta.get("url")}
        contenuto = hit.get("data", {})
        if isinstance(contenuto, dict):
            ita = contenuto.get("ita-IT", contenuto)
            if isinstance(ita, dict):
                record["description"] = ita.get("abstract") or ita.get("description")
        a = da_record(record, base_url)
        if a:
            a.dati = hit
            annunci.append(a)
    return annunci


def ckan(dati: dict, base_url: str) -> list[Annuncio]:
    """CKAN package_search: {"result": {"results": [{"name", "title", "notes", "metadata_modified"}]}}."""
    annunci = []
    for r in dati.get("result", {}).get("results", []):
        annunci.append(Annuncio(
            url=f"https://www.dati.gov.it/view-dataset/dataset?id={r.get('id')}", titolo=r.get("title") or r.get("name"),
            riassunto=pulisci_html(r.get("notes")), pubblicato_il=leggi_data(r.get("metadata_modified")), dati=r,
        ))
    return annunci


def sedia(fonte: Fonte, client: httpx.Client) -> Lettura:
    """Portale UE Funding & Tenders: POST multipart con la parte 'query' in JSON (GET non e' ammesso)."""
    url = fonte.feed_url or fonte.url
    query = {"bool": {"must": [{"terms": {"type": ["1", "2", "8"]}}, {"terms": {"status": ["31094501", "31094502"]}}]}}
    risposta = client.post(
        url,
        files={"query": ("blob", json.dumps(query).encode(), "application/json"),
               "languages": ("blob", b'["it","en"]', "application/json")},
    )
    risposta.raise_for_status()
    dati = risposta.json()
    annunci = []
    for r in dati.get("results", []):
        meta = r.get("metadata", {})
        titolo = _come_testo(meta.get("title")) or _come_testo(r.get("title"))
        ident = _come_testo(meta.get("identifier")) or r.get("reference")
        if not (titolo and ident):
            continue
        annunci.append(Annuncio(
            url=f"https://ec.europa.eu/info/funding-tenders/opportunities/portal/screen/opportunities/topic-details/{ident.lower()}",
            titolo=titolo, riassunto=_come_testo(meta.get("callTitle")),
            pubblicato_il=leggi_data(_come_testo(meta.get("startDate"))),
            dati={"identifier": ident, "status": meta.get("status"), "deadlineDate": meta.get("deadlineDate"),
                  "callIdentifier": meta.get("callIdentifier")},
        ))
    return Lettura(annunci=annunci, codice_http=risposta.status_code, byte=len(risposta.content),
                   impronta_pagina=hashlib.sha256(risposta.content).hexdigest()[:32])


def da_csv(testo: str, base_url: str) -> list[Annuncio]:
    dialetto = csv.Sniffer().sniff(testo[:2000], delimiters=";,\t") if testo.strip() else csv.excel
    righe = list(csv.DictReader(io.StringIO(testo), dialect=dialetto))
    return generico([{k.strip().lower().replace(" ", "_"): v for k, v in r.items() if k} for r in righe], base_url)


FAMIGLIE = {"plone": plone, "wordpress": wordpress, "opencity": opencity, "ckan": ckan}


def leggi(fonte: Fonte, client: httpx.Client) -> Lettura:
    if fonte.piattaforma == "sedia":
        return sedia(fonte, client)
    indirizzo = fonte.indirizzo_da_controllare
    risposta = scarica(client, indirizzo, accept="application/json, text/csv, */*")
    risposta.raise_for_status()
    tipo = risposta.headers.get("content-type", "")
    base = fonte.url or indirizzo
    if "csv" in tipo or indirizzo.endswith(".csv") or "csv" in indirizzo:
        annunci = da_csv(risposta.text, base)
    else:
        dati = risposta.json()
        funzione = FAMIGLIE.get(fonte.piattaforma or "")
        annunci = funzione(dati, base) if funzione else generico(dati, base)
    return Lettura(annunci=annunci, codice_http=risposta.status_code, byte=len(risposta.content),
                   impronta_pagina=hashlib.sha256(risposta.content).hexdigest()[:32])
