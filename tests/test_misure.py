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


def test_misure_aperte_hanno_gli_aspetti_fiscali():
    """Revisione del 07/10/2026: ogni misura aperta dice come si tassa il beneficio (IRES/IRPEF/IRAP), e l'API lo passa."""
    for m in misure.tutte():
        if m["stato"] == "aperto":
            assert len(m.get("fiscale") or "") > 80 and "IRAP" in m["fiscale"], m["id"]
    assert "fiscale" in misure.una("iperammortamento_2026")


def test_esempi_per_tutti_i_profili():
    """Ogni misura aperta ha un esempio per ciascun profilo tipo, con un profilo che esiste e un interesse valido."""
    profili = [p["id"] for p in misure.profili_esempio()]
    assert len(profili) >= 6 and len(set(profili)) == len(profili)
    assert all(p.get("nome") and p.get("descrizione") for p in misure.profili_esempio())
    for m in misure.tutte():
        if m["stato"] != "aperto":
            continue
        esempi = m.get("esempi") or []
        usati = [e["profilo"] for e in esempi]
        assert set(usati) <= set(profili), (m["id"], set(usati) - set(profili))
        assert sorted(usati) == sorted(profili), (m["id"], "profili mancanti o doppi")
        for e in esempi:
            assert e.get("interesse") in misure.INTERESSI and len(e.get("esempio") or "") > 40, (m["id"], e["profilo"])
            assert e["profilo_nome"] != e["profilo"]                        # il nome arriva dall'elenco dei profili
        assert [misure.INTERESSI.index(e["interesse"]) for e in esempi] == sorted(
            misure.INTERESSI.index(e["interesse"]) for e in esempi), m["id"]   # ordinati per interesse


def test_esempi_letti_dal_file(tmp_path):
    f = tmp_path / "misure.yaml"
    f.write_text("""
profili_esempio:
  - {id: ufficio, nome: Ufficio}
misure:
  - id: x
    nome: X
    esempi:
      - {profilo: ufficio, interesse: basso, esempio: poco}
      - {profilo: altro, interesse: alto, esempio: molto}
""")
    esempi = misure.tutte(f)[0]["esempi"]
    assert [e["interesse"] for e in esempi] == ["alto", "basso"]
    assert [e["profilo_nome"] for e in esempi] == ["altro", "Ufficio"]
    assert misure.profili_esempio(f) == [{"id": "ufficio", "nome": "Ufficio"}]
    assert "profilo_nome" not in misure._carica(f)[0][0]["esempi"][0]      # la copia in memoria resta com'era


def test_misure_nuove_per_l_email(tmp_path):
    from datetime import date

    f = tmp_path / "misure.yaml"
    f.write_text("""
misure:
  - {id: nuova, nome: Nuova, stato: aperto, aggiunta_il: 2026-10-06, sintesi: "Una misura nuova."}
  - {id: vecchia, nome: Vecchia, stato: aperto, aggiunta_il: 2026-08-01}
  - {id: chiusa, nome: Chiusa, stato: chiuso, aggiunta_il: 2026-10-06}
  - {id: senza_data, nome: Senza data, stato: aperto}
  - {id: grandi, nome: Solo grandi, stato: aperto, aggiunta_il: 2026-10-05, dimensioni_ammesse: [grande]}
  - {id: sud, nome: Solo Sud, stato: aperto, aggiunta_il: "2026-10-05", regioni: [CAM]}
""")
    oggi = date(2026, 10, 12)
    milano = {"soggetto": "impresa", "dimensione": "piccola", "sedi": [{"provincia": "MI", "regione": "LOM"}]}
    assert [m["id"] for m in misure.nuove_per_profilo(milano, oggi, 30, percorso=f)] == ["nuova"]
    assert misure.nuove_per_profilo(milano, oggi, 30, {"nuova"}, percorso=f) == []           # gia' mandata
    napoli = {**milano, "sedi": [{"provincia": "NA", "regione": "CAM"}]}
    assert [m["id"] for m in misure.nuove_per_profilo(napoli, oggi, 30, percorso=f)] == ["nuova", "sud"]
    assert misure.nuove_per_profilo(milano, date(2026, 10, 5), 30, percorso=f) == []         # non ancora aggiunta
    assert misure.nuove_per_profilo(milano, oggi, 30, percorso=f)[0]["sintesi"] == "Una misura nuova."


def test_misure_vere_hanno_la_data_di_aggiunta():
    from datetime import date

    aperte = [m for m in misure.tutte() if m.get("stato") == "aperto"]
    assert aperte and all(isinstance(m.get("aggiunta_il"), date) for m in aperte)
