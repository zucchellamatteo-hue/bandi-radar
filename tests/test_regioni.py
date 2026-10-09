"""Pagine "Bandi aperti in <regione>" (09/10/2026, PIANO_SEO_GEO punto 7): indirizzi, contenuto, indicizzazione solo
con il blog aperto e almeno 8 bandi, sitemap, robots, /llms.txt e statistiche."""

import json
import os
import re
from datetime import date, timedelta

import pytest
from fastapi.testclient import TestClient

from app import visite
from app.pubblico import regioni, seo

db = pytest.mark.skipif(not os.environ.get("PGHOST"), reason="serve un database Postgres di prova (PGHOST)")
OGGI = date.today()


def _bando(i: int, regione: str = "LOM", giorni: int | None = 60, **altro) -> dict:
    b = {"id": i, "titolo": f"Bando numero {i} per le imprese", "ente": "Regione di prova", "stato": "aperto",
         "scadenza": OGGI + timedelta(days=giorni) if giorni is not None else None, "data_apertura": None,
         "tipi_agevolazione": ["fondo_perduto"], "contributo_massimo": 20000, "percentuale": 50,
         "fondo_perduto_massimo": None, "percentuale_fondo_perduto": None, "finanziamento_massimo": None,
         "territorio_regioni": [regione], "territorio": "vincolo", "sintesi": "Contributo per investimenti. " * 20}
    b.update(altro)
    return b


def _dati(lombardia: int = 9, umbria: int = 3) -> dict:
    per = {"LOM": [_bando(i, giorni=10 if i == 0 else 60 + i) for i in range(lombardia)],
           "UMB": [_bando(100 + i, "UMB") for i in range(umbria)]}
    return {"per_regione": per, "nazionali": 42, "aggiornato": OGGI}


@pytest.fixture
def finti(monkeypatch):
    monkeypatch.setattr(regioni, "dati", lambda conn: _dati())
    monkeypatch.setenv("SITO_URL", "https://bandinqiaro.it")


def test_indirizzi_delle_regioni():
    r = regioni.regioni()
    assert len(r) == 21
    assert r["lombardia"] == ("LOM", "Lombardia")
    assert r["friuli-venezia-giulia"][0] == "FVG" and r["valle-d-aosta"][0] == "VDA"
    assert r["emilia-romagna"][0] == "EMR" and r["provincia-di-trento"][0] == "TN"
    assert all(re.fullmatch(r"[a-z0-9-]+", s) for s in r)


def test_pagina_regione_con_bandi_e_dati_strutturati(finti, monkeypatch):
    monkeypatch.setenv("BLOG_PUBBLICO", "1")
    t = regioni.pagina_regione(None, "lombardia")
    assert "<h1>Bandi aperti in Lombardia per le imprese</h1>" in t
    assert "In scadenza entro 30 giorni (1)" in t and "Altri bandi aperti o in arrivo (8)" in t
    assert "Fondo perduto 50%, fino a 20.000 €" in t and "42 bandi nazionali ed europei" in t
    assert t.count('href="/registrati"') >= 10                        # ogni voce porta alla registrazione
    assert '<link rel="canonical" href="https://bandinqiaro.it/bandi-aperti/lombardia">' in t
    assert 'content="index, follow' in t                              # 9 bandi e blog aperto: indicizzabile
    titolo = re.search(r"<title>(.*?)</title>", t).group(1)
    assert len(titolo) <= 60 and "Lombardia" in titolo, titolo
    descrizione = re.search(r'<meta name="description" content="(.*?)">', t).group(1)
    assert len(descrizione) <= 160
    grafo = json.loads(re.search(r'<script type="application/ld\+json">(.*?)</script>', t, re.S).group(1))["@graph"]
    pagina = next(o for o in grafo if o["@type"] == "CollectionPage")
    assert pagina["mainEntity"]["numberOfItems"] == 9 and len(pagina["mainEntity"]["itemListElement"]) == 9
    assert any(o["@type"] == "BreadcrumbList" for o in grafo)


