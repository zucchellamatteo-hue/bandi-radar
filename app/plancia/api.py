"""API della plancia. Tutte le rotte sono sotto /api e protette dall'autenticazione base dell'app."""

from __future__ import annotations

import threading
from datetime import date, datetime, timedelta, timezone

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

from app.db.connessione import connetti
from app.plancia import semaforo

router = APIRouter(prefix="/api")

# Dove le varie fonti scrivono la scadenza nei dati grezzi (chiavi viste nelle API del registro).
SCADENZA_SQL = """coalesce(
    a.dati->>'scadenza', a.dati->>'data_chiusura', a.dati->>'dataScadenza', a.dati->>'deadlineDate',
    a.dati->>'publish_down', a.dati->>'chiusura_adesione', a.dati->>'news_end_date', a.dati->>'scadenza_bando',
    a.dati->>'data_scadenza', a.dati->>'expires', a.dati->'attributes'->>'data_scadenza')"""

ESITI_STORICO = 5


def _righe(cur) -> list[dict]:
    return [dict(r) for r in cur.fetchall()]


@router.get("/riepilogo")
def riepilogo() -> dict:
    """I numeri in cima alla plancia: fonti per colore, annunci recenti, allarmi."""
    fonti = elenco_fonti()
    colori = {"verde": 0, "giallo": 0, "rosso": 0, "pausa": 0}
    for f in fonti:
        colori[f["colore"]] += 1
    with connetti() as conn, conn.cursor() as cur:
        cur.execute("SELECT count(*) AS n FROM annunci WHERE trovato_il > now() - interval '7 days'")
        ultimi_7 = cur.fetchone()["n"]
        cur.execute("SELECT count(*) AS n FROM annunci")
        totale = cur.fetchone()["n"]
        cur.execute("SELECT max(iniziato_il) AS ultimo FROM controlli")
        ultimo = cur.fetchone()["ultimo"]
    allarmi = [{"fonte_id": f["id"], "nome": f["nome"], "colore": f["colore"], "motivo": f["motivo"]}
               for f in fonti if f["colore"] == "rosso"]
    return {"fonti": colori, "annunci_ultimi_7_giorni": ultimi_7, "annunci_totali": totale,
            "ultimo_controllo": ultimo, "allarmi": allarmi}


@router.get("/fonti")
def elenco_fonti() -> list[dict]:
    """Una riga per fonte con semaforo, ultimo controllo, ultima novita', silenzio, novita' 30/90 giorni."""
    adesso = datetime.now(timezone.utc)
    with connetti() as conn, conn.cursor() as cur:
        cur.execute("SELECT * FROM fonti ORDER BY tipo, territorio, nome")
        fonti = _righe(cur)
        cur.execute(
            """
            SELECT fonte_id, array_agg(esito ORDER BY iniziato_il DESC) AS esiti,
                   max(iniziato_il) AS ultimo_controllo
            FROM (SELECT fonte_id, esito, iniziato_il,
                         row_number() OVER (PARTITION BY fonte_id ORDER BY iniziato_il DESC) AS n
                  FROM controlli) c
            WHERE n <= %s GROUP BY fonte_id
            """,
            (ESITI_STORICO,),
        )
        storico = {r["fonte_id"]: r for r in cur.fetchall()}
        cur.execute(
            """
            SELECT DISTINCT ON (fonte_id) fonte_id, esito, messaggio, iniziato_il, durata_ms, elementi_letti, novita
            FROM controlli ORDER BY fonte_id, iniziato_il DESC
            """
        )
        ultimi = {r["fonte_id"]: r for r in cur.fetchall()}
        cur.execute(
            """
            SELECT fonte_id, max(coalesce(pubblicato_il, trovato_il)) AS ultima, max(trovato_il) AS ultima_trovata,
                   count(*) FILTER (WHERE trovato_il > now() - interval '30 days') AS n30,
                   count(*) FILTER (WHERE trovato_il > now() - interval '90 days') AS n90,
                   (array_agg(titolo ORDER BY trovato_il DESC))[1] AS ultimo_titolo
            FROM annunci GROUP BY fonte_id
            """
        )
        novita = {r["fonte_id"]: r for r in cur.fetchall()}
    risultato = []
    for f in fonti:
        s = storico.get(f["id"])
        u = ultimi.get(f["id"])
        n = novita.get(f["id"])
        stato = semaforo.calcola(f["frequenza"], f["stato"], f["in_pausa"], list(s["esiti"]) if s else [],
                                 n["ultima_trovata"] if n else None, adesso)
        risultato.append({
            **{k: f[k] for k in ("id", "nome", "ente", "tipo", "territorio", "url", "modalita", "frequenza", "stato", "in_pausa", "piattaforma")},
            "colore": stato.colore, "motivo": stato.motivo,
            "silenzio_giorni": stato.silenzio_giorni, "soglia_silenzio_giorni": stato.soglia_silenzio_giorni,
            "ultimo_controllo": u["iniziato_il"] if u else None,
            "ultimo_esito": u["esito"] if u else None,
            "ultimo_messaggio": u["messaggio"] if u else None,
            "ultima_novita": n["ultima_trovata"] if n else None,
            "ultimo_titolo": n["ultimo_titolo"] if n else None,
            "novita_30": n["n30"] if n else 0, "novita_90": n["n90"] if n else 0,
        })
    return risultato


