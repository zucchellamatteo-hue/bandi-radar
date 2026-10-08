"""Email settimanale per impresa: testo (senza database) e ciclo prepara / invia / scarta / disiscrizione (Postgres di prova)."""

import json
import os
import uuid
from datetime import date, timedelta

import pytest

from app import impresa as imp
from app import utenti as u
from app.abbinamento import catalogo, regole
from app.notifiche import email_imprese as ei

db = pytest.mark.skipif(not os.environ.get("PGHOST"), reason="serve un database Postgres di prova (PGHOST)")
OGGI = date(2026, 10, 5)   # un lunedi'


def test_testo_dell_email(monkeypatch):
    monkeypatch.setenv("SITO_URL", "https://prova.it/")
    voci = [{"id": 7, "titolo": "Bando <digitale>", "ente": "Regione Lombardia", "scadenza": date(2026, 10, 15),
             "sintesi": "parola " * 80, "tipi_agevolazione": ["fondo_perduto"], "contributo_massimo": 50000,
             "motivo": "in_scadenza", "livello": regole.COMPATIBILE, "da_verificare": []},
            {"id": 8, "titolo": "Bando export", "ente": None, "scadenza": None, "sintesi": None,
             "motivo": "nuovo", "livello": regole.DA_VERIFICARE, "da_verificare": ["uno", "due", "tre"]}]
    oggetto, testo, corpo = ei.componi({"id": 3, "nome": "Rossi & C srl", "codice_disiscrizione": "abc"}, voci)
    assert oggetto == "2 nuovi bandi adatti a Rossi & C srl (1 in scadenza)"
    assert testo.startswith("Buongiorno Rossi & C srl,")
    assert "Scadenza: 15/10/2026 - IN SCADENZA" in testo and "fondo perduto, fino a 50.000 euro" in testo
    assert "https://prova.it/impresa/bandi/7?impresa=3\n" in testo
    assert "https://prova.it/impresa/bandi/7?impresa=3&supporto=1" in testo
    assert "da verificare: uno; due\n" in testo and "tre" not in testo
    assert "https://prova.it/disiscrizione?codice=abc" in testo and imp.AVVERTENZA in testo
    riga_sintesi = next(r for r in testo.splitlines() if r.strip().startswith("parola"))
    assert len(riga_sintesi.strip()) <= ei.LUNGHEZZA_SINTESI + 1 and riga_sintesi.endswith("…")
    # HTML: testi protetti, link con &amp;
    assert "Bando &lt;digitale&gt;" in corpo and "Rossi &amp; C srl" in corpo and "<digitale>" not in corpo
    assert "impresa=3&amp;supporto=1" in corpo


def _stato(stato="aperto", scadenza=None, chiuso_il=None, ricontrollo=None):
    return {"stato": stato, "scadenza": scadenza, "ora_scadenza": None, "chiuso_il": chiuso_il, "ricontrollo": ricontrollo}


def test_eventi_dei_bandi_gia_segnalati():
    tipi = lambda prima, ora, doc=(), avvisata=False: [e["tipo"] for e in ei.eventi_bando(prima, ora, list(doc), OGGI, avvisata)]  # noqa: E731
    s = OGGI + timedelta(days=40)
    assert tipi(_stato(scadenza=s), _stato(scadenza=s)) == []                                     # niente di nuovo
    assert tipi(_stato(scadenza=s), _stato(scadenza=s + timedelta(days=30))) == ["prorogato"]
    assert tipi(_stato(scadenza=s), _stato(scadenza=s - timedelta(days=20))) == ["scadenza_cambiata"]
    assert tipi(_stato(), _stato(scadenza=s)) == ["scadenza_cambiata"]                            # prima senza data
    # chiusura in anticipo, fondi esauriti, scadenza naturale, gia' chiuso prima
    assert tipi(_stato(scadenza=s), _stato("chiuso", s, chiuso_il=OGGI)) == ["chiuso"]
    assert tipi(_stato(scadenza=s), _stato("chiuso", s, ricontrollo={"stato": "esaurito"})) == ["esaurito"]
    assert tipi(_stato(scadenza=OGGI - timedelta(days=1)), _stato("chiuso", OGGI - timedelta(days=1))) == ["scaduto"]
    assert tipi(_stato(scadenza=OGGI - timedelta(days=1)), _stato("aperto", OGGI - timedelta(days=1))) == ["scaduto"]
    assert tipi(_stato("chiuso", s, chiuso_il=OGGI), _stato("chiuso", s, chiuso_il=OGGI)) == []
    assert tipi(_stato("chiuso", s), _stato("aperto", s + timedelta(days=10))) == ["riaperto"]


