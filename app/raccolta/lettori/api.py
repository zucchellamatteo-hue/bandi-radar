"""Lettore delle API JSON e CSV. Una funzione per famiglia di piattaforma (campo `piattaforma` del registro),
piu' un lettore generico che cerca da solo titolo, link e data in qualunque JSON.
"""

from __future__ import annotations

import csv
import io
import json
import re
from typing import Any
from urllib.parse import urljoin

import hashlib

import httpx

from app.fonti.registro import Fonte
from app.raccolta.date import leggi_data
from app.raccolta.modelli import Annuncio, Lettura
from app.raccolta.scarica import scarica
from app.raccolta.testo import pulisci_html

CHIAVI_TITOLO = ("titolo", "title", "titolo_bando", "nome", "denominazione", "oggetto", "name", "label", "ntt_name_italian", "sys_title")
CHIAVI_URL = ("url", "link", "@id", "href", "permalink", "url_bando", "pagina", "full_url", "sys_canonical_url", "alias")
CHIAVI_RIASSUNTO = ("description", "descrizione", "riassunto", "summary", "excerpt", "contenuto", "abstract", "sottotitolo",
                    "sommario", "intro", "news_description", "txt_descr")
CHIAVI_DATA = ("effective", "published", "pubblicato_il", "data_notizia", "date", "data", "apertura_adesione",
               "data_pubblicazione", "datapubblicazione", "publish_up", "data_apertura", "published_date",
               "news_publication_date", "firstpublishedat", "publishedat", "startdate", "last_modified",
               "modifiedon", "modified", "changed", "created")
CHIAVI_ID = ("id", "codice_bando", "codice", "identifier", "UID", "productnumber", "slug", "codename")
CHIAVI_ANNIDATE = ("attributes", "elements", "system", "metadata", "fields", "path", "categoria")

_MODELLO = re.compile(r"\{([\w.\[\]]+)\}")


def _appiattisci(record: dict) -> dict:
    """Porta in superficie le chiavi dei blocchi annidati tipici (attributes, elements, system, ...)."""
    piatto = dict(record)
    for k in CHIAVI_ANNIDATE:
        v = record.get(k)
        if isinstance(v, dict):
            for kk, vv in v.items():
                piatto.setdefault(kk, vv)
    return piatto


def _cerca(record: dict, percorso: str):
    valore = record
    for parte in percorso.split("."):
        if isinstance(valore, dict):
            valore = valore.get(parte)
        else:
            return None
    return valore


def applica_modello(modello: str, record: dict) -> str | None:
    """Costruisce un indirizzo da un modello come https://x.it/bandi/{slug} o .../{attributes.url}."""
    mancante = False

    def sostituisci(m):
        nonlocal mancante
        v = _come_testo(_cerca(record, m.group(1)))
        if v is None:
            mancante = True
            return ""
        return v

    risultato = _MODELLO.sub(sostituisci, modello)
    return None if mancante else risultato


def _valore(d: dict, chiavi: tuple[str, ...]) -> Any:
    minuscole = {k.lower(): v for k, v in d.items()}
    for k in chiavi:
        v = minuscole.get(k.lower())
        if v not in (None, "", [], {}):
            return v
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


