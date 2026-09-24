"""Lettori: uno per modalita' (rss, api, html). La modalita' 'browser' arriva piu' avanti."""

from __future__ import annotations

from collections.abc import Callable

import httpx

from app.fonti.registro import Fonte
from app.raccolta.modelli import Lettura

Lettore = Callable[[Fonte, httpx.Client], Lettura]


def lettore_per(fonte: Fonte) -> Lettore | None:
    from app.raccolta.lettori import api, html, rss

    return {"rss": rss.leggi, "api": api.leggi, "html": html.leggi}.get(fonte.modalita)
