"""Segnalazioni rapide (06/10/2026): il pulsante "Segnala" in basso a destra in ogni pagina della plancia.

Chiunque abbia fatto l'accesso sceglie il tipo di problema, compila i pochi campi del tipo e scrive un testo libero; la
plancia aggiunge da sola la pagina in cui si trova e, nella pagina di un bando, il suo numero. Matteo e chi ha il
permesso "lavoro" le vedono nella pagina Segnalazioni; le sessioni di Claude Code le leggono con
python -m app.segnalazioni e le chiudono con una risposta (python -m app.segnalazioni rispondi ID risolta "testo").
"""

from __future__ import annotations

import json
import re

# Tipi di segnalazione: nome, descrizione breve e campi propri (chiave -> etichetta). "bando" e' il numero o il nome del
# bando: se e' un numero diventa bando_id. L'ordine e' quello del menu del pulsante.
TIPI: dict[str, dict] = {
    "manca_bando": {
        "nome": "Manca un bando",
        "descrizione": "Conosci un bando che non trovi nel catalogo.",
        "campi": {"bando_nome": "Nome del bando", "link": "Link alla pagina del bando"},
    },
    "errore_scheda": {
        "nome": "Errore in una scheda",
        "descrizione": "Un dato della scheda è sbagliato (importi, beneficiari, territorio, ATECO...).",
        "campi": {"bando": "Bando (numero o nome)", "campo": "Campo sbagliato"},
    },
    "stato_scadenza": {
        "nome": "Stato o scadenza sbagliati",
        "descrizione": "Il bando risulta aperto ma è chiuso (o il contrario), oppure la data è sbagliata.",
        "campi": {"bando": "Bando (numero o nome)", "giusto": "Stato o data giusti"},
    },
    "doppione": {
        "nome": "Doppione",
        "descrizione": "Lo stesso bando compare due volte.",
        "campi": {"bando": "Bando (numero o nome)", "altro_bando": "L'altro bando (numero o link)"},
    },
    "documenti": {
        "nome": "Documenti sbagliati o mancanti",
        "descrizione": "Manca il testo del bando o un allegato, oppure un documento non c'entra.",
        "campi": {"bando": "Bando (numero o nome)", "documento": "Quale documento (nome o link)"},
    },
    "plancia": {
        "nome": "Problema della plancia",
        "descrizione": "Una pagina non funziona, un pulsante non fa niente, un errore sullo schermo.",
        "campi": {},
    },
    "idea": {
        "nome": "Idea o richiesta",
        "descrizione": "Qualcosa che vorresti avere o fare in modo diverso.",
        "campi": {},
    },
    "altro": {
        "nome": "Altro",
        "descrizione": "Tutto il resto.",
        "campi": {},
    },
}
STATI = {"nuova": "nuova", "presa_in_carico": "presa in carico", "risolta": "risolta", "respinta": "respinta"}
APERTE = ("nuova", "presa_in_carico")


class ErroreSegnalazione(ValueError):
    pass


def _numero_bando(valore: str | None) -> int | None:
    m = re.fullmatch(r"\s*#?\s*(\d{1,9})\s*", valore or "")
    return int(m.group(1)) if m else None


def pulisci(d: dict) -> dict:
    """Controlla e pulisce una segnalazione: tipo noto, solo i campi del tipo, qualcosa di scritto."""
    tipo = (d.get("tipo") or "").strip()
    if tipo not in TIPI:
        raise ErroreSegnalazione("Scegli il tipo di segnalazione.")
    grezzi = d.get("dettagli") or {}
    if not isinstance(grezzi, dict):
        raise ErroreSegnalazione("Dettagli non validi.")
    dettagli = {k: str(grezzi[k]).strip()[:1000] for k in TIPI[tipo]["campi"] if str(grezzi.get(k) or "").strip()}
    testo = (d.get("testo") or "").strip()[:4000] or None
    bando_id = d.get("bando_id")
    if bando_id is not None and (not isinstance(bando_id, int) or bando_id <= 0):
        raise ErroreSegnalazione("Numero del bando non valido.")
    if bando_id is None:
        bando_id = _numero_bando(dettagli.get("bando"))
    pagina = (d.get("pagina") or "").strip()[:500] or None
    if tipo == "manca_bando" and not (dettagli.get("bando_nome") or dettagli.get("link")):
        raise ErroreSegnalazione("Scrivi il nome o il link del bando che manca.")
    if not testo and not dettagli:
        raise ErroreSegnalazione("Scrivi cosa vuoi segnalare.")
    return {"tipo": tipo, "testo": testo, "dettagli": dettagli, "bando_id": bando_id, "pagina": pagina}


