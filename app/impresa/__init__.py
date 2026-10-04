"""Area impresa (05/10/2026): le imprese di un utente, i bandi pertinenti, la scheda ridotta, le richieste di supporto.

Ogni impresa ha un profilo ANONIMO nella tabella profili (codice casuale "imp-...", origine 'impresa'): l'abbinamento
e' lo stesso di catalogo e profili (app/abbinamento/catalogo.abbina), senza IA. Nome dell'impresa e utente stanno
nella tabella imprese, separati dal profilo.
"""

from __future__ import annotations

import json
import secrets
from datetime import date

from app.abbinamento import catalogo, regole

# Fasce del modulo guidato: l'abbinamento non inventa i numeri, quindi dalle fasce si ricava solo la dimensione
# (raccomandazione UE 2003/361); dipendenti e fatturato esatti restano vuoti e i bandi con soglie diventano
# "da verificare" invece di essere scartati per sbaglio.
FASCE_DIPENDENTI = {"0": (0, 0), "1-9": (1, 9), "10-49": (10, 49), "50-249": (50, 249), "250+": (250, None)}
FASCE_FATTURATO = {"fino_2m": (0, 2_000_000), "2m-10m": (2_000_000, 10_000_000), "10m-50m": (10_000_000, 50_000_000),
                   "oltre_50m": (50_000_000, None)}
_CLASSI = ("micro", "piccola", "media", "grande")
_CLASSE_DIPENDENTI = {"0": 0, "1-9": 0, "10-49": 1, "50-249": 2, "250+": 3}
_CLASSE_FATTURATO = {"fino_2m": 0, "2m-10m": 1, "10m-50m": 2, "oltre_50m": 3}

AVVERTENZA = "Informazione indicativa: verificare sempre il bando ufficiale prima di presentare la domanda."

# Campi della scheda ridotta (piano: sintesi, forma dell'incentivo, a chi si rivolge, scadenza, cosa serve, link).
CAMPI_SCHEDA_RIDOTTA = ("id", "titolo", "ente", "territorio", "url", "stato", "data_apertura", "ora_apertura", "scadenza",
                        "ora_scadenza", "chiuso_il", "sintesi", "a_chi_si_rivolge", "cosa_finanzia", "spese_ammesse",
                        "requisiti", "tipi_agevolazione", "tipo_agevolazione", "contributo_massimo", "percentuale",
                        "fondo_perduto_massimo", "finanziamento_massimo", "spesa_minima", "spesa_massima", "dotazione",
                        "modalita_selezione", "forma_incentivo", "versione")


class ErroreImpresa(ValueError):
    pass


def dimensione_dalle_fasce(dipendenti: str | None, fatturato: str | None) -> str | None:
    """La classe e' la piu' grande tra quella dei dipendenti e quella del fatturato (senza bilancio: prudenza)."""
    classi = [c for c in (_CLASSE_DIPENDENTI.get(dipendenti or ""), _CLASSE_FATTURATO.get(fatturato or "")) if c is not None]
    return _CLASSI[max(classi)] if classi else None


def _profilo(profilo: dict, codice: str, fasce: dict):
    from app.abbinamento.profilo import Profilo

    p = dict(profilo or {})
    for vietato in ("codice", "note"):   # il codice lo sceglie il sistema; le note sono per i profili di Matteo
        p.pop(vietato, None)
    if not p.get("dimensione"):
        p["dimensione"] = dimensione_dalle_fasce(fasce.get("dipendenti"), fasce.get("fatturato"))
    if fasce.get("dipendenti") == "0":
        p["dipendenti"] = 0
    try:
        return Profilo.model_validate({**p, "codice": codice})
    except Exception as exc:  # noqa: BLE001 - pydantic: si riporta il messaggio leggibile
        errori = getattr(exc, "errors", None)
        if callable(errori):
            raise ErroreImpresa("; ".join(str(e["msg"]).removeprefix("Value error, ") for e in errori())) from exc
        raise ErroreImpresa(str(exc)) from exc


