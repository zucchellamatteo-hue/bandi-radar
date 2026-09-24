"""Riepilogo settimanale: composizione del messaggio su dati finti, senza database."""

from datetime import datetime, timezone

from app.notifiche.novita_settimana import componi


def test_componi_riepilogo():
    da, a = datetime(2026, 9, 17, tzinfo=timezone.utc), datetime(2026, 9, 24, tzinfo=timezone.utc)
    dati = {
        "annunci": [
            {"fonte_id": "x", "fonte": "F", "ente": "Regione Lombardia", "tipo": "regione", "territorio": "LOM",
             "titolo": "Bando <test>", "url": "https://x.it/1", "pubblicato_il": da, "trovato_il": a},
            {"fonte_id": "y", "fonte": "G", "ente": "CCIAA Milano", "tipo": "camera", "territorio": "LOM",
             "titolo": "Voucher", "url": "https://x.it/2", "pubblicato_il": None, "trovato_il": a},
        ],
        "esiti": {"ok": 200, "errore": 3},
        "problemi": [{"id": "z", "nome": "Fonte rotta", "esito": "errore", "messaggio": "HTTP 500"}],
        "fonti_attive": 250,
    }
    oggetto, testo, corpo_html = componi(dati, da, a)
    assert oggetto == "Bandi Radar: 2 novità nella settimana 17/09–24/09/2026"
    assert "== Regioni (1)" in testo and "== Camere di Commercio (1)" in testo
    assert "[Regione Lombardia] 17/09 Bando <test>" in testo
    assert "Fonte rotta: errore (HTTP 500)" in testo
    assert "Bando &lt;test&gt;" in corpo_html and "250" in testo
