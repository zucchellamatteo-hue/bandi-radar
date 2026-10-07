"""Correzioni della diagnosi "perche' manca il testo ufficiale" (PIANO_QUALITA azione 2, 08/10/2026).

Ogni regola ha un caso vero, ridotto all'essenziale: pagine e intestazioni dei siti dove il testo del bando si perdeva.
Senza rete (httpx.MockTransport); i test sul database girano solo con PGHOST (Postgres di prova vuoto).
"""

import io
import os
import zipfile

import httpx
import pytest

from app.raccolta import scarica as modulo_scarica
from app.schede import allegati
from app.schede.allegati import (
    Pausa, categoria_allegato, domini_plone, e_link_a_file, elabora_pagina, pagine_atto, sottopagine,
    tipo_dal_contenuto, trova_allegati, usa_plone,
)
from app.schede.bandi import _e_pagina_di_servizio, url_chiave
from app.schede.pagina_ufficiale import valuta_pagina

from test_allegati import pdf_con_testo


@pytest.fixture(autouse=True)
def senza_robots(monkeypatch):
    monkeypatch.setattr(modulo_scarica, "_robots", {})


def client(percorsi: dict[str, httpx.Response]) -> httpx.Client:
    richieste: list[str] = []

    def risponde(request: httpx.Request) -> httpx.Response:
        richieste.append(str(request.url))
        if request.url.path == "/robots.txt":
            return httpx.Response(404)
        return percorsi.get(str(request.url), httpx.Response(404))

    c = httpx.Client(transport=httpx.MockTransport(risponde), follow_redirects=True)
    c.richieste = richieste
    return c


def pausa(c):
    return Pausa(c, minima=0, dormi=lambda s: None)


def docx(testo: str) -> bytes:
    uscita = io.BytesIO()
    with zipfile.ZipFile(uscita, "w") as z:
        z.writestr("[Content_Types].xml", "<Types/>")
        z.writestr("word/document.xml", f"<w:document><w:body><w:p><w:r><w:t>{testo}</w:t></w:r></w:p></w:body></w:document>")
    return uscita.getvalue()


# --- formato dal contenuto (myCIVIS, Provincia di Bolzano) ------------------------------------------------------

def test_formato_dai_primi_byte_o_da_content_disposition():
    assert tipo_dal_contenuto(pdf_con_testo("x")) == "pdf"
    assert tipo_dal_contenuto(b"0\x82\x01\x00firma" + pdf_con_testo("x")) == "p7m"       # PDF in una busta di firma
    assert tipo_dal_contenuto(docx("Bando")) == "docx"
    assert tipo_dal_contenuto(b"\xd0\xcf\x11\xe0\xa1\xb1\x1a\xe1" + b"\x00" * 100) == "doc"
    assert tipo_dal_contenuto(b"\xd0\xcf\x11\xe0\xa1\xb1\x1a\xe1", 'attachment; filename="Piano finanziario.xls"') == "xls"
    assert tipo_dal_contenuto(b"\x00\x01dati", "attachment; filename*=UTF-8''Avviso%20pubblico.odt") == "odt"
    assert tipo_dal_contenuto(b"<html><body>Accedi</body></html>") is None


def test_mycivis_pdf_mandato_come_octet_stream_si_legge(tmp_path):
    # 2113 (mycivis.civis.bz.it): i documenti sono File/download.aspx?...&Id=<GUID>, Content-Type application/octet-stream.
    pagina = "https://mycivis.civis.bz.it/it/Services/ServiceDetail/?id=1697"
    doc = ("https://mycivis.civis.bz.it/File/download.aspx?Entity=msdyn_kbattachment&Attribute=msdyn_fileattachment"
           "&Id=dcd3e635-f800-f111-8406-000d3aab3772")
    html = f'<main><h1>Contributi per la zootecnia</h1><a href="{doc}">Criteri per la concessione dei contributi</a></main>'
    c = client({pagina: httpx.Response(200, html=html),
                doc: httpx.Response(200, content=pdf_con_testo("Criteri contributi provinciali"),
                                    headers={"content-type": "application/octet-stream",
                                             "content-disposition": 'attachment; filename="Kriterien Criteri.pdf"'})})
    risultati = elabora_pagina(c, "b2113", pagina, tmp_path, pausa(c))
    documento = risultati[1]
    assert documento.tipo == "pdf" and "Criteri contributi provinciali" in documento.testo_estratto
    assert documento.percorso_locale.endswith(".pdf")


