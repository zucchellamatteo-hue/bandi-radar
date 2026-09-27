"""Lettura della "scorta": tutti i bandi ancora aperti di una fonte, non solo le novita'.

Il controllo normale legge la prima pagina di un elenco (le ultime 10 voci di un feed, le ultime 30 di un'API):
basta per vedere cosa esce di nuovo, ma i bandi pubblicati prima e ancora aperti non entrano mai. La scorta si
legge alla prima occasione e poi a intervalli lunghi (di solito una volta al mese), seguendo il blocco `scorta`
del registro:

  scorta:
    url: https://.../elenco?pagina={pagina}   # indirizzo della lettura completa (senza: quello del controllo normale);
                                              # {anno} diventa l'anno in corso (archivi per anno e mese: Regione Molise)
    parametro: page                           # oppure: il numero di pagina va in questo parametro dell'indirizzo
    inizio: 1                                 # numero della prima pagina (0 per le API che contano da zero)
    passo: 1                                  # di quanto cresce (10 per start=0,10,20...)
    pagine: 10                                # al massimo quante pagine
    corpo_json: {...}                         # corpo della POST, se cambia ({pagina} dove va il numero)
    scadenza: scadenza                        # campo dei dati grezzi con la scadenza: si scartano i record gia' scaduti
    senza_scadenza_mesi: 12                   # i record senza scadenza si tengono solo se pubblicati negli ultimi N mesi
    modalita: html                            # se la scorta si legge in un altro modo (feed di 10 voci -> pagine dell'elenco)
    selettore: "main .card"                   # con modalita html: dove stanno i link dei bandi
    frequenza: mensile                        # ogni quanto rileggere la scorta (predefinito: mensile)
    tutte_le_pagine: true                     # non fermarsi alla prima pagina senza link nuovi (mesi senza notizie)

Si smette alla prima pagina che non porta nessun link nuovo (salvo `tutte_le_pagine`). Niente IA, come il controllo normale; tra una pagina
e l'altra una pausa, un solo sito alla volta.
"""

from __future__ import annotations

import copy
import hashlib
import time
from collections.abc import Callable
from dataclasses import replace
from datetime import date, datetime, timedelta, timezone
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

import httpx

from app.fonti.registro import Fonte
from app.raccolta.date import leggi_data
from app.raccolta.modelli import Lettura

PAUSA_TRA_PAGINE = 2.0   # secondi
SEGNAPOSTO = "{pagina}"


def _con_parametro(indirizzo: str, nome: str, valore: int) -> str:
    parti = urlsplit(indirizzo)
    query = [(k, v) for k, v in parse_qsl(parti.query, keep_blank_values=True) if k != nome] + [(nome, str(valore))]
    return urlunsplit(parti._replace(query=urlencode(query, safe="*:/[]\"(), ")))


def _sostituisci(valore, numero: int):
    """Mette il numero di pagina al posto di {pagina} nei valori di un corpo JSON (numero se il valore e' solo quello)."""
    if isinstance(valore, str):
        return numero if valore == SEGNAPOSTO else valore.replace(SEGNAPOSTO, str(numero))
    if isinstance(valore, list):
        return [_sostituisci(v, numero) for v in valore]
    if isinstance(valore, dict):
        return {k: _sostituisci(v, numero) for k, v in valore.items()}
    return valore


def fonte_della_pagina(fonte: Fonte, numero: int) -> Fonte:
    """La stessa fonte, con indirizzo e corpo della richiesta della pagina `numero` della scorta."""
    regole = fonte.scorta
    indirizzo = str(regole.get("url") or fonte.indirizzo_da_controllare)
    indirizzo = indirizzo.replace(SEGNAPOSTO, str(numero)).replace("{anno}", str(date.today().year))
    if regole.get("parametro"):
        indirizzo = _con_parametro(indirizzo, regole["parametro"], numero)
    richiesta = copy.deepcopy(fonte.richiesta)
    corpo = regole.get("corpo_json", richiesta.get("corpo_json"))
    if corpo is not None:
        richiesta["corpo_json"] = _sostituisci(corpo, numero)
    if regole.get("selettore"):
        richiesta["selettore"] = regole["selettore"]
    modalita = regole.get("modalita", fonte.modalita)
    if modalita in {"rss", "api"}:
        return replace(fonte, modalita=modalita, feed_url=indirizzo, richiesta=richiesta)
    return replace(fonte, modalita=modalita, url=indirizzo, richiesta=richiesta)


def _cerca(dati: dict, percorso: str):
    valore = dati
    for parte in percorso.split("."):
        if not isinstance(valore, dict):
            return None
        valore = valore.get(parte)
    return valore


def scaduto(dati: dict | None, campo: str, oggi: date) -> bool:
    """Vero se il campo scadenza dei dati grezzi contiene una data passata. Senza data: non scaduto."""
    valore = _cerca(dati or {}, campo)
    if isinstance(valore, list):
        valore = max((str(v) for v in valore if v), default=None)
    if valore in (None, ""):
        return False
    data = leggi_data(str(valore))
    return data is not None and data.date() < oggi


def leggi_scorta(fonte: Fonte, client: httpx.Client, leggi: Callable[[Fonte, httpx.Client], Lettura],
                 pausa: float = PAUSA_TRA_PAGINE, oggi: date | None = None) -> Lettura:
    """Legge tutte le pagine della scorta con il lettore normale della fonte e unisce gli annunci."""
    regole = fonte.scorta
    inizio, passo, pagine = regole.get("inizio", 1), regole.get("passo", 1), regole.get("pagine", 1)
    oggi = oggi or datetime.now(timezone.utc).date()
    annunci, visti, impronte = [], set(), []
    primo_codice, byte, lette, fermata = None, 0, 0, ""
    for i in range(pagine):
        if i:
            time.sleep(pausa)
        try:
            lettura = leggi(fonte_della_pagina(fonte, inizio + i * passo), client)
        except httpx.HTTPStatusError as exc:
            if not i:
                raise
            fermata = f", fermata alla pagina {i + 1} (HTTP {exc.response.status_code})"
            break
        lette += 1
        primo_codice = primo_codice or lettura.codice_http
        byte += lettura.byte
        impronte.append(lettura.impronta_pagina or "")
        nuovi = [a for a in lettura.annunci if a.url not in visti]
        for a in nuovi:
            visti.add(a.url)
        annunci.extend(nuovi)
        if not nuovi and not regole.get("tutte_le_pagine"):
            break
    scartati = 0
    if regole.get("scadenza"):
        tenuti = [a for a in annunci if not scaduto(a.dati, regole["scadenza"], oggi)]
        if regole.get("senza_scadenza_mesi"):
            # Elenchi misti (Regione Sardegna: gare e affidamenti senza scadenza da anni): senza scadenza, solo i recenti.
            limite = oggi - timedelta(days=31 * regole["senza_scadenza_mesi"])
            tenuti = [a for a in tenuti if _cerca(a.dati or {}, regole["scadenza"]) not in (None, "")
                      or (a.pubblicato_il is not None and a.pubblicato_il.date() >= limite)]
        scartati = len(annunci) - len(tenuti)
        annunci = tenuti
    messaggio = f"scorta: {lette} pagine, {len(annunci)} elementi" + (f" ({scartati} scaduti o vecchi scartati)" if scartati else "")
    return Lettura(annunci=annunci, codice_http=primo_codice, byte=byte, messaggio=messaggio + fermata,
                   impronta_pagina=hashlib.sha256("".join(impronte).encode()).hexdigest()[:32])
