"""API delle misure nazionali: elenco e scheda (per tutti gli utenti entrati, imprese comprese)."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException

from app import misure
from app.utenti.api import utente_corrente

router = APIRouter(prefix="/api")


@router.get("/misure")
def elenco(_: dict = Depends(utente_corrente)) -> list[dict]:
    return misure.tutte()


@router.get("/misure/profili")
def profili(_: dict = Depends(utente_corrente)) -> list[dict]:
    """I profili tipo di impresa degli esempi (prima di /misure/{id}, che altrimenti prenderebbe "profili")."""
    return misure.profili_esempio()


@router.get("/misure/{misura_id}")
def scheda(misura_id: str, _: dict = Depends(utente_corrente)) -> dict:
    m = misure.una(misura_id)
    if not m:
        raise HTTPException(status_code=404, detail="Misura non trovata.")
    return m
