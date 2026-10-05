"""API "Il mio account": scaricare i propri dati e cancellare l'account."""

from __future__ import annotations

import json

from fastapi import APIRouter, Depends, HTTPException, Response
from pydantic import BaseModel

from app import account
from app.db.connessione import connetti
from app.utenti.api import COOKIE, utente_corrente

router = APIRouter(prefix="/api")


class Conferma(BaseModel):
    password: str


@router.get("/account/dati")
def i_miei_dati(utente: dict = Depends(utente_corrente)) -> Response:
    with connetti() as conn:
        dati = account.esporta(conn, utente["id"])
    return Response(json.dumps(dati, ensure_ascii=False, indent=2, default=str), media_type="application/json",
                    headers={"Content-Disposition": 'attachment; filename="bandi-radar-i-miei-dati.json"'})


@router.post("/account/cancella")
def cancella(dati: Conferma, response: Response, utente: dict = Depends(utente_corrente)) -> dict:
    with connetti() as conn:
        try:
            account.cancella(conn, utente, dati.password)
        except account.ErroreAccount as e:
            raise HTTPException(status_code=422, detail=str(e)) from e
        conn.commit()
    response.delete_cookie(COOKIE, path="/")
    return {"cancellato": True}
