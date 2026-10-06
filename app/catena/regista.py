"""Il regista della fase 2 (01/10/2026, richiesta di Matteo; docs/ORCHESTRAZIONE.md).

Ogni ora, dopo la raccolta, porta avanti annunci e bandi di un passo e sblocca quelli fermi:
  1. smistamento a regole degli annunci nuovi;
  2. ripiego: gli annunci che nemmeno l'IA ha saputo classificare vanno avanti come possibili bandi (li filtrano
     gratis "c'e' il bando?" e poi il controllo preliminare);
  3. deduplica, poi sblocco dei doppioni dubbi: titoli quasi uguali dello stesso ente = stesso bando, titoli poco
     simili = bandi diversi, graduatorie o proroghe di un bando che non abbiamo = archiviate, i "simili" all'IA;
  4. pagina ufficiale (i "non trovati" si riprovano dopo 14 giorni) e documenti;
  5. ricontrollo dei documenti dei bandi aperti con la scheda (ogni 14 giorni): se ne arrivano di nuovi, la scheda
     va aggiornata; lo stesso se arriva una proroga, una rettifica o una chiusura;
  6. filtro "c'e' il bando?" (senza IA);
  7. IA con la Batch API: risposte arrivate, smistamento dei "da rivedere", controlli preliminari, schede nuove e
     schede da aggiornare (solo bandi con il testo ufficiale).
Le decisioni di Matteo non si toccano mai. Ogni azione resta in `eventi_catena` (pagina Lavorazione della plancia).
"""

from __future__ import annotations

import os
import re
import sys
from app.db.blocchi import con_blocco

SOGLIA_STESSO = 0.9            # titoli quasi uguali: con lo stesso ente e' lo stesso bando
SOGLIA_DIVERSO = 0.5           # sotto: bandi diversi. Tra le due soglie decide l'IA (gestore ed ente danno titoli diversi
                               # allo stesso bando: Fincalabra e Regione Calabria, FILSE e Regione Liguria, a 0,6-0,7)
DOPPIONI_IA_PER_GIRO = 40      # chiamate dirette, poche e piccole
RICONTROLLO_GIORNI = 14        # documenti dei bandi aperti, pagine non trovate
RICONTROLLI_PER_GIRO = 5


def evento(cur, oggetto: str, oggetto_id: int | None, passo: str, esito: str, motivo: str | None = None) -> None:
    cur.execute("INSERT INTO eventi_catena (oggetto, oggetto_id, passo, esito, motivo) VALUES (%s, %s, %s, %s, %s)",
                (oggetto, oggetto_id, passo, esito, (motivo or "")[:500] or None))


# --- 2. ripiego per gli incerti dell'IA ----------------------------------------------------------------

def ripiego_da_rivedere(conn) -> int:
    """Gli annunci "da_rivedere" anche per l'IA diventano "rilevanti": meglio guardarli che perderli. Costano poco:
    pagina e documenti sono gratis, e se tra i documenti non c'e' un bando si fermano al filtro senza IA.
    La proposta dell'IA resta nelle colonne proposta_*; le decisioni di Matteo non si toccano."""
    with conn.cursor() as cur:
        cur.execute("""UPDATE smistamenti SET proposta_esito = esito, proposta_motivo = motivo, proposta_da = deciso_da,
                              esito = 'rilevante', deciso_da = 'regole', deciso_il = now(),
                              motivo = 'incerto anche per l''IA: mandato avanti, lo filtrano i documenti e il controllo preliminare'
                       WHERE esito = 'da_rivedere' AND deciso_da = 'ia' RETURNING annuncio_id""")
        ids = [r["annuncio_id"] for r in cur.fetchall()]
        for i in ids:
            evento(cur, "annuncio", i, "smistamento", "rilevante", "ripiego: incerto anche per l'IA")
    conn.commit()
    return len(ids)


# --- 3. doppioni dubbi --------------------------------------------------------------------------------

