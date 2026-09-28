"""Lettura della scorta (tutte le pagine di una fonte) e date di pubblicazione nel futuro."""

from dataclasses import replace
from datetime import date, datetime, timezone

import httpx
import pytest

from app.fonti.registro import ErroreRegistro, Fonte, carica_registro
from app.raccolta.esegui import data_di_pubblicazione
from app.raccolta.lettori.api import sedia_annuncio
from app.raccolta.modelli import Annuncio, Lettura
from app.raccolta.scorta import fonte_della_pagina, leggi_scorta, scaduto

FONTE = Fonte(id="prova", nome="Prova", ente="Ente", tipo="regione", territorio="LOM", url="https://esempio.it/bandi",
              modalita="html", frequenza="settimanale", stato="attiva")


def test_pagina_nel_parametro_dell_indirizzo():
    f = replace(FONTE, scorta={"parametro": "page", "inizio": 1, "pagine": 3})
    assert fonte_della_pagina(f, 2).url == "https://esempio.it/bandi?page=2"
    f = replace(FONTE, url="https://esempio.it/bandi?stato=2&page=1", scorta={"parametro": "page"})
    assert fonte_della_pagina(f, 3).url == "https://esempio.it/bandi?stato=2&page=3"


def test_pagina_nell_indirizzo_e_nel_corpo_della_post():
    f = replace(FONTE, modalita="api", feed_url="https://esempio.it/api?x=1",
                richiesta={"metodo": "POST", "corpo_json": {"state": {"current": 1, "resultsPerPage": 50}}},
                scorta={"url": "https://esempio.it/api?pagina={pagina}", "pagine": 5,
                        "corpo_json": {"state": {"current": "{pagina}", "resultsPerPage": 50}}})
    p = fonte_della_pagina(f, 4)
    assert p.feed_url == "https://esempio.it/api?pagina=4" and p.url == FONTE.url
    assert p.richiesta["corpo_json"] == {"state": {"current": 4, "resultsPerPage": 50}}
    assert f.richiesta["corpo_json"]["state"]["current"] == 1   # l'originale non cambia


def _lettore(pagine: dict):
    chiamate = []

    def leggi(fonte, client):
        chiamate.append(fonte.url)
        esito = pagine[fonte.url]
        if isinstance(esito, int):
            raise httpx.HTTPStatusError("x", request=httpx.Request("GET", fonte.url),
                                        response=httpx.Response(esito, request=httpx.Request("GET", fonte.url)))
        return Lettura(annunci=[Annuncio(url=u, titolo=u, dati=d) for u, d in esito], codice_http=200, byte=10)
    return leggi, chiamate


def test_si_ferma_alla_pagina_senza_link_nuovi_e_scarta_i_bandi_scaduti():
    f = replace(FONTE, scorta={"parametro": "p", "pagine": 10, "scadenza": "scade"})
    leggi, chiamate = _lettore({
        "https://esempio.it/bandi?p=1": [("a", {"scade": "2026-12-31"}), ("b", {})],
        "https://esempio.it/bandi?p=2": [("c", {"scade": "2026-01-10"}), ("a", {})],
        "https://esempio.it/bandi?p=3": [("a", {}), ("b", {})],   # ripete la prima: fine
    })
    lettura = leggi_scorta(f, None, leggi, pausa=0, oggi=date(2026, 9, 27))
    assert [a.url for a in lettura.annunci] == ["a", "b"]
    assert len(chiamate) == 3
    assert "3 pagine" in lettura.messaggio and "1 scaduti" in lettura.messaggio


def test_senza_scadenza_si_tengono_solo_i_recenti():
    f = replace(FONTE, scorta={"scadenza": "scade", "senza_scadenza_mesi": 12})
    vecchio, recente = datetime(2024, 1, 1, tzinfo=timezone.utc), datetime(2026, 5, 1, tzinfo=timezone.utc)

    def leggi(fonte, client):
        return Lettura(annunci=[Annuncio(url="vecchio", titolo="v", pubblicato_il=vecchio),
                                Annuncio(url="recente", titolo="r", pubblicato_il=recente),
                                Annuncio(url="vecchio_aperto", titolo="a", pubblicato_il=vecchio, dati={"scade": "2027-01-01"})])
    lettura = leggi_scorta(f, None, leggi, pausa=0, oggi=date(2026, 9, 27))
    assert [a.url for a in lettura.annunci] == ["recente", "vecchio_aperto"]


