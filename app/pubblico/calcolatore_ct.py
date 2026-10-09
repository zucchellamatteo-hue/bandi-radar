"""Calcolatore completo del Conto Termico 3.0 per le imprese (09/10/2026, richiesta di Matteo: "rendi il calcolatore
completo").

Regole: DM MASE 7/8/2025 (Allegato 2) e Regole Applicative GSE del 19/12/2025, cap. 4.2.1 (intensita' per le
imprese), 4.3 (rate), 4.7 (trattenuta) e cap. 9 (algoritmo di ogni intervento, tabelle 15-39). Per un'impresa:
  1. ogni intervento ha il suo incentivo calcolato con l'algoritmo dell'Allegato 2 (costi massimi unitari, energia
     prodotta, coefficienti per zona climatica, massimali), con +10% per i componenti prodotti nell'UE (II.A-F);
  2. poi vale il tetto del Titolo V (art. 27): l'intensita' massima e' una percentuale dei costi ammissibili
     (par. 4.2.1: "importo dell'incentivo espresso in percentuale rispetto ai costi"), quindi l'incentivo e' il minore
     tra algoritmo e tetto. Titolo II: 25% (30% se due o piu' interventi del Titolo II sullo stesso edificio) + 20
     piccole / 10 medie + 15 zona 107.3.a o 5 zona 107.3.c + 15 con energia primaria -40%; massimo 65% PMI, 60%
     grandi; 30% per II.D, II.G, II.H. Titolo III: 45% + 20 piccole / 10 medie;
  3. fino a 15.000 euro in tutto rata unica, altrimenti le rate dell'intervento piu' lungo; trattenuta GSE 1% (max
     250 euro + IVA).
Le stesse formule sono scritte due volte: in JavaScript per la pagina e in Python (calcola) per i test.
"""

from __future__ import annotations

import math

# --- dati delle tabelle del GSE (uguali nel JavaScript sotto) ---
QUF = {"A": 600, "B": 850, "C": 1100, "D": 1400, "E": 1700, "F": 1800}          # tab. 26 e 31 (Quf = hr)
CMAX_OPACHE = {"cop_est": 300, "cop_int": 150, "cop_vent": 350, "pav_est": 170, "pav_int": 150,
               "par_est": 200, "par_int": 100, "par_vent": 250}                    # tab. 15, euro/m2
# Pompe di calore: Ci fino a 35 kW e oltre (tab. 27). Split e double duct solo fino a 12 kW / senza soglia.
CI_PDC = {"aria_acqua": (0.15, 0.06), "vrf": (0.15, 0.055), "rooftop": (0.15, 0.055), "acqua": (0.16, 0.06),
          "geotermica": (0.16, 0.06), "split": (0.07, 0.07), "double_duct": (0.20, 0.20)}
K_IBRIDO = {"no": (1, 1), "factory": (1.25, 1.25), "bivalente": (1, 1.1)}         # tab. 29 (caldaia <=35 / >35 kW)
CI_BIOMASSA = {"caldaia": (0.060, 0.025, 0.020), "stufa_legna": (0.045, None, None), "stufa_pellet": (0.055, None, None)}
CI_SOLARE = {"acs": (0.35, 0.32, 0.13, 0.12, 0.11), "acs_risc": (0.36, 0.33, 0.13, 0.12, 0.11),
             "concentrazione": (0.38, 0.35, 0.13, 0.12, 0.11), "cooling": (0.43, 0.40, 0.17, 0.15, 0.14)}
SCALDACQUA = {("A", False): 500, ("A", True): 1100, ("A+", False): 700, ("A+", True): 1500}   # tab. 38


def _min_pos(*valori):
    return min(v for v in valori if v is not None)


def _ci_solare(tipo: str, superficie: float) -> float:
    c = CI_SOLARE[tipo]
    return c[0] if superficie < 12 else c[1] if superficie <= 50 else c[2] if superficie <= 200 else c[3] if superficie <= 500 else c[4]


def algoritmo_pdc(p: dict, zona: str) -> tuple[float, int]:
    """(incentivo totale, anni) di una pompa di calore elettrica o di un sistema ibrido (tab. 26-29)."""
    kw, scop = p.get("kw", 0), p.get("scop", 0)
    if kw <= 0 or scop <= 1:
        return 0, 0
    ci = CI_PDC[p.get("tipo", "aria_acqua")][0 if kw <= 35 else 1]
    kp = max(1.0, p.get("eta", 0) / p.get("eta_min", 110)) if p.get("eta") else 1.0
    k = K_IBRIDO[p.get("ibrido", "no")][0 if p.get("kw_caldaia", 0) <= 35 else 1]
    anni = 2 if kw <= 35 else 5
    return k * kw * QUF[zona] * (1 - 1 / scop) * kp * ci * anni, anni


