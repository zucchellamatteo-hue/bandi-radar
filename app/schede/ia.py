"""L'IA nelle schede: smistamento con Haiku, controllo preliminare con Haiku, scheda con Sonnet. SPENTO senza chiave.

Finche' nell'ambiente manca ANTHROPIC_API_KEY (la chiave API con il tetto di spesa, mai quella dell'abbonamento)
nessuna funzione di questo modulo chiama l'API: i comandi lo dicono e si fermano. Le protezioni chieste dalla
prova del 25/09/2026 (docs/ricerche/2026-09-25_prova_ia.md) sono gia' qui:

  - smistamento a lotti di 20 annunci; si controlla che tornino tutti gli id e si rimandano i mancanti una volta;
    chi manca ancora resta "da_rivedere" con il motivo "l'IA non ha risposto";
  - risposte in JSON vincolato da uno schema (output_config.format), poi verificate anche dal programma
    (valori ammessi, date, importi, fonti; per le schede verifica_scheda);
  - Batch API (meta' prezzo, risposta entro 24 ore) per tutto quello che non e' urgente, con --batch;
  - controllo preliminare con Haiku prima di Sonnet: e' per imprese? e' l'edizione in corso? e' aperto?
    c'e' il testo del bando? Solo se passa si chiede la scheda;
  - un tetto di spesa mensile anche nel programma (IA_TETTO_MESE_USD, di base 30 $), oltre a quello della Console;
  - le decisioni di Matteo non si sovrascrivono mai.

Uso (quando la chiave ci sara'):
  python -m app.schede.ia stato                        # IA accesa o spenta, spesa del mese
  python -m app.schede.ia smista --limite 100          # gli annunci "da_rivedere" delle regole
  python -m app.schede.ia schede --limite 10           # controllo preliminare e scheda dei bandi pronti
  python -m app.schede.ia schede --bando 45
  python -m app.schede.ia smista --batch               # invia un lotto alla Batch API e si ferma
  python -m app.schede.ia raccogli                     # legge i risultati dei lotti inviati
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from dataclasses import dataclass, field
from datetime import date
from pathlib import Path

from app.schede import campi

CARTELLA = Path(__file__).resolve().parent
MODELLO_SMISTAMENTO = "claude-haiku-4-5"
MODELLO_PRELIMINARE = "claude-haiku-4-5"
MODELLO_SCHEDA = "claude-sonnet-5"
DIMENSIONE_LOTTO = 20            # la prova del 25/09 ha perso 2 annunci su lotti da 45
MASSIMO_TESTO_SCHEDA = 150_000   # caratteri di documenti per Sonnet (circa 40.000 token)
MASSIMO_TESTO_PRELIMINARE = 18_000   # circa 3.000 parole
# Prezzi in dollari per milione di token (ingresso, uscita); con la Batch API la meta'.
PREZZI = {"claude-haiku-4-5": (1.0, 5.0), "claude-sonnet-5": (2.0, 10.0)}
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
    "linee": {"type": "array", "items": _LINEA},
    "vincoli": {"type": "object", "properties": {v: {"type": "string", "enum": list(campi.STATI_VINCOLO)} for v in campi.VINCOLI},
                "required": list(campi.VINCOLI), "additionalProperties": False},
    "completezza": {"type": "string", "enum": list(campi.COMPLETEZZA)},
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


def lotti(elementi: list, dimensione: int = DIMENSIONE_LOTTO) -> list[list]:
    return [elementi[i:i + dimensione] for i in range(0, len(elementi), dimensione)]


def passa_preliminare(p: dict) -> tuple[bool, str]:
    """Si chiede la scheda a Sonnet solo se il controllo preliminare non ha trovato un motivo per fermarsi."""
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
_SENZA_FONTE = {"titolo", "url", "vincoli", "completezza", "fonti", "avvertenze", "linee"}


def _data(testo) -> date | None:
    if isinstance(testo, str) and _DATA.match(testo):
        try:
            return date.fromisoformat(testo)
        except ValueError:
            return None
    return None


def verifica_scheda(s: dict, documenti: list[dict] | None = None) -> list[str]:
    """Controlli automatici su una scheda di Sonnet. Ogni problema e' una frase; nessun problema = lista vuota.
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
    fp, cm = s.get("fondo_perduto_massimo"), s.get("contributo_massimo")
    if isinstance(fp, (int, float)) and isinstance(cm, (int, float)) and fp > cm:
        problemi.append("fondo perduto massimo superiore al contributo massimo")
    if s.get("tipo_agevolazione") == "misto" and s.get("percentuale") == 100 and s.get("finanziamento_massimo"):
        problemi.append("agevolazione mista al 100%: la percentuale deve riguardare solo il fondo perduto")
    vincoli = s.get("vincoli") or {}
    for v, elenchi in _ELENCHI_DEL_VINCOLO.items():
        stato = vincoli.get(v)
        if stato not in campi.STATI_VINCOLO:
            problemi.append(f"vincoli.{v}: stato mancante o non ammesso")
        elif stato == "vincolo" and not any(s.get(e) not in (None, []) for e in elenchi):
            if not (v == "territorio" and s.get("territorio")):
                problemi.append(f"vincoli.{v} = vincolo, ma i campi {', '.join(elenchi)} sono vuoti")
    fonti = {f.get("campo") for f in s.get("fonti") or [] if isinstance(f, dict)}
    senza = [n for n, v in s.items() if n not in _SENZA_FONTE and v not in (None, [], "") and n not in fonti]
    if senza:
        problemi.append("campi senza fonte: " + ", ".join(sorted(senza)))
    if documenti is not None and s.get("completezza") == "bando_ufficiale":
        if not any((d.get("categoria") in ("bando", "decreto")) and len(d.get("testo") or "") > 2000 for d in documenti):
            problemi.append("completezza 'bando_ufficiale' ma tra i documenti non c'e' il testo di un bando o di un decreto")
    return problemi