def test_rilettura_dei_file_altro_gia_scaricati(tmp_path, monkeypatch):
    # Come --rileggi-altro: il file salvato come "...download.aspx.altro" e' un PDF.
    (tmp_path / "b2113").mkdir()
    (tmp_path / "b2113" / "4d1116c88154_download.aspx.altro").write_bytes(pdf_con_testo("Criteri di concessione"))
    percorso = tmp_path / "b2113" / "4d1116c88154_download.aspx.altro"
    tipo = tipo_dal_contenuto(percorso.read_bytes())
    assert tipo == "pdf" and "Criteri di concessione" in allegati.estrai_testo(percorso, tipo)


# --- link a file senza estensione ---------------------------------------------------------------------------

def test_link_a_file_senza_estensione_dei_siti_della_pa():
    html = """<main>
      <a href="/allegato.aspx?pk=68108">Deliberazione della Giunta regionale n. 526 del 13 maggio 2024</a>
      <a href="https://www301.regione.toscana.it/bancadati/atti/Contenuto.xml?id=5530219&amp;nomeFile=Decreto+n.20043+del+03-09-2026">decreto 20043 del 3 settembre 2026</a>
      <a href="https://finlombarda.it/it/attachments/file/view?hash=6d9c0f31467c4cd05670e7df21c55ba6281c66092c0eee5044e278399&amp;canCache=0">02. Decreto 1266-2026-All.to_A_testo del bando</a>
      <a href="https://www.chpe.camcom.it/output_allegato.php?id=1445119">Bando</a>
      <a href="https://www.regione.vda.it/notizie.aspx?pk=5">Una notizia</a>
    </main>"""
    trovati = trova_allegati(html, "https://www.regione.vda.it/agricoltura/aiuti_trasporto_siero_i.aspx")
    assert [(c.tipo, c.url.split("/")[2]) for c in trovati] == [
        ("file", "www.regione.vda.it"), ("file", "www301.regione.toscana.it"), ("file", "finlombarda.it"),
        ("file", "www.chpe.camcom.it")]
    assert not e_link_a_file("https://www.regione.vda.it/notizie.aspx?pk=5")


def test_nome_dal_parametro_nomefile_della_toscana():
    lungo = "bando annualità 2026, che attua dell'intervento SRA16 " * 5    # testo del link oltre 200 caratteri
    html = (f'<main><a href="https://www301.regione.toscana.it/bancadati/atti/Contenuto.xml?id=5530223&amp;'
            f'nomeFile=Decreto+n.20043+del+03-09-2026-+Allegato+A">{lungo}</a></main>')
    c = trova_allegati(html, "https://www.regione.toscana.it/-/contributi")[0]
    assert c.nome == "Decreto n.20043 del 03-09-2026- Allegato A"
    assert categoria_allegato(c.nome, c.url, c.tipo) in ("bando", "decreto")


def test_atto_della_toscana_non_e_un_indirizzo_di_dati():
    chiave = url_chiave("https://www301.regione.toscana.it/bancadati/atti/Contenuto.xml?id=5507044&nomeFile=Delibera+n.342")
    assert not _e_pagina_di_servizio(chiave)
    assert _e_pagina_di_servizio(url_chiave("https://www.regione.toscana.it/opendata/bandi.xml"))


def test_pagina_ufficiale_che_e_un_atto_senza_estensione_si_scarica_come_documento(tmp_path):
    atto = "https://www301.regione.toscana.it/bancadati/atti/Contenuto.xml?id=5507044&nomeFile=Delibera+n.342+del+23-03-2026"
    c = client({atto: httpx.Response(200, content=pdf_con_testo("Delibera di giunta 342"),
                                     headers={"content-type": "application/pdf"})})
    risultati = elabora_pagina(c, "b922", atto, tmp_path, pausa(c))
    assert [(r.tipo, r.errore) for r in risultati] == [("pdf", None)]
    assert "Delibera di giunta 342" in risultati[0].testo_estratto


# --- ordine prima del limite di 30 file ---------------------------------------------------------------------

