"""Allegati: per ogni bando apre la pagina ufficiale, scarica i documenti ufficiali e le FAQ.

Dal 25/09 (Parte 2) si lavora per bando: per ogni bando con la pagina ufficiale trovata
(app/schede/pagina_ufficiale.py) e allegati non ancora cercati:
  1. apre la pagina ufficiale (robots.txt, User-Agent dichiarato, pausa tra le richieste);
  2. trova i link a PDF, DOC, DOCX, XLS, XLSX, ODT, ZIP, P7M e le pagine di FAQ (link con testo "FAQ",
     "domande frequenti");
  3. li scarica in ALLEGATI_CARTELLA/b<id bando>/, con limiti di dimensione per file e per bando;
  4. calcola l'impronta (sha256), estrae il testo (PDF, DOCX, pagine FAQ) e salva una riga in `allegati`;
     conserva anche una copia della pagina stessa (tipo 'pagina'), il cui testo servira' alla scheda;
  5. classifica ogni documento (bando, FAQ, decreto, graduatoria, modulistica, altro): ordina_per_scheda e
     documenti_per_scheda mettono il bando per primo e lasciano fuori la modulistica.
I file non scaricati (troppo grandi, vietati da robots.txt, errori) hanno comunque una riga, con il motivo.

Uso:
  python -m app.schede.allegati               # i bandi da cercare (al massimo 50 per giro)
  python -m app.schede.allegati --limite 10   # solo i primi 10
  python -m app.schede.allegati --bando 45    # un bando preciso, anche se gia' cercato
  python -m app.schede.allegati --annuncio 123   # la pagina di un annuncio preciso, anche se non e' smistato
"""

from __future__ import annotations

import argparse
import hashlib
import io
import logging
import os
import re
import sys
import time
import zipfile
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Iterable
from urllib.parse import parse_qsl, unquote, unquote_plus, urldefrag, urljoin, urlsplit

import httpx
from bs4 import BeautifulSoup

from app.raccolta.lettori.html import _e_cornice, _pulisci
from app.raccolta.robots import permesso
from app.raccolta.scarica import NonPermesso, nuovo_client, regole_robots, scarica

CARTELLA = Path(os.environ.get("ALLEGATI_CARTELLA", "/srv/allegati"))
MASSIMO_FILE = 25 * 1024 * 1024        # byte per singolo file
MASSIMO_ANNUNCIO = 100 * 1024 * 1024   # byte in tutto per annuncio
MASSIMO_FILE_ANNUNCIO = 30             # file per annuncio
PAUSA_SECONDI = 2.0                    # tra due richieste allo stesso sito (di piu' se robots.txt chiede Crawl-delay)
MASSIMO_TESTO = 200_000                # caratteri di testo estratto conservati per file
LIMITE_PREDEFINITO = 50                # annunci per giro

ESTENSIONI = ("pdf", "doc", "docx", "xls", "xlsx", "odt", "zip", "p7m")
# Il tipo dal Content-Type, per i link "FAQ" che portano a un documento invece che a una pagina.
# Per gli altri vale l'estensione del link: molti server mandano i DOCX come application/zip.
TIPI_MIME = {
    "application/pdf": "pdf", "application/msword": "doc",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document": "docx",
    "application/vnd.ms-excel": "xls",
    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet": "xlsx",
    "application/vnd.oasis.opendocument.text": "odt", "application/zip": "zip",
    "application/x-zip-compressed": "zip", "application/pkcs7-mime": "p7m",
}
# L'estensione puo' stare in mezzo al percorso (Liferay: /documents/1/2/Bando.pdf/abc-123?t=...).
_ESTENSIONE = re.compile(r"\.(" + "|".join(ESTENSIONI) + r")(?=/|$)")
# Link di scaricamento senza estensione (Plone: .../allegati/bando-2026/download/file, .../@@download/file,
# .../at_download/file): il tipo vero si legge dal Content-Type quando si scarica.
_SCARICA = re.compile(r"/(?:@@download|at_download|download)(?:/[^/]+)?/?$")
_FAQ = re.compile(r"(?<!\w)(faq|domande frequenti|domande e risposte)(?!\w)", re.IGNORECASE)
_SPAZI = re.compile(r"\s+")
# Testi dei link che non dicono nulla: meglio il nome del file.
_TESTI_VUOTI = {"", "scarica", "download", "qui", "clicca qui", "pdf", "allegato", "apri", "vai", "leggi", "documento", "file"}

logging.getLogger("pypdf").setLevel(logging.ERROR)   # i PDF della PA sono spesso imperfetti: niente avvisi a pioggia


class TroppoGrande(Exception):
    """Il file supera il limite di dimensione: lo scaricamento si interrompe."""


@dataclass
class Candidato:
    url: str
    nome: str
    tipo: str          # un'estensione di ESTENSIONI, oppure 'faq'


