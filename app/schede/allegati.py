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
  python -m app.schede.allegati --rileggi-illeggibili [--prova]   # rilegge con l'OCR i PDF senza testo leggibile

I PDF senza testo leggibile (scansioni, font senza tabella dei caratteri) si leggono con l'OCR (tesseract,
installato nell'immagine della raccolta); se neanche l'OCR da' un testo sensato, il testo resta vuoto.
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
from app.db.blocchi import con_blocco

CARTELLA = Path(os.environ.get("ALLEGATI_CARTELLA", "/srv/allegati"))
MASSIMO_FILE = 25 * 1024 * 1024        # byte per singolo file
MASSIMO_ANNUNCIO = 100 * 1024 * 1024   # byte in tutto per annuncio
MASSIMO_FILE_ANNUNCIO = 30             # file per annuncio
PAUSA_SECONDI = 2.0                    # tra due richieste allo stesso sito (di piu' se robots.txt chiede Crawl-delay)
MASSIMA_PAUSA_IGNORANDO_ROBOTS = 10.0  # per le fonti con ignora_robots: il Crawl-delay conta fino a qui
MASSIMO_TESTO = 600_000                # caratteri di testo estratto conservati per file (02/10: 200.000 tagliava 263 bandi lunghi)
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
# .../download.aspx?...&Id=<GUID>: allegati di myCIVIS (Provincia di Bolzano, 30/09).
_SCARICA = re.compile(r"/(?:@@download|at_download|download)(?:/[^/]+|\.aspx)?/?$", re.IGNORECASE)
# Liferay (Azienda Zero del Veneto e molti siti della PA, 06/10): /documents/<numero>/<codice> senza estensione.
_LIFERAY = re.compile(r"/documents/\d+/[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}/?$", re.IGNORECASE)
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
_CONTENUTO = re.compile(r"contenut", re.IGNORECASE)   # non "content": "footer-content" e' davvero un pie' di pagina


def _togli_cornice(zuppa: BeautifulSoup) -> None:
    """Toglie menu, testata e pie' di pagina del sito, anche quando sono riconoscibili solo dal nome
    (id o classe con footer, menu, navbar...): li' stanno documenti uguali per ogni pagina (fatturazione
    elettronica, privacy, FAQ generali del sito) che non sono allegati del bando."""
    _pulisci(zuppa)
    for tag in list(zuppa.find_all(True)):
        if tag.decomposed or tag.name in ("html", "body", "main", "article"):
            continue
        nome = " ".join([tag.get("id") or "", *(tag.get("class") or [])])
        # Liferay (MASE, 30/09): "lfr-layout-structure-item-breadcrumb-e-contenuto-std" contiene il testo del bando.
        if nome.strip() and _CORNICE.search(nome) and not _CONTENUTO.search(nome) and _e_cornice(tag):
            tag.decompose()


# --- pagine elenco condivise da piu' bandi (06/10/2026) ---------------------------------------------------------
# La Camera di Cuneo mette tutti i bandi su un'unica pagina, ognuno nella sua sezione: senza un filtro ogni bando
# riceveva i documenti di tutti gli altri (segnalato da Matteo sul 423). Quando la pagina ufficiale e' anche quella di
# altri bandi, si tengono solo i link della sezione del bando: dal punto in cui compare la sua "firma" (codice o parole
# del titolo che gli altri non hanno) fino alla firma di un altro bando.
_CODICE = re.compile(r"\bcod(?:ice|\.)?\s*(?:bando\s*)?[:n.\s]*(\d{3,7})\b", re.IGNORECASE)
_PAROLE_VUOTE = {"bando", "bandi", "avviso", "anno", "per", "del", "della", "delle", "dei", "degli", "alla", "alle", "con",
                 "sulle", "sui", "nel", "nella", "una", "the", "and", "contributi", "contributo", "cciaa", "camera",
                 "commercio", "progetto", "pubblico", "imprese", "impresa", "codice", "cod", "2024", "2025", "2026", "2027"}