def test_bando_e_decreti_prima_delle_graduatorie_nel_limite_dei_file(tmp_path, monkeypatch):
    # Calabria 1611: le graduatorie in cima alla pagina riempivano i posti e l'avviso restava fuori.
    monkeypatch.setattr(allegati, "MASSIMO_FILE_ANNUNCIO", 3)
    pagina = "https://calabriaeuropa.regione.calabria.it/bando"
    html = "<main>" + "".join(f'<a href="/g/graduatoria-{i}.pdf">Graduatoria provvisoria {i}</a>' for i in range(4)) + \
        '<a href="/m/modulo-domanda.pdf">Modulo di domanda</a><a href="/d/avviso.pdf">Avviso pubblico</a>' \
        '<a href="/d/ddg-123.pdf">Decreto di approvazione</a></main>'
    percorsi = {pagina: httpx.Response(200, html=html)}
    for nome in ["g/graduatoria-0", "g/graduatoria-1", "g/graduatoria-2", "g/graduatoria-3", "m/modulo-domanda", "d/avviso", "d/ddg-123"]:
        percorsi[f"https://calabriaeuropa.regione.calabria.it/{nome}.pdf"] = httpx.Response(
            200, content=pdf_con_testo(nome), headers={"content-type": "application/pdf"})
    c = client(percorsi)
    risultati = elabora_pagina(c, "b1611", pagina, tmp_path, pausa(c))
    scaricati = [r.nome for r in risultati[1:] if r.errore is None]
    assert scaricati == ["Avviso pubblico", "Decreto di approvazione", "Graduatoria provvisoria 0"]


# --- pagine ASP.NET tutte dentro un <form> ------------------------------------------------------------------

VDA = """<html><body><form method="post" action="./aiuti_trasporto_siero_i.aspx" id="form1">
<input type="hidden" name="__VIEWSTATE" value="/wEPDwUENTM4MWRk" />
<header><a href="/">Regione Autonoma Valle d'Aosta</a></header>
<div id="cerca"><form action="/ricerca.aspx"><input name="q"><button>Cerca</button></form></div>
<div class="contenuto"><h1>Aiuti per il trasporto del siero</h1>
<p>Aiuti per i costi del trasporto del siero residuo delle lavorazioni lattiero casearie presso appositi centri di
smaltimento o lavorazione per i primi centoventi chilometri a partire dalla sede del caseificio, ai sensi dell'art. 13
comma 1 lettera b) della l.r. 17/2016.</p>
<p>Possono beneficiare del contributo in oggetto le micro, piccole e medie imprese, di cui all'allegato I del
regolamento (UE) 2022/2472, operanti sul territorio regionale nel settore della trasformazione e commercializzazione
dei prodotti lattiero-caseari.</p>
<p>Il contributo e' concesso, nei limiti degli stanziamenti di bilancio, sino al 100 per cento della spesa ammissibile,
sulla base degli importi dichiarati nella domanda. Le domande di aiuto devono essere trasmesse dal 15 novembre al 15
dicembre di ogni anno.</p>
<ul class="allegati"><li><a href="/allegato.aspx?pk=68108">Deliberazione della Giunta regionale n. 526 del 13 maggio 2024</a></li>
<li><a href="/allegato.aspx?pk=78805">Domanda aiuto trasporto siero</a></li></ul></div>
<footer>Piazza Deffeyes 1, Aosta</footer>
</form></body></html>"""


def test_pagina_asp_net_dentro_il_form_non_e_vuota():
    testo = allegati.testo_html(VDA)
    assert "Possono beneficiare del contributo" in testo and "Cerca" not in testo
    ok, perche = valuta_pagina(VDA, "https://www.regione.vda.it/agricoltura/aiuti_trasporto_siero_i.aspx")
    assert ok and "2 documenti" in perche


def test_moduli_piccoli_si_tolgono_ancora():
    html = ("<html><body><main><h1>Bando</h1><p>" + "Testo del bando. " * 30 + "</p></main>"
            "<form action='/newsletter'><p>Iscriviti alla newsletter</p><input name='email'></form></body></html>")
    assert "newsletter" not in allegati.testo_html(html)


# --- falso login --------------------------------------------------------------------------------------------

def test_casella_di_accesso_non_fa_login_se_la_pagina_ha_i_documenti():
    # Finmolise: campo password nella testata del sito, 13 documenti del bando nella pagina.
    documenti = "".join(f'<a href="/wp-content/uploads/2026/03/avviso-{i}.pdf">Allegato {i}</a>' for i in range(3))
    html = (f'<html><body><div class="login"><input type="text" name="u"><input type="password" name="p"></div>'
            f'<main><h1>Avviso Microcredito Molise</h1>{documenti}</main></body></html>')
    assert valuta_pagina(html, "https://www.finmolise.it/avviso-microcredito/")[0]
    solo_uno = html.replace(documenti, '<a href="/avviso.pdf">Avviso</a>')
    assert valuta_pagina(solo_uno, "https://www.finmolise.it/avviso-microcredito/") == (False, "pagina di accesso (login)")


