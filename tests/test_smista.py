"""Smistamento a regole: parole chiave dal file YAML, ordine delle decisioni, regola ferma sulla parola "gara"."""

import pytest

from app.schede.smista import ErroreRegole, carica_regole, decidi, normalizza

REGOLE = carica_regole()


def esito(titolo: str, riassunto: str | None = None) -> str:
    return decidi(titolo, riassunto, REGOLE).esito


@pytest.mark.parametrize("titolo", [
    "Bando voucher digitalizzazione PMI 2026",
    "Contributi a fondo perduto per le imprese del commercio",
    "Credito d’imposta per investimenti in beni strumentali",
    "Agevolazioni per l'internazionalizzazione",
    "Incentivi alle assunzioni nelle micro imprese",   # "assunzioni" da sola scarterebbe: vince il rilevante
    "Bando per startup innovative: nuova edizione",
    "Finanziamenti agevolati per la transizione green",
])
def test_rilevanti(titolo):
    assert esito(titolo) == "rilevante"


@pytest.mark.parametrize("titolo", [
    "Concorso pubblico per 3 istruttori amministrativi a tempo indeterminato",
    "Affidamento del servizio di pulizia degli uffici comunali - procedura negoziata",
    "Esito di gara - CIG 9876543210",
    "Pubblicazioni di matrimonio",
    "Estumulazioni ordinarie nel cimitero di via Roma",
    "Refezione scolastica: menu invernale",
    "Graduatoria provvisoria asili nido 2026/2027",
    "Interruzione idrica in via Garibaldi",
    "Ordinanza viabilità per la fiera di San Luca",
    "Elezioni comunali: nomina scrutatori",
])
def test_non_rilevanti(titolo):
    assert esito(titolo) == "non_rilevante"


def test_il_resto_e_da_rivedere():
    assert esito("Avviso pubblico per manifestazione di interesse") == "da_rivedere"
    assert decidi("Comunicato stampa", None, REGOLE).motivo == "regole: nessuna parola chiave"


def test_la_parola_gara_da_sola_non_scarta_mai_un_contributo():
    # Alcuni enti archiviano i contributi sotto "Bandi di gara" (CLAUDE.md).
    assert esito("Bandi di gara: contributi alle imprese per la digitalizzazione") == "rilevante"
    assert esito("Bando di gara", "Voucher per la partecipazione a fiere internazionali") == "rilevante"
    assert esito("Gara d'appalto per la concessione di contributi alle PMI") == "rilevante"
    # Senza segnali rilevanti, la gara vera si scarta.
    assert esito("Gara d'appalto per la manutenzione del verde pubblico") == "non_rilevante"


def test_parole_intere_e_accenti():
    assert esito("Garanzia sui prestiti") == "da_rivedere"          # "gara" non scatta dentro "garanzia"
    assert normalizza("Bonus Bebè – Città") == "bonus bebe – citta"
    assert esito("Bonus bebè: contributo per le famiglie") == "non_rilevante"


def test_contributi_ai_privati_scartati_ma_non_quelli_alle_imprese():
    d = decidi("Contributi per l'affitto 2026", "Domande entro il 30 ottobre", REGOLE)
    assert d.esito == "non_rilevante" and "affitto" in d.motivo and "contribut*" in d.motivo
    assert esito("Contributi per l'affitto dei locali delle attività commerciali") == "rilevante"


def test_il_motivo_dice_quale_regola_e_scattata():
    d = decidi("Nuovo voucher export", None, REGOLE)
    assert d.motivo == "regole: rilevante/voucher: 'voucher'"


def test_gara_vietata_tra_i_contributi_per_privati(tmp_path):
    f = tmp_path / "regole.yaml"
    f.write_text(
        "rilevante: [{gruppo: a, parole: [contributo]}]\n"
        "non_rilevante: [{gruppo: b, parole: [concorso]}]\n"
        "contributi_non_per_imprese: [{gruppo: c, parole: [bando di gara]}]\n", encoding="utf-8")
    with pytest.raises(ErroreRegole, match="gare e appalti"):
        carica_regole(f)


def test_file_regole_mal_formato(tmp_path):
    f = tmp_path / "regole.yaml"
    f.write_text("rilevanti: []\n", encoding="utf-8")
    with pytest.raises(ErroreRegole, match="sezioni non previste"):
        carica_regole(f)


def test_gruppo_con_parole_combinate():
    # "bando" da solo non basta; "bando" + "imprese" si'.
    assert esito("Bando Innevamento 2026") == "da_rivedere"
    d = decidi("Misura per lo sviluppo tecnologico delle startup innovative", None, REGOLE)
    assert d.esito == "rilevante"
    d = decidi("Fondo per l'insediamento dei giovani agricoltori", None, REGOLE)
    assert d.motivo == "regole: rilevante/bando_o_misura_per_imprese: 'fondo' + 'agricoltori'"
