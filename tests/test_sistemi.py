"""Supervisione: registro delle esecuzioni e dati di ogni sistema (con un Postgres di prova)."""

import os

import pytest

from app import sistemi

pytestmark = pytest.mark.skipif(not os.environ.get("PGHOST"), reason="serve un database Postgres di prova (PGHOST)")


@pytest.fixture()
def conn():
    from app.db.connessione import connetti
    from app.db.migrazioni import applica_migrazioni

    with connetti() as c:
        applica_migrazioni(c)
        yield c
        with c.cursor() as cur:
            cur.execute("DELETE FROM esecuzioni WHERE sistema LIKE 'prova%' OR sistema IN ('raccolta', 'regista')")
        c.commit()


def test_esecuzione_ok_ed_errore(conn):
    with sistemi.esecuzione("prova_ok") as e:
        e.riepilogo = "3 fonti controllate"
    with pytest.raises(ValueError):
        with sistemi.esecuzione("prova_errore"):
            raise ValueError("sito irraggiungibile")
    with conn.cursor() as cur:
        cur.execute("SELECT sistema, esito, riepilogo, errore, finito_il FROM esecuzioni WHERE sistema LIKE 'prova%' ORDER BY id")
        righe = cur.fetchall()
    assert [(r["sistema"], r["esito"]) for r in righe] == [("prova_ok", "ok"), ("prova_errore", "errore")]
    assert righe[0]["riepilogo"] == "3 fonti controllate" and "sito irraggiungibile" in righe[1]["errore"]
    assert all(r["finito_il"] for r in righe)


def test_elenco_e_dati_di_ogni_sistema(conn):
    with sistemi.esecuzione("raccolta") as e:
        e.riepilogo = "prova"
    elenco = {s["id"]: s for s in sistemi.elenco(conn)}     # esegue tutte le query dei numeri
    assert set(elenco) == {s.id for s in sistemi.SISTEMI}
    assert elenco["raccolta"]["stato"] == "ok" and elenco["raccolta"]["prossima"] is not None
    assert elenco["regista"]["stato"] in ("mai partito", "ok", "in corso")
    assert elenco["backup"]["stato"] == "esterno"
    for s in sistemi.SISTEMI:                                 # esegue tutte le query dei dati
        d = sistemi.dettaglio(conn, s.id)
        assert d["nome"] == s.nome
        if s.dati:
            assert d["dati"]["colonne"]
    assert sistemi.dettaglio(conn, "inesistente") is None


def test_esecuzione_rimasta_in_corso_risulta_interrotta(conn):
    with conn.cursor() as cur:
        cur.execute("INSERT INTO esecuzioni (sistema, iniziato_il) VALUES ('regista', now() - interval '5 hours')")
    conn.commit()
    assert {s["id"]: s for s in sistemi.elenco(conn)}["regista"]["stato"] == "interrotto"
