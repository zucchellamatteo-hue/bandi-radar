"""Calcolatore completo del Conto Termico 3.0 (09/10/2026): formule dell'Allegato 2 e tetti per le imprese, sugli
esempi della scheda della misura (app/misure/misure.yaml) e su casi limite."""

from app import articoli
from app.pubblico.calcolatore_ct import calcola

PDC = {"tipo": "aria_acqua", "scop": 4, "eta": 150, "eta_min": 110}


def _per(r, codice):
    return next(x for x in r["interventi"] if x["codice"] == codice)


def test_hotel_pompa_di_calore_e_solare():
    r = calcola({"dimensione": "piccola", "zona_climatica": "E", "pdc": dict(PDC, kw=120, spesa=130_000),
                 "solare": {"tipo": "acs", "m2": 40, "qu": 450, "spesa": 50_000}})
    assert round(_per(r, "III.A")["incentivo"]) == 62_591                  # 120 x 1700 x 0,75 x 150/110 x 0,06 x 5 anni
    assert round(_per(r, "III.D")["incentivo"]) == 11_520                  # 0,32 x 450 x 40 x 2 anni
    assert r["anni"] == 5 and round(r["totale"]) == 74_111                  # sotto il tetto del 65%: vale la formula


def test_artigiano_tetto_e_intervento_singolo():
    r = calcola({"dimensione": "piccola", "zona_climatica": "E", "pdc": dict(PDC, kw=40, spesa=30_000),
                 "opache": [{"tipo": "cop_est", "m2": 400, "spesa": 40_000}]})
    assert _per(r, "III.A")["incentivo"] == 19_500                          # formula 20.864, tetto 65%
    a = _per(r, "II.A")
    assert round(a["algoritmo"]) == 22_000 and a["tetto"] == 45 and a["incentivo"] == 18_000   # 55% formula, 45% tetto
    assert r["totale"] == 37_500 and r["anni"] == 5 and r["risparmio_minimo"] == 10 and not r["multi"]


def test_negozio_led_oltre_il_costo_massimo():
    r = calcola({"dimensione": "piccola", "zona_climatica": "E", "pdc": dict(PDC, kw=12, spesa=12_000),
                 "illuminazione": {"tipo": "led", "m2": 150, "spesa": 6_000}})
    assert round(_per(r, "II.E")["incentivo"]) == 2_100                    # 40% x 35 euro/m2 x 150 m2
    assert r["anni"] == 1 and round(r["totale"]) == 8_359                   # sotto 15.000: rata unica


def test_multi_intervento_maggiorazioni_e_tetti():
    base = {"zona_climatica": "C", "opache": [{"tipo": "par_est", "m2": 1000, "spesa": 150_000}],
            "illuminazione": {"tipo": "led", "m2": 2000, "spesa": 60_000}}
    r = calcola(dict(base, dimensione="media"))
    assert r["multi"] and _per(r, "II.A")["tetto"] == 40 and r["risparmio_minimo"] == 20   # 30 + 10 media
    assert round(_per(r, "II.A")["incentivo"]) == 60_000                     # formula 40% (zona C) = tetto 40%
    r = calcola(dict(base, dimensione="piccola", zona_aiuti=15, risparmio_40=True))
    assert _per(r, "II.A")["tetto"] == 65                                    # 30 + 20 + 15 + 15 = 80 -> 65
    r = calcola(dict(base, dimensione="grande", zona_aiuti=15, risparmio_40=True))
    assert _per(r, "II.A")["tetto"] == 60                                    # grandi: massimo 60%
    r = calcola(dict(base, dimensione="piccola", ue=True))
    assert round(_per(r, "II.E")["algoritmo"]) == round(0.4 * 60_000 * 1.1)  # +10% componenti UE


def test_colonnine_e_fotovoltaico_solo_con_pompa_di_calore():
    senza = calcola({"dimensione": "piccola", "fotovoltaico": {"kwp": 10, "spesa": 15_000}, "colonnine": {"tipo": "mono", "n": 1, "spesa": 3_000}})
    assert senza["interventi"] == []
    r = calcola({"dimensione": "piccola", "zona_climatica": "E", "pdc": dict(PDC, kw=10, spesa=12_000),
                 "fotovoltaico": {"kwp": 10, "spesa": 18_000, "kwh": 10, "spesa_acc": 8_000},
                 "colonnine": {"tipo": "mono", "n": 1, "spesa": 3_000}})
    ipdc = _per(r, "III.A")["algoritmo"]
    fv = _per(r, "II.H")
    assert fv["tetto"] == 30 and round(fv["algoritmo"]) == round(min(0.2 * (15_000 + 8_000), ipdc))
    assert _per(r, "II.G")["incentivo"] == min(0.3 * 2_400, ipdc)


def test_biomassa_scaldacqua_teleriscaldamento():
    r = calcola({"dimensione": "piccola", "zona_climatica": "E", "biomassa": {"tipo": "caldaia", "kw": 200, "ce": 1.0, "spesa": 120_000}})
    assert round(_per(r, "III.C")["incentivo"]) == 42_500                   # 200 x 1700 x 0,025 x 5 anni
    r = calcola({"dimensione": "media", "scaldacqua": {"classe": "A+", "oltre_150": True, "spesa": 3_000}})
    assert _per(r, "III.E")["incentivo"] == 1_200                            # 40% di 3.000 sotto il massimo di 1.500
    r = calcola({"dimensione": "grande", "teleriscaldamento": {"kw": 100, "spesa": 20_000}})
    assert _per(r, "III.F")["incentivo"] == 7_200                            # formula 65% x 16.000 = 10.400; tetto 45% x 16.000


def test_il_calcolatore_si_inserisce_nell_articolo():
    h = articoli.in_html("[[calcolatore:conto_termico]]")
    assert 'id="calcolatore-ct"' in h and "ct-pdc-kw" in h and "ct-tlr-spesa" in h and "<script>" in h