def test_chiusi_solo_se_recenti():
    """Matteo, 07/10: tra le novita' solo i bandi chiusi negli ultimi 7 giorni (o dall'ultima email, se piu' recente);
    un bando chiuso gia' prima della segnalazione e' un errore nostro, non una notizia per l'impresa."""
    s = OGGI + timedelta(days=40)

    def tipi(ora, dal=None, segnalato_il=None):
        return [e["tipo"] for e in ei.eventi_bando(_stato(scadenza=s), ora, [], OGGI, False, dal, segnalato_il)]

    assert tipi(_stato("chiuso", s, chiuso_il=OGGI - timedelta(days=3))) == ["chiuso"]
    assert tipi(_stato("chiuso", s, chiuso_il=OGGI - timedelta(days=7))) == ["chiuso"]
    assert tipi(_stato("chiuso", s, chiuso_il=OGGI - timedelta(days=8))) == []                  # piu' di 7 giorni fa
    assert tipi(_stato("chiuso", OGGI - timedelta(days=20))) == []                                # scaduto da tempo
    assert tipi(_stato("chiuso", OGGI - timedelta(days=2)), dal=OGGI - timedelta(days=7)) == ["scaduto"]
    # l'ultima email e' di 2 giorni fa: una chiusura di 4 giorni fa e' precedente, non si ripete
    assert tipi(_stato("chiuso", s, chiuso_il=OGGI - timedelta(days=4)), dal=OGGI - timedelta(days=2)) == []
    # chiusura senza data (ricontrollo della pagina): vale se l'ultima email e' recente
    esaurito = _stato("chiuso", s, ricontrollo={"stato": "esaurito"})
    assert tipi(esaurito, dal=OGGI - timedelta(days=7)) == ["esaurito"]
    assert tipi(esaurito, dal=OGGI - timedelta(days=30)) == []
    # chiuso gia' prima della segnalazione: errore di qualita', non un evento per l'email
    [e] = ei.eventi_bando(_stato(scadenza=s), _stato("chiuso", s, chiuso_il=date(2025, 10, 13)), [], OGGI, False,
                          OGGI - timedelta(days=7), OGGI - timedelta(days=7))
    assert e["tipo"] == "chiuso_prima_della_segnalazione" and "13/10/2025" in e["testo"]
    assert "risulta chiuso dal" not in ei.componi({"id": 1, "nome": "X", "codice_disiscrizione": "c"}, [], [])[1]


def test_eventi_scadenza_vicina_e_documenti():
    tipi = lambda prima, ora, doc=(), avvisata=False: [e["tipo"] for e in ei.eventi_bando(prima, ora, list(doc), OGGI, avvisata)]  # noqa: E731
    s = OGGI + timedelta(days=40)
    # in scadenza entro 14 giorni, una volta sola
    vicina = OGGI + timedelta(days=9)
    assert tipi(_stato(scadenza=vicina), _stato(scadenza=vicina)) == ["in_scadenza"]
    assert tipi(_stato(scadenza=vicina), _stato(scadenza=vicina), avvisata=True) == []
    # nuovi documenti ufficiali
    doc = [{"nome": "Domande frequenti", "categoria": "faq"}, {"nome": "Allegato 2", "categoria": "modulistica"}]
    [e] = ei.eventi_bando(_stato(scadenza=s), _stato(scadenza=s), doc, OGGI, False)
    assert e["tipo"] == "documenti" and "FAQ «Domande frequenti»" in e["testo"] and "modulistica «Allegato 2»" in e["testo"]
    testo = ei.eventi_bando(_stato(scadenza=s), _stato(scadenza=s + timedelta(days=30)), [], OGGI, False)[0]["testo"]
    assert testo == f"Scadenza prorogata: dal {s:%d/%m/%Y} al {s + timedelta(days=30):%d/%m/%Y}."