# --- chiamate ---------------------------------------------------------------------------------------

def costo(modello: str, token_in: int, token_out: int, batch: bool = False) -> float:
    ingresso, uscita = PREZZI.get(modello, (0.0, 0.0))
    c = (token_in * ingresso + token_out * uscita) / 1_000_000
    return c / 2 if batch else c


def parametri(modello: str, istruzioni: str, messaggio: str, schema: dict, max_tokens: int) -> dict:
    """I parametri di una richiesta, uguali per la chiamata diretta e per la Batch API. Istruzioni in cache."""
    return {
        "model": modello,
        "max_tokens": max_tokens,
        "system": [{"type": "text", "text": istruzioni, "cache_control": {"type": "ephemeral"}}],
        "messages": [{"role": "user", "content": messaggio}],
        "output_config": {"format": {"type": "json_schema", "schema": schema}},
    }


@dataclass
class Risposta:
    dati: dict | None
    esito: str                 # ok | incompleta | rifiutata | errore
    token_in: int = 0
    token_out: int = 0
    messaggio: str = ""


def leggi_messaggio(msg) -> Risposta:
    """Da un messaggio dell'API (diretto o da Batch) al JSON, con i casi di errore."""
    uso = getattr(msg, "usage", None)
    token_in = (getattr(uso, "input_tokens", 0) or 0) + (getattr(uso, "cache_read_input_tokens", 0) or 0) \
        + (getattr(uso, "cache_creation_input_tokens", 0) or 0)
    token_out = getattr(uso, "output_tokens", 0) or 0
    if msg.stop_reason == "refusal":
        return Risposta(None, "rifiutata", token_in, token_out, "il modello ha rifiutato la richiesta")
    if msg.stop_reason == "max_tokens":
        return Risposta(None, "incompleta", token_in, token_out, "risposta tagliata (max_tokens)")
    testo = next((b.text for b in msg.content if getattr(b, "type", "") == "text"), "")
    try:
        return Risposta(json.loads(testo), "ok", token_in, token_out)
    except json.JSONDecodeError as exc:
        return Risposta(None, "errore", token_in, token_out, f"JSON non valido: {exc}")


def chiama(client, p: dict) -> Risposta:
    import anthropic

    try:
        return leggi_messaggio(client.messages.create(**p))
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
                                     max_tokens=200 + 120 * len(da_mandare)))
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


def controlla_tetto(conn) -> None:
    tetto = float(os.environ.get("IA_TETTO_MESE_USD", TETTO_MESE_PREDEFINITO))
    speso = spesa_del_mese(conn)
    if speso >= tetto:
        raise IASpenta(f"tetto di spesa del mese raggiunto: {speso:.2f} $ su {tetto:.2f} $ (IA_TETTO_MESE_USD)")


