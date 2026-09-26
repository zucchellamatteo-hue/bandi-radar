"""IA nelle schede: spenta senza chiave, lotti, controllo degli id, schemi JSON, verifica delle schede.
Nessuna chiamata vera: un finto client prende il posto dell'API."""

import json
from datetime import date
from types import SimpleNamespace

import pytest

from app.schede import campi, ia


def test_senza_chiave_non_si_chiama_l_api(monkeypatch):
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    assert not ia.chiave_presente()
    with pytest.raises(ia.IASpenta):
        ia.nuovo_client()


def test_prompt_divisi_in_istruzioni_e_messaggio():
    for nome in ("prompt_smistamento.md", "prompt_scheda.md", "prompt_preliminare.md"):
        istruzioni, modello = ia.leggi_prompt(nome)
        assert istruzioni and modello.startswith("# ") and "<!--" not in istruzioni
    istruzioni, modello = ia.messaggio_smistamento(
        [{"id": 1, "ente": "CCIAA", "tipo_fonte": "camera", "territorio": "LOM", "titolo": "Bando A", "riassunto": "",
          "url": "https://x.it", "testo_pagina": "Contributo alle imprese"},
         {"id": 2, "ente": "Comune", "tipo_fonte": "capoluogo", "territorio": "LOM", "titolo": "Avviso B", "riassunto": "r",
          "url": "https://y.it"}], date(2026, 9, 25))
    assert "sono 2." in istruzioni and '<annuncio id="1">' in modello and '<annuncio id="2">' in modello
    assert "Inizio della pagina (quando il riassunto manca): Contributo alle imprese" in modello
    assert modello.count("Inizio della pagina") == 1 and "{{" not in modello and "{{" not in istruzioni
    # tutti i segnaposto delle istruzioni sono tra quelli che il programma riempie
    import re
    for nome, noti in (("prompt_smistamento.md", {"numero_annunci"}), ("prompt_preliminare.md", {"data_oggi"}),
                       ("prompt_scheda.md", set())):
        assert set(re.findall(r"\{\{(\w+)\}\}", ia.leggi_prompt(nome)[0])) <= noti, nome


def test_riempi():
    assert ia.riempi("a {{x}} {{#l}}[{{y}}]{{/l}} {{#vuota}}no{{/vuota}}", {"x": 1, "l": [{"y": 2}, {"y": 3}], "vuota": []}) == "a 1 [2][3] "


def test_controllo_degli_id():
    r = {"risposte": [{"id": 1, "esito": "rilevante", "motivo": "ok"}, {"id": 1, "esito": "non_rilevante", "motivo": "doppio"},
                      {"id": 9, "esito": "rilevante", "motivo": "sconosciuto"}, {"id": 3, "esito": "forse", "motivo": "?"}]}
    c = ia.controlla_smistamento([1, 2, 3], r)
    assert c.decisi == {1: ("rilevante", "ok")} and c.mancanti == {2, 3} and len(c.estranei) == 3


class FintoClient:
    """Risponde come l'API, con risposte preparate; la prima volta 'dimentica' l'ultimo annuncio del lotto."""

    def __init__(self):
        self.chiamate = []
        self.messages = SimpleNamespace(create=self.create)

    def create(self, **p):
        self.chiamate.append(p)
        ids = [int(x) for x in __import__("re").findall(r'<annuncio id="(\d+)">', p["messages"][0]["content"])]
        if len(self.chiamate) == 1:
            ids = ids[:-1]
        testo = json.dumps({"risposte": [{"id": i, "esito": "rilevante", "motivo": "contributo alle imprese"} for i in ids]})
        return SimpleNamespace(stop_reason="end_turn", content=[SimpleNamespace(type="text", text=testo)],
                               usage=SimpleNamespace(input_tokens=1000, output_tokens=50, cache_read_input_tokens=0,
                                                     cache_creation_input_tokens=0))


def test_smistamento_rimanda_i_mancanti():
    annunci = [{"id": i, "ente": "CCIAA", "tipo_fonte": "camera", "territorio": "LOM", "titolo": f"Bando {i}",
                "riassunto": "x", "url": "https://x.it"} for i in range(1, 21)]
    client, registrate = FintoClient(), []
    esito = ia.smista_lotto(client, annunci, date(2026, 9, 25), lambda *a: registrate.append(a))
    assert len(client.chiamate) == 2 and '<annuncio id="20">' in client.chiamate[1]["messages"][0]["content"]
    assert len(esito.decisi) == 20 and not esito.mancanti and len(registrate) == 2
    p = client.chiamate[0]
    assert p["model"] == "claude-haiku-4-5" and p["output_config"]["format"]["schema"] is ia.SCHEMA_SMISTAMENTO
    assert p["system"][0]["cache_control"] == {"type": "ephemeral"}


def test_lotti_da_venti():
    assert [len(x) for x in ia.lotti(list(range(45)))] == [20, 20, 5]


