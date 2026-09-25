"""Trova la pagina ufficiale di ogni bando, prima di scaricare gli allegati. Senza IA.

Nella prova del 25/09 in 5 schede su 10 il bando vero non era arrivato al modello: pagina con login (Lombardia),
scheda del catalogo nazionale o notizia che rimandano altrove. Qui, per ogni bando, si guardano i suoi annunci e
si applicano le regole della loro fonte, scritte nel registro (campo `pagina_ufficiale`, vedi fonti/README.md):

  campo       il link all'ente sta in un campo dei dati grezzi (incentivi.gov.it: link_ente);
  cerca       la ricerca del sito trova la pagina dal codice del bando (Lombardia: RLO12026055023);
  segui_link  la pagina e' una notizia: si segue il link al bando sul sito dell'ente ("Bando e modulistica");
  escludi     indirizzi che non sono mai la pagina del bando (pagine di domanda con login);
  sostituisci come passare dall'indirizzo salvato alla pagina per le persone (Pordenone: "/api/it/" -> "/it/");
  documenti   plone_api: i documenti stanno nelle sottocartelle, leggibili solo dall'API del sito (Emilia-Romagna).

Poi si apre la pagina candidata e si controlla che contenga davvero un bando (non un login, una pagina vuota o solo
menu). Il primo candidato buono diventa bandi.url; se nessuno va bene il bando resta "bando ufficiale non trovato"
e non avra' scheda finche' non si trova (a mano, o rifacendo la ricerca).

Uso:
  python -m app.schede.pagina_ufficiale                 # i bandi mai cercati (al massimo 100 per giro)
  python -m app.schede.pagina_ufficiale --bando 123     # un bando preciso, anche se gia' cercato
  python -m app.schede.pagina_ufficiale --rifai-non-trovati
  python -m app.schede.pagina_ufficiale --prova --bando 123   # non scrive nulla: dice cosa troverebbe e perche'
"""

from __future__ import annotations

import argparse
import re
import sys
from dataclasses import dataclass, field
from urllib.parse import urldefrag, urljoin, urlsplit

import httpx
from bs4 import BeautifulSoup

from app.raccolta.robots import permesso
from app.raccolta.scarica import NonPermesso, regole_robots, scarica
from app.schede.allegati import _SCARICA, Pausa, _togli_cornice, candidati_plone, testo_html, testo_plone, tipo_da_url
from app.schede.bandi import _e_pagina_di_servizio, url_chiave
from app.schede.smista import normalizza

LIMITE_PREDEFINITO = 100
TESTO_MINIMO = 400          # caratteri di testo utile sotto i quali una pagina e' "vuota"

# Parole che in una pagina di un bando ci sono quasi sempre.
_SEGNI_BANDO = re.compile(
    r"(?<!\w)(bando|avviso|contribut\w*|agevolazion\w*|finanziament\w*|domand[ae]|beneficiari|scadenz\w*|"
    r"voucher|incentiv\w*|fondo perduto|dotazione|spese ammissibili|requisiti)(?!\w)")
_SEGNI_LOGIN = re.compile(r"(?<!\w)(accedi|login|autenticazione|spid|cie|shibboleth|password|credenziali)(?!\w)")
# Testi dei link che, in una notizia, portano al bando sul sito dell'ente.
TESTI_PREDEFINITI = ["bando", "modulistica", "avviso", "scarica il bando", "vai al bando", "pagina del bando",
                     "maggiori informazioni", "leggi il bando", "sito dell'ente", "presentazione della domanda"]


@dataclass
class Candidato:
    url: str
    motivo: str          # da dove viene: "link all'ente del catalogo", "ricerca per codice", ...
    annuncio_id: int | None = None


@dataclass
class Esito:
    url: str | None
    stato: str           # trovata | non_trovata
    motivo: str
    provati: list[str] = field(default_factory=list)   # candidati scartati, con il perche'


# --- controllo della pagina ------------------------------------------------------------------------

def valuta_pagina(html: str, url: str) -> tuple[bool, str]:
    """La pagina contiene un bando? (vero/falso, perche'). Solo regole, niente IA."""
    zuppa = BeautifulSoup(html, "html.parser")
    ha_password = bool(zuppa.find("input", attrs={"type": "password"}))
    _togli_cornice(zuppa)
    testo = testo_html(str(zuppa)) or ""
    norm = normalizza(testo)
    documenti = sum(1 for a in zuppa.find_all("a", href=True)
                    if tipo_da_url(urljoin(url, a["href"])) or _SCARICA.search(urlsplit(urljoin(url, a["href"])).path))
    segni = len(_SEGNI_BANDO.findall(norm))
    if ha_password or (len(_SEGNI_LOGIN.findall(norm)) >= 2 and len(testo) < 2000 and segni < 3):
        return False, "pagina di accesso (login)"
    if len(testo) < TESTO_MINIMO and documenti == 0:
        return False, f"pagina vuota ({len(testo)} caratteri di testo)"
    if segni < 3 and documenti == 0:
        return False, "nessun segno di un bando (solo menu o testo generico)"
    return True, f"{segni} parole da bando, {documenti} documenti"