def test_email_completa_e_ordine_delle_sezioni(monkeypatch):
    monkeypatch.setenv("SITO_URL", "https://prova.it")
    voci = [{"id": 8, "titolo": "Bando nuovo", "ente": "Camera di commercio", "scadenza": None, "sintesi": None,
             "motivo": "nuovo", "livello": regole.COMPATIBILE, "da_verificare": []}]
    aggiornamenti = ei.ordina_aggiornamenti([
        {"id": 5, "titolo": "Bando chiuso", "ente": "Regione", "scadenza": OGGI + timedelta(days=30),
         "eventi": [{"tipo": "chiuso", "testo": "Chiuso in anticipo: non si possono più presentare domande."}]},
        {"id": 4, "titolo": "Bando che scade", "ente": None, "scadenza": OGGI + timedelta(days=5),
         "eventi": [{"tipo": "in_scadenza", "testo": "Scade tra 5 giorni."}]}])
    assert [a["id"] for a in aggiornamenti] == [4, 5]                       # prima le scadenze vicine
    news = [{"id": 1, "titolo": "Novità", "testo": "Il pulsante Segnala.", "link": "/impresa/misure"}]
    misure = [{"id": "fondo_garanzia_pmi", "nome": "Fondo di Garanzia", "sintesi": "Garanzia dello Stato."}]
    imp = {"id": 3, "nome": "Rossi srl", "codice_disiscrizione": "abc"}
    oggetto, testo, corpo = ei.componi(imp, voci, aggiornamenti, news, misure, totale=12, altri=3)
    assert oggetto == "1 nuovo bando adatto a Rossi srl e 2 novità sui bandi già segnalati"
    # Matteo, 07/10: prima i bandi nuovi, poi le novita' sui segnalati, in fondo i chiusi; poi misure, news, chiusura
    posizioni = [testo.index(t) for t in ("Buongiorno Rossi srl", "NUOVI BANDI ADATTI", "Altri 3 bandi adatti",
                                          "NOVITÀ SUI BANDI CHE TI ABBIAMO SEGNALATO", "Bando che scade",
                                          "BANDI SEGNALATI CHE SI SONO CHIUSI", "Bando chiuso",
                                          "AGEVOLAZIONI NAZIONALI", "NEWS", "sono 12",
                                          "Richiedi supporto per la domanda»", imp_avvertenza())]
    assert posizioni == sorted(posizioni)
    # l'introduzione segue lo stesso ordine
    assert ("un nuovo bando adatto alla tua impresa, una novità su un bando che ti abbiamo già segnalato e un bando "
            "segnalato che si è appena chiuso") in testo
    assert "https://prova.it/impresa/misure\n" in testo and "https://prova.it/impresa/misure/fondo_garanzia_pmi" in testo
    assert "Altri 3 bandi adatti ti aspettano nel tuo portale: https://prova.it/impresa?impresa=3" in testo
    # il bando chiuso non ha il link per chiedere supporto, quello in scadenza si'
    assert "/impresa/bandi/4?impresa=3&supporto=1" in testo and "/impresa/bandi/5?impresa=3&supporto=1" not in testo
    assert "<h2" in corpo and "Scopri di più" in corpo and "Vai ai tuoi bandi" in corpo
    h = [corpo.index(t) for t in ("Nuovi bandi adatti", "Novità sui bandi che ti abbiamo segnalato",
                                  "Bandi segnalati che si sono chiusi", "Agevolazioni nazionali", ">News<")]
    assert h == sorted(h)
    # carattere Outfit nell'head, con i ripieghi; documento completo (l'avviso "non rispondere" va prima di </body>)
    assert "fonts.googleapis.com/css2?family=Outfit" in corpo and "'Outfit', 'Segoe UI', 'Helvetica Neue', Arial" in corpo
    assert corpo.startswith("<!DOCTYPE html>") and corpo.endswith("</body></html>")
    from app.notifiche import email
    _, con = email.con_avviso(testo, corpo)
    assert con.index("non rispondere") < con.index("</body>")

    # sezioni vuote: non compaiono
    oggetto, testo, corpo = ei.componi(imp, [], aggiornamenti[:1])
    assert oggetto == "1 novità sui bandi già segnalati a Rossi srl"
    for assente in ("NUOVI BANDI ADATTI", "BANDI SEGNALATI CHE SI SONO CHIUSI", "AGEVOLAZIONI NAZIONALI", "NEWS",
                    "In tutto, oggi", "ti aspettano nel tuo portale"):
        assert assente not in testo