@dataclass
class Risultato:
    """Una riga della tabella allegati."""

    url: str
    nome: str
    tipo: str
    dimensione: int | None = None
    impronta: str | None = None
    percorso_locale: str | None = None   # relativo alla cartella degli allegati
    testo_estratto: str | None = None
    errore: str | None = None


# --- trovare i link -----------------------------------------------------------------------------

def _nome_nella_query(url: str) -> str | None:
    """Alcuni siti mettono il nome del file nei parametri (Regione Lombardia: /download/8a5a...?fileName=Bando.pdf)."""
    for _, valore in parse_qsl(urlsplit(url).query):
        if _ESTENSIONE.search(valore.lower()):
            return valore
    return None


def tipo_da_url(url: str) -> str | None:
    """"bando.pdf" -> pdf; "bando.pdf.p7m" -> p7m (vince l'ultima estensione); nessuna -> None."""
    trovate = _ESTENSIONE.findall(unquote(urlsplit(url).path).lower())
    if not trovate:
        trovate = _ESTENSIONE.findall((_nome_nella_query(url) or "").lower())
    return trovate[-1] if trovate else None


def _nome_da_url(url: str) -> str:
    if not _ESTENSIONE.search(unquote(urlsplit(url).path).lower()) and _nome_nella_query(url):
        return _nome_nella_query(url)
    percorso = unquote_plus(urlsplit(url).path).rstrip("/")   # molti siti scrivono gli spazi come +
    parti = [p for p in percorso.split("/") if p]
    # Liferay: il nome del file e' la parte con l'estensione, non l'ultima.
    for p in reversed(parti):
        if _ESTENSIONE.search(p.lower()):
            return p
    return parti[-1] if parti else urlsplit(url).netloc


_CORNICE = re.compile(r"footer|navbar|menu|cookie|breadcrumb", re.IGNORECASE)


def _togli_cornice(zuppa: BeautifulSoup) -> None:
    """Toglie menu, testata e pie' di pagina del sito, anche quando sono riconoscibili solo dal nome
    (id o classe con footer, menu, navbar...): li' stanno documenti uguali per ogni pagina (fatturazione
    elettronica, privacy, FAQ generali del sito) che non sono allegati del bando."""
    _pulisci(zuppa)
    for tag in list(zuppa.find_all(True)):
        if tag.decomposed or tag.name in ("html", "body", "main", "article"):
            continue
        nome = " ".join([tag.get("id") or "", *(tag.get("class") or [])])
        if nome.strip() and _CORNICE.search(nome) and _e_cornice(tag):
            tag.decompose()


def trova_allegati(html: str, base_url: str) -> list[Candidato]:
    """I link a documenti e pagine FAQ di una pagina, senza doppioni, nell'ordine in cui compaiono."""
    zuppa = BeautifulSoup(html, "html.parser")
    _togli_cornice(zuppa)
    pagina = urldefrag(base_url).url
    visti: set[str] = set()
    candidati: list[Candidato] = []
    for a in zuppa.find_all("a", href=True):
        href = a["href"].strip()
        if not href or href.startswith(("#", "mailto:", "javascript:", "tel:")):
            continue
        url = urldefrag(urljoin(base_url, href)).url
        if not url.startswith(("http://", "https://")) or url == pagina or url in visti:
            continue
        testo = _SPAZI.sub(" ", a.get_text(" ")).strip() or (a.get("title") or "").strip()
        tipo = tipo_da_url(url)
        if tipo is None and (_FAQ.search(testo) or _FAQ.search(unquote(urlsplit(url).path))):
            tipo = "faq"
        if tipo is None and _SCARICA.search(urlsplit(url).path):
            tipo = "file"
        if tipo is None:
            continue
        visti.add(url)
        nome = testo if testo.lower() not in _TESTI_VUOTI and len(testo) <= 200 else _nome_da_url(url)
        candidati.append(Candidato(url, nome, tipo))
    return candidati


# --- scaricare con i limiti ---------------------------------------------------------------------

class Pausa:
    """Aspetta tra due richieste allo stesso sito: PAUSA_SECONDI, o il Crawl-delay di robots.txt se e' maggiore."""

    def __init__(self, client: httpx.Client, minima: float = PAUSA_SECONDI, dormi: Callable[[float], None] = time.sleep):
        self.client, self.minima, self.dormi = client, minima, dormi
        self._ultima: dict[str, float] = {}

    def attendi(self, url: str) -> None:
        sito = urlsplit(url).netloc
        attesa = max(self.minima, regole_robots(self.client, url).crawl_delay or 0)
        if sito in self._ultima:
            resta = attesa - (time.monotonic() - self._ultima[sito])
            if resta > 0:
                self.dormi(resta)
        self._ultima[sito] = time.monotonic()


