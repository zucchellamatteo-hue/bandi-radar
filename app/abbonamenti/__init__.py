"""Abbonamenti con Stripe (05/10/2026): prova gratuita, mensile, annuale con impegno, imprese e sedi in piu'.

Scelte (spiegate a Matteo):
- Stripe Checkout per il primo pagamento, Customer Portal per carta, fatture e disdetta, webhook firmati per lo stato.
- Annuale = 20 euro addebitati ogni mese, con impegno di 12 mesi: nessuna "programmazione" in Stripe; il sistema
  registra la fine dell'impegno e fino ad allora apre il portale nella configurazione senza disdetta
  (STRIPE_PORTALE_ANNUALE). E' la soluzione con meno parti da gestire.
- Imprese e sedi in piu': righe dell'abbonamento con la quantita', aggiornata quando l'impresa cambia i suoi dati.
- Tutto dorme finche' ABBONAMENTI_ATTIVI non e' 1: l'area impresa resta aperta a tutti come oggi.
- Solo chiavi di prova (sk_test_...): le chiavi vere servono STRIPE_PAGAMENTI_VERI=1, cioe' il via di Matteo
  (termini, privacy, fatturazione elettronica risolta).
Le chiamate a Stripe sono richieste HTTP semplici (httpx): niente libreria in piu'.
"""

from __future__ import annotations

import hashlib
import hmac
import os
import time
from datetime import date, datetime, timedelta, timezone

import httpx

API = "https://api.stripe.com/v1"
CHIAVI_PREZZI = {"mensile": "br_mensile", "annuale": "br_annuale", "impresa": "br_impresa_extra", "sede": "br_sede_extra"}
CENTESIMI = {"br_mensile": 3000, "br_annuale": 2000, "br_impresa_extra": 1000, "br_sede_extra": 500}
NOMI_PREZZI = {"br_mensile": "Bandi Radar - mensile", "br_annuale": "Bandi Radar - annuale (impegno 12 mesi, pagato ogni mese)",
               "br_impresa_extra": "Impresa in piu'", "br_sede_extra": "Sede in piu' della stessa impresa"}
STATI_CON_ACCESSO = ("attivo", "in_ritardo", "gratuito")   # in ritardo: Stripe riprova l'addebito, intanto si entra


class ErroreAbbonamento(ValueError):
    pass


def attivi() -> bool:
    return os.environ.get("ABBONAMENTI_ATTIVI", "0") == "1"


def giorni_prova() -> int:
    try:
        return max(0, int(os.environ.get("PROVA_GIORNI", "14")))
    except ValueError:
        return 14


def adesso() -> datetime:
    return datetime.now(timezone.utc)


# --- stato e accesso ---

def leggi(conn, utente_id: int) -> dict:
    """L'abbonamento dell'utente; se non c'e' ancora, comincia la prova gratuita."""
    with conn.cursor() as cur:
        cur.execute("""INSERT INTO abbonamenti (utente_id, prova_fino_al) VALUES (%s, %s)
                       ON CONFLICT (utente_id) DO NOTHING""", (utente_id, adesso() + timedelta(days=giorni_prova())))
        cur.execute("SELECT * FROM abbonamenti WHERE utente_id = %s", (utente_id,))
        return dict(cur.fetchone())


def ha_accesso(a: dict, quando: datetime | None = None) -> bool:
    quando = quando or adesso()
    if a["stato"] in STATI_CON_ACCESSO:
        return True
    if a["stato"] == "prova":
        return bool(a["prova_fino_al"] and a["prova_fino_al"] > quando)
    if a["stato"] == "disdetto":   # pagato fino alla fine del periodo
        return bool(a["fine_periodo"] and a["fine_periodo"] > quando)
    return False


def puo_vedere_i_bandi(conn, utente: dict) -> bool:
    if not attivi() or utente["ruolo"] == "admin":
        return True
    return ha_accesso(leggi(conn, utente["id"]))