def test_email_di_benvenuto(monkeypatch):
    """Prima email: niente sezioni sui bandi gia' segnalati ne' sui chiusi, introduzione di benvenuto, riga "altri N"."""
    monkeypatch.setenv("SITO_URL", "https://prova.it")
    voci = [{"id": i, "titolo": f"Bando {i}", "ente": "Regione", "scadenza": OGGI + timedelta(days=30), "sintesi": None,
             "motivo": "nuovo", "livello": regole.COMPATIBILE, "da_verificare": []} for i in range(1, 11)]
    aggiornamenti = [{"id": 99, "titolo": "Bando chiuso", "ente": None, "scadenza": None,
                      "eventi": [{"tipo": "chiuso", "testo": "Chiuso in anticipo."}]}]
    imp = {"id": 3, "nome": "Rossi srl", "codice_disiscrizione": "abc"}
    oggetto, testo, corpo = ei.componi(imp, voci, aggiornamenti, totale=17, altri=7, benvenuto=True)
    assert oggetto == "Benvenuto in bandinQiaro: i 10 bandi più interessanti per Rossi srl"
    assert "benvenuto in bandinQiaro" in testo and "tra quelli aperti oggi" in testo
    assert "I BANDI PIÙ INTERESSANTI PER LA TUA IMPRESA" in testo
    for assente in ("NOVITÀ SUI BANDI", "SI SONO CHIUSI", "Bando chiuso", "NUOVI BANDI ADATTI"):
        assert assente not in testo
    assert "Altri 7 bandi adatti ti aspettano nel tuo portale: https://prova.it/impresa?impresa=3" in testo
    assert ">Benvenuto<" in corpo


def test_ordine_delle_proposte():
    """Compatibili prima; poi il fondo perduto piu' alto; poi la scadenza piu' vicina."""
    def voce(i, livello=regole.COMPATIBILE, fp=None, contributo=None, tipi=("fondo_perduto",), scadenza=30):
        return {"id": i, "livello": livello, "fuori_zona": False, "fondo_perduto_massimo": fp,
                "contributo_massimo": contributo, "tipi_agevolazione": list(tipi),
                "scadenza": OGGI + timedelta(days=scadenza)}
    voci = [voce(1, regole.DA_VERIFICARE, fp=10**6), voce(2, contributo=50000, scadenza=10),
            voce(3, fp=200000, scadenza=90), voce(4, contributo=50000, scadenza=5),
            voce(5, contributo=10**6, tipi=("finanziamento_agevolato",)), voce(6, tipi=("voucher",))]
    assert [v["id"] for v in sorted(voci, key=ei.chiave_proposta)] == [3, 4, 2, 6, 5, 1]


def imp_avvertenza():
    return imp.AVVERTENZA


# --- con il database ---

@pytest.fixture
def ambiente(monkeypatch):
    from fastapi.testclient import TestClient

    from app.db.connessione import connetti
    from app.db.migrazioni import applica_migrazioni
    from app.main import app

    monkeypatch.setenv("COOKIE_SICURO", "0")
    monkeypatch.delenv("EMAIL_IMPRESE_APPROVAZIONE", raising=False)
    mandate = []
    monkeypatch.setattr(u, "manda", lambda dest, oggetto, testo, html=None: mandate.append((dest, oggetto)) or "stampata")
    with connetti() as conn:
        applica_migrazioni(conn)
        conn.commit()
    # Ogni test vede solo i bandi che crea lui: nel database di prova restano quelli degli altri test, e con il tetto
    # di 10-15 bandi per email cambierebbero quali entrano.
    _AMMESSI.clear()
    originale = catalogo.carica_bandi
    monkeypatch.setattr(catalogo, "carica_bandi", lambda conn: [b for b in originale(conn) if b["id"] in _AMMESSI])
    return TestClient(app), mandate


_AMMESSI: set[int] = set()


def _bando(cur, titolo, scadenza, vincoli, regioni=None, contributo=30000):
    cur.execute("""INSERT INTO bandi (titolo, ente, url, stato, scadenza, completezza, dati, vincoli, territorio_regioni,
                                      sintesi, tipi_agevolazione, contributo_massimo, verifica_documento, secondo_controllo)
                   VALUES (%s, 'Regione Lombardia', 'https://esempio.it/b', 'aperto', %s, 'bando_ufficiale', '{}',
                           %s, %s, 'Contributi per investimenti delle PMI.', '{fondo_perduto}', %s, '{"verificato": "si"}', '{"esito": "corretta", "fatto_il": "2099-01-01T00:00:00+00:00"}') RETURNING id""",
                (titolo, scadenza, json.dumps(vincoli), regioni, contributo))
    bando_id = cur.fetchone()["id"]
    _AMMESSI.add(bando_id)
    return bando_id


