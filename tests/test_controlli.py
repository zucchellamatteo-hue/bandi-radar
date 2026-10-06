"""Controllo delle schede senza IA (app/schede/controlli.py) e link Liferay tra i documenti."""

import json
import os
from datetime import date

import pytest

from app.abbinamento.catalogo import proponibile
from app.schede import controlli
from app.schede.allegati import trova_allegati


def test_link_liferay_senza_estensione_e_un_documento():
    html = ('<a href="https://www.azero.veneto.it/documents/20126/c112466b-43ce-0527-4076-580846c52611">Scarica il bando</a>'
            '<a href="https://www.azero.veneto.it/documents/altro">Altro</a>')
    [c] = trova_allegati(html, "https://www.tb.camcom.gov.it/CCIAA_bandi.asp?cod=2754")
    assert c.url.endswith("580846c52611") and c.tipo == "file" and c.nome == "Scarica il bando"


def test_problemi_gravi_e_da_migliorare():
    b = {"id": 1, "titolo": "Voucher digitali", "completezza": "bando_ufficiale", "data_apertura": date(2026, 11, 1),
         "scadenza": date(2026, 10, 1), "contributo_massimo": 50000, "dotazione": 20000, "percentuale": 150,
         "dati": {"risposta": {"sintesi": "Il bando si svolge in due fasi.", "linee": []}}}
    gravi, migliorare = controlli.problemi(b, [{"id": 2, "titolo": "voucher digitali"}], ["altro"])
    assert len(gravi) == 5          # senza testo del bando, doppione, date, contributo, percentuale
    assert any("condivisa" in m for m in migliorare) and any("fasi" in m for m in migliorare)
    assert any("fornitori" in m for m in migliorare)


def test_scheda_pulita_e_proponibile_solo_senza_gravi():
    b = {"id": 1, "titolo": "Bando", "completezza": "bando_ufficiale",
         "vincoli_spese": {"fornitore": {"stato": "nessun_vincolo"}}, "dati": {"risposta": {"sintesi": "Contributi."}}}
    assert controlli.problemi(b, [], ["bando"]) == ([], [])
    assert proponibile({**b, "controllo": {"gravi": [], "da_migliorare": ["x"]}})
    assert not proponibile({**b, "controllo": {"gravi": ["x"], "da_migliorare": []}})


@pytest.mark.skipif(not os.environ.get("PGHOST"), reason="serve il database di prova")
def test_controlla_scrive_e_non_cambia_la_versione():
    from app.db.connessione import connetti
    from app.db.migrazioni import applica_migrazioni

    with connetti() as conn:
        applica_migrazioni(conn)
        with conn.cursor() as cur:
            cur.execute("INSERT INTO bandi (titolo, completezza, dati) VALUES ('prova controlli', 'bando_ufficiale', %s) "
                        "RETURNING id, versione", (json.dumps({"risposta": {"sintesi": "x"}}),))
            riga = cur.fetchone()
        conn.commit()
        try:
            assert controlli.controlla(conn, bando_id=riga["id"])["con_gravi"] == 1
            with conn.cursor() as cur:
                cur.execute("SELECT versione, controllo FROM bandi WHERE id = %s", (riga["id"],))
                dopo = cur.fetchone()
            assert dopo["versione"] == riga["versione"] and dopo["controllo"]["gravi"]
            assert riga["id"] in [r["id"] for r in controlli.da_rivedere(conn)]
        finally:
            with conn.cursor() as cur:
                cur.execute("DELETE FROM bandi WHERE id = %s", (riga["id"],))
            conn.commit()
