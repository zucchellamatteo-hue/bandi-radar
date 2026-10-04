"""Abbonamenti: firma dei webhook, accesso, chiavi vere rifiutate, checkout e eventi con Stripe finto."""

import hashlib
import hmac
import json
import os
import time
from datetime import datetime, timedelta, timezone

import pytest

from app import abbonamenti as ab

db = pytest.mark.skipif(not os.environ.get("PGHOST"), reason="serve un database Postgres di prova (PGHOST)")


def _firma(corpo: bytes, segreto: str, ts: int | None = None) -> str:
    ts = ts or int(time.time())
    return f"t={ts},v1=" + hmac.new(segreto.encode(), f"{ts}.".encode() + corpo, hashlib.sha256).hexdigest()


def test_firma_dei_webhook():
    corpo = b'{"id": "evt_1"}'
    assert ab.verifica_firma(corpo, _firma(corpo, "whsec_x"), "whsec_x")
    assert not ab.verifica_firma(corpo, _firma(corpo, "whsec_altro"), "whsec_x")
    assert not ab.verifica_firma(corpo + b" ", _firma(corpo, "whsec_x"), "whsec_x")
    assert not ab.verifica_firma(corpo, _firma(corpo, "whsec_x", int(time.time()) - 3600), "whsec_x")   # vecchia
    assert not ab.verifica_firma(corpo, None, "whsec_x") and not ab.verifica_firma(corpo, "t=1,v1=x", "")


def test_accesso_secondo_lo_stato():
    ora = datetime.now(timezone.utc)
    base = {"prova_fino_al": None, "fine_periodo": None}
    assert ab.ha_accesso({**base, "stato": "prova", "prova_fino_al": ora + timedelta(days=1)})
    assert not ab.ha_accesso({**base, "stato": "prova", "prova_fino_al": ora - timedelta(days=1)})
    assert ab.ha_accesso({**base, "stato": "gratuito"}) and ab.ha_accesso({**base, "stato": "in_ritardo"})
    assert ab.ha_accesso({**base, "stato": "disdetto", "fine_periodo": ora + timedelta(days=3)})
    assert not ab.ha_accesso({**base, "stato": "disdetto", "fine_periodo": ora - timedelta(days=3)})


def test_solo_chiavi_di_prova(monkeypatch):
    monkeypatch.setenv("STRIPE_SECRET_KEY", "sk_live_vera")
    monkeypatch.delenv("STRIPE_PAGAMENTI_VERI", raising=False)
    with pytest.raises(ab.ErroreAbbonamento, match="vera"):
        ab._chiave()
    monkeypatch.setenv("STRIPE_SECRET_KEY", "sk_test_prova")
    assert ab._chiave() == "sk_test_prova"
    monkeypatch.delenv("STRIPE_SECRET_KEY")
    with pytest.raises(ab.ErroreAbbonamento, match="configurati"):
        ab._chiave()


PROFILO = {"forma_giuridica": "srl", "sedi": [{"provincia": "MI"}, {"provincia": "BG"}], "ateco": ["62.01"]}


class StripeFinto:
    """Risponde alle chiamate di app.abbonamenti.chiama e le ricorda."""

    def __init__(self):
        self.chiamate = []

    def __call__(self, metodo, percorso, dati=None):
        self.chiamate.append((metodo, percorso, dati or {}))
        if percorso == "/prices":
            return {"data": [{"lookup_key": k, "id": f"price_{k}"} for k in ab.CHIAVI_PREZZI.values()]}
        if percorso == "/customers":
            return {"id": "cus_prova"}
        if percorso == "/checkout/sessions":
            return {"url": "https://checkout.stripe.com/prova"}
        if percorso == "/billing_portal/sessions":
            return {"url": "https://billing.stripe.com/prova"}
        if percorso.startswith("/subscriptions/") and metodo == "GET":
            return {"items": {"data": [{"id": "si_1", "price": {"lookup_key": "br_mensile"}}]}}
        return {}