def _dubbi_aperti(conn) -> list[dict]:
    with conn.cursor() as cur:
        cur.execute("""SELECT DISTINCT ON (d.annuncio_id) d.id, d.annuncio_id, d.bando_id, d.somiglianza, d.motivo,
                              a.titolo, a.url, a.riassunto, a.ruolo, fa.nome AS fonte, fa.ente,
                              b.titolo AS bando_titolo, b.ente AS bando_ente, b.url AS bando_url, b.sintesi AS bando_sintesi,
                              (SELECT ao.riassunto FROM annunci ao WHERE ao.id = b.annuncio_id) AS bando_riassunto,
                              (SELECT fo.ente FROM annunci ao JOIN fonti fo ON fo.id = ao.fonte_id WHERE ao.id = b.annuncio_id)
                                  AS bando_ente_fonte
                       FROM bandi_dubbi d JOIN annunci a ON a.id = d.annuncio_id JOIN fonti fa ON fa.id = a.fonte_id
                       LEFT JOIN bandi b ON b.id = d.bando_id
                       WHERE d.decisione IS NULL AND a.collegato_da IS DISTINCT FROM 'matteo'
                       ORDER BY d.annuncio_id, d.somiglianza DESC NULLS LAST""")
        return [dict(r) for r in cur.fetchall()]


_ANNO = re.compile(r"\b(20[12]\d)\b")
_EDIZIONE = re.compile(r"\b(prim|second|terz|quart|quint)[ao] edizione\b|\b[ivx]+ edizione\b|\bedizione \d+\b|\b\d+[°ªa] edizione\b",
                       re.IGNORECASE)


def edizioni_diverse(a: str, b: str) -> bool:
    """Anni o edizioni diversi nei titoli ("Riapri Calabria - Seconda edizione" e "Riapri Calabria"): non decidono
    le regole, anche con titoli quasi uguali."""
    anni_a, anni_b = set(_ANNO.findall(a)), set(_ANNO.findall(b))
    if anni_a and anni_b and not anni_a & anni_b:
        return True
    ed_a, ed_b = {m.group(0).lower() for m in _EDIZIONE.finditer(a)}, {m.group(0).lower() for m in _EDIZIONE.finditer(b)}
    return ed_a != ed_b


def decisione_regole(d: dict) -> tuple[str, str] | None:
    """('stesso'|'diverso'|'archivia', motivo) se le regole bastano, None se serve l'IA."""
    from app.schede.bandi import ente_normalizzato

    if d["bando_id"] is None:
        return "archivia", "aggiornamento (graduatoria, proroga...) di un bando che non abbiamo"
    s = float(d["somiglianza"] or 0)
    stesso_ente = ente_normalizzato(d["ente"]) == ente_normalizzato(d["bando_ente_fonte"] or d["bando_ente"])
    if s >= SOGLIA_STESSO and stesso_ente and not edizioni_diverse(d["titolo"], d["bando_titolo"] or ""):
        return "stesso", f"titoli quasi uguali ({s:.2f}) e stesso ente"
    if s < SOGLIA_DIVERSO:
        return "diverso", f"titoli poco simili ({s:.2f})"
    return None


def chiedi_ia(client, d: dict, registra) -> tuple[str, str] | None:
    from app.schede import ia

    istruzioni, modello = ia.leggi_prompt("prompt_doppione.md")
    messaggio = ia.riempi(modello, {
        "titolo_annuncio": d["titolo"], "fonte_annuncio": d["fonte"], "ente_annuncio": d["ente"], "url_annuncio": d["url"],
        "testo_annuncio": (d["riassunto"] or "")[:3000], "titolo_bando": d["bando_titolo"], "ente_bando": d["bando_ente"],
        "url_bando": d["bando_url"], "testo_bando": (d["bando_sintesi"] or d["bando_riassunto"] or "")[:3000]})
    schema = {"type": "object", "additionalProperties": False, "required": ["stesso", "motivo"],
              "properties": {"stesso": {"type": "boolean"}, "motivo": {"type": "string"}}}
    r = ia.chiama(client, ia.parametri(ia.MODELLO_PRELIMINARE, istruzioni, messaggio, schema, 4000, "low"))
    registra("doppione", ia.MODELLO_PRELIMINARE, f"doppione-{d['annuncio_id']}-{d['bando_id']}", r)
    if r.dati is None:
        return None
    return ("stesso" if r.dati.get("stesso") else "diverso"), "IA: " + str(r.dati.get("motivo") or "")[:200]


