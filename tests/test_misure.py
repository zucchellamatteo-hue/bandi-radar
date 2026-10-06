"""Misure nazionali: lettura del file, misure che si sommano a un bando, frase per le campagne, file vero valido."""

from app import misure

YAML = """
misure:
  - id: iper
    nome: Iperammortamento
    tipo: maggiorazione_ammortamento
    stato: aperto
    soggetti_ammessi: [impresa]
    categorie_spesa: [macchinari_attrezzature, software_digitale]
    beneficio_stimato: {percentuale_min: 20, percentuale_max: 43}
    cumulabilita: {con_fondo_perduto: nei_limiti, regola: "fino al costo sostenuto"}
  - id: termico
    nome: Conto Termico
    tipo: contributo_conto_capitale
    stato: aperto
    dimensioni_ammesse: [micro, piccola, media]
    categorie_spesa: [energia_efficienza]
    beneficio_stimato: {percentuale_min: 40, percentuale_max: 65}
    cumulabilita: {con_fondo_perduto: "no"}
  - id: vecchia
    nome: Vecchia misura
    stato: da_verificare
    categorie_spesa: [macchinari_attrezzature]
    cumulabilita: {con_fondo_perduto: si}
"""


def test_misure_che_si_sommano(tmp_path):
    f = tmp_path / "misure.yaml"
    f.write_text(YAML)
    assert [m["id"] for m in misure.tutte(f)] == ["iper", "termico", "vecchia"]
    bando = {"categorie_spesa": ["macchinari_attrezzature", "energia_efficienza"]}
    trovate = misure.cumulabili(bando, None, f)
    assert [m["id"] for m in trovate] == ["iper"]            # termico non cumulabile, vecchia non in vigore
    assert trovate[0]["spese_in_comune"] == ["macchinari_attrezzature"]
    assert misure.cumulabili({"categorie_spesa": []}, None, f) == []
    assert misure.cumulabili(bando, {"soggetto": "libero_professionista"}, f) == []
    frase = misure.frase_cumulo(trovate)
    assert "Iperammortamento (circa 20-43% della spesa non coperta dal bando)" in frase and "indicativa" in frase
    assert misure.una("termico", f)["nome"] == "Conto Termico" and misure.una("x", f) is None
    assert misure.cumulabili({**bando, "titolo": "Iperammortamento 2026"}, None, f) == []   # il bando e' la misura


def test_misure_solo_per_alcune_regioni(tmp_path):
    f = tmp_path / "misure.yaml"
    f.write_text("""
misure:
  - {id: zes, nome: ZES, stato: aperto, regioni: [PUG, SIC], categorie_spesa: [macchinari_attrezzature],
     cumulabilita: {con_fondo_perduto: nei_limiti}}
""")
    bando = {"categorie_spesa": ["macchinari_attrezzature"], "territorio_regioni": ["LOM"]}
    assert misure.cumulabili(bando, None, f) == []
    assert len(misure.cumulabili({**bando, "territorio_regioni": ["PUG"]}, None, f)) == 1
    assert len(misure.cumulabili(bando, {"sedi": [{"regione": "SIC"}]}, f)) == 1      # conta la sede dell'impresa


def test_misure_chiuse_mai_sommate():
    """Le misure chiuse stanno nella pagina (in fondo) ma non si propongono mai insieme ai bandi."""
    chiuse = {m["id"] for m in misure.tutte() if m["stato"] == "chiuso"}
    bando = {"categorie_spesa": ["macchinari_attrezzature", "software_digitale", "energia_efficienza", "ricerca_sviluppo",
                                 "formazione", "opere_edili_impianti"], "territorio_regioni": ["PUG"]}
    assert chiuse and not chiuse & {m["id"] for m in misure.cumulabili(bando)}


def test_file_delle_misure_valido():
    """Il file vero (scritto e verificato a mano): ogni voce ha i campi che servono alla plancia."""
    for m in misure.tutte():
        assert m.get("stato") in ("aperto", "da_verificare", "chiuso"), m["id"]
        assert m.get("sintesi") and m.get("ente"), m["id"]
        assert (m.get("cumulabilita") or {}).get("con_fondo_perduto") in ("si", "no", "nei_limiti", "da_verificare"), m["id"]
        b = m.get("beneficio_stimato") or {}
        if b.get("percentuale_max") is not None:
            assert 0 <= float(b["percentuale_min"]) <= float(b["percentuale_max"]) <= 100, m["id"]
