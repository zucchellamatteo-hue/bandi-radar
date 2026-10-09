"""Blog: Markdown sicuro, FAQ, slug e fonti (senza database); pagine pubbliche, permessi, sitemap, /llms.txt, robots e
riquadro "Bando chiuso" (con il database di prova)."""

import json
import os
import re
import uuid
from datetime import date, timedelta

import pytest
from fastapi.testclient import TestClient

from app import articoli
from app.pubblico import seo

db = pytest.mark.skipif(not os.environ.get("PGHOST"), reason="serve un database Postgres di prova (PGHOST)")

CORPO = """## A chi serve
Alle **PMI** di tutta Italia. Vedi [la pagina ufficiale](https://www.mimit.gov.it/x?a=1&b=2) e [la prova](/registrati).

- prima voce
- seconda voce
  che continua

1. passo uno
2. passo due

## Domande frequenti
### Serve un commercialista?
No, ma aiuta.
Molto.

### Quanto dura?
- 12 mesi
- 24 mesi

## Fonti
Testo finale."""


def test_markdown_in_html_sicuro():
    h = articoli.in_html(CORPO)
    assert '<h2 id="a-chi-serve">A chi serve</h2>' in h and "<strong>PMI</strong>" in h
    assert '<a href="https://www.mimit.gov.it/x?a=1&amp;b=2" rel="noopener" target="_blank">la pagina ufficiale</a>' in h
    assert '<a href="/registrati">la prova</a>' in h
    assert "<ul><li>prima voce</li><li>seconda voce che continua</li></ul>" in h
    assert "<ol><li>passo uno</li><li>passo due</li></ol>" in h
    cattivo = articoli.in_html('<script>alert(1)</script> [x](javascript:alert(1)) [y](//altro.it) <img src=x onerror=1>')
    assert "<script" not in cattivo and "<img" not in cattivo and "javascript:" not in cattivo and 'href="//' not in cattivo
    assert "&lt;script&gt;" in cattivo


def test_domande_frequenti_dal_corpo():
    faq = articoli.domande_frequenti(CORPO)
    assert faq == [("Serve un commercialista?", "No, ma aiuta. Molto."), ("Quanto dura?", "12 mesi; 24 mesi")]
    assert articoli.domande_frequenti("## Altro\n### Domanda?\nRisposta") == []


def test_slug_fonti_e_controlli():
    assert articoli.crea_slug("Nuova Sabatini: perché conviene nel 2026?") == "nuova-sabatini-perche-conviene-nel-2026"
    assert articoli._fonti("MIMIT | https://www.mimit.gov.it\n\nhttps://inps.it") == [
        {"nome": "MIMIT", "url": "https://www.mimit.gov.it"}, {"nome": "https://inps.it", "url": "https://inps.it"}]
    with pytest.raises(articoli.ErroreArticoli):
        articoli._fonti("Sito | ftp://x")
    v = articoli._controlla({"titolo": " Un   titolo ", "sommario": "S", "corpo": " C ", "bando_id": " 12 "}, True)
    assert v["slug"] == "un-titolo" and v["titolo"] == "Un titolo" and v["bando_id"] == 12 and v["corpo"] == "C"
    for sbagliato in ({"titolo": "", "sommario": "s", "corpo": "c"}, {"titolo": "t", "sommario": "s"},
                      {"titolo": "t", "sommario": "s" * 301, "corpo": "c"}, {"titolo": "t", "sommario": "s", "corpo": "c", "bando_id": "x"},
                      {"titolo": "t", "sommario": "s", "corpo": "c", "misura_id": "inventata"},
                      {"titolo": "!!!", "sommario": "s", "corpo": "c"}):
        with pytest.raises(articoli.ErroreArticoli):
            articoli._controlla(sbagliato, True)
    assert articoli._controlla({"misura_id": "nuova_sabatini"}, False) == {"misura_id": "nuova_sabatini"}