def _impresa_con_bandi():
    """Utente impresa confermato, impresa a Milano e due bandi aperti: uno compatibile (scade tra 60 giorni), uno da
    verificare in Lombardia (scade tra 10 giorni)."""
    from app.db.connessione import connetti

    with connetti() as conn:
        utente = u.crea_utente(conn, f"impresa-{uuid.uuid4().hex[:8]}@esempio.it", "impresa", password="password-di-prova")
        with conn.cursor() as cur:
            cur.execute("UPDATE utenti SET email_confermata_il = now() WHERE id = %s", (utente["id"],))
            tutti_liberi = {k: "nessun_vincolo" for k in regole.NOMI_VINCOLI}
            compatibile = _bando(cur, "Bando compatibile di prova", OGGI + timedelta(days=60), tutti_liberi)
            senza_ateco = {**tutti_liberi, "territorio": "vincolo"}
            senza_ateco.pop("ateco")   # vincolo sull'ATECO non noto: "da verificare"
            da_verificare = _bando(cur, "Bando lombardo di prova", OGGI + timedelta(days=10), senza_ateco, ["LOM"])
        i = imp.crea(conn, utente["id"], "Officina Prova srl",
                     {"forma_giuridica": "srl", "dimensione": "piccola", "sedi": [{"provincia": "MI"}]})
        conn.commit()
    return utente, i, compatibile, da_verificare


def _email_di(conn, impresa_id):
    with conn.cursor() as cur:
        cur.execute("SELECT * FROM email_imprese WHERE impresa_id = %s ORDER BY id", (impresa_id,))
        return [dict(r) for r in cur.fetchall()]


def _segnalati(conn, impresa_id):
    with conn.cursor() as cur:
        cur.execute("SELECT bando_id, email_id FROM bandi_segnalati WHERE impresa_id = %s", (impresa_id,))
        return {r["bando_id"]: r["email_id"] for r in cur.fetchall()}


@db
def test_prepara_invia_e_non_ripete(ambiente):
    from app.db.connessione import connetti

    _, mandate = ambiente
    utente, i, compatibile, da_verificare = _impresa_con_bandi()
    with connetti() as conn:
        conteggi = ei.prepara(conn, OGGI)
        assert conteggi["create"] >= 1 and conteggi["inviate"] == 0
        [e] = _email_di(conn, i["id"])
        assert e["stato"] == "da_approvare" and e["settimana"] == "2026-W41"
        motivi = {b["bando_id"]: b["motivo"] for b in e["bandi"]}
        assert motivi[compatibile] == "nuovo" and motivi[da_verificare] == "in_scadenza"
        ordine = [b["bando_id"] for b in e["bandi"]]
        assert ordine.index(compatibile) < ordine.index(da_verificare)   # prima i compatibili
        assert f"/impresa/bandi/{compatibile}?impresa={i['id']}" in e["testo"]
        assert f"/impresa/bandi/{da_verificare}?impresa={i['id']}&supporto=1" in e["testo"]
        assert "da verificare: " in e["testo"] and "Officina Prova srl" in e["oggetto"]
        assert e["html"] and "Officina Prova srl" in e["html"]

        ei.prepara(conn, OGGI + timedelta(days=2))   # stessa settimana: nessuna seconda email
        assert len(_email_di(conn, i["id"])) == 1

        assert ei.invia(conn, e["id"], "Matteo") == "stampata"
        assert (utente["email"], e["oggetto"]) in mandate
        [e] = _email_di(conn, i["id"])
        assert e["stato"] == "inviata" and e["decisa_da"] == "Matteo" and e["decisa_il"]
        segnalati = _segnalati(conn, i["id"])
        assert segnalati[compatibile] == e["id"] and segnalati[da_verificare] == e["id"]
        with pytest.raises(ValueError):
            ei.invia(conn, e["id"], "Matteo")   # gia' inviata
        with pytest.raises(ValueError):
            ei.invia(conn, 0, "Matteo")

        ei.prepara(conn, OGGI + timedelta(days=7))   # la settimana dopo gli stessi bandi non tornano
        nuove = [x for x in _email_di(conn, i["id"]) if x["settimana"] == "2026-W42"]
        assert all(b["bando_id"] not in (compatibile, da_verificare) for x in nuove for b in x["bandi"])
        assert any(x["id"] == e["id"] for x in ei.in_attesa(conn))


@db
def test_scarta_non_segna_i_bandi(ambiente):
    from app.db.connessione import connetti

    _, i, compatibile, _ = _impresa_con_bandi()
    with connetti() as conn:
        ei.prepara(conn, OGGI)
        [e] = _email_di(conn, i["id"])
        ei.scarta(conn, e["id"], "Matteo")
        assert _email_di(conn, i["id"])[0]["stato"] == "scartata"
        assert _segnalati(conn, i["id"]) == {}
        with pytest.raises(ValueError):
            ei.scarta(conn, e["id"], "Matteo")
        ei.prepara(conn, OGGI + timedelta(days=7))   # tornano la settimana dopo
        [_, nuova] = _email_di(conn, i["id"])
        assert compatibile in [b["bando_id"] for b in nuova["bandi"]]


