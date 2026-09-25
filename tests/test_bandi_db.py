"""Bandi e annunci nel database: migrazione, deduplica salvata, scelte di Matteo, versioni, API della plancia.

Girano solo con un database Postgres di prova VUOTO (PGHOST impostata): creano e cancellano le proprie righe.
"""

import os

import pytest

pytestmark = pytest.mark.skipif(not os.environ.get("PGHOST"), reason="serve un database Postgres di prova (PGHOST)")


@pytest.fixture()
def conn():
    from app.db.connessione import connetti
    from app.db.migrazioni import applica_migrazioni

    with connetti() as c:
        applica_migrazioni(c)
        with c.cursor() as cur:
            cur.execute("DELETE FROM bandi_dubbi; UPDATE annunci SET bando_id = NULL; DELETE FROM allegati; DELETE FROM bandi;"
                        "DELETE FROM smistamenti; DELETE FROM annunci WHERE fonte_id LIKE 'prova_%'; DELETE FROM fonti WHERE id LIKE 'prova_%'")
            cur.execute("""INSERT INTO fonti (id, nome, ente, tipo, territorio, modalita, frequenza, stato) VALUES
                ('prova_camera', 'Camera', 'Camera di Commercio di Modena', 'camera', 'EMR', 'html', 'settimanale', 'attiva'),
                ('prova_catalogo', 'Catalogo', 'MIMIT (incentivi.gov.it)', 'nazionale', 'ITA', 'api', 'giornaliera', 'attiva')""")
            righe = [
                (1, "prova_camera", "https://mo.camcom.it/bandi/giovani-2026", "Bando occupazione giovanile 2026", None),
                (2, "prova_catalogo", "https://incentivi.gov.it/catalogo/8821", "CCIAA Modena - Bando occupazione giovanile - anno 2026",
                 '{"gestore": "CCIAA Modena", "regioni": ["Emilia-Romagna"], "link_ente": "https://www.mo.camcom.it/bandi/giovani-2026/"}'),
                (3, "prova_camera", "https://mo.camcom.it/bandi/giovani-2026-graduatoria", "Bando occupazione giovanile 2026: graduatoria", None),
                (4, "prova_camera", "https://mo.camcom.it/bandi/export-2026", "Bando voucher export per le PMI del territorio 2026", None),
                (5, "prova_catalogo", "https://incentivi.gov.it/catalogo/9000", "Voucher export PMI territorio modenese 2026", None),
            ]
            for n, fonte, url, titolo, dati in righe:
                cur.execute("""INSERT INTO annunci (id, fonte_id, url, titolo, impronta, dati, trovato_il)
                               VALUES (%s, %s, %s, %s, 'x', %s, now() + %s * interval '1 second')""",
                            (900000 + n, fonte, url, titolo, dati, n))
                cur.execute("INSERT INTO smistamenti (annuncio_id, esito, deciso_da) VALUES (%s, 'rilevante', 'regole')", (900000 + n,))
            cur.execute("""INSERT INTO allegati (annuncio_id, url, nome, tipo) VALUES (900002, 'https://x.it/b.pdf', 'Bando', 'pdf')""")
        c.commit()
        yield c
        with c.cursor() as cur:
            cur.execute("DELETE FROM bandi_dubbi; UPDATE annunci SET bando_id = NULL; DELETE FROM allegati; DELETE FROM bandi;"
                        "DELETE FROM smistamenti; DELETE FROM annunci WHERE fonte_id LIKE 'prova_%'; DELETE FROM fonti WHERE id LIKE 'prova_%'")
        c.commit()


def _bando_di(conn, annuncio):
    with conn.cursor() as cur:
        cur.execute("SELECT bando_id, ruolo, collegato_da FROM annunci WHERE id = %s", (900000 + annuncio,))
        return cur.fetchone()


def test_deduplica_salvata_e_ripetibile(conn):
    from app.schede.bandi import carica, pianifica, salva_piano

    annunci, esistenti, in_dubbio = carica(conn)
    conteggi = salva_piano(conn, pianifica(annunci, esistenti, in_dubbio, anno_corrente=2026))
    assert conteggi["nuovo"] == 2 and conteggi["collega"] == 2 and conteggi["dubbio"] == 1
    b1 = _bando_di(conn, 1)
    assert _bando_di(conn, 2)["bando_id"] == b1["bando_id"] and _bando_di(conn, 2)["ruolo"] == "doppione"
    assert _bando_di(conn, 3)["ruolo"] == "graduatoria"
    assert _bando_di(conn, 5)["bando_id"] is None          # dubbio: resta senza bando finche' si decide
    with conn.cursor() as cur:
        cur.execute("SELECT bando_id FROM allegati WHERE annuncio_id = 900002")
        assert cur.fetchone()["bando_id"] == b1["bando_id"]   # l'allegato passa al bando
    # un secondo giro non cambia nulla
    annunci, esistenti, in_dubbio = carica(conn)
    assert pianifica(annunci, esistenti, in_dubbio, anno_corrente=2026) == []