@con_blocco("doppioni", {"stesso": 0, "diverso": 0, "archivia": 0, "ia": 0, "in_attesa": 0})
def sblocca_dubbi(conn, usa_ia: bool, limite_ia: int = DOPPIONI_IA_PER_GIRO) -> dict:
    from app.schede import ia
    from app.schede.bandi import decidi_collegamento

    conteggi = {"stesso": 0, "diverso": 0, "archivia": 0, "ia": 0, "in_attesa": 0}
    client = registra = None
    for d in _dubbi_aperti(conn):
        decisione, da = decisione_regole(d), "regole"
        if decisione is None:
            if not usa_ia or conteggi["ia"] >= limite_ia:
                conteggi["in_attesa"] += 1
                continue
            try:
                if client is None:
                    client, registra = ia.nuovo_client(), ia.registratore(conn)
                ia.controlla_tetto(conn)
            except ia.IASpenta as exc:
                print(exc)
                usa_ia = False
                conteggi["in_attesa"] += 1
                continue
            conteggi["ia"] += 1
            decisione, da = chiedi_ia(client, d, registra), "ia"
            if decisione is None:
                conteggi["in_attesa"] += 1
                continue
        esito, motivo = decisione
        if esito == "archivia":
            with conn.cursor() as cur:
                cur.execute("""UPDATE bandi_dubbi SET decisione = 'diverso', deciso_da = 'regole', deciso_il = now()
                               WHERE annuncio_id = %s AND decisione IS NULL""", (d["annuncio_id"],))
                cur.execute("""UPDATE smistamenti SET proposta_esito = esito, proposta_motivo = motivo, proposta_da = deciso_da,
                                      esito = 'non_rilevante', deciso_da = 'regole', deciso_il = now(), motivo = %s
                               WHERE annuncio_id = %s AND deciso_da <> 'matteo'""", (f"archiviato: {motivo}", d["annuncio_id"]))
                evento(cur, "annuncio", d["annuncio_id"], "doppione", "archiviato", motivo)
            conn.commit()
        else:
            bando = decidi_collegamento(conn, d["annuncio_id"], d["bando_id"] if esito == "stesso" else None, da, motivo)
            with conn.cursor() as cur:
                evento(cur, "annuncio", d["annuncio_id"], "doppione", f"{esito} ({da})", f"bando {bando}: {motivo}")
            conn.commit()
        conteggi[esito] += 1
    return conteggi


# --- 5. ricontrollo dei documenti e schede da aggiornare -------------------------------------------------

def _documenti_utili(cur, bando_id: int) -> set[str]:
    cur.execute("""SELECT impronta FROM allegati WHERE bando_id = %s AND errore IS NULL AND impronta IS NOT NULL
                   AND categoria IS DISTINCT FROM 'modulistica'""", (bando_id,))
    return {r["impronta"] for r in cur.fetchall()}


@con_blocco("ricontrollo", 0)
def ricontrolla_documenti(conn, limite: int = RICONTROLLI_PER_GIRO) -> int:
    """Bandi aperti o in arrivo con la scheda e i documenti guardati piu' di RICONTROLLO_GIORNI fa: si riapre la
    pagina ufficiale e si scaricano i documenti nuovi. Se ce ne sono, la scheda va aggiornata."""
    from app.schede import allegati

    with conn.cursor() as cur:
        cur.execute("""SELECT id FROM bandi WHERE dati IS NOT NULL AND stato IN ('aperto', 'in_arrivo') AND unito_a IS NULL
                       AND pagina_stato = 'trovata' AND da_aggiornare IS NULL
                       AND allegati_cercati_il < now() - make_interval(days => %s)
                       ORDER BY allegati_cercati_il LIMIT %s""", (RICONTROLLO_GIORNI, limite))
        ids = [r["id"] for r in cur.fetchall()]
    nuovi_bandi = 0
    for bando_id in ids:
        with conn.cursor() as cur:
            prima = _documenti_utili(cur, bando_id)
        allegati.esegui(bando_id=bando_id)
        with conn.cursor() as cur:
            nuovi = _documenti_utili(cur, bando_id) - prima
            cur.execute("UPDATE bandi SET allegati_cercati_il = now() WHERE id = %s", (bando_id,))
            if nuovi:
                nuovi_bandi += 1
                cur.execute("UPDATE bandi SET da_aggiornare = %s, documentazione = NULL WHERE id = %s",
                            (f"{len(nuovi)} documenti nuovi sulla pagina ufficiale", bando_id))
            evento(cur, "bando", bando_id, "ricontrollo documenti", f"{len(nuovi)} nuovi")
        conn.commit()
    return nuovi_bandi


@con_blocco("ricontrollo_stato", {})
def ricontrolla_stato(conn, modulo) -> dict:
    """Pagine ufficiali dei bandi proponibili non chiusi, una volta a settimana: un avviso di chiusura comparso dopo
    la scheda la rende "da aggiornare" (app/schede/ricontrollo_stato.py)."""
    return modulo.ricontrolla(conn, modulo.da_ricontrollare(conn))