def firma_del_bando(titolo: str, codice: str | None, altri_titoli: list[str]) -> re.Pattern | None:
    """Come riconoscere il bando su una pagina che ne elenca altri: il codice, altrimenti le prime parole del titolo
    che gli altri titoli non hanno. None se il bando non si distingue (allora non si filtra)."""
    m = _CODICE.search(titolo or "")
    numero = (codice or "").strip() if (codice or "").strip().isdigit() else (m.group(1) if m else None)
    if numero:
        return re.compile(rf"(?<!\d){re.escape(numero)}(?!\d)")
    parole_altri = {w for t in altri_titoli for w in re.findall(r"\w+", t.lower())}
    proprie = [w for w in re.findall(r"\w+", (titolo or "").lower())
               if len(w) >= 3 and w not in _PAROLE_VUOTE and w not in parole_altri]
    if not proprie:
        return None
    return re.compile(r"\W+(?:\w+\W+){0,3}".join(re.escape(w) for w in proprie[:2]), re.IGNORECASE)


def _scorri(zuppa: BeautifulSoup) -> tuple[str, list[tuple[int, int]]]:
    """Il testo della pagina e, per ogni link, la posizione nel testo in cui compare."""
    testo, link, lunghezza = [], [], 0
    for nodo in zuppa.descendants:
        if getattr(nodo, "name", None) == "a" and nodo.get("href"):
            link.append((lunghezza, id(nodo)))
        elif isinstance(nodo, str) and not getattr(nodo, "name", None):
            testo.append(str(nodo))
            lunghezza += len(testo[-1])
    return "".join(testo), link


def _limiti_sezione(tutto: str, link: list[tuple[int, int]], firma: re.Pattern,
                    altre: list[re.Pattern]) -> tuple[int, int] | None:
    """Inizio e fine della sezione del bando nel testo. Con piu' punti in cui compare la firma (un avviso in cima e la
    sezione vera) vince quello con piu' link prima della firma di un altro bando. None se la firma non c'e'."""
    mie = [m.start() for m in firma.finditer(tutto)]
    if not mie:
        return None
    confini = sorted(m.start() for f in altre for m in f.finditer(tutto))
    migliore, contati = None, -1
    for trovata in mie:
        # Dall'inizio della riga del titolo fino all'inizio della riga del bando successivo.
        inizio = tutto.rfind("\n", 0, trovata) + 1
        fine = next((c for c in confini if c > trovata), len(tutto) + 1)
        a_capo = tutto.rfind("\n", trovata, fine) if fine <= len(tutto) else -1
        fine = a_capo if a_capo > trovata else fine
        n = sum(1 for pos, _ in link if inizio <= pos < fine)
        if n > contati:
            migliore, contati = (inizio, fine), n
    return migliore


def _sezione(zuppa: BeautifulSoup, firma: re.Pattern, altre: list[re.Pattern]) -> set[int] | None:
    """Gli id dei tag <a> che stanno nella sezione del bando (None se la firma non c'e')."""
    tutto, link = _scorri(zuppa)
    limiti = _limiti_sezione(tutto, link, firma, altre)
    if limiti is None:
        return None
    return {i for pos, i in link if limiti[0] <= pos < limiti[1]}


def testo_sezione(html: str, firma: re.Pattern, altre: list[re.Pattern]) -> str | None:
    """Il testo della sola sezione del bando su una pagina elenco (per la copia della pagina)."""
    zuppa = BeautifulSoup(html, "html.parser")
    _togli_cornice(zuppa)
    tutto, link = _scorri(zuppa)
    limiti = _limiti_sezione(tutto, link, firma, altre)
    if limiti is None:
        return None
    return _SPAZI.sub(" ", tutto[limiti[0]:limiti[1]]).strip() or None


