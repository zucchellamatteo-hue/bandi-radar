"""API del feedback sulle schede: voto e problemi dalla pagina del bando, pagina Feedback per l'admin."""

from __future__ import annotations

from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel

from app import feedback as fb
from app.db.connessione import connetti
from app.utenti.api import solo_admin, utente_corrente

router = APIRouter(prefix="/api")


class Problema(BaseModel):
    categoria: str
    campo: str | None = None
    testo: str | None = None


class Giudizio(BaseModel):
    voto: int | None = None
    problemi: list[Problema] = []
    commento: str | None = None


class Gestione(BaseModel):
    stato: Literal["nuovo", "preso_in_carico", "corretto", "respinto"]
    risposta: str | None = None


def _puo_giudicare(utente: dict, bando_id: int | None = None) -> None:
    """Admin e revisori giudicano tutte le schede; l'impresa solo quelle dei bandi adatti alle sue imprese."""
    if utente["ruolo"] in ("admin", "revisore"):
        return
    if utente["ruolo"] == "impresa" and bando_id is not None:
        from app.impresa import imprese_per_bando

        with connetti() as conn:
            if imprese_per_bando(conn, utente["id"], bando_id):
                return
    raise HTTPException(status_code=403, detail="Il tuo profilo non permette questa operazione.")


@router.get("/bandi/{bando_id}/feedback")
def feedback_del_bando(bando_id: int, utente: dict = Depends(utente_corrente)) -> dict:
    _puo_giudicare(utente, bando_id)
    with connetti() as conn:
        try:
            return fb.del_bando(conn, bando_id, utente)
        except fb.ErroreFeedback as e:
            raise HTTPException(status_code=404, detail=str(e)) from e


@router.put("/bandi/{bando_id}/feedback")
def giudica(bando_id: int, dati: Giudizio, utente: dict = Depends(utente_corrente)) -> dict:
    _puo_giudicare(utente, bando_id)
    with connetti() as conn:
        try:
            r = fb.salva(conn, bando_id, utente, dati.voto, [p.model_dump() for p in dati.problemi], dati.commento)
        except fb.ErroreFeedback as e:
            raise HTTPException(status_code=422, detail=str(e)) from e
        conn.commit()
    return r


@router.get("/feedback")
def elenco_feedback(stato: str | None = None, ruolo: str | None = None, categoria: str | None = None,
                    bando: int | None = None, pagina: int = Query(1, ge=1), utente: dict = Depends(utente_corrente)) -> dict:
    """Tutti i giudizi per l'admin; per revisori e imprese solo i loro, con lo stato e la risposta."""
    solo_miei = utente["id"] if utente["ruolo"] != "admin" else None
    with connetti() as conn:
        return fb.elenco(conn, stato or None, ruolo or None, categoria or None, bando, pagina, utente_id=solo_miei) | {
            "categorie": fb.CATEGORIE}


@router.patch("/feedback/{feedback_id}")
def gestisci(feedback_id: int, dati: Gestione, admin: dict = Depends(solo_admin)) -> dict:
    with connetti() as conn:
        try:
            r = fb.gestisci(conn, feedback_id, dati.stato, dati.risposta, admin["email"])
        except fb.ErroreFeedback as e:
            raise HTTPException(status_code=404, detail=str(e)) from e
        conn.commit()
    return r