# --- Plone deciso dal sito, non dalla fonte -----------------------------------------------------------------

class FonteFinta:
    def __init__(self, url, plone):
        self.url, self.documenti_plone = url, plone


def test_plone_deciso_dal_dominio_della_pagina():
    domini = domini_plone([FonteFinta("https://imprese.regione.emilia-romagna.it/leggi-atti-bandi/tutti-i-bandi", True),
                           FonteFinta("https://www.vr.camcom.it/it/contributi", True),
                           FonteFinta("https://www.mimit.gov.it/it/incentivi", False)])
    assert domini == {"regione.emilia-romagna.it", "vr.camcom.it"}
    assert usa_plone("https://fesr.regione.emilia-romagna.it/opportunita/bando-x", domini)   # arrivato dal catalogo
    assert usa_plone("https://www.vr.camcom.it/it/bando", domini)
    assert not usa_plone("https://www.vi.camcom.it/it/bando", domini)          # camcom.it non e' tutto Plone
    assert not usa_plone("https://www.mimit.gov.it/it/incentivi/x", domini)


# --- pagine "atto" ------------------------------------------------------------------------------------------

def test_pagine_atto_del_mimit_prima_le_piu_recenti():
    # 1125, area di crisi di Venezia: i decreti stanno su /it/normativa/..., non sulla pagina della misura.
    html = """<html><body><nav><a href="/it/normativa/decreti-ministeriali">Normativa</a></nav><main>
    <a href="/it/normativa/notifiche-e-avvisi/avviso-direttoriale-del-5-settembre-2025-legge-181-89-chiusura-degli-sportelli">Avviso del Direttore generale del 5 settembre 2025</a>
    <a href="/it/normativa/circolari-note-direttive-e-atti-di-indirizzo/circolare-direttoriale-5-settembre-2025-n-2006-criteri">circolare n. 2006 del 5 settembre 2025</a>
    <a href="/it/normativa/notifiche-e-avvisi/avviso-direttoriale-18-novembre-2025---riapertura-sportelli-aree-di-crisi">Avviso del 18 novembre 2025</a>
    <a href="/it/normativa/decreti-direttoriali/decreto-direttoriale-24-febbraio-2016-area-di-crisi">decreto del 24 febbraio 2016</a>
    <a href="/it/normativa/decreti-direttoriali/decreto-direttoriale-10-marzo-2017-area-di-crisi">decreto del 10 marzo 2017</a>
    <a href="/images/stories/normativa/Accordo-di-Programma-Venezia.pdf">Accordo di programma</a>
    </main></body></html>"""
    trovate = pagine_atto(html, "https://www.mimit.gov.it/it/incentivi/aiuti-per-l-area-di-crisi-industriale-complessa-di-venezia")
    assert len(trovate) == 4
    assert trovate[0].endswith("avviso-direttoriale-18-novembre-2025---riapertura-sportelli-aree-di-crisi")
    assert trovate[-1].endswith("decreto-direttoriale-10-marzo-2017-area-di-crisi")   # il 2016 resta fuori
    assert "https://www.mimit.gov.it/it/normativa/decreti-ministeriali" not in trovate     # menu del sito


def test_pagine_atto_di_lazio_europa_e_della_camera_di_chieti():
    lazio = ('<main><a href="https://www.regione.lazio.it/documenti/88057">Documentazione di riferimento</a>'
             '<a href="https://www.regione.lazio.it/documenti">Tutti i documenti</a></main>')
    assert sottopagine(lazio, "https://www.lazioeuropa.it/bandi/rafforzamento-delle-capacita-manageriali-delle-imprese/") == [
        "https://www.regione.lazio.it/documenti/88057"]
    chieti = ('<main><a href="https://trasparenza.chpe.camcom.it/archivio19_regolamenti_0_9915.html">'
              'Scarica il bando e la modulistica</a></main>')
    assert pagine_atto(chieti, "https://www.chpe.camcom.it/pagina198974_bando-voucher-doppia-transizione-2026.html") == [
        "https://trasparenza.chpe.camcom.it/archivio19_regolamenti_0_9915.html"]