def test_scelte_di_matteo_e_versioni(conn):
    from app.schede.bandi import carica, decisione_matteo, pianifica, salva_piano

    annunci, esistenti, in_dubbio = carica(conn)
    salva_piano(conn, pianifica(annunci, esistenti, in_dubbio, anno_corrente=2026))
    export = _bando_di(conn, 4)["bando_id"]
    # Matteo decide il dubbio: stesso bando
    assert decisione_matteo(conn, 900005, export) == export
    assert _bando_di(conn, 5) == {"bando_id": export, "ruolo": "doppione", "collegato_da": "matteo"}
    with conn.cursor() as cur:
        cur.execute("SELECT decisione, deciso_da FROM bandi_dubbi WHERE annuncio_id = 900005")
        assert cur.fetchone() == {"decisione": "stesso", "deciso_da": "matteo"}
    # poi lo separa: nuovo bando, e la deduplica automatica non lo riattacca
    nuovo = decisione_matteo(conn, 900005, None)
    assert nuovo != export
    annunci, esistenti, in_dubbio = carica(conn)
    assert pianifica(annunci, esistenti, in_dubbio, anno_corrente=2026) == []
    # ogni modifica della scheda conserva la versione precedente, con la causa
    with conn.cursor() as cur:
        cur.execute("SELECT set_config('bandi_radar.causa', 'annuncio 3, proroga', true)")
        cur.execute("UPDATE bandi SET scadenza = '2026-12-31' WHERE id = %s", (export,))
        cur.execute("UPDATE bandi SET qualita = 4 WHERE id = %s", (export,))   # il voto non e' una versione
        cur.execute("SELECT versione FROM bandi WHERE id = %s", (export,))
        assert cur.fetchone()["versione"] == 2
        cur.execute("SELECT versione, causa, dati->>'scadenza' AS scadenza FROM bandi_versioni WHERE bando_id = %s", (export,))
        assert cur.fetchall() == [{"versione": 1, "causa": "annuncio 3, proroga", "scadenza": None}]
    conn.commit()


def test_api_plancia_bandi_e_dubbi(conn):
    from fastapi.testclient import TestClient

    os.environ.setdefault("BASIC_AUTH_USER", "prova")
    os.environ.setdefault("BASIC_AUTH_PASSWORD", "prova")
    from app.main import app
    from app.schede.bandi import carica, pianifica, salva_piano

    annunci, esistenti, in_dubbio = carica(conn)
    salva_piano(conn, pianifica(annunci, esistenti, in_dubbio, anno_corrente=2026))
    c = TestClient(app)
    auth = (os.environ["BASIC_AUTH_USER"], os.environ["BASIC_AUTH_PASSWORD"])

    dettaglio = c.get("/api/annunci/900001", auth=auth).json()
    assert dettaglio["bando"]["titolo"] == "Bando occupazione giovanile 2026"
    assert {a["id"] for a in dettaglio["stesso_bando"]} == {900002, 900003}

    dubbi = c.get("/api/dubbi", auth=auth).json()
    assert dubbi["totale"] == 1 and dubbi["dubbi"][0]["annuncio_id"] == 900005
    r = c.post(f"/api/dubbi/{dubbi['dubbi'][0]['id']}", json={"decisione": "diverso"}, auth=auth)
    assert r.status_code == 200 and c.get("/api/dubbi", auth=auth).json()["totale"] == 0

    # unire a mano l'annuncio 5 al bando dell'annuncio 4
    r = c.post("/api/annunci/900005/bando", json={"azione": "unisci", "con_annuncio": 900004}, auth=auth)
    assert r.status_code == 200 and r.json()["bando_id"] == _bando_di(conn, 4)["bando_id"]
    bando = c.get(f"/api/bandi/{r.json()['bando_id']}", auth=auth).json()
    assert {a["id"] for a in bando["annunci"]} == {900004, 900005}
    assert c.post("/api/annunci/900005/bando", json={"azione": "unisci", "con_annuncio": 900005}, auth=auth).status_code == 400
    assert c.get("/api/bandi/1234567", auth=auth).status_code == 404