def trova_allegati(html: str, base_url: str, firma: re.Pattern | None = None,
                   altre_firme: list[re.Pattern] | None = None) -> list[Candidato]:
    """I link a documenti e pagine FAQ di una pagina, senza doppioni, nell'ordine in cui compaiono. Con `firma`
    (pagina condivisa da piu' bandi) solo quelli della sezione del bando."""
    zuppa = BeautifulSoup(html, "html.parser")
    _togli_cornice(zuppa)
    nella_sezione = _sezione(zuppa, firma, altre_firme or []) if firma is not None else None
    if firma is not None and nella_sezione is None:
        return []   # pagina condivisa ma il bando non c'e': meglio nessun documento che quelli degli altri
    pagina = urldefrag(base_url).url
    visti: set[str] = set()
    candidati: list[Candidato] = []
    for a in zuppa.find_all("a", href=True):
        if nella_sezione is not None and id(a) not in nella_sezione:
            continue
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
        if tipo is None and (_SCARICA.search(urlsplit(url).path) or _LIFERAY.search(urlsplit(url).path)):
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

    def attendi(self, url: str, ignora_robots: bool = False) -> None:
        sito = urlsplit(url).netloc
        ritardo = regole_robots(self.client, url).crawl_delay or 0
        if ignora_robots:
            # Fonte letta nonostante robots.txt (decisione di Matteo): il Crawl-delay di 600 s della Liguria fermerebbe
            # tutto per 10 minuti a bando. Si tiene comunque una pausa ragionevole.
            ritardo = min(ritardo, MASSIMA_PAUSA_IGNORANDO_ROBOTS)
        attesa = max(self.minima, ritardo)
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


# Parole piu' comuni in italiano, inglese (documenti UE), tedesco (Alto Adige) e francese (Valle d'Aosta):
# in un testo vero sono almeno un quinto delle parole.
_PAROLE_COMUNI = frozenset(
    "di e il la le lo i gli del della dei delle dello al alla ai alle a in per con da che un una non si sono "
    "è o nel nella nei sul sulla come ed art the of and to in for on by with is are be "
    "der die das und zu von mit für ist den des im auf sich nicht ein eine dem "
    "les de et du pour au aux est".split())
_PAROLE = re.compile(r"[a-zà-ÿ]+")
_LETTERE = re.compile(r"[^\W\d_]")


def testo_leggibile(testo: str | None) -> bool:
    """False se il testo estratto da un PDF e' spazzatura: font senza la tabella dei caratteri (esce "TXLVLWL\\x03..."
    o "ĐŽŵƉŽƐƚŽ" al posto delle parole) o font disegnati (Type3: "/63 /63 /71"). Si riconosce perche' mancano le
    parole piu' comuni. I testi corti o fatti di sole tabelle di numeri non si giudicano: si tengono."""
    if not testo:
        return False
    parole = _PAROLE.findall(testo.lower())
    if len(parole) < 150:
        pieni = len(re.sub(r"\s", "", testo))
        return "\x03" not in testo and pieni > 0 and len(_LETTERE.findall(testo)) / pieni >= 0.3
    comuni = sum(1 for p in parole if p in _PAROLE_COMUNI)
    return comuni / len(parole) >= 0.05


MASSIMO_PAGINE_OCR = 60     # oltre, si legge solo l'inizio: il bando vero sta nelle prime pagine
SECONDI_OCR = 900           # tempo massimo per file


def testo_ocr(dati: bytes) -> str | None:
    """Legge il PDF come immagini (pdftoppm + tesseract, italiano e inglese). Solo per i PDF senza testo leggibile:
    scansioni e font senza tabella dei caratteri (29/09/2026: Basket Bond Lazio, Puglia Titolo II, DM FER-X)."""
    import shutil
    import subprocess
    import tempfile

    if not (shutil.which("pdftoppm") and shutil.which("tesseract")):
        return None
    with tempfile.TemporaryDirectory() as cartella:
        pdf = Path(cartella) / "doc.pdf"
        pdf.write_bytes(dati)
        try:
            subprocess.run(["pdftoppm", "-r", "200", "-gray", "-png", "-l", str(MASSIMO_PAGINE_OCR), str(pdf),
                            str(Path(cartella) / "p")], check=True, capture_output=True, timeout=SECONDI_OCR)
            pagine = []
            for immagine in sorted(Path(cartella).glob("p-*.png")):
                # Priorita' bassa e un solo processore per file: l'OCR non deve rallentare il resto del server.
                uscita = subprocess.run(["nice", "-n", "15", "tesseract", str(immagine), "-", "-l", "ita+eng"],
                                        check=True, capture_output=True, timeout=SECONDI_OCR,
                                        env={**os.environ, "OMP_THREAD_LIMIT": "1"})
                pagine.append(uscita.stdout.decode("utf-8", "replace"))
        except (subprocess.SubprocessError, OSError):
            return None
    testo = "\n".join(pagine).strip()
    return testo or None


