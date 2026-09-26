"""Pagina ufficiale del bando e ordine degli allegati. Tutto senza rete (httpx.MockTransport)."""

import httpx
import pytest

from app.raccolta import scarica as modulo_scarica
from app.schede.allegati import (
    Pausa, candidati_plone, categoria_allegato, ordina_per_scheda, documenti_per_scheda, trova_allegati,
)
from app.schede.pagina_ufficiale import AnnuncioDelBando, esegui_regole, link_da_seguire, valuta_pagina

BANDO = """<html><body><nav><a href="/">Home</a></nav><main><h1>Bando voucher digitali 2026</h1>
<p>Contributo a fondo perduto per le imprese. Domande dal 1 ottobre, scadenza 30 novembre. Requisiti e spese ammissibili
all'articolo 3. """ + "Testo del bando. " * 40 + """</p><a href="/doc/bando.pdf">Bando</a></main></body></html>"""
LOGIN = """<html><body><h1>Accedi</h1><form><input name="u"><input type="password" name="p"></form></body></html>"""
MENU = """<html><body><main><ul><li><a href="/a">Chi siamo</a></li><li><a href="/b">Contatti</a></li></ul></main></body></html>"""


@pytest.fixture(autouse=True)
def senza_robots(monkeypatch):
    monkeypatch.setattr(modulo_scarica, "_robots", {})


def client(pagine: dict[str, tuple[int, str, str]], chiamate: list | None = None) -> httpx.Client:
    def risposta(richiesta: httpx.Request) -> httpx.Response:
        if chiamate is not None:
            chiamate.append((richiesta.method, str(richiesta.url), richiesta.content.decode()))
        if richiesta.url.path == "/robots.txt":
            return httpx.Response(404)
        stato, tipo, corpo = pagine.get(str(richiesta.url), (404, "text/html", "non c'e'"))
        return httpx.Response(stato, headers={"content-type": tipo}, text=corpo)
    return httpx.Client(transport=httpx.MockTransport(risposta), follow_redirects=True)


def pausa(c):
    return Pausa(c, minima=0, dormi=lambda s: None)


def test_valuta_pagina():
    assert valuta_pagina(BANDO, "https://ente.it/bando")[0]
    assert valuta_pagina(LOGIN, "https://ente.it/login") == (False, "pagina di accesso (login)")
    ok, perche = valuta_pagina(MENU, "https://ente.it/menu")
    assert not ok and "vuota" in perche


def test_link_da_seguire_nella_notizia():
    notizia = """<html><body><main><p>La Camera di Padova apre il bando.</p>
    <a href="https://www.pd.camcom.it/">Padova</a>
    <a href="https://www.pd.camcom.it/bandi/mamme-2026">BANDO E MODULISTICA ONLINE</a>
    <a href="/altra-notizia">Altra notizia sul bando</a></main></body></html>"""
    assert link_da_seguire(notizia, "https://www.unioncamereveneto.it/n", ["bando"]) == ["https://www.pd.camcom.it/bandi/mamme-2026"]
    assert "https://www.unioncamereveneto.it/altra-notizia" in link_da_seguire(notizia, "https://www.unioncamereveneto.it/n", ["bando"], True)


def test_catalogo_segue_il_link_all_ente():
    c = client({"https://mo.camcom.it/bando": (200, "text/html", BANDO)})
    a = AnnuncioDelBando(1, "incentivi", "https://incentivi.gov.it/catalogo/1", {"link_ente": "https://mo.camcom.it/bando"}, None, "origine")
    esito = esegui_regole(c, pausa(c), [a], {"incentivi": {"campo": "link_ente"}})
    assert esito.stato == "trovata" and esito.url == "https://mo.camcom.it/bando" and "link_ente" in esito.motivo


def test_lombardia_pagina_di_domanda_esclusa_e_ricerca_per_codice():
    regole = {"lomb": {"escludi": ["faiDomanda"], "cerca": {
        "url": "https://bandi.lombardia.it/ricerca", "metodo": "POST",
        "corpo_form": {"titolo": "{codice}"}, "link": "/dettaglio/.*{codice}$"}}}
    risultati = '<a href="/dettaglio/altro-RLO12026000001">x</a><a href="/dettaglio/fiere-RLO12026055023">Fiere</a>'
    chiamate = []
    c = client({"https://bandi.lombardia.it/ricerca": (200, "text/html", risultati),
                "https://bandi.lombardia.it/dettaglio/fiere-RLO12026055023": (200, "text/html", BANDO)}, chiamate)
    a = AnnuncioDelBando(1, "lomb", "https://bandi.lombardia.it/faiDomanda?strumentoCod=RLO12026055023", None,
                         "RLO12026055023", "origine")
    esito = esegui_regole(c, pausa(c), [a], regole)
    assert esito.url == "https://bandi.lombardia.it/dettaglio/fiere-RLO12026055023"
    assert ("POST", "https://bandi.lombardia.it/ricerca", "titolo=RLO12026055023") in chiamate
    assert not any("faiDomanda" in u for _, u, _ in chiamate)   # la pagina con login non si apre nemmeno


def test_bando_non_trovato_dice_perche():
    c = client({"https://ente.it/login": (200, "text/html", LOGIN), "https://ente.it/menu": (200, "text/html", MENU)})
    annunci = [AnnuncioDelBando(1, "f", "https://ente.it/login", None, None, "origine"),
               AnnuncioDelBando(2, "f", "https://ente.it/menu", None, None, "doppione")]
    esito = esegui_regole(c, pausa(c), annunci, {})
    assert esito.stato == "non_trovata" and esito.url is None
    assert any("login" in p for p in esito.provati) and any("vuota" in p for p in esito.provati)


