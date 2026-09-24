"""Lettori: uno per modalita' (rss, api, html, browser, sitemap)."""

from __future__ import annotations

from collections.abc import Callable

import httpx

from app.fonti.registro import Fonte
from app.raccolta.modelli import Lettura

Lettore = Callable[[Fonte, httpx.Client], Lettura]


def lettore_per(fonte: Fonte) -> Lettore | None:
    from app.raccolta.lettori import api, browser, html, rss, sitemap

    return {"rss": rss.leggi, "api": api.leggi, "html": html.leggi, "browser": browser.leggi, "sitemap": sitemap.leggi}.get(fonte.modalita)
