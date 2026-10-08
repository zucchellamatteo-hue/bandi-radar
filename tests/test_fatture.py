"""Fattura elettronica: XML valido secondo lo schema ufficiale, controlli dei dati, fattura dal pagamento Stripe."""

import json
import os
import time
from datetime import date
from pathlib import Path

import pytest
from lxml import etree

from app import fatture

db = pytest.mark.skipif(not os.environ.get("PGHOST"), reason="serve un database Postgres di prova (PGHOST)")
SCHEMA = Path(__file__).parent / "dati" / "fatturapa" / "Schema_VFPR12.xsd"
EMITTENTE = {"denominazione": "Studio Prova & C. srl", "partita_iva": "01234567890", "codice_fiscale": "", "regime": "RF01",
             "indirizzo": "Via Roma 1", "cap": "33100", "comune": "Udine", "provincia": "UD"}
CLIENTE = {"denominazione": "Alfa <Impianti> srl", "partita_iva": "09876543210", "codice_fiscale": None,
           "codice_destinatario": "ABC1234", "pec": None, "indirizzo": "Via Verdi 2", "cap": "20100", "comune": "Milano",
           "provincia": "MI"}


def _valida(xml: str) -> None:
    schema = etree.XMLSchema(etree.parse(str(SCHEMA)))
    schema.assertValid(etree.fromstring(xml.encode()))


def test_xml_valido_per_lo_schema_ufficiale():
    righe = [{"descrizione": "bandinQiaro - mensile", "quantita": 1, "prezzo_unitario": "30.00"},
             {"descrizione": "Impresa in più", "quantita": 2, "prezzo_unitario": "10.00"}]
    xml = fatture.genera_xml("1/BR", date(2026, 10, 5), CLIENTE, righe, "0000A", EMITTENTE)
    _valida(xml)
    assert "<ImponibileImporto>50.00</ImponibileImporto><Imposta>11.00</Imposta>" in xml
    assert "<ImportoTotaleDocumento>61.00</ImportoTotaleDocumento>" in xml and "Alfa &lt;Impianti&gt; srl" in xml
    # Solo PEC: codice 0000000 e PECDestinatario.
    xml = fatture.genera_xml("2/BR", date(2026, 10, 5), {**CLIENTE, "codice_destinatario": "0000000", "pec": "alfa@pec.it"},
                             righe[:1], "0000B", EMITTENTE)
    _valida(xml)
    assert "<PECDestinatario>alfa@pec.it</PECDestinatario>" in xml


def test_controlli_dei_dati_di_fatturazione():
    buoni = {"denominazione": "Alfa srl", "partita_iva": "IT09876543210", "pec": "a@pec.it", "indirizzo": "Via X 1",
             "cap": "20100", "comune": "Milano", "provincia": "mi"}
    p = fatture.controlla_dati(buoni)
    assert p["partita_iva"] == "09876543210" and p["codice_destinatario"] == "0000000" and p["provincia"] == "MI"
    with pytest.raises(fatture.ErroreFattura, match="partita IVA"):
        fatture.controlla_dati({**buoni, "partita_iva": "123"})
    with pytest.raises(fatture.ErroreFattura, match="PEC"):
        fatture.controlla_dati({**buoni, "pec": None})
    assert fatture._progressivo(1) == "00001" and fatture._progressivo(36) == "00010"


def test_chiave_vera_rifiutata(monkeypatch):
    monkeypatch.setenv("INVOICETRONIC_API_KEY", "ik_live_x")
    monkeypatch.delenv("FATTURE_VERE", raising=False)
    with pytest.raises(fatture.ErroreFattura, match="FATTURE_VERE"):
        fatture._chiave()


@db
def test_fattura_dal_pagamento_stripe(monkeypatch):
    from conftest import accesso_di_prova
    from fastapi.testclient import TestClient

    from app import abbonamenti
    from app.db.connessione import connetti
    from app.db.migrazioni import applica_migrazioni
    from app.main import app

    for k, v in EMITTENTE.items():
        monkeypatch.setenv(f"FATTURE_EMITTENTE_{k.upper()}", v)
    monkeypatch.setenv("FATTURE_ATTIVE", "1")
    monkeypatch.setenv("STRIPE_WEBHOOK_SECRET", "whsec_prova")
    inviate = []

    def finto(metodo, percorso, **kw):
        inviate.append((metodo, percorso, kw))
        if percorso.startswith("/send/xml"):
            return {"id": 777, "latest_state": "Inviato"}
        if percorso == "/update":
            return [{"state": "Consegnato", "description": "", "last_update": "2026-10-05T10:00:00"}]
        return {}

    monkeypatch.setattr(fatture, "chiama", finto)
    with connetti() as conn:
        applica_migrazioni(conn)
    c = TestClient(app)
    io = accesso_di_prova("impresa")
    assert c.put("/api/impresa/fatturazione", auth=io, json={"denominazione": "Beta srl", "partita_iva": "1"}).status_code == 422
    dati = {**CLIENTE, "denominazione": "Beta srl"}
    assert c.put("/api/impresa/fatturazione", auth=io, json=dati).status_code == 200
    utente_id = c.get("/api/accesso/io", auth=io).json()["id"]
    with connetti() as conn:
        abbonamenti.leggi(conn, utente_id)
        with conn.cursor() as cur:
            cur.execute("UPDATE abbonamenti SET stripe_cliente = %s WHERE utente_id = %s", (f"cus_f{utente_id}", utente_id))
        conn.commit()

    evento = {"id": f"evt_fatt{utente_id}", "type": "invoice.paid", "data": {"object": {
        "id": f"in_{utente_id}", "customer": f"cus_f{utente_id}", "lines": {"data": [
            {"description": "bandinQiaro - mensile", "quantity": 1, "amount": 3000,
             "period": {"start": int(time.time()), "end": int(time.time()) + 30 * 86400}},
            {"description": "Sede in più", "quantity": 1, "amount": 500}]}}}}
    corpo = json.dumps(evento).encode()
    from test_abbonamenti import _firma

    r = c.post("/api/stripe/webhook", content=corpo, headers={"stripe-signature": _firma(corpo, "whsec_prova")})
    assert r.status_code == 200 and "inviata" in r.json()["esito"], r.json()
    with connetti() as conn, conn.cursor() as cur:
        cur.execute("SELECT * FROM fatture WHERE stripe_fattura = %s", (f"in_{utente_id}",))
        f = cur.fetchone()
    assert f["stato"] == "inviata" and f["invio_id"] == "777" and str(f["totale"]) == "42.70"
    _valida(f["xml"])
    assert inviate[0][2]["headers"]["Idempotency-Key"] == f"br-fattura-{f['id']}"
    # Lo stesso pagamento rimandato da Stripe con un altro evento non crea una seconda fattura.
    with connetti() as conn:
        assert fatture.crea_da_stripe(conn, utente_id, evento["data"]["object"]) is None
        assert fatture.aggiorna_stato(conn, f["id"]) == "consegnata"
        conn.commit()
    admin = accesso_di_prova("admin")
    assert any(x["id"] == f["id"] for x in c.get("/api/fatture", auth=admin).json())
    assert c.get(f"/api/fatture/{f['id']}/xml", auth=admin).text.startswith("<?xml")
    assert c.get("/api/fatture", auth=io).status_code == 403