def calcola(d: dict) -> dict:
    """Stessa logica del calcolatore della pagina. `d`: dimensione ("piccola"|"media"|"grande"), zona_climatica
    (A-F), zona_aiuti (0|5|15), risparmio_40, ue (componenti UE), e un dizionario per intervento (vedi test)."""
    dim = {"piccola": 20, "media": 10, "grande": 0}[d.get("dimensione", "piccola")]
    zona = d.get("zona_climatica", "E")
    righe = []                                                       # (codice, titolo, algoritmo, base del tetto, anni)

    def spesa_amm(spesa, cmax_totale):
        return min(spesa, cmax_totale) if cmax_totale is not None else spesa

    pdc = d.get("pdc") or {}
    i_pdc, anni_pdc = algoritmo_pdc(pdc, zona)
    titolo3_pdc = i_pdc > 0
    biom = d.get("biomassa") or {}
    sol = d.get("solare") or {}
    sca = d.get("scaldacqua") or {}
    con_titolo3 = titolo3_pdc or biom.get("kw", 0) > 0 or sca.get("spesa", 0) > 0
    opache = [o for o in d.get("opache") or [] if o.get("spesa", 0) > 0 and o.get("m2", 0) > 0]
    ue = 1.1 if d.get("ue") else 1.0
    # II.A cappotto: 40% (50% zone E-F; 55% con un intervento III.A, III.B, III.C o III.E), Imax 1.000.000 in tutto
    perc_a = 0.55 if con_titolo3 else 0.50 if zona in ("E", "F") else 0.40
    if opache:
        alg = sum(perc_a * min(o["spesa"], CMAX_OPACHE[o["tipo"]] * o["m2"]) for o in opache)
        base = sum(min(o["spesa"], CMAX_OPACHE[o["tipo"]] * o["m2"]) for o in opache)
        righe.append(("II.A", 2, min(alg, 1_000_000) * ue, base, 5))
    inf = d.get("infissi") or {}
    if inf.get("spesa", 0) > 0 and inf.get("m2", 0) > 0:
        cmax = (700 if zona in ("A", "B", "C") else 800) * inf["m2"]
        perc = 0.55 if (opache and con_titolo3) else 0.40
        righe.append(("II.B", 2, min(perc * min(inf["spesa"], cmax), 500_000) * ue, min(inf["spesa"], cmax), 5))
    sch = d.get("schermature") or {}
    voci_c = [(sch.get("spesa", 0), 250 * sch.get("m2", 0), 90_000), (sch.get("spesa_auto", 0), 50 * sch.get("m2_auto", 0), 10_000),
              (sch.get("spesa_pell", 0), (130 if sch.get("pellicole") == "non_riflettenti" else 80) * sch.get("m2_pell", 0), 30_000)]
    voci_c = [v for v in voci_c if v[0] > 0 and v[1] > 0]
    if voci_c:
        righe.append(("II.C", 2, sum(min(0.4 * min(s, c), m) for s, c, m in voci_c) * ue, sum(min(s, c) for s, c, _ in voci_c), 5))
    nz = d.get("nzeb") or {}
    if nz.get("spesa", 0) > 0 and nz.get("m2", 0) > 0:
        cmax = (1000 if zona in ("A", "B", "C") else 1300) * nz["m2"]
        imax = 2_500_000 if zona in ("A", "B", "C") else 3_000_000
        righe.append(("II.D", 2, min(0.65 * min(nz["spesa"], cmax), imax) * ue, min(nz["spesa"], cmax), 5))
    il = d.get("illuminazione") or {}
    if il.get("spesa", 0) > 0 and il.get("m2", 0) > 0:
        led = il.get("tipo", "led") == "led"
        cmax = (35 if led else 15) * il["m2"]
        righe.append(("II.E", 2, min(0.4 * min(il["spesa"], cmax), 140_000 if led else 50_000) * ue, min(il["spesa"], cmax), 5))
    ba = d.get("bacs") or {}
    if ba.get("spesa", 0) > 0 and ba.get("m2", 0) > 0:
        cmax = 60 * ba["m2"]
        righe.append(("II.F", 2, min(0.4 * min(ba["spesa"], cmax), 100_000) * ue, min(ba["spesa"], cmax), 5))
    col = d.get("colonnine") or {}
    if col.get("spesa", 0) > 0 and titolo3_pdc:                    # solo insieme a una pompa di calore elettrica
        tipo, n = col.get("tipo", "mono"), max(1, col.get("n", 1))
        cmax = {"mono": 2400 * n, "tri": 8400 * n, "22_50": 1200 * col.get("kw", 0), "50_100": 60_000, "oltre_100": 110_000}[tipo]
        righe.append(("II.G", 2, min(0.30 * min(col["spesa"], cmax), i_pdc), min(col["spesa"], cmax), anni_pdc))
    fv = d.get("fotovoltaico") or {}
    if (fv.get("spesa", 0) > 0 or fv.get("spesa_acc", 0) > 0) and titolo3_pdc:
        kwp = fv.get("kwp", 0)
        c_fv = 1500 if kwp <= 20 else 1200 if kwp <= 200 else 1100 if kwp <= 600 else 1050
        perc = 0.20 + fv.get("registro", 0) / 100
        amm = min(fv.get("spesa", 0), c_fv * kwp) + min(fv.get("spesa_acc", 0), 1000 * fv.get("kwh", 0))
        righe.append(("II.H", 2, min(perc * amm, i_pdc), amm, anni_pdc))
    if titolo3_pdc:
        righe.append(("III.A", 3, i_pdc, pdc.get("spesa", 0), anni_pdc))
    if biom.get("kw", 0) > 0 and biom.get("spesa", 0) > 0:
        kw, tipo = biom["kw"], biom.get("tipo", "caldaia")
        ci = CI_BIOMASSA[tipo][0 if kw <= 35 else 1 if kw <= 500 else 2] or CI_BIOMASSA[tipo][0]
        ce = biom.get("ce", 1.0)
        annuo = (kw if tipo == "caldaia" else 3.35 * math.log(kw)) * QUF[zona] * ci * ce
        anni = 2 if kw <= 35 else 5
        righe.append(("III.C", 3, annuo * anni, biom["spesa"], anni))
    if sol.get("m2", 0) > 0 and sol.get("spesa", 0) > 0:
        anni = 2 if sol["m2"] <= 50 else 5
        righe.append(("III.D", 3, _ci_solare(sol.get("tipo", "acs"), sol["m2"]) * sol.get("qu", 0) * sol["m2"] * anni, sol["spesa"], anni))
    if sca.get("spesa", 0) > 0:
        righe.append(("III.E", 3, min(0.4 * sca["spesa"], SCALDACQUA[(sca.get("classe", "A"), bool(sca.get("oltre_150")))]), sca["spesa"], 2))
    tlr = d.get("teleriscaldamento") or {}
    if tlr.get("spesa", 0) > 0 and tlr.get("kw", 0) > 0:
        kw = tlr["kw"]
        cmax, imax = (200, 6_500) if kw <= 50 else (160, 15_000) if kw <= 150 else (130, 30_000)
        righe.append(("III.F", 3, min(0.65 * min(tlr["spesa"], cmax * kw), imax), min(tlr["spesa"], cmax * kw), 5))

    lettere_ii = {r[0] for r in righe if r[1] == 2 and r[0] in ("II.A", "II.B", "II.C", "II.E", "II.F")}
    multi = len(lettere_ii) >= 2 or any(r[0] in ("II.D", "II.G", "II.H") for r in righe)
    tetto_ii = min((30 if len(lettere_ii) >= 2 else 25) + dim + d.get("zona_aiuti", 0) + (15 if d.get("risparmio_40") else 0),
                   65 if dim else 60)
    tetto_iii = 45 + dim
    risultato = []
    for codice, titolo, alg, base, anni in righe:
        tetto = (min(tetto_ii, 30) if codice in ("II.D", "II.G", "II.H") else tetto_ii) if titolo == 2 else tetto_iii
        incentivo = min(alg, tetto / 100 * base)
        risultato.append({"codice": codice, "algoritmo": alg, "tetto": tetto, "base": base, "incentivo": incentivo,
                          "anni": anni})
    totale = sum(r["incentivo"] for r in risultato)
    anni = 1 if totale <= 15_000 else max([r["anni"] for r in risultato] or [1])
    return {"interventi": risultato, "totale": totale, "anni": anni, "multi": multi,
            "trattenuta": min(0.01 * totale, 250), "risparmio_minimo": 20 if multi else 10}


