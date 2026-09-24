"""Allegati: link trovati nella pagina, limiti di dimensione, robots.txt, testo dei PDF. Tutto senza rete (httpx.MockTransport)."""

import httpx
import pytest

from app.raccolta import scarica as modulo_scarica
from app.schede import allegati
from app.schede.allegati import Pausa, TroppoGrande, elabora_annuncio, estrai_testo, scarica_file, tipo_da_url, trova_allegati


def pdf_con_testo(testo: str) -> bytes:
    """Un PDF minimo, di una pagina, con una riga di testo."""
    flusso = f"BT /F1 12 Tf 72 720 Td ({testo}) Tj ET".encode()
    oggetti = [
        b"<< /Type /Catalog /Pages 2 0 R >>",
        b"<< /Type /Pages /Kids [3 0 R] /Count 1 >>",
        b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Contents 4 0 R /Resources << /Font << /F1 5 0 R >> >> >>",
        b"<< /Length %d >>\nstream\n" % len(flusso) + flusso + b"\nendstream",
        b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>",
    ]
    uscita, posizioni = b"%PDF-1.4\n", []
    for i, o in enumerate(oggetti, 1):
        posizioni.append(len(uscita))
        uscita += b"%d 0 obj\n" % i + o + b"\nendobj\n"
    xref = len(uscita)
    uscita += b"xref\n0 %d\n0000000000 65535 f \n" % (len(oggetti) + 1)
    for p in posizioni:
        uscita += b"%010d 00000 n \n" % p
    uscita += b"trailer\n<< /Size %d /Root 1 0 R >>\nstartxref\n%d\n%%%%EOF\n" % (len(oggetti) + 1, xref)
    return uscita


PDF = pdf_con_testo("Contributo a fondo perduto fino a 50.000 euro")

PAGINA = """<html><body>
<nav><a href="/">Home</a> <a href="/notizie">Notizie</a></nav>
<h1>Bando voucher digitali</h1>
<a href="/documenti/bando.pdf">Bando (PDF)</a>
<a href="documenti/bando.pdf#pagina=2">stesso bando, altra ancora</a>
<a href="/documents/1/2/Allegato+A.pdf/abc-123?t=17">Scarica</a>
<a href="/documenti/decreto.pdf.p7m">Decreto firmato</a>
<a href="https://altro.it/modulistica/Modulo_domanda.XLSX">Modulo di domanda</a>
<a href="/bandi/voucher/domande">Domande frequenti</a>
<a href="mailto:bandi@esempio.it">Scrivici</a>
<a href="#top">Torna su</a>
</body></html>"""


@pytest.fixture(autouse=True)
def robots_da_capo():
    modulo_scarica._robots.clear()
    yield
    modulo_scarica._robots.clear()


def test_tipo_da_url():
    assert tipo_da_url("https://x.it/a/Bando.PDF") == "pdf"
    assert tipo_da_url("https://x.it/a/decreto.pdf.p7m") == "p7m"
    assert tipo_da_url("https://x.it/documents/1/Allegato.docx/uuid?t=1") == "docx"
    assert tipo_da_url("https://x.it/bandi/pdf-e-moduli") is None
    # Regione Lombardia, Bandi Online: il nome del file sta nei parametri.
    url = "https://www.bandi.regione.lombardia.it/servizi/servizio/bandi/download/8a5a0034?fileName=Allegato%20A%20bando.pdf"
    assert tipo_da_url(url) == "pdf"
    assert allegati._nome_da_url(url) == "Allegato A bando.pdf"


def test_trova_allegati_nella_pagina():
    candidati = trova_allegati(PAGINA, "https://ente.it/bandi/voucher")
    assert [(c.tipo, c.url) for c in candidati] == [
        ("pdf", "https://ente.it/documenti/bando.pdf"),
        ("pdf", "https://ente.it/bandi/documenti/bando.pdf"),
        ("pdf", "https://ente.it/documents/1/2/Allegato+A.pdf/abc-123?t=17"),
        ("p7m", "https://ente.it/documenti/decreto.pdf.p7m"),
        ("xlsx", "https://altro.it/modulistica/Modulo_domanda.XLSX"),
        ("faq", "https://ente.it/bandi/voucher/domande"),
    ]
    assert candidati[0].nome == "Bando (PDF)"
    assert candidati[2].nome == "Allegato A.pdf"   # "Scarica" non dice nulla: si usa il nome del file


def client_finto(percorsi: dict[str, httpx.Response], robots: str = "") -> httpx.Client:
    richieste: list[str] = []

    def risponde(request: httpx.Request) -> httpx.Response:
        richieste.append(request.url.path)
        if request.url.path == "/robots.txt":
            return httpx.Response(200, text=robots) if robots else httpx.Response(404)
        return percorsi.get(request.url.path, httpx.Response(404))

    client = httpx.Client(transport=httpx.MockTransport(risponde), follow_redirects=True)
    client.richieste = richieste
    return client


def test_limite_dichiarato_dal_server(tmp_path, monkeypatch):
    client = client_finto({"/grande.zip": httpx.Response(200, content=b"x" * 5000)})
    with pytest.raises(TroppoGrande):
        scarica_file(client, "https://ente.it/grande.zip", tmp_path / "f", massimo=1000)
    assert not (tmp_path / "f").exists()


def test_limite_senza_dimensione_dichiarata_interrompe_lo_scaricamento(tmp_path):
    blocchi = (b"x" * 600 for _ in range(10))    # risposta a pezzi, senza Content-Length
    client = client_finto({"/flusso.zip": httpx.Response(200, content=blocchi)})
    with pytest.raises(TroppoGrande, match="interrotto"):
        scarica_file(client, "https://ente.it/flusso.zip", tmp_path / "f", massimo=1000)
    assert not (tmp_path / "f").exists()   # nessun file parziale su disco


