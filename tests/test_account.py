"""Il mio account: esportazione dei dati e cancellazione (GDPR)."""

import os

import pytest

pytestmark = pytest.mark.skipif(not os.environ.get("PGHOST"), reason="serve un database Postgres di prova (PGHOST)")


def test_esporta_e_cancella(monkeypatch):
    from conftest import accesso_di_prova
    from fastapi.testclient import TestClient

    from app.db.connessione import connetti
    from app.db.migrazioni import applica_migrazioni
    from app.main import app

    with connetti() as conn:
        applica_migrazioni(conn)
    c = TestClient(app)
    io = accesso_di_prova("impresa")
    imp = c.post("/api/impresa/imprese", auth=io, json={"nome": "Gamma srl", "profilo": {"sedi": [{"provincia": "TO"}]}}).json()
    dati = c.get("/api/account/dati", auth=io)
    assert dati.status_code == 200 and "attachment" in dati.headers["content-disposition"]
    j = dati.json()
    assert j["imprese"][0]["nome"] == "Gamma srl" and "password_hash" not in str(j)
    assert c.post("/api/account/cancella", auth=io, json={"password": "sbagliata!!"}).status_code == 422
    assert c.post("/api/account/cancella", auth=io, json={"password": "password-di-prova"}).status_code == 200
    assert c.get("/api/accesso/io", auth=io).status_code == 401
    with connetti() as conn, conn.cursor() as cur:
        cur.execute("SELECT count(*) AS n FROM profili WHERE codice = %s", (imp["profilo_codice"],))
        assert cur.fetchone()["n"] == 0                       # anche il profilo anonimo
    admin = accesso_di_prova("admin")
    r = c.post("/api/account/cancella", auth=admin, json={"password": "password-di-prova"})
    assert r.status_code == 422 and "amministratore" in r.json()["detail"]