def _fasce(fasce: dict | None) -> dict:
    fasce = {k: v for k, v in (fasce or {}).items() if v}
    if fasce.get("dipendenti") not in (None, *FASCE_DIPENDENTI):
        raise ErroreImpresa("Fascia di dipendenti non valida.")
    if fasce.get("fatturato") not in (None, *FASCE_FATTURATO):
        raise ErroreImpresa("Fascia di fatturato non valida.")
    return {k: fasce[k] for k in ("dipendenti", "fatturato") if k in fasce}


def _nome(nome: str) -> str:
    nome = (nome or "").strip()
    if not nome:
        raise ErroreImpresa("Scrivi il nome dell'impresa.")
    return nome[:200]


def crea(conn, utente_id: int, nome: str, profilo: dict, fasce: dict | None = None) -> dict:
    fasce = _fasce(fasce)
    codice = "imp-" + secrets.token_hex(5)
    p = _profilo(profilo, codice, fasce)
    with conn.cursor() as cur:
        cur.execute("INSERT INTO profili (codice, profilo, origine) VALUES (%s, %s::jsonb, 'impresa')",
                    (codice, p.model_dump_json()))
        cur.execute("""INSERT INTO imprese (utente_id, nome, profilo_codice, dati, codice_disiscrizione)
                       VALUES (%s, %s, %s, %s, %s) RETURNING id""",
                    (utente_id, _nome(nome), codice, json.dumps({"fasce": fasce}), secrets.token_urlsafe(24)))
        nuovo = cur.fetchone()["id"]
    return leggi(conn, utente_id, nuovo)


def aggiorna(conn, utente_id: int, impresa_id: int, nome: str, profilo: dict, fasce: dict | None = None,
             email_settimanale: bool | None = None) -> dict:
    attuale = leggi(conn, utente_id, impresa_id)
    fasce = _fasce(fasce)
    p = _profilo(profilo, attuale["profilo_codice"], fasce)
    with conn.cursor() as cur:
        cur.execute("UPDATE profili SET profilo = %s::jsonb, aggiornato_il = now() WHERE codice = %s",
                    (p.model_dump_json(), attuale["profilo_codice"]))
        cur.execute("""UPDATE imprese SET nome = %s, dati = dati || %s::jsonb, aggiornata_il = now(),
                       email_settimanale = coalesce(%s, email_settimanale) WHERE id = %s""",
                    (_nome(nome), json.dumps({"fasce": fasce}), email_settimanale, impresa_id))
    return leggi(conn, utente_id, impresa_id)


def cancella(conn, utente_id: int, impresa_id: int) -> None:
    attuale = leggi(conn, utente_id, impresa_id)
    with conn.cursor() as cur:
        cur.execute("DELETE FROM imprese WHERE id = %s", (impresa_id,))
        cur.execute("DELETE FROM profili WHERE codice = %s", (attuale["profilo_codice"],))


def _riga(r: dict) -> dict:
    profilo = r.get("profilo") or {}
    return {"id": r["id"], "nome": r["nome"], "profilo_codice": r["profilo_codice"], "profilo": profilo,
            "fasce": (r.get("dati") or {}).get("fasce", {}), "email_settimanale": r["email_settimanale"],
            "sedi": len(profilo.get("sedi") or []), "creata_il": r["creata_il"]}


def elenco(conn, utente_id: int) -> list[dict]:
    with conn.cursor() as cur:
        cur.execute("""SELECT i.*, p.profilo FROM imprese i JOIN profili p ON p.codice = i.profilo_codice
                       WHERE i.utente_id = %s ORDER BY i.id""", (utente_id,))
        return [_riga(dict(r)) for r in cur.fetchall()]


def leggi(conn, utente_id: int, impresa_id: int) -> dict:
    with conn.cursor() as cur:
        cur.execute("""SELECT i.*, p.profilo FROM imprese i JOIN profili p ON p.codice = i.profilo_codice
                       WHERE i.id = %s AND i.utente_id = %s""", (impresa_id, utente_id))
        r = cur.fetchone()
    if not r:
        raise ErroreImpresa("Impresa non trovata.")
    return _riga(dict(r))


def pertinenti(bandi: list[dict], profilo: dict, oggi: date | None = None) -> list[tuple[dict, regole.Esito]]:
    """I bandi da mostrare all'impresa: compatibili o da verificare, proponibili (scheda sul bando ufficiale), aperti o in
    arrivo. Mai gli esclusi. E' lo stesso abbinamento del catalogo e dei profili."""
    return catalogo.abbina(bandi, profilo, oggi)