def test_risposte_rifiutate_o_tagliate():
    base = dict(content=[], usage=SimpleNamespace(input_tokens=1, output_tokens=1))
    assert ia.leggi_messaggio(SimpleNamespace(stop_reason="refusal", **base)).esito == "rifiutata"
    assert ia.leggi_messaggio(SimpleNamespace(stop_reason="max_tokens", **base)).esito == "incompleta"


def _oggetti(schema):
    if isinstance(schema, dict):
        if schema.get("type") == "object":
            yield schema
        for v in schema.values():
            yield from _oggetti(v)
    elif isinstance(schema, list):
        for v in schema:
            yield from _oggetti(v)


@pytest.mark.parametrize("schema", [ia.SCHEMA_SMISTAMENTO, ia.SCHEMA_PRELIMINARE, ia.SCHEMA_SCHEDA])
def test_schemi_validi_per_l_output_vincolato(schema):
    for o in _oggetti(schema):     # l'API chiede additionalProperties false e tutti i campi elencati
        assert o["additionalProperties"] is False and set(o["required"]) == set(o["properties"])
    testo = json.dumps(schema)
    for vietato in ("minimum", "maximum", "minLength", "maxLength"):
        assert f'"{vietato}"' not in testo


def test_preliminare():
    ok = {"per_imprese": "si", "edizione_in_corso": "si", "stato": "aperto", "testo_bando": "si"}
    assert ia.passa_preliminare(ok) == (True, "ok")
    assert not ia.passa_preliminare({**ok, "per_imprese": "no"})[0]          # 3055: enti pubblici
    assert not ia.passa_preliminare({**ok, "stato": "chiuso"})[0]            # 358: gia' chiuso
    assert not ia.passa_preliminare({**ok, "edizione_in_corso": "no"})[0]
    assert ia.passa_preliminare({**ok, "testo_bando": "solo_sintesi"})[0]   # si fa, ma la scheda sara' "solo_sintesi"


SCHEDA_FIERE = {
    "titolo": "Fiere internazionali in Lombardia - secondo sportello", "ente": "Regione Lombardia",
    "gestore": "Unioncamere Lombardia", "url": "https://www.bandi.regione.lombardia.it/x", "territorio": "Lombardia",
    "territorio_regioni": ["LOM"], "territorio_province": [], "territorio_comuni": [], "sede_richiesta": "da_attivare",
    "data_apertura": "2026-07-30", "ora_apertura": "10:00", "scadenza": None, "ora_scadenza": None, "chiuso_il": None,
    "modalita_selezione": "sportello_valutativo", "sintesi": "...", "a_chi_si_rivolge": "PMI",
    "soggetti_ammessi": ["impresa"], "forme_giuridiche_ammesse": [], "forme_giuridiche_escluse": [],
    "dimensioni_ammesse": ["micro", "piccola", "media"], "eta_impresa_min_mesi": None, "eta_impresa_max_mesi": None,
    "requisiti_speciali_obbligatori": [], "requisiti_speciali_premiali": ["nuova_impresa"],
    "dipendenti_min": None, "dipendenti_max": None, "fatturato_min": None, "fatturato_max": None,
    "codici_ateco": [], "codici_ateco_esclusi": ["A", "L"], "ateco_versione": "2025", "regime_aiuto": ["de_minimis"],
    "requisiti": "DURC...", "cosa_finanzia": "fiere", "tipo_agevolazione": "fondo_perduto", "tipi_agevolazione": ["fondo_perduto"],
    "tema": "internazionalizzazione", "temi": ["internazionalizzazione"], "categorie_spesa": ["fiere_eventi"],
    "contributo_massimo": 15000, "percentuale": 60, "fondo_perduto_massimo": 15000, "percentuale_fondo_perduto": 60,
    "finanziamento_massimo": None, "spesa_minima": 6000, "spesa_massima": None, "dotazione": 4668350, "spese_ammesse": "forfait",
    "linee": [], "completezza": "bando_ufficiale", "avvertenze": [],
    "vincoli": {"territorio": "vincolo", "soggetti": "vincolo", "forme_giuridiche": "nessun_vincolo", "dimensioni": "vincolo",
                "ateco": "vincolo", "eta_impresa": "nessun_vincolo", "requisiti_speciali": "nessun_vincolo",
                "dipendenti": "nessun_vincolo", "fatturato": "nessun_vincolo", "spesa": "vincolo", "regime_aiuto": "vincolo"},
}
SCHEDA_FIERE["fonti"] = [{"campo": c, "fonte": "allegato: Bando - art. A.3"} for c, v in SCHEDA_FIERE.items()
                         if v not in (None, [], "") and c not in ("titolo", "url", "vincoli", "completezza", "linee", "avvertenze")]


def test_scheda_buona_senza_problemi():
    documenti = [{"categoria": "bando", "testo": "x" * 5000}]
    assert ia.verifica_scheda(SCHEDA_FIERE, documenti) == []


