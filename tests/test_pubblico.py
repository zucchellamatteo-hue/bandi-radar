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
        assert r.status_code == 200 and "bandinQiaro" in r.text, nome
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
    assert r.text.startswith("# bandinQiaro\n\n> ")
    assert "## Domande frequenti" in r.text and "(https://bandinqiaro.it/condizioni-supporto)" in r.text
    assert "Siti pubblici controllati" in r.text
    assert "Bandi aperti da visionare" in r.text and "con la scheda pronta" not in r.text


# --- Bandi in vetrina (08/10/2026) ---------------------------------------------------------------------------------

def test_riga_dell_agevolazione():
    from app.pubblico import vetrina

    assert vetrina.riga_bando({"tipi_agevolazione": ["fondo_perduto"], "contributo_massimo": 20000,
                               "percentuale": 50}) == "Fondo perduto 50%, fino a 20.000 €"
    assert vetrina.riga_bando({"tipi_agevolazione": ["voucher", "fondo_perduto"], "fondo_perduto_massimo": 20000,
                               "percentuale_fondo_perduto": 42.5}) == "Voucher a fondo perduto 42,5%, fino a 20.000 €"
    assert vetrina.riga_bando({"tipi_agevolazione": ["finanziamento_agevolato"], "finanziamento_massimo": 300000,
                               "percentuale": 75}) == "Finanziamento agevolato, fino a 300.000 €"
    assert vetrina.riga_bando({}) == "Contributo"


def test_file_della_vetrina_valido():
    """Ogni voce del file ha un bando o una misura (che esiste), date e priorita' scritte bene."""
    from datetime import date

    import yaml

    from app import misure
    from app.pubblico import vetrina

    dati = yaml.safe_load(vetrina.FILE.read_text(encoding="utf-8"))
    assert isinstance(dati.get("vetrina"), list)
    for v in dati["vetrina"]:
        assert bool(v.get("bando")) != bool(v.get("misura")), v
        if v.get("bando"):
            assert isinstance(v["bando"], int), v
        else:
            assert misure.una(v["misura"]), v
        for k in ("da", "a"):
            assert v.get(k) is None or isinstance(v[k], date), v
        assert v.get("priorita") is None or isinstance(v["priorita"], int), v
        assert set(v) <= {"bando", "misura", "priorita", "da", "a", "motivo", "titolo", "ente", "riga"}, v


def test_voci_del_file_per_data_e_priorita(tmp_path):
    from datetime import date

    from app.pubblico import vetrina

    f = tmp_path / "vetrina.yaml"
    f.write_text("vetrina:\n  - {bando: 3, priorita: 2}\n  - {bando: 1, priorita: 1, da: 2026-10-01, a: 2026-10-31}\n"
                 "  - {bando: 2, a: 2026-09-30}\n  - {misura: x}\n  - {nota: senza bando}\n", encoding="utf-8")
    voci = vetrina.voci_file(date(2026, 10, 8), f)
    assert [v.get("bando") or v.get("misura") for v in voci] == [1, 3, "x"]       # la 2 e' scaduta
    assert [v.get("bando") for v in vetrina.voci_file(date(2026, 11, 1), f)] == [3, None]
    assert vetrina.voci_file(percorso=tmp_path / "manca.yaml") == []


def test_html_della_vetrina_accessibile():
    from app.pubblico import vetrina

    voci = [{"tipo": "bando", "id": 1, "titolo": "Bando <uno>", "ente": "Regione", "riga": "Fondo perduto 50%",
             "quando": "Scade il 31/12/2026", "dove": "Veneto"},
            {"tipo": "misura", "id": "m", "titolo": "Misura due", "ente": "MIMIT", "riga": "Beneficio",
             "quando": "Sempre aperta", "dove": "Misura nazionale"}]
    h = vetrina.html(voci)
    assert "Bandi in vetrina" in h and "Bando &lt;uno&gt;" in h and "<uno>" not in h
    assert h.count('class="voce attiva"') == 1 and h.count('class="voce"') == 1          # senza JS si vede la prima
    assert h.count('href="/registrati"') == 2 and h.count("Scopri se fa per te") == 2
    assert 'aria-roledescription="carosello"' in h and 'aria-label="1 di 2"' in h
    assert '<div class="comandi" hidden>' in h                                          # puntini e pausa solo con JS
    assert h.count('aria-current="true"') == 1 and "Mostra il bando 2 di 2: Misura due" in h
    assert "prefers-reduced-motion" in h and 'setAttribute("aria-live", timer ? "off" : "polite")' in h
    assert str(vetrina.GIRO_MS) in h and "__GIRO__" not in h
    assert vetrina.html([]) == ""


