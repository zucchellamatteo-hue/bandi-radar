"""News: controlli dei campi (senza database), pagina e API con i permessi, news attive per l'email e la Guida."""

import os
from datetime import date, timedelta

import pytest

from app import news

db = pytest.mark.skipif(not os.environ.get("PGHOST"), reason="serve un database Postgres di prova (PGHOST)")


def test_controlli():
    v = news._controlla({"titolo": "  Titolo   nuovo ", "testo": " Testo. ", "da": "2026-10-12", "a": "", "link": " "}, True)
    assert v["titolo"] == "Titolo nuovo" and v["testo"] == "Testo." and v["da"] == date(2026, 10, 12)
    assert v["a"] is None and v["link"] is None
    for sbagliata in ({"titolo": "", "testo": "x"}, {"titolo": "x"}, {"titolo": "x", "testo": "y", "link": "ftp://a"},
                      {"titolo": "x", "testo": "y", "da": "2026-10-12", "a": "2026-10-01"},
                      {"titolo": "x", "testo": "y", "pubblico": "tutti_quanti"}, {"titolo": "x", "testo": "y", "da": "ieri"},
                      {"titolo": "x", "testo": "y" * (news.LUNGHEZZA_TESTO + 1)}):
        with pytest.raises(news.ErroreNews):
            news._controlla(sbagliata, True)
    assert news._controlla({"link": "/impresa/misure"}, False) == {"link": "/impresa/misure"}


@db
def test_api_e_news_attive():
    from conftest import accesso_di_prova
    from fastapi.testclient import TestClient

    from app.db.connessione import connetti
    from app.db.migrazioni import applica_migrazioni
    from app.main import app

    with connetti() as conn:
        applica_migrazioni(conn)
        conn.commit()
    c = TestClient(app)
    admin = accesso_di_prova("admin")
    r = c.get("/api/news", auth=admin).json()
    # la prima news (migrazione 029) e' una bozza da approvare
    esempio = [n for n in r["news"] if n["titolo"].startswith("Novità di bandinQiaro")]
    assert esempio and esempio[0]["stato"] == "bozza" and r["pubblici"]["tutti"]

    oggi = date.today()
    nuova = c.post("/api/news", auth=admin, json={"titolo": "Prova API", "testo": "Due righe.",
                                                  "da": oggi.isoformat(), "pubblico": "tutti"}).json()
    assert nuova["stato"] == "bozza" and nuova["creata_da"]
    assert c.post("/api/news", auth=admin, json={"titolo": "x"}).status_code == 422
    assert c.patch("/api/news/0", auth=admin, json={"stato": "pubblicata"}).status_code == 404
    with connetti() as conn:
        assert nuova["id"] not in [n["id"] for n in news.attive(conn, oggi)]          # bozza: non va nell'email
    assert c.patch(f"/api/news/{nuova['id']}", auth=admin, json={"stato": "pubblicata"}).json()["stato"] == "pubblicata"
    assert c.patch(f"/api/news/{nuova['id']}", auth=admin, json={"a": (oggi - timedelta(days=1)).isoformat()}).status_code == 422
    with connetti() as conn:
        assert nuova["id"] in [n["id"] for n in news.attive(conn, oggi)]
        assert nuova["id"] not in [n["id"] for n in news.attive(conn, oggi - timedelta(days=1))]   # non ancora iniziata
        assert nuova["id"] not in [n["id"] for n in news.attive(conn, oggi, ("imprese",))]

    impresa = accesso_di_prova("impresa")
    assert nuova["id"] in [n["id"] for n in c.get("/api/news/attive", auth=impresa).json()]
    assert c.get("/api/news", auth=impresa).status_code == 403
    assert c.post("/api/news", auth=impresa, json={"titolo": "x", "testo": "y"}).status_code == 403
    revisore = accesso_di_prova("revisore")                                         # senza "modifiche"
    assert c.patch(f"/api/news/{nuova['id']}", auth=revisore, json={"stato": "bozza"}).status_code == 403
    assert nuova["id"] in [n["id"] for n in c.get("/api/news/attive", auth=revisore).json()]   # pubblico "tutti"
    assert c.delete(f"/api/news/{nuova['id']}", auth=admin).status_code == 200
