"""Feedback sulle schede (05/10/2026): voto e problemi da revisori e imprese, correzioni decise dagli agenti.

Flusso: chi legge la scheda vota e segnala (pagina del bando) -> l'admin vede tutto nella pagina Feedback ->
gli agenti delle sessioni rileggono i documenti (strumenti/sessione/ar/esporta_feedback.py, ISTRUZIONI_FEEDBACK.md)
-> importa_feedback.py applica le correzioni accettate con applica_correzioni() e segna lo stato.
"""

from __future__ import annotations

import json

CATEGORIE = {
    "stato_sbagliato": "stato sbagliato (aperto/chiuso)",
    "non_per_imprese": "non è per imprese",
    "importo_percentuale": "importo o percentuale",
    "beneficiari": "beneficiari",
    "territorio": "territorio",
    "ateco": "codici ATECO",
    "scadenza": "scadenza o date",
    "documento_mancante": "documento mancante",
    "altro": "altro",
}
STATI = ("nuovo", "preso_in_carico", "corretto", "respinto")
PESO = {"admin": 2, "revisore": 2, "impresa": 1}   # le segnalazioni dei revisori pesano piu' di quelle delle imprese


class ErroreFeedback(ValueError):
    pass


def pulisci_problemi(problemi: list[dict]) -> list[dict]:
    puliti = []
    for p in problemi or []:
        categoria = (p.get("categoria") or "").strip()
        if categoria not in CATEGORIE:
            raise ErroreFeedback(f"Categoria non valida: {categoria!r}.")
        testo = (p.get("testo") or "").strip()[:2000] or None
        campo = (p.get("campo") or "").strip()[:60] or None
        if categoria == "altro" and not testo:
            raise ErroreFeedback("Per un problema \"altro\" scrivi cosa non va.")
        puliti.append({"categoria": categoria, "campo": campo, "testo": testo})
    return puliti[:20]


def salva(conn, bando_id: int, utente: dict, voto: int | None, problemi: list[dict], commento: str | None) -> dict:
    """Voto e problemi dell'utente sulla versione attuale della scheda (li sostituisce se c'erano gia').
    Una segnalazione "stato sbagliato" fa ricontrollare la pagina ufficiale al prossimo giro del regista."""
    if voto is not None and not 1 <= voto <= 5:
        raise ErroreFeedback("Il voto va da 1 a 5.")
    problemi = pulisci_problemi(problemi)
    commento = (commento or "").strip()[:4000] or None
    if voto is None and not problemi and not commento:
        raise ErroreFeedback("Dai un voto o segnala almeno un problema.")
    with conn.cursor() as cur:
        cur.execute("SELECT id, versione, dati IS NOT NULL AS ha_scheda FROM bandi WHERE id = %s", (bando_id,))
        b = cur.fetchone()
        if not b:
            raise ErroreFeedback("Bando non trovato.")
        if not b["ha_scheda"]:
            raise ErroreFeedback("Questo bando non ha ancora una scheda da giudicare.")
        cur.execute(
            """INSERT INTO feedback (bando_id, versione, utente_id, ruolo, voto, problemi, commento)
               VALUES (%s, %s, %s, %s, %s, %s, %s)
               ON CONFLICT (bando_id, versione, utente_id) DO UPDATE SET
                 ruolo = EXCLUDED.ruolo, voto = EXCLUDED.voto, problemi = EXCLUDED.problemi, commento = EXCLUDED.commento,
                 aggiornato_il = now(),
                 -- se cambia cosa si segnala, torna da guardare
                 stato = CASE WHEN feedback.problemi IS DISTINCT FROM EXCLUDED.problemi
                                OR feedback.commento IS DISTINCT FROM EXCLUDED.commento THEN 'nuovo' ELSE feedback.stato END
               RETURNING *""",
            (bando_id, b["versione"], utente["id"], utente["ruolo"], voto, json.dumps(problemi), commento))
        r = dict(cur.fetchone())
        if any(p["categoria"] == "stato_sbagliato" for p in problemi):
            # Il ricontrollo (app/schede/ricontrollo_stato.py) prende per primi i bandi mai ricontrollati.
            cur.execute("UPDATE bandi SET stato_ricontrollato_il = NULL WHERE id = %s", (bando_id,))
    return r


def del_bando(conn, bando_id: int, utente: dict) -> dict:
    """Il feedback dell'utente sulla versione attuale e, per l'admin, quelli di tutti (con chi li ha scritti)."""
    with conn.cursor() as cur:
        cur.execute("SELECT versione FROM bandi WHERE id = %s", (bando_id,))
        b = cur.fetchone()
        if not b:
            raise ErroreFeedback("Bando non trovato.")
        cur.execute("SELECT * FROM feedback WHERE bando_id = %s AND utente_id = %s ORDER BY versione DESC LIMIT 1",
                    (bando_id, utente["id"]))
        mio = cur.fetchone()
        tutti = []
        if utente["ruolo"] == "admin":
            cur.execute("""SELECT f.*, u.email, u.nome FROM feedback f JOIN utenti u ON u.id = f.utente_id
                           WHERE f.bando_id = %s ORDER BY f.versione DESC, f.aggiornato_il DESC""", (bando_id,))
            tutti = [dict(r) for r in cur.fetchall()]
    return {"versione": b["versione"], "mio": dict(mio) if mio else None, "tutti": tutti,
            "categorie": CATEGORIE}


