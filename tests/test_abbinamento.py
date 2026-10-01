from datetime import date

from app.abbinamento import ateco, catalogo, regole
from app.abbinamento.regole import COMPATIBILE, DA_VERIFICARE, ESCLUSO, classe_dimensionale, valuta

OGGI = date(2026, 9, 29)
TUTTI_LIBERI = {k: "nessun_vincolo" for k in ("territorio", "soggetti", "forme_giuridiche", "dimensioni", "ateco",
                                             "eta_impresa", "requisiti_speciali", "dipendenti", "fatturato", "spesa",
                                             "regime_aiuto")}


def bando(**campi):
    base = {"id": 1, "titolo": "Bando", "stato": "aperto", "completezza": "bando_ufficiale", "vincoli": dict(TUTTI_LIBERI),
            "scadenza": date(2026, 12, 31)}
    vincoli = campi.pop("vincoli", {})
    base["vincoli"].update(vincoli)
    return {**base, **campi}


SRL_MILANO = {"soggetto": "impresa", "forma_giuridica": "srl", "dimensione": "piccola", "ateco": ["62.01.00"],
              "sedi": [{"tipo": "legale_e_operativa", "regione": "LOM", "provincia": "MI", "comune": "Milano"}],
              "data_costituzione": "2018-03-01", "dipendenti": 20, "fatturato": 3_000_000,
              "requisiti": {"femminile": False, "giovanile": False}}


def test_ateco_normalizza_e_contiene():
    assert ateco.normalizza("6201") == "62.01"
    assert ateco.normalizza("1.1") == "01.1"
    assert ateco.normalizza("c") == "C"
    assert ateco.normalizza("tutti") is None
    assert ateco.contiene("62", "62.01.00") == "si"
    assert ateco.contiene("47.1", "47.11.00") == "si"
    assert ateco.contiene("47.11", "47.1") == "forse"
    assert ateco.contiene("47.2", "47.11") == "no"
    # 62 e' J nel 2007 e K nel 2025
    assert ateco.contiene("J", "62.01", "2007") == "si"
    assert ateco.contiene("K", "62.01", "2025") == "si"
    assert ateco.contiene("J", "62.01", "2025") == "no"


def test_tutto_libero_e_compatibile():
    e = valuta(bando(), SRL_MILANO, OGGI)
    assert e.livello == COMPATIBILE and not e.da_verificare


def test_non_noto_non_e_mai_compatibile():
    e = valuta(bando(vincoli={"dimensioni": "non_noto"}), SRL_MILANO, OGGI)
    assert e.livello == DA_VERIFICARE
    assert "dimensioni ammesse non note" in e.da_verificare


def test_scheda_su_sintesi_al_massimo_da_verificare():
    assert valuta(bando(completezza="solo_sintesi"), SRL_MILANO, OGGI).livello == DA_VERIFICARE


def test_territorio_regione_provincia_comune():
    lombardia = bando(vincoli={"territorio": "vincolo"}, territorio_regioni=["LOM"])
    assert valuta(lombardia, SRL_MILANO, OGGI).livello == COMPATIBILE
    puglia = bando(vincoli={"territorio": "vincolo"}, territorio_regioni=["PUG"])
    e = valuta(puglia, SRL_MILANO, OGGI)
    assert e.livello == ESCLUSO and "Puglia" in e.esclusioni[0]
    # Regione e una sua provincia: vale la provincia (il piu' preciso).
    solo_bergamo = bando(vincoli={"territorio": "vincolo"}, territorio_regioni=["LOM"], territorio_province=["BG"])
    assert valuta(solo_bergamo, SRL_MILANO, OGGI).livello == ESCLUSO
    comune = bando(vincoli={"territorio": "vincolo"}, territorio_comuni=["Comune di Milano"])
    assert valuta(comune, SRL_MILANO, OGGI).livello == COMPATIBILE
    senza_comune = {**SRL_MILANO, "sedi": [{"regione": "LOM", "provincia": "MI"}]}
    assert valuta(comune, senza_comune, OGGI).livello == DA_VERIFICARE


def test_territorio_sede_operativa_e_da_attivare():
    operativa = bando(vincoli={"territorio": "vincolo"}, territorio_regioni=["EMR"], sede_richiesta="operativa")
    due_sedi = {**SRL_MILANO, "sedi": [{"tipo": "legale", "regione": "LOM", "provincia": "MI"},
                                       {"tipo": "operativa", "regione": "EMR", "provincia": "BO"}]}
    assert valuta(operativa, due_sedi, OGGI).livello == COMPATIBILE
    legale = {**operativa, "sede_richiesta": "legale"}
    assert valuta(legale, due_sedi, OGGI).livello == ESCLUSO
    da_attivare = {**operativa, "sede_richiesta": "da_attivare"}
    e = valuta(da_attivare, SRL_MILANO, OGGI)   # si puo' partecipare solo aprendo una sede: da decidere col cliente
    assert e.livello == DA_VERIFICARE and e.fuori_zona and any("aprirne una" in x for x in e.da_verificare)
    assert valuta(da_attivare, due_sedi, OGGI).livello == COMPATIBILE


def test_territorio_ue_con_elenchi_vuoti():
    ue = bando(vincoli={"territorio": "vincolo"}, territorio="Stati membri UE e Paesi associati a Horizon Europe")
    assert valuta(ue, SRL_MILANO, OGGI).livello == COMPATIBILE
    a_parole = bando(vincoli={"territorio": "vincolo"}, territorio="area del cratere sismico")
    assert valuta(a_parole, SRL_MILANO, OGGI).livello == DA_VERIFICARE