def _scrivi(blocchi: Iterable[bytes], destinazione: Path, massimo: int) -> tuple[int, str]:
    """Scrive i blocchi in un file temporaneo, fermandosi oltre `massimo` byte. Ritorna (byte, sha256)."""
    destinazione.parent.mkdir(parents=True, exist_ok=True)
    impronta, n = hashlib.sha256(), 0
    try:
        with open(destinazione, "wb") as f:
            for blocco in blocchi:
                n += len(blocco)
                if n > massimo:
                    raise TroppoGrande(f"oltre {massimo // (1024 * 1024)} MB: scaricamento interrotto")
                impronta.update(blocco)
                f.write(blocco)
    except BaseException:
        destinazione.unlink(missing_ok=True)
        raise
    return n, impronta.hexdigest()


def scarica_file(client: httpx.Client, url: str, destinazione: Path, massimo: int,
                 ignora_robots: bool = False) -> tuple[int, str, str]:
    """Scarica in streaming un file in `destinazione`. Ritorna (byte, sha256, content-type).

    Se il server dichiara una dimensione oltre il limite non si scarica nulla; se non la dichiara,
    ci si ferma appena si supera il limite. Nessun file parziale resta su disco.
    """
    if not ignora_robots and not permesso(regole_robots(client, url), url):
        raise NonPermesso(f"robots.txt vieta {url}")
    with client.stream("GET", url) as risposta:
        risposta.raise_for_status()
        dichiarata = risposta.headers.get("content-length", "")
        if dichiarata.isdigit() and int(dichiarata) > massimo:
            raise TroppoGrande(f"{int(dichiarata) // (1024 * 1024)} MB, oltre il limite di {massimo // (1024 * 1024)} MB")
        n, impronta = _scrivi(risposta.iter_bytes(64 * 1024), destinazione, massimo)
        return n, impronta, risposta.headers.get("content-type", "").split(";")[0].strip().lower()


def _nome_file_sicuro(nome: str, tipo: str) -> str:
    """Solo lettere, cifre, punto, trattino e trattino basso; estensione coerente col tipo."""
    base = re.sub(r"[^A-Za-z0-9._-]+", "_", nome).strip("._") or "allegato"
    estensione = "html" if tipo == "faq" else tipo
    if not base.lower().endswith("." + estensione):
        base = f"{base}.{estensione}"
    return base[-100:]


# --- estrarre il testo --------------------------------------------------------------------------

def testo_pdf(dati: bytes) -> str | None:
    from pypdf import PdfReader

    try:
        lettore = PdfReader(io.BytesIO(dati))
        pagine = [(p.extract_text() or "") for p in lettore.pages]
    except Exception:  # noqa: BLE001 - PDF rotti, cifrati o scansioni: nessun testo, non un errore
        return None
    testo = "\n".join(pagine).strip()
    return testo or None


def testo_html(html: str) -> str | None:
    """Il testo leggibile di una pagina (per le FAQ), senza menu, script e pie' di pagina."""
    zuppa = BeautifulSoup(html, "html.parser")
    for tag in zuppa(["script", "style", "noscript", "nav", "header", "footer", "form"]):
        tag.decompose()
    righe = (_SPAZI.sub(" ", r).strip() for r in zuppa.get_text("\n").splitlines())
    testo = "\n".join(r for r in righe if r)
    return testo or None


def estrai_testo(percorso: Path, tipo: str) -> str | None:
    dati = percorso.read_bytes()
    testo = None
    if tipo == "pdf":
        testo = testo_pdf(dati)
    elif tipo == "p7m":
        # Documento firmato: quasi sempre un PDF dentro la busta di firma, leggibile cosi' com'e'.
        inizio, fine = dati.find(b"%PDF-"), dati.rfind(b"%%EOF")
        if inizio >= 0 and fine > inizio:
            testo = testo_pdf(dati[inizio:fine + 5])
    elif tipo == "docx":
        try:
            with zipfile.ZipFile(io.BytesIO(dati)) as z:
                xml = z.read("word/document.xml").decode("utf-8", "replace")
            testo = _SPAZI.sub(" ", re.sub(r"<[^>]+>", " ", xml.replace("</w:p>", "\n"))).strip() or None
        except (zipfile.BadZipFile, KeyError):
            testo = None
    elif tipo in ("faq", "pagina"):
        testo = testo_html(dati.decode("utf-8", "replace"))
    return testo[:MASSIMO_TESTO] if testo else None


