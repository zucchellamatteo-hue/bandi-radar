"""Feedback sulle schede: controlli dei problemi (senza database) e flusso completo con un Postgres di prova."""

import json
import os

import pytest

from app import feedback as fb

db = pytest.mark.skipif(not os.environ.get("PGHOST"), reason="serve un database Postgres di prova (PGHOST)")


def test_problemi_puliti_e_controllati():
    assert fb.pulisci_problemi([{"categoria": "ateco", "campo": " codici_ateco ", "testo": "  manca 10.41 "}]) == [
        {"categoria": "ateco", "campo": "codici_ateco", "testo": "manca 10.41"}]
    with pytest.raises(fb.ErroreFeedback):
        fb.pulisci_problemi([{"categoria": "boh"}])
    with pytest.raises(fb.ErroreFeedback):
        fb.pulisci_problemi([{"categoria": "altro", "testo": " "}])


@pytest.fixture
def ambiente(monkeypatch):
    from fastapi.testclient import TestClient

    from app.db.connessione import connetti
    from app.db.migrazioni import applica_migrazioni
    from app.main import app

    with connetti() as conn:
        applica_migrazioni(conn)
        with conn.cursor() as cur:
            scheda = {"titolo": "Bando feedback di prova", "completezza": "bando_ufficiale", "scadenza": "2026-12-31",
                      "codici_ateco": ["62.01"]}
            cur.execute("""INSERT INTO bandi (titolo, url, scadenza, codici_ateco, completezza, dati, stato_ricontrollato_il)
                           VALUES ('Bando feedback di prova', 'https://esempio.it/b', '2026-12-31', '{62.01}', 'bando_ufficiale',
                                   %s, now()) RETURNING id""", (json.dumps({"risposta": scheda}),))
            bando_id = cur.fetchone()["id"]
            cur.execute("INSERT INTO bandi (titolo) VALUES ('Senza scheda') RETURNING id")
            senza = cur.fetchone()["id"]
        conn.commit()
    return TestClient(app), bando_id, senza


@db
def test_voto_e_problemi_dal_revisore(ambiente):
    from conftest import accesso_di_prova

    from app.db.connessione import connetti

    c, bando_id, senza = ambiente
    rev = accesso_di_prova("revisore")
    assert c.get(f"/api/bandi/{bando_id}/feedback", auth=rev).json()["mio"] is None
    corpo = {"voto": 2, "problemi": [{"categoria": "stato_sbagliato", "campo": "stato", "testo": "la pagina dice chiuso"}]}
    r = c.put(f"/api/bandi/{bando_id}/feedback", json=corpo, auth=rev)
    assert r.status_code == 200 and r.json()["stato"] == "nuovo" and r.json()["ruolo"] == "revisore"
    # "stato sbagliato" fa ricontrollare la pagina ufficiale al prossimo giro.
    with connetti() as conn, conn.cursor() as cur:
        cur.execute("SELECT stato_ricontrollato_il FROM bandi WHERE id = %s", (bando_id,))
        assert cur.fetchone()["stato_ricontrollato_il"] is None
    # Lo stesso utente sulla stessa versione cambia il suo giudizio, non ne aggiunge un altro.
    assert c.put(f"/api/bandi/{bando_id}/feedback", json={"voto": 4}, auth=rev).status_code == 200
    mio = c.get(f"/api/bandi/{bando_id}/feedback", auth=rev).json()
    assert mio["mio"]["voto"] == 4 and mio["tutti"] == []          # il revisore non vede i giudizi degli altri
    assert c.put(f"/api/bandi/{bando_id}/feedback", json={"voto": 9}, auth=rev).status_code == 422
    assert c.put(f"/api/bandi/{bando_id}/feedback", json={}, auth=rev).status_code == 422
    assert c.put(f"/api/bandi/{senza}/feedback", json={"voto": 3}, auth=rev).status_code == 422
    miei = c.get("/api/feedback", auth=rev).json()
    assert miei["totale"] == 1 and miei["feedback"][0]["bando_id"] == bando_id
    assert c.patch(f"/api/feedback/{mio['mio']['id']}", json={"stato": "respinto"}, auth=rev).status_code == 403
    imp = accesso_di_prova("impresa")
    assert c.put(f"/api/bandi/{bando_id}/feedback", json={"voto": 3}, auth=imp).status_code == 403


@db
def test_pagina_feedback_admin_e_correzione(ambiente):
    from conftest import accesso_di_prova

    from app.db.connessione import connetti

    c, bando_id, _ = ambiente
    rev = accesso_di_prova("revisore")
    c.put(f"/api/bandi/{bando_id}/feedback", auth=rev,
          json={"voto": 2, "problemi": [{"categoria": "scadenza", "campo": "scadenza", "testo": "e' il 30/11"}]})
    admin = accesso_di_prova("admin")
    elenco = c.get(f"/api/feedback?stato=nuovo&categoria=scadenza&bando={bando_id}", auth=admin).json()
    assert elenco["totale"] == 1 and elenco["feedback"][0]["peso"] == 2 and "email" in elenco["feedback"][0]
    fid = elenco["feedback"][0]["id"]
    assert len(c.get(f"/api/bandi/{bando_id}/feedback", auth=admin).json()["tutti"]) == 1

    with connetti() as conn:
        with pytest.raises(fb.ErroreFeedback):
            fb.applica_correzioni(conn, bando_id, [{"campo": "inventato", "valore": 1}], "prova")
        with pytest.raises(fb.ErroreFeedback):   # valore fuori elenco: non si salva niente
            fb.applica_correzioni(conn, bando_id, [{"campo": "dimensioni_ammesse", "valore": ["enorme"]}], "prova")
        conn.rollback()
        fb.applica_correzioni(conn, bando_id, [{"campo": "scadenza", "valore": "2026-11-30", "citazione": "entro il 30/11/2026"}],
                              f"feedback {fid}: scadenza corretta")
        conn.commit()
        with conn.cursor() as cur:
            cur.execute("SELECT scadenza::text AS s, versione, dati, stato FROM bandi WHERE id = %s", (bando_id,))
            b = cur.fetchone()
            assert b["s"] == "2026-11-30" and b["versione"] == 2
            assert b["dati"]["correzioni_feedback"][0]["citazione"] == "entro il 30/11/2026"
            assert b["stato"] == "aperto"
            cur.execute("SELECT causa FROM bandi_versioni WHERE bando_id = %s", (bando_id,))
            assert cur.fetchone()["causa"].startswith(f"feedback {fid}")

    r = c.patch(f"/api/feedback/{fid}", json={"stato": "corretto", "risposta": "Grazie, scadenza corretta."}, auth=admin)
    assert r.status_code == 200 and r.json()["gestito_da"].startswith("prova-admin")
    assert c.get(f"/api/bandi/{bando_id}/feedback", auth=rev).json()["mio"]["risposta"] == "Grazie, scadenza corretta."