def elenco(conn, stato: str | None = None, ruolo: str | None = None, categoria: str | None = None,
           bando_id: int | None = None, pagina: int = 1, per_pagina: int = 50, utente_id: int | None = None) -> dict:
    condizioni, valori = [], []
    if utente_id:   # il revisore vede solo i suoi giudizi
        condizioni.append("f.utente_id = %s"); valori.append(utente_id)
    if stato:
        condizioni.append("f.stato = %s"); valori.append(stato)
    if ruolo:
        condizioni.append("f.ruolo = %s"); valori.append(ruolo)
    if categoria:
        condizioni.append("f.problemi @> %s::jsonb"); valori.append(json.dumps([{"categoria": categoria}]))
    if bando_id:
        condizioni.append("f.bando_id = %s"); valori.append(bando_id)
    dove = ("WHERE " + " AND ".join(condizioni)) if condizioni else ""
    with conn.cursor() as cur:
        cur.execute(f"SELECT count(*) AS n FROM feedback f {dove}", valori)
        totale = cur.fetchone()["n"]
        cur.execute("SELECT stato, count(*) AS n FROM feedback WHERE %s::bigint IS NULL OR utente_id = %s GROUP BY stato",
                    (utente_id, utente_id))
        conteggi = {s: 0 for s in STATI} | {r["stato"]: r["n"] for r in cur.fetchall()}
        cur.execute(
            f"""SELECT f.*, u.email, u.nome, b.titolo, b.ente, b.versione AS versione_attuale, b.qualita
                FROM feedback f JOIN utenti u ON u.id = f.utente_id JOIN bandi b ON b.id = f.bando_id {dove}
                ORDER BY (f.stato = 'nuovo') DESC, CASE f.ruolo WHEN 'impresa' THEN 1 ELSE 0 END, f.aggiornato_il DESC
                LIMIT %s OFFSET %s""", (*valori, per_pagina, (max(pagina, 1) - 1) * per_pagina))
        righe = [dict(r) | {"peso": PESO.get(r["ruolo"], 1)} for r in cur.fetchall()]
    return {"totale": totale, "conteggi": conteggi, "pagina": pagina, "per_pagina": per_pagina, "feedback": righe}


def gestisci(conn, feedback_id: int, stato: str, risposta: str | None, chi: str) -> dict:
    if stato not in STATI:
        raise ErroreFeedback("Stato non valido.")
    with conn.cursor() as cur:
        cur.execute("""UPDATE feedback SET stato = %s, risposta = coalesce(%s, risposta), gestito_il = now(), gestito_da = %s
                       WHERE id = %s RETURNING *""", (stato, (risposta or "").strip() or None, chi, feedback_id))
        r = cur.fetchone()
    if not r:
        raise ErroreFeedback("Feedback non trovato.")
    return dict(r)


def applica_correzioni(conn, bando_id: int, correzioni: list[dict], causa: str) -> list[str]:
    """Applica alla scheda le correzioni accettate [{campo, valore, citazione}] con la stessa pulizia delle schede
    (app/schede/ia.prepara_scheda): i valori fuori elenco si tolgono e si segnalano. Ritorna i problemi trovati.
    Il cambio finisce nello storico delle versioni con la causa indicata."""
    from datetime import date

    from app.schede import campi, ia

    with conn.cursor() as cur:
        cur.execute("SELECT dati FROM bandi WHERE id = %s FOR UPDATE", (bando_id,))
        b = cur.fetchone()
    if not b or not b["dati"] or not isinstance(b["dati"].get("risposta"), dict):
        raise ErroreFeedback(f"Il bando {bando_id} non ha una scheda da correggere.")
    risposta = dict(b["dati"]["risposta"])
    for c in correzioni:
        campo = c.get("campo")
        if campo not in ia.SCHEMA_SCHEDA["properties"] or campo in ("fonti", "url"):
            raise ErroreFeedback(f"Campo della scheda sconosciuto: {campo!r}.")
        risposta[campo] = c.get("valore")
    scheda, tolti = ia.prepara_scheda(risposta)
    for c in correzioni:   # un valore corretto che la pulizia ha tolto e' un errore dell'agente: non si salva niente
        if any(t.startswith(f"{c['campo']}:") for t in tolti):
            raise ErroreFeedback(f"Valore non ammesso per {c['campo']}: {c.get('valore')!r} ({'; '.join(tolti)}).")
    valori = {col: scheda.get(col) for col in ia._COLONNE_SCHEDA}
    for col in ("vincoli", "linee", *ia._DETTAGLI_SCHEDA):
        valori[col] = json.dumps(valori[col]) if valori[col] is not None else None
    dati = dict(b["dati"])
    dati["risposta"] = scheda
    dati["fonti"] = dict(dati.get("fonti") or {}) | {c["campo"]: c.get("citazione") for c in correzioni if c.get("citazione")}
    dati["correzioni_feedback"] = [*(dati.get("correzioni_feedback") or []),
                                   *({"campo": c["campo"], "valore": c.get("valore"), "citazione": c.get("citazione"),
                                      "causa": causa} for c in correzioni)]
    # Lo stato lo calcola il sistema dalle date (app/schede/stato.py): si ricalcola qui, nello stesso salvataggio,
    # cosi' la correzione e' una sola versione e non si fa commit a meta' (decide chi chiama).
    oggi = date.today()
    valori["stato"] = campi.calcola_stato(ia._data(scheda.get("data_apertura")), ia._data(scheda.get("scadenza")), oggi,
                                          ia._data(scheda.get("chiuso_il")))
    assegnazioni = ", ".join(f"{col} = %s" for col in valori)
    with conn.cursor() as cur:
        cur.execute("SELECT set_config('bandi_radar.causa', %s, true)", (causa[:300],))
        cur.execute(f"UPDATE bandi SET {assegnazioni}, stato_calcolato_il = %s, dati = %s WHERE id = %s",
                    (*valori.values(), oggi, json.dumps(dati), bando_id))
    return ia.verifica_scheda(scheda)