@db
def test_senza_approvazione_parte_subito(ambiente, monkeypatch):
    from app.db.connessione import connetti

    monkeypatch.setenv("EMAIL_IMPRESE_APPROVAZIONE", "0")
    _, i, compatibile, _ = _impresa_con_bandi()
    with connetti() as conn:
        assert ei.prepara(conn, OGGI)["inviate"] >= 1
        assert _email_di(conn, i["id"])[0]["stato"] == "inviata"
        assert compatibile in _segnalati(conn, i["id"])


@db
def test_disiscrizione_e_rotte_admin(ambiente):
    from conftest import accesso_di_prova

    from app.db.connessione import connetti

    client, _ = ambiente
    _, i, _, _ = _impresa_con_bandi()
    with connetti() as conn, conn.cursor() as cur:
        cur.execute("SELECT codice_disiscrizione FROM imprese WHERE id = %s", (i["id"],))
        codice = cur.fetchone()["codice_disiscrizione"]
    assert client.get("/api/disiscrizione", params={"codice": "sbagliato"}).status_code == 404
    r = client.get("/api/disiscrizione", params={"codice": codice})   # senza accesso
    assert r.status_code == 200 and r.json() == {"impresa": "Officina Prova srl"}
    with connetti() as conn:
        ei.prepara(conn, OGGI)
        assert _email_di(conn, i["id"]) == []

    assert client.get("/api/email-imprese").status_code == 401
    revisore = accesso_di_prova("revisore")
    assert client.get("/api/email-imprese", auth=revisore).status_code == 403
    assert client.post("/api/email-imprese/prepara", auth=revisore).status_code == 403
    assert client.post("/api/email-imprese/1/invia", auth=revisore).status_code == 403
    assert client.post("/api/email-imprese/1/scarta", auth=revisore).status_code == 403

    admin = accesso_di_prova("admin")
    assert client.get("/api/email-imprese", auth=admin).status_code == 200
    assert client.post("/api/email-imprese/prepara", auth=admin).status_code == 200
    assert client.post("/api/email-imprese/0/invia", auth=admin).status_code == 404


@db
def test_novita_sui_bandi_segnalati_e_news(ambiente):
    """Dopo la prima email: proroga e nuove FAQ arrivano la settimana dopo, una volta sola; il bando gia' annunciato
    "in scadenza" non torna; la news pubblicata va una volta sola."""
    from app import news
    from app.db.connessione import connetti

    _, i, compatibile, da_verificare = _impresa_con_bandi()
    with connetti() as conn:
        n = news.crea(conn, {"titolo": "Novità di prova", "testo": "Due righe.", "stato": "pubblicata",
                             "da": OGGI, "a": OGGI + timedelta(days=30)}, "prova")
        conn.commit()
        ei.prepara(conn, OGGI)
        [e] = _email_di(conn, i["id"])
        assert n["id"] in e["contenuti"]["news"] and "Novità di prova" in e["testo"]
        assert {b["bando_id"]: b["scadenza"] for b in e["bandi"]}[da_verificare] == (OGGI + timedelta(days=10)).isoformat()
        ei.invia(conn, e["id"], "Matteo")

        nuova_scadenza = OGGI + timedelta(days=90)
        with conn.cursor() as cur:
            cur.execute("UPDATE bandi SET scadenza = %s WHERE id = %s", (nuova_scadenza, compatibile))
            cur.execute("""INSERT INTO allegati (bando_id, url, nome, tipo, categoria)
                           VALUES (%s, 'https://esempio.it/faq.pdf', 'FAQ aggiornate', 'pdf', 'faq')""", (compatibile,))
        conn.commit()

        ei.prepara(conn, OGGI + timedelta(days=7))
        [seconda] = [x for x in _email_di(conn, i["id"]) if x["settimana"] == "2026-W42"]
        aggiornati = {a["bando_id"]: a["eventi"] for a in seconda["contenuti"]["aggiornamenti"]}
        assert aggiornati[compatibile] == ["prorogato", "documenti"]
        assert da_verificare not in aggiornati          # gia' annunciato in scadenza nella prima email
        assert f"al {nuova_scadenza:%d/%m/%Y}" in seconda["testo"] and "FAQ «FAQ aggiornate»" in seconda["testo"]
        assert n["id"] not in seconda["contenuti"]["news"] and "Novità di prova" not in seconda["testo"]
        assert seconda["testo"].index("NOVITÀ SUI BANDI") < seconda["testo"].index("Richiedi supporto per la domanda»")
        ei.invia(conn, seconda["id"], "Matteo")

        ei.prepara(conn, OGGI + timedelta(days=14))     # la proroga e le FAQ non si ripetono
        terze = [x for x in _email_di(conn, i["id"]) if x["settimana"] == "2026-W43"]
        assert all(a["bando_id"] != compatibile for x in terze for a in x["contenuti"]["aggiornamenti"])


