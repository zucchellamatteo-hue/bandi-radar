"""API dei prossimi passi: lettura con il permesso "lavoro", modifiche solo per l'admin."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException

from app import passi
from app.db.connessione import connetti
from app.utenti.api import richiede, solo_admin

router = APIRouter(prefix="/api")


@router.get("/passi")
def elenco(_: dict = Depends(richiede("lavoro"))) -> dict:
    with connetti() as conn:
        return {"passi": passi.elenco(conn), "tipi": passi.TIPI, "stati": passi.STATI}


@router.post("/passi")
def crea(dati: dict, admin: dict = Depends(solo_admin)) -> dict:
    with connetti() as conn:
        try:
            r = passi.crea(conn, dati, admin["email"])
        except passi.ErrorePasso as e:
            raise HTTPException(status_code=422, detail=str(e)) from e
        conn.commit()
    return r


@router.patch("/passi/{passo_id}")
def modifica(passo_id: int, dati: dict, admin: dict = Depends(solo_admin)) -> dict:
    with connetti() as conn:
        try:
            r = passi.modifica(conn, passo_id, dati, admin["email"])
        except passi.ErrorePasso as e:
            raise HTTPException(status_code=422, detail=str(e)) from e
        conn.commit()
    return r


@router.delete("/passi/{passo_id}")
def cancella(passo_id: int, _: dict = Depends(solo_admin)) -> dict:
    with connetti() as conn:
        passi.cancella(conn, passo_id)
        conn.commit()
    return {"cancellato": True}
