"""Allegati: per gli annunci rilevanti apre la pagina originale, scarica i documenti ufficiali e le FAQ.

Per ogni annuncio con smistamento "rilevante" e non ancora cercato (o cambiato dopo l'ultima ricerca):
  1. apre la pagina dell'annuncio (robots.txt, User-Agent dichiarato, pausa tra le richieste);
  2. trova i link a PDF, DOC, DOCX, XLS, XLSX, ODT, ZIP, P7M e le pagine di FAQ (link con testo "FAQ",
     "domande frequenti");
  3. li scarica in ALLEGATI_CARTELLA/<id annuncio>/, con limiti di dimensione per file e per annuncio;
  4. calcola l'impronta (sha256), estrae il testo (PDF, DOCX, pagine FAQ) e salva una riga in `allegati`;
     conserva anche una copia della pagina stessa (tipo 'pagina'), il cui testo servira' alla scheda.
I file non scaricati (troppo grandi, vietati da robots.txt, errori) hanno comunque una riga, con il motivo.

Uso:
  python -m app.schede.allegati               # tutti gli annunci rilevanti da cercare (al massimo 50 per giro)
  python -m app.schede.allegati --limite 10   # solo i primi 10
  python -m app.schede.allegati --annuncio 123   # un annuncio preciso, anche se non e' ancora smistato
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


# --- un annuncio --------------------------------------------------------------------------------

def elabora_annuncio(client: httpx.Client, annuncio_id: int, url_annuncio: str, cartella: Path, pausa: Pausa,
                     ignora_robots: bool = False, gia_scaricati: int = 0, gia_presenti: set[str] | None = None,
                     ) -> list[Risultato]:
    """Apre la pagina dell'annuncio, scarica documenti e FAQ. Non tocca il database.

    `ignora_robots` (decisione di Matteo sulla fonte) vale solo per il sito della pagina dell'annuncio,
    non per i siti esterni a cui la pagina rimanda. Solleva NonPermesso o errori HTTP se la pagina stessa
    non si puo' aprire.
    """
    pagina = urldefrag(url_annuncio).url
    sito = urlsplit(pagina).netloc
    gia_presenti = gia_presenti or set()

    def ignora(url: str) -> bool:
        return ignora_robots and urlsplit(url).netloc == sito

    risultati: list[Risultato] = []
    cartella_annuncio = cartella / str(annuncio_id)
    tipo_pagina = tipo_da_url(pagina)
    if tipo_pagina:   # l'annuncio punta direttamente a un documento
        candidati = [Candidato(pagina, _nome_da_url(pagina), tipo_pagina)]
    else:
        pausa.attendi(pagina)
        risposta = scarica(client, pagina, accept="text/html,application/xhtml+xml", ignora_robots=ignora(pagina))
        risposta.raise_for_status()
        candidati = trova_allegati(risposta.text, str(risposta.url))
        risultati.append(_copia_pagina(risposta, pagina, cartella, cartella_annuncio))
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
        if c.tipo == "faq" and mime in TIPI_MIME:
            r.tipo = TIPI_MIME[mime]          # la "FAQ" e' un documento (es. un PDF), non una pagina
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


# --- database -----------------------------------------------------------------------------------

def annunci_da_elaborare(conn, annuncio_id: int | None, limite: int) -> list[dict]:
    with conn.cursor() as cur:
        if annuncio_id:
            cur.execute("SELECT id, fonte_id, url, titolo FROM annunci WHERE id = %s", (annuncio_id,))
        else:
            # Rilevanti mai cercati, o cambiati dopo l'ultima ricerca (proroghe, nuovi allegati).
            cur.execute(
                """
                SELECT a.id, a.fonte_id, a.url, a.titolo FROM annunci a
                JOIN smistamenti s ON s.annuncio_id = a.id AND s.esito = 'rilevante'
                WHERE a.allegati_cercati_il IS NULL OR a.aggiornato_il > a.allegati_cercati_il
                ORDER BY a.trovato_il DESC LIMIT %s
                """,
                (limite,),
            )
        return list(cur.fetchall())


def documenti_del_sito(conn) -> set[str]:
    """I file gia' trovati in due o piu' annunci diversi: sono documenti del sito (moduli generali,
    informative), non allegati di un bando. Non si scaricano di nuovo."""
    with conn.cursor() as cur:
        cur.execute("SELECT url FROM allegati WHERE tipo <> 'pagina' GROUP BY url HAVING count(DISTINCT annuncio_id) >= 2")
        return {r["url"] for r in cur.fetchall()}


def gia_scaricati(conn, annuncio_id: int) -> set[str]:
    with conn.cursor() as cur:
        cur.execute("SELECT url FROM allegati WHERE annuncio_id = %s AND errore IS NULL AND tipo <> 'pagina'", (annuncio_id,))
        return {r["url"] for r in cur.fetchall()}


def salva(conn, annuncio_id: int, risultati: list[Risultato]) -> None:
    with conn.cursor() as cur:
        for r in risultati:
            cur.execute(
                """
                INSERT INTO allegati (annuncio_id, url, nome, tipo, dimensione, impronta, percorso_locale,
                                      testo_estratto, errore, scaricato_il)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, now())
                ON CONFLICT (annuncio_id, url) DO UPDATE SET
                    nome = EXCLUDED.nome, tipo = EXCLUDED.tipo, dimensione = EXCLUDED.dimensione,
                    impronta = EXCLUDED.impronta, percorso_locale = EXCLUDED.percorso_locale,
                    testo_estratto = EXCLUDED.testo_estratto, errore = EXCLUDED.errore, scaricato_il = now()
                """,
                (annuncio_id, r.url, r.nome, r.tipo, r.dimensione, r.impronta, r.percorso_locale,
                 r.testo_estratto, r.errore),
            )
        cur.execute("UPDATE annunci SET allegati_cercati_il = now() WHERE id = %s", (annuncio_id,))
    conn.commit()


def segna_cercato(conn, annuncio_id: int) -> None:
    with conn.cursor() as cur:
        cur.execute("UPDATE annunci SET allegati_cercati_il = now() WHERE id = %s", (annuncio_id,))
    conn.commit()


def esegui(annuncio_id: int | None = None, limite: int = LIMITE_PREDEFINITO, cartella: Path = CARTELLA) -> int:
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
    ignora_robots = {f.id: f.ignora_robots for f in carica_registro(CARTELLA_FONTI)}
    file_totali = byte_totali = errori_totali = 0
    with connetti() as conn, nuovo_client() as client:
        applica_migrazioni(conn)
        annunci = annunci_da_elaborare(conn, annuncio_id, limite)
        print(f"Annunci da elaborare: {len(annunci)}")
        pausa = Pausa(client)
        for a in annunci:
            presenti = gia_scaricati(conn, a["id"])
            try:
                risultati = elabora_annuncio(client, a["id"], a["url"], cartella, pausa,
                                             ignora_robots.get(a["fonte_id"], False), len(presenti),
                                             presenti | documenti_del_sito(conn))
            except NonPermesso:
                segna_cercato(conn, a["id"])
                print(f"saltato  [{a['id']}] robots.txt vieta la pagina {a['url']}")
                continue
            except httpx.HTTPStatusError as exc:
                if 400 <= exc.response.status_code < 500:   # pagina sparita: inutile riprovare al prossimo giro
                    segna_cercato(conn, a["id"])
                print(f"errore   [{a['id']}] HTTP {exc.response.status_code} su {a['url']}")
                continue
            except httpx.HTTPError as exc:                  # rete o timeout: si riprova al prossimo giro
                print(f"errore   [{a['id']}] {type(exc).__name__}: {str(exc)[:120]}")
                continue
            salva(conn, a["id"], risultati)
            ok = [r for r in risultati if not r.errore]
            byte = sum(r.dimensione or 0 for r in ok)
            file_totali += len(ok)
            byte_totali += byte
            errori_totali += len(risultati) - len(ok)
            print(f"ok       [{a['id']}] {a['titolo'][:70]}: {len(ok)} file ({byte / 1024 / 1024:.1f} MB), "
                  f"{len(risultati) - len(ok)} non scaricati", flush=True)
            for r in risultati:
                if r.errore:
                    print(f"           - {r.nome[:60]}: {r.errore}")
    print(f"Totale: {file_totali} file scaricati ({byte_totali / 1024 / 1024:.1f} MB), {errori_totali} non scaricati.")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Scarica allegati e FAQ degli annunci rilevanti.")
    parser.add_argument("--annuncio", type=int, metavar="ID", help="solo questo annuncio (anche se non smistato)")
    parser.add_argument("--limite", type=int, default=LIMITE_PREDEFINITO, metavar="N",
                        help=f"al massimo N annunci per giro (default {LIMITE_PREDEFINITO})")
    args = parser.parse_args(argv)
    return esegui(args.annuncio, args.limite)


if __name__ == "__main__":
    sys.exit(main())
