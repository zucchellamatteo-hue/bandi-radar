"""Correzioni tecniche della valutazione SEO/GEO del 09/10/2026: title e description, dati strutturati, intestazioni
di sicurezza e cache, IndexNow (sempre con una richiesta finta: nessuna chiamata vera), landing in memoria, tabelle."""

import json
import os
import re
import time
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app import articoli
from app.pubblico import blog, indexnow, landing, seo

db = pytest.mark.skipif(not os.environ.get("PGHOST"), reason="serve un database Postgres di prova (PGHOST)")
RADICE = Path(__file__).resolve().parents[1]

TITOLI = [
    "Iperammortamento 2026: quanto si risparmia su macchinari, software e fotovoltaico (e perché non vale per l'IRAP)",
    "Ecobonus imprese 2026: detrazione del 36% per i lavori di risparmio energetico, cosa entra, fisco e confronto con il Conto Termico",
    "Fondo di Garanzia PMI 2026: lo Stato garantisce l'80% del prestito per investimenti (anche software)",
    "Sismabonus 2026 per le imprese: 36% sui lavori antisismici, fino a 34.560 euro per unità. Guida con esempi e fisco",
    "Art Bonus 2026 per le imprese: dona alla cultura e recupera il 65% in F24, senza tasse sul credito",
    "Breve",
]


def _parole_intere(breve: str, intero: str) -> bool:
    """Ogni parola del titolo breve (tolto il marchio) e' una parola intera del titolo originale."""
    originali = set(re.findall(r"[\w'’.%-]+", intero))
    return all(p in originali for p in re.findall(r"[\w'’.%-]+", breve.replace(seo.MARCHIO, "")))


# --- 1. title e description ---------------------------------------------------------------------------------------

@pytest.mark.parametrize("titolo", TITOLI)
def test_title_al_massimo_60_caratteri_senza_parole_tagliate(titolo):
    t = seo.titolo_pagina(titolo)
    assert len(t) <= 60 and "…" not in t and "..." not in t
    assert _parole_intere(t, titolo), t
    assert not re.search(r"\b(e|su|per|di|del|a|il|la)( \| bandinQiaro)?$", t), t      # niente parola debole in fondo
    assert seo.MARCHIO in seo.titolo_pagina("Breve")


def test_title_con_il_titolo_per_google():
    assert seo.titolo_pagina(TITOLI[0], "Iperammortamento 2026: risparmio, software e IRAP") == \
        "Iperammortamento 2026: risparmio, software e IRAP"                       # 49 + marchio = 63: senza marchio
    assert seo.titolo_pagina(TITOLI[0], "Iperammortamento 2026") == "Iperammortamento 2026 | bandinQiaro"
    assert seo.titolo_pagina(TITOLI[0]) == "Iperammortamento 2026: quanto si risparmia | bandinQiaro"
    with pytest.raises(articoli.ErroreArticoli):
        articoli._controlla({"titolo_seo": "x" * 71}, False)
    assert articoli._controlla({"titolo_seo": "  Breve   titolo "}, False) == {"titolo_seo": "Breve titolo"}
    assert articoli._controlla({"titolo_seo": "  "}, False) == {"titolo_seo": None}


def test_description_tra_140_e_160_caratteri():
    lungo = ("Un macchinario 4.0 da 200.000 euro vale circa 86.400 euro di IRES in meno. Beni e software ammessi dagli "
             "allegati IV e V, il nodo cloud/SaaS, perché l'IRAP non si riduce e i passi sul GSE.")
    d = seo.descrizione_meta(lungo)
    assert 140 <= len(d) <= 160 and d.endswith("…") and _parole_intere(d.rstrip("…"), lungo)
    frasi = ("Art Bonus: credito d'imposta del 65% sulle donazioni in denaro alla cultura pubblica, fino al 5 per mille dei "
             "ricavi, in tre quote F24 (codice 6842). Non tassato IRES né IRAP. Esempi.")
    assert seo.descrizione_meta(frasi).endswith("(codice 6842).")                   # si chiude a fine frase
    corto = "Contributo del 50% per le PMI che comprano software in cloud, con esempi in euro e le scadenze del bando."
    d = seo.descrizione_meta(corto, "Aggiornato il 07/10/2026, con le fonti ufficiali.")
    assert 140 <= len(d) <= 160 and d.startswith(corto)
    assert seo.descrizione_meta("x " * 30) == ("x " * 30).strip()                 # troppo corta e senza coda: com'e'