# --- la pagina: modulo e JavaScript (stessa logica di calcola) ---

def _num(id_: str, etichetta: str, valore: str = "", passo: str = "1") -> str:
    return (f'<label for="{id_}">{etichetta}</label><input id="{id_}" type="number" inputmode="decimal" min="0" '
            f'step="{passo}" value="{valore}">')


def _sel(id_: str, etichetta: str, opzioni: list[tuple[str, str]]) -> str:
    voci = "".join(f'<option value="{v}">{t}</option>' for v, t in opzioni)
    return f'<label for="{id_}">{etichetta}</label><select id="{id_}">{voci}</select>'


def _spunta(id_: str, etichetta: str, acceso: bool = False) -> str:
    return f'<label class="spunta"><input id="{id_}" type="checkbox"{" checked" if acceso else ""}> {etichetta}</label>'


def _blocco(titolo: str, corpo: str, aperto: bool = False) -> str:
    return f'<details class="ct-blocco"{" open" if aperto else ""}><summary>{titolo}</summary>{corpo}</details>'


_OPACHE = [("cop_est", "Copertura, isolamento esterno (max 300 €/m²)"), ("cop_int", "Copertura, interno (150 €/m²)"),
           ("cop_vent", "Copertura ventilata (350 €/m²)"), ("pav_est", "Pavimento, esterno (170 €/m²)"),
           ("pav_int", "Pavimento, interno o sottotetto (150 €/m²)"), ("par_est", "Pareti, cappotto esterno (200 €/m²)"),
           ("par_int", "Pareti, interno (100 €/m²)"), ("par_vent", "Parete ventilata (250 €/m²)")]