def _copia_pagina(risposta: httpx.Response, url: str, cartella: Path, cartella_annuncio: Path) -> Risultato:
    """Copia della pagina dell'annuncio (tipo 'pagina'): il suo testo servira' alla scheda, e resta
    leggibile anche se l'ente cambia o toglie la pagina. Si aggiorna a ogni ricerca, fuori dai limiti."""
    r = Risultato(url, "Pagina dell'annuncio (copia)", "pagina")
    temporaneo = cartella_annuncio / f".in_corso_{os.getpid()}"
    try:
        r.dimensione, r.impronta = _scrivi([risposta.content], temporaneo, MASSIMO_FILE)
    except TroppoGrande as exc:
        r.errore = f"troppo grande: {exc}"
        return r
    finale = cartella_annuncio / f"{r.impronta[:12]}_pagina.html"
    for vecchia in cartella_annuncio.glob("*_pagina.html"):   # si tiene solo l'ultima copia
        if vecchia != finale:
            vecchia.unlink()
    temporaneo.replace(finale)
    r.percorso_locale = str(finale.relative_to(cartella))
    r.testo_estratto = (testo_html(risposta.text) or "")[:MASSIMO_TESTO] or None
    return r


# --- documenti dei siti Plone/Volto -----------------------------------------------------------------

def candidati_plone(client: httpx.Client, pausa: Pausa, url_pagina: str, massimo_pagine: int = 15) -> list[Candidato]:
    """I siti Plone con interfaccia Volto (Regione Emilia-Romagna) costruiscono la pagina con JavaScript: nell'HTML
    non c'e' nessun link ai documenti. Il bando e i moduli stanno nelle sottocartelle ("Presentazione domanda",
    "Documenti"...), leggibili dall'API del sito (++api++). Si scende di tre livelli al massimo."""
    parti = urlsplit(url_pagina)
    base = f"{parti.scheme}://{parti.netloc}"
    # Due modi di esporre l'API: /++api++/percorso (Emilia-Romagna) o /api/percorso (Comune di Pordenone).
    prefisso = None
    for p in ("/++api++", "/api"):
        pausa.attendi(base + p + parti.path)
        try:
            prova = scarica(client, base + p + parti.path.rstrip("/"), accept="application/json")
            if prova.status_code == 200 and "json" in prova.headers.get("content-type", ""):
                prefisso = p
                break
        except (httpx.HTTPError, NonPermesso):
            continue
    if prefisso is None:
        return []

    def percorso_di(url: str) -> str:
        percorso = urlsplit(url).path
        return percorso[len(prefisso):] if percorso.startswith(prefisso + "/") else percorso

    da_visitare = [(parti.path.rstrip("/"), 0)]
    visitate: set[str] = set()
    trovati: list[Candidato] = []
    while da_visitare and len(visitate) < massimo_pagine:
        percorso, livello = da_visitare.pop(0)
        if percorso in visitate:
            continue
        visitate.add(percorso)
        indirizzo = f"{base}{prefisso}{percorso}"
        pausa.attendi(indirizzo)
        try:
            risposta = scarica(client, indirizzo, accept="application/json")
            risposta.raise_for_status()
            dati = risposta.json()
        except (httpx.HTTPError, NonPermesso, ValueError):
            continue
        for item in dati.get("items") or []:
            tipo, url = item.get("@type"), item.get("@id") or ""
            if not url.startswith(base):
                continue
            url = base + percorso_di(url)
            if tipo in ("File", "Image"):
                file_url = url + "/@@download/file"
                c = Candidato(file_url, (item.get("title") or _nome_da_url(url))[:200], tipo_da_url(url) or "file")
                if all(x.url != c.url for x in trovati):
                    trovati.append(c)
            elif item.get("is_folderish") is not False and livello < 3:
                da_visitare.append((percorso_di(url).rstrip("/"), livello + 1))
    return trovati


# --- una pagina: annuncio o bando ------------------------------------------------------------------

def elabora_annuncio(client: httpx.Client, annuncio_id: int, url_annuncio: str, cartella: Path, pausa: Pausa,
                     ignora_robots: bool = False, gia_scaricati: int = 0, gia_presenti: set[str] | None = None,
                     ) -> list[Risultato]:
    """Apre la pagina dell'annuncio, scarica documenti e FAQ. Non tocca il database."""
    return elabora_pagina(client, str(annuncio_id), url_annuncio, cartella, pausa, ignora_robots, gia_scaricati, gia_presenti)


