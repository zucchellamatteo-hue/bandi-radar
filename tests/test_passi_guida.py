"""Prossimi passi (modificabili dall'admin) e guida filtrata per ruolo e permessi."""

import os

import pytest

from app import guida

db = pytest.mark.skipif(not os.environ.get("PGHOST"), reason="serve un database Postgres di prova (PGHOST)")

YAML = """
sezioni:
  - {id: a, titolo: Accesso, per: [tutti], testo: "Entra con la **password**."}
  - {id: b, titolo: Utenti, per: [admin], testo: "- Invita"}
  - {id: c, titolo: Giudizi, per: [giudizi], testo: "Vota."}
  - {id: d, titolo: Fonti, per: [lavoro], testo: "Semaforo."}
  - {id: e, titolo: La tua impresa, per: [impresa], testo: "Descrivi."}
"""


def test_guida_filtrata(tmp_path):
    f = tmp_path / "guida.yaml"
    f.write_text(YAML)
    ids = lambda u: [s["id"] for s in guida.per_utente(u, f)]   # noqa: E731
    assert ids({"ruolo": "admin", "permessi": []}) == ["a", "b", "c", "d", "e"]
    assert ids({"ruolo": "impresa", "permessi": []}) == ["a", "e"]
    assert ids({"ruolo": "revisore", "permessi": ["catalogo", "giudizi"]}) == ["a", "c"]
    assert ids({"ruolo": "revisore", "permessi": ["giudizi", "lavoro"]}) == ["a", "c", "d"]


def test_file_della_guida_valido():
    sezioni = guida.tutte()
    validi = {"tutti", "admin", "impresa", "catalogo", "giudizi", "lavoro", "modifiche", "imprese"}
    assert len({s["id"] for s in sezioni}) == len(sezioni)
    for s in sezioni:
        assert set(s.get("per") or ["tutti"]) <= validi, s["id"]
    if sezioni:
        assert any("impresa" in s["per"] for s in sezioni) and any("admin" in s["per"] for s in sezioni)


@db
def test_prossimi_passi():
    from conftest import accesso_di_prova
    from fastapi.testclient import TestClient

    from app import passi
    from app.db.connessione import connetti
    from app.db.migrazioni import applica_migrazioni
    from app.main import app

    with connetti() as conn:
        applica_migrazioni(conn)
    c = TestClient(app)
    admin = accesso_di_prova("admin")
    r = c.get("/api/passi", auth=admin).json()
    assert any("Luca" in p["titolo"] for p in r["passi"]) and r["stati"]["rimandato"] == "rimandato"
    nuovo = c.post("/api/passi", auth=admin, json={"titolo": "Provare il catalogo", "tipo": "da_sviluppare", "priorita": 1}).json()
    assert nuovo["stato"] == "da_fare" and nuovo["aggiornato_da"].startswith("prova-admin")
    assert c.post("/api/passi", auth=admin, json={"titolo": " "}).status_code == 422
    assert c.patch(f"/api/passi/{nuovo['id']}", auth=admin, json={"stato": "fatto"}).json()["stato"] == "fatto"
    assert c.patch(f"/api/passi/{nuovo['id']}", auth=admin, json={"stato": "boh"}).status_code == 422
    with connetti() as conn:
        assert "Provare il catalogo" not in passi.testo(passi.elenco(conn))      # i fatti non vanno nell'elenco
    rev = accesso_di_prova("revisore")
    assert c.get("/api/passi", auth=rev).status_code == 403                    # senza "lavoro"
    assert c.post("/api/passi", auth=rev, json={"titolo": "x"}).status_code == 403
    assert c.delete(f"/api/passi/{nuovo['id']}", auth=admin).status_code == 200
    imp = accesso_di_prova("impresa")
    assert c.get("/api/guida", auth=imp).status_code == 200