_MODULO = "".join([
    '<div class="calcolatore" id="calcolatore-ct"><h3>Calcola il Conto Termico 3.0 della tua impresa</h3>',
    '<p class="piccolo">Apri gli interventi che ti interessano e scrivi spesa (IVA esclusa) e misure. Il calcolo segue '
    'le formule del GSE per ogni intervento e poi il tetto per le imprese.</p>',
    _sel("ct-dim", "Dimensione dell'impresa", [("piccola", "Micro o piccola"), ("media", "Media"), ("grande", "Grande")]),
    _sel("ct-zc", "Zona climatica del comune (A più calda, F più fredda; la trovi nell'APE)",
         [("E", "E (gran parte del Nord e dell'Appennino)"), ("D", "D"), ("C", "C"), ("B", "B"), ("A", "A"), ("F", "F (montagna)")]),
    _sel("ct-za", "Zona per gli aiuti a finalità regionale (solo per l'efficienza, Titolo II)",
         [("0", "Fuori dalle zone assistite"), ("5", "Zona assistita art. 107.3.c"), ("15", "Zona assistita art. 107.3.a (Mezzogiorno)")]),
    _spunta("ct-40", "Con i lavori il fabbisogno di energia primaria scende di almeno il 40% (APE prima e dopo)"),
    _spunta("ct-ue", "Componenti principali prodotti nell'Unione europea (+10% sugli interventi II.A-II.F)"),
    _blocco("Pompa di calore elettrica o sistema ibrido (III.A, III.B)", "".join([
        _sel("ct-pdc-tipo", "Tipo", [("aria_acqua", "Aria/acqua"), ("vrf", "Aria/aria VRF/VRV"), ("rooftop", "Aria/aria rooftop"),
                                     ("split", "Aria/aria split o multisplit fino a 12 kW"), ("acqua", "Acqua di falda"),
                                     ("geotermica", "Geotermica"), ("double_duct", "Fixed double duct")]),
        _num("ct-pdc-kw", "Potenza nominale (Prated, kW, dalla scheda prodotto)", "30", "0.1"),
        _num("ct-pdc-scop", "SCOP (o COP per i double duct), clima medio", "4", "0.01"),
        _num("ct-pdc-eta", "Efficienza stagionale ηs in % (dalla scheda prodotto; vuoto = premialità 1)", "150"),
        _num("ct-pdc-etamin", "ηs minima Ecodesign in % (di solito 110 a media temperatura, 125 a bassa)", "110"),
        _sel("ct-pdc-ibr", "Configurazione", [("no", "Solo pompa di calore"), ("factory", "Sistema ibrido factory made (k 1,25)"),
                                             ("bivalente", "Sistema bivalente o pompa di calore add-on")]),
        _num("ct-pdc-kwc", "Potenza della caldaia del sistema ibrido (kW)", "0", "0.1"),
        _num("ct-pdc-spesa", "Spesa (euro)", "30000", "100")]), aperto=True),
    _blocco("Isolamento di coperture, pavimenti e pareti (II.A)", "".join(
        _sel(f"ct-op{i}-tipo", f"Superficie {i}", _OPACHE) + _num(f"ct-op{i}-m2", "m² isolati") + _num(f"ct-op{i}-spesa", "Spesa (euro)", "", "100")
        for i in (1, 2))),
    _blocco("Infissi (II.B)", _num("ct-inf-m2", "m² di infissi sostituiti") + _num("ct-inf-spesa", "Spesa (euro)", "", "100")),
    _blocco("Schermature solari (II.C)", "".join([
        _num("ct-sch-m2", "Schermature: m²"), _num("ct-sch-spesa", "Schermature: spesa (euro)", "", "100"),
        _num("ct-aut-m2", "Automazione delle schermature: m²"), _num("ct-aut-spesa", "Automazione: spesa (euro)", "", "100"),
        _sel("ct-pel-tipo", "Pellicole a filtrazione solare", [("non_riflettenti", "Selettive non riflettenti (130 €/m²)"), ("riflettenti", "Selettive riflettenti (80 €/m²)")]),
        _num("ct-pel-m2", "Pellicole: m²"), _num("ct-pel-spesa", "Pellicole: spesa (euro)", "", "100")])),
    _blocco("Trasformazione in edificio a energia quasi zero, nZEB (II.D)",
            _num("ct-nz-m2", "Superficie utile dell'edificio (m²)") + _num("ct-nz-spesa", "Spesa (euro)", "", "100")),
    _blocco("Illuminazione (II.E)", _sel("ct-il-tipo", "Tipo", [("led", "LED (35 €/m²)"), ("altre", "Altre lampade efficienti (15 €/m²)")])
            + _num("ct-il-m2", "Superficie illuminata (m² calpestabili)") + _num("ct-il-spesa", "Spesa (euro)", "", "100")),
    _blocco("Building automation (II.F)", _num("ct-ba-m2", "Superficie controllata (m²)") + _num("ct-ba-spesa", "Spesa (euro)", "", "100")),
    _blocco("Colonnine di ricarica, solo con la pompa di calore (II.G)", "".join([
        _sel("ct-col-tipo", "Tipo", [("mono", "Fino a 22 kW, monofase (2.400 € a punto)"), ("tri", "Fino a 22 kW, trifase (8.400 € a punto)"),
                                    ("22_50", "Da 22 a 50 kW (1.200 €/kW)"), ("50_100", "Da 50 a 100 kW (60.000 €)"), ("oltre_100", "Oltre 100 kW (110.000 €)")]),
        _num("ct-col-n", "Punti di ricarica", "1"), _num("ct-col-kw", "Potenza (kW, per 22-50 kW)", "", "0.1"),
        _num("ct-col-spesa", "Spesa (euro)", "", "100")])),
    _blocco("Fotovoltaico e accumulo, solo con la pompa di calore (II.H)", "".join([
        _num("ct-fv-kwp", "Potenza di picco (kWp)", "", "0.1"), _num("ct-fv-spesa", "Spesa per l'impianto (euro)", "", "100"),
        _num("ct-fv-kwh", "Accumulo (kWh)", "", "0.1"), _num("ct-fv-spacc", "Spesa per l'accumulo (euro)", "", "100"),
        _sel("ct-fv-reg", "Moduli nel registro delle tecnologie del fotovoltaico", [("0", "No"), ("5", "Sezione a (+5 punti)"), ("10", "Sezione b (+10 punti)"), ("15", "Sezione c (+15 punti)")])])),
    _blocco("Generatore a biomassa (III.C)", "".join([
        _sel("ct-bio-tipo", "Tipo", [("caldaia", "Caldaia"), ("stufa_pellet", "Stufa o termocamino a pellet"), ("stufa_legna", "Stufa o termocamino a legna")]),
        _num("ct-bio-kw", "Potenza nominale (kW)", "", "0.1"),
        _sel("ct-bio-ce", "Polveri rispetto alla classe 5 stelle", [("1", "Fino al 20% in meno"), ("1.2", "Dal 20% al 50% in meno"), ("1.5", "Oltre il 50% in meno")]),
        _num("ct-bio-spesa", "Spesa (euro)", "", "100")])),
    _blocco("Solare termico (III.D)", "".join([
        _sel("ct-sol-tipo", "Uso", [("acs", "Acqua calda sanitaria"), ("acs_risc", "Acqua calda e riscaldamento o calore di processo"),
                                    ("concentrazione", "Collettori a concentrazione"), ("cooling", "Solar cooling")]),
        _num("ct-sol-m2", "Superficie lorda dei collettori (m²)", "", "0.1"),
        _num("ct-sol-qu", "Energia per m² dal certificato Solar Keymark (kWh/m² l'anno; spesso 400-600)", "450"),
        _num("ct-sol-spesa", "Spesa (euro)", "", "100")])),
    _blocco("Scaldacqua a pompa di calore (III.E)", "".join([
        _sel("ct-sca-cl", "Classe energetica", [("A", "A"), ("A+", "A+ o superiore")]),
        _spunta("ct-sca-150", "Accumulo oltre 150 litri"), _num("ct-sca-spesa", "Spesa (euro)", "", "100")])),
    _blocco("Allaccio al teleriscaldamento efficiente (III.F)",
            _num("ct-tlr-kw", "Potenza della sottostazione (kW)", "", "0.1") + _num("ct-tlr-spesa", "Spesa (euro)", "", "100")),
    '<table class="ct-risultati"><thead><tr><th>Intervento</th><th>Formula GSE</th><th>Tetto imprese</th><th>Incentivo</th></tr></thead>'
    '<tbody id="ct-righe"></tbody><tfoot><tr><td colspan="3"><b>Contributo stimato</b></td><td class="cr" id="ct-tot">-</td></tr>'
    '<tr><td colspan="3">Come arriva</td><td class="cr" id="ct-rate">-</td></tr></tfoot></table>',
    '<p class="cs-nota" aria-live="polite"></p>',
    '<p class="piccolo">Stima con le formule dell\'Allegato 2 del DM 7/8/2025 e delle Regole Applicative GSE: per ogni '
    'intervento il minore tra la formula e il tetto percentuale per le imprese sui costi ammissibili (IVA esclusa, entro i '
    'costi massimi). Dalla prima rata il GSE trattiene l\'1% (al massimo 250 euro più IVA). La cifra vera la decide il GSE '
    'dopo l\'istruttoria. Per le imprese la richiesta preliminare va inviata prima del primo ordine.</p></div>',
])

