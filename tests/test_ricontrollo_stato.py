"""Ricontrollo settimanale dello stato (piano del 03/10): frasi di chiusura solo nelle righe nuove della pagina, e sul
database la scheda che diventa "da aggiornare" con la pagina di oggi salvata."""

import os

import pytest

from app.schede import ricontrollo_stato as rs

PRIMA = """Bando voucher digitali 2026
Le domande si presentano dal 01/03/2026 fino a esaurimento delle risorse, salvo chiusura anticipata.
Lo sportello potra' essere sospeso se la dotazione risulti esaurita."""


def test_formule_dei_bandi_aperti_non_sono_chiusure():
    assert rs.frasi_di_chiusura(None, PRIMA) == []
    assert rs.frasi_di_chiusura(PRIMA, PRIMA) == []


def test_avviso_di_chiusura_nelle_righe_nuove():
    oggi = PRIMA + "\nATTENZIONE: la dotazione finanziaria del bando è esaurita. Non è più possibile presentare domanda."
    frasi = rs.frasi_di_chiusura(PRIMA, oggi)
    assert frasi and "esaurita" in frasi[0]
    assert rs.righe_nuove(PRIMA, oggi).startswith("ATTENZIONE")


@pytest.mark.parametrize("riga", ["La piattaforma è chiusa dal 13/03/2026.", "Bando Chiuso Inizio 20-07-2026",
                                  "Stato Atto: SCADUTO", "Opportunità scaduta",
                                  "Con determinazione n. 109 si procede alla chiusura anticipata al 08/04/2026",
                                  "Lo sportello è temporaneamente sospeso dal 03/03/2026"])
def test_frasi_di_chiusura(riga):
    assert rs.frasi_di_chiusura(PRIMA, PRIMA + "\n" + riga)


@pytest.mark.skipif(not os.environ.get("PGHOST"), reason="serve un database Postgres di prova (PGHOST)")
def test_ricontrollo_sul_database():
    from app.db.connessione import connetti
    from app.db.migrazioni import applica_migrazioni

    with connetti() as conn:
        applica_migrazioni(conn)
        with conn.cursor() as cur:
            ids = []
            for titolo in ("Bando che chiude", "Bando che resta aperto", "Bando non per imprese"):
                cur.execute("""INSERT INTO bandi (titolo, url, dati, completezza, data_apertura, preliminare)
                               VALUES (%s, 'https://esempio.it/bando', '{}', 'bando_ufficiale', '2026-03-01',
                                       %s) RETURNING id""",
                            (titolo, '{"per_imprese": "no"}' if "non per" in titolo else '{"per_imprese": "si"}'))
                ids.append(cur.fetchone()["id"])
                cur.execute("""INSERT INTO allegati (bando_id, url, nome, tipo, testo_estratto)
                               VALUES (%s, %s, 'pagina', 'pagina', %s)""", (ids[-1], f"https://esempio.it/{ids[-1]}", PRIMA))
        conn.commit()
        try:
            scelti = [b for b in rs.da_ricontrollare(conn, limite=1000) if b["id"] in ids]
            assert {b["id"] for b in scelti} == set(ids[:2])        # il bando non per imprese non si ricontrolla
            pagine = {f"https://esempio.it/{ids[0]}": PRIMA + "\nLo sportello è chiuso per esaurimento dei fondi.",
                      f"https://esempio.it/{ids[1]}": PRIMA}
            conti = rs.ricontrolla(conn, scelti, scarica_testo=pagine.get)
            assert (conti["controllati"], conti["chiusure"]) == (2, 1)
            with conn.cursor() as cur:
                cur.execute("SELECT id, da_aggiornare, stato_ricontrollato_il FROM bandi WHERE id = ANY(%s) ORDER BY id", (ids,))
                righe = cur.fetchall()
                cur.execute("SELECT testo_estratto FROM allegati WHERE bando_id = %s", (ids[0],))
                pagina = cur.fetchone()["testo_estratto"]
            assert "chiuso" in righe[0]["da_aggiornare"] and righe[1]["da_aggiornare"] is None
            assert righe[0]["stato_ricontrollato_il"] and righe[1]["stato_ricontrollato_il"]
            assert "sportello è chiuso" in pagina                   # la nuova scheda legge la pagina di oggi
            assert not [b for b in rs.da_ricontrollare(conn, limite=1000) if b["id"] in ids]   # fino alla settimana dopo
        finally:
            with conn.cursor() as cur:
                cur.execute("DELETE FROM eventi_catena WHERE oggetto = 'bando' AND oggetto_id = ANY(%s)", (ids,))
                cur.execute("DELETE FROM allegati WHERE bando_id = ANY(%s)", (ids,))
                cur.execute("DELETE FROM bandi WHERE id = ANY(%s)", (ids,))
            conn.commit()