# --- candidati dalle regole della fonte ----------------------------------------------------------

def _escluso(url: str, regole: dict) -> str | None:
    for pezzo in regole.get("escludi") or []:
        if pezzo in url:
            return f"escluso dal registro ('{pezzo}')"
    chiave = url_chiave(url)
    if not chiave or _e_pagina_di_servizio(chiave):
        return "indirizzo di dati o API, non una pagina"
    return None


def link_da_seguire(html: str, base: str, testi: list[str], stesso_sito: bool = False) -> list[str]:
    """In una notizia: i link il cui testo parla del bando, nell'ordine della pagina. Di solito solo verso un
    altro sito (la notizia di Unioncamere rimanda alla Camera); con `stesso_sito` anche dentro lo stesso sito."""
    zuppa = BeautifulSoup(html, "html.parser")
    _togli_cornice(zuppa)
    sito = urlsplit(base).netloc.removeprefix("www.")
    cerca = [normalizza(t) for t in testi]
    trovati = []
    for a in zuppa.find_all("a", href=True):
        url = urldefrag(urljoin(base, a["href"].strip())).url
        parti = urlsplit(url)
        if parti.scheme not in ("http", "https") or url == urldefrag(base).url:
            continue
        if parti.netloc.removeprefix("www.") == sito and not stesso_sito:
            continue
        if parti.path.strip("/") == "" and not parti.query:
            continue                      # la home di un sito non e' la pagina di un bando
        testo = normalizza(" ".join(a.get_text(" ").split()) or a.get("title") or "")
        if any(t in testo for t in cerca) and url not in trovati:
            trovati.append(url)
    return trovati


def cerca_per_codice(client: httpx.Client, pausa: Pausa, regola: dict, codice: str) -> str | None:
    """Usa la ricerca del sito (regola `cerca` del registro) e ritorna il link del risultato che corrisponde."""
    corpo = {k: str(v).replace("{codice}", codice) for k, v in (regola.get("corpo_form") or {}).items()}
    url = regola["url"].replace("{codice}", codice)
    pausa.attendi(url)
    if (regola.get("metodo") or "GET").upper() == "POST":
        if not permesso(regole_robots(client, url), url):
            raise NonPermesso(f"robots.txt vieta {url}")
        risposta = client.post(url, data=corpo, headers={"Accept": "text/html", "X-Requested-With": "XMLHttpRequest"})
    else:
        risposta = scarica(client, url, accept="text/html")
    risposta.raise_for_status()
    modello = re.compile(regola["link"].replace("{codice}", re.escape(codice)))
    for a in BeautifulSoup(risposta.text, "html.parser").find_all("a", href=True):
        if modello.search(a["href"]):
            return urljoin(str(risposta.url), a["href"])
    return None


@dataclass
class AnnuncioDelBando:
    id: int
    fonte_id: str
    url: str
    dati: dict | None
    codice: str | None
    ruolo: str | None


def indirizzo_pagina(a: AnnuncioDelBando, regole: dict, indirizzo_fonte: str | None) -> str:
    """L'indirizzo della pagina dell'annuncio per le persone. Alcune fonti salvano un link relativo (va completato
    con l'indirizzo della fonte) o l'indirizzo dell'API al posto della pagina (regola `sostituisci` del registro:
    Comune di Pordenone, "/api/it/" -> "/it/")."""
    url = urljoin(indirizzo_fonte, a.url) if indirizzo_fonte and not a.url.startswith(("http://", "https://")) else a.url
    for da, a_ in (regole.get("sostituisci") or {}).items():
        url = url.replace(da, a_, 1)
    return url


