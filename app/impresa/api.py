"""API dell'area impresa (/api/impresa/...) e, per l'admin, delle imprese iscritte e delle richieste di supporto."""

from __future__ import annotations

import os
from typing import Literal

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from app import impresa as imp
from app.db.connessione import connetti
from app.utenti import manda
from app.utenti.api import richiede, utente_corrente

router = APIRouter(prefix="/api")


def utente_impresa(utente: dict = Depends(utente_corrente)) -> dict:
    """L'area impresa e' per gli utenti impresa; l'admin puo' usarla per provarla con imprese sue."""
    if utente["ruolo"] not in ("impresa", "admin"):
        raise HTTPException(status_code=403, detail="L'area impresa e' per gli utenti impresa.")
    return utente


class DatiImpresa(BaseModel):
    nome: str
    profilo: dict
    fasce: dict = {}
    email_settimanale: bool | None = None


class Richiesta(BaseModel):
    impresa_id: int
    bando_id: int
    messaggio: str | None = None
    origine: Literal["piattaforma", "email"] = "piattaforma"


class GestioneRichiesta(BaseModel):
    stato: Literal["nuova", "in_corso", "accettata", "chiusa"]
    nota: str | None = None


def _errore(e: imp.ErroreImpresa, codice: int = 422):
    return HTTPException(status_code=404 if "non trovat" in str(e) else codice, detail=str(e))


@router.get("/impresa/imprese")
def le_mie_imprese(utente: dict = Depends(utente_impresa)) -> list[dict]:
    with connetti() as conn:
        return imp.elenco(conn, utente["id"])


@router.post("/impresa/imprese")
def nuova_impresa(dati: DatiImpresa, utente: dict = Depends(utente_impresa)) -> dict:
    with connetti() as conn:
        try:
            r = imp.crea(conn, utente["id"], dati.nome, dati.profilo, dati.fasce)
        except imp.ErroreImpresa as e:
            raise _errore(e) from e
        conn.commit()
    _sincronizza(utente["id"])
    return r


@router.put("/impresa/imprese/{impresa_id}")
def modifica_impresa(impresa_id: int, dati: DatiImpresa, utente: dict = Depends(utente_impresa)) -> dict:
    with connetti() as conn:
        try:
            r = imp.aggiorna(conn, utente["id"], impresa_id, dati.nome, dati.profilo, dati.fasce, dati.email_settimanale)
        except imp.ErroreImpresa as e:
            raise _errore(e) from e
        conn.commit()
    _sincronizza(utente["id"])
    return r


@router.delete("/impresa/imprese/{impresa_id}")
def cancella_impresa(impresa_id: int, utente: dict = Depends(utente_impresa)) -> dict:
    with connetti() as conn:
        try:
            imp.cancella(conn, utente["id"], impresa_id)
        except imp.ErroreImpresa as e:
            raise _errore(e) from e
        conn.commit()
    _sincronizza(utente["id"])
    return {"cancellata": True}


def _sincronizza(utente_id: int) -> None:
    """Imprese e sedi in piu' nell'abbonamento Stripe; un errore di Stripe non deve fermare il salvataggio."""
    from app import abbonamenti

    try:
        with connetti() as conn:
            abbonamenti.sincronizza_quantita(conn, utente_id)
            conn.commit()
    except Exception as exc:  # noqa: BLE001
        print(f"[abbonamento dell'utente {utente_id} non aggiornato: {exc}]")


def _puo_vedere(conn, utente: dict) -> bool:
    from app import abbonamenti

    r = abbonamenti.puo_vedere_i_bandi(conn, utente)
    conn.commit()
    return r


@router.get("/impresa/imprese/{impresa_id}/bandi")
def bandi_impresa(impresa_id: int, utente: dict = Depends(utente_impresa)) -> dict:
    """Con gli abbonamenti accesi, chi non ha un abbonamento (o la prova) vede quanti bandi ci sono, non quali."""
    with connetti() as conn:
        try:
            r = imp.bandi_dell_impresa(conn, utente["id"], impresa_id)
        except imp.ErroreImpresa as e:
            raise _errore(e) from e
        if not _puo_vedere(conn, utente):
            return {**r, "bandi": [], "bloccato": True}
        return r


@router.get("/impresa/bandi/{bando_id}")
def scheda(bando_id: int, utente: dict = Depends(utente_impresa)) -> dict:
    with connetti() as conn:
        if not _puo_vedere(conn, utente):
            raise HTTPException(status_code=402, detail="La prova gratuita e' finita: abbonati per vedere le schede.")
        try:
            return imp.scheda_ridotta(conn, utente["id"], bando_id)
        except imp.ErroreImpresa as e:
            raise HTTPException(status_code=404, detail=str(e)) from e


@router.post("/impresa/richieste")
def richiedi_supporto(dati: Richiesta, utente: dict = Depends(utente_impresa)) -> dict:
    with connetti() as conn:
        try:
            r = imp.richiedi_supporto(conn, utente, dati.impresa_id, dati.bando_id, dati.messaggio, dati.origine)
        except imp.ErroreImpresa as e:
            raise _errore(e) from e
        conn.commit()
    destinatario = os.environ.get("EMAIL_MATTEO")
    if destinatario:
        manda(destinatario, *imp.email_richiesta(r, utente))
    return {"id": r["id"], "stato": r["stato"],
            "messaggio": "Richiesta inviata: ti ricontattiamo noi per valutare insieme la domanda."}


@router.get("/impresa/richieste")
def le_mie_richieste(utente: dict = Depends(utente_impresa)) -> list[dict]:
    with connetti() as conn:
        return imp.richieste_dell_utente(conn, utente["id"])


# --- admin: imprese iscritte e richieste di supporto ---

@router.get("/imprese")
def imprese_iscritte(_: dict = Depends(richiede("imprese"))) -> list[dict]:
    with connetti() as conn:
        return imp.imprese_tutte(conn)


@router.get("/richieste")
def tutte_le_richieste(stato: str | None = None, _: dict = Depends(richiede("imprese"))) -> list[dict]:
    with connetti() as conn:
        return imp.richieste_tutte(conn, stato or None)


@router.patch("/richieste/{richiesta_id}")
def gestisci_richiesta(richiesta_id: int, dati: GestioneRichiesta, _: dict = Depends(richiede("imprese"))) -> dict:
    with connetti() as conn:
        try:
            r = imp.gestisci_richiesta(conn, richiesta_id, dati.stato, dati.nota)
        except imp.ErroreImpresa as e:
            raise _errore(e) from e
        conn.commit()
    return r
