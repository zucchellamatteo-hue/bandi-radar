"""Solo il blog aperto ai motori (BLOG_PUBBLICO), meta tag di verifica di Google e Bing, statistiche senza cookie
delle pagine pubbliche (08/10/2026)."""

import os
import uuid

import pytest
from fastapi.testclient import TestClient
from test_pubblico import _permesso

from app import pubblico, visite
from app.pubblico import blog, seo

db = pytest.mark.skipif(not os.environ.get("PGHOST"), reason="serve un database Postgres di prova (PGHOST)")

ARTICOLO = {"id": 1, "slug": "nuova-sabatini", "titolo": "Nuova Sabatini", "sommario": "Due righe.", "stato": "pubblicato",
            "corpo": "## Cos'è\nTesto.", "fonti": [], "autore": "Mario Rossi", "pubblicato_il": None, "aggiornato_il": None}


def _solo_blog(monkeypatch):
    monkeypatch.setenv("PAGINA_PUBBLICA", "0")
    monkeypatch.setenv("BLOG_PUBBLICO", "1")
    monkeypatch.setenv("SITO_URL", "https://bandinqiaro.it")


def test_robots_con_il_solo_blog_aperto(monkeypatch):
    from app.main import app

    c = TestClient(app)
    monkeypatch.setenv("PAGINA_PUBBLICA", "0")
    monkeypatch.delenv("BLOG_PUBBLICO", raising=False)
    assert "Allow" not in c.get("/robots.txt").text                       # di base tutto chiuso, come prima
    _solo_blog(monkeypatch)
    t = c.get("/robots.txt").text
    assert t.rstrip().splitlines()[-1] == "Sitemap: https://bandinqiaro.it/sitemap.xml"
    for percorso in ("/blog", "/blog/nuova-sabatini", "/llms.txt", "/sitemap.xml", "/favicon.svg", "/immagini/anteprima.png"):
        assert _permesso(t, percorso), percorso
    for percorso in ("/", "/?gclid=abc", "/presentazione", "/privacy", "/termini", "/catalogo", "/impresa", "/registrati",
                     "/accedi", "/api/plancia/bandi", "/api/visite", "/visite", "/articoli", "/bandi/12", "/supervisione"):
        assert not _permesso(t, percorso), percorso
    monkeypatch.setenv("PAGINA_PUBBLICA", "1")                              # tutto aperto: come prima, blog compreso
    t = c.get("/robots.txt").text
    assert _permesso(t, "/") and _permesso(t, "/privacy") and _permesso(t, "/blog/x") and not _permesso(t, "/catalogo")


def test_sitemap_solo_blog():
    s = seo.sitemap_xml(articoli=[("/blog", "2026-10-08"), ("/blog/nuova-sabatini", "2026-10-07")], solo_blog=True)
    assert "/blog/nuova-sabatini</loc>" in s and "/blog</loc>" in s
    assert "/privacy" not in s and "/termini" not in s and f"<loc>{seo.assoluto('/')}</loc>" not in s
    vuota = seo.sitemap_xml(articoli=[], solo_blog=True)                      # nessun articolo: almeno /blog
    assert vuota.count("<url>") == 1 and "/blog</loc>" in vuota


def test_sitemap_dal_sito_solo_blog(monkeypatch):
    from app.main import app

    _solo_blog(monkeypatch)
    r = TestClient(app).get("/sitemap.xml")
    assert r.status_code == 200 and "<loc>https://bandinqiaro.it/blog</loc>" in r.text
    assert "<loc>https://bandinqiaro.it/</loc>" not in r.text and "privacy" not in r.text
    monkeypatch.setenv("PAGINA_PUBBLICA", "1")
    assert "<loc>https://bandinqiaro.it/</loc>" in TestClient(app).get("/sitemap.xml").text


