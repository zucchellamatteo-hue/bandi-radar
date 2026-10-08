"""Fattura elettronica degli abbonamenti (05/10/2026, ricerche docs/ricerche/2026-10-05_fatturazione_*.md).

Flusso: Stripe incassa (evento invoice.paid) -> qui si crea la fattura numerata (sezionale "BR") con l'XML FatturaPA
1.2.2 generato da noi (cosi' si puo' cambiare fornitore toccando solo l'invio) -> Invoicetronic la manda allo SdI ->
le sue notifiche (webhook firmato) aggiornano lo stato: consegnata, scartata, non consegnata.

Spento finche' FATTURE_ATTIVE non e' 1. Con la chiave di prova (ik_test_) le fatture vanno nella sandbox; la chiave
vera (ik_live_) serve anche FATTURE_VERE=1: una fattura inviata allo SdI non si ritira, si storna con una nota di credito.
Chi emette (studio o societa') e i suoi dati: variabili FATTURE_EMITTENTE_* (decisione di Matteo).
"""

from __future__ import annotations

import json
import os
import re
from datetime import date, datetime, timezone
from decimal import ROUND_HALF_UP, Decimal
from xml.sax.saxutils import escape

import httpx

API = "https://api.invoicetronic.com/v1"
ALIQUOTA = Decimal("22.00")
SEZIONALE = "BR"
STATI_SDI = {"Inviato": "inviata", "Consegnato": "consegnata", "AccettatoDalDestinatario": "consegnata",
             "DecorrenzaTermini": "consegnata", "NonConsegnato": "non_consegnata", "ImpossibilitaDiRecapito": "non_consegnata",
             "AttestazioneTrasmissioneFattura": "non_consegnata", "Scartato": "scartata",
             "RifiutatoDalDestinatario": "scartata"}
_PIVA = re.compile(r"^\d{11}$")
_CF = re.compile(r"^([A-Z0-9]{16}|\d{11})$")
_CODICE_DESTINATARIO = re.compile(r"^[A-Z0-9]{7}$")
_CAP = re.compile(r"^\d{5}$")


class ErroreFattura(ValueError):
    pass


def attive() -> bool:
    return os.environ.get("FATTURE_ATTIVE", "0") == "1"


