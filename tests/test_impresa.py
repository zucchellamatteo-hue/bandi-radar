"""Area impresa: fasce, imprese con profilo anonimo, bandi pertinenti, scheda ridotta, richieste di supporto, registrazione."""

import json
import os
import uuid

import pytest

from app import impresa as imp

db = pytest.mark.skipif(not os.environ.get("PGHOST"), reason="serve un database Postgres di prova (PGHOST)")


def test_dimensione_dalle_fasce():
    assert imp.dimensione_dalle_fasce("1-9", "fino_2m") == "micro"
    assert imp.dimensione_dalle_fasce("1-9", "10m-50m") == "media"      # vince la classe piu' grande
    assert imp.dimensione_dalle_fasce("50-249", None) == "media"
    assert imp.dimensione_dalle_fasce(None, None) is None


PROFILO = {"forma_giuridica": "srl", "sedi": [{"tipo": "legale_e_operativa", "provincia": "MI"}], "ateco": ["62.01"]}


@pytest.fixture
def ambiente(monkeypatch):
    from fastapi.testclient import TestClient

    from app import utenti as u
    from app.db.connessione import connetti
    from app.db.migrazioni import applica_migrazioni
    from app.main import app

    monkeypatch.setenv("COOKIE_SICURO", "0")
    monkeypatch.setattr(u, "manda", lambda *a, **k: "stampata")
    monkeypatch.setattr("app.impresa.api.manda", lambda *a, **k: "stampata")
    with connetti() as conn:
        applica_migrazioni(conn)
        with conn.cursor() as cur:
            dati = json.dumps({"risposta": {"titolo": "x"}})
            cur.execute("""INSERT INTO bandi (titolo, ente, url, stato, scadenza, completezza, territorio_regioni, sintesi, dati,
                                              tipi_agevolazione, contributo_massimo)
                           VALUES ('Bando digitale Lombardia', 'Regione Lombardia', 'https://esempio.it/l', 'aperto',
                                   current_date + 30, 'bando_ufficiale', '{LOM}', 'Contributi per il digitale.', %s,
                                   '{fondo_perduto}', 50000) RETURNING id""", (dati,))
            aperto = cur.fetchone()["id"]
            cur.execute("""INSERT INTO bandi (titolo, stato, completezza, territorio_regioni, dati)
                           VALUES ('Bando chiuso', 'chiuso', 'bando_ufficiale', '{LOM}', %s) RETURNING id""", (dati,))
            chiuso = cur.fetchone()["id"]
        conn.commit()
    return TestClient(app), aperto, chiuso


@db
def test_imprese_bandi_e_scheda_ridotta(ambiente):
    from conftest import accesso_di_prova

    c, aperto, chiuso = ambiente
    io = accesso_di_prova("impresa")
    assert c.get("/api/impresa/imprese", auth=io).json() == []
    assert c.get("/api/valori", auth=io).status_code == 200          # elenchi per il modulo guidato
    assert c.get("/api/bandi", auth=io).status_code == 403           # il catalogo completo no
    r = c.post("/api/impresa/imprese", auth=io,
               json={"nome": "Rossi Software srl", "profilo": PROFILO, "fasce": {"dipendenti": "1-9", "fatturato": "fino_2m"}})
    assert r.status_code == 200, r.text
    impresa = r.json()
    assert impresa["profilo"]["dimensione"] == "micro" and impresa["profilo_codice"].startswith("imp-")
    assert "Rossi" not in json.dumps(impresa["profilo"])               # il nome non entra nel profilo anonimo
    assert c.post("/api/impresa/imprese", auth=io, json={"nome": " ", "profilo": PROFILO}).status_code == 422
    assert c.post("/api/impresa/imprese", auth=io,
                  json={"nome": "X", "profilo": {**PROFILO, "attivita": "mail a mario@rossi.it"}}).status_code == 422

    bandi = c.get(f"/api/impresa/imprese/{impresa['id']}/bandi", auth=io).json()
    ids = [b["id"] for b in bandi["bandi"]]
    assert aperto in ids and chiuso not in ids
    assert all(b["esito"]["livello"] != "escluso" for b in bandi["bandi"]) and "qualita" not in bandi["bandi"][0]
    # Pagina "I miei bandi" (07/10): gruppo, agevolazione in una riga, motivo, riepilogo e misure nazionali.
    riga = next(b for b in bandi["bandi"] if b["id"] == aperto)
    assert riga["gruppo"] in ("adatti", "da_valutare") and riga["agevolazione"] == "Fondo perduto, fino a 50.000 €"
    assert riga["motivo"] and riga["fondo_perduto"] is True and riga["giorni_alla_scadenza"] == 30 and not riga["in_scadenza"]
    assert {"adatti", "da_valutare", "in_scadenza", "nuovi"} <= set(bandi["conteggi"]) and "misure" in bandi["misure"]
    admin = accesso_di_prova("admin")
    vista = c.get(f"/api/profili/{impresa['profilo_codice']}/vista-impresa", auth=admin).json()
    assert vista["impresa"]["nome"] == "Rossi Software srl" and [b["id"] for b in vista["bandi"]] == ids
    assert c.get(f"/api/profili/{impresa['profilo_codice']}/vista-impresa", auth=io).status_code == 403

    scheda = c.get(f"/api/impresa/bandi/{aperto}", auth=io).json()
    assert scheda["titolo"] == "Bando digitale Lombardia" and "verificare" in scheda["avvertenza"]
    assert scheda["imprese"][0]["nome"] == "Rossi Software srl" and "dati" not in scheda
    assert c.get(f"/api/impresa/bandi/{chiuso}", auth=io).status_code == 404

    # Feedback dell'impresa: solo sui bandi che vede.
    assert c.put(f"/api/bandi/{aperto}/feedback", json={"voto": 5}, auth=io).status_code == 200
    assert c.put(f"/api/bandi/{chiuso}/feedback", json={"voto": 5}, auth=io).status_code == 403

    # Un'altra impresa (altro utente) non vede le imprese del primo.
    altro = accesso_di_prova("impresa")
    assert c.get(f"/api/impresa/imprese/{impresa['id']}/bandi", auth=altro).status_code == 404
    assert c.get(f"/api/impresa/bandi/{aperto}", auth=altro).status_code == 404

    # Modifica: email settimanale spenta, fasce cambiate.
    r = c.put(f"/api/impresa/imprese/{impresa['id']}", auth=io,
              json={"nome": "Rossi Software srl", "profilo": PROFILO, "fasce": {"dipendenti": "10-49"}, "email_settimanale": False})
    assert r.status_code == 200 and r.json()["profilo"]["dimensione"] == "piccola" and r.json()["email_settimanale"] is False