@router.get("/fonti/{fonte_id}")
def dettaglio_fonte(fonte_id: str) -> dict:
    with connetti() as conn, conn.cursor() as cur:
        cur.execute("SELECT * FROM fonti WHERE id = %s", (fonte_id,))
        fonte = cur.fetchone()
        if not fonte:
            raise HTTPException(404, "fonte non trovata")
        cur.execute("SELECT * FROM controlli WHERE fonte_id = %s ORDER BY iniziato_il DESC LIMIT 50", (fonte_id,))
        controlli = _righe(cur)
        cur.execute("SELECT id, url, titolo, riassunto, pubblicato_il, trovato_il FROM annunci WHERE fonte_id = %s ORDER BY trovato_il DESC LIMIT 50", (fonte_id,))
        annunci = _righe(cur)
    return {"fonte": dict(fonte), "controlli": controlli, "annunci": annunci}


class Pausa(BaseModel):
    in_pausa: bool


@router.post("/fonti/{fonte_id}/pausa")
def metti_in_pausa(fonte_id: str, corpo: Pausa) -> dict:
    with connetti() as conn, conn.cursor() as cur:
        cur.execute("UPDATE fonti SET in_pausa = %s WHERE id = %s RETURNING id", (corpo.in_pausa, fonte_id))
        if not cur.fetchone():
            raise HTTPException(404, "fonte non trovata")
        conn.commit()
    return {"id": fonte_id, "in_pausa": corpo.in_pausa}


_rilanci_in_corso: set[str] = set()


def _rilancia(fonte_id: str) -> None:
    from app.raccolta.esegui import esegui

    try:
        esegui(selezione=fonte_id)
    finally:
        _rilanci_in_corso.discard(fonte_id)


@router.post("/fonti/{fonte_id}/rilancia")
def rilancia(fonte_id: str) -> dict:
    """Controlla la fonte adesso, in sottofondo. La riga della plancia si aggiorna al prossimo caricamento."""
    with connetti() as conn, conn.cursor() as cur:
        cur.execute("SELECT 1 FROM fonti WHERE id = %s", (fonte_id,))
        if not cur.fetchone():
            raise HTTPException(404, "fonte non trovata")
    if fonte_id in _rilanci_in_corso:
        return {"id": fonte_id, "stato": "gia' in corso"}
    _rilanci_in_corso.add(fonte_id)
    threading.Thread(target=_rilancia, args=(fonte_id,), daemon=True).start()
    return {"id": fonte_id, "stato": "avviato"}


