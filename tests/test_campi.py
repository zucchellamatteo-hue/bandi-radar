"""Campi della scheda per l'abbinamento: valori ammessi allineati tra codice, prompt e documentazione; stato dalle date."""

import os
from datetime import date
from pathlib import Path

import pytest

from app.schede import campi
from app.schede.campi import calcola_stato

RADICE = Path(__file__).resolve().parents[1]
PROMPT = (RADICE / "app" / "schede" / "prompt_scheda.md").read_text(encoding="utf-8")
SCHEDA = (RADICE / "docs" / "SCHEDA_BANDO.md").read_text(encoding="utf-8")
MIGRAZIONE = (RADICE / "app" / "db" / "migrazioni" / "007_campi_abbinamento.sql").read_text(encoding="utf-8")


@pytest.mark.parametrize("campo", sorted(campi.VALORI_AMMESSI))
def test_valori_ammessi_scritti_nel_prompt_e_nella_scheda(campo):
    for valore in campi.VALORI_AMMESSI[campo]:
        if campo == "territorio_regioni":
            assert valore in PROMPT, f"{valore} manca nel prompt"
            continue
        assert f'"{valore}"' in PROMPT or f"`{valore}`" in PROMPT, f"{campo}: {valore} manca nel prompt"
        assert f"`{valore}`" in SCHEDA, f"{campo}: {valore} manca in docs/SCHEDA_BANDO.md"


def test_ogni_campo_ha_la_sua_colonna_e_la_sua_chiave_nel_prompt():
    for campo in [*campi.VALORI_AMMESSI, *campi.NUMERICI, "vincoli", "linee", "gestore", "ora_scadenza", "chiuso_il"]:
        assert f'"{campo}"' in PROMPT, f"{campo} manca nel formato del prompt"
        if campo not in ("contributo_massimo", "percentuale", "dimensioni_ammesse"):     # colonne gia' nella migrazione 004
            assert f"COLUMN IF NOT EXISTS {campo} " in MIGRAZIONE, f"{campo} manca nella migrazione 007"
    for vincolo in campi.VINCOLI:
        assert f'"{vincolo}"' in PROMPT and f"`{vincolo}`" in SCHEDA


def test_stato_calcolato_dalle_date():
    oggi = date(2026, 9, 25)
    assert calcola_stato(date(2026, 7, 30), None, oggi) == "aperto"                    # sportello senza scadenza
    assert calcola_stato(date(2026, 10, 1), date(2026, 11, 30), oggi) == "in_arrivo"
    assert calcola_stato(date(2026, 9, 1), date(2026, 9, 24), oggi) == "chiuso"
    assert calcola_stato(None, date(2026, 9, 25), oggi) == "aperto"                    # l'ultimo giorno e' ancora aperto
    assert calcola_stato(date(2026, 7, 30), None, oggi, chiuso_il=date(2026, 9, 10)) == "chiuso"   # fondi esauriti
    assert calcola_stato(None, None, oggi) is None


@pytest.mark.skipif(not os.environ.get("PGHOST"), reason="serve un database Postgres di prova (PGHOST)")
def test_stato_aggiornato_nel_database_con_storico():
    from app.db.connessione import connetti
    from app.db.migrazioni import applica_migrazioni
    from app.schede.stato import aggiorna_stati

    with connetti() as conn:
        applica_migrazioni(conn)
        with conn.cursor() as cur:
            cur.execute("INSERT INTO bandi (titolo, data_apertura, scadenza) VALUES ('prova stato', '2026-09-01', '2026-09-30') RETURNING id")
            bando = cur.fetchone()["id"]
        conn.commit()
        try:
            aggiorna_stati(conn, date(2026, 9, 25))
            aggiorna_stati(conn, date(2026, 10, 1))
            assert aggiorna_stati(conn, date(2026, 10, 2)) == 0   # nessun cambio: nessuna versione nuova
            with conn.cursor() as cur:
                cur.execute("SELECT stato, versione FROM bandi WHERE id = %s", (bando,))
                riga = cur.fetchone()
                assert riga["stato"] == "chiuso" and riga["versione"] == 3
                cur.execute("SELECT causa FROM bandi_versioni WHERE bando_id = %s ORDER BY versione", (bando,))
                assert [r["causa"] for r in cur.fetchall()] == ["stato ricalcolato il 2026-09-25", "stato ricalcolato il 2026-10-01"]
        finally:
            with conn.cursor() as cur:
                cur.execute("DELETE FROM bandi WHERE id = %s", (bando,))
            conn.commit()