# --- 2. dati strutturati ------------------------------------------------------------------------------------------

def _articolo(**altro) -> dict:
    a = {"id": 1, "titolo": TITOLI[0], "slug": "iperammortamento-2026-guida-completa", "sommario": "Un sommario. " * 15,
         "corpo": "## Quanto vale\nTesto.\n\n## Domande frequenti\n### Vale anche per IRAP?\nNo.", "fonti": [],
         "bando_id": None, "misura_id": None, "autore": None, "stato": "pubblicato", "titolo_seo": None,
         "pubblicato_il": datetime(2026, 10, 7, 21, 57, tzinfo=timezone.utc),
         "aggiornato_il": datetime(2026, 10, 7, 15, 41, tzinfo=timezone.utc)}
    return a | altro


def _json_ld(html: str) -> dict:
    return json.loads(re.search(r'<script type="application/ld\+json">(.*?)</script>', html, re.S).group(1))


def test_dati_strutturati_dell_articolo(monkeypatch):
    monkeypatch.setenv("SITO_URL", "https://bandinqiaro.it")
    monkeypatch.setenv("BLOG_PUBBLICO", "1")
    monkeypatch.setenv("AUTORE_ARTICOLI", "Redazione bandinQiaro – contenuti verificati da un dottore commercialista")
    h = blog.pagina_articolo(None, _articolo())
    grafo = _json_ld(h)["@graph"]
    art = next(o for o in grafo if o["@type"] == "Article")
    assert len(art["headline"]) <= 110 and _parole_intere(art["headline"], TITOLI[0])
    assert art["headline"] == "Iperammortamento 2026: quanto si risparmia su macchinari, software e fotovoltaico"
    assert art["dateModified"] >= art["datePublished"] == "2026-10-07T21:57:00+00:00"        # mai prima della pubblicazione
    assert art["author"] == {"@type": "Organization", "name": "Redazione bandinQiaro", "url": "https://bandinqiaro.it/blog",
                             "parentOrganization": {"@id": "https://bandinqiaro.it/#organizzazione"}}
    assert '<meta property="og:type" content="article">' in h and 'content="website"' not in h
    assert '<meta property="article:published_time" content="2026-10-07T21:57:00+00:00">' in h
    assert '<meta property="article:modified_time" content="2026-10-07T21:57:00+00:00">' in h
    assert '<time datetime="2026-10-07T21:57:00+00:00">07/10/2026</time>' in h
    titolo = re.search(r"<title>(.*?)</title>", h).group(1)
    descr = re.search(r'<meta name="description" content="(.*?)">', h).group(1)
    assert len(titolo) <= 60 and 140 <= len(descr) <= 160
    assert next(o for o in grafo if o["@type"] == "FAQPage")["mainEntity"][0]["name"] in h   # coerente con la pagina
    # con il titolo per Google: headline intera se sta in 110, altrimenti il titolo per Google
    h = blog.pagina_articolo(None, _articolo(titolo_seo="Iperammortamento 2026: risparmio, software e IRAP"))
    assert next(o for o in _json_ld(h)["@graph"] if o["@type"] == "Article")["headline"] == \
        "Iperammortamento 2026: risparmio, software e IRAP"
    assert "<title>Iperammortamento 2026: risparmio, software e IRAP</title>" in h
    assert f"<h1>{TITOLI[0].replace(chr(39), '&#x27;')}</h1>" in h                   # in pagina il titolo intero
    corto = blog.pagina_articolo(None, _articolo(titolo="Nuova Sabatini 2026", aggiornato_il=datetime(2026, 10, 9, tzinfo=timezone.utc)))
    art = next(o for o in _json_ld(corto)["@graph"] if o["@type"] == "Article")
    assert art["headline"] == "Nuova Sabatini 2026" and art["dateModified"] == "2026-10-09T00:00:00+00:00"


def test_autore_persona_o_redazione():
    assert seo.autore("Mario Rossi, commercialista") == {"@type": "Person", "name": "Mario Rossi",
                                                          "description": "Mario Rossi, commercialista"}
    for redazione in (None, "", articoli.AUTORE_SEGNAPOSTO, "Redazione bandinQiaro"):
        a = seo.autore(redazione)
        assert a["@type"] == "Organization" and a["name"] == "Redazione bandinQiaro"


