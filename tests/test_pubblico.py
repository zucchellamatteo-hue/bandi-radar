"""Pagina pubblica: testi legali, interruttore PAGINA_PUBBLICA, cookie di misurazione solo con l'ID e il consenso,
landing con i numeri, SEO tecnica (robots, sitemap, canonico, JSON-LD) e /llms.txt (07/10/2026)."""

import json
import os
import re

import pytest
from fastapi.testclient import TestClient

from app import pubblico
from app.pubblico import landing, seo

db = pytest.mark.skipif(not os.environ.get("PGHOST"), reason="serve un database Postgres di prova (PGHOST)")


def test_pagine_legali_senza_database(monkeypatch):
    from app.main import app

    monkeypatch.delenv("PAGINA_PUBBLICA", raising=False)
    monkeypatch.setenv("SITO_URL", "https://bandinqiaro.it/")
    c = TestClient(app)
    for nome in ("termini", "privacy", "cookie", "condizioni-supporto", "note-legali"):
        r = c.get(f"/{nome}")
        assert r.status_code == 200 and "Bandi Radar" in r.text, nome
        assert 'content="noindex, nofollow"' in r.text          # finche' la pagina non e' accesa
        assert f'<link rel="canonical" href="https://bandinqiaro.it/{nome}">' in r.text
    assert pubblico.legale("inventata") is None


def test_tag_di_google_solo_con_l_id(monkeypatch):
    monkeypatch.delenv("GOOGLE_ADS_ID", raising=False)
    monkeypatch.delenv("GOOGLE_ANALYTICS_ID", raising=False)
    assert '["", ""].filter(Boolean)' in pubblico.pagina("x", "<p>y</p>")    # niente ID: niente Google, niente banner
    monkeypatch.setenv("GOOGLE_ADS_ID", "AW-123\"><script>")
    monkeypatch.setenv("GOOGLE_ANALYTICS_ID", "G-ABC")
    assert '["AW-123script", "G-ABC"]' in pubblico.pagina("x", "<p>y</p>")   # niente caratteri pericolosi
    assert "googletagmanager" not in pubblico.pagina("x", "<p>y</p>").split("<script>")[0]   # mai caricato prima del consenso
    monkeypatch.setenv("PAGINA_PUBBLICA", "1")
    assert 'content="index, follow' in pubblico.pagina("x", "<p>y</p>", indicizza=pubblico.pubblica())


def test_robots_chiuso_finche_la_pagina_e_spenta(monkeypatch):
    from app.main import app

    c = TestClient(app)
    monkeypatch.setenv("PAGINA_PUBBLICA", "0")
    r = c.get("/robots.txt")
    assert r.status_code == 200 and "Disallow: /" in r.text and "Allow" not in r.text
    monkeypatch.setenv("PAGINA_PUBBLICA", "1")
    monkeypatch.setenv("SITO_URL", "https://bandinqiaro.it")
    t = c.get("/robots.txt").text
    assert "Allow: /$" in t and "Allow: /privacy$" in t and "Allow: /llms.txt" in t
    assert t.rstrip().splitlines()[-1] == "Sitemap: https://bandinqiaro.it/sitemap.xml"
    for programma in ("OAI-SearchBot", "ClaudeBot", "Claude-SearchBot", "PerplexityBot", "Google-Extended"):
        assert f"User-agent: {programma}" in t                       # i motori IA possono leggere le pagine pubbliche
    # Regole lette come fa Google (vince la regola piu' lunga): aperte solo le pagine pubbliche.
    for percorso in ("/", "/?gclid=abc", "/privacy", "/condizioni-supporto", "/llms.txt", "/immagini/anteprima.png"):
        assert _permesso(t, percorso), percorso
    for percorso in ("/catalogo", "/impresa", "/registrati", "/accedi", "/api/plancia/bandi", "/bandi/12", "/supervisione",
                     "/presentazione", "/privacy/altro"):
        assert not _permesso(t, percorso), percorso


def _permesso(robots: str, percorso: str) -> bool:
    regole = []
    for riga in robots.splitlines():
        campo, _, valore = riga.partition(": ")
        if campo in ("Allow", "Disallow") and valore:
            schema = re.escape(valore).replace(r"\*", ".*").replace(r"\$", "$")
            if re.match(schema, percorso):
                regole.append((len(valore), campo == "Allow"))
    return max(regole, default=(0, True))[1]


def test_sitemap_con_il_dominio_di_sito_url(monkeypatch):
    from app.main import app

    monkeypatch.setenv("SITO_URL", "https://bandinqiaro.it/")
    r = TestClient(app).get("/sitemap.xml")
    assert r.status_code == 200 and r.headers["content-type"].startswith("application/xml")
    assert "<loc>https://bandinqiaro.it/</loc>" in r.text and "<loc>https://bandinqiaro.it/privacy</loc>" in r.text
    assert "catalogo" not in r.text and "impresa" not in r.text


