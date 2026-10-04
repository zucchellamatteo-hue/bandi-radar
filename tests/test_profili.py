"""Profili d'impresa anonimi: formato, controlli di anonimato, API (quest'ultima solo con un Postgres di prova)."""

import os
from datetime import date

import pytest
from pydantic import ValidationError

from app.abbinamento import regole
from app.abbinamento.profilo import Profilo

from conftest import accesso_di_prova


def test_profilo_valido_e_normalizzato():
    p = Profilo.model_validate({
        "codice": "C001", "forma_giuridica": "srl", "ateco": ["6201", " "], "sedi": [{"provincia": "mi", "comune": "Milano"}],
        "requisiti": {"femminile": True}, "temi": ["digitale"], "data_costituzione": "2019-05-01"})
    assert p.ateco == ["62.01"]
    assert p.sedi[0].provincia == "MI" and p.sedi[0].regione == "LOM"
    assert p.per_regole()["data_costituzione"] == date(2019, 5, 1)


@pytest.mark.parametrize("dati, parola", [
    ({"codice": "RSSMRA80A01F205X"}, "codice fiscale"),
    ({"codice": "12345678901"}, "partita IVA"),
    ({"codice": "C1", "note": "scrivere a mario.rossi@esempio.it"}, "email"),
    ({"codice": "C1", "attivita": "titolare RSSMRA80A01F205X"}, "codice fiscale"),
    ({"codice": "C1", "note": "chiamare 333 1234567"}, "telefono"),
    ({"codice": "Mario Rossi"}, "pattern"),
    ({"codice": "C1", "sedi": [{"regione": "PUG", "provincia": "MI"}]}, "non è in"),
    ({"codice": "C1", "forma_giuridica": "srl_unipersonale"}, "forma giuridica"),
    ({"codice": "C1", "requisiti": {"bella": True}}, "requisiti sconosciuti"),
    ({"codice": "C1", "ateco": ["C"]}, "ATECO"),
    ({"codice": "C1", "da_costituire": True, "data_costituzione": "2020-01-01"}, "da costituire"),
    ({"codice": "C1", "nome": "Rossi srl"}, "Extra inputs"),
])
def test_profilo_rifiuta_dati_personali_e_valori_sbagliati(dati, parola):
    with pytest.raises(ValidationError, match=parola):
        Profilo.model_validate(dati)


def test_startup_da_costituire_passa_nei_bandi_per_aspiranti():
    p = Profilo.model_validate({"codice": "S1", "da_costituire": True, "requisiti": {"startup_innovativa": True},
                                "sedi": [{"regione": "EMR"}]}).per_regole()
    bando = {"stato": "aperto", "completezza": "bando_ufficiale", "soggetti_ammessi": ["aspirante_imprenditore"],
             "vincoli": {"soggetti": "vincolo", "territorio": "vincolo"}, "territorio_regioni": ["EMR"]}
    assert regole.valuta(bando, p).livello == regole.DA_VERIFICARE   # gli altri vincoli sono "non noti"
    bando["vincoli"].update({k: "nessun_vincolo" for k in regole.NOMI_VINCOLI if k not in ("soggetti", "territorio")})
    assert regole.valuta(bando, p).livello == regole.COMPATIBILE


@pytest.mark.skipif(not os.environ.get("PGHOST"), reason="serve un database Postgres di prova (PGHOST)")
def test_api_profili():
    from fastapi.testclient import TestClient

    from app.db.connessione import connetti
    from app.db.migrazioni import applica_migrazioni
    from app.main import app

    with connetti() as conn:
        applica_migrazioni(conn)
        with conn.cursor() as cur:
            cur.execute("DELETE FROM profili WHERE codice LIKE 'prova-%'")
        conn.commit()
    c = TestClient(app)
    auth = accesso_di_prova()
    corpo = {"forma_giuridica": "srl", "dimensione": "piccola", "sedi": [{"provincia": "BO"}], "ateco": ["62.01"]}
    r = c.put("/api/profili/prova-1", json=corpo, auth=auth)
    assert r.status_code == 200 and r.json()["profilo"]["sedi"][0]["regione"] == "EMR"
    assert c.put("/api/profili/prova-1", json={**corpo, "dimensione": "micro"}, auth=auth).status_code == 200
    assert c.get("/api/profili/prova-1", auth=auth).json()["profilo"]["dimensione"] == "micro"
    r = c.put("/api/profili/prova-2", json={"note": "cf RSSMRA80A01F205X"}, auth=auth)
    assert r.status_code == 422 and "codice fiscale" in r.json()["detail"]
    risultati = c.get("/api/profili/prova-1/bandi", auth=auth).json()
    assert set(risultati["conteggi"]) == {"compatibile", "da_verificare", "escluso"}
    assert c.post("/api/abbina", json=corpo, auth=auth).status_code == 200
    assert c.delete("/api/profili/prova-1", auth=auth).status_code == 200
    assert c.get("/api/profili/prova-1", auth=auth).status_code == 404
