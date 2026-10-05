"""API della guida: ogni utente riceve solo le sezioni che lo riguardano."""

from fastapi import APIRouter, Depends

from app import guida
from app.utenti.api import utente_corrente

router = APIRouter(prefix="/api")


@router.get("/guida")
def sezioni(utente: dict = Depends(utente_corrente)) -> list[dict]:
    return guida.per_utente(utente)
