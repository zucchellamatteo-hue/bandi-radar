"""Pagina "I miei bandi" (07/10): agevolazione in una riga, motivi semplici, gruppi e ordine, misure per tipo di impresa."""

from datetime import date, datetime

from app import misure
from app.abbinamento import regole
from app.impresa import vista

OGGI = date(2026, 10, 7)


def test_agevolazione_in_una_riga():
    assert vista.agevolazione({"tipi_agevolazione": ["fondo_perduto"], "percentuale": 50, "contributo_massimo": 20000}) \
        == "Fondo perduto 50%, fino a 20.000 €"
    assert vista.agevolazione({"tipi_agevolazione": ["finanziamento_agevolato", "fondo_perduto"], "percentuale_fondo_perduto": 20,
                               "finanziamento_massimo": 200000}) == "Fondo perduto 20% + finanziamento agevolato, fino a 200.000 €"
    assert vista.agevolazione({"tipi_agevolazione": ["credito_imposta"]}) == "Credito d'imposta"
    assert vista.agevolazione({"tipi_agevolazione": ["altro"]}) == "Agevolazione da leggere nella scheda"


def test_motivi_semplici():
    e = regole.Esito(livello=regole.DA_VERIFICARE, da_verificare=["manca il codice ATECO", "settori ammessi non noti",
                                                                  "serve impresa femminile: dato mancante nel profilo"])
    assert vista.motivi_semplici(e) == ["indica il codice ATECO: serve a capire se il tuo settore è ammesso",
                                        "serve verificare il codice ATECO", "riservato a impresa femminile: indica se lo sei"]
    assert vista.motivo(e).startswith("Indica il codice ATECO")
    ok = regole.Esito(punti_a_favore=["sede in Lombardia", "micro impresa ammessa"])
    assert vista.motivo(ok) == "Requisiti rispettati: sede in Lombardia; micro impresa ammessa"


def test_gruppi_ordine_scadenza_e_nuovo():
    adatto = regole.Esito()
    dubbio = regole.Esito(livello=regole.DA_VERIFICARE, da_verificare=["x"])
    lontano = regole.Esito(livello=regole.DA_VERIFICARE, da_verificare=["x"], fuori_zona=True)
    prestito = {"id": 1, "tipi_agevolazione": ["finanziamento_agevolato"], "scadenza": date(2026, 10, 10)}
    fp_tardi = {"id": 2, "tipi_agevolazione": ["fondo_perduto"], "scadenza": date(2026, 12, 1)}
    fp_presto = {"id": 3, "tipi_agevolazione": ["voucher"], "scadenza": date(2026, 11, 1)}
    fp_senza = {"id": 4, "tipi_agevolazione": ["fondo_perduto"], "scadenza": None}
    altrove = {"id": 5, "tipi_agevolazione": ["fondo_perduto"], "scadenza": date(2026, 10, 8)}
    ordinati = vista.ordina([(altrove, lontano), (prestito, dubbio), (fp_senza, dubbio), (fp_tardi, dubbio),
                             (fp_presto, dubbio), (prestito | {"id": 6}, adatto)])
    # adatti, poi da valutare (fondo perduto prima, poi per scadenza, senza scadenza in fondo), poi altre regioni
    assert [b["id"] for b, _ in ordinati] == [6, 3, 2, 4, 1, 5]
    r = vista.arricchisci({"esito": dubbio.come_dict()}, {**prestito, "scheda_il": datetime(2026, 10, 3, 9)}, dubbio, OGGI)
    assert r["gruppo"] == "da_valutare" and r["in_scadenza"] and r["giorni_alla_scadenza"] == 3 and r["nuovo"]
    vecchio = vista.arricchisci({"esito": adatto.come_dict()}, {**fp_tardi, "scheda_il": datetime(2026, 9, 20)}, adatto, OGGI)
    assert vecchio["gruppo"] == "adatti" and not vecchio["in_scadenza"] and not vecchio["nuovo"]
    c = vista.conteggi([r, vecchio])
    assert c["adatti"] == 1 and c["da_valutare"] == 1 and c["in_scadenza"] == 1 and c["nuovi"] == 1


def test_misure_per_tipo_di_impresa():
    assert misure.tipo_di_impresa({"ateco": ["56.10.11"]}) == "ristorazione_ricettivo"
    assert misure.tipo_di_impresa({"ateco": ["26.51.29"], "dipendenti": 5}) == "artigiano"
    assert misure.tipo_di_impresa({"ateco": ["25.11"], "dimensione": "media"}) == "manifattura"
    assert misure.tipo_di_impresa({"ateco": ["62.01"], "requisiti": {"startup_innovativa": True}}) == "startup"
    assert misure.tipo_di_impresa({"ateco": ["62.01"]}) == "ufficio_servizi"
    assert misure.tipo_di_impresa({"ateco": []}) is None
    r = misure.per_profilo({"soggetto": "impresa", "dimensione": "micro", "ateco": ["56.10"],
                            "sedi": [{"regione": "LOM"}]})
    assert r["tipo"]["id"] == "ristorazione_ricettivo" and r["misure"]
    ids = [m["id"] for m in r["misure"]]
    assert "credito_zes_unica_2026" not in ids                          # solo per le regioni ZES
    assert all(m["esempio"] is None or m["esempio"]["interesse"] != "nullo" for m in r["misure"])
    interessi = [m["esempio"]["interesse"] for m in r["misure"] if m["esempio"]]
    assert interessi == sorted(interessi, key=misure.INTERESSI.index)  # prima le piu' interessanti