def crea(conn, d: dict, utente: dict | None) -> dict:
    v = pulisci(d)
    with conn.cursor() as cur:
        if v["bando_id"] is not None:   # un numero che non e' un bando resta nei dettagli, senza collegamento
            cur.execute("SELECT 1 FROM bandi WHERE id = %s", (v["bando_id"],))
            if not cur.fetchone():
                v["dettagli"].setdefault("bando", str(v["bando_id"]))
                v["bando_id"] = None
        cur.execute("""INSERT INTO segnalazioni (tipo, testo, dettagli, bando_id, pagina, utente_id, ruolo)
                       VALUES (%s, %s, %s, %s, %s, %s, %s) RETURNING *""",
                    (v["tipo"], v["testo"], json.dumps(v["dettagli"]), v["bando_id"], v["pagina"],
                     utente["id"] if utente else None, utente["ruolo"] if utente else None))
        return dict(cur.fetchone())


def elenco(conn, stato: str | None = None, tipo: str | None = None, pagina: int = 1, per_pagina: int = 50,
           utente_id: int | None = None) -> dict:
    """Segnalazioni dalla piu' recente, le aperte prima. stato="aperte" = nuove e prese in carico."""
    condizioni, valori = [], []
    if utente_id:   # chi non ha il permesso "lavoro" vede solo le sue
        condizioni.append("s.utente_id = %s"); valori.append(utente_id)
    if stato == "aperte":
        condizioni.append("s.stato IN ('nuova', 'presa_in_carico')")
    elif stato:
        condizioni.append("s.stato = %s"); valori.append(stato)
    if tipo:
        condizioni.append("s.tipo = %s"); valori.append(tipo)
    dove = ("WHERE " + " AND ".join(condizioni)) if condizioni else ""
    with conn.cursor() as cur:
        cur.execute(f"SELECT count(*) AS n FROM segnalazioni s {dove}", valori)
        totale = cur.fetchone()["n"]
        cur.execute("""SELECT stato, tipo, count(*) AS n FROM segnalazioni WHERE %s::bigint IS NULL OR utente_id = %s
                       GROUP BY stato, tipo""", (utente_id, utente_id))
        conteggi = {s: 0 for s in STATI}
        aperte_per_tipo = {t: 0 for t in TIPI}
        for r in cur.fetchall():
            conteggi[r["stato"]] += r["n"]
            if r["stato"] in APERTE:
                aperte_per_tipo[r["tipo"]] += r["n"]
        cur.execute(
            f"""SELECT s.*, u.email, u.nome, b.titolo AS bando_titolo
                FROM segnalazioni s LEFT JOIN utenti u ON u.id = s.utente_id LEFT JOIN bandi b ON b.id = s.bando_id {dove}
                ORDER BY (s.stato IN ('nuova', 'presa_in_carico')) DESC, s.creata_il DESC, s.id DESC
                LIMIT %s OFFSET %s""", (*valori, per_pagina, (max(pagina, 1) - 1) * per_pagina))
        righe = [dict(r) for r in cur.fetchall()]
    return {"totale": totale, "conteggi": conteggi, "aperte_per_tipo": aperte_per_tipo, "pagina": pagina,
            "per_pagina": per_pagina, "segnalazioni": righe}


def gestisci(conn, segnalazione_id: int, stato: str, risposta: str | None, chi: str) -> dict:
    if stato not in STATI:
        raise ErroreSegnalazione("Stato non valido.")
    with conn.cursor() as cur:
        cur.execute("""UPDATE segnalazioni SET stato = %s, risposta = coalesce(%s, risposta), gestita_il = now(), gestita_da = %s
                       WHERE id = %s RETURNING *""", (stato, (risposta or "").strip()[:4000] or None, chi, segnalazione_id))
        r = cur.fetchone()
    if not r:
        raise ErroreSegnalazione("Segnalazione non trovata.")
    return dict(r)


def testo(segnalazioni: list[dict]) -> str:
    """Elenco leggibile per le sessioni di Claude Code: le segnalazioni aperte, dalla piu' recente."""
    righe = []
    for s in segnalazioni:
        dettagli = "; ".join(f"{TIPI[s['tipo']]['campi'].get(k, k)}: {v}" for k, v in (s.get("dettagli") or {}).items())
        intestazione = (f"- #{s['id']} [{TIPI[s['tipo']]['nome']}, {STATI[s['stato']]}] {s['creata_il']:%d/%m/%Y %H:%M}"
                        f" da {s.get('email') or 'utente cancellato'}" + (f" ({s['ruolo']})" if s.get("ruolo") else ""))
        corpo = [intestazione]
        if s.get("bando_id"):
            corpo.append(f"  bando {s['bando_id']}: {s.get('bando_titolo') or ''}".rstrip())
        if dettagli:
            corpo.append(f"  {dettagli}")
        if s.get("testo"):
            corpo.append(f"  {s['testo']}")
        if s.get("pagina"):
            corpo.append(f"  pagina: {s['pagina']}")
        righe.append("\n".join(corpo))
    return "\n".join(righe) or "Nessuna segnalazione aperta."