_SCRIPT = """<script>
(function () {
  var box = document.getElementById("calcolatore-ct"); if (!box) return;
  function n(id) { var e = box.querySelector("#" + id); var x = e ? Number(e.value) : 0; return isFinite(x) && x > 0 ? x : 0; }
  function s(id) { return box.querySelector("#" + id).value; }
  function c(id) { return box.querySelector("#" + id).checked; }
  var QUF = {A: 600, B: 850, C: 1100, D: 1400, E: 1700, F: 1800};
  var CMAX_OP = {cop_est: 300, cop_int: 150, cop_vent: 350, pav_est: 170, pav_int: 150, par_est: 200, par_int: 100, par_vent: 250};
  var CI_PDC = {aria_acqua: [0.15, 0.06], vrf: [0.15, 0.055], rooftop: [0.15, 0.055], acqua: [0.16, 0.06], geotermica: [0.16, 0.06],
                split: [0.07, 0.07], double_duct: [0.20, 0.20]};
  var K_IBR = {no: [1, 1], factory: [1.25, 1.25], bivalente: [1, 1.1]};
  var CI_BIO = {caldaia: [0.060, 0.025, 0.020], stufa_legna: [0.045, 0.045, 0.045], stufa_pellet: [0.055, 0.055, 0.055]};
  var CI_SOL = {acs: [0.35, 0.32, 0.13, 0.12, 0.11], acs_risc: [0.36, 0.33, 0.13, 0.12, 0.11],
                concentrazione: [0.38, 0.35, 0.13, 0.12, 0.11], cooling: [0.43, 0.40, 0.17, 0.15, 0.14]};
  var NOMI = {"II.A": "Isolamento (II.A)", "II.B": "Infissi (II.B)", "II.C": "Schermature (II.C)", "II.D": "nZEB (II.D)",
              "II.E": "Illuminazione (II.E)", "II.F": "Building automation (II.F)", "II.G": "Colonnine (II.G)",
              "II.H": "Fotovoltaico (II.H)", "III.A": "Pompa di calore (III.A/B)", "III.C": "Biomassa (III.C)",
              "III.D": "Solare termico (III.D)", "III.E": "Scaldacqua PdC (III.E)", "III.F": "Teleriscaldamento (III.F)"};
  function aggiorna() {
    var dim = {piccola: 20, media: 10, grande: 0}[s("ct-dim")], zona = s("ct-zc"), ue = c("ct-ue") ? 1.1 : 1, righe = [], note = [];
    // pompa di calore
    var kw = n("ct-pdc-kw"), scop = n("ct-pdc-scop"), ipdc = 0, anniPdc = 0;
    if (kw > 0 && scop > 1 && n("ct-pdc-spesa") > 0) {
      var tipo = s("ct-pdc-tipo"), ci = CI_PDC[tipo][kw <= 35 ? 0 : 1];
      var kp = n("ct-pdc-eta") ? Math.max(1, n("ct-pdc-eta") / (n("ct-pdc-etamin") || 110)) : 1;
      var k = K_IBR[s("ct-pdc-ibr")][n("ct-pdc-kwc") <= 35 ? 0 : 1];
      anniPdc = kw <= 35 ? 2 : 5;
      ipdc = k * kw * QUF[zona] * (1 - 1 / scop) * kp * ci * anniPdc;
      if (tipo === "split" && kw > 12) note.push("Gli split e multisplit sono ammessi fino a 12 kW.");
    }
    var bioKw = n("ct-bio-kw"), bioSp = n("ct-bio-spesa"), scaSp = n("ct-sca-spesa");
    var conT3 = ipdc > 0 || (bioKw > 0 && bioSp > 0) || scaSp > 0;
    // II.A
    var opAlg = 0, opBase = 0, percA = conT3 ? 0.55 : (zona === "E" || zona === "F" ? 0.50 : 0.40);
    [1, 2].forEach(function (i) {
      var m2 = n("ct-op" + i + "-m2"), sp = n("ct-op" + i + "-spesa");
      if (m2 > 0 && sp > 0) { var b = Math.min(sp, CMAX_OP[s("ct-op" + i + "-tipo")] * m2); opAlg += percA * b; opBase += b; }
    });
    if (opBase) righe.push(["II.A", 2, Math.min(opAlg, 1000000) * ue, opBase, 5]);
    var im2 = n("ct-inf-m2"), isp = n("ct-inf-spesa");
    if (im2 > 0 && isp > 0) {
      var ib = Math.min(isp, (/[ABC]/.test(zona) ? 700 : 800) * im2);
      righe.push(["II.B", 2, Math.min((opBase && conT3 ? 0.55 : 0.40) * ib, 500000) * ue, ib, 5]);
    }
    var cAlg = 0, cBase = 0;
    [[n("ct-sch-spesa"), 250 * n("ct-sch-m2"), 90000], [n("ct-aut-spesa"), 50 * n("ct-aut-m2"), 10000],
     [n("ct-pel-spesa"), (s("ct-pel-tipo") === "non_riflettenti" ? 130 : 80) * n("ct-pel-m2"), 30000]].forEach(function (v) {
      if (v[0] > 0 && v[1] > 0) { var b = Math.min(v[0], v[1]); cAlg += Math.min(0.4 * b, v[2]); cBase += b; }
    });
    if (cBase) righe.push(["II.C", 2, cAlg * ue, cBase, 5]);
    var nm2 = n("ct-nz-m2"), nsp = n("ct-nz-spesa");
    if (nm2 > 0 && nsp > 0) {
      var abc = /[ABC]/.test(zona), nb = Math.min(nsp, (abc ? 1000 : 1300) * nm2);
      righe.push(["II.D", 2, Math.min(0.65 * nb, abc ? 2500000 : 3000000) * ue, nb, 5]);
    }
    var lm2 = n("ct-il-m2"), lsp = n("ct-il-spesa"), led = s("ct-il-tipo") === "led";
    if (lm2 > 0 && lsp > 0) { var lb = Math.min(lsp, (led ? 35 : 15) * lm2); righe.push(["II.E", 2, Math.min(0.4 * lb, led ? 140000 : 50000) * ue, lb, 5]); }
    var bm2 = n("ct-ba-m2"), bsp = n("ct-ba-spesa");
    if (bm2 > 0 && bsp > 0) { var bb = Math.min(bsp, 60 * bm2); righe.push(["II.F", 2, Math.min(0.4 * bb, 100000) * ue, bb, 5]); }
    var csp = n("ct-col-spesa");
    if (csp > 0) {
      if (!ipdc) note.push("Colonnine e fotovoltaico sono ammessi solo insieme a una pompa di calore elettrica.");
      else {
        var np = Math.max(1, n("ct-col-n"));
        var cm = {mono: 2400 * np, tri: 8400 * np, "22_50": 1200 * n("ct-col-kw"), "50_100": 60000, oltre_100: 110000}[s("ct-col-tipo")];
        var cb = Math.min(csp, cm); righe.push(["II.G", 2, Math.min(0.30 * cb, ipdc), cb, anniPdc]);
      }
    }
    var kwp = n("ct-fv-kwp"), fsp = n("ct-fv-spesa"), asp = n("ct-fv-spacc");
    if (fsp > 0 || asp > 0) {
      if (!ipdc) { if (note.indexOf("Colonnine e fotovoltaico sono ammessi solo insieme a una pompa di calore elettrica.") < 0) note.push("Colonnine e fotovoltaico sono ammessi solo insieme a una pompa di calore elettrica."); }
      else {
        var cfv = kwp <= 20 ? 1500 : kwp <= 200 ? 1200 : kwp <= 600 ? 1100 : 1050;
        var fb = Math.min(fsp, cfv * kwp) + Math.min(asp, 1000 * n("ct-fv-kwh"));
        righe.push(["II.H", 2, Math.min((0.20 + Number(s("ct-fv-reg")) / 100) * fb, ipdc), fb, anniPdc]);
      }
    }
    if (ipdc) righe.push(["III.A", 3, ipdc, n("ct-pdc-spesa"), anniPdc]);
    if (bioKw > 0 && bioSp > 0) {
      var bt = s("ct-bio-tipo"), bci = CI_BIO[bt][bioKw <= 35 ? 0 : bioKw <= 500 ? 1 : 2], ba = bioKw <= 35 ? 2 : 5;
      if (bt !== "caldaia" && bioKw > 35) note.push("Stufe e termocamini: il coefficiente del GSE e' previsto fino a 35 kW.");
      var annuo = (bt === "caldaia" ? bioKw : 3.35 * Math.log(bioKw)) * QUF[zona] * bci * Number(s("ct-bio-ce"));
      righe.push(["III.C", 3, annuo * ba, bioSp, ba]);
    }
    var sm2 = n("ct-sol-m2"), ssp = n("ct-sol-spesa");
    if (sm2 > 0 && ssp > 0) {
      var cs = CI_SOL[s("ct-sol-tipo")], sci = sm2 < 12 ? cs[0] : sm2 <= 50 ? cs[1] : sm2 <= 200 ? cs[2] : sm2 <= 500 ? cs[3] : cs[4];
      var sa = sm2 <= 50 ? 2 : 5; righe.push(["III.D", 3, sci * n("ct-sol-qu") * sm2 * sa, ssp, sa]);
    }
    if (scaSp > 0) {
      var smax = {"A": [500, 1100], "A+": [700, 1500]}[s("ct-sca-cl")][c("ct-sca-150") ? 1 : 0];
      righe.push(["III.E", 3, Math.min(0.4 * scaSp, smax), scaSp, 2]);
    }
    var tkw = n("ct-tlr-kw"), tsp = n("ct-tlr-spesa");
    if (tkw > 0 && tsp > 0) {
      var tc = tkw <= 50 ? [200, 6500] : tkw <= 150 ? [160, 15000] : [130, 30000], tb = Math.min(tsp, tc[0] * tkw);
      righe.push(["III.F", 3, Math.min(0.65 * tb, tc[1]), tb, 5]);
    }
    var lettere = {}; righe.forEach(function (r) { if (["II.A", "II.B", "II.C", "II.E", "II.F"].indexOf(r[0]) >= 0) lettere[r[0]] = 1; });
    var nII = Object.keys(lettere).length;
    var multi = nII >= 2 || righe.some(function (r) { return ["II.D", "II.G", "II.H"].indexOf(r[0]) >= 0; });
    var tettoII = Math.min((nII >= 2 ? 30 : 25) + dim + Number(s("ct-za")) + (c("ct-40") ? 15 : 0), dim ? 65 : 60), tettoIII = 45 + dim;
    var tot = 0, anni = 1, html = "";
    righe.forEach(function (r) {
      var tetto = r[1] === 2 ? (["II.D", "II.G", "II.H"].indexOf(r[0]) >= 0 ? Math.min(tettoII, 30) : tettoII) : tettoIII;
      var inc = Math.min(r[2], tetto / 100 * r[3]); tot += inc; anni = Math.max(anni, r[4]);
      html += "<tr><td>" + NOMI[r[0]] + "</td><td class='cr'>" + bqEuro.format(r[2]) + "</td><td class='cr'>" + tetto + "% = "
            + bqEuro.format(tetto / 100 * r[3]) + "</td><td class='cr'><b>" + bqEuro.format(inc) + "</b></td></tr>";
    });
    if (tot <= 15000) anni = 1;
    box.querySelector("#ct-righe").innerHTML = html || "<tr><td colspan='4'>Scrivi spesa e misure di almeno un intervento.</td></tr>";
    box.querySelector("#ct-tot").textContent = tot ? bqEuro.format(tot) : "-";
    box.querySelector("#ct-rate").textContent = !tot ? "-" : anni === 1 ? "rata unica" : anni + " rate annuali da " + bqEuro.format(tot / anni);
    if (nII) note.unshift("Efficienza (Titolo II): serve un risparmio di energia primaria di almeno il " + (multi ? "20" : "10") + "%, dimostrato con l'APE prima e dopo.");
    if (tot) note.push("Trattenuta del GSE sulla prima rata: " + bqEuro.format(Math.min(0.01 * tot, 250)) + " più IVA.");
    box.querySelector(".cs-nota").textContent = note.join(" ");
  }
  box.querySelectorAll("input,select").forEach(function (e) { e.addEventListener("input", aggiorna); e.addEventListener("change", aggiorna); });
  aggiorna();
})();
</script>"""

HTML = _MODULO + _SCRIPT