def test_data_modifica_mai_prima_della_pubblicazione():
    prima, dopo = datetime(2026, 10, 7, 15, tzinfo=timezone.utc), datetime(2026, 10, 7, 22, tzinfo=timezone.utc)
    assert blog.data_modifica({"aggiornato_il": prima, "pubblicato_il": dopo}) == dopo
    assert blog.data_modifica({"aggiornato_il": dopo, "pubblicato_il": prima}) == dopo
    assert blog.data_modifica({"aggiornato_il": prima, "pubblicato_il": None}) == prima


# --- 3. intestazioni di sicurezza e cache -------------------------------------------------------------------------

def test_caddyfile_con_le_intestazioni_di_sicurezza():
    testo = (RADICE / "deploy" / "Caddyfile").read_text(encoding="utf-8")
    blocco = re.search(r"\{\$SITE_ADDRESS\} \{(.*?)\n\}", testo, re.S).group(1)
    assert 'Strict-Transport-Security "max-age=31536000"' in blocco and "preload" not in blocco.split("header {")[1]
    for riga in ('X-Content-Type-Options "nosniff"', 'Referrer-Policy "strict-origin-when-cross-origin"',
                 'X-Frame-Options "SAMEORIGIN"', "Permissions-Policy", "-Server"):
        assert riga in blocco, riga
    # l'anteprima del blog in plancia e' un iframe srcDoc: non scarica nulla, X-Frame-Options non la tocca
    assert 'srcDoc={anteprima}' in (RADICE / "plancia" / "src" / "pagine" / "Articoli.tsx").read_text(encoding="utf-8")


def test_cache_dei_file_per_i_motori_e_delle_immagini():
    from app.main import app

    c = TestClient(app)
    assert c.get("/robots.txt").headers["cache-control"] == "public, max-age=300"
    assert c.get("/favicon.svg").headers["cache-control"] == "public, max-age=604800"
    assert c.get("/immagini/anteprima.png").headers["cache-control"] == "public, max-age=604800"


# --- 4. IndexNow --------------------------------------------------------------------------------------------------

CHIAVE = "0123456789abcdef0123456789abcdef"


@pytest.fixture
def finta(monkeypatch):
    """IndexNow acceso con una richiesta finta che registra cosa si sarebbe mandato (nessuna chiamata vera)."""
    chiamate = []
    monkeypatch.setenv("INDEXNOW_KEY", CHIAVE)
    monkeypatch.setenv("BLOG_PUBBLICO", "1")
    monkeypatch.setenv("SITO_URL", "https://bandinqiaro.it")
    monkeypatch.setattr(indexnow, "_post", lambda url, dati: chiamate.append((url, dati)) or 200)
    return chiamate


def test_indexnow_invia_host_chiave_e_indirizzi(finta):
    esito = indexnow.invia(["https://bandinqiaro.it/blog/a", "https://bandinqiaro.it/blog/a", "https://altro.it/x"])
    assert finta == [("https://api.indexnow.org/indexnow", {
        "host": "bandinqiaro.it", "key": CHIAVE, "keyLocation": f"https://bandinqiaro.it/{CHIAVE}.txt",
        "urlList": ["https://bandinqiaro.it/blog/a"]})]
    assert "1 indirizzi, risposta 200" in esito


def test_indexnow_spento_senza_chiave_o_con_il_blog_chiuso(finta, monkeypatch):
    monkeypatch.setenv("BLOG_PUBBLICO", "0")
    monkeypatch.setenv("PAGINA_PUBBLICA", "0")
    assert not indexnow.attivo() and "non attivo" in indexnow.invia(["https://bandinqiaro.it/blog"])
    assert indexnow.avvisa_in_disparte(["https://bandinqiaro.it/blog"]) is None
    monkeypatch.setenv("PAGINA_PUBBLICA", "1")
    assert indexnow.attivo()
    for sbagliata in ("", "corta", "con spazi dentro 123", "a/b" * 5):
        monkeypatch.setenv("INDEXNOW_KEY", sbagliata)
        assert not indexnow.attivo() and indexnow.file_chiave(f"{sbagliata}.txt") is None
    assert finta == []


