"""API dell'email settimanale per impresa: approvazione dell'admin e link pubblico per non riceverla piu'."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException

from app import impresa
from app.db.connessione import connetti
from app.notifiche import email_imprese
from app.utenti.api import richiede

router = APIRouter(prefix="/api")


def _chi(admin: dict) -> str:
    return admin.get("nome") or admin["email"]


def _errore(e: ValueError) -> HTTPException:
    return HTTPException(status_code=404 if "non trovata" in str(e) else 409, detail=str(e))


@router.get("/email-imprese")
def elenco(admin: dict = Depends(richiede("imprese"))) -> list[dict]:
    with connetti() as conn:
        return email_imprese.in_attesa(conn)


@router.post("/email-imprese/prepara")
def prepara(admin: dict = Depends(richiede("imprese"))) -> dict:
    with connetti() as conn:
        return email_imprese.prepara(conn)


@router.post("/email-imprese/{email_id}/invia")
def invia(email_id: int, admin: dict = Depends(richiede("imprese"))) -> dict:
    with connetti() as conn:
        try:
            esito = email_imprese.invia(conn, email_id, _chi(admin))
        except ValueError as e:
            raise _errore(e) from e
    return {"esito": esito}


@router.post("/email-imprese/{email_id}/scarta")
def scarta(email_id: int, admin: dict = Depends(richiede("imprese"))) -> dict:
    with connetti() as conn:
        try:
            email_imprese.scarta(conn, email_id, _chi(admin))
        except ValueError as e:
            raise _errore(e) from e
    return {"ok": True}


@router.get("/disiscrizione")
def disiscrizione(codice: str = "") -> dict:
    """Pubblica (senza accesso): il codice nel link dell'email basta a spegnere l'email settimanale di quell'impresa."""
    with connetti() as conn:
        nome = impresa.disiscrivi(conn, codice)
        conn.commit()
    if not nome:
        raise HTTPException(status_code=404, detail="Link non valido.")
    return {"impresa": nome}
