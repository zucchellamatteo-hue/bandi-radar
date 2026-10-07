"""Abbinamento a regole (nessuna IA) tra una scheda di bando e un profilo d'impresa anonimo.

Segue la tabella "campo della scheda <-> dato del profilo <-> regola di confronto" di docs/SCHEDA_BANDO.md:
per ogni vincolo si guarda prima lo stato (`vincoli`):
  - nessun_vincolo -> va bene;
  - non_noto       -> "da verificare" (mai "va bene");
  - vincolo        -> si applica la regola: rispettata -> va bene; non rispettata -> escluso, con il motivo;
                      campi vuoti o dato mancante nel profilo -> "da verificare".
Una scheda che non e' fatta sul bando ufficiale (completezza) non da' mai "compatibile", al massimo "da verificare".

Lo stesso motore serve al catalogo della plancia: i filtri sono un profilo "parziale" (`parziale=True`), e i
vincoli su cui il filtro non dice nulla non si guardano. Il formato del profilo e' in docs/PROFILO_IMPRESA.md.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from datetime import date

from app.abbinamento import ateco
from app.abbinamento.territorio import NOMI_REGIONI, nome_comune, regione_della_provincia

COMPATIBILE, DA_VERIFICARE, ESCLUSO = "compatibile", "da_verificare", "escluso"
ORDINE_LIVELLI = {COMPATIBILE: 0, DA_VERIFICARE: 1, ESCLUSO: 2}

# Classe dimensionale (raccomandazione UE 2003/361): dipendenti sotto la soglia e fatturato entro la soglia
# (in alternativa il totale di bilancio, che spesso manca: allora la classe e' stimata).
CLASSI = ("micro", "piccola", "media", "grande")
_SOGLIE = (("micro", 10, 2_000_000, 2_000_000), ("piccola", 50, 10_000_000, 10_000_000),
           ("media", 250, 50_000_000, 43_000_000))

# Territorio a parole che vuol dire "anche l'Italia": bandi UE e nazionali con gli elenchi vuoti.
_TUTTA_ITALIA = re.compile(r"stat[oi] membr|horizon|paesi (ammissibili|partecipanti)|unione europea|\bue\b|"
                           r"tutt[oa] (il territorio|italia)|territorio nazionale|nazionale|\bitalia\b", re.IGNORECASE)

NOMI_VINCOLI = {
    "territorio": "territorio", "soggetti": "tipo di soggetto", "forme_giuridiche": "forma giuridica",
    "dimensioni": "dimensione", "ateco": "codice ATECO", "eta_impresa": "età dell'impresa",
    "requisiti_speciali": "requisiti speciali", "dipendenti": "numero di dipendenti", "fatturato": "fatturato",
    "spesa": "importo del progetto", "regime_aiuto": "regime d'aiuto",
}


@dataclass
class Esito:
    livello: str = COMPATIBILE
    esclusioni: list[str] = field(default_factory=list)      # perche' il bando non va
    da_verificare: list[str] = field(default_factory=list)   # cosa manca per dire "va bene"
    punti_a_favore: list[str] = field(default_factory=list)  # requisiti rispettati, premialita', interessi in comune
    da_controllare: list[str] = field(default_factory=list)  # con il cliente: de minimis, esclusioni, obblighi
    interessi: int = 0                                        # temi e spese in comune: serve a ordinare
    fuori_zona: bool = False                                  # bando di un'altra regione: in fondo ai da verificare

    def escludi(self, motivo: str) -> None:
        self.esclusioni.append(motivo)

    def verifica(self, motivo: str) -> None:
        self.da_verificare.append(motivo)

    def chiudi(self) -> "Esito":
        self.livello = ESCLUSO if self.esclusioni else DA_VERIFICARE if self.da_verificare else COMPATIBILE
        return self

    def come_dict(self) -> dict:
        return {"livello": self.livello, "esclusioni": self.esclusioni, "da_verificare": self.da_verificare,
                "punti_a_favore": self.punti_a_favore, "da_controllare": self.da_controllare,
                "interessi": self.interessi, "fuori_zona": self.fuori_zona, "dubbi_pesanti": dubbi_pesanti(self)}


def classe_dimensionale(profilo: dict) -> tuple[str | None, str | None]:
    """(classe, classe_possibile_se_piu_piccola). La classe dichiarata vince; altrimenti la si stima da dipendenti e
    fatturato. Senza totale di bilancio, un'impresa grande per fatturato potrebbe essere piu' piccola: la seconda
    voce dice quale."""
    if profilo.get("dimensione"):
        return profilo["dimensione"], None
    dip, fatt, bil = profilo.get("dipendenti"), profilo.get("fatturato"), profilo.get("totale_bilancio")
    if dip is None and fatt is None:
        return None, None
    per_dip = next((c for c, soglia, _, _ in _SOGLIE if dip is not None and dip < soglia), "grande") if dip is not None else None
    per_soldi = None
    if fatt is not None or bil is not None:
        per_soldi = next((c for c, _, s_fatt, s_bil in _SOGLIE
                          if (fatt is not None and fatt <= s_fatt) or (bil is not None and bil <= s_bil)), "grande")
    candidati = [c for c in (per_dip, per_soldi) if c]
    classe = max(candidati, key=CLASSI.index)
    possibile = None
    if per_dip and per_soldi and CLASSI.index(per_soldi) > CLASSI.index(per_dip) and bil is None:
        possibile = per_dip   # col totale di bilancio sotto soglia sarebbe della classe dei dipendenti
    return classe, possibile


def mesi_tra(inizio: date, fine: date) -> int:
    return (fine.year - inizio.year) * 12 + fine.month - inizio.month - (fine.day < inizio.day)


def _euro(n) -> str:
    return f"{float(n):,.0f} €".replace(",", ".")


def _elenco(valori) -> str:
    return ", ".join(str(v).replace("_", " ") for v in valori)


def _stato(bando: dict, vincolo: str) -> str:
    return (bando.get("vincoli") or {}).get(vincolo) or "non_noto"


# --- le regole, una per vincolo --------------------------------------------------------------------------------

def _territorio(b: dict, p: dict, e: Esito, parziale: bool) -> None:
    sedi = [s for s in (p.get("sedi") or []) if s.get("regione") or s.get("provincia") or s.get("comune")]
    if parziale and not sedi:
        return
    stato = _stato(b, "territorio")
    if stato == "nessun_vincolo":
        _progetto_altrove(b, sedi, e)
        return
    livelli = set(b.get("livelli") or [])
    if stato == "non_noto" and livelli and livelli <= {"ue", "nazionale"} and _TUTTA_ITALIA.search(b.get("territorio") or ""):
        return   # bandi UE e nazionali: "Paesi ammissibili", "Stati membri"... l'Italia c'e' sempre
    if stato == "non_noto":
        regioni_fonti = set(b.get("regioni_fonti") or [])
        locale = regioni_fonti and set(b.get("livelli") or []) <= _LIVELLI_LOCALI
        regioni_sedi = {s.get("regione") or regione_della_provincia(s.get("provincia")) for s in sedi}
        if locale and not regioni_sedi & regioni_fonti:
            e.fuori_zona = True
            e.verifica(f"territorio non noto, ma il bando è di {_dove(regioni_fonti, set(), [])}")
        else:
            e.verifica("territorio non noto: leggere il bando")
        return
    if not sedi:
        e.verifica("manca la sede dell'impresa")
        return
    regioni = set(b.get("territorio_regioni") or [])
    province = {x.upper() for x in (b.get("territorio_province") or [])}
    comuni = {nome_comune(x) for x in (b.get("territorio_comuni") or [])}
    if not (regioni or province or comuni):
        if _TUTTA_ITALIA.search(b.get("territorio") or ""):
            return
        e.verifica(f"territorio scritto solo a parole: {(b.get('territorio') or 'non indicato')[:120]}")
        return
    richiesta = b.get("sede_richiesta") or "legale_o_operativa"
    tipi = {"legale": ("legale", "legale_e_operativa"), "operativa": ("operativa", "legale_e_operativa")}.get(richiesta)
    candidate = [s for s in sedi if not tipi or (s.get("tipo") or "legale_e_operativa") in tipi]
    if richiesta == "operativa" and not candidate:
        candidate = [s for s in sedi if s.get("tipo") == "legale"]   # sede legale senza indicazioni: spesso e' anche operativa
        dubbio_tipo = bool(candidate)
    else:
        dubbio_tipo = False
    coperte = {regione_della_provincia(x) for x in province}
    # Bando di un comune senza regione scritta: la regione e' quella delle fonti che lo pubblicano.
    regioni_comuni = regioni or ({r for r in (b.get("regioni_fonti") or [])} if comuni and not province else set())
    grado = {"no": 0, "forse": 1, "si": 2}
    esito_migliore = "no"
    for s in candidate:
        regione = s.get("regione") or regione_della_provincia(s.get("provincia"))
        if s.get("comune") and nome_comune(s["comune"]) in comuni:
            questo = "si"
        elif s.get("provincia") and s["provincia"].upper() in province:
            questo = "si"
        elif regione and regione in regioni and regione not in coperte:
            questo = "si" if not comuni else "forse"
        elif comuni and not s.get("comune") and (not regioni_comuni or regione in regioni_comuni):
            questo = "forse"
        elif province and not s.get("provincia") and regione and regione in coperte:
            questo = "forse"
        else:
            questo = "no"
        esito_migliore = max(esito_migliore, questo, key=grado.get)
        if esito_migliore == "si":
            break
    dove = _dove(regioni, province, b.get("territorio_comuni") or [])
    if esito_migliore == "si":
        if dubbio_tipo:
            e.verifica(f"serve una sede operativa in {dove}: verificare che la sede legale lo sia")
        else:
            e.punti_a_favore.append(f"sede in {dove}")
    elif esito_migliore == "forse":
        e.verifica(f"il bando vale solo per {dove}: completare provincia e comune della sede")
    elif richiesta == "da_attivare":
        # Ammessa anche senza sede, ma solo aprendone una: e' una scelta da fare con il cliente, non un "compatibile".
        e.fuori_zona = True
        e.verifica(f"nessuna sede in {dove}: il bando chiede di aprirne una prima dell'erogazione")
    else:
        tipo_sede = {"legale": "sede legale", "operativa": "sede operativa"}.get(richiesta, "sede")
        e.escludi(f"serve una {tipo_sede} in {dove}")


_LIVELLI_LOCALI = {"regione", "camera", "capoluogo", "provincia", "fondazione"}


def _progetto_altrove(b: dict, sedi: list[dict], e: Esito) -> None:
    """Nessun vincolo sulla sede, ma il bando lo pubblicano solo enti di un'altra regione: di solito e' il progetto
    (le riprese, il terreno, l'immobile) a dover stare li'. Non si esclude, ma si segnala."""
    regioni_fonti = set(b.get("regioni_fonti") or [])
    livelli = set(b.get("livelli") or [])
    if not regioni_fonti or not livelli or not livelli <= _LIVELLI_LOCALI or not sedi:
        return
    regioni_sedi = {s.get("regione") or regione_della_provincia(s.get("provincia")) for s in sedi}
    if not regioni_sedi & regioni_fonti:
        e.fuori_zona = True
        e.verifica(f"bando di {_dove(regioni_fonti, set(), [])}: la sede può essere altrove, "
                   "ma di solito il progetto va realizzato lì")


def _dove(regioni, province, comuni) -> str:
    parti = [NOMI_REGIONI.get(r, r) for r in sorted(regioni)] + [f"provincia {p}" for p in sorted(province)]
    parti += list(comuni)[:5]
    return ", ".join(parti) or "nel territorio del bando"


# Bandi non per imprese (07/10/2026, email di prova di Matteo: bandi 809 e 3883 proposti come "da verificare"). Chi fa
# attivita' economica: impresa, professionista, aspirante imprenditore. Gli altri soggetti non sono imprese.
_IMPRENDITORIALI = {"impresa", "libero_professionista", "aspirante_imprenditore"}
# Parole che dicono che tra i destinatari ci sono anche imprese o professionisti (se mancano, il bando e' per altri).
_PAROLE_IMPRESA = re.compile(r"impres|aziend|societ[aà]|\bditt[ae]\b|operatori economici|\bm?pmi\b|consorzi|cooperativ|"
                             r"start-?up|professionist|commercian|esercent|artigian|datori di lavoro|partita iva|"
                             r"lavorator[ei] autonom", re.IGNORECASE)
# Frasi che ammettono le imprese solo in casi particolari, in un bando fatto per enti e associazioni.
_IMPRESE_SOLO_IN_PARTE = re.compile(
    r"solo per (le )?iniziative (senza|non a) scopo di lucro|"
    r"non (devono|possono) essere (usat|utilizzat)\w* per attivit[aà] economic\w*|"
    r"imprese singole possono beneficiare solo|non sono ammesse le imprese", re.IGNORECASE)
_SOLO_SOCIALI = re.compile(r"(impres[ae]|cooperativ[ae])( \w+)? social[ei]", re.IGNORECASE)
_TITOLO_NON_PROFIT = re.compile(r"senza scopo di lucro|non a scopo di lucro|no[- ]?profit|terzo settore|volontariato",
                                re.IGNORECASE)


def _non_per_imprese(b: dict, soggetto: str | None, stato: str) -> str | None:
    """Il motivo per cui un bando che a parole non esclude le imprese in realta' non e' per loro, oppure None.
    Prudente: si guarda solo quando l'elenco dei beneficiari non contiene imprese (o le ammette solo per iniziative
    senza scopo di lucro) e il testo "a chi si rivolge" non parla di imprese."""
    if soggetto not in _IMPRENDITORIALI or stato == "nessun_vincolo":
        return None
    elenco = b.get("soggetti_ammessi") or []
    ammessi = set(elenco)
    testo = " ".join((b.get("a_chi_si_rivolge") or "").split())
    if ammessi & _IMPRENDITORIALI:
        parte = _IMPRESE_SOLO_IN_PARTE.search(testo)
        if parte and elenco[0] not in _IMPRENDITORIALI:
            return f"il bando è per enti e associazioni: le imprese solo in casi particolari («{parte.group(0)}»)"
        return None
    if ammessi and "altro" not in ammessi:
        return None   # "ammessi solo: ..." lo dice gia' la regola dei soggetti
    if _PAROLE_IMPRESA.search(testo):
        return None
    if testo and (ammessi or b.get("per_imprese") == "incerto"):
        return f"il bando non è per imprese: si rivolge a {testo[:140].rstrip(' ,;.')}{'…' if len(testo) > 140 else ''}"
    if b.get("per_imprese") == "incerto" or _TITOLO_NON_PROFIT.search(b.get("titolo") or ""):
        return "dal bando non risulta che le imprese possano partecipare"
    return None


def _solo_imprese_sociali(b: dict) -> bool:
    """Le sole imprese ammesse sono imprese o cooperative sociali (es. bando 519)."""
    testo = b.get("a_chi_si_rivolge") or ""
    return bool(_SOLO_SOCIALI.search(testo)) and not _PAROLE_IMPRESA.search(_SOLO_SOCIALI.sub(" ", testo)) \
        and (b.get("soggetti_ammessi") or ["impresa"])[0] != "impresa"


def _soggetti(b: dict, p: dict, e: Esito, parziale: bool) -> None:
    soggetto = "aspirante_imprenditore" if p.get("da_costituire") else p.get("soggetto")
    if parziale and not soggetto:
        return
    stato = _stato(b, "soggetti")
    motivo = _non_per_imprese(b, soggetto, stato)
    if motivo:
        e.escludi(motivo)
        return
    if stato == "vincolo" and soggetto in _IMPRENDITORIALI and _solo_imprese_sociali(b):
        sociale = (p.get("requisiti") or {}).get("impresa_sociale")
        if sociale is False:
            e.escludi("riservato a imprese e cooperative sociali")
        elif sociale is None:
            e.verifica("tra le imprese ammette solo le imprese sociali: dato mancante nel profilo")
        return
    if stato == "nessun_vincolo":
        return
    if stato == "non_noto":
        e.verifica("beneficiari non noti")
        return
    ammessi = b.get("soggetti_ammessi") or []
    if not soggetto:
        e.verifica("manca il tipo di soggetto")
    elif not ammessi:
        e.verifica("beneficiari scritti solo a parole: leggere a chi si rivolge")
    elif soggetto in ammessi:
        return
    elif "altro" in ammessi:
        e.verifica(f"ammessi anche altri soggetti ({_elenco(ammessi)}): verificare")
    else:
        e.escludi(f"ammessi solo: {_elenco(ammessi)}")


def _forme(b: dict, p: dict, e: Esito, parziale: bool) -> None:
    forma = p.get("forma_giuridica")
    if parziale and not forma:
        return
    stato = _stato(b, "forme_giuridiche")
    ammesse, escluse = b.get("forme_giuridiche_ammesse") or [], b.get("forme_giuridiche_escluse") or []
    if stato == "nessun_vincolo":
        return
    if stato == "non_noto":
        e.verifica("forme giuridiche ammesse non note")
        return
    if not forma:
        e.verifica("manca la forma giuridica")
        return
    simili = {forma, "srl"} if forma == "srls" else {forma}   # una srl semplificata e' una srl
    if escluse and forma in escluse:
        e.escludi(f"forma giuridica esclusa ({forma.replace('_', ' ')})")
    elif ammesse and not simili & set(ammesse):
        if "altro" in ammesse:
            e.verifica(f"forme ammesse: {_elenco(ammesse)}: verificare")
        else:
            e.escludi(f"forme ammesse: {_elenco(ammesse)}")
    elif not ammesse and not escluse:
        e.verifica("forme giuridiche scritte solo a parole")


def _dimensioni(b: dict, p: dict, e: Esito, parziale: bool) -> None:
    classe, possibile = classe_dimensionale(p)
    if parziale and not classe:
        return
    stato = _stato(b, "dimensioni")
    ammesse = b.get("dimensioni_ammesse") or []
    if stato == "nessun_vincolo":
        return
    if stato == "non_noto":
        e.verifica("dimensioni ammesse non note")
        return
    if not classe:
        e.verifica("manca la dimensione dell'impresa")
    elif not ammesse:
        e.verifica("dimensioni ammesse scritte solo a parole")
    elif classe in ammesse:
        e.punti_a_favore.append(f"{classe} impresa ammessa")
    elif possibile and possibile in ammesse:
        e.verifica(f"ammesse {_elenco(ammesse)}: l'impresa lo è se il totale di bilancio è sotto soglia")
    else:
        e.escludi(f"ammesse solo imprese {_elenco(ammesse)}")


def _ateco(b: dict, p: dict, e: Esito, parziale: bool) -> None:
    codici = [c for c in (p.get("ateco") or []) if ateco.normalizza(c)]
    if parziale and not codici:
        return
    stato = _stato(b, "ateco")
    ammessi, esclusi = b.get("codici_ateco") or [], b.get("codici_ateco_esclusi") or []
    versione_bando = b.get("ateco_versione")
    versione_cliente = p.get("ateco_versione") or "2025"
    stessa_versione = versione_bando in (None, versione_cliente)
    if not codici:
        if stato != "nessun_vincolo" or esclusi:
            e.verifica("manca il codice ATECO")
        return
    # Le esclusioni valgono sempre, anche con "tutti i settori".
    for x in esclusi:
        if any(ateco.contiene(x, c, versione_bando or versione_cliente) == "si" for c in codici):
            if stessa_versione:
                e.escludi(f"settore escluso (ATECO {x})")
            else:
                e.verifica(f"settore forse escluso (ATECO {x}, versione {versione_bando}): verificare")
            return
    if stato == "nessun_vincolo":
        return
    if stato == "non_noto":
        e.verifica("settori ammessi non noti")
        return
    if not ammessi:
        if not esclusi:
            e.verifica("settori ammessi scritti solo a parole")
        return
    risposte = [ateco.contiene(x, c, versione_bando or versione_cliente) for x in ammessi for c in codici]
    if "si" in risposte:
        if stessa_versione:
            e.punti_a_favore.append("ATECO ammesso")
        else:
            e.verifica(f"ATECO ammesso ma il bando usa la versione {versione_bando}: verificare la corrispondenza")
    elif "forse" in risposte:
        e.verifica("il bando ammette solo alcune sottocategorie dell'ATECO del cliente")
    elif stessa_versione:
        e.escludi(f"ATECO non ammesso (ammessi: {_elenco(ammessi[:8])}{'…' if len(ammessi) > 8 else ''})")
    else:
        e.verifica(f"ATECO non trovato tra gli ammessi, ma il bando usa la versione {versione_bando}: verificare")


def _eta(b: dict, p: dict, e: Esito, parziale: bool, oggi: date) -> None:
    costituzione = p.get("data_costituzione")
    if isinstance(costituzione, str):
        costituzione = date.fromisoformat(costituzione)
    mesi = 0 if p.get("da_costituire") else (mesi_tra(costituzione, oggi) if costituzione else None)
    if parziale and mesi is None:
        return
    stato = _stato(b, "eta_impresa")
    minimo, massimo = b.get("eta_impresa_min_mesi"), b.get("eta_impresa_max_mesi")
    if stato == "nessun_vincolo":
        return
    if stato == "non_noto":
        e.verifica("età dell'impresa richiesta non nota")
        return
    if minimo is None and massimo is None:
        e.verifica("limite di età dell'impresa scritto solo a parole")
    elif mesi is None:
        e.verifica("manca la data di costituzione")
    elif minimo is not None and mesi < minimo:
        e.escludi(f"serve un'impresa attiva da almeno {minimo} mesi")
    elif massimo is not None and mesi > massimo:
        e.escludi(f"serve un'impresa nata da non più di {massimo} mesi")


def _requisiti(b: dict, p: dict, e: Esito, parziale: bool) -> None:
    requisiti = p.get("requisiti") or {}
    obbligatori = b.get("requisiti_speciali_obbligatori") or []
    for r in b.get("requisiti_speciali_premiali") or []:
        if requisiti.get(r):
            e.punti_a_favore.append(f"premialità: {r.replace('_', ' ')}")
    if parziale:
        # Nel catalogo il filtro "femminile" cerca i bandi riservati o premiali: lo fa catalogo.filtra.
        return
    stato = _stato(b, "requisiti_speciali")
    if stato == "nessun_vincolo":
        return
    if stato == "non_noto":
        e.verifica("requisiti speciali non noti")
        return
    if not obbligatori:
        e.verifica("requisiti speciali scritti solo a parole")
        return
    for r in obbligatori:
        valore = requisiti.get(r)
        if r == "nuova_impresa" and valore is None and p.get("da_costituire"):
            valore = True
        nome = r.replace("_", " ")
        if r == "altro":
            e.verifica("c'è un requisito speciale da leggere nel bando")
        elif valore is True:
            e.punti_a_favore.append(f"requisito {nome}")
        elif valore is False:
            e.escludi(f"riservato a impresa {nome}")
        else:
            e.verifica(f"serve impresa {nome}: dato mancante nel profilo")


def _intervallo(b: dict, p: dict, e: Esito, parziale: bool, vincolo: str, campo: str, nome: str, euro: bool) -> None:
    valore = p.get(campo)
    if parziale and valore is None:
        return
    stato = _stato(b, vincolo)
    minimo, massimo = b.get(f"{campo}_min"), b.get(f"{campo}_max")
    if stato == "nessun_vincolo" or (stato == "vincolo" and minimo is None and massimo is None):
        return   # la soglia a parole di solito coincide con la dimensione, gia' controllata
    if stato == "non_noto":
        e.verifica(f"soglie di {nome} non note")
        return
    fmt = _euro if euro else (lambda n: f"{float(n):g}")
    if valore is None:
        e.verifica(f"manca il {nome} (il bando chiede {'da ' + fmt(minimo) if minimo is not None else ''}"
                   f"{' a ' + fmt(massimo) if massimo is not None else ''})")
    elif minimo is not None and valore < minimo:
        e.escludi(f"{nome} sotto il minimo di {fmt(minimo)}")
    elif massimo is not None and valore > massimo:
        e.escludi(f"{nome} sopra il massimo di {fmt(massimo)}")


def _spesa_e_interessi(b: dict, p: dict, e: Esito) -> None:
    """Serve a ordinare, non a escludere (docs/SCHEDA_BANDO.md)."""
    importo = p.get("importo_progetto")
    if importo is not None:
        if b.get("spesa_minima") and importo < b["spesa_minima"]:
            e.verifica(f"progetto sotto la spesa minima di {_euro(b['spesa_minima'])}")
        elif b.get("spesa_massima") and importo > b["spesa_massima"]:
            e.da_controllare.append(f"spesa ammessa al massimo {_euro(b['spesa_massima'])}: il resto è a carico dell'impresa")
    temi = set(p.get("temi") or []) & set(b.get("temi") or [])
    spese = set(p.get("categorie_spesa") or []) & set(b.get("categorie_spesa") or [])
    e.interessi = len(temi) + len(spese)
    if temi or spese:
        e.punti_a_favore.append(f"in linea con: {_elenco(sorted(temi | spese))}")


def _da_controllare(b: dict, e: Esito) -> None:
    regimi = b.get("regime_aiuto") or []
    if "de_minimis" in regimi or "de_minimis_agricolo" in regimi:
        e.da_controllare.append("aiuti de minimis ricevuti negli ultimi 3 anni")
    esclusioni = (b.get("esclusioni") or {}).get("soggetti") or []
    if esclusioni:
        e.da_controllare.append(f"esclusioni: {_elenco(esclusioni)}")
    if b.get("modalita_selezione") in ("sportello", "sportello_valutativo", "click_day"):
        e.da_controllare.append(f"domanda {b['modalita_selezione'].replace('_', ' ')}: presentarla presto")
    linee = b.get("linee") or []
    if len(linee) > 1:
        e.da_controllare.append(f"il bando ha {len(linee)} linee: scegliere quella adatta")


def valuta(bando: dict, profilo: dict, oggi: date | None = None, parziale: bool = False) -> Esito:
    """Confronta una scheda (riga di `bandi`) con un profilo. `parziale`: i dati che mancano al profilo non si
    guardano (filtri del catalogo), invece di dare "da verificare" (abbinamento di un profilo vero)."""
    oggi = oggi or date.today()
    e = Esito()
    _territorio(bando, profilo, e, parziale)
    _soggetti(bando, profilo, e, parziale)
    _forme(bando, profilo, e, parziale)
    _dimensioni(bando, profilo, e, parziale)
    _ateco(bando, profilo, e, parziale)
    _eta(bando, profilo, e, parziale, oggi)
    _requisiti(bando, profilo, e, parziale)
    _intervallo(bando, profilo, e, parziale, "dipendenti", "dipendenti", "numero di dipendenti", euro=False)
    _intervallo(bando, profilo, e, parziale, "fatturato", "fatturato", "fatturato", euro=True)
    _spesa_e_interessi(bando, profilo, e)
    _da_controllare(bando, e)
    if bando.get("completezza") != "bando_ufficiale" and not e.esclusioni:
        e.verifica("scheda fatta solo su una sintesi, non sul bando ufficiale"
                   if bando.get("completezza") == "solo_sintesi" else "scheda senza documenti letti")
    if not parziale and bando.get("stato") not in ("aperto", "in_arrivo"):
        if bando.get("stato") == "chiuso":
            e.escludi("bando chiuso")
        else:
            e.verifica("stato del bando non noto (nessuna data)")
    return e.chiudi()


# Dubbi "lievi": di solito il bando non pone davvero quel limite, o basta leggerlo. Gli altri (territorio, beneficiari,
# settori, dimensione, requisiti che mancano al profilo) possono escludere l'impresa: sono "pesanti".
_DUBBI_LIEVI = ("soglie di ", "scheda fatta solo su una sintesi", "scheda senza documenti", "età dell'impresa richiesta non nota",
                "forme giuridiche ammesse non note", "requisiti speciali non noti", "stato del bando non noto",
                "limite di età dell'impresa scritto solo a parole", "forme giuridiche scritte solo a parole")


def dubbi_pesanti(esito: Esito) -> int:
    return sum(1 for d in esito.da_verificare if not d.startswith(_DUBBI_LIEVI))


def chiave_ordine(bando: dict, esito: Esito) -> tuple:
    """Prima i compatibili, poi i da verificare, poi gli esclusi. Tra i da verificare: prima quelli della zona
    dell'impresa, poi quelli con meno dubbi pesanti e meno dubbi in tutto (i piu' vicini a "compatibile"); a parita',
    piu' interessi in comune e scadenza piu' vicina (senza scadenza in fondo)."""
    scadenza = bando.get("scadenza")
    dubbi = (dubbi_pesanti(esito), len(esito.da_verificare)) if esito.livello == DA_VERIFICARE else (0, 0)
    return (ORDINE_LIVELLI[esito.livello], esito.fuori_zona, *dubbi, -esito.interessi, scadenza is None, scadenza or date.max)
