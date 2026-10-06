"""Segnali di stato gratuiti (senza IA): casi veri della valutazione del 27/09."""

import os
from datetime import date

import pytest

from app.schede.segnali import Segnali, date_barrate, scadenza_nei_dati, segnali_da_dati, segnali_dal_testo

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


# Revisione del 06/10 sui 502 bandi fermati dai segnali: frasi vere delle pagine che non vogliono dire "chiuso".
OGGI_REVISIONE = date(2026, 10, 6)


def test_chiusura_anticipata_solo_prevista_non_chiude():
    foggia = ("Presentazione delle domande dalle ore 09:00 del 29/09/2023 alle ore 21:00 del 30/10/2023. Si terrà conto "
              "dell’ordine cronologico di ricezione delle domande. Al raggiungimento di richieste di contributi superiori "
              "alla dotazione finanziaria sarà possibile la chiusura anticipata del bando.")
    assert segnali_dal_testo(foggia, OGGI_REVISIONE).chiuso == []
    foggia2 = ("Al raggiungimento di richieste di contributi superiori alla dotazione finanziaria sarà possibile procedere "
               "alla chiusura anticipata del bando.")
    assert segnali_dal_testo(foggia2, OGGI_REVISIONE).chiuso == []
    maremma = ("Bando a sostegno delle iniziative locali e di valorizzazione dei prodotti tipici - Anno 2026 | Camera di "
               "Commercio Maremma e Tirreno Salta al contenuto principale Aperto Scade 10/11/2026 salvo chiusura "
               "anticipata per esaurimento risorse ID 3722")
    s = segnali_dal_testo(maremma, OGGI_REVISIONE)
    assert s.stato == "aperto" and s.aperto == ["scadenza 10/11/2026 scritta nella pagina"]
    puglia = ("dovranno inviare la propria istanza entro e non oltre le ore 23.59 del giorno 20 dicembre 2026 (salvo "
              "chiusura anticipata per raggiungimento budget, opportunamente comunicato)")
    assert segnali_dal_testo(puglia, OGGI_REVISIONE).stato == "aperto"


def test_chiusure_anticipate_avvenute_restano():
    alto_adige = ("Con determinazione del Segretario Generale n. 134 del 24/09/2025 è stata disposta la chiusura anticipata "
                  "del bando alle ore 17:00 del 24/09/2025 per esaurimento delle risorse disponibili.")
    assert segnali_dal_testo(alto_adige, OGGI_REVISIONE).stato == "chiuso"
    sondrio = "Bando Nuova Impresa 2023 Avviso del 11 gennaio 2024 : chiusura anticipata dello sportello per esaurimento delle risorse disponibili."
    assert segnali_dal_testo(sondrio, OGGI_REVISIONE).stato == "chiuso"
    bergamo = "Bando Fiere 2026: chiusura anticipata dei termini 08/05/2026 - Il bando è stato chiuso anticipatamente per esaurimento del fondo disponibile ."
    assert segnali_dal_testo(bergamo, OGGI_REVISIONE).stato == "chiuso"


def test_voci_di_menu_e_frasi_su_altro_non_chiudono():
    simest = ("Operatività fino al 2021 - SIMEST Operatività fino al 2021 Non hai trovato quello che cercavi? Consulta qui "
              "ulteriori strumenti non più operativi Strumenti attualmente non disponibili Operatività finanziamenti "
              "agevolati per l’internalizzazione fino al 2021 Scopri di più")
    assert segnali_dal_testo(simest, OGGI_REVISIONE).chiuso == []
    finlombarda = ("dispongono di patrimonio netto positivo nell'ultimo bilancio approvato; nel caso in cui l’ultimo bilancio "
                   "non sia ancora stato chiuso si richiede la presentazione dell’ultimo bilancio approvato")
    assert segnali_dal_testo(finlombarda, OGGI_REVISIONE).chiuso == []
    sondrio = "AVVISO DEL 30 MAGGIO 2023: il bando è stato chiuso con Determinazione del D.O. n. 76/2003 per esaurimento delle risorse."
    assert segnali_dal_testo(sondrio, OGGI_REVISIONE).stato == "chiuso"


def test_stato_del_portale_calabria():
    # "Conclusione Data aggiornamento stato" e' l'etichetta dello stato della procedura, non testo di servizio.
    conclusione = "Grandi Eventi Avviso pubblico di selezione Fondo: PAC 2007/2013 Conclusione Data aggiornamento stato 11 Nov 2022 Obiettivo"
    assert segnali_dal_testo(conclusione, OGGI_REVISIONE).stato == "chiuso"
    aperto = "Azione: 1_2_4 / Fondo: FESR Aperto Data aggiornamento stato 16 Lug 2026 Obiettivo"
    assert segnali_dal_testo(aperto, OGGI_REVISIONE).stato == "aperto"
    sospeso = "Azione: Azione 6.8.3 / Fondo: PAC 2014/2020 Sospeso Data aggiornamento stato 9 Set 2026 Obiettivo"
    assert segnali_dal_testo(sospeso, OGGI_REVISIONE).chiuso == []
    # Bando 1225: la pagina e' dell'edizione 2023, ma tra gli annunci c'e' l'"Annualita' 2025" pubblicata il 13/05/2025.
    manifestazioni = ("Avviso Pubblico per la concessione di contributi per Manifestazioni Sportive Azione: Azione 6.8.3 / "
                      "Fondo: PAC Calabria 2014-2020 Conclusione Data aggiornamento stato 16 Ott 2023 Obiettivo")
    s = segnali_dal_testo(manifestazioni, OGGI_REVISIONE, ultima_pubblicazione=date(2025, 5, 13))
    assert s.chiuso == [] and s.stato == "aperto" and "13/05/2025" in s.aperto[0]
    assert segnali_dal_testo(manifestazioni, OGGI_REVISIONE, ultima_pubblicazione=date(2023, 1, 11)).stato == "chiuso"


