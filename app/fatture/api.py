"""API delle fatture: dati di fatturazione dell'impresa, elenco e invio per l'admin, notifiche di Invoicetronic."""

from __future__ import annotations

import json
import os

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import Response

from app import abbonamenti, fatture
from app.db.connessione import connetti
from app.impresa.api import utente_impresa
from app.utenti.api import richiede

router = APIRouter(prefix="/api")


@router.get("/impresa/fatturazione")
def i_miei_dati(utente: dict = Depends(utente_impresa)) -> dict:
    with connetti() as conn:
        return {"dati": fatture.leggi_dati(conn, utente["id"]), "richiesti": fatture.attive()}


@router.put("/impresa/fatturazione")
def salva(dati: dict, utente: dict = Depends(utente_impresa)) -> dict:
    with connetti() as conn:
        try:
            r = fatture.salva_dati(conn, utente["id"], dati)
        except fatture.ErroreFattura as e:
            raise HTTPException(status_code=422, detail=str(e)) from e
        conn.commit()
    return r


@router.get("/fatture")
def elenco(_: dict = Depends(richiede("imprese"))) -> list[dict]:
    with connetti() as conn:
        return fatture.elenco(conn)


@router.get("/fatture/{fattura_id}/xml")
def xml(fattura_id: int, _: dict = Depends(richiede("imprese"))) -> Response:
    with connetti() as conn, conn.cursor() as cur:
        cur.execute("SELECT anno, numero, xml FROM fatture WHERE id = %s", (fattura_id,))
        f = cur.fetchone()
    if not f:
        raise HTTPException(status_code=404, detail="Fattura non trovata.")
    return Response(f["xml"], media_type="application/xml",
                    headers={"Content-Disposition": f'attachment; filename="fattura_{f["anno"]}_{f["numero"]}.xml"'})


@router.post("/fatture/{fattura_id}/invia")
def reinvia(fattura_id: int, _: dict = Depends(richiede("modifiche"))) -> dict:
    with connetti() as conn:
        esito = fatture.invia(conn, fattura_id)
        conn.commit()
    return {"esito": esito}


@router.post("/fatture/{fattura_id}/aggiorna")
def aggiorna(fattura_id: int, _: dict = Depends(richiede("imprese"))) -> dict:
    with connetti() as conn:
        try:
            esito = fatture.aggiorna_stato(conn, fattura_id)
        except fatture.ErroreFattura as e:
            raise HTTPException(status_code=422, detail=str(e)) from e
        conn.commit()
    return {"esito": esito}


@router.post("/invoicetronic/webhook")
async def webhook(request: Request) -> dict:
    """Notifiche di Invoicetronic (firma come Stripe, intestazione Invoicetronic-Signature): a ogni notifica dello SdI
    (update.add) si aggiorna lo stato della fattura."""
    corpo = await request.body()
    segreto = os.environ.get("INVOICETRONIC_WEBHOOK_SECRET", "")
    if not abbonamenti.verifica_firma(corpo, request.headers.get("invoicetronic-signature"), segreto):
        raise HTTPException(status_code=400, detail="firma non valida")
    evento = json.loads(corpo)
    if evento.get("endpoint") != "update" or not evento.get("resource_id"):
        return {"ricevuto": True}
    notifica = fatture.chiama("GET", f"/update/{evento['resource_id']}")
    with connetti() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT id FROM fatture WHERE invio_id = %s", (str(notifica.get("send_id")),))
            f = cur.fetchone()
        esito = fatture.aggiorna_stato(conn, f["id"]) if f else "fattura sconosciuta"
        conn.commit()
    return {"ricevuto": True, "esito": esito}
