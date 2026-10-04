"""API degli abbonamenti: pagina "Abbonamento" dell'impresa, webhook di Stripe, elenco e modifiche dell'admin."""

from __future__ import annotations

import json
import os
from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel

from app import abbonamenti as ab
from app.db.connessione import connetti
from app.impresa.api import utente_impresa
from app.utenti.api import solo_admin

router = APIRouter(prefix="/api")


class Piano(BaseModel):
    piano: Literal["mensile", "annuale"]


class Modifica(BaseModel):
    stato: Literal["prova", "gratuito", "disdetto"] | None = None
    giorni_prova_in_piu: int | None = None
    nota: str | None = None


@router.get("/impresa/abbonamento")
def il_mio_abbonamento(utente: dict = Depends(utente_impresa)) -> dict:
    with connetti() as conn:
        r = ab.riepilogo(conn, utente)
        conn.commit()
    return r


@router.post("/impresa/abbonamento/checkout")
def paga(dati: Piano, utente: dict = Depends(utente_impresa)) -> dict:
    with connetti() as conn:
        try:
            return {"url": ab.checkout(conn, utente, dati.piano)}
        except ab.ErroreAbbonamento as e:
            raise HTTPException(status_code=422, detail=str(e)) from e


@router.post("/impresa/abbonamento/portale")
def gestisci(utente: dict = Depends(utente_impresa)) -> dict:
    with connetti() as conn:
        try:
            return {"url": ab.portale(conn, utente)}
        except ab.ErroreAbbonamento as e:
            raise HTTPException(status_code=422, detail=str(e)) from e


@router.post("/stripe/webhook")
async def webhook(request: Request) -> dict:
    """Eventi di Stripe (pubblico, ma accettato solo con la firma giusta: STRIPE_WEBHOOK_SECRET)."""
    corpo = await request.body()
    if not ab.verifica_firma(corpo, request.headers.get("stripe-signature"), os.environ.get("STRIPE_WEBHOOK_SECRET", "")):
        raise HTTPException(status_code=400, detail="firma non valida")
    evento = json.loads(corpo)
    with connetti() as conn:
        esito = ab.gestisci_evento(conn, evento)
        conn.commit()
    return {"ricevuto": True, "esito": esito}


@router.get("/abbonamenti")
def tutti(_: dict = Depends(solo_admin)) -> list[dict]:
    with connetti() as conn:
        return ab.elenco(conn)


@router.patch("/abbonamenti/{utente_id}")
def modifica(utente_id: int, dati: Modifica, _: dict = Depends(solo_admin)) -> dict:
    with connetti() as conn:
        try:
            r = ab.imposta(conn, utente_id, dati.stato, dati.giorni_prova_in_piu, dati.nota)
        except ab.ErroreAbbonamento as e:
            raise HTTPException(status_code=422, detail=str(e)) from e
        conn.commit()
    return r