@db
def test_richiesta_di_supporto_e_pagina_admin(ambiente):
    from conftest import accesso_di_prova

    c, aperto, chiuso = ambiente
    io = accesso_di_prova("impresa")
    iid = c.post("/api/impresa/imprese", auth=io, json={"nome": "Bianchi snc", "profilo": PROFILO}).json()["id"]
    r = c.post("/api/impresa/richieste", auth=io, json={"impresa_id": iid, "bando_id": aperto, "messaggio": "vorrei rifare il sito"})
    assert r.status_code == 200, r.text
    assert c.post("/api/impresa/richieste", auth=io, json={"impresa_id": iid, "bando_id": aperto}).status_code == 422   # gia' aperta
    assert c.post("/api/impresa/richieste", auth=io, json={"impresa_id": iid, "bando_id": chiuso}).status_code == 422
    assert c.get("/api/impresa/richieste", auth=io).json()[0]["stato"] == "nuova"

    admin = accesso_di_prova("admin")
    richieste = c.get("/api/richieste", auth=admin).json()
    mia = next(x for x in richieste if x["impresa_id"] == iid)
    assert mia["impresa_nome"] == "Bianchi snc" and mia["messaggio"] == "vorrei rifare il sito"
    assert c.patch(f"/api/richieste/{mia['id']}", auth=admin, json={"stato": "in_corso", "nota": "chiamato"}).status_code == 200
    assert any(i["nome"] == "Bianchi snc" for i in c.get("/api/imprese", auth=admin).json())

    rev = accesso_di_prova("revisore")
    for rotta in ("/api/impresa/imprese", "/api/richieste", "/api/imprese"):
        assert c.get(rotta, auth=rev).status_code == 403, rotta
    assert c.get("/api/richieste", auth=io).status_code == 403


@db
def test_profili_delle_imprese_fuori_dalla_pagina_profili(ambiente):
    from conftest import accesso_di_prova

    c, _, _ = ambiente
    io = accesso_di_prova("impresa")
    codice = c.post("/api/impresa/imprese", auth=io, json={"nome": "Verdi", "profilo": PROFILO}).json()["profilo_codice"]
    admin = accesso_di_prova("admin")
    assert codice not in [p["codice"] for p in c.get("/api/profili", auth=admin).json()]
    assert c.put(f"/api/profili/{codice}", auth=admin, json=PROFILO).status_code == 409
    assert c.delete(f"/api/profili/{codice}", auth=admin).status_code == 404


@db
def test_registrazione_e_conferma(ambiente, monkeypatch):
    from app import utenti as u

    c, _, _ = ambiente
    email = f"nuova-{uuid.uuid4().hex[:8]}@esempio.it"
    corpo = {"email": email, "password": "password-lunga-1", "nome": "Nuova"}
    monkeypatch.setenv("REGISTRAZIONE_APERTA", "0")
    assert c.post("/api/accesso/registrazione", json=corpo).status_code == 403
    monkeypatch.setenv("REGISTRAZIONE_APERTA", "1")
    mandate = []
    monkeypatch.setattr(u, "manda", lambda dest, oggetto, testo: mandate.append(testo) or "stampata")
    assert c.post("/api/accesso/registrazione", json=corpo).status_code == 200
    # Prima della conferma non si entra.
    r = c.post("/api/accesso/entra", json={"email": email, "password": "password-lunga-1"})
    assert r.status_code == 401 and "conferma" in r.json()["detail"]
    codice = mandate[0].split("codice=")[1].split()[0]
    r = c.post("/api/accesso/conferma", json={"codice": codice})
    assert r.status_code == 200 and r.json()["ruolo"] == "impresa"
    assert c.get("/api/impresa/imprese").status_code == 200
    assert c.post("/api/accesso/entra", json={"email": email, "password": "password-lunga-1"}).status_code == 200