def test_indexnow_errore_di_rete_non_blocca(finta, monkeypatch):
    def guasto(url, dati):
        raise OSError("rete giu'")
    monkeypatch.setattr(indexnow, "_post", guasto)
    assert "errore di rete" in indexnow.invia(["https://bandinqiaro.it/blog"])
    monkeypatch.setattr(indexnow, "_post", lambda url, dati: 403)
    assert "403 (chiave non valida" in indexnow.invia(["https://bandinqiaro.it/blog"])


def test_indexnow_quando_cambia_un_articolo(finta):
    pubb, bozza = {"slug": "a", "stato": "pubblicato"}, {"slug": "a", "stato": "bozza"}
    assert indexnow.articolo_cambiato(bozza, bozza) is None                               # bozze: nessun avviso
    for prima, dopo in ((bozza, pubb), (pubb, pubb), (pubb, bozza), (pubb, {"slug": "a", "stato": "archiviato"})):
        indexnow.articolo_cambiato(prima, dopo).join(5)
    assert len(finta) == 4 and all(d["urlList"] == ["https://bandinqiaro.it/blog/a", "https://bandinqiaro.it/blog"]
                                   for _, d in finta)
    indexnow.articolo_cambiato(pubb, {"slug": "b", "stato": "pubblicato"}).join(5)         # indirizzo cambiato
    assert finta[-1][1]["urlList"][-1] == "https://bandinqiaro.it/blog/a"


def test_file_della_chiave_e_robots(finta, monkeypatch):
    from app.main import app

    c = TestClient(app)
    r = c.get(f"/{CHIAVE}.txt")
    assert r.status_code == 200 and r.text == CHIAVE
    assert c.get("/altrachiave1234.txt").status_code == 404
    assert f"Allow: /{CHIAVE}.txt$" in c.get("/robots.txt").text
    monkeypatch.delenv("INDEXNOW_KEY")
    assert c.get(f"/{CHIAVE}.txt").status_code == 404 and ".txt$" not in c.get("/robots.txt").text


# --- 5. landing in memoria ----------------------------------------------------------------------------------------

def test_landing_pronta_in_memoria_senza_database(monkeypatch):
    from app import main

    landing._cache.clear()
    composte = []
    monkeypatch.setattr(landing, "_componi", lambda conn: composte.append(1) or f"<html>pagina {len(composte)}</html>")
    landing._cache["dati"] = {"finto": True}
    assert landing.presentazione(None) == "<html>pagina 1</html>"
    assert landing.presentazione(None) == "<html>pagina 1</html>" and len(composte) == 1      # dalla memoria

    def niente_database():
        raise AssertionError("con la pagina in memoria non si apre il database")
    monkeypatch.setattr(main, "connetti", niente_database)
    inizio = time.perf_counter()
    r = TestClient(main.app).get("/presentazione")
    assert r.text == "<html>pagina 1</html>" and time.perf_counter() - inizio < 0.3
    monkeypatch.setenv("TITOLARE_SITO", "Studio Prova")                                       # cambia il .env: si rifa'
    assert landing.da_cache() is None and landing.presentazione(None) == "<html>pagina 2</html>"
    landing._cache["pagina"] = (time.monotonic() - 1,) + landing._cache["pagina"][1:]          # scaduta: si rifa'
    assert landing.presentazione(None) == "<html>pagina 3</html>"
    landing._cache.clear()


def test_numeri_scaduti_si_ricalcolano_in_disparte(monkeypatch):
    landing._cache.clear()
    calcoli, in_disparte = [], []
    monkeypatch.setattr(landing, "_calcola", lambda conn: calcoli.append(1) or {"n": len(calcoli)})
    monkeypatch.setattr(landing, "_ricalcola_in_disparte", lambda: in_disparte.append(1))
    assert landing.numeri(None) == {"n": 1}                                  # la prima volta si aspetta il calcolo
    landing._cache["scade"] = 0                                              # scaduti
    assert landing.numeri(None) == {"n": 1} and in_disparte == [1] and calcoli == [1]   # subito i vecchi
    landing._cache.clear()


def test_pagina_senza_numeri_non_resta_in_memoria(monkeypatch):
    landing._cache.clear()
    monkeypatch.setattr(landing, "_componi", lambda conn: "<html>senza numeri</html>")
    landing.presentazione(None)
    assert landing.da_cache() is None


