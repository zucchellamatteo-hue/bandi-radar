"""Piccole utilita' sui testi."""

from __future__ import annotations

import re

from bs4 import BeautifulSoup

_SPAZI = re.compile(r"\s+")


def pulisci_html(testo: str | None, massimo: int = 600) -> str | None:
    """Toglie i tag HTML e gli spazi doppi; accorcia a `massimo` caratteri."""
    if not testo:
        return None
    pulito = _SPAZI.sub(" ", BeautifulSoup(testo, "html.parser").get_text(" ")).strip()
    if not pulito:
        return None
    return pulito[:massimo]
