"""Protezioni del 02/10/2026 (analisi della struttura): blocchi, tetto con i lotti in volo, homepage degli enti."""

import os

import pytest

from app.schede.pagina_ufficiale import _PORTALE_ENTE


def test_homepage_dei_portali_degli_enti():
    for portale in ("www.bs.camcom.it", "www.comune.perugia.it", "www.regione.lombardia.it", "www.invitalia.it",
                    "www.ministeroturismo.gov.it", "comune.fossalto.cb.it"):
        assert _PORTALE_ENTE.search(portale), portale
    for dedicato in ("taxcreditlibrerie.cultura.gov.it", "www.mettersinproprio.it", "dottorati-imprese.mur.gov.it"):
        assert not _PORTALE_ENTE.search(dedicato), dedicato


db = pytest.mark.skipif(not os.environ.get("PGHOST"), reason="serve un database Postgres di prova (PGHOST)")


@db
def test_lo_stesso_passo_non_gira_due_volte_insieme():
    from app.db.blocchi import blocco, con_blocco

    chiamate = []

    @con_blocco("prova_passo", "occupato")
    def passo():
        chiamate.append(1)
        return "fatto"

    with blocco("prova_passo") as primo:
        assert primo
        with blocco("prova_passo") as secondo:      # un altro processo (altra connessione) lo trova preso
            assert not secondo
        assert passo() == "occupato" and not chiamate
    assert passo() == "fatto" and chiamate == [1]   # liberato all'uscita


@db
def test_il_tetto_conta_i_lotti_in_volo(monkeypatch):
    from app.db.connessione import connetti
    from app.db.migrazioni import applica_migrazioni
    from app.schede import ia

    monkeypatch.setenv("IA_TETTO_MESE_USD", "1")
    with connetti() as conn:
        applica_migrazioni(conn)
        with conn.cursor() as cur:
            cur.execute("""INSERT INTO chiamate_ia (scopo, modello, batch, batch_id, riferimento, esito)
                           SELECT 'scheda', 'claude-opus-5-5', true, 'prova-lotto', 'sch-prova-' || g, 'inviata'
                           FROM generate_series(1, 10) g""")
        conn.commit()
        try:
            assert ia.spesa_in_volo(conn) == pytest.approx(10 * ia.COSTO_STIMATO_IN_VOLO["scheda"])
            with pytest.raises(ia.IASpenta, match="stimati per i lotti in attesa"):
                ia.controlla_tetto(conn)
        finally:
            with conn.cursor() as cur:
                cur.execute("DELETE FROM chiamate_ia WHERE batch_id = 'prova-lotto'")
            conn.commit()