def _testo_pdf_o_ocr(dati: bytes) -> str | None:
    testo = testo_pdf(dati)
    if testo_leggibile(testo):
        return testo
    letto = testo_ocr(dati)
    if testo_leggibile(letto):
        return letto
    # Meglio nessun testo che spazzatura: l'IA la prenderebbe per il bando.
    return None


def estrai_testo(percorso: Path, tipo: str) -> str | None:
    dati = percorso.read_bytes()
    testo = None
    if tipo == "pdf":
        testo = _testo_pdf_o_ocr(dati)
    elif tipo == "p7m":
        # Documento firmato: quasi sempre un PDF dentro la busta di firma, leggibile cosi' com'e'.
        inizio, fine = dati.find(b"%PDF-"), dati.rfind(b"%%EOF")
        if inizio >= 0 and fine > inizio:
            testo = _testo_pdf_o_ocr(dati[inizio:fine + 5])
    elif tipo == "docx":
        try:
            with zipfile.ZipFile(io.BytesIO(dati)) as z:
                xml = z.read("word/document.xml").decode("utf-8", "replace")
            testo = _SPAZI.sub(" ", re.sub(r"<[^>]+>", " ", xml.replace("</w:p>", "\n"))).strip() or None
        except (zipfile.BadZipFile, KeyError):
            testo = None
    elif tipo in ("faq", "pagina"):
        testo = testo_html(dati.decode("utf-8", "replace"))
    return _senza_nul(testo)[:MASSIMO_TESTO] if testo else None


_SURROGATI = re.compile(r"[\ud800-\udfff]")


def _senza_nul(testo: str) -> str:
    """Postgres non accetta il carattere nullo nei testi, e l'UTF-8 non accetta i "surrogati" isolati:
    alcuni PDF della PA contengono l'uno o gli altri (Calabria Europa, 26/09/2026)."""
    return _SURROGATI.sub("", testo.replace("\x00", ""))


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
    r.testo_estratto = _senza_nul(testo_html(risposta.text) or "")[:MASSIMO_TESTO] or None
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


def testo_plone(client: httpx.Client, pausa: Pausa, url_pagina: str) -> str | None:
    """Il testo di una pagina Plone/Volto letto dall'API: descrizione piu' i blocchi di testo. Nell'HTML delle
    pagine Volto (Emilia-Romagna) spesso c'e' solo lo scheletro della pagina, costruita poi con JavaScript."""
    parti = urlsplit(url_pagina)
    base = f"{parti.scheme}://{parti.netloc}"
    for prefisso in ("/++api++", "/api"):
        indirizzo = base + prefisso + parti.path.rstrip("/")
        try:
            pausa.attendi(indirizzo)
            risposta = scarica(client, indirizzo, accept="application/json")
            if risposta.status_code != 200 or "json" not in risposta.headers.get("content-type", ""):
                continue
            dati = risposta.json()
        except (httpx.HTTPError, NonPermesso, ValueError):
            continue
        righe = [str(dati.get("title") or ""), str(dati.get("description") or "")]

        def raccogli(x):
            if isinstance(x, dict):
                if isinstance(x.get("plaintext"), str):
                    righe.append(x["plaintext"])
                if isinstance(x.get("data"), str) and "<" in x["data"]:
                    righe.append(testo_html(x["data"]) or "")
                for v in x.values():
                    raccogli(v)
            elif isinstance(x, list):
                for v in x:
                    raccogli(v)

        raccogli({k: dati.get(k) for k in ("text", "blocks", "text_extended", "destinatari", "finanziato", "riferimenti_bando")})
        testo = "\n".join(r.strip() for r in righe if r and r.strip())
        return _senza_nul(testo)[:MASSIMO_TESTO] or None
    return None


def con_testo_dai_dati(conn, bando_id: int, campi: list[str], risultati: list[Risultato]) -> list[Risultato]:
    """Portale UE (regola `testo_dai_dati` del registro): la copia della pagina e' vuota, il testo del bando sta nei
    dati grezzi dell'annuncio. Se e' piu' lungo, prende il posto del testo della copia."""
    if not campi:
        return risultati
    with conn.cursor() as cur:
        cur.execute("SELECT dati FROM annunci WHERE bando_id = %s", (bando_id,))
        testi = [str(r["dati"].get(c) or "") for r in cur.fetchall() if isinstance(r["dati"], dict) for c in campi]
    testo = max(testi, key=len, default="")
    for r in risultati:
        if r.tipo == "pagina" and len(testo) > len(r.testo_estratto or ""):
            r.testo_estratto = _senza_nul(testo)[:MASSIMO_TESTO]
    return risultati