def test_articolo_indicizzabile_con_il_solo_blog(monkeypatch):
    monkeypatch.setenv("PAGINA_PUBBLICA", "0")
    monkeypatch.delenv("BLOG_PUBBLICO", raising=False)
    t = blog.pagina_articolo(None, ARTICOLO)
    assert 'content="noindex, nofollow"' in t and "Anteprima:" in t
    _solo_blog(monkeypatch)
    t = blog.pagina_articolo(None, ARTICOLO)
    assert 'content="index, follow' in t and "Anteprima:" not in t and 'class="bozza"' not in t
    assert "/registrati" in t                                               # l'invito a registrarsi resta
    assert "/presentazione" not in t                                        # niente link all'anteprima della landing
    assert '"item":"https://bandinqiaro.it/"' not in t                     # briciole senza la landing chiusa
    anteprima = blog.pagina_articolo(None, ARTICOLO | {"stato": "bozza"}, anteprima=True)
    assert 'content="noindex, nofollow"' in anteprima                       # le bozze mai
    assert 'content="noindex, nofollow"' in pubblico.legale("privacy")      # i testi legali restano chiusi
    monkeypatch.setenv("PAGINA_PUBBLICA", "1")
    t = blog.pagina_articolo(None, ARTICOLO)
    assert 'content="index, follow' in t and '"item":"https://bandinqiaro.it/"' in t


def test_landing_resta_chiusa_con_il_solo_blog(monkeypatch, tmp_path):
    from app import main

    _solo_blog(monkeypatch)
    (tmp_path / "index.html").write_text('<html><head><meta name="robots" content="noindex, nofollow" /></head><body>plancia</body></html>')
    monkeypatch.setattr(main, "CARTELLA_PLANCIA", tmp_path)
    t = TestClient(main.app).get("/").text
    assert "plancia" in t and "Prezzo di lancio" not in t                  # "/" porta ancora all'accesso


def test_meta_di_verifica(monkeypatch, tmp_path):
    from app import main

    monkeypatch.delenv("GOOGLE_SITE_VERIFICATION", raising=False)
    monkeypatch.delenv("BING_SITE_VERIFICATION", raising=False)
    assert seo.meta_verifica() == "" and "google-site-verification" not in pubblico.pagina("x", "<p>y</p>")
    monkeypatch.setenv("GOOGLE_SITE_VERIFICATION", 'abc_DEF-123"><script>')
    monkeypatch.setenv("BING_SITE_VERIFICATION", "0123ABCD")
    t = pubblico.pagina("x", "<p>y</p>")
    assert '<meta name="google-site-verification" content="abc_DEF-123script">' in t      # niente caratteri pericolosi
    assert '<meta name="msvalidate.01" content="0123ABCD">' in t
    assert "google-site-verification" in blog.pagina_articolo(None, ARTICOLO)
    # "/" con la landing chiusa e' la pagina d'accesso della plancia: il tag ci va lo stesso (Google lo cerca li')
    (tmp_path / "index.html").write_text("<html><head><title>p</title></head><body></body></html>")
    monkeypatch.setattr(main, "CARTELLA_PLANCIA", tmp_path)
    c = TestClient(main.app)
    assert '<meta name="msvalidate.01" content="0123ABCD"></head>' in c.get("/").text
    assert "msvalidate" not in c.get("/catalogo").text                     # solo su "/"