def test_testo_dei_pdf_e_dei_p7m(tmp_path):
    assert "fondo perduto" in allegati.testo_pdf(PDF)
    assert allegati.testo_pdf(b"non sono un pdf") is None
    busta = tmp_path / "decreto.pdf.p7m"
    busta.write_bytes(b"0\x82\x01\x00firma" + PDF + b"\x00\x00certificato")
    assert "50.000 euro" in estrai_testo(busta, "p7m")


def test_elabora_annuncio(tmp_path, monkeypatch):
    monkeypatch.setattr(allegati, "MASSIMO_FILE", 20_000)
    pagina = """<a href="/doc/bando.pdf">Bando</a> <a href="/doc/enorme.zip">Tutto in un file</a>
    <a href="/riservato/modulo.docx">Modulo</a> <a href="/doc/finto.pdf">Finto</a> <a href="/faq-voucher">FAQ</a>
    <a href="/doc/sparito.pdf">Sparito</a>"""
    faq = "<html><body><nav>menu</nav><h1>FAQ</h1><p>Chi puo' partecipare?</p><p>Le PMI.</p><script>x()</script></body></html>"
    client = client_finto({
        "/bandi/voucher": httpx.Response(200, html=pagina),
        "/doc/bando.pdf": httpx.Response(200, content=PDF, headers={"content-type": "application/pdf"}),
        "/doc/enorme.zip": httpx.Response(200, content=b"z" * 30_000),
        "/riservato/modulo.docx": httpx.Response(200, content=b"docx"),
        "/doc/finto.pdf": httpx.Response(200, html="<p>Accedi per scaricare</p>"),
        "/faq-voucher": httpx.Response(200, html=faq),
    }, robots="User-agent: *\nDisallow: /riservato/\nCrawl-delay: 5\n")
    dormite: list[float] = []
    risultati = elabora_annuncio(client, 7, "https://ente.it/bandi/voucher#dettaglio", tmp_path,
                                 Pausa(client, minima=0, dormi=dormite.append))
    per_url = {r.url.rsplit("/", 1)[-1]: r for r in risultati}

    copia = risultati[0]   # prima riga: la copia della pagina dell'annuncio
    assert copia.tipo == "pagina" and copia.url == "https://ente.it/bandi/voucher" and "Tutto in un file" in copia.testo_estratto

    bando = per_url["bando.pdf"]
    assert bando.errore is None and bando.dimensione == len(PDF) and len(bando.impronta) == 64
    assert bando.percorso_locale == f"7/{bando.impronta[:12]}_bando.pdf"
    assert (tmp_path / bando.percorso_locale).read_bytes() == PDF
    assert "fondo perduto" in bando.testo_estratto

    assert per_url["enorme.zip"].errore.startswith("troppo grande")
    assert per_url["modulo.docx"].errore == "robots.txt del sito vieta il file"
    assert per_url["finto.pdf"].errore == "il link porta a una pagina web, non a un documento"
    assert per_url["sparito.pdf"].errore == "HTTP 404"
    faq_r = per_url["faq-voucher"]
    assert faq_r.tipo == "faq" and faq_r.percorso_locale.endswith(".html")
    assert "Chi puo' partecipare?\nLe PMI." in faq_r.testo_estratto and "menu" not in faq_r.testo_estratto

    assert "/riservato/modulo.docx" not in client.richieste          # robots.txt rispettato: mai chiesto
    assert dormite and max(dormite) > 4                               # Crawl-delay di 5 secondi rispettato
    assert sorted(p.name for p in (tmp_path / "7").iterdir()) == sorted(
        r.percorso_locale.split("/")[1] for r in (copia, bando, faq_r))   # nessun file parziale


def test_limite_di_file_per_annuncio(tmp_path, monkeypatch):
    monkeypatch.setattr(allegati, "MASSIMO_FILE_ANNUNCIO", 2)
    pagina = "".join(f'<a href="/d/{i}.pdf">Doc {i}</a>' for i in range(4))
    client = client_finto({"/b": httpx.Response(200, html=pagina),
                           **{f"/d/{i}.pdf": httpx.Response(200, content=pdf_con_testo(f"doc {i}")) for i in range(4)}})
    risultati = elabora_annuncio(client, 1, "https://ente.it/b", tmp_path, Pausa(client, minima=0, dormi=lambda s: None),
                                 gia_scaricati=1)
    assert [r.errore is None for r in risultati] == [True, True, False, False, False]   # pagina + 1 file
    assert "/d/1.pdf" not in client.richieste


def test_ignora_robots_vale_solo_per_il_sito_della_fonte(tmp_path):
    pagina = '<a href="/doc/a.pdf">A</a> <a href="https://altro.it/doc/b.pdf">B</a>'

    def risponde(request):
        if request.url.path == "/robots.txt":
            return httpx.Response(200, text="User-agent: *\nDisallow: /\n")
        if request.url.path == "/b":
            return httpx.Response(200, html=pagina)
        return httpx.Response(200, content=PDF)

    client = httpx.Client(transport=httpx.MockTransport(risponde))
    risultati = elabora_annuncio(client, 2, "https://ente.it/b", tmp_path, Pausa(client, minima=0, dormi=lambda s: None),
                                 ignora_robots=True)
    assert [r.errore for r in risultati] == [None, None, "robots.txt del sito vieta il file"]   # pagina, a.pdf, b.pdf