def _bandi_liberi(n, base, titolo="Bando ricco"):
    """n bandi compatibili con tutti, a fondo perduto, con contributi diversi (base + i). Ritorna gli id dal contributo
    piu' alto al piu' basso (l'ordine atteso nell'email)."""
    from app.db.connessione import connetti

    liberi = {k: "nessun_vincolo" for k in regole.NOMI_VINCOLI}
    with connetti() as conn, conn.cursor() as cur:
        ids = [_bando(cur, f"{titolo} {i}", OGGI + timedelta(days=60), liberi, contributo=base + i) for i in range(n)]
        conn.commit()
    return list(reversed(ids))


@db
def test_prima_email_di_benvenuto_e_visti_nel_portale(ambiente):
    """Prima email: benvenuto, al massimo 10 bandi (i piu' ricchi a fondo perduto prima), riga "Altri N", gli altri
    adatti registrati come "visti nel portale" all'invio; la settimana dopo solo i bandi davvero nuovi."""
    from app.db.connessione import connetti

    _, i, compatibile, da_verificare = _impresa_con_bandi()
    ricchi = _bandi_liberi(12, 100000)
    with connetti() as conn:
        ei.prepara(conn, OGGI)
        [e] = _email_di(conn, i["id"])
        ids = [b["bando_id"] for b in e["bandi"]]
        assert ids == ricchi[:10]                                   # massimo 10, dal fondo perduto piu' alto
        visti = e["contenuti"]["visti_portale"]
        assert e["contenuti"]["benvenuto"] is True and set(visti) == {*ricchi[10:], compatibile, da_verificare}
        assert e["oggetto"].startswith("Benvenuto in bandinQiaro: i 10 bandi")
        assert "Altri 4 bandi adatti ti aspettano nel tuo portale" in e["testo"]
        assert "NOVITÀ SUI BANDI" not in e["testo"] and "SI SONO CHIUSI" not in e["testo"]
        assert "tra quelli aperti oggi" in e["testo"]
        ei.invia(conn, e["id"], "Matteo")
        with conn.cursor() as cur:
            cur.execute("SELECT bando_id, modo FROM bandi_segnalati WHERE impresa_id = %s", (i["id"],))
            modi = {r["bando_id"]: r["modo"] for r in cur.fetchall()}
        assert {b for b, m in modi.items() if m == "email"} == set(ids)
        assert {b for b, m in modi.items() if m == "portale"} == set(visti)

        [nuovo] = _bandi_liberi(1, 5000, "Bando arrivato dopo")
        ei.prepara(conn, OGGI + timedelta(days=7))
        [seconda] = [x for x in _email_di(conn, i["id"]) if x["settimana"] == "2026-W42"]
        assert [b["bando_id"] for b in seconda["bandi"]] == [nuovo] and not seconda["contenuti"]["benvenuto"]
        assert seconda["contenuti"]["visti_portale"] == [] and "ti aspettano nel tuo portale" not in seconda["testo"]
        # sui bandi solo "visti nel portale" niente novita' per email (il da_verificare scade entro 14 giorni)
        assert all(a["bando_id"] not in visti for a in seconda["contenuti"]["aggiornamenti"])


def _impresa_abituale(conn, bandi_segnalati: dict, email_il: date):
    """Impresa che ha gia' ricevuto un'email (preparata il giorno `email_il`) con i bandi indicati (bando -> data)."""
    utente = u.crea_utente(conn, f"impresa-{uuid.uuid4().hex[:8]}@esempio.it", "impresa", password="password-di-prova")
    with conn.cursor() as cur:
        cur.execute("UPDATE utenti SET email_confermata_il = now() WHERE id = %s", (utente["id"],))
    i = imp.crea(conn, utente["id"], "Cliente Abituale srl",
                 {"forma_giuridica": "srl", "dimensione": "piccola", "sedi": [{"provincia": "MI"}]})
    with conn.cursor() as cur:
        cur.execute("""INSERT INTO email_imprese (impresa_id, settimana, bandi, oggetto, testo, stato, creata_il)
                       VALUES (%s, %s, '[]', 'prima', 'prima', 'inviata', %s) RETURNING id""",
                    (i["id"], ei.settimana_iso(email_il), email_il))
        email_id = cur.fetchone()["id"]
        for bando_id, quando in bandi_segnalati.items():
            cur.execute("""INSERT INTO bandi_segnalati (impresa_id, bando_id, email_id, segnalato_il)
                           VALUES (%s, %s, %s, %s)""", (i["id"], bando_id, email_id, quando))
    conn.commit()
    return i


