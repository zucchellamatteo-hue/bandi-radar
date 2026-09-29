"""Codici ATECO: forma normale ("62.01.00"), sezione (lettera) e confronto "il codice del cliente sta dentro
il codice del bando". Le sezioni cambiano tra ATECO 2007 e ATECO 2025 (NACE Rev. 2.1): per esempio 62 e' J nel 2007
e K nel 2025; il commercio (G) nel 2025 comincia da 46."""

from __future__ import annotations

import re

# Divisione (due cifre) -> sezione, per versione. Intervalli [da, a].
_SEZIONI = {
    "2007": [("A", 1, 3), ("B", 5, 9), ("C", 10, 33), ("D", 35, 35), ("E", 36, 39), ("F", 41, 43), ("G", 45, 47),
             ("H", 49, 53), ("I", 55, 56), ("J", 58, 63), ("K", 64, 66), ("L", 68, 68), ("M", 69, 75), ("N", 77, 82),
             ("O", 84, 84), ("P", 85, 85), ("Q", 86, 88), ("R", 90, 93), ("S", 94, 96), ("T", 97, 98), ("U", 99, 99)],
    "2025": [("A", 1, 3), ("B", 5, 9), ("C", 10, 33), ("D", 35, 35), ("E", 36, 39), ("F", 41, 43), ("G", 46, 47),
             ("H", 49, 53), ("I", 55, 56), ("J", 58, 60), ("K", 61, 63), ("L", 64, 66), ("M", 68, 68), ("N", 69, 75),
             ("O", 77, 82), ("P", 84, 84), ("Q", 85, 85), ("R", 86, 88), ("S", 90, 93), ("T", 94, 96), ("U", 97, 98),
             ("V", 99, 99)],
}


def normalizza(codice: str | None) -> str | None:
    """"6201" -> "62.01"; "62.1" resta; "1" -> "01"; "c" -> "C". None se non e' un codice."""
    c = (codice or "").strip().upper().rstrip(".")
    if re.fullmatch(r"[A-V]", c):
        return c
    if re.fullmatch(r"\d{1,2}(\.\d{1,2}){0,2}", c):
        parti = c.split(".")
        parti[0] = parti[0].zfill(2)
        return ".".join(parti)
    if re.fullmatch(r"\d{3,6}", c):   # senza punti: 2 cifre, poi gruppi di 2
        c = c.zfill(len(c) + len(c) % 2)
        return ".".join(c[i:i + 2] for i in range(0, len(c), 2))
    return None


def sezione(codice: str, versione: str = "2025") -> str | None:
    try:
        divisione = int(codice[:2])
    except ValueError:
        return None
    for lettera, da, a in _SEZIONI.get(versione, _SEZIONI["2025"]):
        if da <= divisione <= a:
            return lettera
    return None


def contiene(codice_bando: str, codice_cliente: str, versione_bando: str = "2025") -> str:
    """Il codice del cliente sta dentro il codice del bando?
    'si'; 'forse' (il cliente e' meno preciso del bando: "62" contro "62.01"); 'no'."""
    b, c = normalizza(codice_bando), normalizza(codice_cliente)
    if not b or not c:
        return "no"
    if len(b) == 1:                    # sezione
        return "si" if sezione(c, versione_bando) == b else "no"
    if c == b or c.startswith(b):      # "47.11.00" sta in "47.1" e in "47"
        return "si"
    if b.startswith(c):
        return "forse"
    return "no"