def test_immagini_e_favicon():
    from app.main import app

    c = TestClient(app)
    assert c.get("/favicon.svg").headers["content-type"].startswith("image/svg+xml")
    r = c.get("/immagini/anteprima.png")
    assert r.status_code == 200 and r.content[:4] == b"\x89PNG"
    from fastapi import HTTPException

    from app.main import immagine
    with pytest.raises(HTTPException):
        immagine("../__init__.py")                                    # solo i file della cartella immagini
    assert c.get("/immagini/nessuna.png").status_code == 404


def test_json_ld_valido_e_protetto():
    blocco = seo.json_ld([seo.domande_frequenti([("Domanda </script>?", "Risposta")]),
                          seo.servizio("descrizione", 20, 14)])
    assert "</script>?" not in blocco.removesuffix("</script>")
    dati = json.loads(re.search(r">(.*)</script>$", blocco, re.S).group(1))
    tipi = [o["@type"] for o in dati["@graph"]]
    assert tipi == ["FAQPage", "Service"]
    offerta = dati["@graph"][1]["offers"]
    assert offerta["price"] == "20.00" and offerta["priceCurrency"] == "EUR"
    assert offerta["priceSpecification"]["valueAddedTaxIncluded"] is False


def test_faq_senza_numeri_e_senza_html():
    domande = landing.faq(None, 14)
    assert len(domande) >= 8
    assert all("<" not in d and "<" not in r for d, r in domande)
    assert any("20 euro al mese" in r for _, r in domande)


@db
def test_landing_numeri_e_interruttore(monkeypatch):
    from app.db.connessione import connetti
    from app.db.migrazioni import applica_migrazioni
    from app.main import app

    with connetti() as conn:
        applica_migrazioni(conn)
        conn.commit()
    landing._cache.clear()
    monkeypatch.setenv("SITO_URL", "https://bandinqiaro.it")
    c = TestClient(app)
    r = c.get("/presentazione")
    assert r.status_code == 200
    t = r.text
    for pezzo in ("Come funziona, in 3 passi", "Prezzo di lancio", "Domande frequenti", "/registrati", "/privacy",
                  "/termini", "siti pubblici controllati", "misure nazionali", "Chi c'è dietro"):
        assert pezzo in t, pezzo
    assert '<link rel="canonical" href="https://bandinqiaro.it/">' in t
    assert 'property="og:image" content="https://bandinqiaro.it/immagini/anteprima.png"' in t
    assert 'content="noindex, nofollow"' in t                        # spenta: anteprima non indicizzata
    dati = json.loads(re.search(r'<script type="application/ld\+json">(.*?)</script>', t, re.S).group(1))
    tipi = {o["@type"] for o in dati["@graph"]}
    assert {"Organization", "WebSite", "Service", "FAQPage"} <= tipi
    faq = next(o for o in dati["@graph"] if o["@type"] == "FAQPage")
    assert faq["mainEntity"][0]["name"] in t                          # le domande del JSON-LD sono quelle della pagina

    monkeypatch.setenv("PAGINA_PUBBLICA", "0")
    assert "Prezzo di lancio" not in c.get("/").text                  # spenta: "/" porta all'accesso
    monkeypatch.setenv("PAGINA_PUBBLICA", "1")
    t = c.get("/").text
    assert "Prezzo di lancio" in t and 'content="index, follow' in t and "Anteprima:" not in t
    c.cookies.set("br_sessione", "qualcosa")
    assert "Prezzo di lancio" not in c.get("/").text                  # chi ha fatto l'accesso va alla plancia


@db
def test_numeri_veri_e_in_memoria(monkeypatch):
    from app.db.connessione import connetti
    from app.db.migrazioni import applica_migrazioni

    with connetti() as conn:
        applica_migrazioni(conn)
        with conn.cursor() as cur:
            cur.execute("SELECT count(*) AS n FROM bandi_situazione WHERE situazione = 'proponibile'")
            proponibili = cur.fetchone()["n"]
        landing._cache.clear()
        n = landing.numeri(conn)
        assert n["proponibili"] == proponibili and n["misure"] > 0 and n["fonti"] >= 0
        landing._cache["dati"] = dict(n, proponibili=-1)                  # in memoria: non ricalcola
        assert landing.numeri(conn)["proponibili"] == -1
        landing._cache.clear()


@db
def test_llms_txt(monkeypatch):
    from app.db.connessione import connetti
    from app.db.migrazioni import applica_migrazioni
    from app.main import app

    with connetti() as conn:
        applica_migrazioni(conn)
        conn.commit()
    landing._cache.clear()
    monkeypatch.setenv("SITO_URL", "https://bandinqiaro.it")
    r = TestClient(app).get("/llms.txt")
    assert r.status_code == 200 and r.headers["content-type"].startswith("text/markdown")
    assert r.text.startswith("# Bandi Radar\n\n> ")
    assert "## Domande frequenti" in r.text and "(https://bandinqiaro.it/condizioni-supporto)" in r.text
    assert "Siti pubblici controllati" in r.text