def test_poche_voci_o_blog_chiuso_non_si_indicizza(finti, monkeypatch):
    monkeypatch.setenv("BLOG_PUBBLICO", "1")
    monkeypatch.setenv("PAGINA_PUBBLICA", "0")
    assert 'content="noindex, nofollow"' in regioni.pagina_regione(None, "umbria")       # 3 bandi, sotto la soglia
    assert "Bandi aperti in Umbria" in regioni.pagina_regione(None, "umbria")
    assert "nella Provincia di Bolzano" in regioni.pagina_regione(None, "provincia-di-bolzano")
    monkeypatch.setenv("BLOG_PUBBLICO", "0")
    t = regioni.pagina_regione(None, "lombardia")
    assert 'content="noindex, nofollow"' in t and "Anteprima" in t
    assert regioni.pagina_regione(None, "atlantide") is None


def test_sitemap_e_llms_solo_regioni_sopra_la_soglia(finti):
    voci = regioni.voci_sitemap(None)
    assert [p for p, _ in voci] == ["/bandi-aperti", "/bandi-aperti/lombardia"]
    xml = seo.sitemap_xml(articoli=voci, solo_blog=True)
    assert "<loc>https://bandinqiaro.it/bandi-aperti/lombardia</loc>" in xml and "<changefreq>daily</changefreq>" in xml
    righe = "\n".join(regioni.righe_llms(None))
    assert "(https://bandinqiaro.it/bandi-aperti/lombardia)" in righe and "umbria" not in righe


def test_elenco_delle_regioni(finti, monkeypatch):
    monkeypatch.setenv("BLOG_PUBBLICO", "1")
    t = regioni.pagina_elenco(None)
    assert t.count('href="/bandi-aperti/') == 21
    assert '<a href="/bandi-aperti/lombardia"><span>Lombardia</span><b>9</b></a>' in t
    assert 'content="index, follow' in t


def test_robots_e_statistiche():
    r = seo.robots_txt(False, blog=True)
    assert "Allow: /bandi-aperti" in r and "Allow: /blog" in r and "Disallow: /\n" in r
    assert visite.percorso_contato("/bandi-aperti") == "/bandi-aperti"
    assert visite.percorso_contato("/bandi-aperti/lombardia/") == "/bandi-aperti/lombardia"
    assert visite.percorso_contato("/bandi/12") is None                # la plancia non si conta


def test_dati_dai_proponibili(monkeypatch):
    """I nazionali (territorio senza vincolo) non finiscono in una regione; un bando di piu' regioni va in tutte."""
    righe = [_bando(1, "LOM"), _bando(2, territorio="nessun_vincolo", territorio_regioni=[]),
             _bando(3, territorio_regioni=["LOM", "PIE"])]

    class Cursore:
        def __enter__(self):
            return self

        def __exit__(self, *a):
            return False

        def execute(self, sql, *a):
            assert "bandi_situazione" in sql and "proponibile" in sql

        def fetchall(self):
            return righe

    class Conn:
        def cursor(self):
            return Cursore()

    regioni._cache.clear()
    d = regioni.dati(Conn())
    assert [b["id"] for b in d["per_regione"]["LOM"]] == [1, 3] and [b["id"] for b in d["per_regione"]["PIE"]] == [3]
    assert d["nazionali"] == 1
    regioni._cache.clear()


@db
def test_indirizzi_rispondono_sul_database(monkeypatch):
    from app.db.connessione import connetti
    from app.db.migrazioni import applica_migrazioni
    from app.main import app

    with connetti() as conn:
        applica_migrazioni(conn)
        conn.commit()
    regioni._cache.clear()
    c = TestClient(app)
    assert c.get("/bandi-aperti").status_code == 200
    r = c.get("/bandi-aperti/lombardia")
    assert r.status_code == 200 and "Bandi aperti in Lombardia" in r.text
    assert c.get("/bandi-aperti/atlantide").status_code == 404
    regioni._cache.clear()
