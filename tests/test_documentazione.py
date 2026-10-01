from app.schede.documentazione import valuta

REGOLAMENTO = ("Art. 1 Finalita'. Art. 2 Beneficiari: le micro, piccole e medie imprese. Art. 3 Requisiti di ammissione. "
               "Art. 4 Spese ammissibili: macchinari e consulenze. Art. 5 Intensita' dell'aiuto: contributo massimo "
               "del 50 per cento, in regime de minimis ai sensi del regolamento (UE) 2831/2023. Art. 6 Presentazione "
               "della domanda entro il termine del 30 novembre. Art. 7 Istruttoria e valutazione. Art. 8 Erogazione "
               "e rendicontazione. ") * 12


def doc(testo, tipo="pdf", categoria="bando", nome="Bando 2026"):
    return {"nome": nome, "tipo": tipo, "categoria": categoria, "testo_estratto": testo, "errore": None}


def test_c_e_il_bando():
    esito, motivo = valuta([doc(REGOLAMENTO), doc("Pagina del bando", "pagina", "pagina")])
    assert esito == "bando" and "Bando 2026" in motivo


def test_una_pagina_web_anche_lunga_e_solo_sintesi():
    # Le pagine descrittive (myCIVIS, Finlombarda, catalogo) non sono il bando: l'IA le ha giudicate sintesi.
    assert valuta([doc(REGOLAMENTO, "pagina", "pagina")])[0] == "sintesi"


def test_modulistica_graduatorie_e_documenti_brevi_non_bastano():
    assert valuta([doc(REGOLAMENTO, categoria="modulistica"), doc(REGOLAMENTO, categoria="graduatoria")])[0] == "sintesi"
    assert valuta([doc(REGOLAMENTO[:1500])])[0] == "sintesi"
    assert valuta([doc("Il bando apre a novembre: domande dal sito. " * 100)])[0] == "sintesi"


def test_niente_di_leggibile():
    assert valuta([])[0] == "nessuno"
    assert valuta([doc("TXLVLWL\x03JHQHUDOL\x03GL\x03DPPLVVLELOLWj " * 200)])[0] == "nessuno"
    assert valuta([{**doc(REGOLAMENTO), "errore": "troppo grande"}])[0] == "nessuno"