# --- una pagina: annuncio o bando ------------------------------------------------------------------

def elabora_annuncio(client: httpx.Client, annuncio_id: int, url_annuncio: str, cartella: Path, pausa: Pausa,
                     ignora_robots: bool = False, gia_scaricati: int = 0, gia_presenti: set[str] | None = None,
                     ) -> list[Risultato]:
    """Apre la pagina dell'annuncio, scarica documenti e FAQ. Non tocca il database."""
    return elabora_pagina(client, str(annuncio_id), url_annuncio, cartella, pausa, ignora_robots, gia_scaricati, gia_presenti)


def elabora_pagina(client: httpx.Client, sottocartella: str, url_pagina: str, cartella: Path, pausa: Pausa,
                   ignora_robots: bool = False, gia_scaricati: int = 0, gia_presenti: set[str] | None = None,
                   plone_api: bool = False, nome_copia: str = "Pagina dell'annuncio (copia)",
                   firma: re.Pattern | None = None, altre_firme: list[re.Pattern] | None = None) -> list[Risultato]:
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
        pausa.attendi(pagina, ignora_robots=ignora(pagina))
        risposta = scarica(client, pagina, accept="text/html,application/xhtml+xml", ignora_robots=ignora(pagina))
        risposta.raise_for_status()
        candidati = trova_allegati(risposta.text, str(risposta.url), firma, altre_firme)
        copia = _copia_pagina(risposta, pagina, cartella, cartella_annuncio)
        copia.nome = nome_copia
        if firma is not None:   # pagina elenco: della copia si tiene solo il testo della sezione del bando
            sezione = testo_sezione(risposta.text, firma, altre_firme or [])
            if sezione:
                copia.testo_estratto = sezione
                copia.nome = f"{nome_copia}, solo la sezione del bando"
        risultati.append(copia)
        if plone_api:
            candidati = candidati_plone(client, pausa, str(risposta.url)) + candidati
            testo_api = testo_plone(client, pausa, str(risposta.url))
            if testo_api and len(testo_api) > len(copia.testo_estratto or ""):
                copia.testo_estratto = testo_api     # la pagina Volto ha il testo solo nell'API
    candidati = [c for c in candidati if c.url not in gia_presenti]

    usati, contati = 0, gia_scaricati
    for c in candidati:
        r = Risultato(c.url, _senza_nul(c.nome)[:300], c.tipo)
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
            pausa.attendi(c.url, ignora_robots=ignora(c.url))
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
        except (httpx.InvalidURL, ValueError) as exc:   # link malformato (es. nome del sito troppo lungo): solo questo file
            temporaneo.unlink(missing_ok=True)
            r.errore = f"indirizzo non valido: {str(exc)[:150]}"
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


# Verifica del 02/10 (4109, 3603): "Avviso Asse II Allegato B)" e "Allegato I" (istruzioni e massimali) finivano
# nella modulistica per il solo nome "Allegato X", e la scheda li perdeva. Se il nome e' modulistica solo per
# "Allegato X", decide il testo: un modulo ha "il sottoscritto", "dichiara", la firma; un atto ha articoli,
# beneficiari, intensita', spese ammissibili.
_ALLEGATO_LETTERA = re.compile(r"(?<![a-z])(allegato [b-z]\b|all[ ._-]?[b-z][ ._-]|allegato [ivx]+\b)")
_NOME_DECRETO = re.compile(r"^\s*(d\.? ?d\.?|d\.? ?g\.? ?r\.?|ddg|ddpf|decreto|determin|delibera)\b[ .]*(n\.?|nr\.?|num)?\s*\d")
_SEGNI_MODULO = re.compile(r"sottoscritt|dichiara\b|dichiaro\b|chiede (?:di|la concessione|l'ammissione)|luogo e data|"
                           r"firma (?:digitale )?del (?:legale|titolare|richiedente)|timbro e firma", re.IGNORECASE)
