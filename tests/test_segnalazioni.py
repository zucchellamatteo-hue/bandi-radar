"""Segnalazioni rapide (pulsante "Segnala"): controlli senza database e flusso completo con un Postgres di prova."""

import os

import pytest

from app import segnalazioni as sg

db = pytest.mark.skipif(not os.environ.get("PGHOST"), reason="serve un database Postgres di prova (PGHOST)")


def test_controlli_della_segnalazione():
    v = sg.pulisci({"tipo": "manca_bando", "dettagli": {"bando_nome": "  Bando Voucher Digitali ", "campo": "estraneo", "link": ""},
                    "testo": "  ", "pagina": "/catalogo?q=voucher"})
    assert v == {"tipo": "manca_bando", "testo": None, "dettagli": {"bando_nome": "Bando Voucher Digitali"}, "bando_id": None,
                 "pagina": "/catalogo?q=voucher"}
    # Il campo "bando" con un numero diventa il collegamento al bando.
    assert sg.pulisci({"tipo": "errore_scheda", "dettagli": {"bando": " #42 ", "campo": "scadenza"}})["bando_id"] == 42
    assert sg.pulisci({"tipo": "errore_scheda", "dettagli": {"bando": "Voucher Lombardia"}})["bando_id"] is None
    assert sg.pulisci({"tipo": "idea", "testo": "filtro per provincia", "bando_id": 7})["bando_id"] == 7
    with pytest.raises(sg.ErroreSegnalazione):
        sg.pulisci({"tipo": "boh", "testo": "x"})
    with pytest.raises(sg.ErroreSegnalazione):   # per un bando mancante servono nome o link
        sg.pulisci({"tipo": "manca_bando", "testo": "c'e' un bando nuovo"})
    with pytest.raises(sg.ErroreSegnalazione):   # niente di scritto
        sg.pulisci({"tipo": "plancia", "testo": "  "})
    with pytest.raises(sg.ErroreSegnalazione):
        sg.pulisci({"tipo": "altro", "testo": "x", "bando_id": -1})
    assert all({"nome", "descrizione", "campi"} <= set(t) for t in sg.TIPI.values())


@pytest.fixture
def ambiente():
    from fastapi.testclient import TestClient

    from app.db.connessione import connetti
    from app.db.migrazioni import applica_migrazioni
    from app.main import app

    with connetti() as conn:
        applica_migrazioni(conn)
        with conn.cursor() as cur:
            cur.execute("INSERT INTO bandi (titolo) VALUES ('Bando segnalazioni di prova') RETURNING id")
            bando_id = cur.fetchone()["id"]
            cur.execute("DELETE FROM segnalazioni")
        conn.commit()
    return TestClient(app), bando_id


@db
def test_segnalare_leggere_e_rispondere(ambiente):
    from conftest import accesso_di_prova

    from app.db.connessione import connetti

    c, bando_id = ambiente
    assert c.post("/api/segnalazioni", json={"tipo": "idea", "testo": "x"}).status_code == 401
    rev = accesso_di_prova("revisore")                       # permessi di base: catalogo e giudizi
    assert set(c.get("/api/segnalazioni/tipi", auth=rev).json()["tipi"]) == set(sg.TIPI)
    r = c.post("/api/segnalazioni", auth=rev, json={"tipo": "errore_scheda", "dettagli": {"bando": str(bando_id), "campo": "scadenza"},
                                                    "testo": "la scadenza e' il 30/11", "pagina": f"/bandi/{bando_id}"})
    assert r.status_code == 200 and r.json()["bando_id"] == bando_id and r.json()["stato"] == "nuova" and r.json()["ruolo"] == "revisore"
    assert c.post("/api/segnalazioni", auth=rev, json={"tipo": "manca_bando", "testo": "manca"}).status_code == 422
    imp = accesso_di_prova("impresa")
    r = c.post("/api/segnalazioni", auth=imp, json={"tipo": "manca_bando", "dettagli": {"link": "https://esempio.it/voucher"},
                                                    "pagina": "/impresa"})
    assert r.status_code == 200
    mancante = r.json()["id"]
    # Un numero che non e' un bando resta scritto ma non si collega.
    r = c.post("/api/segnalazioni", auth=imp, json={"tipo": "doppione", "dettagli": {"bando": "999999999"}, "testo": "doppio"})
    assert r.status_code == 200 and r.json()["bando_id"] is None and r.json()["dettagli"]["bando"] == "999999999"

    # Chi non ha "lavoro" vede solo le sue; non puo' gestirle.
    mie = c.get("/api/segnalazioni", auth=imp).json()
    assert mie["totale"] == 2 and {s["utente_id"] for s in mie["segnalazioni"]} == {r.json()["utente_id"]}
    assert c.patch(f"/api/segnalazioni/{mancante}", auth=rev, json={"stato": "risolta"}).status_code == 403

    admin = accesso_di_prova("admin")
    tutte = c.get("/api/segnalazioni?stato=aperte", auth=admin).json()
    assert tutte["totale"] == 3 and tutte["aperte_per_tipo"]["manca_bando"] == 1 and tutte["conteggi"]["nuova"] == 3
    solo = c.get("/api/segnalazioni?tipo=manca_bando", auth=admin).json()
    assert [s["id"] for s in solo["segnalazioni"]] == [mancante] and "email" in solo["segnalazioni"][0]
    con_bando = c.get("/api/segnalazioni?tipo=errore_scheda", auth=admin).json()["segnalazioni"][0]
    assert con_bando["bando_titolo"] == "Bando segnalazioni di prova"

    r = c.patch(f"/api/segnalazioni/{mancante}", auth=admin, json={"stato": "risolta", "risposta": "Aggiunto, grazie."})
    assert r.status_code == 200 and r.json()["gestita_da"].startswith("prova-admin")
    assert c.patch("/api/segnalazioni/999999999", auth=admin, json={"stato": "risolta"}).status_code == 404
    assert c.patch(f"/api/segnalazioni/{mancante}", auth=admin, json={"stato": "boh"}).status_code == 422
    assert c.get("/api/segnalazioni?stato=aperte", auth=admin).json()["totale"] == 2
    risposte = {s["id"]: s["risposta"] for s in c.get("/api/segnalazioni", auth=imp).json()["segnalazioni"]}
    assert risposte[mancante] == "Aggiunto, grazie."

    # Il testo per le sessioni di Claude Code e il comando per rispondere.
    from app.segnalazioni.__main__ import main

    with connetti() as conn:
        aperte = sg.elenco(conn, stato="aperte")["segnalazioni"]
        stampa = sg.testo(aperte)
    assert "Errore in una scheda" in stampa and f"bando {bando_id}" in stampa and "Manca un bando" not in stampa
    altra = aperte[0]["id"]
    assert main(["rispondi", str(altra), "respinta", "non", "e'", "un", "doppione"]) == 0
    with connetti() as conn, conn.cursor() as cur:
        cur.execute("SELECT stato, risposta, gestita_da FROM segnalazioni WHERE id = %s", (altra,))
        assert dict(cur.fetchone()) == {"stato": "respinta", "risposta": "non e' un doppione", "gestita_da": "agente"}
    assert main(["rispondi", str(altra), "boh"]) == 1