def test_verifica_scheda_trova_gli_errori_della_prova():
    s = json.loads(json.dumps(SCHEDA_FIERE))
    s.update({"dimensioni_ammesse": ["piccolissima"], "scadenza": "30/11/2026", "data_apertura": "2026-12-01",
              "contributo_massimo": 99999998000, "percentuale": 120, "ora_scadenza": "16"})
    s["vincoli"]["forme_giuridiche"] = "vincolo"
    s["fonti"] = [f for f in s["fonti"] if f["campo"] != "dotazione"]
    problemi = " | ".join(ia.verifica_scheda(s, [{"categoria": "pagina", "testo": "breve"}]))
    for atteso in ("valore non ammesso 'piccolissima'", "scadenza: data non valida", "importo non plausibile",
                   "percentuale oltre 100", "ora_scadenza: ora non valida", "vincoli.forme_giuridiche = vincolo",
                   "campi senza fonte: dotazione", "completezza 'bando_ufficiale'"):
        assert atteso in problemi, atteso


def test_misto_al_cento_per_cento():
    s = {**SCHEDA_FIERE, "tipo_agevolazione": "misto", "percentuale": 100, "finanziamento_massimo": 240000}
    assert any("mista al 100%" in p for p in ia.verifica_scheda(s))


def test_colonne_della_scheda_esistono():
    # ogni campo salvato ha una colonna (migrazioni 004 e 007): nessun UPDATE su colonne inesistenti
    from pathlib import Path

    sql = " ".join(p.read_text() for p in (Path(__file__).resolve().parents[1] / "app" / "db" / "migrazioni").glob("*.sql"))
    for c in ia._COLONNE_SCHEDA:
        assert f" {c} " in sql, c
    assert set(campi.VINCOLI) == set(ia.SCHEMA_SCHEDA["properties"]["vincoli"]["properties"])


@pytest.mark.skipif(not __import__("os").environ.get("PGHOST"), reason="serve un database Postgres di prova (PGHOST)")
def test_scheda_salvata_nella_tabella_bandi():
    from app.db.connessione import connetti
    from app.db.migrazioni import applica_migrazioni

    with connetti() as conn:
        applica_migrazioni(conn)
        with conn.cursor() as cur:
            cur.execute("INSERT INTO bandi (titolo, stato) VALUES ('prova scheda', 'aperto') RETURNING id")
            bando = cur.fetchone()["id"]
        conn.commit()
        try:
            ia.salva_scheda(conn, bando, SCHEDA_FIERE, [], 0.05)
            with conn.cursor() as cur:
                cur.execute("SELECT * FROM bandi WHERE id = %s", (bando,))
                b = cur.fetchone()
            assert b["gestore"] == "Unioncamere Lombardia" and b["codici_ateco_esclusi"] == ["A", "L"]
            assert b["vincoli"]["ateco"] == "vincolo" and b["completezza"] == "bando_ufficiale"
            assert str(b["ora_apertura"]) == "10:00:00" and b["stato"] == "aperto"      # lo stato non lo scrive l'IA
            assert b["dati"]["fonti"]["gestore"].startswith("allegato") and b["versione"] == 2
        finally:
            with conn.cursor() as cur:
                cur.execute("DELETE FROM bandi WHERE id = %s", (bando,))
            conn.commit()


def test_dettagli_per_il_commercialista_nello_schema_e_nei_controlli():
    # I sei blocchi chiesti da Matteo il 25/09: nello schema della risposta e controllati come gli altri campi.
    for blocco in ("intensita", "finanziamento", "vincoli_spese", "esclusioni", "obblighi", "domanda", "contributo_minimo"):
        assert blocco in ia.SCHEMA_SCHEDA["required"]
    assert set(ia.SCHEMA_SCHEDA["properties"]["vincoli_spese"]["properties"]) == set(campi.VINCOLI_SPESA)
    scheda = {
        "percentuale": 60,
        "intensita": {"percentuale_base": 70, "maggiorazioni": [{"motivo": "simpatia", "punti_percentuali": 5}]},
        "finanziamento": {"quota_fondo_perduto": 130, "tasso_tipo": "zero"},
        "vincoli_spese": {"fornitore": {"stato": "vincolo", "dettaglio": None}, "iva": {"stato": "non_noto", "dettaglio": None}},
        "esclusioni": {"soggetti": ["impresa_difficolta", "antipatia"]},
    }
    problemi = ia._verifica_dettagli(scheda)
    assert "intensita.maggiorazioni.motivo: valore non ammesso 'simpatia'" in problemi
    assert "esclusioni.soggetti: valore non ammesso 'antipatia'" in problemi
    assert "finanziamento.quota_fondo_perduto: percentuale oltre 100 (130)" in problemi
    assert "intensita.percentuale_base superiore alla percentuale massima" in problemi
    assert "vincoli_spese.fornitore = vincolo, ma manca il dettaglio" in problemi
    assert not ia._pieno({"iva": {"stato": "non_noto", "dettaglio": None}})