def quantita_extra(conn, utente_id: int) -> tuple[int, int]:
    """(imprese in piu', sedi in piu'): la prima impresa con la sua prima sede e' compresa nell'abbonamento."""
    with conn.cursor() as cur:
        cur.execute("""SELECT jsonb_array_length(coalesce(p.profilo->'sedi', '[]')) AS sedi
                       FROM imprese i JOIN profili p ON p.codice = i.profilo_codice WHERE i.utente_id = %s""", (utente_id,))
        sedi = [r["sedi"] for r in cur.fetchall()]
    return max(0, len(sedi) - 1), sum(max(0, s - 1) for s in sedi)


def riepilogo(conn, utente: dict) -> dict:
    a = leggi(conn, utente["id"])
    imprese, sedi = quantita_extra(conn, utente["id"])
    giorni = None
    if a["stato"] == "prova" and a["prova_fino_al"]:
        giorni = max(0, -(-(a["prova_fino_al"] - adesso()).total_seconds() // 86400))   # giorni che restano, per eccesso
        giorni = int(giorni)
    return {"stato": a["stato"], "piano": a["piano"], "accesso": ha_accesso(a) or not attivi(), "attivi": attivi(),
            "giorni_prova": giorni, "prova_fino_al": a["prova_fino_al"], "fine_impegno": a["fine_impegno"],
            "fine_periodo": a["fine_periodo"], "imprese_extra": imprese, "sedi_extra": sedi,
            "prezzi": {k: CENTESIMI[v] / 100 for k, v in CHIAVI_PREZZI.items()},
            "iva_inclusa": os.environ.get("PREZZI_IVA_INCLUSA", "0") == "1",
            "stripe": bool(os.environ.get("STRIPE_SECRET_KEY")), "portale": bool(a["stripe_cliente"])}


def elenco(conn) -> list[dict]:
    with conn.cursor() as cur:
        cur.execute("""SELECT u.id AS utente_id, u.email, u.nome, a.stato, a.piano, a.prova_fino_al, a.fine_impegno,
                              a.fine_periodo, a.imprese_extra, a.sedi_extra, a.nota,
                              (SELECT count(*) FROM imprese i WHERE i.utente_id = u.id) AS imprese
                       FROM utenti u LEFT JOIN abbonamenti a ON a.utente_id = u.id
                       WHERE u.ruolo = 'impresa' ORDER BY u.creato_il DESC""")
        return [dict(r) for r in cur.fetchall()]


def imposta(conn, utente_id: int, stato: str | None = None, giorni_prova_in_piu: int | None = None,
            nota: str | None = None) -> dict:
    """Modifica a mano dell'admin: abbonamento gratuito, prova allungata, nota."""
    if stato is not None and stato not in ("prova", "gratuito", "disdetto"):
        raise ErroreAbbonamento("Si possono impostare a mano solo: prova, gratuito, disdetto.")
    leggi(conn, utente_id)
    with conn.cursor() as cur:
        if giorni_prova_in_piu:
            cur.execute("""UPDATE abbonamenti SET prova_fino_al = greatest(coalesce(prova_fino_al, now()), now())
                           + make_interval(days => %s) WHERE utente_id = %s""", (giorni_prova_in_piu, utente_id))
        cur.execute("""UPDATE abbonamenti SET stato = coalesce(%s, stato), nota = coalesce(%s, nota), aggiornato_il = now()
                       WHERE utente_id = %s RETURNING *""", (stato, nota, utente_id))
        return dict(cur.fetchone())


# --- Stripe ---

def _chiave() -> str:
    chiave = os.environ.get("STRIPE_SECRET_KEY", "")
    if not chiave:
        raise ErroreAbbonamento("I pagamenti non sono ancora configurati.")
    if not chiave.startswith(("sk_test_", "rk_test_")) and os.environ.get("STRIPE_PAGAMENTI_VERI") != "1":
        raise ErroreAbbonamento("Chiave Stripe vera senza il via ai pagamenti veri (STRIPE_PAGAMENTI_VERI=1): fermo.")
    return chiave


def chiama(metodo: str, percorso: str, dati: dict | None = None) -> dict:
    """Una richiesta all'API di Stripe (parametri in forma piatta: "line_items[0][price]")."""
    r = httpx.request(metodo, f"{API}{percorso}", data=dati if metodo != "GET" else None,
                      params=dati if metodo == "GET" else None, auth=(_chiave(), ""), timeout=30)
    corpo = r.json()
    if r.status_code >= 400:
        raise ErroreAbbonamento(f"Stripe: {corpo.get('error', {}).get('message', r.status_code)}")
    return corpo


def prezzi_stripe() -> dict[str, str]:
    """lookup_key -> id del prezzo in Stripe (creati da `python -m app.abbonamenti prepara-stripe`)."""
    dati = {f"lookup_keys[{i}]": k for i, k in enumerate(CHIAVI_PREZZI.values())}
    trovati = {p["lookup_key"]: p["id"] for p in chiama("GET", "/prices", {**dati, "active": "true"})["data"]}
    mancano = set(CHIAVI_PREZZI.values()) - set(trovati)
    if mancano:
        raise ErroreAbbonamento(f"Prezzi mancanti in Stripe: {', '.join(sorted(mancano))} (prepara-stripe).")
    return trovati


def _cliente(conn, utente: dict, a: dict) -> str:
    if a["stripe_cliente"]:
        return a["stripe_cliente"]
    # A Stripe va l'email (serve per ricevute e fatture), mai il profilo dell'impresa.
    c = chiama("POST", "/customers", {"email": utente["email"], "name": utente.get("nome") or "",
                                      "metadata[utente_id]": str(utente["id"])})
    with conn.cursor() as cur:
        cur.execute("UPDATE abbonamenti SET stripe_cliente = %s WHERE utente_id = %s", (c["id"], utente["id"]))
    return c["id"]


def checkout(conn, utente: dict, piano: str) -> str:
    """Pagina di pagamento di Stripe per il piano scelto, con imprese e sedi in piu'. Ritorna l'indirizzo."""
    from app.utenti import sito_url

    if piano not in ("mensile", "annuale"):
        raise ErroreAbbonamento("Piano non valido.")
    a = leggi(conn, utente["id"])
    if a["stato"] in ("attivo", "in_ritardo") and a["stripe_abbonamento"]:
        raise ErroreAbbonamento("Hai gia' un abbonamento attivo: per cambiarlo usa \"Gestisci abbonamento\".")
    prezzi = prezzi_stripe()
    imprese, sedi = quantita_extra(conn, utente["id"])
    dati = {"mode": "subscription", "customer": _cliente(conn, utente, a), "client_reference_id": str(utente["id"]),
            "line_items[0][price]": prezzi[CHIAVI_PREZZI[piano]], "line_items[0][quantity]": "1",
            "subscription_data[metadata][utente_id]": str(utente["id"]), "subscription_data[metadata][piano]": piano,
            "billing_address_collection": "required", "tax_id_collection[enabled]": "true",
            "customer_update[address]": "auto", "customer_update[name]": "auto", "locale": "it",
            "success_url": f"{sito_url()}/impresa/abbonamento?esito=ok", "cancel_url": f"{sito_url()}/impresa/abbonamento"}
    riga = 1
    for chiave, quanti in (("impresa", imprese), ("sede", sedi)):
        if quanti:
            dati[f"line_items[{riga}][price]"] = prezzi[CHIAVI_PREZZI[chiave]]
            dati[f"line_items[{riga}][quantity]"] = str(quanti)
            riga += 1
    # I giorni di prova che restano valgono anche pagando prima (Stripe vuole almeno 2 giorni nel futuro).
    # Prezzi IVA esclusa (Matteo, 05/10): Stripe aggiunge l'IVA al 22% con l'aliquota creata da prepara-stripe.
    if os.environ.get("STRIPE_IVA_22"):
        dati["subscription_data[default_tax_rates][0]"] = os.environ["STRIPE_IVA_22"]
    # Con le fatture elettroniche accese servono prima i dati di fatturazione (ragione sociale, P.IVA, SDI o PEC).
    from app import fatture

    if fatture.attive() and not fatture.leggi_dati(conn, utente["id"]):
        raise ErroreAbbonamento("Prima inserisci i dati di fatturazione (ragione sociale, partita IVA, codice SDI o PEC).")
    if a["stato"] == "prova" and a["prova_fino_al"] and a["prova_fino_al"] > adesso() + timedelta(days=2):
        dati["subscription_data[trial_end]"] = str(int(a["prova_fino_al"].timestamp()))
    conn.commit()
    return chiama("POST", "/checkout/sessions", dati)["url"]


def portale(conn, utente: dict) -> str:
    """Portale clienti di Stripe: carta, fatture, disdetta (non durante l'impegno dell'annuale)."""
    from app.utenti import sito_url

    a = leggi(conn, utente["id"])
    if not a["stripe_cliente"]:
        raise ErroreAbbonamento("Non c'e' ancora un abbonamento da gestire.")
    dati = {"customer": a["stripe_cliente"], "return_url": f"{sito_url()}/impresa/abbonamento", "locale": "it"}
    senza_disdetta = os.environ.get("STRIPE_PORTALE_ANNUALE")
    if a["piano"] == "annuale" and a["fine_impegno"] and a["fine_impegno"] > date.today() and senza_disdetta:
        dati["configuration"] = senza_disdetta
    elif os.environ.get("STRIPE_PORTALE"):
        dati["configuration"] = os.environ["STRIPE_PORTALE"]
    return chiama("POST", "/billing_portal/sessions", dati)["url"]


def sincronizza_quantita(conn, utente_id: int) -> str:
    """Dopo che l'impresa ha cambiato imprese o sedi: aggiorna le quantita' in Stripe (con il conguaglio)."""
    imprese, sedi = quantita_extra(conn, utente_id)
    with conn.cursor() as cur:
        cur.execute("UPDATE abbonamenti SET imprese_extra = %s, sedi_extra = %s WHERE utente_id = %s RETURNING stripe_abbonamento, stato",
                    (imprese, sedi, utente_id))
        a = cur.fetchone()
    if not a or not a["stripe_abbonamento"] or a["stato"] not in ("attivo", "in_ritardo") or not attivi():
        return "niente da aggiornare"
    prezzi = prezzi_stripe()
    abb = chiama("GET", f"/subscriptions/{a['stripe_abbonamento']}")
    presenti = {i["price"]["lookup_key"]: i["id"] for i in abb["items"]["data"]}
    dati, n = {"proration_behavior": "create_prorations"}, 0
    for chiave, quanti in (("impresa", imprese), ("sede", sedi)):
        lk = CHIAVI_PREZZI[chiave]
        if lk in presenti and quanti:
            dati.update({f"items[{n}][id]": presenti[lk], f"items[{n}][quantity]": str(quanti)})
        elif lk in presenti:
            dati.update({f"items[{n}][id]": presenti[lk], f"items[{n}][deleted]": "true"})
        elif quanti:
            dati.update({f"items[{n}][price]": prezzi[lk], f"items[{n}][quantity]": str(quanti)})
        else:
            continue
        n += 1
    if n:
        chiama("POST", f"/subscriptions/{a['stripe_abbonamento']}", dati)
    return f"{imprese} imprese e {sedi} sedi in piu'"


# --- webhook ---

def verifica_firma(corpo: bytes, intestazione: str | None, segreto: str, tolleranza: int = 300) -> bool:
    """Firma dei webhook di Stripe: HMAC-SHA256 di "timestamp.corpo" con il segreto dell'endpoint."""
    if not intestazione or not segreto:
        return False
    parti = dict(p.split("=", 1) for p in intestazione.split(",") if "=" in p)
    firme = [p.split("=", 1)[1] for p in intestazione.split(",") if p.startswith("v1=")]
    try:
        ts = int(parti.get("t", ""))
    except ValueError:
        return False
    if abs(time.time() - ts) > tolleranza:
        return False
    atteso = hmac.new(segreto.encode(), f"{ts}.".encode() + corpo, hashlib.sha256).hexdigest()
    return any(hmac.compare_digest(atteso, f) for f in firme)


_STATI_STRIPE = {"active": "attivo", "trialing": "attivo", "past_due": "in_ritardo", "unpaid": "in_ritardo",
                 "canceled": "disdetto", "incomplete_expired": "disdetto", "paused": "disdetto"}


def _un_anno_dopo(d: date) -> date:
    try:
        return d.replace(year=d.year + 1)
    except ValueError:   # 29 febbraio
        return d + timedelta(days=365)


def _data(ts) -> datetime | None:
    return datetime.fromtimestamp(ts, timezone.utc) if ts else None


def gestisci_evento(conn, evento: dict) -> str:
    """Applica un evento di Stripe (una volta sola). Ritorna cosa e' stato fatto."""
    with conn.cursor() as cur:
        cur.execute("INSERT INTO eventi_stripe (id, tipo) VALUES (%s, %s) ON CONFLICT DO NOTHING RETURNING id",
                    (evento["id"], evento["type"]))
        if not cur.fetchone():
            return "gia' ricevuto"
    o = evento["data"]["object"]
    esito = "ignorato"
    with conn.cursor() as cur:
        if evento["type"] == "checkout.session.completed" and o.get("mode") == "subscription":
            utente_id = int(o.get("client_reference_id") or 0)
            cur.execute("""UPDATE abbonamenti SET stripe_cliente = %s, stripe_abbonamento = %s, aggiornato_il = now()
                           WHERE utente_id = %s""", (o.get("customer"), o.get("subscription"), utente_id))
            esito = f"pagamento completato per l'utente {utente_id}"
        elif evento["type"].startswith("customer.subscription."):
            utente_id = int((o.get("metadata") or {}).get("utente_id") or 0)
            if not utente_id:
                cur.execute("SELECT utente_id FROM abbonamenti WHERE stripe_cliente = %s", (o.get("customer"),))
                r = cur.fetchone()
                utente_id = r["utente_id"] if r else 0
            stato = _STATI_STRIPE.get(o.get("status"))
            if utente_id and stato:
                if evento["type"] == "customer.subscription.deleted":
                    stato = "disdetto"
                piano = (o.get("metadata") or {}).get("piano")
                inizio = _data(o.get("start_date"))
                impegno = _un_anno_dopo(inizio.date()) if inizio and piano == "annuale" else None
                cur.execute("""UPDATE abbonamenti SET stato = CASE WHEN stato = 'gratuito' THEN stato ELSE %s END,
                                 piano = coalesce(%s, piano), stripe_abbonamento = %s, stripe_cliente = coalesce(stripe_cliente, %s),
                                 fine_periodo = %s, fine_impegno = coalesce(fine_impegno, %s), aggiornato_il = now()
                               WHERE utente_id = %s""",
                            (stato, piano, o.get("id"), o.get("customer"), _data(o.get("current_period_end")
                             or (o.get("items", {}).get("data") or [{}])[0].get("current_period_end")), impegno, utente_id))
                esito = f"utente {utente_id}: {stato}"
        elif evento["type"] == "invoice.paid":
            esito = _fattura_elettronica(conn, o)
        elif evento["type"] == "invoice.payment_failed":
            cur.execute("UPDATE abbonamenti SET stato = 'in_ritardo', aggiornato_il = now() WHERE stripe_cliente = %s "
                        "AND stato = 'attivo'", (o.get("customer"),))
            esito = "addebito non riuscito"
        cur.execute("UPDATE eventi_stripe SET esito = %s WHERE id = %s", (esito, evento["id"]))
    return esito


def _fattura_elettronica(conn, fattura_stripe: dict) -> str:
    """Pagamento riuscito: fattura elettronica (app/fatture), se attiva. Un errore non ferma il webhook: la fattura
    resta da rifare dalla pagina Imprese."""
    from app import fatture

    if not fatture.attive():
        return "pagamento registrato (fatture elettroniche spente)"
    with conn.cursor() as cur:
        cur.execute("SELECT utente_id FROM abbonamenti WHERE stripe_cliente = %s", (fattura_stripe.get("customer"),))
        r = cur.fetchone()
    if not r:
        return "pagamento di un cliente sconosciuto: nessuna fattura"
    try:
        fid = fatture.crea_da_stripe(conn, r["utente_id"], fattura_stripe)
    except fatture.ErroreFattura as exc:
        return f"fattura non creata: {exc}"
    if fid is None:
        return "fattura gia' fatta o importo zero"
    return f"fattura {fid}: {fatture.invia(conn, fid)}"


# --- preparazione dei prodotti in Stripe (una volta, con le chiavi di prova) ---

def prepara_stripe() -> list[str]:
    """Crea in Stripe i prezzi (con lookup_key, si possono rilanciare) e la configurazione del portale senza disdetta."""
    from app.utenti import sito_url

    iva = "inclusive" if os.environ.get("PREZZI_IVA_INCLUSA", "0") == "1" else "exclusive"
    fatti = []
    dati = {f"lookup_keys[{i}]": k for i, k in enumerate(CHIAVI_PREZZI.values())}
    esistenti = {p["lookup_key"] for p in chiama("GET", "/prices", dati)["data"]}
    for lk, centesimi in CENTESIMI.items():
        if lk in esistenti:
            fatti.append(f"{lk}: c'era gia'")
            continue
        p = chiama("POST", "/prices", {"currency": "eur", "unit_amount": str(centesimi), "recurring[interval]": "month",
                                       "lookup_key": lk, "tax_behavior": iva, "product_data[name]": NOMI_PREZZI[lk]})
        fatti.append(f"{lk}: creato {p['id']}")
    comune = {"business_profile[headline]": "Bandi Radar - il tuo abbonamento",
              "business_profile[privacy_policy_url]": f"{sito_url()}/privacy",
              "business_profile[terms_of_service_url]": f"{sito_url()}/termini",
              "features[invoice_history][enabled]": "true", "features[payment_method_update][enabled]": "true",
              "features[customer_update][enabled]": "true", "features[customer_update][allowed_updates][0]": "address",
              "features[customer_update][allowed_updates][1]": "tax_id", "features[customer_update][allowed_updates][2]": "name"}
    normale = chiama("POST", "/billing_portal/configurations", {**comune, "features[subscription_cancel][enabled]": "true",
                                                               "features[subscription_cancel][mode]": "at_period_end",
                                                               "default_return_url": f"{sito_url()}/impresa/abbonamento"})
    annuale = chiama("POST", "/billing_portal/configurations", {**comune, "features[subscription_cancel][enabled]": "false",
                                                               "default_return_url": f"{sito_url()}/impresa/abbonamento"})
    fatti.append(f"portale con disdetta: STRIPE_PORTALE={normale['id']}")
    iva22 = chiama("POST", "/tax_rates", {"display_name": "IVA", "percentage": "22", "inclusive": "false", "country": "IT",
                                          "jurisdiction": "IT", "description": "IVA ordinaria 22%"})
    fatti.append(f"aliquota IVA 22%: STRIPE_IVA_22={iva22['id']}")
    fatti.append(f"portale senza disdetta per l'annuale: STRIPE_PORTALE_ANNUALE={annuale['id']}")
    return fatti