def segna_aggiornamenti(conn) -> int:
    """Proroghe, rettifiche, chiusure e FAQ collegate al bando dopo la scheda: la scheda va aggiornata."""
    with conn.cursor() as cur:
        cur.execute("""UPDATE bandi b SET da_aggiornare = sub.motivo
                       FROM (SELECT a.bando_id, string_agg(DISTINCT a.ruolo, ', ') AS motivo FROM annunci a JOIN bandi x ON x.id = a.bando_id
                             WHERE x.dati IS NOT NULL AND x.da_aggiornare IS NULL AND a.ruolo IN ('proroga', 'rettifica', 'chiusura', 'faq')
                               AND a.collegato_il > coalesce(x.scheda_il, x.aggiornato_il)
                             GROUP BY a.bando_id) sub
                       WHERE b.id = sub.bando_id RETURNING b.id, b.da_aggiornare""")
        righe = cur.fetchall()
        for r in righe:
            evento(cur, "bando", r["id"], "aggiornamento", "scheda da aggiornare", f"arrivato: {r['da_aggiornare']}")
    conn.commit()
    return len(righe)


# --- il giro --------------------------------------------------------------------------------------------

def _conta(sql: str, *parametri) -> dict:
    from app.db.connessione import connetti

    with connetti() as conn, conn.cursor() as cur:
        cur.execute(sql, parametri)
        return dict(cur.fetchone())


def _passo(sistema: str, lavoro) -> None:
    """Un passo del giro, registrato nella Supervisione (app/sistemi.py). Se fallisce, il giro va avanti."""
    import traceback
    from datetime import datetime, timezone

    from app.sistemi import esecuzione

    try:
        with esecuzione(sistema) as e:
            e.riepilogo = lavoro(datetime.now(timezone.utc))
    except Exception:  # noqa: BLE001 - un passo rotto non ferma gli altri
        traceback.print_exc()