def test_autore_predefinito(monkeypatch):
    monkeypatch.delenv("AUTORE_ARTICOLI", raising=False)
    assert articoli.autore_predefinito() == articoli.AUTORE_SEGNAPOSTO
    monkeypatch.setenv("AUTORE_ARTICOLI", "Mario Rossi, commercialista")
    assert articoli.autore_predefinito() == "Mario Rossi, commercialista"


def test_sitemap_e_robots_con_il_blog(monkeypatch):
    monkeypatch.setenv("SITO_URL", "https://bandinqiaro.it")
    s = seo.sitemap_xml(articoli=[("/blog", "2026-10-07"), ("/blog/nuova-sabatini", "2026-10-06")])
    assert "<loc>https://bandinqiaro.it/blog/nuova-sabatini</loc><lastmod>2026-10-06</lastmod>" in s
    t = seo.robots_txt(True)
    from test_pubblico import _permesso

    assert _permesso(t, "/blog") and _permesso(t, "/blog/nuova-sabatini")
    assert not _permesso(t, "/articoli") and not _permesso(t, "/api/articoli")      # la pagina della plancia resta chiusa


def _bando(cur, scadenza):
    cur.execute("""INSERT INTO bandi (titolo, url, scadenza, completezza, stato) VALUES (%s, 'https://esempio.it/b', %s,
                   'bando_ufficiale', 'aperto') RETURNING id""", (f"Bando di prova blog {uuid.uuid4().hex[:6]}", scadenza))
    return cur.fetchone()["id"]


