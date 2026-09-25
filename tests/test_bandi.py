"""Deduplica annunci -> bandi, senza rete e senza database."""

from app.schede.bandi import (
    Annuncio, analizza_titolo, codice_ufficiale, ente_normalizzato, pianifica, ruolo_da_titolo,
    somiglianza, territorio_annuncio, url_chiave,
)


def ann(id, titolo, url=None, fonte="f1", ente="Camera di Commercio di Modena", territorio="EMR", dati=None, bando=None):
    return Annuncio(id, fonte, url or f"https://esempio.it/{fonte}/{id}", titolo, ente, territorio, dati, bando).prepara()


def test_codice_lombardia_da_indirizzo_e_dati():
    assert codice_ufficiale("https://www.bandi.regione.lombardia.it/bpm/web/la-mia-area/domande/faiDomanda?strumentoCod=RLO12026055023",
                            "x", None) == "RLO12026055023"
    assert codice_ufficiale("https://dati.lombardia.it/x.json#abc", "x", {"codice_bando": "RLAI2026053804"}) == "RLAI2026053804"
    assert codice_ufficiale("https://esempio.it/bando", "Bando 2026", {}) is None


def test_url_chiave_toglie_solo_il_superfluo():
    assert url_chiave("https://www.Esempio.it/bandi/x/?utm_source=a#top") == "esempio.it/bandi/x"
    assert url_chiave("http://esempio.it/bandi/x/index.html") == "esempio.it/bandi/x"
    # i parametri che identificano la pagina restano
    assert url_chiave("https://www.regione.marche.it/Bandi/p/1?idb=28598") == "regione.marche.it/Bandi/p/1?idb=28598"
    assert url_chiave(None) is None and url_chiave("mailto:x@y.it") is None


def test_ente_normalizzato():
    assert ente_normalizzato("Camera di Commercio, Industria, Artigianato e Agricoltura di Modena") == "camera modena"
    assert ente_normalizzato("CCIAA Modena") == "camera modena"


def test_territorio_dal_catalogo_nazionale():
    assert territorio_annuncio("ITA", {"regioni": ["Emilia-Romagna"]}) == "EMR"
    assert territorio_annuncio("ITA", {"regioni": ["Lombardia", "Veneto"]}) == "ITA"
    assert territorio_annuncio("LOM", None) == "LOM"
    assert territorio_annuncio("ITA", {"regioni": ["Lombardia", "Veneto"], "gestore": "Regione Lombardia"}) == "LOM"


def test_ruolo_dal_titolo():
    assert ruolo_da_titolo("Bando Qualità Artigiana: approvazione terza graduatoria") == "graduatoria"
    assert ruolo_da_titolo("Proroga del bando PID NEXT") == "proroga"
    assert ruolo_da_titolo("Rettifica avviso Made in Sicily") == "rettifica"
    assert ruolo_da_titolo("Bando Voucher Digitali 2026 - FAQ") == "faq"
    assert ruolo_da_titolo("Bando Voucher Digitali 2026") is None


def test_edizioni_e_parti_diverse_non_sono_lo_stesso_titolo():
    a = analizza_titolo("Bando Fiere - secondo sportello 2026")
    b = analizza_titolo("Bando Fiere - primo sportello 2026")
    assert a.edizione != b.edizione and a.parole == b.parole
    assert analizza_titolo("Poli di innovazione Linea A").edizione == {"lineaa"}
    assert analizza_titolo("Bando voucher I semestre 2026").edizione != analizza_titolo("Bando voucher II semestre 2026").edizione


def test_somiglianza_ignora_il_nome_dell_ente():
    ente = ente_normalizzato("CCIAA Modena")
    a = analizza_titolo("CCIAA Modena - Bando occupazione giovanile - anno 2026", ente)
    b = analizza_titolo("Bando occupazione giovanile 2026", ente)
    assert somiglianza(a, b) == 1.0


def test_stesso_codice_da_due_fonti_un_solo_bando():
    annunci = [
        ann(1, "PR FESR AZIONE 1.3.1 CONTRIBUTI FIERE...", fonte="lombardia_api", ente="Regione Lombardia", territorio="LOM",
            dati={"codice_bando": "RLO12026055023"}),
        ann(2, "Contributi per le fiere internazionali in Lombardia", fonte="lombardia_online", ente="Regione Lombardia",
            territorio="LOM", url="https://www.bandi.regione.lombardia.it/faiDomanda?strumentoCod=RLO12026055023"),
    ]
    piano = pianifica(annunci, anno_corrente=2026)
    assert [e.azione for _, e in piano] == ["nuovo", "collega"]
    assert piano[1][1].bando == piano[0][1].bando and "codice" in piano[1][1].motivo