@db
def test_cliente_abituale_massimo_15(ambiente):
    from app.db.connessione import connetti

    ricchi = _bandi_liberi(17, 100000)
    with connetti() as conn:
        i = _impresa_abituale(conn, {}, OGGI - timedelta(days=7))
        ei.prepara(conn, OGGI)
        [e] = [x for x in _email_di(conn, i["id"]) if x["settimana"] == "2026-W41"]
        assert [b["bando_id"] for b in e["bandi"]] == ricchi[:15] and not e["contenuti"]["benvenuto"]
        assert e["contenuti"]["visti_portale"] == ricchi[15:]
        assert "NUOVI BANDI ADATTI" in e["testo"] and "Benvenuto" not in e["oggetto"]
        assert "Altri 2 bandi adatti ti aspettano nel tuo portale" in e["testo"]


@db
def test_bandi_chiusi_solo_recenti_e_errori_di_qualita(ambiente):
    """Tra i bandi segnalati: chiuso 2 giorni fa -> nell'email, in fondo; scaduto 20 giorni fa -> niente; chiuso nel
    2025 ma segnalato una settimana fa -> non nell'email, diventa una segnalazione nella plancia (una sola)."""
    from app.db.connessione import connetti

    liberi = {k: "nessun_vincolo" for k in regole.NOMI_VINCOLI}
    settimana_fa = OGGI - timedelta(days=7)
    with connetti() as conn:
        with conn.cursor() as cur:
            recente = _bando(cur, "Chiuso da poco", OGGI + timedelta(days=30), liberi)
            vecchio = _bando(cur, "Scaduto da tempo", OGGI - timedelta(days=20), liberi)
            sbagliato = _bando(cur, "Chiuso da un anno", OGGI + timedelta(days=30), liberi)
            aperto = _bando(cur, "Ancora aperto in scadenza", OGGI + timedelta(days=6), liberi)
            nuovo = _bando(cur, "Bando nuovo della settimana", OGGI + timedelta(days=60), liberi)
        conn.commit()
        i = _impresa_abituale(conn, {recente: settimana_fa, vecchio: OGGI - timedelta(days=30),
                                     sbagliato: settimana_fa, aperto: settimana_fa}, settimana_fa)
        with conn.cursor() as cur:   # le chiusure arrivano dopo l'ultima email (nuova versione del bando)
            cur.execute("UPDATE bandi SET stato = 'chiuso', chiuso_il = %s WHERE id = %s", (OGGI - timedelta(days=2), recente))
            cur.execute("UPDATE bandi SET stato = 'chiuso' WHERE id = %s", (vecchio,))
            cur.execute("UPDATE bandi SET stato = 'chiuso', chiuso_il = '2025-10-13' WHERE id = %s", (sbagliato,))
        conn.commit()
        conteggi = ei.prepara(conn, OGGI)
        [e] = [x for x in _email_di(conn, i["id"]) if x["settimana"] == "2026-W41"]
        assert [b["bando_id"] for b in e["bandi"]] == [nuovo]
        aggiornati = {a["bando_id"]: a["eventi"] for a in e["contenuti"]["aggiornamenti"]}
        assert aggiornati == {aperto: ["in_scadenza"], recente: ["chiuso"]}
        t = e["testo"]
        assert (t.index("NUOVI BANDI ADATTI") < t.index("NOVITÀ SUI BANDI") < t.index("Ancora aperto")
                < t.index("SI SONO CHIUSI") < t.index("Chiuso da poco") < t.index("Richiedi supporto per la domanda»"))
        assert "Scaduto da tempo" not in t and "Chiuso da un anno" not in t and "13/10/2025" not in t
        assert "Ci scusiamo" not in t
        assert conteggi["errori_qualita"] == 1
        with conn.cursor() as cur:
            cur.execute("SELECT count(*) AS n FROM segnalazioni WHERE bando_id = %s AND tipo = 'stato_scadenza'", (sbagliato,))
            assert cur.fetchone()["n"] == 1
        ei.prepara(conn, OGGI + timedelta(days=1))   # stessa settimana: la segnalazione non si ripete
        with conn.cursor() as cur:
            cur.execute("SELECT count(*) AS n FROM segnalazioni WHERE bando_id = %s", (sbagliato,))
            assert cur.fetchone()["n"] == 1