def da_record(record: dict, base_url: str, url_modello: str | None = None) -> Annuncio | None:
    """Trasforma un record generico (dizionario) in Annuncio, cercando le chiavi note."""
    grezzo = record
    record = _appiattisci(record)
    titolo = _come_testo(_valore(record, CHIAVI_TITOLO))
    if not titolo:
        return None
    url = applica_modello(url_modello, grezzo) if url_modello else None
    if not url:
        url = _come_testo(_valore(record, CHIAVI_URL))
    if not url:
        ident = _come_testo(_valore(record, CHIAVI_ID))
        if not ident:
            return None
        url = base_url + "#" + ident
    url = urljoin(base_url, url)
    data = _come_testo(_valore(record, CHIAVI_DATA))
    return Annuncio(
        url=url, titolo=pulisci_html(titolo, 300) or titolo,
        riassunto=pulisci_html(_come_testo(_valore(record, CHIAVI_RIASSUNTO))),
        pubblicato_il=leggi_data(data), dati=grezzo,
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


def generico(dati: Any, base_url: str, url_modello: str | None = None) -> list[Annuncio]:
    annunci = []
    for record in _elenco_record(dati):
        a = da_record(record, base_url, url_modello)
        if a:
            annunci.append(a)
    return annunci


def _stringhe(dati: Any):
    if isinstance(dati, str):
        yield dati
    elif isinstance(dati, list):
        for x in dati:
            yield from _stringhe(x)
    elif isinstance(dati, dict):
        for x in dati.values():
            yield from _stringhe(x)


def html_in_json(dati: Any, base_url: str, url_modello: str | None = None) -> list[Annuncio]:
    """Risposte JSON che contengono frammenti HTML (DataTables, filtri AJAX): si estraggono i link dai frammenti."""
    from app.raccolta.lettori.html import estrai_link

    frammenti = [s for s in _stringhe(dati) if "<a " in s or "href=" in s]
    return estrai_link("<html><body><main>" + "\n".join(frammenti) + "</main></body></html>", base_url)


# ---- Famiglie con struttura nota -------------------------------------------------------------------

def plone(dati: dict, base_url: str, url_modello: str | None = None) -> list[Annuncio]:
    """Plone REST API: {"items": [{"@id", "title", "description", "effective", ...}]}. Salta le cartelle."""
    annunci = []
    for it in dati.get("items", []):
        if it.get("@type") in ("Folder", "PNAnnouncementsContainer"):
            continue
        a = da_record(it, base_url, url_modello)
        if a:
            annunci.append(a)
    return annunci


def wordpress(dati: list, base_url: str, url_modello: str | None = None) -> list[Annuncio]:
    """WordPress REST: lista di {"link", "title": {"rendered"}, "date", "excerpt": {"rendered"}}."""
    return generico(dati, base_url, url_modello)


def opencity(dati: dict, base_url: str, url_modello: str | None = None) -> list[Annuncio]:
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


def ckan(dati: dict, base_url: str, url_modello: str | None = None) -> list[Annuncio]:
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


def strapi_con_token_nel_bundle(fonte: Fonte, client: httpx.Client) -> Lettura:
    """Siti Angular + Strapi (es. Comune dell'Aquila): il token pubblico dell'API sta nel main.*.js del sito."""
    pagina = scarica(client, fonte.url, accept="text/html", ignora_robots=fonte.ignora_robots)
    pagina.raise_for_status()
    m = re.search(r'src="([^"]*main[^"]*\.js)"', pagina.text)
    if not m:
        raise ValueError("bundle main.*.js non trovato nella pagina")
    bundle = scarica(client, urljoin(str(pagina.url), m.group(1)), ignora_robots=fonte.ignora_robots)
    bundle.raise_for_status()
    token = re.search(r'apiToken\s*:\s*"([0-9a-fA-F]{32,})"', bundle.text)
    if not token:
        raise ValueError("apiToken non trovato nel bundle")
    risposta = client.get(fonte.feed_url, headers={"Authorization": f"Bearer {token.group(1)}", "Accept": "application/json"})
    risposta.raise_for_status()
    annunci = generico(risposta.json(), fonte.url, fonte.richiesta.get("url_modello"))
    return Lettura(annunci=annunci, codice_http=risposta.status_code, byte=len(risposta.content),
                   impronta_pagina=hashlib.sha256(risposta.content).hexdigest()[:32])


def da_csv(testo: str, base_url: str) -> list[Annuncio]:
    dialetto = csv.Sniffer().sniff(testo[:2000], delimiters=";,\t") if testo.strip() else csv.excel
    righe = list(csv.DictReader(io.StringIO(testo), dialect=dialetto))
    return generico([{k.strip().lower().replace(" ", "_"): v for k, v in r.items() if k} for r in righe], base_url)


FAMIGLIE = {"plone": plone, "wordpress": wordpress, "opencity": opencity, "ckan": ckan, "html_in_json": html_in_json}


def richiedi(fonte: Fonte, client: httpx.Client) -> httpx.Response:
    """Esegue la richiesta descritta nel campo `richiesta` del registro (GET semplice se manca)."""
    r = fonte.richiesta
    intestazioni = {"Accept": "application/json", **r.get("intestazioni", {})}
    indirizzo = fonte.indirizzo_da_controllare
    if r.get("metodo", "GET").upper() == "POST":
        from app.raccolta.scarica import NonPermesso, permesso, regole_robots

        if not fonte.ignora_robots and not permesso(regole_robots(client, indirizzo), indirizzo):
            raise NonPermesso(f"robots.txt vieta {indirizzo}")
        if "corpo_form" in r:
            return client.post(indirizzo, data=r["corpo_form"], headers=intestazioni)
        return client.post(indirizzo, json=r.get("corpo_json", {}), headers=intestazioni)
    return scarica(client, indirizzo, accept=intestazioni.pop("Accept"), ignora_robots=fonte.ignora_robots) \
        if len(intestazioni) == 1 else client.get(indirizzo, headers=intestazioni)


def leggi(fonte: Fonte, client: httpx.Client) -> Lettura:
    if fonte.piattaforma == "sedia":
        return sedia(fonte, client)
    if fonte.piattaforma == "angular_strapi":
        return strapi_con_token_nel_bundle(fonte, client)
    indirizzo = fonte.indirizzo_da_controllare
    risposta = richiedi(fonte, client)
    risposta.raise_for_status()
    tipo = risposta.headers.get("content-type", "")
    base = fonte.url or indirizzo
    url_modello = fonte.richiesta.get("url_modello")
    if "csv" in tipo or indirizzo.endswith(".csv") or "csv" in indirizzo:
        annunci = da_csv(risposta.text, base)
    else:
        dati = json.loads(risposta.text)   # alcuni siti dichiarano text/html ma mandano JSON
        funzione = FAMIGLIE.get(fonte.piattaforma or "")
        annunci = funzione(dati, base, url_modello) if funzione else generico(dati, base, url_modello)
    return Lettura(annunci=annunci, codice_http=risposta.status_code, byte=len(risposta.content),
                   impronta_pagina=hashlib.sha256(risposta.content).hexdigest()[:32])