def test_edizione_nuova_tra_gli_annunci():
    pagina = {"testo_estratto": "Fondo: PAC Calabria 2014-2020 Conclusione Data aggiornamento stato 16 Ott 2023 Obiettivo",
              "percorso_locale": None}
    annunci = [{"url": "https://calabriaeuropa.regione.calabria.it/bando/manifestazioni-sportive/", "dati": None,
                "pubblicato_il": "2023-01-11T00:00:00+00:00", "ruolo": "origine"},
               {"url": "https://www.regione.calabria.it/bandi/atto_numero_16451-graduatoria-definitiva/", "dati": None,
                "pubblicato_il": "2026-09-30T00:00:00+00:00", "ruolo": "graduatoria"}]
    # La graduatoria esce dopo la chiusura: non e' un'edizione nuova.
    assert segnali_da_dati("https://x.it/b", annunci, [pagina], OGGI_REVISIONE).stato == "chiuso"
    annunci.append({"url": "https://calabriaeuropa.regione.calabria.it/bando/manifestazioni-sportive-annualita-2025/",
                    "dati": None, "pubblicato_il": "2025-05-13T00:00:00+00:00", "ruolo": "doppione"})
    assert segnali_da_dati("https://x.it/b", annunci, [pagina], OGGI_REVISIONE).stato == "aperto"


def test_termini_futuri_scritti_in_altro_modo():
    lombardia = ("Aperto Ti porto io Codice: RLU12026053838 Pubblicato il: 24/06/2026 , ore 15:20 Domande dal: 30/06/2026 , "
                 "ore 10:00 Scade il: 15/10/2026 , ore 16:00 La misura è finalizzata")
    assert "scadenza 15/10/2026 scritta nella pagina" in segnali_dal_testo(lombardia, OGGI_REVISIONE).aperto
    gal = "Termine presentazione domande PROROGATO alle ore 13.00 del 12 ottobre 2026 Importo a Bando 710.624,00 €"
    assert segnali_dal_testo(gal, OGGI_REVISIONE).stato == "aperto"
    annualita = ("Presentazione delle domande di contributo: per l’annualità 2026, dal 3 agosto 2026 e fino al 15 settembre "
                 "2026; per l’annualità 2027, dal 2 agosto 2027 e fino al 15 settembre 2027.")
    assert segnali_dal_testo(annualita, OGGI_REVISIONE).stato == "aperto"
    bari = "Bando certificazione competenze anno 2026 a favore delle MPMI Domande dal 01/10/2026 al 16/12/2026 Finalità e obiettivi"
    assert segnali_dal_testo(bari, OGGI_REVISIONE).stato == "aperto"
    # I termini per altro (rendicontazione, eventi) non contano.
    emilia = ("Bando Certificazioni ESG 2025 - BC25 Pubblicata la graduatoria - Termine ultimo per la presentazione della "
              "rendicontazione ore 18:00 del 31/10/2026 Bando Chiuso Condividi")
    assert segnali_dal_testo(emilia, OGGI_REVISIONE).stato == "chiuso"
    spese = ("Bando Chiuso Le spese dovranno essere interamente sostenute (fatturate e pagate) a partire dal 01/05/2026 "
             "ed entro il 31/05/2027 Presentazione delle domande e rendicontazione")
    assert segnali_dal_testo(spese, OGGI_REVISIONE).stato == "chiuso"
    fiera = "Bando Scaduto. La manifestazione si svolgerà presso il porto turistico Marina di Brindisi dal 22 al 26 ottobre 2026."
    assert segnali_dal_testo(fiera, OGGI_REVISIONE).stato == "chiuso"


def test_data_barrata_conta_solo_quella_subito_dopo():
    bari = ('<p><strong>a partire <s>dalle ore 10:00 del 01/10/2026</s> e fino alle ore 12:00 del 16/12/2026. '
            '<span>AVVISO 01.01.2026 -- Si comunica che per problemi tecnici</span></strong></p>')
    assert date_barrate(bari, OGGI_REVISIONE) == []
    foggia = ("<p>Le imprese interessate a candidarsi all'iniziativa dovranno compilare, a partire dalle ore 9:00 del "
              "7/08/2026 e fino alle ore 12:00 del <s>4/09/2026</s> 18/09/2026, la manifestazione di interesse</p>")
    assert date_barrate(foggia, OGGI_REVISIONE) == ["data barrata 4/09/2026, nuova data 18/09/2026 gia' passata"]


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