@con_blocco("regista", {})
def giro() -> dict:
    from app.db.connessione import connetti
    from app.schede import allegati, bandi, documentazione, ia, pagina_ufficiale, smista
    from app.sistemi import esecuzione

    riepilogo: dict = {}

    def smistamento(inizio):
        smista.esegui(n_esempi=0)
        with connetti() as conn:
            riepilogo["ripiego"] = ripiego_da_rivedere(conn)
        n = _conta("SELECT count(*) FILTER (WHERE esito = 'rilevante') AS r, count(*) FILTER (WHERE esito = 'non_rilevante') AS nr, "
                   "count(*) FILTER (WHERE esito = 'da_rivedere') AS dr FROM smistamenti WHERE deciso_il >= %s", inizio)
        return (f"{n['r']} rilevanti, {n['nr']} non rilevanti, {n['dr']} da rivedere "
                f"(di cui {riepilogo['ripiego']} incerti dell'IA mandati avanti)")

    def doppioni(inizio):
        bandi.esegui(n_esempi=0)
        with connetti() as conn:
            c = riepilogo["doppioni"] = sblocca_dubbi(conn, usa_ia=ia.chiave_presente())
        bandi.esegui(n_esempi=0)        # gli annunci appena sbloccati diventano bandi
        return (f"{c['stesso']} uniti a un bando, {c['diverso']} bandi nuovi, {c['archivia']} archiviati "
                f"({c['ia']} decisi dall'IA); {c['in_attesa']} ancora da decidere")

    def pagine(inizio):
        pagina_ufficiale.esegui(limite=int(os.environ.get("CATENA_PAGINE_PER_GIRO", "50")))
        n = _conta("SELECT count(*) FILTER (WHERE pagina_stato = 'trovata') AS t, count(*) FILTER (WHERE pagina_stato = 'non_trovata') AS nt, "
                   "count(*) FILTER (WHERE pagina_stato IS NULL) AS r FROM bandi WHERE pagina_cercata_il >= %s", inizio)
        return f"{n['t']} pagine trovate, {n['nt']} non trovate, {n['r']} errori di rete (si riprova)"

    def documenti(inizio):
        allegati.esegui(limite=int(os.environ.get("CATENA_ALLEGATI_PER_GIRO", "25")))
        with connetti() as conn:
            riepilogo["documenti_nuovi"] = ricontrolla_documenti(conn)
            riepilogo["schede_da_aggiornare"] = segna_aggiornamenti(conn)
        n = _conta("SELECT count(DISTINCT bando_id) AS b, count(*) FILTER (WHERE errore IS NULL) AS f, "
                   "count(*) FILTER (WHERE errore IS NOT NULL) AS e FROM allegati WHERE scaricato_il >= %s", inizio)
        return (f"{n['f']} file scaricati per {n['b']} bandi ({n['e']} non scaricati); ricontrollo: "
                f"{riepilogo['documenti_nuovi']} bandi con documenti nuovi; {riepilogo['schede_da_aggiornare']} schede da aggiornare")

    def stato_pagine(inizio):
        from app.schede import ricontrollo_stato

        with connetti() as conn:
            c = riepilogo["ricontrollo_stato"] = ricontrolla_stato(conn, ricontrollo_stato)
        if not c:
            return "saltato: un altro ricontrollo e' in corso"
        return (f"{c['controllati']} pagine ufficiali ricontrollate, {c['chiusure']} con un possibile avviso di chiusura "
                f"(scheda da aggiornare), {c['cambiati']} cambiate, {c['errori']} non scaricate")

    def filtro(inizio):
        prima = _conta("SELECT count(*) AS n FROM bandi WHERE allegati_cercati_il IS NOT NULL AND documentazione IS NULL")["n"]
        documentazione.esegui()
        return f"{prima} bandi valutati"

    def intelligenza(inizio):
        if not ia.chiave_presente():
            return "spenta: manca la chiave API"
        preliminari = 0
        with connetti() as conn:
            try:
                ia.cmd_raccogli(conn)
                # Dal 05/10 (prodotto indipendente) il lavoro pesante va a lotti, a meta' prezzo: anche i controlli
                # preliminari, che dal 02/10 partivano con chiamate dirette. Con IA_PRELIMINARI_DIRETTI=1 si torna
                # alle chiamate dirette (la scheda parte nello stesso giro, ma costa il doppio).
                if os.environ.get("IA_PRELIMINARI_DIRETTI", "0") == "1":
                    preliminari = ia.cmd_preliminari_diretti(conn)
                # Un lotto in volo per tipo (prima uno solo per tutto: un lotto di smistamento bloccava le schede
                # per 13 ore). Il costo resta sotto controllo con il tetto, che conta anche i lotti in volo.
                in_volo = ia.scopi_in_volo(conn)
                if "smistamento" not in in_volo:
                    ia.cmd_smista(conn, int(os.environ.get("CATENA_SMISTA_PER_GIRO", "100")), batch=True)
                # Le schede con l'API solo se IA_SCHEDE_API=1 nel .env (decisione di Matteo del 02/10: finche' il
                # servizio non e' venduto le schede si scrivono nelle sessioni di Claude Code, a costo zero). Senza,
                # il lotto porta solo controlli preliminari e seconde letture.
                if not in_volo & {"preliminare", "scheda"}:
                    if os.environ.get("IA_SCHEDE_API", "0") == "1":
                        ia.cmd_schede_batch(conn)
                    else:
                        ia.cmd_schede_batch(conn, limite_schede=0)
            except ia.IASpenta as exc:
                return f"{preliminari} controlli preliminari diretti; IA fermata: {exc}"
        n = _conta("SELECT count(*) FILTER (WHERE esito = 'inviata') AS inviate, count(*) FILTER (WHERE esito <> 'inviata') AS altre, "
                   "coalesce(sum(costo_usd), 0) AS costo FROM chiamate_ia WHERE fatta_il >= %s", inizio)
        return (f"{preliminari} controlli preliminari diretti; {n['inviate']} richieste mandate alla Batch API, "
                f"{n['altre']} risposte registrate, {float(n['costo']):.2f} $")

    with esecuzione("regista") as giro_intero:
        def controlli_schede(inizio):
            from app.schede import controlli

            with connetti() as conn:
                c = riepilogo["controlli"] = controlli.controlla(conn)
            return f"{c['controllati']} schede controllate: {c['con_gravi']} con problemi gravi, {c['da_migliorare']} da migliorare"

        for nome, lavoro in (("smistamento", smistamento), ("doppioni", doppioni), ("pagine", pagine),
                             ("documenti", documenti), ("stato_pagine", stato_pagine), ("filtro", filtro),
                             ("ia", intelligenza), ("controllo_schede", controlli_schede)):
            _passo(nome, lavoro)
        giro_intero.riepilogo = (f"{riepilogo.get('ripiego', 0)} incerti mandati avanti; doppioni: "
                                 f"{riepilogo.get('doppioni', {})}; {riepilogo.get('schede_da_aggiornare', 0)} schede da aggiornare")
        with connetti() as conn, conn.cursor() as cur:
            evento(cur, "giro", None, "giro", "fatto", str(riepilogo))
            conn.commit()
    print("Regista:", riepilogo)
    return riepilogo


def main() -> int:
    giro()
    return 0


if __name__ == "__main__":
    sys.exit(main())