def test_tipo_di_visitatore():
    casi = {
        "Mozilla/5.0 (compatible; Googlebot/2.1; +http://www.google.com/bot.html)": ("motore", "Googlebot"),
        "Mozilla/5.0 AppleWebKit/537.36 (KHTML, like Gecko; compatible; bingbot/2.0; +http://www.bing.com/bingbot.htm)": ("motore", "Bingbot"),
        "Mozilla/5.0 AppleWebKit/537.36 (KHTML, like Gecko); compatible; GPTBot/1.2; +https://openai.com/gptbot": ("ia", "GPTBot"),
        "Mozilla/5.0 AppleWebKit/537.36 (KHTML, like Gecko); compatible; OAI-SearchBot/1.0": ("ia", "OAI-SearchBot"),
        "Mozilla/5.0 AppleWebKit/537.36 (KHTML, like Gecko); compatible; ChatGPT-User/1.0; +https://openai.com/bot": ("ia", "ChatGPT-User"),
        "Mozilla/5.0 AppleWebKit/537.36 (KHTML, like Gecko; compatible; ClaudeBot/1.0; +claudebot@anthropic.com)": ("ia", "ClaudeBot"),
        "Mozilla/5.0 (compatible; Claude-User/1.0; +Claude-User@anthropic.com)": ("ia", "Claude-User"),
        "Mozilla/5.0 AppleWebKit/537.36 (KHTML, like Gecko; compatible; PerplexityBot/1.0; +https://perplexity.ai/perplexitybot)": ("ia", "PerplexityBot"),
        "Mozilla/5.0 AppleWebKit/537.36 (KHTML, like Gecko; compatible; Perplexity-User/1.0)": ("ia", "Perplexity-User"),
        "Mozilla/5.0 (Macintosh) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17 Safari/605.1.15 (Applebot/0.1)": ("motore", "Applebot"),
        "CCBot/2.0 (https://commoncrawl.org/faq/)": ("ia", "CCBot"),
        "Mozilla/5.0 (Linux; Android 5.0) AppleWebKit/537.36 (KHTML, like Gecko) Mobile Safari/537.36 (compatible; Bytespider)": ("ia", "Bytespider"),
        "meta-externalagent/1.1 (+https://developers.facebook.com/docs/sharing/webmasters/crawler)": ("ia", "Meta-ExternalAgent"),
        "Mozilla/5.0 (compatible; AhrefsBot/7.0; +http://ahrefs.com/robot/)": ("altro", "AhrefsBot"),
        "curl/8.5.0": ("altro", "altro programma"),
        "": ("altro", "senza nome"),
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/129.0 Safari/537.36": ("persona", ""),
        "Mozilla/5.0 (iPhone; CPU iPhone OS 18_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/18.0 Mobile/15E148 Safari/604.1": ("persona", ""),
    }
    for ua, atteso in casi.items():
        assert visite.visitatore(ua) == atteso, ua


def test_provenienza_solo_dominio():
    propri = {"bandinqiaro.it"}
    assert visite.provenienza(None, propri) == "diretto" and visite.provenienza("", propri) == "diretto"
    assert visite.provenienza("https://www.google.it/search?q=bandi+imprese", propri) == "google.it"
    assert visite.provenienza("https://chatgpt.com/c/abc-123?x=1", propri) == "chatgpt.com"
    assert visite.provenienza("https://www.perplexity.ai/search/abc", propri) == "perplexity.ai"
    assert visite.provenienza("https://bandinqiaro.it/blog", propri) == "interno"
    assert visite.provenienza("android-app://com.google.android.gm/", propri) == "com.google.android.gm"
    assert visite.provenienza("https://m.facebook.com/", propri) == "facebook.com"
    for dominio, gruppo in (("chatgpt.com", "ia"), ("perplexity.ai", "ia"), ("copilot.microsoft.com", "ia"),
                            ("gemini.google.com", "ia"), ("claude.ai", "ia"), ("google.it", "motore"), ("google.com", "motore"),
                            ("bing.com", "motore"), ("duckduckgo.com", "motore"), ("linkedin.com", "social"),
                            ("lnkd.in", "social"), ("diretto", "diretto"), ("esempio.it", "altro")):
        assert visite.gruppo_provenienza(dominio) == gruppo, dominio


def test_utm_e_percorsi():
    assert visite.utm("utm_source=ChatGPT.com&utm_medium=&utm_campaign=Lancio%202026&gclid=x") == ("chatgpt.com", "", "lancio 2026")
    assert visite.utm("") == ("", "", "")
    assert len(visite.utm("utm_source=" + "a" * 500)[0]) == visite.MASSIMO_UTM
    for p in ("/", "/blog", "/blog/", "/blog/nuova-sabatini", "/llms.txt", "/sitemap.xml", "/robots.txt"):
        assert visite.percorso_contato(p), p
    for p in ("/catalogo", "/api/visite", "/presentazione", "/privacy", "/blog/a/b", "/assets/index.js", "/blog/X_Y"):
        assert visite.percorso_contato(p) is None, p


