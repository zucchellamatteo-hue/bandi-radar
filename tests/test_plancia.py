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


def test_semaforo_fonte_che_risponde_ma_non_legge_nulla():
    s = calcola("settimanale", "attiva", False, ["ok"], None, ADESSO, elementi_ultimo=0)
    assert s.colore == "giallo" and "non si legge nulla" in s.motivo
    s = calcola("settimanale", "attiva", False, ["ok"], None, ADESSO, elementi_ultimo=5)
    assert s.motivo == "nessuna novita' trovata finora"


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
    assert "totale" in c.get("/api/annunci?esito=rilevante", auth=auth).json()
    assert "totale" in c.get("/api/annunci?esito=non_smistato", auth=auth).json()
    assert c.get("/api/allegati/999999999/file", auth=auth).status_code == 404


# --- allegati e smistamento con un database finto (senza Postgres): percorsi, autenticazione, validazione ---

class _CursoreFinto:
    def __init__(self, righe):
        self.righe, self.eseguite = list(righe), []

    def __enter__(self):
        return self

    def __exit__(self, *a):
        return False

    def execute(self, sql, valori=None):
        self.eseguite.append((sql, valori))

    def fetchone(self):
        return self.righe.pop(0) if self.righe else None


class _ConnessioneFinta:
    def __init__(self, righe):
        self.cursore = _CursoreFinto(righe)

    def __enter__(self):
        return self

    def __exit__(self, *a):
        return False

    def cursor(self):
        return self.cursore

    def commit(self):
        pass


@pytest.fixture
def client_plancia(monkeypatch, tmp_path):
    from fastapi.testclient import TestClient

    from app.main import app

    monkeypatch.setenv("BASIC_AUTH_USER", "prova")
    monkeypatch.setenv("BASIC_AUTH_PASSWORD", "segreta")
    monkeypatch.setenv("ALLEGATI_CARTELLA", str(tmp_path / "allegati"))
    (tmp_path / "allegati" / "7").mkdir(parents=True)
    (tmp_path / "allegati" / "7" / "abcdef123456_bando.pdf").write_bytes(b"%PDF-1.4 finto")
    (tmp_path / "allegati" / "7" / "abcdef123456_faq.html").write_text("<script>alert(1)</script>FAQ")
    (tmp_path / "fuori.txt").write_text("segreto")
    return TestClient(app), ("prova", "segreta")


def _db(monkeypatch, *righe):
    from app.plancia import api

    conn = _ConnessioneFinta(righe)
    monkeypatch.setattr(api, "connetti", lambda: conn)
    return conn


def test_percorso_sicuro_resta_nella_cartella(tmp_path):
    from app.plancia.api import percorso_sicuro

    cartella = tmp_path / "allegati"
    (cartella / "7").mkdir(parents=True)
    (cartella / "7" / "a.pdf").write_bytes(b"x")
    (tmp_path / "fuori.txt").write_text("segreto")
    (cartella / "7" / "collegamento.pdf").symlink_to(tmp_path / "fuori.txt")
    assert percorso_sicuro(cartella, "7/a.pdf") == cartella / "7" / "a.pdf"
    for cattivo in ("../fuori.txt", "7/../../fuori.txt", str(tmp_path / "fuori.txt"), "7", "", None, "7/collegamento.pdf"):
        assert percorso_sicuro(cartella, cattivo) is None, cattivo


def test_file_allegato_servito_con_autenticazione(client_plancia, monkeypatch):
    c, auth = client_plancia
    assert c.get("/api/allegati/1/file").status_code == 401
    _db(monkeypatch, {"tipo": "pdf", "percorso_locale": "7/abcdef123456_bando.pdf"})
    r = c.get("/api/allegati/1/file", auth=auth)
    assert r.status_code == 200 and r.content == b"%PDF-1.4 finto"
    assert r.headers["content-type"] == "application/pdf" and 'filename="bando.pdf"' in r.headers["content-disposition"]


def test_file_allegato_faq_in_sandbox(client_plancia, monkeypatch):
    c, auth = client_plancia
    _db(monkeypatch, {"tipo": "faq", "percorso_locale": "7/abcdef123456_faq.html"})
    r = c.get("/api/allegati/2/file", auth=auth)
    assert r.status_code == 200 and r.headers["content-security-policy"] == "sandbox"


def test_file_allegato_rifiuta_percorsi_fuori_cartella(client_plancia, monkeypatch):
    c, auth = client_plancia
    _db(monkeypatch, {"tipo": "pdf", "percorso_locale": "../fuori.txt"})
    assert c.get("/api/allegati/3/file", auth=auth).status_code == 404
    _db(monkeypatch)   # allegato inesistente
    assert c.get("/api/allegati/4/file", auth=auth).status_code == 404


def test_correzione_smistamento(client_plancia, monkeypatch):
    c, auth = client_plancia
    assert c.post("/api/annunci/1/smistamento", json={"esito": "forse"}, auth=auth).status_code == 422
    assert c.get("/api/annunci?esito=boh", auth=auth).status_code == 422
    conn = _db(monkeypatch, {"?column?": 1},
               {"esito": "rilevante", "deciso_da": "matteo", "proposta_esito": "non_rilevante", "proposta_da": "regole"})
    r = c.post("/api/annunci/1/smistamento", json={"esito": "rilevante"}, auth=auth)
    assert r.status_code == 200 and r.json()["deciso_da"] == "matteo" and r.json()["proposta_da"] == "regole"
    sql, valori = conn.cursore.eseguite[-1]
    assert "'matteo'" in sql and "proposta_esito" in sql and valori == (1, "rilevante")