def test_link_ente_del_catalogo_trova_il_bando_della_camera():
    annunci = [
        ann(1, "Bando internazionalizzazione anno 2026", url="https://www.marche.camcom.it/bandi/internaz-2026",
            fonte="cciaa_marche", ente="Camera di Commercio delle Marche", territorio="MAR"),
        ann(2, "CCIAA Marche - Bando Internazionalizzazione Anno 2026", fonte="incentivi", ente="CCIAA Marche",
            territorio="MAR", dati={"link_ente": "https://marche.camcom.it/bandi/internaz-2026/"}),
    ]
    piano = pianifica(annunci, anno_corrente=2026)
    assert piano[1][1].azione == "collega" and "indirizzo" in piano[1][1].motivo


def test_indirizzo_ripetuto_nella_stessa_fonte_non_identifica():
    # Due voci del catalogo con lo stesso link generico all'ente: non sono lo stesso bando.
    dati = {"link_ente": "https://www.regione.umbria.it/la-regione/bandi"}
    annunci = [
        ann(1, "Contributi per l'efficienza energetica 2026", fonte="incentivi", ente="Regione Umbria", territorio="UMB", dati=dati),
        ann(2, "Voucher per la digitalizzazione del commercio 2026", fonte="incentivi", ente="Regione Umbria", territorio="UMB", dati=dati),
    ]
    assert [e.azione for _, e in pianifica(annunci, anno_corrente=2026)] == ["nuovo", "nuovo"]


def test_stesso_titolo_stesso_ente_stessa_edizione():
    annunci = [
        ann(1, "Bando Fiere internazionali all'estero 2026", fonte="cciaa_como"),
        ann(2, "CCIAA Modena - Bando Fiere internazionali all'estero - anno 2026", fonte="incentivi"),
    ]
    assert pianifica(annunci, anno_corrente=2026)[1][1].azione == "collega"


def test_edizioni_diverse_sono_bandi_diversi():
    annunci = [ann(1, "Bando Voucher Turismo 2025"), ann(2, "Bando Voucher Turismo 2026")]
    assert [e.azione for _, e in pianifica(annunci, anno_corrente=2026)] == ["nuovo", "nuovo"]


def test_camere_diverse_con_lo_stesso_tipo_di_bando():
    annunci = [
        ann(1, "Bando Internazionalizzazione - Anno 2026", ente="CCIAA Foggia", territorio="PUG", fonte="fg"),
        ann(2, "Bando Voucher Internazionalizzazione - Anno 2026", ente="CCIAA Bari", territorio="PUG", fonte="ba"),
    ]
    assert [e.azione for _, e in pianifica(annunci, anno_corrente=2026)] == ["nuovo", "nuovo"]


def test_luoghi_diversi_nel_titolo():
    ente = "Camera di Commercio di Arezzo Siena"
    annunci = [ann(1, "Bando voucher doppia transizione 2026 Siena", ente=ente),
               ann(2, "Bando voucher doppia transizione 2026 Arezzo", ente=ente)]
    assert [e.azione for _, e in pianifica(annunci, anno_corrente=2026)] == ["nuovo", "nuovo"]


def test_titolo_simile_ma_non_uguale_e_un_dubbio():
    annunci = [
        ann(1, "Bando voucher digitali I4.0 2026", fonte="a"),
        ann(2, "Voucher digitali I4.0 2026 per le PMI", fonte="b", ente="Unioncamere Emilia-Romagna"),
    ]
    piano = pianifica(annunci, anno_corrente=2026)
    assert piano[1][1].azione == "dubbio" and piano[1][1].bando == piano[0][1].bando


def test_graduatoria_si_aggancia_al_bando():
    annunci = [
        ann(1, "Bando contributi doppia transizione digitale ed ecologica 2026"),
        ann(2, "Bando contributi doppia transizione digitale ed ecologica 2026: pubblicata la graduatoria"),
    ]
    piano = pianifica(annunci, anno_corrente=2026)
    assert piano[1][1].azione == "collega" and piano[1][1].ruolo == "graduatoria"


def test_aggiornamento_senza_bando():
    piano = pianifica([ann(1, "Proroga del bando PID NEXT"), ann(2, "PID - graduatoria bando Voucher Digitali anno 2020")],
                      anno_corrente=2026)
    assert piano[0][1].azione == "dubbio" and piano[0][1].bando is None
    assert piano[1][1].azione == "ignora"   # bando vecchio: non si chiede a Matteo


def test_annunci_gia_collegati_o_in_dubbio_non_si_toccano():
    annunci = [ann(1, "Voucher export 2026", bando=10), ann(2, "Voucher export 2026"), ann(3, "Voucher fiere 2026")]
    piano = pianifica(annunci, {10: [annunci[0]]}, in_dubbio={3}, anno_corrente=2026)
    assert [(a.id, e.azione, e.bando) for a, e in piano] == [(2, "collega", 10)]