def registratore(conn, batch: bool = False, batch_id: str | None = None):
    def registra(scopo: str, modello: str, riferimento: str, r: Risposta) -> None:
        with conn.cursor() as cur:
            cur.execute(
                """INSERT INTO chiamate_ia (scopo, modello, batch, batch_id, riferimento, token_in, token_out, costo_usd, esito, messaggio)
                   VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)""",
                (scopo, modello, batch, batch_id, riferimento[:2000], r.token_in, r.token_out,
                 costo(modello, r.token_in, r.token_out, batch), r.esito, r.messaggio[:500]),
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


def documenti_del_bando(conn, bando_id: int, massimo: int) -> tuple[list[dict], list[str]]:
    from app.schede.allegati import documenti_per_scheda

    with conn.cursor() as cur:
        cur.execute("""SELECT nome, url, tipo, categoria, testo_estratto, errore FROM allegati
                       WHERE bando_id = %s AND annuncio_id IS NULL""", (bando_id,))
        return documenti_per_scheda([dict(r) for r in cur.fetchall()], massimo)


def bandi_da_schedare(conn, bando_id: int | None, limite: int) -> list[dict]:
    with conn.cursor() as cur:
        if bando_id:
            cur.execute("SELECT * FROM bandi WHERE id = %s", (bando_id,))
        else:
            cur.execute(
                """SELECT * FROM bandi WHERE pagina_stato = 'trovata' AND allegati_cercati_il IS NOT NULL
                   AND dati IS NULL AND preliminare IS NULL ORDER BY id LIMIT %s""", (limite,))
        return [dict(r) for r in cur.fetchall()]


_COLONNE_SCHEDA = [c for c in _CAMPI_SCHEDA if c not in ("fonti", "avvertenze", "url")]


def salva_scheda(conn, bando_id: int, scheda: dict, problemi: list[str], costo_usd: float) -> None:
    """Scrive i campi nella tabella bandi (lo stato no: lo calcola il sistema) e la risposta intera in `dati`."""
    valori = {c: scheda.get(c) for c in _COLONNE_SCHEDA}
    for c in ("vincoli", "linee"):
        valori[c] = json.dumps(valori[c]) if valori[c] is not None else None
    dati = {"risposta": scheda, "problemi": problemi, "costo_usd": round(costo_usd, 4), "modello": MODELLO_SCHEDA,
            "fonti": {f["campo"]: f["fonte"] for f in scheda.get("fonti") or [] if isinstance(f, dict) and "campo" in f},
            "avvertenze": scheda.get("avvertenze") or []}
    assegnazioni = ", ".join(f"{c} = %s" for c in valori)
    with conn.cursor() as cur:
        cur.execute("SELECT set_config('bandi_radar.causa', 'scheda compilata da Sonnet', true)")
        cur.execute(f"UPDATE bandi SET {assegnazioni}, dati = %s WHERE id = %s",
                    (*valori.values(), json.dumps(dati), bando_id))
    conn.commit()


# --- comandi ----------------------------------------------------------------------------------------

def cmd_stato(conn) -> int:
    print("IA:", "ACCESA (chiave presente)" if chiave_presente() else "SPENTA (manca ANTHROPIC_API_KEY)")
    print(f"Spesa del mese: {spesa_del_mese(conn):.2f} $ su un tetto di "
          f"{float(os.environ.get('IA_TETTO_MESE_USD', TETTO_MESE_PREDEFINITO)):.2f} $")
    return 0


def cmd_smista(conn, limite: int, batch: bool) -> int:
    client = nuovo_client()
    controlla_tetto(conn)
    annunci = annunci_da_smistare(conn, limite)
    print(f"Annunci da smistare con Haiku: {len(annunci)} ({len(lotti(annunci))} lotti)")
    oggi = date.today()
    aggiungi_inizio_pagina(annunci)
    if batch:
        richieste, gruppi = [], []
        for n, lotto in enumerate(lotti(annunci)):
            istruzioni, messaggio = messaggio_smistamento(lotto, oggi)
            richieste.append({"custom_id": f"smista-{n}",
                              "params": parametri(MODELLO_SMISTAMENTO, istruzioni, messaggio, SCHEMA_SMISTAMENTO,
                                                  200 + 120 * len(lotto))})
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


def cmd_raccogli(conn) -> int:
    """Legge i lotti inviati alla Batch API e salva le risposte, con gli stessi controlli degli id.
    Gli annunci senza risposta restano "da_rivedere": un nuovo 'smista' li rimanda."""
    client = nuovo_client()
    with conn.cursor() as cur:
        cur.execute("SELECT id, batch_id, riferimento FROM chiamate_ia WHERE batch AND esito = 'inviata'")
        inviati = list(cur.fetchall())
    per_lotto: dict[str, dict[str, tuple[int, list[int]]]] = {}
    for riga in inviati:
        custom_id, _, ids = riga["riferimento"].partition(":")
        per_lotto.setdefault(riga["batch_id"], {})[custom_id] = (riga["id"], [int(x) for x in ids.split(",") if x])
    for batch_id, richieste in per_lotto.items():
        if client.messages.batches.retrieve(batch_id).processing_status != "ended":
            print(f"{batch_id}: ancora in lavorazione")
            continue
        registra = registratore(conn, True, batch_id)
        for risultato in client.messages.batches.results(batch_id):
            riga_id, ids = richieste.get(risultato.custom_id, (None, []))
            if risultato.result.type == "succeeded":
                r = leggi_messaggio(risultato.result.message)
                registra("smistamento", MODELLO_SMISTAMENTO, f"{risultato.custom_id}:" + ",".join(map(str, ids)), r)
                controllo = controlla_smistamento(ids, r.dati)
                salva_smistamento(conn, controllo.decisi, 0.0)
                print(f"{risultato.custom_id}: {len(controllo.decisi)} decisi, {len(controllo.mancanti)} senza risposta")
            else:
                print(f"{risultato.custom_id}: {risultato.result.type} (restano da rivedere)")
            if riga_id:
                with conn.cursor() as cur:
                    cur.execute("UPDATE chiamate_ia SET esito = 'raccolta' WHERE id = %s", (riga_id,))
                conn.commit()
    return 0


def cmd_schede(conn, bando_id: int | None, limite: int) -> int:
    client = nuovo_client()
    oggi = date.today()
    registra = registratore(conn)
    istr_pre, mod_pre = leggi_prompt("prompt_preliminare.md")
    istr_scheda, mod_scheda = leggi_prompt("prompt_scheda.md")
    for b in bandi_da_schedare(conn, bando_id, limite):
        controlla_tetto(conn)
        corti, _ = documenti_del_bando(conn, b["id"], MASSIMO_TESTO_PRELIMINARE)
        r = chiama(client, parametri(MODELLO_PRELIMINARE, istr_pre, riempi(mod_pre, {
            "data_oggi": oggi.isoformat(), "titolo": b["titolo"], "url": b["url"], "documenti": corti}),
            SCHEMA_PRELIMINARE, 1000))
        registra("preliminare", MODELLO_PRELIMINARE, str(b["id"]), r)
        if r.dati is None:
            print(f"[{b['id']}] controllo preliminare non riuscito: {r.messaggio}")
            continue
        with conn.cursor() as cur:
            cur.execute("UPDATE bandi SET preliminare = %s WHERE id = %s", (json.dumps(r.dati), b["id"]))
        conn.commit()
        ok, perche = passa_preliminare(r.dati)
        if not ok:
            print(f"[{b['id']}] niente scheda: {perche} ({r.dati.get('motivo')})")
            continue
        documenti, avvertenze = documenti_del_bando(conn, b["id"], MASSIMO_TESTO_SCHEDA)
        with conn.cursor() as cur:
            cur.execute("SELECT id, titolo FROM annunci WHERE bando_id = %s", (b["id"],))
            collegati = "; ".join(f"{x['id']} {x['titolo'][:80]}" for x in cur.fetchall())
        messaggio = riempi(mod_scheda, {
            "data_oggi": oggi.isoformat(), "titolo": b["titolo"], "ente": b["ente"], "territorio": b["territorio"],
            "url": b["url"], "pagina_motivo": b.get("pagina_motivo"), "annunci": collegati,
            "avvertenze_documenti": "\n".join(f"- {a}" for a in avvertenze) or "- nessuna", "documenti": documenti})
        r = chiama(client, parametri(MODELLO_SCHEDA, istr_scheda, messaggio, SCHEMA_SCHEDA, 16000))
        registra("scheda", MODELLO_SCHEDA, str(b["id"]), r)
        if r.dati is None:
            print(f"[{b['id']}] scheda non riuscita: {r.messaggio}")
            continue
        problemi = verifica_scheda(r.dati, documenti)
        salva_scheda(conn, b["id"], r.dati, problemi, costo(MODELLO_SCHEDA, r.token_in, r.token_out))
        print(f"[{b['id']}] scheda salvata{'' if not problemi else f', {len(problemi)} problemi da controllare'}", flush=True)
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="IA nelle schede (spenta senza ANTHROPIC_API_KEY).")
    parser.add_argument("comando", choices=["stato", "smista", "schede", "raccogli"])
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
            return cmd_schede(conn, args.bando, args.limite)
        except IASpenta as exc:
            print(exc)
            return 0


if __name__ == "__main__":
    sys.exit(main())