@db
def test_visite_contate_senza_identificativi(monkeypatch):
    from conftest import accesso_di_prova

    from app.db.connessione import connetti
    from app.db.migrazioni import applica_migrazioni
    from app.main import app

    with connetti() as conn:
        applica_migrazioni(conn)
        conn.execute("DELETE FROM visite WHERE giorno = current_date")
        conn.commit()
    _solo_blog(monkeypatch)
    c = TestClient(app)
    campagna = "prova-" + uuid.uuid4().hex[:6]
    persona = {"user-agent": "Mozilla/5.0 (Windows NT 10.0) Chrome/129.0 Safari/537.36"}
    assert c.get(f"/robots.txt?utm_source=LinkedIn&utm_campaign={campagna}", headers=persona).status_code == 200
    c.get("/robots.txt", headers=persona | {"referer": "https://chatgpt.com/c/123"})
    c.get("/robots.txt", headers=persona | {"referer": "https://chatgpt.com/c/456"})
    c.get("/robots.txt", headers={"user-agent": "Mozilla/5.0 (compatible; GPTBot/1.2; +https://openai.com/gptbot)",
                                  "referer": "https://esempio.it/"})
    c.get("/sitemap.xml", headers={"user-agent": "Mozilla/5.0 (compatible; Googlebot/2.1)"})
    c.get("/blog/non-esiste-davvero", headers=persona)                        # 404: non si conta
    admin = accesso_di_prova("admin")
    c.get("/robots.txt", headers=persona, auth=admin)                         # chi ha fatto l'accesso non si conta
    with connetti() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT * FROM visite WHERE giorno = current_date ORDER BY percorso, provenienza")
            righe = cur.fetchall()
    colonne = set(righe[0])
    assert colonne == {"giorno", "percorso", "provenienza", "utm_source", "utm_medium", "utm_campaign", "visitatore",
                       "programma", "conteggio"}                             # niente IP, User-Agent o identificativi
    per = {(r["percorso"], r["provenienza"], r["utm_source"], r["visitatore"], r["programma"]): r["conteggio"] for r in righe}
    assert per[("/robots.txt", "chatgpt.com", "", "persona", "")] == 2
    assert per[("/robots.txt", "diretto", "linkedin", "persona", "")] == 1
    assert per[("/robots.txt", "diretto", "", "ia", "GPTBot")] == 1         # dei programmi niente provenienza
    assert per[("/sitemap.xml", "diretto", "", "motore", "Googlebot")] == 1
    assert sum(per.values()) == 5 and not any(p.startswith("/blog/") for p, *_ in per)

    r = c.get("/api/visite?giorni=30", auth=admin).json()
    assert r["totali"]["persone"] == 3 and r["totali"]["ia"] == 1 and r["totali"]["motori"] == 1
    assert r["totali"]["persone_da_ia"] == 2
    assert {"provenienza": "chatgpt.com", "visite": 2, "gruppo": "ia"} in r["provenienze"]
    assert any(x["utm_campaign"] == campagna and x["utm_source"] == "linkedin" for x in r["campagne"])
    assert any(x["programma"] == "GPTBot" and x["percorso"] == "/robots.txt" for x in r["programmi"])
    assert c.get("/api/visite", auth=accesso_di_prova("impresa")).status_code == 403
    assert TestClient(app).get("/api/visite").status_code == 401


# --- rapporto SEO/GEO via email (app/notifiche/rapporto_seo.py) ---

def test_rapporto_frequenza_e_orario(monkeypatch):
    from datetime import date, datetime

    from app.notifiche import rapporto_seo as r

    monkeypatch.delenv("RAPPORTO_SEO", raising=False)
    assert r.frequenza() == "giornaliero"
    monkeypatch.setenv("RAPPORTO_SEO", "Settimanale")
    assert r.frequenza() == "settimanale"
    monkeypatch.setenv("RAPPORTO_SEO", "a caso")
    assert r.frequenza() == "giornaliero"
    martedi, lunedi = datetime(2026, 10, 13, 7, 5), datetime(2026, 10, 12, 8, 0)
    assert r.da_inviare(martedi, "giornaliero") and not r.da_inviare(martedi.replace(hour=6), "giornaliero")
    assert not r.da_inviare(martedi, "settimanale") and r.da_inviare(lunedi, "settimanale")
    assert not r.da_inviare(lunedi, "spento")
    assert r.chiave(date(2026, 10, 13), "giornaliero") == "2026-10-13"
    assert r.chiave(date(2026, 10, 13), "settimanale") == "2026-W42"
    p = r.periodi(date(2026, 10, 13), "giornaliero")
    assert p["corrente"] == (date(2026, 10, 12),) * 2 and p["precedente"] == (date(2026, 10, 11),) * 2
    assert p["sette"] == (date(2026, 10, 6), date(2026, 10, 12))
    assert r.dati_search_console(None, date(2026, 10, 6), date(2026, 10, 12)) is None      # non ancora collegato
    assert r._variazione(5, 4) == "+1 (+25%)" and r._variazione(3, 3) == "=" and r._variazione(2, 0) == "+2"


