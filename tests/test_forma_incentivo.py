"""Forma dell'incentivo (02/10): ricavata dai campi delle schede vecchie, controlli e pulizia di quella compilata."""
from decimal import Decimal

from app.schede import forma_incentivo, ia


def test_ricava_misto_prestito_e_fondo_perduto():
    b = {"tipi_agevolazione": ["finanziamento_agevolato", "fondo_perduto"], "percentuale_fondo_perduto": Decimal("20"),
         "fondo_perduto_massimo": Decimal("200000"), "finanziamento_massimo": Decimal("700000"),
         "finanziamento": {"percentuale_finanziamento": 70, "tasso_tipo": "zero", "durata_mesi": 96, "preammortamento_mesi": 24},
         "spesa_minima": 50000, "spesa_massima": None}
    fi = forma_incentivo.ricava(b)
    assert fi["ricavata"] and len(fi["righe"]) == 1
    forme = fi["righe"][0]["forme"]
    assert [f["forma"] for f in forme] == ["fondo_perduto", "finanziamento_agevolato"]
    assert forme[1]["percentuale"] == 70 and forme[1]["massimale"] == Decimal("700000")
    assert "tasso zero" in forme[1]["condizioni"] and "preammortamento 24 mesi" in forme[1]["condizioni"]
    assert fi["descrizione"].startswith("Fondo perduto 20% (fino a 200.000 €) + finanziamento agevolato 70%")


def test_ricava_per_dimensione_e_linee():
    b = {"tipi_agevolazione": ["fondo_perduto"], "percentuale": 60, "contributo_massimo": 3000000,
         "intensita": {"per_dimensione": {"micro": 60, "piccola": 60, "media": 50, "grande": None},
                       "maggiorazioni": [{"motivo": "femminile", "punti_percentuali": 5, "note": None}]}}
    fi = forma_incentivo.ricava(b)
    assert [r["per_chi"] for r in fi["righe"]] == ["Micro imprese", "Piccole imprese", "Medie imprese"]
    assert fi["righe"][2]["forme"][0]["percentuale"] == 50
    assert fi["note"] == "Maggiorazioni: femminile +5%"
    b["linee"] = [{"nome": "Asse I", "contributo_massimo": 19200, "percentuale": None},
                  {"nome": "Asse III", "contributo_massimo": 75000, "percentuale": 80}]
    righe = forma_incentivo.ricava(b)["righe"]
    assert [(r["per_chi"], r["forme"][0]["percentuale"], r["forme"][0]["massimale"]) for r in righe] == [
        ("Asse I", 60, 19200), ("Asse III", 80, 75000)]


def test_senza_tipo_niente_e_compilata_vince():
    assert forma_incentivo.ricava({"percentuale": 50}) is None
    compilata = {"descrizione": "Voucher", "righe": [{"per_chi": "Tutti", "forme": [{"forma": "voucher"}]}], "note": None}
    assert forma_incentivo.per_la_plancia({"forma_incentivo": compilata, "tipi_agevolazione": ["fondo_perduto"]})["ricavata"] is False
    vuota = {"descrizione": None, "righe": [], "note": None}
    assert forma_incentivo.per_la_plancia({"forma_incentivo": vuota, "tipi_agevolazione": ["servizi"]})["ricavata"] is True


def test_controlli_e_pulizia():
    fi = {"descrizione": "x", "righe": [{"per_chi": "Tutti", "forme": [
        {"forma": "fondo_perduto", "percentuale": 60, "massimale": 1000, "condizioni": None},
        {"forma": "finanziamento_agevolato", "percentuale": 50, "massimale": None, "condizioni": None}]}], "note": None}
    assert any("sommano 110" in p for p in ia.verifica_forma_incentivo(fi))
    grezza = {"forma_incentivo": {"descrizione": "x", "righe": [{"per_chi": "Tutti", "forme": [
        {"forma": "prestito_magico", "percentuale": 10}, {"forma": "servizi", "percentuale": None}]}]}}
    scheda, tolti = ia.prepara_scheda(grezza)
    assert [f["forma"] for f in scheda["forma_incentivo"]["righe"][0]["forme"]] == ["servizi"]
    assert any("prestito_magico" in t for t in tolti)
    assert ia.prepara_scheda({})[0]["forma_incentivo"] == {"descrizione": None, "righe": [], "note": None}


def test_ricava_usa_la_percentuale_base():
    b = {"tipi_agevolazione": ["fondo_perduto"], "percentuale": 60, "contributo_massimo": 30000,
         "intensita": {"percentuale_base": 50, "maggiorazioni": [{"motivo": "rating_legalita", "punti_percentuali": 5}]},
         "linee": [{"nome": "Misura 1", "percentuale": 60, "contributo_massimo": 30000},
                   {"nome": "Misura 2", "percentuale": 40, "contributo_massimo": 5000}]}
    righe = forma_incentivo.ricava(b)["righe"]
    assert [r["forme"][0]["percentuale"] for r in righe] == [50, 40]