def test_errore_dopo_la_prima_pagina_tiene_quello_che_ha_letto():
    f = replace(FONTE, scorta={"parametro": "p", "pagine": 10})
    leggi, _ = _lettore({"https://esempio.it/bandi?p=1": [("a", {})], "https://esempio.it/bandi?p=2": 404})
    lettura = leggi_scorta(f, None, leggi, pausa=0)
    assert [a.url for a in lettura.annunci] == ["a"] and "HTTP 404" in lettura.messaggio
    leggi, _ = _lettore({"https://esempio.it/bandi?p=1": 503})
    with pytest.raises(httpx.HTTPStatusError):
        leggi_scorta(f, None, leggi, pausa=0)


def test_scadenza_nei_dati_grezzi():
    oggi = date(2026, 9, 27)
    assert scaduto({"s": "2026-09-26T00:00:00"}, "s", oggi)
    assert not scaduto({"s": "2026-09-27"}, "s", oggi)
    assert not scaduto({"s": None}, "s", oggi) and not scaduto(None, "s", oggi)
    assert not scaduto({"a": {"b": "31/12/2026"}}, "a.b", oggi)
    assert scaduto({"s": ["2025-01-01", "2026-01-01"]}, "s", oggi)


def test_registro_controlla_il_blocco_scorta(tmp_path):
    voce = """
- id: prova_ok
  nome: Prova
  ente: Ente
  tipo: regione
  territorio: LOM
  url: https://esempio.it/bandi
  modalita: html
  frequenza: settimanale
  stato: attiva
  scorta: {SCORTA}
"""
    (tmp_path / "a.yaml").write_text(voce.replace("{SCORTA}", "{parametro: page, pagine: 5, frequenza: mensile}"))
    assert carica_registro(tmp_path)[0].scorta["pagine"] == 5
    for errata, frammento in [("{pagine: 5}", "vuole parametro"), ("{pagine: zero, parametro: p}", "numero intero"),
                              ("{frequenza: annuale}", "non ammessa"), ("{colore: blu}", "ammette solo")]:
        (tmp_path / "a.yaml").write_text(voce.replace("{SCORTA}", errata))
        with pytest.raises(ErroreRegistro, match=frammento):
            carica_registro(tmp_path)


def test_data_di_pubblicazione_nel_futuro_diventa_data_futura():
    adesso = datetime(2026, 9, 27, tzinfo=timezone.utc)
    a = Annuncio(url="u", titolo="t", pubblicato_il=datetime(2026, 10, 30, tzinfo=timezone.utc))
    assert data_di_pubblicazione(a, adesso) is None and a.dati == {"data_futura": "2026-10-30"}
    b = Annuncio(url="u", titolo="t", pubblicato_il=datetime(2026, 9, 27, 20, tzinfo=timezone.utc))
    assert data_di_pubblicazione(b, adesso) == b.pubblicato_il and b.dati == {}


def test_portale_ue_sovvenzione_a_cascata_ha_titolo_e_pagina_propri():
    r = {"metadata": {"type": ["8"], "identifier": ["DIGITAL-ECCC-2024-DEPLOY-NCC-06"], "title": ["Topic madre"],
                      "caName": ["Enhancing Cybersecurity of SMEs (SSNS-2026)"], "projectName": ["NCC Hungary"],
                      "url": ["https://ec.europa.eu/.../competitive-calls-cs/46786367"],
                      "deadlineDate": ["2026-11-28T22:59:00.000+0000"], "description": ["<p>Micro, small and medium</p>"]}}
    a = sedia_annuncio(r)
    assert a.titolo == "Enhancing Cybersecurity of SMEs (SSNS-2026)"
    assert a.url.endswith("competitive-calls-cs/46786367")
    assert a.dati["scadenza"] == "2026-11-28" and "NCC Hungary" in a.riassunto
    t = sedia_annuncio({"metadata": {"type": ["1"], "identifier": ["HORIZON-X-01"], "title": ["Un topic"], "callTitle": ["Call"],
                                     "deadlineDate": ["2026-03-04T00:00:00.000+0000", "2027-01-01T00:00:00.000+0000"]}})
    assert t.url.endswith("/topic-details/horizon-x-01") and t.titolo == "Un topic"
    assert t.dati["scadenza"] == "2027-01-01"   # piu' scadenze: vale l'ultima


def test_osservatore_con_selettore_tiene_i_titoli_corti_e_scarta_il_link_alla_pagina_in_http():
    from app.raccolta.lettori.html import estrai_link

    html = """<main><div class="card"><a href="/incentivi/legge-181">Legge 181</a></div>
              <div class="card"><a href="http://esempio.it/incentivi">Stato incentivo o strumento 0 Selected items</a></div>
              <p><a href="/altro">Corto</a></p></main>"""
    annunci = estrai_link(html, "https://esempio.it/incentivi", "div.card")
    assert [a.titolo for a in annunci] == ["Legge 181"]
    assert estrai_link(html, "https://esempio.it/incentivi") == []   # senza selettore i titoli corti restano fuori