def elabora_pagina(client: httpx.Client, sottocartella: str, url_pagina: str, cartella: Path, pausa: Pausa,
                   ignora_robots: bool = False, gia_scaricati: int = 0, gia_presenti: set[str] | None = None,
                   plone_api: bool = False, nome_copia: str = "Pagina dell'annuncio (copia)") -> list[Risultato]:
    """Apre una pagina (dell'annuncio o ufficiale del bando), scarica documenti e FAQ. Non tocca il database.

    `ignora_robots` (decisione di Matteo sulla fonte) vale solo per il sito della pagina,
    non per i siti esterni a cui la pagina rimanda. Solleva NonPermesso o errori HTTP se la pagina stessa
    non si puo' aprire. Con `plone_api` i documenti si cercano anche nell'API del sito (candidati_plone).
    """
    pagina = urldefrag(url_pagina).url
    sito = urlsplit(pagina).netloc
    gia_presenti = gia_presenti or set()

    def ignora(url: str) -> bool:
        return ignora_robots and urlsplit(url).netloc == sito

    risultati: list[Risultato] = []
    cartella_annuncio = cartella / sottocartella
    tipo_pagina = tipo_da_url(pagina)
    if tipo_pagina:   # la pagina e' direttamente un documento
        candidati = [Candidato(pagina, _nome_da_url(pagina), tipo_pagina)]
    else:
        pausa.attendi(pagina)
        risposta = scarica(client, pagina, accept="text/html,application/xhtml+xml", ignora_robots=ignora(pagina))
        risposta.raise_for_status()
        candidati = trova_allegati(risposta.text, str(risposta.url))
        copia = _copia_pagina(risposta, pagina, cartella, cartella_annuncio)
        copia.nome = nome_copia
        risultati.append(copia)
        if plone_api:
            candidati = candidati_plone(client, pausa, str(risposta.url)) + candidati
    candidati = [c for c in candidati if c.url not in gia_presenti]

    usati, contati = 0, gia_scaricati
    for c in candidati:
        r = Risultato(c.url, c.nome[:300], c.tipo)
        risultati.append(r)
        if contati >= MASSIMO_FILE_ANNUNCIO:
            r.errore = f"non scaricato: gia' {MASSIMO_FILE_ANNUNCIO} file per questo annuncio"
            continue
        restano = MASSIMO_ANNUNCIO - usati
        if restano <= 0:
            r.errore = f"non scaricato: gia' {MASSIMO_ANNUNCIO // (1024 * 1024)} MB per questo annuncio"
            continue
        temporaneo = cartella_annuncio / f".in_corso_{os.getpid()}"
        try:
            pausa.attendi(c.url)
            n, impronta, mime = scarica_file(client, c.url, temporaneo, min(MASSIMO_FILE, restano), ignora(c.url))
        except TroppoGrande as exc:
            r.errore = f"troppo grande: {exc}"
            continue
        except NonPermesso:
            r.errore = "robots.txt del sito vieta il file"
            continue
        except httpx.HTTPStatusError as exc:
            r.errore = f"HTTP {exc.response.status_code}"
            continue
        except httpx.HTTPError as exc:
            r.errore = f"{type(exc).__name__}: {str(exc)[:200]}"
            continue
        if c.tipo in ("faq", "file") and mime in TIPI_MIME:
            r.tipo = TIPI_MIME[mime]          # la "FAQ" o il link senza estensione e' un documento (es. un PDF)
        elif c.tipo == "file" and mime not in ("text/html", "application/xhtml+xml"):
            r.tipo = "altro"                  # formato non previsto: si conserva, ma non se ne legge il testo
        elif c.tipo != "faq" and mime in ("text/html", "application/xhtml+xml"):
            temporaneo.unlink(missing_ok=True)
            r.errore = "il link porta a una pagina web, non a un documento"
            continue
        finale = cartella_annuncio / f"{impronta[:12]}_{_nome_file_sicuro(_nome_da_url(c.url), r.tipo)}"
        temporaneo.replace(finale)
        r.dimensione, r.impronta = n, impronta
        r.percorso_locale = str(finale.relative_to(cartella))
        r.testo_estratto = estrai_testo(finale, r.tipo)
        usati += n
        contati += 1
    return risultati


# --- che documento e', e in che ordine va alla scheda ---------------------------------------------

def _regola(*parole: str) -> re.Pattern:
    return re.compile(r"(?<![a-z])(" + "|".join(parole) + r")")


# Dal nome (testo del link o nome del file) e dall'indirizzo. L'ordine conta: vince la prima che scatta.
CATEGORIE = [
    ("faq", _regola(r"faq", r"domande frequenti", r"domande e risposte", r"chiariment")),
    ("modulistica", _regola(r"modul", r"modell", r"mod[ ._-]?\d", r"domanda di", r"schema di domanda", r"dichiaraz", r"f24",
                            r"procura", r"whistleblow", r"informativa", r"privacy", r"delega", r"fac[ ._-]?simile",
                            r"format\b", r"template", r"dsan", r"autocertific", r"istanza", r"allegato [b-z]\b",
                            r"allegato_[b-z]\b", r"all[ ._-]?[b-z][ ._-]", r"relazione finale", r"rendicontazion",
                            r"scheda anagrafica", r"piano finanziario", r"business plan", r"perizia", r"guida.*compilazion",
                            r"manuale", r"istruzioni", r"guida")),
    ("graduatoria", _regola(r"graduatori", r"esit[io]", r"elenco (?:delle )?(?:domande|imprese|ammess|benefic)",
                            r"ammess[ie] a contributo", r"beneficiari")),
    ("decreto", _regola(r"decreto", r"delibera", r"determin", r"d[ ._-]?g[ ._-]?r\b", r"dgr", r"ddg", r"ddpf",
                        r"d[ ._-]?d[ ._-]", r"provvediment", r"atto")),
    ("bando", _regola(r"bando", r"avviso", r"allegato a\b", r"allegato_a\b", r"all[ ._-]?a[ ._-]", r"disciplinare",
                      r"regolamento", r"testo integrale", r"scheda (?:tecnica|prodotto|misura)", r"misura", r"criteri")),
]
ORDINE_CATEGORIE = {"bando": 0, "pagina": 1, "faq": 2, "decreto": 3, "graduatoria": 4, "altro": 5, "modulistica": 9}