# --- 6. tabelle negli articoli ------------------------------------------------------------------------------------

def test_tabelle_anche_senza_barre_ai_lati():
    h = articoli.in_html("Scaglioni:\n\nScaglione | Maggiorazione\n--- | ---:\nfino a 2,5 milioni | **180%**\n"
                         "da 2,5 a 10 milioni | 100%\n\nFine.")
    assert "<th>Scaglione</th><th>Maggiorazione</th>" in h and "<td><strong>180%</strong></td>" in h
    assert h.count("<tr>") == 3 and "---" not in h and "<p>Fine.</p>" in h
    testo = articoli.in_html("Scegli A | B secondo i casi.\nAltra riga.")
    assert "<table" not in testo and "A | B" in testo                      # un "|" nel testo non fa una tabella
    misto = articoli.in_html("|Voce|Valore|\n|---|---|\n|a|1|")
    assert "<th>Voce</th>" in misto and "<td>1</td>" in misto


# --- con il database: pagina vera, cache e IndexNow alla pubblicazione -------------------------------------------

@db
def test_articolo_pubblicato_seo_cache_e_indexnow(finta):
    from conftest import accesso_di_prova

    from app.db.connessione import connetti
    from app.db.migrazioni import applica_migrazioni
    from app.main import app

    with connetti() as conn:
        applica_migrazioni(conn)
        conn.commit()
    c = TestClient(app)
    admin = accesso_di_prova("admin")
    sigla = uuid.uuid4().hex[:6]
    a = c.post("/api/articoli", auth=admin, json={"titolo": TITOLI[0] + f" {sigla}", "sommario": "Sommario. " * 20,
                                                  "corpo": "## Uno\nTesto.\n\nA | B\n--- | ---\n1 | 2",
                                                  "titolo_seo": f"Iperammortamento {sigla}"}).json()
    assert a["titolo_seo"] == f"Iperammortamento {sigla}"
    assert finta == []                                                     # bozza: nessun avviso
    with connetti() as conn, conn.cursor() as cur:                         # scritto ieri, pubblicato oggi
        cur.execute("UPDATE articoli SET aggiornato_il = now() - interval '1 day' WHERE id = %s", (a["id"],))
        conn.commit()
    c.patch(f"/api/articoli/{a['id']}", auth=admin, json={"stato": "pubblicato"})
    for _ in range(50):
        if finta:
            break
        time.sleep(0.1)
    assert finta and finta[0][1]["urlList"] == [f"https://bandinqiaro.it/blog/{a['slug']}", "https://bandinqiaro.it/blog"]
    r = c.get(f"/blog/{a['slug']}")
    assert r.headers["cache-control"] == "public, max-age=300" and "<table>" in r.text
    art = next(o for o in _json_ld(r.text)["@graph"] if o["@type"] == "Article")
    assert art["dateModified"] >= art["datePublished"]
    assert f"<title>Iperammortamento {sigla} | bandinQiaro</title>" in r.text
    assert c.get("/blog").headers["cache-control"] == "public, max-age=300"

    # invio del giorno: una volta sola, con le pagine cambiate
    with connetti() as conn:
        with conn.cursor() as cur:
            cur.execute("DELETE FROM notifiche_inviate WHERE nome = %s", (indexnow.NOME_INVIO,))
        conn.commit()
        prima = len(finta)
        esito = indexnow.invio_del_giorno(conn)
        assert "risposta 200" in esito and f"https://bandinqiaro.it/blog/{a['slug']}" in finta[-1][1]["urlList"]
        assert indexnow.gia_fatto_oggi(conn) and indexnow.invio_del_giorno(conn) is None and len(finta) == prima + 1
        domani = datetime.now().date() + timedelta(days=1)
        assert "risposta 200" in indexnow.invio_del_giorno(conn, domani)        # cambiato il giorno dell'ultimo invio: si ripete
        dopodomani = domani + timedelta(days=1)
        assert "nessuna pagina" in indexnow.invio_del_giorno(conn, dopodomani)  # niente di nuovo: non si manda
        assert len(finta) == prima + 2
        with conn.cursor() as cur:
            cur.execute("DELETE FROM notifiche_inviate WHERE nome = %s", (indexnow.NOME_INVIO,))
        conn.commit()
    c.delete(f"/api/articoli/{a['id']}", auth=admin)
