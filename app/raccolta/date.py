"""Lettura tollerante delle date che si trovano nei feed, nelle API e nelle pagine italiane."""

from __future__ import annotations

import re
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime

_MESI = {
    "gennaio": 1, "febbraio": 2, "marzo": 3, "aprile": 4, "maggio": 5, "giugno": 6, "luglio": 7,
    "agosto": 8, "settembre": 9, "ottobre": 10, "novembre": 11, "dicembre": 12,
    "gen": 1, "feb": 2, "mar": 3, "apr": 4, "mag": 5, "giu": 6, "lug": 7, "ago": 8, "set": 9, "ott": 10, "nov": 11, "dic": 12,
}
_NUMERICA = re.compile(r"\b(\d{1,2})[/.-](\d{1,2})[/.-](\d{2,4})\b")
_ESTESA = re.compile(r"\b(\d{1,2})\s+([a-zà]+)\s+(\d{4})\b", re.IGNORECASE)


def leggi_data(testo: str | None) -> datetime | None:
    """Prova nell'ordine: ISO 8601, formato email (RFC 822), gg/mm/aaaa, '12 settembre 2026'."""
    if not testo:
        return None
    testo = testo.strip()
    try:
        d = datetime.fromisoformat(testo.replace("Z", "+00:00"))
        return d if d.tzinfo else d.replace(tzinfo=timezone.utc)
    except ValueError:
        pass
    try:
        return parsedate_to_datetime(testo)
    except (TypeError, ValueError, IndexError):
        pass
    m = _NUMERICA.search(testo)
    if m:
        g, me, a = int(m.group(1)), int(m.group(2)), int(m.group(3))
        if a < 100:
            a += 2000
        try:
            return datetime(a, me, g, tzinfo=timezone.utc)
        except ValueError:
            return None
    m = _ESTESA.search(testo)
    if m and m.group(2).lower() in _MESI:
        try:
            return datetime(int(m.group(3)), _MESI[m.group(2).lower()], int(m.group(1)), tzinfo=timezone.utc)
        except ValueError:
            return None
    return None