def categoria_allegato(nome: str, url: str, tipo: str) -> str:
    if tipo == "pagina":
        return "pagina"
    if tipo == "faq":
        return "faq"
    testo = f"{nome} {_nome_da_url(url)}".lower().replace("_", " ")
    for categoria, regola in CATEGORIE:
        if regola.search(testo):
            return categoria
    return "altro"


def _data_nel_nome(testo: str) -> str:
    """Per mettere per primo il decreto piu' recente: la data (o almeno l'anno) scritta nel nome, se c'e'."""
    m = re.search(r"(\d{1,2})[._/-](\d{1,2})[._/-](20\d{2})", testo)
    if m:
        return f"{m.group(3)}{int(m.group(2)):02d}{int(m.group(1)):02d}"
    anni = re.findall(r"20\d{2}", testo)
    return max(anni) + "0000" if anni else "00000000"


def ordina_per_scheda(allegati: list[dict]) -> list[dict]:
    """Allegati (righe con nome, url, tipo, categoria, testo_estratto) nell'ordine in cui vanno a Sonnet:
    prima il bando, poi la pagina ufficiale, le FAQ, il decreto piu' recente, le graduatorie, il resto.
    La modulistica resta fuori (si conserva per la plancia, ma non serve a compilare la scheda)."""
    utili = []
    for a in allegati:
        if a.get("errore"):
            continue
        categoria = a.get("categoria") or categoria_allegato(a.get("nome") or "", a.get("url") or "", a.get("tipo") or "")
        if categoria == "modulistica":
            continue
        utili.append({**a, "categoria": categoria})
    return sorted(utili, key=lambda a: (ORDINE_CATEGORIE.get(a["categoria"], 5),
                                        "" if a["categoria"] != "decreto" else _invertito(_data_nel_nome(f"{a.get('nome')} {a.get('url')}"))))


def _invertito(data: str) -> str:
    return "".join(str(9 - int(c)) for c in data)


def documenti_per_scheda(allegati: list[dict], massimo: int = 150_000) -> tuple[list[dict], list[str]]:
    """I documenti per la scheda, gia' in ordine, con il testo tagliato **dal fondo**: se non c'e' spazio si
    accorciano gli ultimi documenti, mai il bando. Ritorna (documenti con 'testo', avvertenze da dire a Sonnet)."""
    documenti, avvertenze, restano = [], [], massimo
    for a in ordina_per_scheda(allegati):
        testo = a.get("testo_estratto") or ""
        if not testo and a["tipo"] not in ("pagina", "faq"):
            avvertenze.append(f"{a.get('nome')}: nessun testo leggibile (scansione o formato non letto)")
        if restano <= 0:
            avvertenze.append(f"{a.get('nome')}: escluso per lunghezza")
            continue
        if len(testo) > restano:
            avvertenze.append(f"{a.get('nome')}: tagliato dopo {restano} caratteri su {len(testo)}")
            testo = testo[:restano]
        restano -= len(testo)
        documenti.append({**a, "testo": testo})
    return documenti, avvertenze


# --- database -----------------------------------------------------------------------------------

def annunci_da_elaborare(conn, annuncio_id: int | None, limite: int) -> list[dict]:
    with conn.cursor() as cur:
        cur.execute("SELECT id, fonte_id, url, titolo FROM annunci WHERE id = %s", (annuncio_id,))
        return list(cur.fetchall())


def bandi_da_elaborare(conn, bando_id: int | None, limite: int) -> list[dict]:
    """Bandi con la pagina ufficiale trovata e allegati mai cercati (o pagina cambiata dopo l'ultima ricerca)."""
    with conn.cursor() as cur:
        if bando_id:
            cur.execute("SELECT b.id, b.url, b.titolo, b.pagina_stato FROM bandi b WHERE b.id = %s", (bando_id,))
        else:
            cur.execute(
                """SELECT b.id, b.url, b.titolo, b.pagina_stato FROM bandi b
                   WHERE b.pagina_stato = 'trovata' AND b.url IS NOT NULL AND b.allegati_cercati_il IS NULL
                   ORDER BY b.id LIMIT %s""",
                (limite,),
            )
        return list(cur.fetchall())