@db
def test_prova_checkout_eventi_e_blocco(monkeypatch):
    from conftest import accesso_di_prova
    from fastapi.testclient import TestClient

    from app.db.connessione import connetti
    from app.db.migrazioni import applica_migrazioni
    from app.main import app

    with connetti() as conn:
        applica_migrazioni(conn)
    finto = StripeFinto()
    monkeypatch.setattr(ab, "chiama", finto)
    monkeypatch.setenv("STRIPE_SECRET_KEY", "sk_test_prova")
    monkeypatch.setenv("STRIPE_WEBHOOK_SECRET", "whsec_prova")
    monkeypatch.setenv("ABBONAMENTI_ATTIVI", "1")
    c = TestClient(app)
    io = accesso_di_prova("impresa")
    iid = c.post("/api/impresa/imprese", auth=io, json={"nome": "Prova spa", "profilo": PROFILO}).json()["id"]
    c.post("/api/impresa/imprese", auth=io, json={"nome": "Seconda", "profilo": {**PROFILO, "sedi": [{"provincia": "MI"}]}})

    a = c.get("/api/impresa/abbonamento", auth=io).json()
    assert a["stato"] == "prova" and a["accesso"] and a["giorni_prova"] == 14
    assert a["imprese_extra"] == 1 and a["sedi_extra"] == 1                 # la seconda impresa, la seconda sede
    assert "bloccato" not in c.get(f"/api/impresa/imprese/{iid}/bandi", auth=io).json()

    # Pagamento: la pagina di Stripe con il piano, l'impresa e la sede in piu' e i giorni di prova rimasti.
    assert c.post("/api/impresa/abbonamento/checkout", auth=io, json={"piano": "annuale"}).json()["url"].startswith("https://checkout")
    dati = [d for m, p, d in finto.chiamate if p == "/checkout/sessions"][0]
    assert dati["line_items[0][price]"] == "price_br_annuale" and dati["line_items[1][quantity]"] == "1"
    assert dati["line_items[2][price]"] == "price_br_sede_extra" and "subscription_data[trial_end]" in dati
    utente_id = int(dati["client_reference_id"])

    def manda(evento):
        corpo = json.dumps(evento).encode()
        return c.post("/api/stripe/webhook", content=corpo, headers={"stripe-signature": _firma(corpo, "whsec_prova")})

    assert c.post("/api/stripe/webhook", content=b"{}", headers={"stripe-signature": "t=1,v1=x"}).status_code == 400
    assert manda({"id": f"evt_a{utente_id}", "type": "checkout.session.completed",
                  "data": {"object": {"mode": "subscription", "client_reference_id": str(utente_id),
                                      "customer": "cus_prova", "subscription": f"sub_{utente_id}"}}}).status_code == 200
    inizio = int(time.time())
    evento = {"id": f"evt_b{utente_id}", "type": "customer.subscription.updated",
              "data": {"object": {"id": f"sub_{utente_id}", "customer": "cus_prova", "status": "active", "start_date": inizio,
                                  "current_period_end": inizio + 30 * 86400,
                                  "metadata": {"utente_id": str(utente_id), "piano": "annuale"}}}}
    assert manda(evento).json()["esito"].endswith("attivo")
    assert manda(evento).json()["esito"] == "gia' ricevuto"                 # Stripe puo' rimandarlo
    a = c.get("/api/impresa/abbonamento", auth=io).json()
    assert a["stato"] == "attivo" and a["piano"] == "annuale" and a["fine_impegno"] and a["portale"]
    assert c.post("/api/impresa/abbonamento/portale", auth=io).json()["url"].startswith("https://billing")

    # Disdetto e periodo finito: si vedono i numeri, non i bandi; l'admin lo rende gratuito e torna tutto.
    with connetti() as conn, conn.cursor() as cur:
        cur.execute("UPDATE abbonamenti SET stato = 'disdetto', fine_periodo = now() - interval '1 day' WHERE utente_id = %s",
                    (utente_id,))
        conn.commit()
    r = c.get(f"/api/impresa/imprese/{iid}/bandi", auth=io).json()
    assert r["bloccato"] and r["bandi"] == [] and "conteggi" in r
    admin = accesso_di_prova("admin")
    assert any(x["utente_id"] == utente_id for x in c.get("/api/abbonamenti", auth=admin).json())
    assert c.patch(f"/api/abbonamenti/{utente_id}", auth=admin, json={"stato": "gratuito"}).status_code == 200
    assert "bloccato" not in c.get(f"/api/impresa/imprese/{iid}/bandi", auth=io).json()
    assert c.patch(f"/api/abbonamenti/{utente_id}", auth=admin, json={"stato": "attivo"}).status_code == 422
    assert c.patch(f"/api/abbonamenti/{utente_id}", auth=io, json={"stato": "gratuito"}).status_code == 403


@db
def test_abbonamenti_spenti_lasciano_entrare(monkeypatch):
    from conftest import accesso_di_prova
    from fastapi.testclient import TestClient

    from app.db.connessione import connetti
    from app.main import app

    monkeypatch.setenv("ABBONAMENTI_ATTIVI", "0")
    c = TestClient(app)
    io = accesso_di_prova("impresa")
    iid = c.post("/api/impresa/imprese", auth=io, json={"nome": "Libera", "profilo": PROFILO}).json()["id"]
    with connetti() as conn, conn.cursor() as cur:
        cur.execute("UPDATE abbonamenti SET prova_fino_al = now() - interval '1 day' "
                    "WHERE utente_id = (SELECT utente_id FROM imprese WHERE id = %s)", (iid,))
        conn.commit()
    assert "bloccato" not in c.get(f"/api/impresa/imprese/{iid}/bandi", auth=io).json()