def riga_bando(b: dict, esito: regole.Esito) -> dict:
    """Riga dell'elenco "I miei bandi": niente dati di lavorazione (qualita', livelli delle fonti)."""
    r = catalogo.riga(b, esito)
    for interno in ("qualita", "livelli", "completezza"):
        r.pop(interno, None)
    return r


def bandi_dell_impresa(conn, utente_id: int, impresa_id: int, bandi: list[dict] | None = None) -> dict:
    impresa = leggi(conn, utente_id, impresa_id)
    from app.abbinamento.profilo import Profilo

    profilo = Profilo.model_validate(impresa["profilo"]).per_regole()
    risultati = pertinenti(bandi if bandi is not None else catalogo.carica_bandi(conn), profilo)
    conteggi = {"compatibile": 0, "da_verificare": 0}
    for _, e in risultati:
        conteggi[e.livello] += 1
    return {"impresa": {"id": impresa["id"], "nome": impresa["nome"]}, "conteggi": conteggi,
            "bandi": [riga_bando(b, e) for b, e in risultati]}


def imprese_per_bando(conn, utente_id: int, bando_id: int) -> list[dict]:
    """Le imprese dell'utente per cui il bando e' pertinente, con l'esito: vuoto = l'utente non puo' vederlo."""
    from app.abbinamento.profilo import Profilo

    imprese = elenco(conn, utente_id)
    if not imprese:
        return []
    bandi = [b for b in catalogo.carica_bandi(conn) if b["id"] == bando_id]
    if not bandi:
        return []
    trovate = []
    for i in imprese:
        for b, e in pertinenti(bandi, Profilo.model_validate(i["profilo"]).per_regole()):
            trovate.append({"id": i["id"], "nome": i["nome"], "esito": e.come_dict()})
    return trovate


def scheda_ridotta(conn, utente_id: int, bando_id: int) -> dict:
    imprese = imprese_per_bando(conn, utente_id, bando_id)
    if not imprese:
        raise ErroreImpresa("Bando non trovato tra quelli adatti alle tue imprese.")
    with conn.cursor() as cur:
        cur.execute(f"SELECT {', '.join(CAMPI_SCHEDA_RIDOTTA)} FROM bandi WHERE id = %s", (bando_id,))
        b = dict(cur.fetchone())
        cur.execute("""SELECT id, nome, url, tipo FROM allegati WHERE bando_id = %s AND annuncio_id IS NULL
                       AND categoria IN ('bando', 'modulistica', 'faq', 'decreto') AND errore IS NULL ORDER BY id""",
                    (bando_id,))
        documenti = [dict(r) for r in cur.fetchall()]
    return {**b, "imprese": imprese, "documenti_ufficiali": [{"nome": d["nome"], "url": d["url"]} for d in documenti],
            "avvertenza": AVVERTENZA}


# --- richieste di supporto ---

STATI_RICHIESTA = ("nuova", "in_corso", "accettata", "chiusa")


def richiedi_supporto(conn, utente: dict, impresa_id: int, bando_id: int, messaggio: str | None,
                      origine: str = "piattaforma") -> dict:
    impresa = leggi(conn, utente["id"], impresa_id)
    if not any(i["id"] == impresa_id for i in imprese_per_bando(conn, utente["id"], bando_id)):
        raise ErroreImpresa("Il bando non risulta adatto a questa impresa.")
    with conn.cursor() as cur:
        cur.execute("""SELECT id FROM richieste_supporto WHERE impresa_id = %s AND bando_id = %s AND stato <> 'chiusa'""",
                    (impresa_id, bando_id))
        gia = cur.fetchone()
        if gia:
            raise ErroreImpresa("Hai gia' una richiesta aperta per questo bando: ti ricontattiamo noi.")
        cur.execute("""INSERT INTO richieste_supporto (impresa_id, bando_id, utente_id, messaggio, origine)
                       VALUES (%s, %s, %s, %s, %s) RETURNING *""",
                    (impresa_id, bando_id, utente["id"], (messaggio or "").strip()[:4000] or None,
                     origine if origine in ("piattaforma", "email") else "piattaforma"))
        r = dict(cur.fetchone())
        cur.execute("SELECT titolo, scadenza FROM bandi WHERE id = %s", (bando_id,))
        bando = cur.fetchone()
    r["impresa_nome"], r["bando_titolo"], r["bando_scadenza"] = impresa["nome"], bando["titolo"], bando["scadenza"]
    return r