def fonti_del_bando(conn, bando_id: int) -> list[str]:
    with conn.cursor() as cur:
        cur.execute("SELECT DISTINCT fonte_id FROM annunci WHERE bando_id = %s", (bando_id,))
        return [r["fonte_id"] for r in cur.fetchall()]


def documenti_del_sito(conn) -> set[str]:
    """I file gia' trovati in due o piu' annunci o bandi diversi: sono documenti del sito (moduli generali,
    informative), non allegati di un bando. Non si scaricano di nuovo."""
    with conn.cursor() as cur:
        cur.execute("""SELECT url FROM allegati WHERE tipo <> 'pagina'
                       GROUP BY url HAVING count(DISTINCT coalesce('a' || annuncio_id, 'b' || bando_id)) >= 2""")
        return {r["url"] for r in cur.fetchall()}


def gia_scaricati(conn, annuncio_id: int | None = None, bando_id: int | None = None) -> set[str]:
    with conn.cursor() as cur:
        if bando_id is not None:
            cur.execute("SELECT url FROM allegati WHERE bando_id = %s AND annuncio_id IS NULL AND errore IS NULL "
                        "AND tipo <> 'pagina'", (bando_id,))
        else:
            cur.execute("SELECT url FROM allegati WHERE annuncio_id = %s AND errore IS NULL AND tipo <> 'pagina'", (annuncio_id,))
        return {r["url"] for r in cur.fetchall()}


def salva(conn, annuncio_id: int, risultati: list[Risultato]) -> None:
    with conn.cursor() as cur:
        cur.execute("SELECT bando_id FROM annunci WHERE id = %s", (annuncio_id,))
        riga = cur.fetchone()
        bando = riga["bando_id"] if riga else None
        for r in risultati:
            cur.execute(
                """
                INSERT INTO allegati (annuncio_id, bando_id, url, nome, tipo, categoria, dimensione, impronta, percorso_locale,
                                      testo_estratto, errore, scaricato_il)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, now())
                ON CONFLICT (annuncio_id, url) DO UPDATE SET
                    nome = EXCLUDED.nome, tipo = EXCLUDED.tipo, categoria = EXCLUDED.categoria, dimensione = EXCLUDED.dimensione,
                    impronta = EXCLUDED.impronta, percorso_locale = EXCLUDED.percorso_locale,
                    testo_estratto = EXCLUDED.testo_estratto, errore = EXCLUDED.errore, scaricato_il = now()
                """,
                (annuncio_id, bando, r.url, r.nome, r.tipo, categoria_allegato(r.nome, r.url, r.tipo), r.dimensione,
                 r.impronta, r.percorso_locale, r.testo_estratto, r.errore),
            )
        cur.execute("UPDATE annunci SET allegati_cercati_il = now() WHERE id = %s", (annuncio_id,))
    conn.commit()


def salva_bando(conn, bando_id: int, risultati: list[Risultato]) -> None:
    with conn.cursor() as cur:
        for r in risultati:
            cur.execute(
                """
                INSERT INTO allegati (annuncio_id, bando_id, url, nome, tipo, categoria, dimensione, impronta, percorso_locale,
                                      testo_estratto, errore, scaricato_il)
                VALUES (NULL, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, now())
                ON CONFLICT (bando_id, url) WHERE annuncio_id IS NULL DO UPDATE SET
                    nome = EXCLUDED.nome, tipo = EXCLUDED.tipo, categoria = EXCLUDED.categoria, dimensione = EXCLUDED.dimensione,
                    impronta = EXCLUDED.impronta, percorso_locale = EXCLUDED.percorso_locale,
                    testo_estratto = EXCLUDED.testo_estratto, errore = EXCLUDED.errore, scaricato_il = now()
                """,
                (bando_id, r.url, r.nome, r.tipo, categoria_allegato(r.nome, r.url, r.tipo), r.dimensione,
                 r.impronta, r.percorso_locale, r.testo_estratto, r.errore),
            )
        cur.execute("UPDATE bandi SET allegati_cercati_il = now() WHERE id = %s", (bando_id,))
    conn.commit()


def segna_cercato(conn, annuncio_id: int | None = None, bando_id: int | None = None) -> None:
    with conn.cursor() as cur:
        if bando_id is not None:
            cur.execute("UPDATE bandi SET allegati_cercati_il = now() WHERE id = %s", (bando_id,))
        else:
            cur.execute("UPDATE annunci SET allegati_cercati_il = now() WHERE id = %s", (annuncio_id,))
    conn.commit()


