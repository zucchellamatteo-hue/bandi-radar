"""Guida della piattaforma (05/10/2026): sezioni in app/guida/guida.yaml, ognuna con chi la vede.

Un'unica guida, filtrata per chi la legge: l'admin vede tutto; l'impresa le sezioni "tutti" e "impresa"; il revisore
le sezioni "tutti" e quelle dei permessi che ha (catalogo, giudizi, lavoro, modifiche, imprese).
"""

from __future__ import annotations

from pathlib import Path

import yaml

FILE = Path(__file__).resolve().parent / "guida.yaml"


def tutte(percorso: Path | None = None) -> list[dict]:
    p = percorso or FILE
    if not p.is_file():
        return []
    dati = yaml.safe_load(p.read_text(encoding="utf-8")) or {}
    return [s for s in dati.get("sezioni") or [] if isinstance(s, dict) and s.get("titolo") and s.get("testo")]


def per_utente(utente: dict, percorso: Path | None = None) -> list[dict]:
    if utente["ruolo"] == "admin":
        visibili = None
    elif utente["ruolo"] == "impresa":
        visibili = {"tutti", "impresa"}
    else:
        visibili = {"tutti", *(utente.get("permessi") or [])}
    return [{"id": s.get("id"), "titolo": s["titolo"], "testo": s["testo"], "per": s.get("per") or ["tutti"]}
            for s in tutte(percorso) if visibili is None or visibili & set(s.get("per") or ["tutti"])]