@router.get("/annunci")
def catalogo(
    q: str | None = None, tipo: str | None = None, territorio: str | None = None, fonte: str | None = None,
    da: date | None = None, a: date | None = None, scadenza_entro: int | None = Query(None, ge=1, le=365),
    pagina: int = Query(1, ge=1), per_pagina: int = Query(50, ge=1, le=200),
) -> dict:
    """Catalogo degli annunci con filtri. I filtri su ATECO, dimensione ecc. arrivano con le schede (Fase 3)."""
    condizioni, valori = [], []
    if q:
        condizioni.append("(a.titolo ILIKE %s OR a.riassunto ILIKE %s OR f.ente ILIKE %s)")
        valori += [f"%{q}%"] * 3
    if tipo:
        condizioni.append("f.tipo = %s"); valori.append(tipo)
    if territorio:
        condizioni.append("f.territorio = %s"); valori.append(territorio)
    if fonte:
        condizioni.append("a.fonte_id = %s"); valori.append(fonte)
    if da:
        condizioni.append("coalesce(a.pubblicato_il, a.trovato_il) >= %s"); valori.append(da)
    if a:
        condizioni.append("coalesce(a.pubblicato_il, a.trovato_il) < %s"); valori.append(a + timedelta(days=1))
    if scadenza_entro:
        condizioni.append(f"data_sicura({SCADENZA_SQL}) BETWEEN current_date AND current_date + %s")
        valori.append(scadenza_entro)
    dove = ("WHERE " + " AND ".join(condizioni)) if condizioni else ""
    with connetti() as conn, conn.cursor() as cur:
        cur.execute(f"SELECT count(*) AS n FROM annunci a JOIN fonti f ON f.id = a.fonte_id {dove}", valori)
        totale = cur.fetchone()["n"]
        cur.execute(
            f"""
            SELECT a.id, a.fonte_id, f.nome AS fonte, f.ente, f.tipo, f.territorio, a.url, a.titolo, a.riassunto,
                   a.pubblicato_il, a.trovato_il, data_sicura({SCADENZA_SQL}) AS scadenza
            FROM annunci a JOIN fonti f ON f.id = a.fonte_id {dove}
            ORDER BY coalesce(a.pubblicato_il, a.trovato_il) DESC, a.id DESC
            LIMIT %s OFFSET %s
            """,
            valori + [per_pagina, (pagina - 1) * per_pagina],
        )
        righe = _righe(cur)
        cur.execute("SELECT DISTINCT territorio FROM fonti ORDER BY territorio")
        territori = [r["territorio"] for r in cur.fetchall()]
    return {"totale": totale, "pagina": pagina, "per_pagina": per_pagina, "annunci": righe, "territori": territori}


@router.get("/annunci/{annuncio_id}")
def dettaglio_annuncio(annuncio_id: int) -> dict:
    with connetti() as conn, conn.cursor() as cur:
        cur.execute(
            """
            SELECT a.*, f.nome AS fonte, f.ente, f.tipo, f.territorio, f.url AS fonte_url
            FROM annunci a JOIN fonti f ON f.id = a.fonte_id WHERE a.id = %s
            """,
            (annuncio_id,),
        )
        riga = cur.fetchone()
    if not riga:
        raise HTTPException(404, "annuncio non trovato")
    return dict(riga)


@router.get("/novita/settimane")
def settimane() -> list[dict]:
    """Le settimane con novita', dalla piu' recente: la pagina 'Novita'' stile blog."""
    with connetti() as conn, conn.cursor() as cur:
        cur.execute(
            """
            SELECT to_char(date_trunc('week', trovato_il), 'IYYY-"W"IW') AS chiave,
                   date_trunc('week', trovato_il)::date AS inizio, count(*) AS n, count(DISTINCT fonte_id) AS fonti
            FROM annunci GROUP BY 1, 2 ORDER BY 2 DESC LIMIT 52
            """
        )
        return _righe(cur)


@router.get("/novita/settimane/{chiave}")
def settimana(chiave: str) -> dict:
    """Le novita' di una settimana (chiave come 2026-W39), raggruppate per tipo di fonte."""
    try:
        anno, sett = chiave.split("-W")
        inizio = date.fromisocalendar(int(anno), int(sett), 1)
    except ValueError:
        raise HTTPException(400, "chiave settimana non valida (es. 2026-W39)")
    fine = inizio + timedelta(days=7)
    with connetti() as conn, conn.cursor() as cur:
        cur.execute(
            f"""
            SELECT a.id, a.fonte_id, f.nome AS fonte, f.ente, f.tipo, f.territorio, a.url, a.titolo, a.riassunto,
                   a.pubblicato_il, a.trovato_il, data_sicura({SCADENZA_SQL}) AS scadenza
            FROM annunci a JOIN fonti f ON f.id = a.fonte_id
            WHERE a.trovato_il >= %s AND a.trovato_il < %s
            ORDER BY f.tipo, coalesce(a.pubblicato_il, a.trovato_il) DESC
            """,
            (inizio, fine),
        )
        righe = _righe(cur)
    gruppi: dict[str, list] = {}
    for r in righe:
        gruppi.setdefault(r["tipo"], []).append(r)
    return {"chiave": chiave, "inizio": inizio, "fine": fine - timedelta(days=1), "totale": len(righe),
            "gruppi": [{"tipo": t, "annunci": v} for t, v in gruppi.items()]}
