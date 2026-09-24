"""Lettori della raccolta: feed, API e osservatore HTML, su dati di esempio senza rete."""

from datetime import datetime
from pathlib import Path

from app.raccolta.date import leggi_data
from app.raccolta.lettori.api import da_csv, generico, opencity, plone, wordpress
from app.raccolta.lettori.html import estrai_link
from app.raccolta.lettori.rss import analizza_feed

DATI = Path(__file__).parent / "dati"


def test_feed_rss2():
    annunci = analizza_feed((DATI / "feed_rss2.xml").read_bytes())
    assert [a.titolo for a in annunci] == ["Voucher digitalizzazione PMI 2026", "Bando fiere internazionali"]
    assert annunci[0].riassunto == "Contributo a fondo perduto per le micro e piccole imprese ."
    assert annunci[0].pubblicato_il.date().isoformat() == "2026-09-21"
    assert annunci[1].pubblicato_il.date().isoformat() == "2026-09-15"


def test_feed_atom_e_rdf():
    (atom,) = analizza_feed((DATI / "feed_atom.xml").read_bytes())
    assert atom.url == "https://esempio.it/avvisi/centro-storico" and atom.pubblicato_il.year == 2026
    (rdf,) = analizza_feed((DATI / "feed_rdf.xml").read_bytes())
    assert rdf.titolo == "Bando attivo uno" and rdf.pubblicato_il.date().isoformat() == "2026-09-10"


def test_api_plone_salta_cartelle():
    dati = {"items": [
        {"@id": "https://x.it/bandi/uno", "@type": "Bando", "title": "Bando uno", "description": "d", "effective": "2026-09-01T00:00:00+00:00"},
        {"@id": "https://x.it/bandi", "@type": "Folder", "title": "Cartella bandi"},
    ]}
    (a,) = plone(dati, "https://x.it/bandi")
    assert a.url == "https://x.it/bandi/uno" and a.pubblicato_il.month == 9


def test_api_wordpress_titoli_rendered():
    dati = [{"id": 5, "link": "https://x.it/b/5", "title": {"rendered": "Bando &amp; avviso"}, "date": "2026-09-02T10:00:00",
             "excerpt": {"rendered": "<p>testo</p>"}}]
    (a,) = wordpress(dati, "https://x.it")
    assert a.titolo == "Bando & avviso" and a.riassunto == "testo"


def test_api_generico_socrata_senza_link():
    dati = [{"codice_bando": "RL1", "titolo_bando": "Fondo giovani agricoltori", "apertura_adesione": "2026-10-13T00:00:00.000"}]
    (a,) = generico(dati, "https://dati.lombardia.it/x")
    assert a.url == "https://dati.lombardia.it/x#RL1" and a.pubblicato_il.day == 13


def test_api_opencity():
    dati = {"searchHits": [{"metadata": {"id": 7, "name": {"ita-IT": "Bando servizio"}, "published": "2026-01-02T00:00:00+01:00"},
                            "data": {"ita-IT": {"abstract": "sintesi"}}}]}
    (a,) = opencity(dati, "https://tn.it/servizi")
    assert a.titolo == "Bando servizio" and a.riassunto == "sintesi" and a.url.endswith("#7")


def test_csv():
    testo = "Titolo;Data apertura;Link\nBando FESR;01/03/2026;https://x.it/fesr\n"
    (a,) = da_csv(testo, "https://x.it")
    assert a.titolo == "Bando FESR" and a.url == "https://x.it/fesr" and a.pubblicato_il.month == 3


def test_osservatore_html():
    annunci = estrai_link((DATI / "pagina_elenco.html").read_text(), "https://comune.esempio.it/avvisi")
    urls = [a.url for a in annunci]
    assert urls == ["https://comune.esempio.it/avvisi/contributi-imprese-2026", "https://comune.esempio.it/avvisi/bando-commercio"]
    assert annunci[0].pubblicato_il.date().isoformat() == "2026-09-18"
    assert annunci[1].pubblicato_il.date().isoformat() == "2026-09-12"


def test_date():
    assert leggi_data("2026-09-24") == datetime.fromisoformat("2026-09-24T00:00:00+00:00")
    assert leggi_data("scade il 3 ottobre 2026").month == 10
    assert leggi_data("22/09/26").year == 2026
    assert leggi_data("nessuna data") is None


def test_feed_con_spazi_prima_della_dichiarazione():
    grezzo = b"\n\n" + (DATI / "feed_rss2.xml").read_bytes()
    assert len(analizza_feed(grezzo)) == 2


def test_osservatore_ripiega_su_tutta_la_pagina_e_tiene_le_schede_con_header():
    html = """<html><body><header><a href="/menu/voce-lunga-del-menu-principale">Voce lunga del menu principale</a></header>
    <main id="content"></main>
    <div class="elenco"><article><header><a href="/avvisi/bando-imprese-artigiane-2026">Bando imprese artigiane 2026</a></header></article></div>
    <footer><a href="/note-legali-e-privacy-del-sito">Note legali e privacy del sito</a></footer></body></html>"""
    annunci = estrai_link(html, "https://x.it/avvisi")
    assert [a.url for a in annunci] == ["https://x.it/avvisi/bando-imprese-artigiane-2026"]


def test_robots_con_jolly():
    from app.raccolta.robots import analizza, permesso

    regole = analizza("User-agent: *\nAllow: /kweb*/sito\nDisallow: /\n\nUser-agent: Googlebot\nAllow: /\n", "BandiRadar/0.1")
    assert permesso(regole, "https://x.it/kweb-abc/sito/incentivi")
    assert not permesso(regole, "https://x.it/altro")
    tutto = analizza("User-agent: *\nDisallow: /api/\nDisallow: /content/search\n", "BandiRadar/0.1")
    assert permesso(tutto, "https://x.it/opendata/api/content/search/x")
    assert not permesso(tutto, "https://x.it/content/search?q=1")
    assert permesso(analizza("", "BandiRadar/0.1"), "https://x.it/qualunque")


def test_osservatore_prende_il_titolo_della_scheda_quando_il_link_dice_solo_scopri_di_piu():
    html = """<html><body><main><div class="card"><h3>Finanziamento per la patrimonializzazione delle PMI</h3>
    <p>testo</p><a href="/finanziamenti/patrimonializzazione">Scopri di più</a></div></main></body></html>"""
    (a,) = estrai_link(html, "https://x.it/finanziamenti")
    assert a.titolo == "Finanziamento per la patrimonializzazione delle PMI"


def test_osservatore_non_butta_una_testata_che_contiene_il_contenuto():
    html = """<html><body><header><main><ul><li><a href="/bandi/bando-contributi-fiere-2026">Bando contributi fiere 2026</a></li></ul></main></header></body></html>"""
    assert len(estrai_link(html, "https://x.it/bandi")) == 1
