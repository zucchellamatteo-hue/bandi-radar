"""Segnali di stato gratuiti (senza IA): casi veri della valutazione del 27/09."""

import os
from datetime import date

import pytest

from app.schede.segnali import Segnali, date_barrate, scadenza_nei_dati, segnali_dal_testo

OGGI = date(2026, 9, 28)


def test_etichette_in_testa_alla_pagina():
    emilia = ("Bando Innovazione Digitale 2026 PI26 € 2.000.000 di risorse disponibili | Domanda online dalle ore 10:00 "
              "del 20/07/2026 Bando Chiuso Condividi Facebook")
    assert segnali_dal_testo(emilia, OGGI).stato == "chiuso"
    calabria = "Voucher per la transizione digitale delle PMI Azione: 1_2_4 / Fondo: FESR Valutazione Data aggiornamento stato 16 Lug 2026"
    assert segnali_dal_testo(calabria, OGGI).stato == "chiuso"
    finpiemonte = "Scarica la sintesi della misura Chiuso Codice fondo 1184 - Anno 2026 - In vigore dal 28/07/2026 al 06/08/2026"
    s = segnali_dal_testo(finpiemonte, OGGI)
    assert s.stato == "chiuso" and "in vigore fino al 06/08/2026" in s.chiuso
    assert segnali_dal_testo("In vigore dal 10/09/2026 al 30/09/2027 Aperto", OGGI).stato == "aperto"
    assert segnali_dal_testo("Avviso: chiusura anticipata dello sportello per esaurimento della dotazione", OGGI).stato == "chiuso"


def test_fino_a_esaurimento_delle_risorse_non_vuol_dire_chiuso():
    on = "ON - Oltre Nuove imprese a tasso zero. Le domande si presentano fino a esaurimento delle risorse disponibili."
    assert segnali_dal_testo(on, OGGI).stato is None
    assert segnali_dal_testo("Le risorse sono esaurite: lo sportello e' chiuso dal 3 settembre.", OGGI).stato == "chiuso"


def test_scadenza_futura_nella_pagina_blocca_la_chiusura():
    s = segnali_dal_testo("Bando Chiuso per la prima finestra. Data di scadenza: 30/11/2026", OGGI)
    assert s.chiuso and s.aperto and s.stato is None     # segnali opposti: decide l'IA


def test_data_barrata_con_la_nuova_accanto():
    cosenza = "<table><tr><td>05 BANDO DOPPIA TRANSIZIONE</td><td><del>30/09/2026</del> 08/04/2026</td></tr></table>"
    assert date_barrate(cosenza, OGGI) == ["data barrata 30/09/2026, nuova data 08/04/2026 gia' passata"]
    prorogata = "<p>Scadenza: <s>30/06/2026</s> 31/12/2026</p>"
    assert date_barrate(prorogata, OGGI) == []


def test_scadenza_nei_dati_grezzi_della_fonte():
    assert scadenza_nei_dati({"scadenza": "2026-12-31T00:00:00"}) == date(2026, 12, 31)          # incentivi.gov.it
    assert scadenza_nei_dati({"scadenza_bando": "2026-11-13T23:00:00+00:00"}) == date(2026, 11, 13)   # Plone
    assert scadenza_nei_dati({"deadlineDate": ["2026-03-04", "2027-01-01"]}) == date(2027, 1, 1)      # Portale UE
    assert scadenza_nei_dati({"attributes": {"data_scadenza": "2025-05-05"}}) == date(2025, 5, 5)
    assert scadenza_nei_dati({"titolo": "x"}) is None and scadenza_nei_dati(None) is None


def test_stato_complessivo():
    assert Segnali(chiuso=["a"]).stato == "chiuso"
    assert Segnali(aperto=["b"]).stato == "aperto"
    assert Segnali(chiuso=["a"], aperto=["b"]).stato is None and Segnali().stato is None


@pytest.mark.skipif(not os.environ.get("PGHOST"), reason="serve un database Postgres di prova (PGHOST)")
def test_bando_con_scadenza_passata_nella_fonte_si_ferma_senza_ia(monkeypatch):
    from app.db.connessione import connetti
    from app.db.migrazioni import applica_migrazioni
    from app.schede import ia

    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    with connetti() as conn:
        applica_migrazioni(conn)
        with conn.cursor() as cur:
            cur.execute("INSERT INTO fonti (id, nome, ente, tipo, territorio, modalita, frequenza, stato) "
                        "VALUES ('prova_segnali', 'Prova', 'Ente', 'regione', 'LOM', 'api', 'settimanale', 'attiva') "
                        "ON CONFLICT (id) DO NOTHING")
            cur.execute("INSERT INTO bandi (titolo, url, pagina_stato, allegati_cercati_il) "
                        "VALUES ('prova segnali', 'https://esempio.it/b', 'trovata', now()) RETURNING id")
            bando = cur.fetchone()["id"]
            cur.execute("INSERT INTO annunci (fonte_id, url, titolo, impronta, dati, bando_id) VALUES "
                        "('prova_segnali', 'https://esempio.it/b', 'prova', 'x', '{\"scadenza\": \"2025-01-31\"}', %s)", (bando,))
        conn.commit()
        try:
            assert ia.cmd_schede(conn, bando, 1) == 0      # senza chiave: nessuna chiamata, ma il bando si ferma
            with conn.cursor() as cur:
                cur.execute("SELECT preliminare FROM bandi WHERE id = %s", (bando,))
                pre = cur.fetchone()["preliminare"]
            assert pre["stato"] == "chiuso" and pre["deciso_da"] == "segnali" and "31/01/2025" in pre["motivo"]
        finally:
            with conn.cursor() as cur:
                cur.execute("DELETE FROM annunci WHERE fonte_id = 'prova_segnali'")
                cur.execute("DELETE FROM bandi WHERE id = %s", (bando,))
                cur.execute("DELETE FROM fonti WHERE id = 'prova_segnali'")
            conn.commit()