def soldi(x) -> Decimal:
    return Decimal(str(x)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


# --- dati di fatturazione del cliente ---

def controlla_dati(d: dict) -> dict:
    """Controlli di forma (non di esistenza) dei dati di fatturazione; ritorna i dati puliti."""
    pulito = {k: (str(d.get(k) or "").strip() or None) for k in
              ("denominazione", "partita_iva", "codice_fiscale", "codice_destinatario", "pec", "indirizzo", "cap", "comune",
               "provincia")}
    for k in ("partita_iva", "codice_fiscale", "codice_destinatario", "provincia"):
        if pulito[k]:
            pulito[k] = pulito[k].upper().replace(" ", "")
    if pulito["partita_iva"] and pulito["partita_iva"].startswith("IT"):
        pulito["partita_iva"] = pulito["partita_iva"][2:]
    errori = []
    if not pulito["denominazione"]:
        errori.append("ragione sociale")
    if not _PIVA.match(pulito["partita_iva"] or ""):
        errori.append("partita IVA (11 cifre)")
    if pulito["codice_fiscale"] and not _CF.match(pulito["codice_fiscale"]):
        errori.append("codice fiscale")
    if pulito["codice_destinatario"] and not _CODICE_DESTINATARIO.match(pulito["codice_destinatario"]):
        errori.append("codice destinatario (7 caratteri)")
    if not pulito["codice_destinatario"] and not (pulito["pec"] and "@" in pulito["pec"]):
        errori.append("codice destinatario oppure PEC")
    for k, nome in (("indirizzo", "indirizzo"), ("comune", "comune")):
        if not pulito[k]:
            errori.append(nome)
    if not _CAP.match(pulito["cap"] or ""):
        errori.append("CAP")
    if not re.match(r"^[A-Z]{2}$", pulito["provincia"] or ""):
        errori.append("provincia (sigla)")
    if errori:
        raise ErroreFattura("Controlla: " + ", ".join(errori) + ".")
    pulito["codice_destinatario"] = pulito["codice_destinatario"] or "0000000"
    return pulito


def salva_dati(conn, utente_id: int, d: dict) -> dict:
    p = controlla_dati(d)
    with conn.cursor() as cur:
        cur.execute("""INSERT INTO dati_fatturazione (utente_id, denominazione, partita_iva, codice_fiscale, codice_destinatario,
                         pec, indirizzo, cap, comune, provincia) VALUES (%(u)s, %(denominazione)s, %(partita_iva)s,
                         %(codice_fiscale)s, %(codice_destinatario)s, %(pec)s, %(indirizzo)s, %(cap)s, %(comune)s, %(provincia)s)
                       ON CONFLICT (utente_id) DO UPDATE SET denominazione = EXCLUDED.denominazione,
                         partita_iva = EXCLUDED.partita_iva, codice_fiscale = EXCLUDED.codice_fiscale,
                         codice_destinatario = EXCLUDED.codice_destinatario, pec = EXCLUDED.pec, indirizzo = EXCLUDED.indirizzo,
                         cap = EXCLUDED.cap, comune = EXCLUDED.comune, provincia = EXCLUDED.provincia, aggiornato_il = now()
                       RETURNING *""", p | {"u": utente_id})
        return dict(cur.fetchone())


def leggi_dati(conn, utente_id: int) -> dict | None:
    with conn.cursor() as cur:
        cur.execute("SELECT * FROM dati_fatturazione WHERE utente_id = %s", (utente_id,))
        r = cur.fetchone()
    return dict(r) if r else None


# --- XML FatturaPA ---

def emittente() -> dict:
    e = {k: os.environ.get(f"FATTURE_EMITTENTE_{k.upper()}", "").strip() for k in
         ("denominazione", "partita_iva", "codice_fiscale", "regime", "indirizzo", "cap", "comune", "provincia")}
    e["regime"] = e["regime"] or "RF01"
    mancano = [k for k in ("denominazione", "partita_iva", "indirizzo", "cap", "comune", "provincia") if not e[k]]
    if mancano:
        raise ErroreFattura(f"Mancano i dati di chi emette le fatture: FATTURE_EMITTENTE_{', FATTURE_EMITTENTE_'.join(m.upper() for m in mancano)}.")
    return e


def _t(nome: str, valore) -> str:
    return f"<{nome}>{escape(str(valore))}</{nome}>"


def _sede(d: dict) -> str:
    return ("<Sede>" + _t("Indirizzo", d["indirizzo"][:60]) + _t("CAP", d["cap"]) + _t("Comune", d["comune"][:60])
            + _t("Provincia", d["provincia"]) + _t("Nazione", "IT") + "</Sede>")


def genera_xml(numero: str, data_doc: date, cliente: dict, righe: list[dict], progressivo: str, em: dict | None = None) -> str:
    """FatturaPA 1.2.2 (FPR12), fattura ordinaria TD01 tra privati, IVA 22%, pagata con carta (MP08)."""
    em = em or emittente()
    linee, imponibile = [], Decimal("0")
    for i, r in enumerate(righe, start=1):
        quantita = soldi(r.get("quantita") or 1)
        prezzo = soldi(r["prezzo_unitario"])
        totale = soldi(quantita * prezzo)
        imponibile += totale
        linee.append("<DettaglioLinee>" + _t("NumeroLinea", i) + _t("Descrizione", r["descrizione"][:1000])
                     + _t("Quantita", quantita) + _t("PrezzoUnitario", prezzo) + _t("PrezzoTotale", totale)
                     + _t("AliquotaIVA", ALIQUOTA) + "</DettaglioLinee>")
    imposta = soldi(imponibile * ALIQUOTA / 100)
    totale_doc = imponibile + imposta
    pec = _t("PECDestinatario", cliente["pec"]) if cliente.get("codice_destinatario") == "0000000" and cliente.get("pec") else ""
    cf_em = _t("CodiceFiscale", em["codice_fiscale"]) if em.get("codice_fiscale") else ""
    cf_cl = _t("CodiceFiscale", cliente["codice_fiscale"]) if cliente.get("codice_fiscale") else ""
    return (
        '<?xml version="1.0" encoding="UTF-8"?>'
        '<p:FatturaElettronica versione="FPR12" xmlns:ds="http://www.w3.org/2000/09/xmldsig#" '
        'xmlns:p="http://ivaservizi.agenziaentrate.gov.it/docs/xsd/fatture/v1.2" '
        'xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">'
        "<FatturaElettronicaHeader>"
        "<DatiTrasmissione><IdTrasmittente>" + _t("IdPaese", "IT") + _t("IdCodice", em["partita_iva"]) + "</IdTrasmittente>"
        + _t("ProgressivoInvio", progressivo) + _t("FormatoTrasmissione", "FPR12")
        + _t("CodiceDestinatario", cliente["codice_destinatario"]) + pec + "</DatiTrasmissione>"
        "<CedentePrestatore><DatiAnagrafici><IdFiscaleIVA>" + _t("IdPaese", "IT") + _t("IdCodice", em["partita_iva"])
        + "</IdFiscaleIVA>" + cf_em + "<Anagrafica>" + _t("Denominazione", em["denominazione"][:80]) + "</Anagrafica>"
        + _t("RegimeFiscale", em["regime"]) + "</DatiAnagrafici>" + _sede(em) + "</CedentePrestatore>"
        "<CessionarioCommittente><DatiAnagrafici><IdFiscaleIVA>" + _t("IdPaese", "IT") + _t("IdCodice", cliente["partita_iva"])
        + "</IdFiscaleIVA>" + cf_cl + "<Anagrafica>" + _t("Denominazione", cliente["denominazione"][:80]) + "</Anagrafica>"
        "</DatiAnagrafici>" + _sede(cliente) + "</CessionarioCommittente>"
        "</FatturaElettronicaHeader>"
        "<FatturaElettronicaBody><DatiGenerali><DatiGeneraliDocumento>" + _t("TipoDocumento", "TD01") + _t("Divisa", "EUR")
        + _t("Data", data_doc.isoformat()) + _t("Numero", numero) + _t("ImportoTotaleDocumento", totale_doc)
        + _t("Causale", "Abbonamento bandinQiaro") + "</DatiGeneraliDocumento></DatiGenerali>"
        "<DatiBeniServizi>" + "".join(linee) + "<DatiRiepilogo>" + _t("AliquotaIVA", ALIQUOTA)
        + _t("ImponibileImporto", soldi(imponibile)) + _t("Imposta", imposta) + _t("EsigibilitaIVA", "I") + "</DatiRiepilogo>"
        "</DatiBeniServizi>"
        "<DatiPagamento>" + _t("CondizioniPagamento", "TP02") + "<DettaglioPagamento>" + _t("ModalitaPagamento", "MP08")
        + _t("ImportoPagamento", totale_doc) + "</DettaglioPagamento></DatiPagamento>"
        "</FatturaElettronicaBody></p:FatturaElettronica>")


def _progressivo(n: int) -> str:
    """ProgressivoInvio: al massimo 5 caratteri alfanumerici, diverso per ogni invio."""
    cifre, s = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ", ""
    while True:
        n, r = divmod(n, 36)
        s = cifre[r] + s
        if not n:
            return s.rjust(5, "0")[-5:]


# --- creazione dalla fattura di Stripe ---

def righe_da_stripe(fattura_stripe: dict) -> list[dict]:
    """Righe della fattura dalle righe di Stripe (importi in centesimi, IVA esclusa)."""
    righe = []
    for linea in (fattura_stripe.get("lines") or {}).get("data") or []:
        quantita = linea.get("quantity") or 1
        importo = Decimal(linea.get("amount") or 0) / 100
        if importo == 0:
            continue
        periodo = linea.get("period") or {}
        descrizione = linea.get("description") or "Abbonamento bandinQiaro"
        if periodo.get("start") and periodo.get("end"):
            dal = datetime.fromtimestamp(periodo["start"], timezone.utc).date()
            al = datetime.fromtimestamp(periodo["end"], timezone.utc).date()
            descrizione += f" (dal {dal:%d/%m/%Y} al {al:%d/%m/%Y})"
        righe.append({"descrizione": descrizione, "quantita": quantita, "prezzo_unitario": str(soldi(importo / quantita))})
    return righe


def crea_da_stripe(conn, utente_id: int, fattura_stripe: dict) -> int | None:
    """Fattura per un pagamento Stripe (una sola per pagamento). None se c'e' gia' o se l'importo e' zero."""
    with conn.cursor() as cur:
        cur.execute("SELECT id FROM fatture WHERE stripe_fattura = %s", (fattura_stripe["id"],))
        if cur.fetchone():
            return None
    righe = righe_da_stripe(fattura_stripe)
    if not righe:
        return None
    cliente = leggi_dati(conn, utente_id)
    if not cliente:
        raise ErroreFattura(f"L'utente {utente_id} non ha i dati di fatturazione.")
    oggi = date.today()
    with conn.cursor() as cur:
        cur.execute("SELECT pg_advisory_xact_lock(424243)")   # numerazione senza buchi ne' doppioni
        cur.execute("SELECT coalesce(max(numero), 0) + 1 AS n FROM fatture WHERE anno = %s", (oggi.year,))
        n = cur.fetchone()["n"]
        cur.execute("SELECT nextval(pg_get_serial_sequence('fatture', 'id')) AS id")
        fid = cur.fetchone()["id"]
        cliente_xml = {k: cliente[k] for k in ("denominazione", "partita_iva", "codice_fiscale", "codice_destinatario", "pec",
                                               "indirizzo", "cap", "comune", "provincia")}
        xml = genera_xml(f"{n}/{SEZIONALE}", oggi, cliente_xml, righe, _progressivo(fid))
        imponibile = sum((soldi(Decimal(r["prezzo_unitario"]) * Decimal(str(r["quantita"]))) for r in righe), Decimal("0"))
        iva = soldi(imponibile * ALIQUOTA / 100)
        cur.execute("""INSERT INTO fatture (id, anno, numero, utente_id, stripe_fattura, data, cliente, righe, imponibile, iva,
                         totale, xml) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)""",
                    (fid, oggi.year, n, utente_id, fattura_stripe["id"], oggi, json.dumps(cliente_xml), json.dumps(righe),
                     imponibile, iva, imponibile + iva, xml))
    return fid


# --- invio con Invoicetronic ---

def _chiave() -> str:
    chiave = os.environ.get("INVOICETRONIC_API_KEY", "")
    if not chiave:
        raise ErroreFattura("Invio delle fatture non configurato (INVOICETRONIC_API_KEY).")
    if not chiave.startswith("ik_test_") and os.environ.get("FATTURE_VERE") != "1":
        raise ErroreFattura("Chiave vera di Invoicetronic senza FATTURE_VERE=1: fermo (una fattura inviata non si ritira).")
    return chiave


def chiama(metodo: str, percorso: str, **kwargs) -> dict:
    r = httpx.request(metodo, f"{API}{percorso}", auth=(_chiave(), ""), timeout=60, **kwargs)
    if r.status_code >= 400:
        raise ErroreFattura(f"Invoicetronic {r.status_code}: {r.text[:300]}")
    return r.json() if r.content else {}


def invia(conn, fattura_id: int) -> str:
    with conn.cursor() as cur:
        cur.execute("SELECT id, xml, stato FROM fatture WHERE id = %s FOR UPDATE", (fattura_id,))
        f = cur.fetchone()
        if not f or f["stato"] not in ("da_inviare", "errore"):
            return "niente da inviare"
        try:
            # Idempotency-Key: se la richiesta si ripete (rete), Invoicetronic non manda due volte la stessa fattura.
            r = chiama("POST", "/send/xml?validate=true", content=f["xml"].encode(),
                       headers={"Content-Type": "application/xml", "Idempotency-Key": f"br-fattura-{fattura_id}"})
        except (ErroreFattura, httpx.HTTPError) as exc:
            cur.execute("UPDATE fatture SET stato = 'errore', esito = %s, aggiornata_il = now() WHERE id = %s",
                        (str(exc)[:500], fattura_id))
            return "errore"
        cur.execute("UPDATE fatture SET stato = 'inviata', invio_id = %s, esito = %s, aggiornata_il = now() WHERE id = %s",
                    (str(r.get("id")), r.get("latest_state") or "inviata", fattura_id))
    return "inviata"


def aggiorna_stato(conn, fattura_id: int) -> str:
    """Legge le notifiche dello SdI per la fattura (le chiede il webhook update.add, o a mano)."""
    with conn.cursor() as cur:
        cur.execute("SELECT invio_id FROM fatture WHERE id = %s", (fattura_id,))
        f = cur.fetchone()
    if not f or not f["invio_id"]:
        return "non inviata"
    risposta = chiama("GET", "/update", params={"send_id": f["invio_id"], "page_size": 50})
    notifiche = risposta if isinstance(risposta, list) else risposta.get("items") or risposta.get("data") or []
    if not notifiche:
        return "nessuna notifica"
    ultima = max(notifiche, key=lambda u: u.get("last_update") or u.get("created") or "")
    stato = STATI_SDI.get(ultima.get("state"), "inviata")
    esito = f"{ultima.get('state')}: {ultima.get('description') or ''}".strip(": ")
    with conn.cursor() as cur:
        cur.execute("UPDATE fatture SET stato = %s, esito = %s, aggiornata_il = now() WHERE id = %s", (stato, esito[:500], fattura_id))
    return stato


def elenco(conn, limite: int = 200) -> list[dict]:
    with conn.cursor() as cur:
        cur.execute("""SELECT f.id, f.anno, f.numero, f.data, f.cliente->>'denominazione' AS cliente, f.imponibile, f.iva,
                              f.totale, f.stato, f.esito, f.aggiornata_il, u.email
                       FROM fatture f LEFT JOIN utenti u ON u.id = f.utente_id ORDER BY f.id DESC LIMIT %s""", (limite,))
        return [dict(r) for r in cur.fetchall()]