_SEGNI_ATTO = re.compile(r"\bart(?:icolo|\.)\s*\d|beneficiar|intensit[aà]|spese ammissibili|dotazione finanziaria|"
                         r"criteri di (?:valutazione|selezione)|massimal[ei]|contributo concedibile|soggetti ammessi", re.IGNORECASE)


def sembra_atto(testo: str | None) -> bool:
    """Il testo e' un atto (bando, avviso, istruzioni con importi) e non un modulo da compilare."""
    if not testo or len(testo) < 3000 or _SEGNI_MODULO.search(testo[:4000]):
        return False
    return len({m.group(0).lower()[:5] for m in _SEGNI_ATTO.finditer(testo[:40000])}) >= 3


def categoria_allegato(nome: str, url: str, tipo: str, testo: str | None = None) -> str:
    """Categoria dal nome e dall'indirizzo; con il testo, corregge i falsi "modulistica" (vedi sopra)."""
    if tipo == "pagina":
        return "pagina"
    if tipo == "faq":
        return "faq"
    nome_l = (nome or "").lower()
    if _NOME_DECRETO.search(nome_l) and not re.search(r"allegat|modul|fac[ ._-]?simile", nome_l):
        return "decreto"     # "DD n. 331 ... Proroga" con "modulistica" nell'indirizzo restava tra i moduli (833)
    testo_nome = f"{nome} {_nome_da_url(url)}".lower().replace("_", " ")
    for categoria, regola in CATEGORIE:
        if regola.search(testo_nome):
            if categoria == "modulistica" and testo is not None and sembra_atto(testo):
                senza_lettera = _ALLEGATO_LETTERA.sub(" ", testo_nome)
                if not CATEGORIE[1][1].search(senza_lettera):
                    if CATEGORIE[4][1].search(_ALLEGATO_LETTERA.sub(" ", nome_l)):
                        return "bando"     # il nome dice bando o avviso: vince sull'indirizzo
                    return next((c for c, r in CATEGORIE[2:] if r.search(senza_lettera)), "altro")
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
                                        bool(_SUPERATA.search(a.get("nome") or "")),
                                        "" if a["categoria"] != "decreto" else _invertito(_data_nel_nome(f"{a.get('nome')} {a.get('url')}"))))


# Versioni superate di un bando (verifica del 04/10: 4180 metteva prima "Bando A - versione in vigore fino al
# 21.02.2024" e lasciava fuori quello aggiornato nel 2026; 1647 la pre-informazione al posto dell'avviso definitivo):
# restano tra i documenti, ma dopo quelle in vigore della stessa categoria.
_SUPERATA = re.compile(r"pre-?\s?informazione|\bbozza\b|in vigore fino al|versione (?:precedente|superata|originaria)",
                       re.IGNORECASE)


def _invertito(data: str) -> str:
    return "".join(str(9 - int(c)) for c in data)


RISERVA_DOCUMENTO = 30_000   # caratteri garantiti a ogni documento prima di allungare i primi