@db
def test_rapporto_seo_con_i_dati(monkeypatch, capsys):
    from datetime import date, timedelta

    from app.db.connessione import connetti
    from app.db.migrazioni import applica_migrazioni
    from app.notifiche import rapporto_seo as r

    oggi = date(2031, 3, 12)                  # giorni lontani: non si mescola con le altre prove
    ieri, prima = oggi - timedelta(days=1), oggi - timedelta(days=2)
    righe = [(ieri, "/blog/nuova-sabatini", "chatgpt.com", "chatgpt.com", "persona", "", 3),
             (ieri, "/blog/nuova-sabatini", "google.it", "", "persona", "", 2),
             (ieri, "/blog", "bing.com", "", "persona", "", 1),
             (prima, "/blog", "google.it", "", "persona", "", 4),
             (ieri, "/blog/nuova-sabatini", "diretto", "", "ia", "GPTBot", 5),
             (ieri, "/llms.txt", "diretto", "", "ia", "ClaudeBot", 1),
             (ieri, "/sitemap.xml", "diretto", "", "motore", "Googlebot", 2)]
    with connetti() as conn:
        applica_migrazioni(conn)
        conn.execute("DELETE FROM visite WHERE giorno BETWEEN %s AND %s", (oggi - timedelta(days=20), oggi))
        conn.execute("DELETE FROM notifiche_inviate WHERE nome = 'rapporto_seo'")
        for g, perc, prov, src, tipo, prog, n in righe:
            conn.execute("""INSERT INTO visite (giorno, percorso, provenienza, utm_source, visitatore, programma, conteggio)
                            VALUES (%s, %s, %s, %s, %s, %s, %s)""", (g, perc, prov, src, tipo, prog, n))
        conn.commit()
        d = r.raccogli(conn, oggi, "giornaliero")
    assert d["persone"] == {"corrente": 6, "precedente": 4, "sette": 10}
    assert d["blog"]["corrente"] == 6 and d["da_ia"]["corrente"] == 3
    assert d["da_google"] == {"corrente": 2, "precedente": 4, "sette": 6}
    assert d["da_bing"]["corrente"] == 1 and d["letture_ia"]["corrente"] == 6 and d["letture_motori"]["corrente"] == 2
    assert d["pagine"][0][0] == "/blog/nuova-sabatini"
    oggetto, testo, corpo = r.componi(d, oggi)
    assert "6 visite di persone" in oggetto and "3 dai motori IA" in oggetto
    assert "Search Console: non ancora collegato." in testo and "chatgpt.com [MOTORE IA]" in testo
    assert "IA GPTBot su /blog/nuova-sabatini: 5" in testo and "Nuove imprese registrate" in testo
    assert "+2 (+50%)" in testo and "(motore IA)" in corpo and "<script" not in corpo

    monkeypatch.delenv("RESEND_API_KEY", raising=False)
    monkeypatch.setenv("RAPPORTO_SEO", "giornaliero")
    monkeypatch.delenv("EMAIL_MATTEO", raising=False)
    assert r.invia_rapporto(oggi=oggi).startswith("non inviato: manca EMAIL_MATTEO")
    assert r.invia_rapporto(oggi=oggi) == "gia' inviato"                     # una volta sola al giorno
    monkeypatch.setenv("EMAIL_MATTEO", "matteo@esempio.it")
    domani = oggi + timedelta(days=1)
    assert r.invia_rapporto(oggi=domani) == "stampata a matteo@esempio.it"   # senza Resend: solo stampata
    assert "Search Console: non ancora collegato." in capsys.readouterr().out
    assert r.gia_inviato_adesso(domani)
    monkeypatch.setenv("RAPPORTO_SEO", "spento")
    assert r.invia_rapporto(oggi=oggi + timedelta(days=2)).startswith("spento")
    with connetti() as conn:
        conn.execute("DELETE FROM visite WHERE giorno BETWEEN %s AND %s", (oggi - timedelta(days=20), oggi))
        conn.execute("DELETE FROM notifiche_inviate WHERE nome = 'rapporto_seo'")
        conn.commit()
