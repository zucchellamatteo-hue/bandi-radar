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
    assert oggetto == "bandinQiaro: 2 novità nella settimana 17/09–24/09/2026"
    assert "== Regioni (1)" in testo and "== Camere di Commercio (1)" in testo
    assert "[Regione Lombardia] 17/09 Bando <test>" in testo
    assert "Fonte rotta: errore (HTTP 500)" in testo
    assert "Bando &lt;test&gt;" in corpo_html and "250" in testo


def test_email_automatiche_dicono_di_non_rispondere(monkeypatch):
    from app.notifiche import email

    monkeypatch.delenv("EMAIL_MITTENTE", raising=False)
    monkeypatch.setenv("SITO_URL", "https://esempio.it")
    monkeypatch.setenv("EMAIL_CONTATTO", "info@esempio.it")
    assert email.mittente() == "bandinQiaro <non-rispondere@esempio.it>"
    testo, html = email.con_avviso("Ciao", "<html><body><p>Ciao</p></body></html>")
    assert "non rispondere" in testo and "info@esempio.it" in testo
    assert "non rispondere" in html and html.endswith("</p></body></html>")
    inviate = []
    monkeypatch.setenv("RESEND_API_KEY", "re_prova")
    monkeypatch.setattr(email.httpx, "post", lambda url, json, headers, timeout: inviate.append(json) or
                        type("R", (), {"raise_for_status": lambda self: None})())
    assert email.invia("a@b.it", "Oggetto", "Testo") == "inviata"
    assert inviate[0]["from"] == "bandinQiaro <non-rispondere@esempio.it>" and "non rispondere" in inviate[0]["text"]
    # Anche le email scritte solo in testo partono con la versione HTML (08/10: inviti nello spam), e le risposte
    # vanno alla casella di contatto.
    assert inviate[0]["reply_to"] == "info@esempio.it"
    assert email.invia("a@b.it", "Invito", "Ciao <Luca>,\n\napri https://esempio.it/invito?c=abc&d=1\n") == "inviata"
    h = inviate[1]["html"]
    assert '<a href="https://esempio.it/invito?c=abc&amp;d=1">' in h and "Ciao &lt;Luca&gt;," in h and "non rispondere" in h
