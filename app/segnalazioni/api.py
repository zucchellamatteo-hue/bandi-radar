"""API delle segnalazioni rapide: le scrive chiunque abbia fatto l'accesso, le legge tutte chi ha il permesso "lavoro"
(gli altri solo le proprie, con la risposta), le gestisce chi ha "modifiche"."""

from __future__ import annotations

from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel

from app import segnalazioni as sg
from app.db.connessione import connetti
from app.utenti import ha_permesso
from app.utenti.api import richiede, utente_corrente

router = APIRouter(prefix="/api")


class NuovaSegnalazione(BaseModel):
    tipo: str
    testo: str | None = None
    dettagli: dict[str, str | None] = {}
    bando_id: int | None = None
    pagina: str | None = None


class Gestione(BaseModel):
    stato: Literal["nuova", "presa_in_carico", "risolta", "respinta"]
    risposta: str | None = None


@router.get("/segnalazioni/tipi")
def tipi(_: dict = Depends(utente_corrente)) -> dict:
    return {"tipi": sg.TIPI, "stati": sg.STATI}


@router.post("/segnalazioni")
def segnala(dati: NuovaSegnalazione, utente: dict = Depends(utente_corrente)) -> dict:
    with connetti() as conn:
        try:
            r = sg.crea(conn, dati.model_dump(), utente)
        except sg.ErroreSegnalazione as e:
            raise HTTPException(status_code=422, detail=str(e)) from e
        conn.commit()
    return r


@router.get("/segnalazioni")
def elenco(stato: str | None = None, tipo: str | None = None, pagina: int = Query(1, ge=1),
           utente: dict = Depends(utente_corrente)) -> dict:
    solo_mie = None if ha_permesso(utente, "lavoro") else utente["id"]
    with connetti() as conn:
        return sg.elenco(conn, stato or None, tipo or None, pagina, utente_id=solo_mie) | {"tipi": sg.TIPI, "stati": sg.STATI}


@router.patch("/segnalazioni/{segnalazione_id}")
def gestisci(segnalazione_id: int, dati: Gestione, chi: dict = Depends(richiede("modifiche"))) -> dict:
    with connetti() as conn:
        try:
            r = sg.gestisci(conn, segnalazione_id, dati.stato, dati.risposta, chi["email"])
        except sg.ErroreSegnalazione as e:
            raise HTTPException(status_code=404, detail=str(e)) from e
        conn.commit()
    return r