def test_ateco_ammessi_esclusi_e_versioni():
    ammessi = bando(vincoli={"ateco": "vincolo"}, codici_ateco=["62", "63"], ateco_versione="2025")
    assert valuta(ammessi, SRL_MILANO, OGGI).livello == COMPATIBILE
    altri = bando(vincoli={"ateco": "vincolo"}, codici_ateco=["10", "11"], ateco_versione="2025")
    assert valuta(altri, SRL_MILANO, OGGI).livello == ESCLUSO
    # Tutti i settori tranne... : l'esclusione vale anche con nessun_vincolo.
    tranne = bando(codici_ateco_esclusi=["J", "K"], ateco_versione="2025")
    assert valuta(tranne, SRL_MILANO, OGGI).livello == ESCLUSO
    vecchia = bando(vincoli={"ateco": "vincolo"}, codici_ateco=["10"], ateco_versione="2007")
    assert valuta(vecchia, SRL_MILANO, OGGI).livello == DA_VERIFICARE


def test_dimensione_stimata_e_totale_di_bilancio():
    assert classe_dimensionale({"dipendenti": 20, "fatturato": 3_000_000}) == ("piccola", None)
    # 8 dipendenti ma 5 milioni di fatturato: piccola, ma micro se il totale di bilancio e' sotto 2 milioni.
    assert classe_dimensionale({"dipendenti": 8, "fatturato": 5_000_000}) == ("piccola", "micro")
    solo_micro = bando(vincoli={"dimensioni": "vincolo"}, dimensioni_ammesse=["micro"])
    assert valuta(solo_micro, {**SRL_MILANO, "dimensione": None, "dipendenti": 8, "fatturato": 5_000_000},
                  OGGI).livello == DA_VERIFICARE
    assert valuta(solo_micro, SRL_MILANO, OGGI).livello == ESCLUSO


def test_requisiti_speciali_e_eta():
    femminile = bando(vincoli={"requisiti_speciali": "vincolo"}, requisiti_speciali_obbligatori=["femminile"])
    assert valuta(femminile, SRL_MILANO, OGGI).livello == ESCLUSO
    assert valuta(femminile, {**SRL_MILANO, "requisiti": {"femminile": True}}, OGGI).livello == COMPATIBILE
    assert valuta(femminile, {**SRL_MILANO, "requisiti": {}}, OGGI).livello == DA_VERIFICARE
    startup = bando(vincoli={"eta_impresa": "vincolo"}, eta_impresa_max_mesi=36)
    assert valuta(startup, SRL_MILANO, OGGI).livello == ESCLUSO
    assert valuta(startup, {**SRL_MILANO, "da_costituire": True, "soggetto": None}, OGGI).livello == COMPATIBILE


def test_soggetti_e_forme():
    aspiranti = bando(vincoli={"soggetti": "vincolo"}, soggetti_ammessi=["aspirante_imprenditore"])
    assert valuta(aspiranti, SRL_MILANO, OGGI).livello == ESCLUSO
    srl = bando(vincoli={"forme_giuridiche": "vincolo"}, forme_giuridiche_ammesse=["srl", "spa"])
    assert valuta(srl, {**SRL_MILANO, "forma_giuridica": "srls"}, OGGI).livello == COMPATIBILE
    assert valuta(srl, {**SRL_MILANO, "forma_giuridica": "snc"}, OGGI).livello == ESCLUSO


def test_stato_e_ordine():
    chiuso = bando(stato="chiuso")
    assert valuta(chiuso, SRL_MILANO, OGGI).livello == ESCLUSO
    presto = bando(id=2, scadenza=date(2026, 10, 10))
    tardi = bando(id=3, scadenza=date(2026, 11, 10))
    dubbio = bando(id=4, scadenza=date(2026, 10, 1), completezza="solo_sintesi")
    risultato = catalogo.abbina([tardi, dubbio, presto, chiuso], SRL_MILANO, OGGI)
    assert [b["id"] for b, _ in risultato] == [2, 3]   # la scheda su una sintesi non si propone (01/10)
    disparte = catalogo.abbina([tardi, dubbio, presto, chiuso], SRL_MILANO, OGGI, in_disparte=True)
    assert [b["id"] for b, _ in disparte] == [4]


def test_catalogo_filtri_parziali():
    bandi = [
        {**bando(id=1, vincoli={"dimensioni": "vincolo"}, dimensioni_ammesse=["piccola", "media"]), "livelli": ["regione"]},
        {**bando(id=2), "livelli": ["camera"]},                                               # nessun vincolo
        {**bando(id=3, vincoli={"dimensioni": "non_noto"}), "livelli": ["regione"]},           # da verificare
        {**bando(id=4, vincoli={"dimensioni": "vincolo"}, dimensioni_ammesse=["micro"]), "livelli": ["regione"]},
    ]
    for b in bandi:
        b.setdefault("requisiti_speciali_obbligatori", [])
        b.setdefault("requisiti_speciali_premiali", [])
        for campo in ("tipi_agevolazione", "temi", "categorie_spesa", "regime_aiuto"):
            b.setdefault(campo, [])
        b.setdefault("modalita_selezione", None)
    trovati = catalogo.filtra(bandi, catalogo.Filtri(dimensione="piccola"), OGGI)
    assert [(b["id"], e.livello) for b, e in trovati] == [(1, COMPATIBILE), (2, COMPATIBILE), (3, DA_VERIFICARE)]
    # Senza filtri su chi partecipa, nessun vincolo si guarda.
    assert len(catalogo.filtra(bandi, catalogo.Filtri(), OGGI)) == 4
    assert [b["id"] for b, _ in catalogo.filtra(bandi, catalogo.Filtri(livello="camera"), OGGI)] == [2]