def documenti_per_scheda(allegati: list[dict], massimo: int = 150_000) -> tuple[list[dict], list[str]]:
    """I documenti per la scheda, gia' in ordine. Ogni documento ha l'inizio garantito; il resto dello spazio va ai
    documenti in ordine (prima il bando), quindi si accorcia la coda dei documenti piu' lunghi. Ritorna
    (documenti con 'testo', avvertenze da dire a chi scrive la scheda)."""
    documenti, avvertenze, ordinati, visti = [], [], [], {}
    for a in ordina_per_scheda(allegati):
        # Lo stesso testo in piu' documenti (1542: l'avviso allegato a tre determinazioni) si legge una volta sola.
        impronta = _SPAZI.sub(" ", (a.get("testo_estratto") or "")[:5000]).strip().lower()
        if len(impronta) > 2000 and impronta in visti:
            avvertenze.append(f"{a.get('nome')}: stesso testo di '{visti[impronta]}', letto una volta sola")
            continue
        visti.setdefault(impronta, a.get("nome"))
        ordinati.append(a)
    lunghezze = [len(a.get("testo_estratto") or "") for a in ordinati]
    # Prima ogni documento ha l'inizio garantito, poi il resto va in ordine (03/10: in 4163 un avviso di 296.000
    # caratteri lasciava fuori la determina e le FAQ). Con molti documenti la parte garantita si accorcia, fino a
    # meta' dello spazio in tutto (04/10: con 27 documenti 4180 tornava al taglio dal fondo e perdeva il bando in vigore).
    riserva = min(RISERVA_DOCUMENTO, massimo // (2 * max(1, len(ordinati))))
    quote, restano = [], massimo
    for n in lunghezze:
        quote.append(min(n, riserva, restano))
        restano -= quote[-1]
    for i, n in enumerate(lunghezze):
        aggiunta = max(0, min(n - quote[i], restano))
        quote[i] += aggiunta
        restano -= aggiunta
    for a, n, quota in zip(ordinati, lunghezze, quote):
        testo = a.get("testo_estratto") or ""
        if not testo and a["tipo"] not in ("pagina", "faq"):
            avvertenze.append(f"{a.get('nome')}: nessun testo leggibile (scansione o formato non letto)")
        if n and not quota:
            avvertenze.append(f"{a.get('nome')}: escluso per lunghezza")
            continue
        if n > quota:
            avvertenze.append(f"{a.get('nome')}: tagliato dopo {quota} caratteri su {n}")
            testo = testo[:quota]
        documenti.append({**a, "testo": testo})
    return documenti, avvertenze


# --- database -----------------------------------------------------------------------------------

def annunci_da_elaborare(conn, annuncio_id: int | None, limite: int) -> list[dict]:
    with conn.cursor() as cur:
        cur.execute("SELECT id, fonte_id, url, titolo FROM annunci WHERE id = %s", (annuncio_id,))
        return list(cur.fetchall())


def firme_pagina_condivisa(conn, bando: dict) -> tuple[re.Pattern | None, list[re.Pattern]]:
    """Se la pagina ufficiale del bando e' anche quella di altri bandi (pagina elenco), la firma del bando e quelle
    degli altri; altrimenti (None, [])."""
    with conn.cursor() as cur:
        cur.execute("""SELECT id, titolo, codice_ufficiale FROM bandi WHERE url = %s AND id <> %s AND unito_a IS NULL""",
                    (bando["url"], bando["id"]))
        altri = [dict(r) for r in cur.fetchall()]
        cur.execute("SELECT codice_ufficiale FROM bandi WHERE id = %s", (bando["id"],))
        r = cur.fetchone()
    if not altri:
        return None, []
    titoli = [a["titolo"] for a in altri]
    firma = firma_del_bando(bando["titolo"], r["codice_ufficiale"] if r else None, titoli)
    if firma is None:
        return None, []   # titoli quasi uguali: e' un doppione, non una pagina elenco (lo decide la deduplica)
    altre = [f for a in altri if (f := firma_del_bando(a["titolo"], a["codice_ufficiale"],
                                                       [bando["titolo"], *[t for t in titoli if t != a["titolo"]]]))]
    return firma, altre


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
                (annuncio_id, bando, r.url, r.nome, r.tipo, categoria_allegato(r.nome, r.url, r.tipo, r.testo_estratto), r.dimensione,
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
                (bando_id, r.url, r.nome, r.tipo, categoria_allegato(r.nome, r.url, r.tipo, r.testo_estratto), r.dimensione,
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


@con_blocco("allegati", 0)
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
                plone = any(f.documenti_plone for f in fonti)
                presenti = gia_scaricati(conn, bando_id=x["id"])
                campi_testo = [f.pagina_ufficiale["testo_dai_dati"] for f in fonti if f.pagina_ufficiale.get("testo_dai_dati")]
                firma, altre = firme_pagina_condivisa(conn, x)
                chiamata = lambda: con_testo_dai_dati(
                    conn, x["id"], campi_testo,
                    elabora_pagina(client, f"b{x['id']}", x["url"], cartella, pausa, ignora, len(presenti),
                                   presenti | documenti_del_sito(conn), plone, "Pagina del bando (copia)", firma, altre))
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


def rileggi_illeggibili(cartella: Path = CARTELLA, bando_id: int | None = None, prova: bool = False,
                        paralleli: int = 1) -> int:
    """Rilegge i PDF gia' scaricati il cui testo e' vuoto o spazzatura (testo_leggibile), con l'OCR se serve.
    Stampa i bandi toccati: le loro schede vanno rifatte."""
    from app.db.connessione import connetti

    from concurrent.futures import ThreadPoolExecutor

    # La modulistica non va alla scheda e i bandi chiusi non servono: si saltano. Prima i bandi con la scheda.
    condizione = ("a.tipo IN ('pdf', 'p7m') AND a.percorso_locale IS NOT NULL AND a.categoria IS DISTINCT FROM 'modulistica'"
                  " AND b.stato IS DISTINCT FROM 'chiuso'" + (" AND a.bando_id = %s" if bando_id else ""))
    with connetti() as conn:
        with conn.cursor() as cur:
            cur.execute(f"""SELECT a.id FROM allegati a JOIN bandi b ON b.id = a.bando_id WHERE {condizione}
                            ORDER BY b.completezza IS NULL, b.stato IS NULL, a.bando_id, a.id""",
                        (bando_id,) if bando_id else ())
            ids = [r["id"] for r in cur.fetchall()]
        da_rifare = []
        for inizio in range(0, len(ids), 500):
            with conn.cursor() as cur:
                cur.execute("SELECT id, bando_id, percorso_locale, tipo, testo_estratto FROM allegati WHERE id = ANY(%s)",
                            (ids[inizio:inizio + 500],))
                trovati = {r["id"]: r for r in cur.fetchall() if not testo_leggibile(r["testo_estratto"])}
            da_rifare += [dict(trovati[i], testo_estratto=None) for i in ids[inizio:inizio + 500] if i in trovati]
        print(f"PDF controllati: {len(ids)}; senza testo leggibile: {len(da_rifare)}", flush=True)

        def leggi(r: dict) -> tuple[dict, str | None, bool]:
            percorso = cartella / r["percorso_locale"]
            return (r, estrai_testo(percorso, r["tipo"]), True) if percorso.exists() else (r, None, False)

        bandi_toccati: set[int] = set()
        with ThreadPoolExecutor(max_workers=max(1, paralleli)) as esecutore:   # l'OCR gira in processi esterni
            for r, testo, esiste in esecutore.map(leggi, da_rifare):
                if not esiste:
                    print(f"manca    [allegato {r['id']}] {r['percorso_locale']}")
                    continue
                print(f"{'letto   ' if testo else 'illeggib'} [allegato {r['id']}, bando {r['bando_id']}] "
                      f"{r['percorso_locale'][:70]}: {len(testo or '')} caratteri", flush=True)
                if prova:
                    continue
                with conn.cursor() as cur:
                    cur.execute("UPDATE allegati SET testo_estratto = %s WHERE id = %s", (testo, r["id"]))
                conn.commit()
                if testo and r["bando_id"]:
                    bandi_toccati.add(r["bando_id"])
    print("Bandi con testo nuovo (schede da rifare):", " ".join(str(b) for b in sorted(bandi_toccati)) or "nessuno")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Scarica allegati e FAQ dalla pagina ufficiale dei bandi.")
    parser.add_argument("--bando", type=int, metavar="ID", help="solo questo bando (anche se gia' cercato)")
    parser.add_argument("--annuncio", type=int, metavar="ID", help="la pagina di un annuncio preciso, come prima")
    parser.add_argument("--limite", type=int, default=LIMITE_PREDEFINITO, metavar="N",
                        help=f"al massimo N bandi per giro (default {LIMITE_PREDEFINITO})")
    parser.add_argument("--rileggi-illeggibili", action="store_true",
                        help="rilegge (anche con l'OCR) i PDF gia' scaricati senza testo leggibile, poi si ferma")
    parser.add_argument("--prova", action="store_true", help="con --rileggi-illeggibili: mostra, non salva")
    parser.add_argument("--paralleli", type=int, default=1, metavar="N",
                        help="con --rileggi-illeggibili: N file letti insieme (l'OCR usa un processore per file)")
    args = parser.parse_args(argv)
    if args.rileggi_illeggibili:
        return rileggi_illeggibili(bando_id=args.bando, prova=args.prova, paralleli=args.paralleli)
    return esegui(args.annuncio, args.limite, bando_id=args.bando)


if __name__ == "__main__":
    sys.exit(main())