def test_documenti_letti_dalla_pagina_atto(tmp_path):
    # 4514 (Lazio Europa): l'avviso sta sulla pagina dell'atto della Regione, con il PDF.
    pagina = "https://www.lazioeuropa.it/bandi/rafforzamento-delle-capacita-manageriali-delle-imprese/"
    atto = "https://www.regione.lazio.it/documenti/88057"
    pdf = "https://www.regione.lazio.it/sites/default/files/documentazione/2025/DD-G16530-04-12-2025-Allegato1-avviso.pdf"
    c = client({
        pagina: httpx.Response(200, html=f'<main><h1>Capacita\' manageriali</h1><a href="{atto}">Documentazione di riferimento</a></main>'),
        atto: httpx.Response(200, html=f'<main><a href="{pdf}">Allegato - Avviso Rafforzamento delle capacita\' manageriali</a></main>'),
        pdf: httpx.Response(200, content=pdf_con_testo("Avviso pubblico"), headers={"content-type": "application/pdf"}),
    })
    risultati = elabora_pagina(c, "b4514", pagina, tmp_path, pausa(c))
    assert [(r.tipo, r.errore) for r in risultati] == [("pagina", None), ("pdf", None)]
    assert categoria_allegato(risultati[1].nome, risultati[1].url, "pdf") in ("bando", "decreto")


# --- registro: "Vai alla pagina" / "Vai al bando" ----------------------------------------------------------

def test_registro_segue_vai_alla_pagina_e_vai_al_bando():
    from app.fonti.registro import CARTELLA_FONTI, carica_registro
    from app.schede.pagina_ufficiale import link_da_seguire

    registro = {f.id: f for f in carica_registro(CARTELLA_FONTI)}
    fvg = registro["fvg_bandi_avvisi"].pagina_ufficiale["segui_link"]
    treviso = registro["cciaa_treviso_belluno_bandi"].pagina_ufficiale["segui_link"]
    assert fvg == {"testi": ["vai alla pagina"], "stesso_sito": True}
    assert treviso == {"testi": ["vai al bando"], "stesso_sito": True}
    scheda = ('<main><h2>Contributi per l\'artigianato</h2><a href="/rafvg/cms/RAFVG/economia-imprese/artigianato/FOGLIA21/">'
              'Vai alla pagina</a></main>')
    assert link_da_seguire(scheda, "https://www.regione.fvg.it/rafvg/cms/RAFVG/MODULI/bandi_avvisi/dettaglio.jsp?id=1",
                           fvg["testi"], fvg["stesso_sito"]) == [
        "https://www.regione.fvg.it/rafvg/cms/RAFVG/economia-imprese/artigianato/FOGLIA21/"]


# --- database: filtro da rifare quando arrivano documenti nuovi -----------------------------------------------

