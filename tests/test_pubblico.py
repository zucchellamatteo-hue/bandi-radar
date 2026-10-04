"""Pagina pubblica: testi legali, interruttore PAGINA_PUBBLICA, cookie di misurazione solo con l'ID e il consenso."""

import os

import pytest
from fastapi.testclient import TestClient

from app import pubblico

db = pytest.mark.skipif(not os.environ.get("PGHOST"), reason="serve un database Postgres di prova (PGHOST)")


def test_pagine_legali_senza_database(monkeypatch):
    from app.main import app

    monkeypatch.delenv("PAGINA_PUBBLICA", raising=False)
    c = TestClient(app)
    for nome in ("termini", "privacy", "cookie", "condizioni-supporto"):
        r = c.get(f"/{nome}")
        assert r.status_code == 200 and "Bandi Radar" in r.text, nome
        assert 'content="noindex, nofollow"' in r.text          # finche' la pagina non e' accesa
    assert pubblico.legale("inventata") is None


def test_tag_di_google_solo_con_l_id(monkeypatch):
    monkeypatch.delenv("GOOGLE_ADS_ID", raising=False)
    assert 'var ID = ""' in pubblico.pagina("x", "<p>y</p>")
    monkeypatch.setenv("GOOGLE_ADS_ID", "AW-123\"><script>")
    assert 'var ID = "AW-123script"' in pubblico.pagina("x", "<p>y</p>")   # niente caratteri pericolosi
    monkeypatch.setenv("PAGINA_PUBBLICA", "1")
    assert 'content="index, follow"' in pubblico.pagina("x", "<p>y</p>", indicizza=pubblico.pubblica())


@db
def test_presentazione_e_interruttore(monkeypatch):
    from app.db.connessione import connetti
    from app.db.migrazioni import applica_migrazioni
    from app.main import app

    with connetti() as conn:
        applica_migrazioni(conn)
    c = TestClient(app)
    r = c.get("/presentazione")
    assert r.status_code == 200 and "Fonti controllate" in r.text and "Prezzi" in r.text
    monkeypatch.setenv("PAGINA_PUBBLICA", "0")
    assert "Fonti controllate" not in c.get("/").text                 # spenta: "/" porta all'accesso
    monkeypatch.setenv("PAGINA_PUBBLICA", "1")
    assert "Fonti controllate" in c.get("/").text
    c.cookies.set("br_sessione", "qualcosa")
    assert "Fonti controllate" not in c.get("/").text                 # chi ha fatto l'accesso va alla plancia
