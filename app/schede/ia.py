"""L'IA nelle schede: smistamento, controllo preliminare e scheda con Claude Opus 5.5. SPENTO senza chiave.

Dal 28/09/2026 (decisione di Matteo dopo la valutazione del 27/09, docs/ricerche/2026-09-27_valutazione_efficacia.md)
tutti e tre i passi usano Opus 5.5: Haiku scartava aiuti veri, Sonnet lasciava errori gravi in 9 schede su 21.
Con Opus 5.5 il ragionamento e' sempre acceso (non si spegne: 400) e si regola con `effort`, di base "medium".

Finche' nell'ambiente manca ANTHROPIC_API_KEY (la chiave API con il tetto di spesa, mai quella dell'abbonamento)
nessuna funzione di questo modulo chiama l'API: i comandi lo dicono e si fermano. Le protezioni chieste dalla
prova del 25/09/2026 (docs/ricerche/2026-09-25_prova_ia.md) sono gia' qui:

  - smistamento a lotti di 20 annunci; si controlla che tornino tutti gli id e si rimandano i mancanti una volta;
    chi manca ancora resta "da_rivedere" con il motivo "l'IA non ha risposto";
  - risposte in JSON vincolato da uno schema (output_config.format), poi verificate anche dal programma
    (valori ammessi, date, importi, fonti; per le schede verifica_scheda);
  - Batch API (meta' prezzo, risposta entro 24 ore) per tutto quello che non e' urgente, con --batch;
  - controllo preliminare prima della scheda: e' per imprese? e' l'edizione in corso? e' aperto? c'e' il testo
    del bando? Solo se passa si chiede la scheda. Prima, gratis, i segnali di stato (app/schede/segnali.py): un
    bando con soli segnali di chiusura non va all'IA; un bando che l'IA dice chiuso ma che ha una scadenza futura
    nei dati della fonte si rilegge una seconda volta, con piu' ragionamento;
  - un tetto di spesa mensile anche nel programma (IA_TETTO_MESE_USD, di base 30 $), oltre a quello della Console;
  - le decisioni di Matteo non si sovrascrivono mai.

Uso (quando la chiave ci sara'):
  python -m app.schede.ia stato                        # IA accesa o spenta, spesa del mese
  python -m app.schede.ia smista --limite 100          # gli annunci "da_rivedere" delle regole
  python -m app.schede.ia schede --limite 10           # controllo preliminare e scheda dei bandi pronti
  python -m app.schede.ia schede --bando 45
  python -m app.schede.ia smista --batch               # invia un lotto alla Batch API e si ferma
  python -m app.schede.ia raccogli                     # legge i risultati dei lotti inviati
  python -m app.schede.ia schede --batch --limite 150  # controlli preliminari e schede con la Batch API
  python -m app.schede.ia ciclo                        # il giro automatico (lo fa gia' la raccolta ogni ora)
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from dataclasses import dataclass, field
from datetime import date, datetime, timezone
from pathlib import Path

from app.schede import campi
from app.db.blocchi import con_blocco

CARTELLA = Path(__file__).resolve().parent
MODELLO_SMISTAMENTO = "claude-opus-5-5"
MODELLO_PRELIMINARE = "claude-opus-5-5"
MODELLO_SCHEDA = "claude-opus-5-5"
# Quanto ragiona il modello (output_config.effort). Opus 5.5 ha "medium" di base: lo si scrive sempre, esplicito.
EFFORT = {"smistamento": "medium", "preliminare": "medium", "seconda_lettura": "high", "scheda": "medium"}
DIMENSIONE_LOTTO = 20            # la prova del 25/09 ha perso 2 annunci su lotti da 45
MASSIMO_TESTO_SCHEDA = 300_000   # caratteri di documenti per la scheda (circa 75.000 token; 02/10: con 150.000 i bandi a piu' assi perdevano le ultime parti)
MASSIMO_TESTO_PRELIMINARE = 18_000   # circa 3.000 parole
# Prezzi in dollari per milione di token (ingresso, uscita, lettura dalla cache), verificati il 28/09/2026;
# con la Batch API la meta'. La scrittura in cache costa 1,25 volte l'ingresso.
PREZZI = {"claude-opus-5-5": (4.0, 20.0, 0.20), "claude-haiku-4-5": (1.0, 5.0, 0.10), "claude-sonnet-5": (2.0, 10.0, 0.20)}
TETTO_MESE_PREDEFINITO = 30.0


class IASpenta(RuntimeError):
    """Manca la chiave API, o il tetto di spesa del mese e' raggiunto: non si chiama l'API."""


def chiave_presente() -> bool:
    return bool(os.environ.get("ANTHROPIC_API_KEY", "").strip())


def nuovo_client():
    """Il client dell'SDK ufficiale. Solo con la chiave API: mai credenziali dell'abbonamento (CLAUDE.md)."""
    if not chiave_presente():
        raise IASpenta("IA spenta: manca ANTHROPIC_API_KEY nel file .env (chiave API con tetto di spesa)")
    import anthropic

    return anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"], max_retries=3)


# --- prompt ------------------------------------------------------------------------------------------

def leggi_prompt(nome: str) -> tuple[str, str]:
    """(istruzioni, modello del messaggio): il file si divide al primo titolo di primo livello dopo # ISTRUZIONI.
    Le istruzioni sono uguali per tutte le chiamate, quindi vanno nel messaggio di sistema."""
    testo = re.sub(r"<!--.*?-->", "", (CARTELLA / nome).read_text(encoding="utf-8"), flags=re.S).strip()
    parti = re.split(r"(?m)^# (?!ISTRUZIONI)", testo, maxsplit=1)
    istruzioni = parti[0].replace("# ISTRUZIONI", "", 1).strip()
    return istruzioni, ("# " + parti[1]).strip() if len(parti) > 1 else ""


def riempi(modello: str, valori: dict) -> str:
    """Segnaposto {{nome}} e blocchi {{#elenco}}...{{/elenco}} (ripetuti per ogni elemento, o tolti se vuoti)."""
    def blocco(m: re.Match) -> str:
        nome, corpo = m.group(1), m.group(2)
        elenco = valori.get(nome)
        if not elenco:
            return ""
        if not isinstance(elenco, list):
            elenco = [valori]
        return "".join(riempi(corpo, {**valori, **(x if isinstance(x, dict) else {})}) for x in elenco)

    testo = re.sub(r"\{\{#(\w+)\}\}(.*?)\{\{/\1\}\}", blocco, modello, flags=re.S)
    return re.sub(r"\{\{(\w+)\}\}", lambda m: "" if valori.get(m.group(1)) is None else str(valori[m.group(1)]), testo)


# --- schemi JSON delle risposte (output_config.format) ---------------------------------------------

def _o_null(schema: dict) -> dict:
    return {"anyOf": [schema, {"type": "null"}]}


def _elenco(valori) -> dict:
    return {"type": "array", "items": {"type": "string", "enum": list(valori)}}


SCHEMA_SMISTAMENTO = {
    "type": "object",
    "properties": {"risposte": {"type": "array", "items": {
        "type": "object",
        "properties": {"id": {"type": "integer"},
                       "esito": {"type": "string", "enum": ["rilevante", "non_rilevante", "da_rivedere"]},
                       "motivo": {"type": "string"}},
        "required": ["id", "esito", "motivo"], "additionalProperties": False}}},
    "required": ["risposte"], "additionalProperties": False,
}

SCHEMA_PRELIMINARE = {
    "type": "object",
    "properties": {
        "per_imprese": {"type": "string", "enum": ["si", "no", "incerto"]},
        "edizione_in_corso": {"type": "string", "enum": ["si", "no", "incerto"]},
        "stato": {"type": "string", "enum": ["aperto", "in_arrivo", "chiuso", "non_noto"]},
        "testo_bando": {"type": "string", "enum": ["si", "solo_sintesi", "no"]},
        "motivo": {"type": "string"},
    },
    "required": ["per_imprese", "edizione_in_corso", "stato", "testo_bando", "motivo"], "additionalProperties": False,
}

_TESTO, _NUMERO = {"type": "string"}, {"type": "number"}
_LINEA = {
    "type": "object",
    "properties": {
        "nome": _TESTO, "a_chi_si_rivolge": _o_null(_TESTO),
        "soggetti_ammessi": _elenco(campi.SOGGETTI), "dimensioni_ammesse": _elenco(campi.DIMENSIONI),
        "requisiti_speciali_obbligatori": _elenco(campi.REQUISITI_SPECIALI),
        "eta_impresa_max_mesi": _o_null(_NUMERO),
        "codici_ateco": {"type": "array", "items": _TESTO}, "codici_ateco_esclusi": {"type": "array", "items": _TESTO},
        "tipi_agevolazione": _elenco(campi.TIPI_AGEVOLAZIONE),
        "contributo_massimo": _o_null(_NUMERO), "percentuale": _o_null(_NUMERO), "fondo_perduto_massimo": _o_null(_NUMERO),
        "spesa_minima": _o_null(_NUMERO), "spesa_massima": _o_null(_NUMERO), "note": _o_null(_TESTO),
    },
    "required": ["nome", "a_chi_si_rivolge", "soggetti_ammessi", "dimensioni_ammesse", "requisiti_speciali_obbligatori",
                 "eta_impresa_max_mesi", "codici_ateco", "codici_ateco_esclusi", "tipi_agevolazione", "contributo_massimo",
                 "percentuale", "fondo_perduto_massimo", "spesa_minima", "spesa_massima", "note"],
    "additionalProperties": False,
}
def _oggetto(proprieta: dict) -> dict:
    return {"type": "object", "properties": proprieta, "required": list(proprieta), "additionalProperties": False}


def _blocco(nome: str, **altri) -> dict:
    """Uno dei sei blocchi di dettagli (campi.DETTAGLI): numeri e testi facoltativi, piu' i campi particolari."""
    parti = campi.DETTAGLI[nome]
    return _oggetto({**{n: _o_null(_NUMERO) for n in parti["numerici"]}, **{t: _o_null(_TESTO) for t in parti["testi"]},
                     **altri})


_DETTAGLI_SCHEDA: dict[str, dict] = {
    "intensita": _blocco(
        "intensita",
        per_dimensione=_oggetto({d: _o_null(_NUMERO) for d in campi.DIMENSIONI}),
        maggiorazioni={"type": "array", "items": _oggetto({
            "motivo": {"type": "string", "enum": list(campi.MOTIVI_MAGGIORAZIONE)},
            "punti_percentuali": _o_null(_NUMERO), "note": _o_null(_TESTO)})},
    ),
    "finanziamento": _blocco("finanziamento", tasso_tipo=_o_null({"type": "string", "enum": list(campi.TIPI_TASSO)})),
    # Forma dell'incentivo (02/10): una frase chiara e una riga per gruppo di beneficiari (o linea) con le sue forme.
    "forma_incentivo": _oggetto({
        "descrizione": _o_null(_TESTO),
        "righe": {"type": "array", "items": _oggetto({
            "per_chi": _TESTO,
            "forme": {"type": "array", "items": _oggetto({
                "forma": {"type": "string", "enum": list(campi.FORME_INCENTIVO)},
                "percentuale": _o_null(_NUMERO), "massimale": _o_null(_NUMERO), "condizioni": _o_null(_TESTO)})},
            "spesa_minima": _o_null(_NUMERO), "spesa_massima": _o_null(_NUMERO),
            "agevolazione_massima": _o_null(_NUMERO), "note": _o_null(_TESTO)})},
        "note": _o_null(_TESTO),
    }),
    "vincoli_spese": _oggetto({v: _oggetto({"stato": {"type": "string", "enum": list(campi.STATI_VINCOLO)},
                                           "dettaglio": _o_null(_TESTO)}) for v in campi.VINCOLI_SPESA}),
    "esclusioni": _blocco("esclusioni", soggetti=_elenco(campi.ESCLUSIONI_SOGGETTI)),
    "obblighi": _blocco("obblighi", erogazione=_elenco(campi.EROGAZIONE)),
    "domanda": _blocco("domanda", requisiti=_elenco(campi.REQUISITI_DOMANDA)),
}
_CAMPI_SCHEDA: dict[str, dict] = {
    "titolo": _TESTO, "ente": _o_null(_TESTO), "gestore": _o_null(_TESTO), "url": _TESTO, "territorio": _o_null(_TESTO),
    "territorio_regioni": _elenco(campi.REGIONI), "territorio_province": {"type": "array", "items": _TESTO},
    "territorio_comuni": {"type": "array", "items": _TESTO},
    "sede_richiesta": _o_null({"type": "string", "enum": list(campi.SEDE_RICHIESTA)}),
    "data_apertura": _o_null(_TESTO), "ora_apertura": _o_null(_TESTO), "scadenza": _o_null(_TESTO),
    "ora_scadenza": _o_null(_TESTO), "chiuso_il": _o_null(_TESTO),
    "modalita_selezione": _o_null({"type": "string", "enum": list(campi.MODALITA_SELEZIONE)}),
    "sintesi": _o_null(_TESTO), "a_chi_si_rivolge": _o_null(_TESTO),
    "soggetti_ammessi": _elenco(campi.SOGGETTI), "forme_giuridiche_ammesse": _elenco(campi.FORME_GIURIDICHE),
    "forme_giuridiche_escluse": _elenco(campi.FORME_GIURIDICHE), "dimensioni_ammesse": _elenco(campi.DIMENSIONI),
    "requisiti_speciali_obbligatori": _elenco(campi.REQUISITI_SPECIALI),
    "requisiti_speciali_premiali": _elenco(campi.REQUISITI_SPECIALI),
    "codici_ateco": {"type": "array", "items": _TESTO}, "codici_ateco_esclusi": {"type": "array", "items": _TESTO},
    "ateco_versione": _o_null({"type": "string", "enum": list(campi.VERSIONI_ATECO)}),
    "regime_aiuto": _elenco(campi.REGIMI_AIUTO), "requisiti": _o_null(_TESTO), "cosa_finanzia": _o_null(_TESTO),
    "tipo_agevolazione": _o_null({"type": "string", "enum": [*campi.TIPI_AGEVOLAZIONE, "misto"]}),
    "tipi_agevolazione": _elenco(campi.TIPI_AGEVOLAZIONE),
    "tema": _o_null({"type": "string", "enum": list(campi.TEMI)}), "temi": _elenco(campi.TEMI),
    "categorie_spesa": _elenco(campi.CATEGORIE_SPESA), "spese_ammesse": _o_null(_TESTO),
    **{n: _o_null(_NUMERO) for n in campi.NUMERICI},
    **_DETTAGLI_SCHEDA,
    "linee": {"type": "array", "items": _LINEA},
    "vincoli": {"type": "object", "properties": {v: {"type": "string", "enum": list(campi.STATI_VINCOLO)} for v in campi.VINCOLI},
                "required": list(campi.VINCOLI), "additionalProperties": False},
    "completezza": {"type": "string", "enum": list(campi.COMPLETEZZA)},
    # Una frase per ogni vincolo "vincolo" che i numeri non spiegano (06/10/2026, segnalato da Matteo sul 423: "eta'
    # dell'impresa: limitato" senza dire come). Elenco di coppie, come le fonti. Resta nella scheda, non e' una colonna.
    "note_vincoli": {"type": "array", "items": {"type": "object", "properties": {"vincolo": _TESTO, "nota": _TESTO},
                                                "required": ["vincolo", "nota"], "additionalProperties": False}},
    # Le fonti come elenco di coppie: le chiavi libere non si possono vincolare con uno schema chiuso.
    "fonti": {"type": "array", "items": {"type": "object", "properties": {"campo": _TESTO, "fonte": _TESTO},
                                         "required": ["campo", "fonte"], "additionalProperties": False}},
    "avvertenze": {"type": "array", "items": _TESTO},
}
SCHEMA_SCHEDA = {"type": "object", "properties": _CAMPI_SCHEDA, "required": list(_CAMPI_SCHEDA), "additionalProperties": False}


# --- controlli sulle risposte -----------------------------------------------------------------------

@dataclass
class Smistamento:
    decisi: dict[int, tuple[str, str]] = field(default_factory=dict)   # id -> (esito, motivo)
    mancanti: set[int] = field(default_factory=set)
    estranei: list = field(default_factory=list)                          # id sconosciuti o doppi: si scartano


def controlla_smistamento(inviati: list[int], risposta: dict | None) -> Smistamento:
    """Tornano tutti gli id, una volta sola, con un esito ammesso? Quello che non torna va rimandato."""
    esito = Smistamento()
    attesi = set(inviati)
    for r in (risposta or {}).get("risposte") or []:
        i = r.get("id") if isinstance(r, dict) else None
        if i not in attesi or i in esito.decisi or r.get("esito") not in ("rilevante", "non_rilevante", "da_rivedere"):
            esito.estranei.append(r)
            continue
        esito.decisi[i] = (r["esito"], str(r.get("motivo") or "")[:300])
    esito.mancanti = attesi - set(esito.decisi)
    return esito


def max_token_smistamento(n: int) -> int:
    """Risposta (circa 120 token per annuncio) piu' spazio per il ragionamento, sempre acceso su Opus 5.5."""
    return 6000 + 150 * n


def lotti(elementi: list, dimensione: int = DIMENSIONE_LOTTO) -> list[list]:
    return [elementi[i:i + dimensione] for i in range(0, len(elementi), dimensione)]


def passa_preliminare(p: dict) -> tuple[bool, str]:
    """Si chiede la scheda al modello solo se il controllo preliminare non ha trovato un motivo per fermarsi."""
    if p.get("per_imprese") == "no":
        return False, "non e' per imprese"
    if p.get("edizione_in_corso") == "no":
        return False, "edizione passata (archivio)"
    if p.get("stato") == "chiuso":
        return False, "bando chiuso: bastano titolo, date e link"
    if p.get("testo_bando") == "no":
        return False, "nessun testo di bando da leggere"
    return True, "ok"


_DATA = re.compile(r"^\d{4}-\d{2}-\d{2}$")
_ORA = re.compile(r"^([01]\d|2[0-3]):[0-5]\d$")
_IMPORTO_MASSIMO = 5_000_000_000      # oltre, e' un valore di riempimento (99.999.998.000 di incentivi.gov.it)
_ELENCHI_DEL_VINCOLO = {
    "territorio": ("territorio_regioni", "territorio_province", "territorio_comuni"),
    "soggetti": ("soggetti_ammessi",), "forme_giuridiche": ("forme_giuridiche_ammesse", "forme_giuridiche_escluse"),
    "dimensioni": ("dimensioni_ammesse",), "ateco": ("codici_ateco", "codici_ateco_esclusi"),
    "eta_impresa": ("eta_impresa_min_mesi", "eta_impresa_max_mesi"), "requisiti_speciali": ("requisiti_speciali_obbligatori",),
    "dipendenti": ("dipendenti_min", "dipendenti_max"), "fatturato": ("fatturato_min", "fatturato_max"),
    "spesa": ("spesa_minima", "spesa_massima"), "regime_aiuto": ("regime_aiuto",),
}
_SENZA_FONTE = {"titolo", "url", "vincoli", "completezza", "fonti", "avvertenze", "linee", "note_vincoli"}


def _data(testo) -> date | None:
    if isinstance(testo, str) and _DATA.match(testo):
        try:
            return date.fromisoformat(testo)
        except ValueError:
            return None
    return None


def _pieno(v) -> bool:
    """Un campo dice qualcosa? Un blocco di dettagli con tutti i valori vuoti (o "non_noto") non dice niente."""
    if isinstance(v, dict):
        return any(_pieno(x) for k, x in v.items() if not (k == "stato" and x == "non_noto"))
    if isinstance(v, list):
        return any(_pieno(x) for x in v)
    return v not in (None, "", "non_noto")


def _verifica_dettagli(s: dict) -> list[str]:
    """I sei blocchi di dettagli: valori ammessi, numeri plausibili, percentuali entro 100."""
    problemi: list[str] = []
    for percorso, ammessi in campi.VALORI_AMMESSI_DETTAGLI.items():
        blocco, *resto = percorso.split(".")
        valori = [(s.get(blocco) or {}).get(resto[0])]
        if len(resto) == 2:     # elenco di oggetti: intensita.maggiorazioni.motivo
            valori = [m.get(resto[1]) for m in valori[0] or [] if isinstance(m, dict)]
        for v in valori:
            for x in (v if isinstance(v, list) else [v] if v is not None else []):
                if x not in ammessi:
                    problemi.append(f"{percorso}: valore non ammesso {x!r}")
    for blocco, parti in campi.DETTAGLI.items():
        for n in parti["numerici"]:
            v = (s.get(blocco) or {}).get(n)
            if v is None:
                continue
            if not isinstance(v, (int, float)) or v < 0 or v > _IMPORTO_MASSIMO:
                problemi.append(f"{blocco}.{n}: numero non plausibile {v!r}")
            elif f"{blocco}.{n}" in campi.PERCENTUALI_DETTAGLI and v > 100:
                problemi.append(f"{blocco}.{n}: percentuale oltre 100 ({v})")
    problemi += verifica_forma_incentivo(s.get("forma_incentivo"))
    # Dal 03/10 `percentuale` e' la percentuale base (la piu' alta tra le basi), non quella con le maggiorazioni.
    intensita = s.get("intensita") or {}
    basi = [v for v in [intensita.get("percentuale_base"), *(intensita.get("per_dimensione") or {}).values()]
            if isinstance(v, (int, float))]
    percentuale = s.get("percentuale")
    if basi and isinstance(percentuale, (int, float)):
        if percentuale > max(basi) and intensita.get("maggiorazioni"):
            problemi.append(f"percentuale {percentuale} oltre la base {max(basi)}: deve essere la percentuale base, "
                            "le maggiorazioni vanno in intensita e nelle avvertenze")
        elif percentuale < max(basi):
            problemi.append(f"percentuale {percentuale} sotto la percentuale base {max(basi)}")
    for voce, v in (s.get("vincoli_spese") or {}).items():
        if isinstance(v, dict) and v.get("stato") == "vincolo" and not v.get("dettaglio"):
            problemi.append(f"vincoli_spese.{voce} = vincolo, ma manca il dettaglio")
    return problemi


def verifica_forma_incentivo(fi) -> list[str]:
    """Forma dell'incentivo: forme ammesse, percentuali entro 100 (anche sommate nella stessa riga), importi plausibili."""
    problemi: list[str] = []
    if not isinstance(fi, dict):
        return problemi
    for i, riga in enumerate(fi.get("righe") or [], 1):
        if not isinstance(riga, dict):
            problemi.append(f"forma_incentivo.righe[{i}]: non e' un oggetto")
            continue
        if not riga.get("per_chi"):
            problemi.append(f"forma_incentivo.righe[{i}]: manca per_chi")
        somma = 0
        for f in riga.get("forme") or []:
            if not isinstance(f, dict) or f.get("forma") not in campi.FORME_INCENTIVO:
                problemi.append(f"forma_incentivo.righe[{i}]: forma non ammessa {f.get('forma') if isinstance(f, dict) else f!r}")
                continue
            pc = f.get("percentuale")
            if pc is not None and (not isinstance(pc, (int, float)) or pc < 0 or pc > 100):
                problemi.append(f"forma_incentivo.righe[{i}].{f['forma']}: percentuale non plausibile {pc!r}")
            elif isinstance(pc, (int, float)) and f["forma"] in ("fondo_perduto", "finanziamento_agevolato", "credito_imposta", "voucher"):
                somma += pc
        if somma > 100:
            problemi.append(f"forma_incentivo.righe[{i}]: le quote sulla spesa sommano {somma}% (oltre 100)")
        for n in ("spesa_minima", "spesa_massima", "agevolazione_massima"):
            v = riga.get(n)
            if v is not None and (not isinstance(v, (int, float)) or v < 0 or v > _IMPORTO_MASSIMO):
                problemi.append(f"forma_incentivo.righe[{i}].{n}: importo non plausibile {v!r}")
    return problemi


def verifica_scheda(s: dict, documenti: list[dict] | None = None) -> list[str]:
    """Controlli automatici su una scheda dell'IA. Ogni problema e' una frase; nessun problema = lista vuota.
    Una scheda con problemi si salva lo stesso, ma va in coda a Matteo (dati.problemi)."""
    problemi: list[str] = []
    for nome, ammessi in campi.VALORI_AMMESSI.items():
        v = s.get(nome)
        for x in (v if isinstance(v, list) else [v] if v is not None else []):
            if x not in ammessi:
                problemi.append(f"{nome}: valore non ammesso {x!r}")
    for nome in ("data_apertura", "scadenza", "chiuso_il"):
        if s.get(nome) is not None and _data(s[nome]) is None:
            problemi.append(f"{nome}: data non valida {s[nome]!r}")
    for nome in ("ora_apertura", "ora_scadenza"):
        if s.get(nome) is not None and not _ORA.match(str(s[nome])):
            problemi.append(f"{nome}: ora non valida {s[nome]!r}")
    apertura, scadenza = _data(s.get("data_apertura")), _data(s.get("scadenza"))
    if apertura and scadenza and apertura > scadenza:
        problemi.append("la data di apertura viene dopo la scadenza")
    if scadenza and scadenza.year < 2015:
        problemi.append(f"scadenza troppo vecchia ({scadenza})")
    for nome in campi.NUMERICI:
        v = s.get(nome)
        if v is None:
            continue
        if not isinstance(v, (int, float)) or v < 0 or v > _IMPORTO_MASSIMO:
            problemi.append(f"{nome}: importo non plausibile {v!r}")
        elif nome in campi.PERCENTUALI and v > 100:
            problemi.append(f"{nome}: percentuale oltre 100 ({v})")
    problemi += _verifica_dettagli(s)
    fp, cm = s.get("fondo_perduto_massimo"), s.get("contributo_massimo")
    if isinstance(fp, (int, float)) and isinstance(cm, (int, float)) and fp > cm:
        problemi.append("fondo perduto massimo superiore al contributo massimo")
    if s.get("tipo_agevolazione") == "misto" and s.get("percentuale") == 100 and s.get("finanziamento_massimo"):
        problemi.append("agevolazione mista al 100%: la percentuale deve riguardare solo il fondo perduto")
    vincoli = s.get("vincoli") or {}
    spiegati = {n.get("vincolo") for n in s.get("note_vincoli") or [] if isinstance(n, dict) and n.get("nota")}
    for v, elenchi in _ELENCHI_DEL_VINCOLO.items():
        stato = vincoli.get(v)
        if stato not in campi.STATI_VINCOLO:
            problemi.append(f"vincoli.{v}: stato mancante o non ammesso")
        elif stato == "vincolo" and not any(s.get(e) not in (None, []) for e in elenchi):
            if not (v == "territorio" and s.get("territorio")) and v not in spiegati:   # una nota in note_vincoli basta
                problemi.append(f"vincoli.{v} = vincolo, ma i campi {', '.join(elenchi)} sono vuoti (e manca la nota)")
    # Una regione scritta solo a parole non serve all'abbinamento (verifica del 02/10, 3677).
    if vincoli.get("territorio") == "vincolo" and not s.get("territorio_regioni") and not s.get("territorio_province"):
        from app.abbinamento.territorio import NOMI_REGIONI

        nominata = next((nome for nome in NOMI_REGIONI.values()
                         if re.search(rf"\b{re.escape(nome)}\b", s.get("territorio") or "", re.IGNORECASE)), None)
        if nominata:
            problemi.append(f"territorio: nomina {nominata}, ma territorio_regioni e' vuoto")
    fonti = {f.get("campo") for f in s.get("fonti") or [] if isinstance(f, dict)}
    senza = [n for n, v in s.items() if n not in _SENZA_FONTE and _pieno(v) and n not in fonti]
    if senza:
        problemi.append("campi senza fonte: " + ", ".join(sorted(senza)))
    if documenti is not None and s.get("completezza") == "bando_ufficiale":
        if not any((d.get("categoria") in ("bando", "decreto")) and len(d.get("testo") or "") > 2000 for d in documenti):
            problemi.append("completezza 'bando_ufficiale' ma tra i documenti non c'e' il testo di un bando o di un decreto")
    return problemi


# --- chiamate ---------------------------------------------------------------------------------------

def costo(modello: str, token_in: int, token_out: int, batch: bool = False, cache_lettura: int = 0,
          cache_scrittura: int = 0) -> float:
    """Dollari di una chiamata. token_in comprende i token letti e scritti in cache, che hanno prezzi propri."""
    ingresso, uscita, lettura = PREZZI.get(modello, (0.0, 0.0, 0.0))
    normali = max(token_in - cache_lettura - cache_scrittura, 0)
    c = (normali * ingresso + cache_scrittura * ingresso * 1.25 + cache_lettura * lettura + token_out * uscita) / 1_000_000
    return c / 2 if batch else c


def parametri(modello: str, istruzioni: str, messaggio: str, schema: dict | None, max_tokens: int,
              effort: str = "medium") -> dict:
    """I parametri di una richiesta, uguali per la chiamata diretta e per la Batch API. Istruzioni in cache.
    Opus 5.5: niente `thinking` (il ragionamento e' sempre acceso, si regola con effort), niente tool_choice
    forzato; con uno schema la risposta e' JSON vincolato (output_config.format). La scheda NON usa lo schema
    (02/10/2026: 79 campi facoltativi, l'API ne accetta al massimo 16 e rifiutava ogni richiesta): il formato lo
    descrive il prompt e la risposta passa da prepara_scheda e verifica_scheda. max_tokens comprende anche il
    ragionamento: va lasciato largo."""
    config: dict = {"effort": effort}
    if schema is not None:
        config["format"] = {"type": "json_schema", "schema": schema}
    return {
        "model": modello,
        "max_tokens": max_tokens,
        "system": [{"type": "text", "text": istruzioni, "cache_control": {"type": "ephemeral"}}],
        "messages": [{"role": "user", "content": messaggio}],
        "output_config": config,
    }


@dataclass
class Risposta:
    dati: dict | None
    esito: str                 # ok | incompleta | rifiutata | errore
    token_in: int = 0
    token_out: int = 0
    messaggio: str = ""
    cache_lettura: int = 0
    cache_scrittura: int = 0

    def costo(self, modello: str, batch: bool = False) -> float:
        return costo(modello, self.token_in, self.token_out, batch, self.cache_lettura, self.cache_scrittura)


def leggi_messaggio(msg) -> Risposta:
    """Da un messaggio dell'API (diretto o da Batch) al JSON, con i casi di errore."""
    uso = getattr(msg, "usage", None)
    lettura = getattr(uso, "cache_read_input_tokens", 0) or 0
    scrittura = getattr(uso, "cache_creation_input_tokens", 0) or 0
    token_in = (getattr(uso, "input_tokens", 0) or 0) + lettura + scrittura
    token_out = getattr(uso, "output_tokens", 0) or 0   # comprende il ragionamento
    cache = {"cache_lettura": lettura, "cache_scrittura": scrittura}
    if msg.stop_reason == "refusal":
        dettagli = getattr(msg, "stop_details", None)
        categoria = getattr(dettagli, "category", None) if dettagli else None
        return Risposta(None, "rifiutata", token_in, token_out,
                        "il modello ha rifiutato la richiesta" + (f" ({categoria})" if categoria else ""), **cache)
    if msg.stop_reason == "max_tokens":
        return Risposta(None, "incompleta", token_in, token_out, "risposta tagliata (max_tokens)", **cache)
    testo = "".join(b.text for b in msg.content if getattr(b, "type", "") == "text")
    try:
        return Risposta(estrai_json(testo), "ok", token_in, token_out, **cache)
    except json.JSONDecodeError as exc:
        return Risposta(None, "errore", token_in, token_out, f"JSON non valido: {exc}", **cache)


def estrai_json(testo: str) -> dict:
    """Il JSON della risposta. Senza schema vincolato (la scheda) il modello puo' aggiungere un blocco ```json o una
    frase prima: si prende l'oggetto dalla prima { all'ultima }."""
    testo = testo.strip()
    try:
        return json.loads(testo)
    except json.JSONDecodeError:
        inizio, fine = testo.find("{"), testo.rfind("}")
        if inizio < 0 or fine <= inizio:
            raise
        return json.loads(testo[inizio:fine + 1])


def _vuoto(schema: dict):
    if schema.get("type") == "array" or (isinstance(schema.get("type"), list) and "array" in schema["type"]):
        return []
    if schema.get("type") == "object" and "properties" in schema:
        return {k: _vuoto(v) for k, v in schema["properties"].items()}
    return None


def _completa(dati: dict, schema: dict) -> dict:
    """Aggiunge le chiavi mancanti (vuote) e toglie quelle in piu', ricorsivamente sugli oggetti."""
    fuori = {}
    for k, s in schema["properties"].items():
        v = dati.get(k)
        if s.get("type") == "object" and "properties" in s and isinstance(v, dict):
            fuori[k] = _completa(v, s)
        elif v is None:
            fuori[k] = _vuoto(s)
        else:
            fuori[k] = v
    return fuori


def prepara_scheda(grezza: dict) -> tuple[dict, list[str]]:
    """Senza schema vincolato: completa le chiavi e toglie i valori che il database o i filtri non accettano
    (fuori dagli elenchi, date e ore non valide, numeri non plausibili). Rende (scheda, cosa e' stato tolto).
    Lo usano l'API e l'importazione delle schede scritte in sessione (strumenti/sessione/ar/importa.py)."""
    s = _completa(grezza if isinstance(grezza, dict) else {}, SCHEMA_SCHEDA)
    tolti = []
    for nome, ammessi in campi.VALORI_AMMESSI.items():
        v = s.get(nome)
        if isinstance(v, list):
            buoni = [x for x in v if x in ammessi]
            if len(buoni) != len(v):
                tolti.append(f"{nome}: tolti {[x for x in v if x not in ammessi]}")
                s[nome] = buoni
        elif v is not None and v not in ammessi:
            tolti.append(f"{nome}: tolto {v!r}")
            s[nome] = None
    fi = s.get("forma_incentivo")
    if isinstance(fi, dict):
        righe = [r for r in fi.get("righe") or [] if isinstance(r, dict)]
        for r in righe:
            forme = [f for f in r.get("forme") or [] if isinstance(f, dict)]
            buone = [f for f in forme if f.get("forma") in campi.FORME_INCENTIVO]
            if len(buone) != len(forme):
                tolti.append(f"forma_incentivo: tolte forme {[f.get('forma') for f in forme if f not in buone]}")
            r["forme"] = buone
        fi["righe"] = righe
    if s.get("tipo_agevolazione") not in (None, *campi.TIPI_AGEVOLAZIONE, "misto"):
        tolti.append(f"tipo_agevolazione: tolto {s['tipo_agevolazione']!r}")
        s["tipo_agevolazione"] = None
    if s.get("tema") not in (None, *campi.TEMI):
        tolti.append(f"tema: tolto {s['tema']!r}")
        s["tema"] = None
    for nome in ("data_apertura", "scadenza", "chiuso_il"):
        if s.get(nome) is not None and _data(s[nome]) is None:
            tolti.append(f"{nome}: tolta data non valida {s[nome]!r}")
            s[nome] = None
    for nome in ("ora_apertura", "ora_scadenza"):
        if s.get(nome) is not None and not _ORA.match(str(s[nome])):
            tolti.append(f"{nome}: tolta ora non valida {s[nome]!r}")
            s[nome] = None
    for nome in campi.NUMERICI:
        v = s.get(nome)
        if v is not None and (not isinstance(v, (int, float)) or isinstance(v, bool) or v < 0 or v > _IMPORTO_MASSIMO):
            tolti.append(f"{nome}: tolto numero non plausibile {v!r}")
            s[nome] = None
    for nome in ("eta_impresa_min_mesi", "eta_impresa_max_mesi"):
        if isinstance(s.get(nome), float):
            s[nome] = round(s[nome])
    vincoli = s.get("vincoli") if isinstance(s.get("vincoli"), dict) else {}
    for v in campi.VINCOLI:
        if vincoli.get(v) not in campi.STATI_VINCOLO:
            vincoli[v] = "non_noto"
    s["vincoli"] = vincoli
    if s.get("completezza") not in campi.COMPLETEZZA:
        tolti.append(f"completezza: {s.get('completezza')!r} sostituito con nessun_documento")
        s["completezza"] = "nessun_documento"
    return s, tolti


def chiama(client, p: dict) -> Risposta:
    import anthropic

    try:
        # In streaming: con il ragionamento e schede lunghe una richiesta semplice rischia il timeout HTTP.
        with client.messages.stream(**p) as flusso:
            return leggi_messaggio(flusso.get_final_message())
    except anthropic.APIStatusError as exc:
        return Risposta(None, "errore", messaggio=f"API {exc.status_code}: {str(exc)[:200]}")
    except anthropic.APIConnectionError as exc:
        return Risposta(None, "errore", messaggio=f"rete: {str(exc)[:200]}")


# --- smistamento ------------------------------------------------------------------------------------

def messaggio_smistamento(annunci: list[dict], oggi: date) -> tuple[str, str]:
    istruzioni, modello = leggi_prompt("prompt_smistamento.md")
    istruzioni = istruzioni.replace("{{numero_annunci}}", str(len(annunci)))
    return istruzioni, riempi(modello, {"data_oggi": oggi.isoformat(), "annunci": annunci})


def smista_lotto(client, annunci: list[dict], oggi: date, registra=None) -> Smistamento:
    """Un lotto: chiamata, controllo degli id, un solo rinvio dei mancanti. Chi manca ancora resta da decidere."""
    finale = Smistamento()
    da_mandare = annunci
    for tentativo in (1, 2):
        istruzioni, messaggio = messaggio_smistamento(da_mandare, oggi)
        r = chiama(client, parametri(MODELLO_SMISTAMENTO, istruzioni, messaggio, SCHEMA_SMISTAMENTO,
                                     max_tokens=max_token_smistamento(len(da_mandare)), effort=EFFORT["smistamento"]))
        if registra:
            registra("smistamento", MODELLO_SMISTAMENTO, ",".join(str(a["id"]) for a in da_mandare), r)
        controllo = controlla_smistamento([a["id"] for a in da_mandare], r.dati)
        finale.decisi.update(controllo.decisi)
        finale.estranei += controllo.estranei
        if not controllo.mancanti:
            break
        da_mandare = [a for a in da_mandare if a["id"] in controllo.mancanti]
    finale.mancanti = {a["id"] for a in annunci} - set(finale.decisi)
    for i in finale.mancanti:
        finale.decisi[i] = ("da_rivedere", "l'IA non ha risposto")
    return finale


# --- database ---------------------------------------------------------------------------------------

def spesa_del_mese(conn) -> float:
    with conn.cursor() as cur:
        cur.execute("SELECT coalesce(sum(costo_usd), 0) AS c FROM chiamate_ia WHERE fatta_il >= date_trunc('month', now())")
        return float(cur.fetchone()["c"])


# Costo stimato di una richiesta in volo nella Batch API (misurato il 01-02/10, schede stimate): il tetto conta anche
# i lotti mandati e non ancora pagati, altrimenti un lotto grande lo sfonderebbe.
COSTO_STIMATO_IN_VOLO = {"smistamento": 0.05, "preliminare": 0.012, "scheda": 0.35, "doppione": 0.005}   # scheda: misurata 0,43 $ in batch per un bando lungo (02/10)


def spesa_in_volo(conn) -> float:
    with conn.cursor() as cur:
        cur.execute("SELECT scopo, count(*) AS n FROM chiamate_ia WHERE batch AND esito = 'inviata' GROUP BY 1")
        return sum(COSTO_STIMATO_IN_VOLO.get(r["scopo"], 0.1) * r["n"] for r in cur.fetchall())


def controlla_tetto(conn) -> None:
    tetto = float(os.environ.get("IA_TETTO_MESE_USD", TETTO_MESE_PREDEFINITO))
    speso, in_volo = spesa_del_mese(conn), spesa_in_volo(conn)
    if speso + in_volo >= tetto:
        raise IASpenta(f"tetto di spesa del mese raggiunto: {speso:.2f} $ spesi + {in_volo:.2f} $ stimati per i lotti in "
                       f"attesa, su {tetto:.2f} $ (IA_TETTO_MESE_USD)")


def registratore(conn, batch: bool = False, batch_id: str | None = None):
    def registra(scopo: str, modello: str, riferimento: str, r: Risposta) -> None:
        with conn.cursor() as cur:
            cur.execute(
                """INSERT INTO chiamate_ia (scopo, modello, batch, batch_id, riferimento, token_in, token_out, costo_usd, esito, messaggio)
                   VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)""",
                (scopo, modello, batch, batch_id, riferimento[:2000], r.token_in, r.token_out,
                 r.costo(modello, batch), r.esito, r.messaggio[:500]),
            )
        conn.commit()
    return registra


def annunci_da_smistare(conn, limite: int) -> list[dict]:
    with conn.cursor() as cur:
        cur.execute(
            """SELECT a.id, a.titolo, coalesce(a.riassunto, '') AS riassunto, a.url, f.ente, f.tipo AS tipo_fonte, f.territorio
               FROM annunci a JOIN smistamenti s ON s.annuncio_id = a.id JOIN fonti f ON f.id = a.fonte_id
               WHERE s.esito = 'da_rivedere' AND s.deciso_da = 'regole' ORDER BY a.id LIMIT %s""",
            (limite,),
        )
        return [dict(r) for r in cur.fetchall()]


def aggiungi_inizio_pagina(annunci: list[dict], caratteri: int = 1500) -> None:
    """Per gli annunci senza riassunto, l'inizio della pagina (una richiesta ciascuno, con le buone maniere):
    nella prova del 25/09 avrebbe evitato meta' degli errori di Haiku."""
    from app.raccolta.scarica import NonPermesso, nuovo_client as client_http, scarica
    from app.schede.allegati import Pausa, testo_html

    import httpx

    with client_http() as c:
        pausa = Pausa(c)
        for a in annunci:
            if (a.get("riassunto") or "").strip() or not str(a.get("url", "")).startswith("http"):
                continue
            try:
                pausa.attendi(a["url"])
                r = scarica(c, a["url"], accept="text/html")
                if r.status_code == 200 and "html" in r.headers.get("content-type", ""):
                    a["testo_pagina"] = (testo_html(r.text) or "")[:caratteri]
            except (httpx.HTTPError, NonPermesso):
                continue


def salva_smistamento(conn, decisi: dict[int, tuple[str, str]], costo_per_annuncio: float) -> None:
    """La decisione dell'IA sostituisce solo quella delle regole; mai quella di Matteo."""
    with conn.cursor() as cur:
        for i, (esito, motivo) in decisi.items():
            cur.execute(
                """UPDATE smistamenti SET esito = %s, motivo = %s, deciso_da = 'ia', costo = %s, deciso_il = now()
                   WHERE annuncio_id = %s AND deciso_da = 'regole'""",
                (esito, f"IA: {motivo}", costo_per_annuncio, i),
            )
    conn.commit()


# Scheda del catalogo nazionale incentivi.gov.it: campi dei dati grezzi dell'annuncio, con il nome per l'IA.
_CAMPI_CATALOGO = (("titolo", "Titolo"), ("gestore", "Soggetto gestore"), ("riassunto", "Descrizione"),
                   ("apertura", "Apertura"), ("scadenza", "Scadenza"), ("regioni", "Regioni"),
                   ("soggetti", "Beneficiari"), ("dimensioni", "Dimensioni d'impresa"), ("forma", "Forma dell'agevolazione"),
                   ("spese", "Spese ammesse"), ("settori", "Settori"), ("ateco", "Codici ATECO"),
                   ("costo_min", "Spesa minima (euro)"), ("costo_max", "Spesa massima (euro)"),
                   ("dotazione", "Dotazione (euro)"), ("link_ente", "Pagina dell'ente"), ("url", "Pagina del catalogo"))


def scheda_catalogo(dati: dict) -> str:
    righe = ["SCHEDA DEL CATALOGO NAZIONALE incentivi.gov.it (sintesi redatta dal Ministero, NON il testo del bando)"]
    for chiave, nome in _CAMPI_CATALOGO:
        v = dati.get(chiave)
        if isinstance(v, list):
            v = ", ".join(str(x) for x in v)
        if v not in (None, "", "0"):
            righe.append(f"{nome}: {v}")
    return "\n".join(righe)


def documenti_del_bando(conn, bando_id: int, massimo: int) -> tuple[list[dict], list[str]]:
    """I documenti del bando in ordine. Se il bando e' anche nel catalogo incentivi.gov.it, si aggiunge in testa la
    sua scheda (30/09): quando la pagina dell'ente e' vuota o bloccata e' l'unica fonte, e la scheda sara' "solo_sintesi"."""
    from app.schede.allegati import documenti_per_scheda

    with conn.cursor() as cur:
        cur.execute("""SELECT nome, url, tipo, categoria, testo_estratto, errore FROM allegati
                       WHERE bando_id = %s AND annuncio_id IS NULL""", (bando_id,))
        allegati = [dict(r) for r in cur.fetchall()]
        cur.execute("""SELECT url, dati FROM annunci WHERE bando_id = %s AND fonte_id = 'incentivi_gov_ricerca'
                       AND jsonb_typeof(dati) = 'object' ORDER BY id LIMIT 1""", (bando_id,))
        catalogo = cur.fetchone()
    if not catalogo:
        return documenti_per_scheda(allegati, massimo)
    # In testa: e' corta, e se la pagina dell'ente e' solo menu il limite del controllo preliminare la taglierebbe.
    # Il prompt dice gia' che il bando vale piu' delle sintesi.
    testo = scheda_catalogo(catalogo["dati"])[:max(0, massimo // 3)]
    sintesi = {"nome": "Scheda del catalogo incentivi.gov.it (sintesi, non il bando)", "url": catalogo["url"],
               "tipo": "pagina", "categoria": "altro", "testo_estratto": testo, "errore": None, "testo": testo}
    documenti, avvertenze = documenti_per_scheda(allegati, massimo - len(testo))
    return [sintesi, *documenti], avvertenze


MODULO_PRELIMINARE = 3_000   # caratteri dell'inizio del modulo di domanda dati al controllo preliminare
_MODULO_DOMANDA = re.compile(r"domanda|istanza|adesione|dichiarazion|richiesta di (?:contributo|agevolazione)", re.IGNORECASE)


def documenti_preliminare(conn, bando_id: int) -> list[dict]:
    """I documenti del controllo preliminare: l'inizio del bando e, in fondo, l'inizio del modulo di domanda (03/10).
    La verifica del 02/10 ha trovato bandi per societa' sportive e per enti che si vedevano solo dal modulo
    ("regime L. 398/1991", "non ente commerciale"): il modulo dice chi puo' davvero firmare la domanda."""
    from app.schede.allegati import categoria_allegato

    documenti, _ = documenti_del_bando(conn, bando_id, MASSIMO_TESTO_PRELIMINARE)
    with conn.cursor() as cur:
        cur.execute("""SELECT nome, url, tipo, categoria, testo_estratto FROM allegati WHERE bando_id = %s
                       AND annuncio_id IS NULL AND errore IS NULL AND testo_estratto IS NOT NULL ORDER BY id""", (bando_id,))
        for a in cur.fetchall():
            categoria = a["categoria"] or categoria_allegato(a["nome"] or "", a["url"] or "", a["tipo"] or "")
            if categoria == "modulistica" and _MODULO_DOMANDA.search(f"{a['nome']} {a['url']}"):
                testo = a["testo_estratto"][:MODULO_PRELIMINARE]
                documenti.append({**a, "categoria": "modulistica", "nome": f"Modulo di domanda (inizio): {a['nome']}",
                                  "testo": testo})
                break
    return documenti


def bandi_da_schedare(conn, bando_id: int | None, limite: int) -> list[dict]:
    with conn.cursor() as cur:
        if bando_id:
            cur.execute("SELECT * FROM bandi WHERE id = %s", (bando_id,))
        else:
            # Solo i bandi con il testo ufficiale tra i documenti (app/schede/documentazione.py, 01/10).
            cur.execute(
                """SELECT * FROM bandi WHERE pagina_stato = 'trovata' AND allegati_cercati_il IS NOT NULL
                   AND documentazione = 'bando' AND dati IS NULL AND preliminare IS NULL ORDER BY id LIMIT %s""", (limite,))
        return [dict(r) for r in cur.fetchall()]


_COLONNE_SCHEDA = [c for c in _CAMPI_SCHEDA if c not in ("fonti", "avvertenze", "url", "note_vincoli")]


def salva_scheda(conn, bando_id: int, scheda: dict, problemi: list[str], costo_usd: float) -> None:
    """Scrive i campi nella tabella bandi (lo stato no: lo calcola il sistema) e la risposta intera in `dati`."""
    valori = {c: scheda.get(c) for c in _COLONNE_SCHEDA}
    for c in ("vincoli", "linee", *_DETTAGLI_SCHEDA):
        valori[c] = json.dumps(valori[c]) if valori[c] is not None else None
    dati = {"risposta": scheda, "problemi": problemi, "costo_usd": round(costo_usd, 4), "modello": MODELLO_SCHEDA,
            "fonti": {f["campo"]: f["fonte"] for f in scheda.get("fonti") or [] if isinstance(f, dict) and "campo" in f},
            "avvertenze": scheda.get("avvertenze") or []}
    assegnazioni = ", ".join(f"{c} = %s" for c in valori)
    with conn.cursor() as cur:
        cur.execute("SELECT set_config('bandi_radar.causa', %s, true)", (f"scheda compilata da {MODELLO_SCHEDA}",))
        cur.execute(f"UPDATE bandi SET {assegnazioni}, dati = %s, scheda_il = now(), da_aggiornare = NULL WHERE id = %s",
                    (*valori.values(), json.dumps(dati), bando_id))
    conn.commit()


# --- comandi ----------------------------------------------------------------------------------------

def cmd_stato(conn) -> int:
    print("IA:", "ACCESA (chiave presente)" if chiave_presente() else "SPENTA (manca ANTHROPIC_API_KEY)")
    print(f"Spesa del mese: {spesa_del_mese(conn):.2f} $ su un tetto di "
          f"{float(os.environ.get('IA_TETTO_MESE_USD', TETTO_MESE_PREDEFINITO)):.2f} $")
    return 0


@con_blocco("ia_smistamento", 0)
def cmd_smista(conn, limite: int, batch: bool) -> int:
    client = nuovo_client()
    controlla_tetto(conn)
    annunci = annunci_da_smistare(conn, limite)
    print(f"Annunci da smistare con l'IA ({MODELLO_SMISTAMENTO}): {len(annunci)} ({len(lotti(annunci))} lotti)")
    oggi = date.today()
    aggiungi_inizio_pagina(annunci)
    if batch:
        if not annunci:
            return 0
        richieste, gruppi = [], []
        for n, lotto in enumerate(lotti(annunci)):
            istruzioni, messaggio = messaggio_smistamento(lotto, oggi)
            richieste.append({"custom_id": f"smista-{n}",
                              "params": parametri(MODELLO_SMISTAMENTO, istruzioni, messaggio, SCHEMA_SMISTAMENTO,
                                                  max_token_smistamento(len(lotto)), EFFORT["smistamento"])})
            gruppi.append(f"smista-{n}:" + ",".join(str(a["id"]) for a in lotto))
        lotto_batch = client.messages.batches.create(requests=richieste)
        registra = registratore(conn, True, lotto_batch.id)
        for g in gruppi:   # gli id di ogni richiesta restano qui: custom_id ha un limite di lunghezza
            registra("smistamento", MODELLO_SMISTAMENTO, g, Risposta(None, "inviata"))
        print(f"Inviato alla Batch API: {lotto_batch.id}. Risultati con: python -m app.schede.ia raccogli")
        return 0
    registra = registratore(conn)
    for lotto in lotti(annunci):
        controlla_tetto(conn)
        esito = smista_lotto(client, lotto, oggi, registra)
        salva_smistamento(conn, esito.decisi, 0.0)
        print(f"lotto di {len(lotto)}: {sum(1 for e, _ in esito.decisi.values() if e == 'rilevante')} rilevanti, "
              f"{len(esito.mancanti)} senza risposta, {len(esito.estranei)} risposte scartate", flush=True)
    return 0


def scopi_in_volo(conn) -> set[str]:
    """Quali tipi di richiesta hanno un lotto ancora in attesa nella Batch API."""
    with conn.cursor() as cur:
        cur.execute("SELECT DISTINCT scopo FROM chiamate_ia WHERE batch AND esito = 'inviata'")
        return {r["scopo"] for r in cur.fetchall()}


def _in_volo(conn) -> dict[str, list[int]]:
    """Richieste inviate alla Batch API e non ancora raccolte, per lotto: {batch_id: [id delle righe]}."""
    with conn.cursor() as cur:
        cur.execute("SELECT id, batch_id FROM chiamate_ia WHERE batch AND esito = 'inviata'")
        righe = cur.fetchall()
    volo: dict[str, list[int]] = {}
    for r in righe:
        volo.setdefault(r["batch_id"], []).append(r["id"])
    return volo


@con_blocco("ia_raccogli", 0)
def cmd_raccogli(conn) -> int:
    """Legge i lotti inviati alla Batch API e salva le risposte, con gli stessi controlli della chiamata diretta.
    Tre tipi di richiesta, dal custom_id: smista-N (lotto di annunci), pre-ID e pre2-ID (controllo preliminare e
    seconda lettura del bando ID), sch-ID (scheda). Gli annunci senza risposta restano "da_rivedere"."""
    from app.schede.segnali import segnali_del_bando

    client = nuovo_client()
    with conn.cursor() as cur:
        cur.execute("SELECT id, batch_id, riferimento FROM chiamate_ia WHERE batch AND esito = 'inviata'")
        inviati = list(cur.fetchall())
    per_lotto: dict[str, dict[str, tuple[int, list[int]]]] = {}
    for riga in inviati:
        custom_id, _, ids = riga["riferimento"].partition(":")
        per_lotto.setdefault(riga["batch_id"], {})[custom_id] = (riga["id"], [int(x) for x in ids.split(",") if x])
    oggi = date.today()
    for batch_id, richieste in per_lotto.items():
        if client.messages.batches.retrieve(batch_id).processing_status != "ended":
            print(f"{batch_id}: ancora in lavorazione")
            continue
        registra = registratore(conn, True, batch_id)
        for risultato in client.messages.batches.results(batch_id):
            cid = risultato.custom_id
            riga_id, ids = richieste.get(cid, (None, []))
            if risultato.result.type != "succeeded":
                print(f"{cid}: {risultato.result.type} (si riprova a mano)")
                registra(_scopo(cid), MODELLO_SMISTAMENTO, cid, Risposta(None, "errore", messaggio=risultato.result.type))
            else:
                r = leggi_messaggio(risultato.result.message)
                if cid.startswith("smista-"):
                    registra("smistamento", MODELLO_SMISTAMENTO, f"{cid}:" + ",".join(map(str, ids)), r)
                    controllo = controlla_smistamento(ids, r.dati)
                    salva_smistamento(conn, controllo.decisi, 0.0)
                    print(f"{cid}: {len(controllo.decisi)} decisi, {len(controllo.mancanti)} senza risposta")
                elif cid.startswith(("pre-", "pre2-")):
                    registra("preliminare", MODELLO_PRELIMINARE, cid, r)
                    if r.dati is not None:
                        salva_preliminare_batch(conn, int(cid.split("-")[1]), r.dati, cid.startswith("pre2-"),
                                                segnali_del_bando, oggi)
                elif cid.startswith("sch-"):
                    registra("scheda", MODELLO_SCHEDA, cid, r)
                    bando_id = int(cid.split("-")[1])
                    if r.dati is not None:
                        documenti, _ = documenti_del_bando(conn, bando_id, MASSIMO_TESTO_SCHEDA)
                        scheda, tolti = prepara_scheda(r.dati)
                        salva_scheda(conn, bando_id, scheda, tolti + verifica_scheda(scheda, documenti),
                                     r.costo(MODELLO_SCHEDA, batch=True))
                        print(f"{cid}: scheda salvata")
            if riga_id:
                with conn.cursor() as cur:
                    cur.execute("UPDATE chiamate_ia SET esito = 'raccolta' WHERE id = %s", (riga_id,))
                conn.commit()
    return 0


def _scopo(custom_id: str) -> str:
    return "smistamento" if custom_id.startswith("smista-") else "scheda" if custom_id.startswith("sch-") else "preliminare"


def salva_preliminare_batch(conn, bando_id: int, dati: dict, seconda: bool, segnali_del_bando, oggi: date) -> None:
    """Il preliminare arrivato dalla Batch API. Se dice chiuso ma la fonte dice aperto, si chiede la seconda
    lettura al giro dopo (seconda_lettura: da_fare) e intanto la scheda aspetta."""
    if seconda:
        with conn.cursor() as cur:
            cur.execute("SELECT preliminare FROM bandi WHERE id = %s", (bando_id,))
            prima = (cur.fetchone() or {}).get("preliminare") or {}
        dati["prima_lettura"] = {"stato": prima.get("stato"), "motivo": prima.get("motivo")}
    elif dati.get("stato") == "chiuso" and segnali_del_bando(conn, bando_id, oggi).aperto:
        dati["seconda_lettura"] = "da_fare"
    with conn.cursor() as cur:
        cur.execute("UPDATE bandi SET preliminare = %s WHERE id = %s AND dati IS NULL", (json.dumps(firma(dati, "ia")), bando_id))
    conn.commit()


def firma(preliminare: dict, da: str) -> dict:
    """Chi ha deciso il controllo preliminare e quando: la situazione del bando (vista bandi_situazione) li mostra."""
    return {**preliminare, "deciso_da": preliminare.get("deciso_da") or da,
            "deciso_il": datetime.now(timezone.utc).isoformat(timespec="seconds")}


def preliminare_dai_segnali(s) -> dict | None:
    """Controllo preliminare senza IA: se i segnali gratuiti (app/schede/segnali.py) dicono solo "chiuso" (scadenza
    passata nei dati della fonte, "Bando Chiuso" nella pagina, data barrata...) il bando si ferma qui, senza spesa."""
    if s.stato != "chiuso":
        return None
    return {"per_imprese": "incerto", "edizione_in_corso": "incerto", "stato": "chiuso", "testo_bando": "si",
            "motivo": ("segnali gratuiti, senza IA: " + "; ".join(s.chiuso))[:500], "deciso_da": "segnali",
            "deciso_il": datetime.now(timezone.utc).isoformat(timespec="seconds")}


def seconda_lettura(segnali) -> str:
    """Il testo aggiunto al messaggio del controllo preliminare quando si rilegge un bando dato per chiuso."""
    return ("\n\n# Seconda lettura\n\nUna prima lettura di questi documenti ha concluso che il bando e' chiuso, ma i dati "
            "raccolti dalla fonte dicono altro: " + "; ".join(segnali.aperto) + ". Rileggi con attenzione le date di "
            "apertura e chiusura, le proroghe e gli avvisi di chiusura anticipata. Rispondi 'chiuso' solo se il testo "
            "dice chiaramente che le domande non si possono piu' presentare; altrimenti 'aperto', 'in_arrivo' o "
            "'non_noto', e spiega nel motivo quale data hai trovato.")


@dataclass
class Prompt:
    istr_pre: str
    mod_pre: str
    istr_scheda: str
    mod_scheda: str
    oggi: date

    @classmethod
    def carica(cls, oggi: date) -> "Prompt":
        istr_pre, mod_pre = leggi_prompt("prompt_preliminare.md")
        istr_scheda, mod_scheda = leggi_prompt("prompt_scheda.md")
        return cls(riempi(istr_pre, {"data_oggi": oggi.isoformat()}), mod_pre, istr_scheda, mod_scheda, oggi)

    def preliminare(self, conn, b: dict) -> str:
        corti = documenti_preliminare(conn, b["id"])
        return riempi(self.mod_pre, {"data_oggi": self.oggi.isoformat(), "titolo": b["titolo"], "url": b["url"],
                                     "documenti": corti})

    def scheda(self, conn, b: dict) -> tuple[str, list[dict]]:
        documenti, avvertenze = documenti_del_bando(conn, b["id"], MASSIMO_TESTO_SCHEDA)
        with conn.cursor() as cur:
            cur.execute("SELECT id, titolo FROM annunci WHERE bando_id = %s", (b["id"],))
            collegati = "; ".join(f"{x['id']} {x['titolo'][:80]}" for x in cur.fetchall())
        return riempi(self.mod_scheda, {
            "data_oggi": self.oggi.isoformat(), "titolo": b["titolo"], "ente": b["ente"], "territorio": b["territorio"],
            "url": b["url"], "pagina_motivo": b.get("pagina_motivo"), "annunci": collegati,
            "avvertenze_documenti": "\n".join(f"- {a}" for a in avvertenze) or "- nessuna", "documenti": documenti}), documenti


def ferma_con_segnali(conn, b: dict, segnali) -> bool:
    gratuito = preliminare_dai_segnali(segnali)
    if not gratuito:
        return False
    with conn.cursor() as cur:
        cur.execute("UPDATE bandi SET preliminare = %s WHERE id = %s", (json.dumps(gratuito), b["id"]))
    conn.commit()
    print(f"[{b['id']}] niente scheda, fermato senza IA: {gratuito['motivo']}", flush=True)
    return True


def cmd_schede(conn, bando_id: int | None, limite: int) -> int:
    client = None     # si apre solo quando serve: i bandi fermati dai segnali gratuiti non chiamano l'API
    registra = registratore(conn)
    pr = Prompt.carica(date.today())
    from app.schede.segnali import segnali_del_bando

    for b in bandi_da_schedare(conn, bando_id, limite):
        segnali = segnali_del_bando(conn, b["id"], pr.oggi)
        if ferma_con_segnali(conn, b, segnali):
            continue
        client = client or nuovo_client()
        controlla_tetto(conn)
        pre = preliminare_diretto(conn, client, pr, b, segnali, registra)
        if pre is None:
            continue
        ok, perche = passa_preliminare(pre)
        if not ok:
            print(f"[{b['id']}] niente scheda: {perche} ({pre.get('motivo')})")
            continue
        messaggio, documenti = pr.scheda(conn, b)
        r = chiama(client, parametri(MODELLO_SCHEDA, pr.istr_scheda, messaggio, None, 64000, EFFORT["scheda"]))
        registra("scheda", MODELLO_SCHEDA, str(b["id"]), r)
        if r.dati is None:
            print(f"[{b['id']}] scheda non riuscita: {r.messaggio}")
            continue
        scheda, tolti = prepara_scheda(r.dati)
        problemi = tolti + verifica_scheda(scheda, documenti)
        salva_scheda(conn, b["id"], scheda, problemi, r.costo(MODELLO_SCHEDA))
        print(f"[{b['id']}] scheda salvata{'' if not problemi else f', {len(problemi)} problemi da controllare'}", flush=True)
    return 0


def preliminare_diretto(conn, client, pr, b: dict, segnali, registra) -> dict | None:
    """Controllo preliminare con una chiamata diretta (con la seconda lettura se l'IA dice chiuso ma la fonte scrive
    una scadenza futura). Salva e rende la risposta, o None se non e' riuscito."""
    messaggio_pre = pr.preliminare(conn, b)
    r = chiama(client, parametri(MODELLO_PRELIMINARE, pr.istr_pre, messaggio_pre, SCHEMA_PRELIMINARE, 8000,
                                 EFFORT["preliminare"]))
    registra("preliminare", MODELLO_PRELIMINARE, str(b["id"]), r)
    if r.dati is None:
        print(f"[{b['id']}] controllo preliminare non riuscito: {r.messaggio}")
        return None
    if r.dati.get("stato") == "chiuso" and segnali.aperto:
        # Seconda lettura: l'IA dice chiuso ma la fonte scrive una scadenza futura (o "aperto"). Nella prova
        # del 26/09 cosi' si erano fermati bandi aperti (MATCHIN, intelligenza artificiale nelle PMI).
        seconda = chiama(client, parametri(MODELLO_PRELIMINARE, pr.istr_pre, messaggio_pre + seconda_lettura(segnali),
                                           SCHEMA_PRELIMINARE, 16000, EFFORT["seconda_lettura"]))
        registra("preliminare", MODELLO_PRELIMINARE, f"{b['id']} seconda lettura", seconda)
        if seconda.dati is not None:
            seconda.dati["prima_lettura"] = {"stato": r.dati.get("stato"), "motivo": r.dati.get("motivo")}
            r = seconda
    with conn.cursor() as cur:
        cur.execute("UPDATE bandi SET preliminare = %s WHERE id = %s", (json.dumps(firma(r.dati, "ia")), b["id"]))
    conn.commit()
    return r.dati


PRELIMINARI_DIRETTI_PER_GIRO = 40   # circa 0,5 $: cosi' la scheda parte nello stesso giro, senza aspettare un lotto


@con_blocco("ia_preliminari", 0)
def cmd_preliminari_diretti(conn, limite: int = PRELIMINARI_DIRETTI_PER_GIRO) -> int:
    """Controlli preliminari dei bandi nuovi con il testo ufficiale, con chiamate dirette (02/10/2026: con la Batch API
    un bando aspettava circa 13 ore per il preliminare e altrettante per la scheda). Rende quanti ne ha fatti."""
    from app.schede.segnali import segnali_del_bando

    pr = Prompt.carica(date.today())
    registra = registratore(conn)
    client = None
    with conn.cursor() as cur:
        cur.execute("""SELECT * FROM bandi WHERE pagina_stato = 'trovata' AND allegati_cercati_il IS NOT NULL
                       AND documentazione = 'bando' AND dati IS NULL AND preliminare IS NULL ORDER BY id DESC LIMIT %s""",
                    (limite,))
        bandi = [dict(r) for r in cur.fetchall()]
    fatti = 0
    for b in bandi:
        segnali = segnali_del_bando(conn, b["id"], pr.oggi)
        if ferma_con_segnali(conn, b, segnali):
            continue
        client = client or nuovo_client()
        controlla_tetto(conn)
        if preliminare_diretto(conn, client, pr, b, segnali, registra) is not None:
            fatti += 1
    return fatti


LIMITE_PRELIMINARI_BATCH = 150    # per giro: il costo di un lotto resta prevedibile (circa 2 $ in batch)
LIMITE_SCHEDE_BATCH = 40          # circa 4-5 $ in batch


@con_blocco("ia_schede", 0)
def cmd_schede_batch(conn, limite_pre: int = LIMITE_PRELIMINARI_BATCH, limite_schede: int = LIMITE_SCHEDE_BATCH) -> int:
    """Controlli preliminari, seconde letture e schede con la Batch API (meta' prezzo, risposte entro 24 ore).
    Ogni bando si manda una volta sola per tipo di richiesta: se la risposta non va, si riprova a mano
    (python -m app.schede.ia schede --bando ID). I bandi con soli segnali di chiusura si fermano gratis."""
    from app.schede.segnali import segnali_del_bando

    client = nuovo_client()
    controlla_tetto(conn)
    pr = Prompt.carica(date.today())
    with conn.cursor() as cur:
        # Non si rimanda una richiesta ancora in volo; una risposta fallita (errore, scaduta, tagliata) si riprova
        # una volta (02/10: prima restava per sempre "in attesa"). Quelle riuscite non tornano qui: il bando ha gia'
        # preliminare o scheda.
        cur.execute("""SELECT riferimento FROM chiamate_ia WHERE scopo IN ('preliminare', 'scheda') AND batch
                       GROUP BY riferimento
                       HAVING bool_or(esito = 'inviata') OR count(*) FILTER (WHERE esito IN ('inviata', 'raccolta')) >= 2""")
        gia = {r["riferimento"] for r in cur.fetchall()}
        cur.execute("""SELECT * FROM bandi WHERE pagina_stato = 'trovata' AND allegati_cercati_il IS NOT NULL
                       AND documentazione = 'bando' AND unito_a IS NULL
                       AND ((dati IS NULL AND (preliminare IS NULL OR preliminare->>'seconda_lettura' = 'da_fare'
                             OR preliminare->>'deciso_da' IS DISTINCT FROM 'segnali'))
                            OR (dati IS NOT NULL AND da_aggiornare IS NOT NULL))
                       ORDER BY id""")
        bandi = [dict(r) for r in cur.fetchall()]
    richieste: list[dict] = []
    n_pre = n_sch = 0
    for b in bandi:
        pre = b["preliminare"]
        if b["dati"] is not None:
            # Scheda da aggiornare (regista: documenti nuovi, proroga, rettifica, chiusura). Una richiesta per versione.
            cid = f"sch-{b['id']}-v{b['versione']}"
            if cid not in gia and n_sch < limite_schede:
                messaggio, _ = pr.scheda(conn, b)
                richieste.append({"custom_id": cid, "params": parametri(
                    MODELLO_SCHEDA, pr.istr_scheda, messaggio, None, 64000, EFFORT["scheda"])})
                n_sch += 1
            continue
        if pre is None and n_pre < limite_pre and f"pre-{b['id']}" not in gia:
            segnali = segnali_del_bando(conn, b["id"], pr.oggi)
            if ferma_con_segnali(conn, b, segnali):
                continue
            richieste.append({"custom_id": f"pre-{b['id']}", "params": parametri(
                MODELLO_PRELIMINARE, pr.istr_pre, pr.preliminare(conn, b), SCHEMA_PRELIMINARE, 8000, EFFORT["preliminare"])})
            n_pre += 1
        elif pre and pre.get("seconda_lettura") == "da_fare" and f"pre2-{b['id']}" not in gia and n_pre < limite_pre:
            segnali = segnali_del_bando(conn, b["id"], pr.oggi)
            richieste.append({"custom_id": f"pre2-{b['id']}", "params": parametri(
                MODELLO_PRELIMINARE, pr.istr_pre, pr.preliminare(conn, b) + seconda_lettura(segnali), SCHEMA_PRELIMINARE,
                16000, EFFORT["seconda_lettura"])})
            n_pre += 1
        elif pre and passa_preliminare(pre)[0] and not pre.get("seconda_lettura") == "da_fare" \
                and f"sch-{b['id']}" not in gia and n_sch < limite_schede:
            messaggio, _ = pr.scheda(conn, b)
            richieste.append({"custom_id": f"sch-{b['id']}", "params": parametri(
                MODELLO_SCHEDA, pr.istr_scheda, messaggio, None, 64000, EFFORT["scheda"])})
            n_sch += 1
    if not richieste:
        print("Batch: nessun bando da mandare.")
        return 0
    lotto = client.messages.batches.create(requests=richieste)
    registra = registratore(conn, True, lotto.id)
    for r in richieste:
        registra(_scopo(r["custom_id"]), r["params"]["model"], r["custom_id"], Risposta(None, "inviata"))
    print(f"Batch {lotto.id}: {n_pre} controlli preliminari, {n_sch} schede. Risposte entro 24 ore (ia raccogli).")
    return 0


def ciclo_catena() -> None:
    """Il lavoro sui bandi nel giro orario della raccolta (app/raccolta/demone.py): smistamento a regole, deduplica,
    pagina ufficiale e allegati a piccoli lotti; poi, se c'e' la chiave, l'IA con la Batch API: raccoglie le risposte
    arrivate e manda i nuovi lotti (smistamento dei "da rivedere", controlli preliminari, schede)."""
    # Dal 01/10 la sequenza la decide il regista (app/catena/regista.py): passi, riprove, sblocchi e aggiornamenti.
    from app.catena import regista

    regista.giro()


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="IA nelle schede (spenta senza ANTHROPIC_API_KEY).")
    parser.add_argument("comando", choices=["stato", "smista", "schede", "raccogli", "ciclo"])
    parser.add_argument("--limite", type=int, default=100, metavar="N")
    parser.add_argument("--bando", type=int, metavar="ID")
    parser.add_argument("--batch", action="store_true", help="usa la Batch API (meta' prezzo, risposta entro 24 ore)")
    args = parser.parse_args(argv)
    from app.db.connessione import connetti
    from app.db.migrazioni import applica_migrazioni

    with connetti() as conn:
        applica_migrazioni(conn)
        try:
            if args.comando == "stato":
                return cmd_stato(conn)
            if args.comando == "smista":
                return cmd_smista(conn, args.limite, args.batch)
            if args.comando == "raccogli":
                return cmd_raccogli(conn)
            if args.comando == "ciclo":
                ciclo_catena()
                return 0
            if args.batch and not args.bando:
                return cmd_schede_batch(conn, args.limite, min(args.limite, LIMITE_SCHEDE_BATCH))
            return cmd_schede(conn, args.bando, args.limite)
        except IASpenta as exc:
            print(exc)
            return 0


if __name__ == "__main__":
    sys.exit(main())
