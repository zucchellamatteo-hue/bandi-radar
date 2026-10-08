"""Campagne di lancio: profili anonimi, abbinamento ai bandi recenti, bozze di testo; script per il computer di Matteo."""

import importlib.util
import json
import os
from pathlib import Path

import pytest

from app import campagne as cp

db = pytest.mark.skipif(not os.environ.get("PGHOST"), reason="serve un database Postgres di prova (PGHOST)")


def _script():
    percorso = Path(__file__).resolve().parents[1] / "strumenti" / "anagrafiche" / "esporta_profili.py"
    spec = importlib.util.spec_from_file_location("esporta_profili", percorso)
    modulo = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(modulo)
    return modulo


def test_script_anagrafiche_ricava_categorie():
    s = _script()
    assert s.forma_giuridica("ALFA IMPIANTI S.R.L.") == "srl" and s.forma_giuridica("BETA SRLS") == "srls"
    assert s.forma_giuridica("GAMMA S.N.C. DI ROSSI") == "snc" and s.forma_giuridica("Mario Rossi") is None
    assert s.ateco("432101") == "43.21.01" and s.ateco("43.21") == "43.21" and s.ateco("") is None
    assert s.dimensione(12, 1.5e6) == "piccola" and s.dimensione(3, 0.4e6) == "micro" and s.dimensione(None, None) is None


def test_testo_con_segnaposto():
    p = {"n_compatibili": 4, "bandi": [
        {"bando_id": 1, "titolo": "Digitale PMI", "ente": "Regione Lombardia", "scadenza": "2026-12-31", "importo": 50000,
         "percentuale": 50, "livello": "compatibile"},
        {"bando_id": 2, "titolo": "Altro", "ente": None, "scadenza": None, "importo": None, "percentuale": None, "livello": "da_verificare"}]}
    oggetto, testo = cp.testo(p, "https://esempio.it")
    assert "{RAGIONE_SOCIALE}" in oggetto and "{FIRMA}" in testo and "agevolazione fino a 50.000 €" in testo
    assert "31/12/2026" in testo and "Altro" not in testo and "altri 3 bandi" in testo and "https://esempio.it/registrati" in testo
    assert cp.testo({"n_compatibili": 0, "bandi": []}, "x") == ("", "")
    invito, messaggio = cp.messaggi_linkedin(p, "https://esempio.it")
    assert len(invito) <= 300 and "{NOME}" in invito and "Digitale PMI" in invito
    assert messaggio.startswith("Grazie {NOME}") and "non la ricontatterò" in messaggio


def test_fondo_perduto_prima():
    from app.abbinamento import catalogo, regole

    e = regole.Esito(livello=regole.COMPATIBILE)
    prestito = ({"id": 1, "tipi_agevolazione": ["finanziamento_agevolato"]}, e)
    contributo = ({"id": 2, "tipi_agevolazione": ["fondo_perduto"]}, e)
    dubbio = ({"id": 3, "tipi_agevolazione": ["fondo_perduto"]}, regole.Esito(livello=regole.DA_VERIFICARE))
    assert [b["id"] for b, _ in catalogo.prima_il_fondo_perduto([prestito, dubbio, contributo])] == [2, 1, 3]
    # Senza soldi (servizi, riconoscimenti): in secondo piano, dopo gli altri dello stesso livello (09/10).
    servizio = ({"id": 4, "tipi_agevolazione": ["servizi"]}, e)
    assert catalogo.secondo_piano(servizio[0]) and not catalogo.secondo_piano(prestito[0])
    assert [b["id"] for b, _ in catalogo.prima_il_fondo_perduto([servizio, prestito, contributo])] == [2, 1, 4]


@db
def test_campagna_completa(monkeypatch):
    from conftest import accesso_di_prova
    from fastapi.testclient import TestClient

    from app.db.connessione import connetti
    from app.db.migrazioni import applica_migrazioni
    from app.main import app
    from app.schede.campi import VINCOLI

    vincoli = {v: "nessun_vincolo" for v in VINCOLI} | {"territorio": "vincolo"}
    with connetti() as conn:
        applica_migrazioni(conn)
        with conn.cursor() as cur:
            cur.execute("""INSERT INTO bandi (titolo, ente, stato, scadenza, completezza, territorio_regioni, dati, scheda_il,
                                              contributo_massimo, percentuale, vincoli, verifica_documento, secondo_controllo)
                           VALUES ('Bando campagna Lombardia', 'Regione Lombardia', 'aperto', current_date + 40, 'bando_ufficiale',
                                   '{LOM}', %s, now(), 80000, 50, %s, '{"verificato": "si"}', '{"esito": "corretta", "fatto_il": "2099-01-01T00:00:00+00:00"}') RETURNING id""",
                        (json.dumps({"risposta": {}}), json.dumps(vincoli)))
            bando = cur.fetchone()["id"]
        conn.commit()
        profili = [{"codice": "p-aaa", "profilo": {"sedi": [{"provincia": "MI"}], "ateco": ["62.01"], "dimensione": "micro"}},
                   {"codice": "p-bbb", "profilo": {"sedi": [{"provincia": "PA"}], "ateco": ["10.41"], "dimensione": "piccola"}},
                   {"codice": "p-ccc", "profilo": {"sedi": [{"provincia": "MI"}], "ateco": ["62.01"], "dimensione": "micro"}}]
        with pytest.raises(cp.ErroreCampagna):   # dati identificativi rifiutati come nei profili
            cp.crea(conn, "x", 60, [{"codice": "p-x", "profilo": {"attivita": "scrivere a info@rossi.it"}}], "prova")
        conn.rollback()
        cid = cp.crea(conn, "Prova", 60, profili, "prova")
        riepilogo = cp.analizza(conn, cid)
        conn.commit()
        assert riepilogo["prospetti"] == 3 and riepilogo["profili_diversi"] == 2
        with conn.cursor() as cur:
            cur.execute("SELECT codice, n_compatibili, bandi FROM prospetti WHERE campagna_id = %s ORDER BY codice", (cid,))
            righe = {r["codice"]: r for r in cur.fetchall()}
        assert any(b["bando_id"] == bando and b["livello"] == "compatibile" for b in righe["p-aaa"]["bandi"])
        assert not any(b["bando_id"] == bando for b in righe["p-bbb"]["bandi"])     # Sicilia: escluso per territorio
        segmenti = cp.segmenti(conn, cid)
        assert segmenti[0]["ateco"] == "62" and segmenti[0]["regione"] == "LOM" and segmenti[0]["imprese"] == 2

    c = TestClient(app)
    admin = accesso_di_prova("admin")
    csv_testo = c.get(f"/api/campagne/{cid}/esporta", auth=admin).text
    assert "p-aaa" in csv_testo and "{RAGIONE_SOCIALE}" in csv_testo
    d = c.get(f"/api/campagne/{cid}", auth=admin).json()
    assert d["stato"] == "pronta" and d["esempio"]["testo"]
    rev = accesso_di_prova("revisore")
    assert c.get("/api/campagne", auth=rev).status_code == 403
    r = c.post("/api/campagne", auth=admin, json={"nome": "vuota", "profili": []})
    assert r.status_code == 422
    assert c.delete(f"/api/campagne/{cid}", auth=admin).status_code == 200
