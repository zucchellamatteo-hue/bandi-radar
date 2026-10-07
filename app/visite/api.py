"""API della pagina Visite (08/10/2026): statistiche anonime delle pagine pubbliche, in lettura con il permesso "lavoro"."""

from __future__ import annotations

from fastapi import APIRouter, Depends

from app import visite
from app.db.connessione import connetti
from app.utenti.api import richiede

router = APIRouter(prefix="/api")


@router.get("/visite")
def riepilogo(giorni: int = 30, _: dict = Depends(richiede("lavoro"))) -> dict:
    with connetti() as conn:
        return visite.riepilogo(conn, giorni)
