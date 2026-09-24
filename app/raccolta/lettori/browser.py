"""Lettore con browser senza interfaccia (Chromium via Playwright), per i siti che riempiono l'elenco via JavaScript.

Apre la pagina, aspetta che la rete si calmi, prende l'HTML finale e lo passa allo stesso estrattore
di link dell'osservatore HTML. Costa piu' tempo e memoria di una richiesta semplice: si usa solo per
le fonti con modalita 'browser'.
"""

from __future__ import annotations

import glob
import hashlib
import os

import httpx

from app.fonti.registro import Fonte
from app.raccolta.lettori.html import estrai_link
from app.raccolta.modelli import Lettura
from app.raccolta.scarica import USER_AGENT, NonPermesso, permesso, regole_robots

ATTESA_MS = 45_000


def _eseguibile() -> str | None:
    """Chromium di Playwright: quello installato nell'immagine Docker, o uno indicato a mano."""
    esplicito = os.environ.get("BROWSER_ESEGUIBILE")
    if esplicito:
        return esplicito
    base = os.environ.get("PLAYWRIGHT_BROWSERS_PATH", "")
    if base:
        trovati = glob.glob(os.path.join(base, "chromium-*", "chrome-linux", "chrome"))
        if trovati:
            return trovati[0]
    return None


def scarica_con_browser(url: str) -> tuple[str, str]:
    """Ritorna (html finale, url finale)."""
    from playwright.sync_api import sync_playwright

    with sync_playwright() as p:
        browser = p.chromium.launch(executable_path=_eseguibile(), args=["--no-sandbox", "--disable-dev-shm-usage"])
        try:
            contesto = browser.new_context(
                user_agent=USER_AGENT, locale="it-IT",
                ignore_https_errors=os.environ.get("BROWSER_IGNORA_CERTIFICATI") == "1",
            )
            pagina = contesto.new_page()
            pagina.goto(url, wait_until="domcontentloaded", timeout=ATTESA_MS)
            try:
                pagina.wait_for_load_state("networkidle", timeout=ATTESA_MS)
            except Exception:  # noqa: BLE001 - se la rete non si calma, si legge cio' che c'e'
                pass
            pagina.wait_for_timeout(1500)
            return pagina.content(), pagina.url
        finally:
            browser.close()


def leggi(fonte: Fonte, client: httpx.Client) -> Lettura:
    if not fonte.ignora_robots and not permesso(regole_robots(client, fonte.url), fonte.url):
        raise NonPermesso(f"robots.txt vieta {fonte.url}")
    html, url_finale = scarica_con_browser(fonte.url)
    annunci = estrai_link(html, url_finale, fonte.richiesta.get("selettore"))
    return Lettura(annunci=annunci, codice_http=200, byte=len(html),
                   impronta_pagina=hashlib.sha256(html.encode("utf-8", "replace")).hexdigest()[:32])