@pytest.mark.skipif(not os.environ.get("PGHOST"), reason="serve un database Postgres di prova (PGHOST)")
def test_documenti_nuovi_rimettono_il_filtro_e_il_regista_ricontrolla_i_bandi_in_disparte(monkeypatch):
    from app.catena import regista
    from app.db.connessione import connetti
    from app.db.migrazioni import applica_migrazioni
    from app.schede.allegati import Risultato, salva_bando

    with connetti() as conn:
        applica_migrazioni(conn)
        with conn.cursor() as cur:
            cur.execute("""INSERT INTO bandi (titolo, ente, url, stato, pagina_stato, documentazione, documentazione_motivo,
                                              allegati_cercati_il)
                           VALUES ('Aiuti trasporto siero', 'Regione Valle d''Aosta', 'https://www.regione.vda.it/siero',
                                   'aperto', 'trovata', 'sintesi', 'solo pagine', now() - interval '20 days')
                           RETURNING id""")
            bando = cur.fetchone()["id"]
        conn.commit()
        try:
            pagina = Risultato("https://www.regione.vda.it/siero", "Pagina del bando (copia)", "pagina", 10, "p" * 64,
                               testo_estratto="pagina")
            assert salva_bando(conn, bando, [pagina]) == 0                  # solo la copia della pagina: niente di nuovo
            with conn.cursor() as cur:
                cur.execute("SELECT documentazione FROM bandi WHERE id = %s", (bando,))
                assert cur.fetchone()["documentazione"] == "sintesi"
                cur.execute("UPDATE bandi SET allegati_cercati_il = now() - interval '20 days' WHERE id = %s", (bando,))
                cur.execute("SELECT situazione FROM bandi_situazione WHERE id = %s", (bando,))
                assert cur.fetchone()["situazione"] == "in_disparte"
            conn.commit()

            # Il regista riapre la pagina: l'ente ha pubblicato la delibera (allegati.esegui finto, senza rete).
            delibera = Risultato("https://www.regione.vda.it/allegato.aspx?pk=68108",
                                 "Deliberazione della Giunta regionale n. 526", "pdf", 100, "d" * 64, testo_estratto="delibera")
            chiamati = []

            def esegui_finto(bando_id=None, **kw):
                chiamati.append(bando_id)
                with connetti() as c2:
                    salva_bando(c2, bando_id, [pagina, delibera])
                return 0

            monkeypatch.setattr(allegati, "esegui", esegui_finto)
            assert regista.ricontrolla_in_disparte(conn) == 1
            assert chiamati == [bando]
            with conn.cursor() as cur:
                cur.execute("SELECT documentazione, allegati_cercati_il > now() - interval '1 minute' AS rifatto, da_aggiornare "
                            "FROM bandi WHERE id = %s", (bando,))
                riga = cur.fetchone()
                assert riga["documentazione"] is None and riga["rifatto"] and riga["da_aggiornare"] is None   # senza scheda
                cur.execute("SELECT esito FROM eventi_catena WHERE oggetto_id = %s AND passo = 'ricontrollo in disparte'", (bando,))
                assert cur.fetchone()["esito"] == "1 nuovi"
            # Appena ricontrollato: al giro dopo non si riapre.
            assert regista.ricontrolla_in_disparte(conn) == 0 and chiamati == [bando]
        finally:
            with conn.cursor() as cur:
                cur.execute("DELETE FROM eventi_catena WHERE oggetto = 'bando' AND oggetto_id = %s", (bando,))
                cur.execute("DELETE FROM allegati WHERE bando_id = %s", (bando,))
                cur.execute("DELETE FROM bandi WHERE id = %s", (bando,))
            conn.commit()


@pytest.mark.skipif(not os.environ.get("PGHOST"), reason="serve un database Postgres di prova (PGHOST)")
def test_rileggi_altro_corregge_tipo_testo_e_filtro(tmp_path):
    from app.db.connessione import connetti
    from app.db.migrazioni import applica_migrazioni

    (tmp_path / "b1").mkdir()
    (tmp_path / "b1" / "4d1116c88154_download.aspx.altro").write_bytes(pdf_con_testo("Criteri di concessione"))
    with connetti() as conn:
        applica_migrazioni(conn)
        with conn.cursor() as cur:
            cur.execute("""INSERT INTO bandi (titolo, stato, documentazione, allegati_cercati_il)
                           VALUES ('Zootecnia Alto Adige', 'aperto', 'sintesi', now()) RETURNING id""")
            bando = cur.fetchone()["id"]
            cur.execute("""INSERT INTO allegati (bando_id, url, nome, tipo, categoria, percorso_locale, impronta)
                           VALUES (%s, 'https://mycivis.civis.bz.it/File/download.aspx?Id=1', 'Criteri per la concessione',
                                   'altro', 'altro', 'b1/4d1116c88154_download.aspx.altro', 'x')""", (bando,))
        conn.commit()
        try:
            allegati.rileggi_altro(tmp_path, bando_id=bando, prova=True)
            with conn.cursor() as cur:
                cur.execute("SELECT tipo FROM allegati WHERE bando_id = %s", (bando,))
                assert cur.fetchone()["tipo"] == "altro"                       # --prova: niente scritto
            conn.rollback()
            allegati.rileggi_altro(tmp_path, bando_id=bando)
            with conn.cursor() as cur:
                cur.execute("SELECT tipo, testo_estratto FROM allegati WHERE bando_id = %s", (bando,))
                riga = cur.fetchone()
                cur.execute("SELECT documentazione FROM bandi WHERE id = %s", (bando,))
                assert cur.fetchone()["documentazione"] is None
            assert riga["tipo"] == "pdf" and "Criteri di concessione" in riga["testo_estratto"]
        finally:
            with conn.cursor() as cur:
                cur.execute("DELETE FROM allegati WHERE bando_id = %s", (bando,))
                cur.execute("DELETE FROM bandi WHERE id = %s", (bando,))
            conn.commit()

