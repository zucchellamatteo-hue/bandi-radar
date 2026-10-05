"""API delle campagne di lancio (permesso "imprese"): carica i profili anonimi, guarda i risultati, scarica il CSV."""

from __future__ import annotations

import threading

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import Response
from pydantic import BaseModel

from app import campagne as cp
from app.db.connessione import connetti
from app.utenti import sito_url
from app.utenti.api import richiede

router = APIRouter(prefix="/api")


class NuovaCampagna(BaseModel):
    nome: str
    giorni: int = 60
    profili: list[dict]


def _analizza_in_fondo(campagna_id: int) -> None:
    """L'abbinamento di migliaia di imprese richiede qualche minuto: si fa fuori dalla richiesta."""
    try:
        with connetti() as conn:
            cp.analizza(conn, campagna_id)
            conn.commit()
    except Exception as exc:  # noqa: BLE001
        with connetti() as conn, conn.cursor() as cur:
            cur.execute("UPDATE campagne SET stato = 'errore', riepilogo = coalesce(riepilogo, '{}') || jsonb_build_object('errore', %s::text) "
                        "WHERE id = %s", (str(exc)[:300], campagna_id))
            conn.commit()


@router.get("/campagne")
def elenco(_: dict = Depends(richiede("imprese"))) -> list[dict]:
    with connetti() as conn:
        return cp.elenco(conn)


@router.post("/campagne")
def crea(dati: NuovaCampagna, utente: dict = Depends(richiede("imprese"))) -> dict:
    with connetti() as conn:
        try:
            cid = cp.crea(conn, dati.nome, dati.giorni, dati.profili, utente["email"])
        except cp.ErroreCampagna as e:
            raise HTTPException(status_code=422, detail=str(e)) from e
        conn.commit()
    threading.Thread(target=_analizza_in_fondo, args=(cid,), daemon=True).start()
    return {"id": cid}


@router.get("/campagne/{campagna_id}")
def dettaglio(campagna_id: int, _: dict = Depends(richiede("imprese"))) -> dict:
    with connetti() as conn:
        try:
            return cp.dettaglio(conn, campagna_id, sito_url())
        except cp.ErroreCampagna as e:
            raise HTTPException(status_code=404, detail=str(e)) from e


@router.get("/campagne/{campagna_id}/esporta")
def esporta(campagna_id: int, _: dict = Depends(richiede("imprese"))) -> Response:
    with connetti() as conn:
        testo = cp.esporta_csv(conn, campagna_id, sito_url())
    return Response("﻿" + testo, media_type="text/csv; charset=utf-8",
                    headers={"Content-Disposition": f'attachment; filename="campagna_{campagna_id}.csv"'})


@router.delete("/campagne/{campagna_id}")
def cancella(campagna_id: int, _: dict = Depends(richiede("imprese"))) -> dict:
    with connetti() as conn, conn.cursor() as cur:
        cur.execute("DELETE FROM campagne WHERE id = %s", (campagna_id,))
        conn.commit()
    return {"cancellata": True}