def test_indirizzo_relativo_e_sostituzione():
    c = client({"https://www.fondidigaranzia.it/notizia/": (200, "text/html", BANDO),
                "https://www.comune.pordenone.it/it/bandi/x": (200, "text/html", BANDO)})
    a = AnnuncioDelBando(1, "mcc", "/notizia/", None, None, "origine")
    assert esegui_regole(c, pausa(c), [a], {}, {"mcc": "https://www.fondidigaranzia.it/news"}).url == "https://www.fondidigaranzia.it/notizia/"
    b = AnnuncioDelBando(2, "pn", "https://www.comune.pordenone.it/api/it/bandi/x", None, None, "origine")
    assert esegui_regole(c, pausa(c), [b], {"pn": {"sostituisci": {"/api/it/": "/it/"}}}).url == "https://www.comune.pordenone.it/it/bandi/x"


def test_documenti_plone_dalle_sottocartelle():
    import json
    base = "https://imprese.er.it"
    pagine = {
        f"{base}/++api++/bandi/x": (200, "application/json", json.dumps({"items": [
            {"@type": "Bando Folder Deepening", "@id": f"{base}/bandi/x/presentazione-domanda", "title": "Presentazione domanda"}]})),
        f"{base}/++api++/bandi/x/presentazione-domanda": (200, "application/json", json.dumps({"items": [
            {"@type": "Document", "@id": f"{base}/bandi/x/presentazione-domanda/bando-e-modulistica"}]})),
        f"{base}/++api++/bandi/x/presentazione-domanda/bando-e-modulistica": (200, "application/json", json.dumps({"items": [
            {"@type": "File", "@id": f"{base}/bandi/x/presentazione-domanda/bando-e-modulistica/dgr-1126.pdf", "title": "D.G.R. 1126"},
            {"@type": "File", "@id": f"{base}/bandi/x/presentazione-domanda/bando-e-modulistica/mod-1.doc", "title": "Mod. 1"}]})),
    }
    c = client(pagine)
    trovati = candidati_plone(c, pausa(c), f"{base}/bandi/x")
    assert [(t.nome, t.tipo) for t in trovati] == [("D.G.R. 1126", "pdf"), ("Mod. 1", "doc")]
    assert trovati[0].url.endswith("/dgr-1126.pdf/@@download/file")


def test_link_di_scaricamento_senza_estensione():
    html = '<main><a href="/bandi/x/allegati/bando-2026/download/file">Bando 2026</a></main>'
    assert [(c.nome, c.tipo) for c in trova_allegati(html, "https://www.mo.camcom.it/bandi/x")] == [("Bando 2026", "file")]


def test_categorie_degli_allegati():
    assert categoria_allegato("Bando fiere internazionali - Secondo sportello", "x.pdf", "pdf") == "bando"
    assert categoria_allegato("Decreto approvazione Bando e impegno di spesa", "x.pdf", "pdf") == "decreto"
    assert categoria_allegato("Modello richiesta di agevolazione", "x.pdf", "pdf") == "modulistica"
    assert categoria_allegato("Facsimile F24", "x.pdf", "pdf") == "modulistica"
    assert categoria_allegato("FAQ aggiornate", "x.pdf", "pdf") == "faq"
    assert categoria_allegato("Scarica", "https://ente.it/Allegato_A_bando.pdf", "pdf") == "bando"
    assert categoria_allegato("Graduatoria", "x.pdf", "pdf") == "graduatoria"
    assert categoria_allegato("Pagina del bando (copia)", "https://x", "pagina") == "pagina"


def test_ordine_e_testo_per_la_scheda():
    allegati = [
        {"nome": "Modulo di domanda", "url": "m.pdf", "tipo": "pdf", "testo_estratto": "modulo"},
        {"nome": "Delibera 2025", "url": "d1.pdf", "tipo": "pdf", "testo_estratto": "vecchia"},
        {"nome": "Pagina del bando (copia)", "url": "https://x", "tipo": "pagina", "testo_estratto": "pagina"},
        {"nome": "Decreto 12/03/2026", "url": "d2.pdf", "tipo": "pdf", "testo_estratto": "nuovo"},
        {"nome": "FAQ", "url": "f.pdf", "tipo": "pdf", "testo_estratto": "faq"},
        {"nome": "Bando", "url": "b.pdf", "tipo": "pdf", "testo_estratto": "B" * 100},
        {"nome": "Scansione", "url": "s.pdf", "tipo": "pdf", "testo_estratto": None},
        {"nome": "Rotto", "url": "r.pdf", "tipo": "pdf", "testo_estratto": "x", "errore": "HTTP 404"},
    ]
    assert [a["nome"] for a in ordina_per_scheda(allegati)] == [
        "Bando", "Pagina del bando (copia)", "FAQ", "Decreto 12/03/2026", "Delibera 2025", "Scansione"]
    documenti, avvertenze = documenti_per_scheda(allegati, massimo=110)
    assert documenti[0]["testo"] == "B" * 100                 # il bando intero
    assert documenti[1]["testo"] == "pagina"
    assert any("tagliato" in x for x in avvertenze) or any("escluso" in x for x in avvertenze)
    assert any("Scansione" in x and "nessun testo" in x for x in avvertenze)


def test_testo_delle_pagine_volto_dall_api():
    import json

    from app.schede.allegati import testo_plone

    base = "https://imprese.er.it"
    c = client({f"{base}/++api++/bandi/x": (200, "application/json", json.dumps({
        "title": "Digital Export", "description": "Contributi per le PMI",
        "blocks": {"a": {"@type": "slate", "plaintext": "Il contributo massimo e' di 20.000 euro."}}}))})
    testo = testo_plone(c, pausa(c), f"{base}/bandi/x")
    assert "Contributi per le PMI" in testo and "20.000 euro" in testo