def esegui(annuncio_id: int | None = None, limite: int = LIMITE_PREDEFINITO, cartella: Path = CARTELLA,
           bando_id: int | None = None) -> int:
    """Senza --annuncio: i bandi con la pagina ufficiale trovata (Parte 2 del 25/09). Con --annuncio: la pagina
    di un annuncio preciso, come prima (utile per le prove)."""
    from app.db.connessione import connetti
    from app.db.migrazioni import applica_migrazioni
    from app.fonti.registro import CARTELLA_FONTI, carica_registro

    try:
        cartella.mkdir(parents=True, exist_ok=True)
    except OSError as exc:
        print(f"Non riesco a creare la cartella degli allegati {cartella}: {exc}", file=sys.stderr)
        return 2
    if not os.access(cartella, os.W_OK):
        print(f"La cartella degli allegati {cartella} non e' scrivibile.", file=sys.stderr)
        return 2
    registro = {f.id: f for f in carica_registro(CARTELLA_FONTI)}
    file_totali = byte_totali = errori_totali = 0
    with connetti() as conn, nuovo_client() as client:
        applica_migrazioni(conn)
        pausa = Pausa(client)
        if annuncio_id:
            lavori = [("annuncio", a) for a in annunci_da_elaborare(conn, annuncio_id, limite)]
        else:
            lavori = [("bando", b) for b in bandi_da_elaborare(conn, bando_id, limite)]
        print(f"Da elaborare: {len(lavori)}")
        for genere, x in lavori:
            if genere == "bando":
                if not x["url"]:
                    print(f"saltato  [bando {x['id']}] nessuna pagina ufficiale")
                    continue
                fonti = [registro[f] for f in fonti_del_bando(conn, x["id"]) if f in registro]
                sito = urlsplit(x["url"]).netloc
                ignora = any(f.ignora_robots and urlsplit(f.url or "").netloc == sito for f in fonti)
                plone = any(f.pagina_ufficiale.get("documenti") == "plone_api" for f in fonti)
                presenti = gia_scaricati(conn, bando_id=x["id"])
                chiamata = lambda: elabora_pagina(client, f"b{x['id']}", x["url"], cartella, pausa, ignora, len(presenti),
                                                  presenti | documenti_del_sito(conn), plone, "Pagina del bando (copia)")
                segna = lambda: segna_cercato(conn, bando_id=x["id"])
                etichetta = f"bando {x['id']}"
            else:
                fonte = registro.get(x["fonte_id"])
                presenti = gia_scaricati(conn, annuncio_id=x["id"])
                chiamata = lambda: elabora_annuncio(client, x["id"], x["url"], cartella, pausa,
                                                    bool(fonte and fonte.ignora_robots), len(presenti),
                                                    presenti | documenti_del_sito(conn))
                segna = lambda: segna_cercato(conn, annuncio_id=x["id"])
                etichetta = f"annuncio {x['id']}"
            try:
                risultati = chiamata()
            except NonPermesso:
                segna()
                print(f"saltato  [{etichetta}] robots.txt vieta la pagina {x['url']}")
                continue
            except httpx.HTTPStatusError as exc:
                if 400 <= exc.response.status_code < 500:   # pagina sparita: inutile riprovare al prossimo giro
                    segna()
                print(f"errore   [{etichetta}] HTTP {exc.response.status_code} su {x['url']}")
                continue
            except httpx.HTTPError as exc:                  # rete o timeout: si riprova al prossimo giro
                print(f"errore   [{etichetta}] {type(exc).__name__}: {str(exc)[:120]}")
                continue
            if genere == "bando":
                salva_bando(conn, x["id"], risultati)
            else:
                salva(conn, x["id"], risultati)
            ok = [r for r in risultati if not r.errore]
            byte = sum(r.dimensione or 0 for r in ok)
            file_totali += len(ok)
            byte_totali += byte
            errori_totali += len(risultati) - len(ok)
            print(f"ok       [{etichetta}] {x['titolo'][:70]}: {len(ok)} file ({byte / 1024 / 1024:.1f} MB), "
                  f"{len(risultati) - len(ok)} non scaricati", flush=True)
            for r in risultati:
                stato = r.errore or categoria_allegato(r.nome, r.url, r.tipo)
                print(f"           - {r.nome[:60]}: {stato}")
    print(f"Totale: {file_totali} file scaricati ({byte_totali / 1024 / 1024:.1f} MB), {errori_totali} non scaricati.")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Scarica allegati e FAQ dalla pagina ufficiale dei bandi.")
    parser.add_argument("--bando", type=int, metavar="ID", help="solo questo bando (anche se gia' cercato)")
    parser.add_argument("--annuncio", type=int, metavar="ID", help="la pagina di un annuncio preciso, come prima")
    parser.add_argument("--limite", type=int, default=LIMITE_PREDEFINITO, metavar="N",
                        help=f"al massimo N bandi per giro (default {LIMITE_PREDEFINITO})")
    args = parser.parse_args(argv)
    return esegui(args.annuncio, args.limite, bando_id=args.bando)


if __name__ == "__main__":
    sys.exit(main())