@db
def test_blog_completo(monkeypatch):
    from conftest import accesso_di_prova

    from app.db.connessione import connetti
    from app.db.migrazioni import applica_migrazioni
    from app.main import app

    with connetti() as conn:
        applica_migrazioni(conn)
        with conn.cursor() as cur:
            aperto = _bando(cur, date.today() + timedelta(days=90))
            scaduto = _bando(cur, date.today() - timedelta(days=3))
        conn.commit()
    monkeypatch.setenv("SITO_URL", "https://bandinqiaro.it")
    monkeypatch.setenv("PAGINA_PUBBLICA", "0")
    c = TestClient(app)
    admin, revisore, impresa = accesso_di_prova("admin"), accesso_di_prova("revisore"), accesso_di_prova("impresa")
    sigla = uuid.uuid4().hex[:6]
    nuovo = {"titolo": f"Guida di prova {sigla}", "sommario": "Due righe di sommario.", "corpo": CORPO,
             "fonti": f"MIMIT | https://www.mimit.gov.it/{sigla}", "bando_id": aperto, "stato": "pubblicato"}

    # scrivere: serve "modifiche"; nasce sempre in bozza anche se si chiede "pubblicato"
    assert c.post("/api/articoli", auth=revisore, json=nuovo).status_code == 403
    assert c.post("/api/articoli", auth=impresa, json=nuovo).status_code == 403
    a = c.post("/api/articoli", auth=admin, json=nuovo).json()
    assert a["stato"] == "bozza" and a["slug"] == f"guida-di-prova-{sigla}" and a["fonti"][0]["nome"] == "MIMIT"
    assert c.post("/api/articoli", auth=admin, json=nuovo).status_code == 422            # stesso indirizzo
    assert c.post("/api/articoli", auth=admin, json=nuovo | {"slug": "altro-" + sigla, "bando_id": 0}).status_code == 422
    elenco = c.get("/api/articoli", auth=admin).json()
    assert any(x["id"] == a["id"] and x["parole"] > 20 for x in elenco["articoli"]) and elenco["misure"]
    assert c.get("/api/articoli", auth=impresa).status_code == 403

    # la bozza non esiste per il pubblico, ne' in sitemap e /llms.txt; l'anteprima si' (con "lavoro")
    assert c.get(f"/blog/{a['slug']}").status_code == 404
    assert a["slug"] not in c.get("/sitemap.xml").text and a["slug"] not in c.get("/llms.txt").text
    ant = c.post("/api/articoli/anteprima", auth=admin, json=nuovo | {"id": a["id"]}).json()["html"]
    assert "Anteprima dalla plancia" in ant and 'content="noindex, nofollow"' in ant
    assert c.post("/api/articoli/anteprima", auth=impresa, json=nuovo).status_code == 403

    # pubblicare: solo l'admin (chi ha "modifiche" ma non e' admin riceve un rifiuto)
    with connetti() as conn:
        with pytest.raises(PermissionError):
            articoli.modifica(conn, a["id"], {"stato": "pubblicato"}, "qualcuno", admin=False)
    p = c.patch(f"/api/articoli/{a['id']}", auth=admin, json={"stato": "pubblicato"}).json()
    assert p["stato"] == "pubblicato" and p["pubblicato_il"] and p["aggiornato_il"] == a["aggiornato_il"]
    with connetti() as conn:
        with pytest.raises(PermissionError):                                          # pubblicato: lo tocca solo l'admin
            articoli.modifica(conn, a["id"], {"titolo": "Cambiato"}, "qualcuno", admin=False)
        with pytest.raises(PermissionError):
            articoli.cancella(conn, a["id"], admin=False)

    r = c.get(f"/blog/{a['slug']}")
    assert r.status_code == 200
    t = r.text
    assert "Aggiornato il" in t and "Bando chiuso" not in t and "/registrati" in t and f"https://www.mimit.gov.it/{sigla}" in t
    assert 'content="noindex, nofollow"' in t                                         # sito spento: niente indice
    assert f'<link rel="canonical" href="https://bandinqiaro.it/blog/{a["slug"]}">' in t
    dati = json.loads(re.search(r'<script type="application/ld\+json">(.*?)</script>', t, re.S).group(1))
    tipi = {o["@type"] for o in dati["@graph"]}
    assert {"Article", "FAQPage", "BreadcrumbList", "Organization"} <= tipi
    faq = next(o for o in dati["@graph"] if o["@type"] == "FAQPage")
    assert faq["mainEntity"][0]["name"] == "Serve un commercialista?" and faq["mainEntity"][0]["name"] in t
    art = next(o for o in dati["@graph"] if o["@type"] == "Article")
    assert art["datePublished"] and art["dateModified"] and art["author"]["name"]
    assert a["slug"] in c.get("/blog").text
    assert f"<loc>https://bandinqiaro.it/blog/{a['slug']}</loc>" in c.get("/sitemap.xml").text
    assert f"(https://bandinqiaro.it/blog/{a['slug']})" in c.get("/llms.txt").text
    monkeypatch.setenv("PAGINA_PUBBLICA", "1")
    assert 'content="index, follow' in c.get(f"/blog/{a['slug']}").text and 'content="index, follow' in c.get("/blog").text

    # il bando collegato scade: riquadro "Bando chiuso" automatico, anche nell'elenco e in /llms.txt
    c.patch(f"/api/articoli/{a['id']}", auth=admin, json={"bando_id": scaduto})
    t = c.get(f"/blog/{a['slug']}").text
    assert "Bando chiuso" in t and f"scaduto il {date.today() - timedelta(days=3):%d/%m/%Y}" in t
    assert "bando chiuso" in c.get("/blog").text
    assert "bando chiuso: solo consultazione" in c.get("/llms.txt").text
    assert any(x["chiuso"] for x in c.get("/api/articoli", auth=admin).json()["articoli"] if x["id"] == a["id"])

    # misura nazionale non piu' aperta: stesso riquadro
    with connetti() as conn:
        assert articoli.situazione_collegata(conn, {"misura_id": "credito_formazione_40"})["cosa"] == "misura"
        assert articoli.situazione_collegata(conn, {"misura_id": "nuova_sabatini"}) is None

    # archiviato: 410, fuori da sitemap ed elenco
    c.patch(f"/api/articoli/{a['id']}", auth=admin, json={"stato": "archiviato"})
    assert c.get(f"/blog/{a['slug']}").status_code == 410
    assert a["slug"] not in c.get("/sitemap.xml").text and a["slug"] not in c.get("/blog").text
    assert c.get("/blog/non-esiste-davvero").status_code == 404
    assert c.delete(f"/api/articoli/{a['id']}", auth=admin).status_code == 200