def esegui_regole(client, pausa, annunci: list[AnnuncioDelBando], regole_fonti: dict[str, dict],
                  indirizzi_fonti: dict[str, str] | None = None) -> Esito:
    """Prova i candidati, dal piu' affidabile, finche' uno contiene un bando."""
    provati: list[str] = []
    visti: set[str] = set()
    indirizzi_fonti = indirizzi_fonti or {}

    def prova(c: Candidato) -> Esito | None:
        chiave = url_chiave(c.url)
        if not chiave or chiave in visti:
            return None
        visti.add(chiave)
        regole = regole_fonti.get(next((a.fonte_id for a in annunci if a.id == c.annuncio_id), ""), {})
        escluso = _escluso(c.url, regole)
        if escluso:
            provati.append(f"{c.url} ({c.motivo}): {escluso}")
            return None
        if tipo_da_url(c.url):
            return Esito(c.url, "trovata", f"{c.motivo}: il link porta direttamente al documento", provati)
        try:
            pausa.attendi(c.url)
            risposta = scarica(client, c.url, accept="text/html,application/xhtml+xml")
            risposta.raise_for_status()
        except NonPermesso:
            provati.append(f"{c.url} ({c.motivo}): robots.txt vieta la pagina")
            return None
        except httpx.HTTPStatusError as exc:
            provati.append(f"{c.url} ({c.motivo}): HTTP {exc.response.status_code}")
            return None
        except httpx.HTTPError as exc:
            provati.append(f"{c.url} ({c.motivo}): {type(exc).__name__}")
            return None
        tipo = risposta.headers.get("content-type", "").split(";")[0].strip().lower()
        if tipo and tipo not in ("text/html", "application/xhtml+xml", "text/plain"):
            return Esito(str(risposta.url), "trovata", f"{c.motivo}: il link porta direttamente al documento", provati)
        # Una notizia che rimanda al bando sul sito dell'ente: si segue il link prima di accettare la notizia.
        segui = regole.get("segui_link")
        if segui:
            for link in link_da_seguire(risposta.text, str(risposta.url), segui.get("testi") or TESTI_PREDEFINITI,
                                        bool(segui.get("stesso_sito"))):
                esito = prova(Candidato(link, f"link della notizia {c.url}", c.annuncio_id))
                if esito:
                    return esito
        ok, perche = valuta_pagina(risposta.text, str(risposta.url))
        if not ok and regole.get("documenti") == "plone_api":
            # Pagina Volto: testo e documenti stanno nell'API del sito, non nell'HTML.
            testo = normalizza(testo_plone(client, pausa, str(risposta.url)) or "")
            documenti = len(candidati_plone(client, pausa, str(risposta.url)))
            if len(_SEGNI_BANDO.findall(testo)) >= 3 or documenti:
                ok, perche = True, f"letta dall'API del sito: {len(_SEGNI_BANDO.findall(testo))} parole da bando, {documenti} documenti"
        if ok:
            return Esito(str(risposta.url), "trovata", f"{c.motivo} ({perche})", provati)
        provati.append(f"{c.url} ({c.motivo}): {perche}")
        return None

    # 1. regole "forti": link all'ente nei dati grezzi e ricerca per codice
    for a in annunci:
        regole = regole_fonti.get(a.fonte_id, {})
        if regole.get("campo") and isinstance((a.dati or {}).get(regole["campo"]), str):
            esito = prova(Candidato(a.dati[regole["campo"]].strip(), f"link all'ente ({regole['campo']}) dell'annuncio {a.id}", a.id))
            if esito:
                return esito
        if regole.get("cerca") and a.codice:
            try:
                trovato = cerca_per_codice(client, pausa, regole["cerca"], a.codice)
            except (httpx.HTTPError, NonPermesso) as exc:
                provati.append(f"ricerca del codice {a.codice}: {type(exc).__name__}")
                trovato = None
            if trovato:
                esito = prova(Candidato(trovato, f"ricerca del codice {a.codice}", a.id))
                if esito:
                    return esito
            else:
                provati.append(f"ricerca del codice {a.codice}: nessun risultato")
    # 2. le pagine degli annunci stessi (prima quelle di origine), seguendo i link se la fonte pubblica notizie
    for a in sorted(annunci, key=lambda x: (x.ruolo != "origine", x.id)):
        esito = prova(Candidato(indirizzo_pagina(a, regole_fonti.get(a.fonte_id, {}), indirizzi_fonti.get(a.fonte_id)),
                                f"pagina dell'annuncio {a.id}", a.id))
        if esito:
            return esito
    return Esito(None, "non_trovata", "bando ufficiale non trovato", provati)


# --- database ---------------------------------------------------------------------------------------

def bandi_da_cercare(conn, bando_id: int | None, limite: int, rifai_non_trovati: bool) -> list[dict]:
    with conn.cursor() as cur:
        if bando_id:
            cur.execute("SELECT id, titolo FROM bandi WHERE id = %s", (bando_id,))
        else:
            condizione = "pagina_stato IS NULL" + (" OR pagina_stato = 'non_trovata'" if rifai_non_trovati else "")
            cur.execute(f"SELECT id, titolo FROM bandi WHERE {condizione} ORDER BY id LIMIT %s", (limite,))
        return list(cur.fetchall())


