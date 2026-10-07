"""API delle news: elenco con il permesso "lavoro", scrittura con "modifiche" (l'admin li ha tutti); le news attive per
chiunque abbia fatto l'accesso (riquadro in cima alla Guida)."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException

from app import news
from app.db.connessione import connetti
from app.utenti.api import richiede, utente_corrente

router = APIRouter(prefix="/api")


def _chi(u: dict) -> str:
    return u.get("nome") or u["email"]


def _errore(e: news.ErroreNews) -> HTTPException:
    return HTTPException(status_code=404 if "non trovata" in str(e) else 422, detail=str(e))


@router.get("/news")
def elenco(_: dict = Depends(richiede("lavoro"))) -> dict:
    with connetti() as conn:
        return {"news": news.elenco(conn), "pubblici": news.PUBBLICI, "stati": news.STATI}


@router.get("/news/attive")
def attive(utente: dict = Depends(utente_corrente)) -> list[dict]:
    with connetti() as conn:
        return news.per_utente(conn, utente)


@router.post("/news")
def crea(dati: dict, utente: dict = Depends(richiede("modifiche"))) -> dict:
    with connetti() as conn:
        try:
            r = news.crea(conn, dati, _chi(utente))
        except news.ErroreNews as e:
            raise _errore(e) from e
        conn.commit()
    return r


@router.patch("/news/{news_id}")
def modifica(news_id: int, dati: dict, utente: dict = Depends(richiede("modifiche"))) -> dict:
    with connetti() as conn:
        try:
            r = news.modifica(conn, news_id, dati, _chi(utente))
        except news.ErroreNews as e:
            raise _errore(e) from e
        conn.commit()
    return r


@router.delete("/news/{news_id}")
def cancella(news_id: int, _: dict = Depends(richiede("modifiche"))) -> dict:
    with connetti() as conn:
        news.cancella(conn, news_id)
        conn.commit()
    return {"cancellata": True}