def richieste_dell_utente(conn, utente_id: int) -> list[dict]:
    with conn.cursor() as cur:
        cur.execute("""SELECT r.id, r.bando_id, r.impresa_id, r.messaggio, r.stato, r.creata_il, b.titolo AS bando_titolo,
                              i.nome AS impresa_nome
                       FROM richieste_supporto r JOIN imprese i ON i.id = r.impresa_id JOIN bandi b ON b.id = r.bando_id
                       WHERE i.utente_id = %s ORDER BY r.creata_il DESC""", (utente_id,))
        return [dict(r) for r in cur.fetchall()]


def richieste_tutte(conn, stato: str | None = None) -> list[dict]:
    with conn.cursor() as cur:
        cur.execute("""SELECT r.*, b.titolo AS bando_titolo, b.scadenza AS bando_scadenza, i.nome AS impresa_nome,
                              u.email, u.nome AS utente_nome
                       FROM richieste_supporto r JOIN imprese i ON i.id = r.impresa_id JOIN bandi b ON b.id = r.bando_id
                       JOIN utenti u ON u.id = i.utente_id
                       WHERE %s::text IS NULL OR r.stato = %s
                       ORDER BY (r.stato = 'nuova') DESC, r.creata_il DESC LIMIT 500""", (stato, stato))
        return [dict(r) for r in cur.fetchall()]


def gestisci_richiesta(conn, richiesta_id: int, stato: str, nota: str | None) -> dict:
    if stato not in STATI_RICHIESTA:
        raise ErroreImpresa("Stato non valido.")
    with conn.cursor() as cur:
        cur.execute("""UPDATE richieste_supporto SET stato = %s, nota = coalesce(%s, nota), aggiornata_il = now()
                       WHERE id = %s RETURNING *""", (stato, nota, richiesta_id))
        r = cur.fetchone()
    if not r:
        raise ErroreImpresa("Richiesta non trovata.")
    return dict(r)


def email_richiesta(r: dict, utente: dict) -> tuple[str, str]:
    """Email a Matteo per una richiesta di supporto (va a lui, non all'IA: qui il nome dell'impresa puo' esserci)."""
    from app.utenti import sito_url

    testo = (f"Nuova richiesta di supporto per la domanda.\n\n"
             f"Impresa: {r['impresa_nome']}\nUtente: {utente.get('nome') or ''} <{utente['email']}>\n"
             f"Bando: {r['bando_titolo']} (scadenza {r['bando_scadenza'] or 'non indicata'})\n"
             f"Messaggio: {r.get('messaggio') or '(nessuno)'}\n\n"
             f"Scheda: {sito_url()}/bandi/{r['bando_id']}\nRichieste: {sito_url()}/imprese\n")
    return f"Richiesta di supporto: {r['bando_titolo'][:80]}", testo


def imprese_tutte(conn) -> list[dict]:
    """Per l'admin: imprese iscritte con l'utente, le sedi e se ricevono l'email."""
    with conn.cursor() as cur:
        cur.execute("""SELECT i.id, i.nome, i.email_settimanale, i.creata_il, u.email, u.nome AS utente_nome, u.attivo,
                              jsonb_array_length(coalesce(p.profilo->'sedi', '[]')) AS sedi,
                              (SELECT count(*) FROM richieste_supporto r WHERE r.impresa_id = i.id) AS richieste
                       FROM imprese i JOIN utenti u ON u.id = i.utente_id JOIN profili p ON p.codice = i.profilo_codice
                       ORDER BY i.creata_il DESC""")
        return [dict(r) for r in cur.fetchall()]


def disiscrivi(conn, codice: str) -> str | None:
    """Toglie l'email settimanale dal link nell'email (senza accesso). Ritorna il nome dell'impresa o None."""
    with conn.cursor() as cur:
        cur.execute("UPDATE imprese SET email_settimanale = false WHERE codice_disiscrizione = %s RETURNING nome",
                    (codice or "",))
        r = cur.fetchone()
    return r["nome"] if r else None