def annunci_del_bando(conn, bando_id: int) -> list[AnnuncioDelBando]:
    from app.schede.bandi import codice_ufficiale

    with conn.cursor() as cur:
        cur.execute("SELECT id, fonte_id, url, titolo, dati, ruolo FROM annunci WHERE bando_id = %s ORDER BY id", (bando_id,))
        righe = cur.fetchall()
    return [AnnuncioDelBando(r["id"], r["fonte_id"], r["url"], r["dati"] if isinstance(r["dati"], dict) else None,
                             codice_ufficiale(r["url"], r["titolo"], r["dati"] if isinstance(r["dati"], dict) else None),
                             r["ruolo"]) for r in righe]


def salva(conn, bando_id: int, esito: Esito) -> None:
    with conn.cursor() as cur:
        cur.execute("SELECT set_config('bandi_radar.causa', %s, true)", (f"ricerca della pagina ufficiale: {esito.motivo}"[:300],))
        cur.execute(
            """UPDATE bandi SET pagina_stato = %s, pagina_motivo = %s, pagina_cercata_il = now(),
                      url = coalesce(%s, url), url_chiave = coalesce(%s, url_chiave),
                      allegati_cercati_il = CASE WHEN %s IS DISTINCT FROM url THEN NULL ELSE allegati_cercati_il END
               WHERE id = %s""",
            (esito.stato, (esito.motivo + ("" if esito.stato == "trovata" else " — " + "; ".join(esito.provati)))[:2000],
             esito.url, url_chiave(esito.url) if esito.url else None, esito.url, bando_id),
        )
    conn.commit()


def esegui(bando_id: int | None = None, limite: int = LIMITE_PREDEFINITO, rifai_non_trovati: bool = False,
           prova: bool = False) -> int:
    from collections import Counter

    from app.db.connessione import connetti
    from app.db.migrazioni import applica_migrazioni
    from app.fonti.registro import CARTELLA_FONTI, carica_registro
    from app.raccolta.scarica import nuovo_client

    registro = carica_registro(CARTELLA_FONTI)
    regole = {f.id: f.pagina_ufficiale for f in registro}
    indirizzi = {f.id: f.url for f in registro if f.url}
    conteggi: Counter = Counter()
    motivi_mancati: Counter = Counter()
    with connetti() as conn, nuovo_client() as client:
        applica_migrazioni(conn)
        pausa = Pausa(client)
        bandi = bandi_da_cercare(conn, bando_id, limite, rifai_non_trovati)
        print(f"Bandi da cercare: {len(bandi)}")
        for b in bandi:
            esito = esegui_regole(client, pausa, annunci_del_bando(conn, b["id"]), regole, indirizzi)
            conteggi[esito.stato] += 1
            if esito.stato == "trovata":
                print(f"trovata     [{b['id']}] {b['titolo'][:70]}\n            {esito.url}\n            ({esito.motivo})", flush=True)
            else:
                for p in esito.provati:
                    motivi_mancati[p.rsplit(": ", 1)[-1]] += 1
                print(f"NON TROVATA [{b['id']}] {b['titolo'][:70]}", flush=True)
                for p in esito.provati:
                    print(f"            - {p[:200]}")
            if not prova:
                salva(conn, b["id"], esito)
    print(f"\nTotale: {conteggi['trovata']} trovate, {conteggi['non_trovata']} non trovate.")
    if motivi_mancati:
        print("Perche' i candidati sono stati scartati (bandi non trovati): "
              + ", ".join(f"{m} {n}" for m, n in motivi_mancati.most_common()))
    if prova:
        print("PROVA: nessuna modifica al database.")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Trova la pagina ufficiale dei bandi (senza IA).")
    parser.add_argument("--bando", type=int, metavar="ID", help="solo questo bando, anche se gia' cercato")
    parser.add_argument("--limite", type=int, default=LIMITE_PREDEFINITO, metavar="N", help="al massimo N bandi per giro")
    parser.add_argument("--rifai-non-trovati", action="store_true", help="riprova anche i bandi non trovati la volta scorsa")
    parser.add_argument("--prova", action="store_true", help="non scrive nel database")
    args = parser.parse_args(argv)
    return esegui(args.bando, args.limite, args.rifai_non_trovati, args.prova)


if __name__ == "__main__":
    sys.exit(main())