@db
def test_vetrina_dal_file_e_in_automatico(tmp_path, monkeypatch):
    from datetime import date, timedelta

    from app.db.connessione import connetti
    from app.db.migrazioni import applica_migrazioni
    from app.pubblico import vetrina

    oggi = date.today()
    prove = [  # titolo, stato, scadenza, fondo perduto massimo, controllo
        ("Vetrina buono", "aperto", oggi + timedelta(days=60), 50000, {}),
        ("Vetrina chiuso", "chiuso", oggi - timedelta(days=1), 50000, {}),
        ("Vetrina con errori", "aperto", oggi + timedelta(days=60), 80000, {"gravi": ["importo sbagliato"]}),
        ("Vetrina enorme", "aperto", oggi + timedelta(days=60), 30_000_000, {}),
        ("Vetrina in arrivo", "in_arrivo", oggi + timedelta(days=90), 20000, {}),
    ]
    with connetti() as conn:
        applica_migrazioni(conn)
        ids = {}
        with conn.cursor() as cur:
            for titolo, stato, scadenza, importo, controllo in prove:
                cur.execute("""INSERT INTO bandi (titolo, ente, stato, scadenza, data_apertura, completezza, controllo,
                                                  tipi_agevolazione, fondo_perduto_massimo, percentuale_fondo_perduto, vincoli)
                               VALUES (%s, %s, %s, %s, %s, 'bando_ufficiale', %s, '{fondo_perduto}', %s, 50,
                                       '{"territorio": "nessun_vincolo"}') RETURNING id""",
                            (titolo, "Ente " + titolo, stato, scadenza, oggi + timedelta(days=30), json.dumps(controllo), importo))
                ids[titolo] = cur.fetchone()["id"]
        try:
            f = tmp_path / "vetrina.yaml"
            f.write_text(f"vetrina:\n  - {{bando: {ids['Vetrina chiuso']}, priorita: 1}}\n"
                         f"  - {{bando: {ids['Vetrina in arrivo']}, priorita: 2, riga: 'Riga scritta a mano'}}\n"
                         "  - {misura: iperammortamento_2026, priorita: 3}\n", encoding="utf-8")
            monkeypatch.setattr(vetrina, "FILE", f)
            voci = vetrina._scegli(conn, 10, oggi)              # 10: altri test possono lasciare bandi nel database
            titoli = [v["titolo"] for v in voci]
            assert titoli[:2] == ["Vetrina in arrivo", "Iperammortamento 2026 (Nuovo Piano Transizione 5.0)"]
            assert voci[0]["riga"] == "Riga scritta a mano" and voci[0]["quando"].startswith("Domande dal ")
            assert voci[0]["dove"] == "Tutta Italia" and voci[1]["dove"] == "Misura nazionale"
            assert "Vetrina buono" in titoli                                     # aggiunto in automatico
            assert not {"Vetrina chiuso", "Vetrina con errori", "Vetrina enorme"} & set(titoli)
            buono = next(v for v in voci if v["titolo"] == "Vetrina buono")
            assert buono["riga"] == "Fondo perduto 50%, fino a 50.000 €"
            assert len(vetrina._scegli(conn, 1, oggi)) == 1
        finally:
            conn.rollback()


@db
def test_landing_con_la_vetrina_e_i_testi_nuovi(monkeypatch):
    from app.db.connessione import connetti
    from app.db.migrazioni import applica_migrazioni
    from app.main import app
    from app.pubblico import vetrina

    with connetti() as conn:
        applica_migrazioni(conn)
        conn.commit()
    landing._cache.clear()
    vetrina._cache.clear()
    t = TestClient(app).get("/presentazione").text
    assert "Bandi in vetrina" in t and "Scopri se fa per te" in t                # almeno la misura del file
    assert "bandi aperti da visionare" in t and "con la scheda pronta" not in t and "bandi aperti con la scheda" not in t
    assert ("Ogni bando viene esaminato e riorganizzato in modo chiaro e semplice e ti segnaliamo quelli che fanno al "
            "caso della tua impresa. Se vuoi, poi, un consulente ti aiuta con la predisposizione e la presentazione "
            "della domanda.") in t
    assert "Unione Europea, Ministeri, Regioni, Camere di Commercio e Comuni" in t
