"""Plancia: regole del semaforo (senza database) e API (solo se c'e' un database di prova: PGHOST impostata)."""

import os
from datetime import datetime, timedelta, timezone

import pytest

from app.plancia.semaforo import calcola

ADESSO = datetime(2026, 9, 24, tzinfo=timezone.utc)


def test_semaforo_verde_quando_tutto_regolare():
    s = calcola("settimanale", "attiva", False, ["ok", "ok"], ADESSO - timedelta(days=3), ADESSO)
    assert s.colore == "verde" and s.silenzio_giorni == 3 and s.soglia_silenzio_giorni == 30


def test_semaforo_rosso_con_tre_errori_o_struttura_cambiata():
    assert calcola("giornaliera", "attiva", False, ["errore", "errore", "errore", "ok"], ADESSO, ADESSO).colore == "rosso"
    assert calcola("giornaliera", "attiva", False, ["struttura_cambiata", "ok"], ADESSO, ADESSO).colore == "rosso"


def test_semaforo_giallo_con_un_errore_o_silenzio_o_mai_controllata():
    assert calcola("giornaliera", "attiva", False, ["errore", "ok"], ADESSO, ADESSO).colore == "giallo"
    s = calcola("giornaliera", "attiva", False, ["ok"], ADESSO - timedelta(days=45), ADESSO)
    assert s.colore == "giallo" and "silenzio" in s.motivo
    assert calcola("mensile", "attiva", False, [], None, ADESSO).colore == "giallo"


def test_semaforo_pausa():
    assert calcola("mensile", "attiva", True, ["ok"], ADESSO, ADESSO).colore == "pausa"
    assert calcola("mensile", "esclusa", False, [], None, ADESSO).colore == "pausa"


def test_soglia_silenzio_dipende_dalla_frequenza():
    assert calcola("mensile", "attiva", False, ["ok"], ADESSO, ADESSO).soglia_silenzio_giorni == 90
    assert calcola("giornaliera", "attiva", False, ["ok"], ADESSO, ADESSO).soglia_silenzio_giorni == 30


@pytest.mark.skipif(not os.environ.get("PGHOST"), reason="serve un database Postgres di prova (PGHOST)")
def test_api_plancia_risponde():
    from fastapi.testclient import TestClient

    os.environ.setdefault("BASIC_AUTH_USER", "prova")
    os.environ.setdefault("BASIC_AUTH_PASSWORD", "prova")
    from app.db.connessione import connetti
    from app.db.migrazioni import applica_migrazioni
    from app.main import app

    with connetti() as conn:
        applica_migrazioni(conn)
    auth = (os.environ["BASIC_AUTH_USER"], os.environ["BASIC_AUTH_PASSWORD"])
    c = TestClient(app)
    assert c.get("/api/fonti").status_code == 401
    assert c.get("/api/riepilogo", auth=auth).status_code == 200
    assert isinstance(c.get("/api/fonti", auth=auth).json(), list)
    assert "totale" in c.get("/api/annunci?q=imprese", auth=auth).json()
    assert c.get("/api/novita/settimane/2026-W39", auth=auth).status_code == 200
    assert c.get("/api/novita/settimane/x", auth=auth).status_code == 400
    assert c.get("/api/fonti/non_esiste", auth=auth).status_code == 404