@db
def test_carica_sempre_in_bozza():
    from app.db.connessione import connetti
    from app.db.migrazioni import applica_migrazioni

    sigla = uuid.uuid4().hex[:6]
    voci = [{"titolo": f"Caricato {sigla}", "sommario": "S.", "corpo": "## Uno\nTesto.", "stato": "pubblicato",
             "fonti": [{"nome": "INPS", "url": "https://www.inps.it"}], "misura_id": "incentivi_assunzione_2026"}]
    with connetti() as conn:
        applica_migrazioni(conn)
        primo = articoli.carica(conn, voci, "prova")
        secondo = articoli.carica(conn, voci, "prova")
        a = articoli.per_slug(conn, f"caricato-{sigla}")
        conn.rollback()
    assert "caricato in bozza" in primo[0][1] and "c'era già" in secondo[0][1]
    assert a["stato"] == "bozza" and a["fonti"] == [{"nome": "INPS", "url": "https://www.inps.it"}]


def test_bozze_preparate_dalle_sessioni_sono_valide():
    """I file in strumenti/sessione/blog si caricano senza errori: campi validi, misure esistenti, FAQ presenti."""
    from pathlib import Path

    cartella = Path(__file__).resolve().parents[1] / "strumenti" / "sessione" / "blog"
    file = sorted(cartella.glob("*.json"))
    assert file
    slug = []
    for f in file:
        for a in json.loads(f.read_text(encoding="utf-8")):
            v = articoli._controlla({k: a[k] for k in articoli.CAMPI_TESTO if k in a}, True)
            assert articoli._fonti(a["fonti"]) and len(v["sommario"]) <= 230, v["slug"]
            assert len(articoli.domande_frequenti(a["corpo"])) >= 3, v["slug"]
            assert "<table" not in a["corpo"], v["slug"]    # niente HTML scritto a mano (le tabelle Markdown vanno bene)
            slug.append(v["slug"])
    assert len(slug) == len(set(slug))


def test_tabelle_nel_markdown():
    from app.articoli import in_html

    html = in_html("Testo\n\n| Voce | Valore |\n|---|---:|\n| Spesa | 200.000 € |\n| **Credito** | 27.000 € |\n\nFine")
    assert "<table>" in html and "<th>Voce</th>" in html and "<td><strong>Credito</strong></td>" in html
    assert "---" not in html


def test_calcolatore_sabatini():
    """La riga [[calcolatore:sabatini]] diventa il calcolatore; un nome sconosciuto non mostra niente; la formula
    torna con le percentuali del foglio MIMIT (7,72%, 10,09%, 14,26%)."""
    from app import articoli
    from app.pubblico import calcolatori

    h = articoli.in_html("Testo.\n\n[[calcolatore:sabatini]]\n\n[[calcolatore:inventato]]\n\nFine.")
    assert 'id="calcolatore-sabatini"' in h and "<script>" in h and "inventato" not in h
    assert "<script>" not in articoli.in_html("Nel testo [[calcolatore:sabatini]] in mezzo a una frase.")
    assert round(calcolatori.contributo_sabatini(100000, 0.0275)) == 7717
    assert round(calcolatori.contributo_sabatini(100000, 0.03575) / 1000, 1) == 10.1
    assert round(calcolatori.contributo_sabatini(100000, 0.05) / 1000, 1) == 14.3


def test_calcolatori_con_i_limiti_delle_misure():
    """Le formule dei calcolatori (09/10) danno i numeri delle schede in app/misure/misure.yaml."""
    from app import articoli
    from app.pubblico import calcolatori as c

    assert c.iperammortamento(100_000) == 180_000
    assert c.iperammortamento(5_000_000) == 7_000_000            # 4.500.000 + 2.500.000
    assert c.iperammortamento(20_000_000) == c.iperammortamento(30_000_000) == 17_000_000
    assert round(c.credito_rs(155_000, 70_000, 20_000)) == 24_000  # esempio della scheda: base 240.000
    assert c.credito_rs(100_000_000) == 5_000_000                # tetto annuo
    campania = (60, 50, 40)
    assert c.credito_zes(1_000_000, campania, 0) == 600_000
    assert c.credito_zes(1_000_000, campania, 2) == 400_000
    assert c.credito_zes(199_999, campania, 0) == 0               # sotto la soglia di 200.000
    assert c.credito_zes(80_000_000, campania, 0) == 27_000_000   # importo corretto: 40% x (55 + 0,5 x 25)
    assert c.credito_zes(400_000, campania, 0, altri_aiuti=100_000) == 140_000   # esempio dell'articolo (Puglia)
    assert c.credito_zes(400_000, campania, 0, altri_aiuti=300_000) == 0
    assert round(c.art_bonus(153_846, 20_000_000)) == 100_000      # esempio del portale
    assert c.art_bonus(5_000, 1_000_000) == 3_250
    # Conto Termico: gli esempi dell'articolo (Regole Applicative GSE, par. 4.2.1 e 4.6)
    assert c.conto_termico(20, titolo3=30_000) == (19_500, 2)                       # pompa di calore 30 kW, piccola
    assert c.conto_termico(10, titolo3=150_000, titolo2=450_000, multi=True) == (262_500, 5)  # manifattura media
    assert c.conto_termico(20, titolo3=30_000, titolo2=40_000, pompa_piccola=False) == (37_500, 5)  # artigiano
    assert c.conto_termico(20, titolo3=12_000, titolo2=6_000) == (10_500, 1)        # negozio: rata unica
    assert c.conto_termico(10, titolo2=240_000) == (84_000, 5)                      # logistica: 35%
    assert c.conto_termico(20, titolo2=100_000, multi=True, zona=15, risparmio_40=True)[0] == 65_000   # tetto PMI
    assert c.conto_termico(0, titolo2=100_000, multi=True, zona=15, risparmio_40=True)[0] == 60_000    # tetto grandi
    assert c.conto_termico(0, titolo3=100_000)[0] == 45_000
    for nome in c.CALCOLATORI:                                    # ogni calcolatore si inserisce e porta il suo script
        h = articoli.in_html(f"[[calcolatore:{nome}]]")
        assert "bqEuro" in h and 'class="calcolatore"' in h


def test_link_ad_articoli_in_bozza_diventano_testo():
    from app import articoli
    from app.pubblico.blog import senza_link_a_bozze

    h = articoli.in_html("Vedi [Fondo](/blog/fondo-garanzia) e [iper](/blog/iper#a) e [MIMIT](https://www.mimit.gov.it).")
    out = senza_link_a_bozze(h, {"iper"})
    assert "Vedi Fondo e" in out and '<a href="/blog/iper#a">iper</a>' in out and "mimit.gov.it" in out


def test_lista_da_spuntare_e_paragrafi_condizionati(monkeypatch):
    """Liste "- [ ]" con le caselle; blocchi [[se:...]] visibili solo con il servizio attivo (09/10)."""
    from app import articoli

    h = articoli.in_html("- [ ] Contratto a tempo e materiali\n- [x] Perizia")
    assert '<ul class="spunte">' in h and h.count('type="checkbox"') == 2 and "checked" in h and "[ ]" not in h
    md = "Prima.\n\n[[se:contatti]]\nScrivici a [[email_contatto]].\n[[fine]]\n\n[[se:abbonamenti]]\nAbbonati.\n[[fine]]\n\nDopo."
    monkeypatch.delenv("EMAIL_CONTATTO", raising=False)
    monkeypatch.setenv("PAGINA_PUBBLICA", "0")
    h = articoli.in_html(md)
    assert "Scrivici" not in h and "Abbonati" not in h and "Prima" in h and "Dopo" in h and "[[" not in h
    assert "Nascosto ai lettori" in articoli.in_html(md, anteprima=True)
    monkeypatch.setenv("EMAIL_CONTATTO", "info@esempio.it")
    h = articoli.in_html(md)
    assert '<a href="mailto:info@esempio.it">info@esempio.it</a>' in h and "Abbonati" not in h
    monkeypatch.setenv("PAGINA_PUBBLICA", "1")
    assert "Abbonati" in articoli.in_html(md)
