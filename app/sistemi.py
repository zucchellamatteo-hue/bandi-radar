"""I sistemi automatici di Bandi Radar: nome, spiegazione, programmazione, esecuzioni e dati (01/10/2026, richiesta di
Matteo). La pagina Supervisione della plancia li mostra tutti in un posto: cosa e' in corso, com'e' andata l'ultima
volta, quando riparte, e cliccando i dati di ognuno.

Ogni sistema che gira dentro il servizio `raccolta` registra le sue esecuzioni con `esecuzione("nome")` (tabella
`esecuzioni`). I sistemi fuori dai container (aggiornamento automatico, backup, sessioni di Claude Code) si descrivono
qui ma non scrivono esecuzioni: si vedono dal server.
"""

from __future__ import annotations

import traceback
from contextlib import contextmanager
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone


@dataclass
class Sistema:
    id: str
    nome: str
    spiegazione: str
    programmazione: str
    ogni_minuti: int | None = None        # per stimare la prossima esecuzione; None = non periodico o esterno
    gruppo: str = "Lavorazione"
    esterno: bool = False                 # fuori dal servizio raccolta: niente esecuzioni registrate
    dati: str | None = None               # chiave della query dei dati (DATI)


SISTEMI: list[Sistema] = [
    Sistema("raccolta", "Raccolta dalle fonti",
            "Controlla le circa 300 fonti del registro (Regioni, Camere di Commercio, Ministeri, UE, Comuni, catalogo "
            "incentivi.gov.it), ognuna nel modo che la sua piattaforma richiede (feed RSS, API, pagine web, browser) e "
            "alla sua frequenza; salva gli annunci nuovi. Una volta a settimana legge per intero la 'scorta' dei bandi "
            "ancora aperti.", "ogni ora", 60, "Raccolta", dati="controlli"),
    Sistema("regista", "Regista della lavorazione",
            "Dopo la raccolta porta avanti di un passo ogni annuncio e ogni bando, nell'ordine dei sistemi qui sotto; "
            "riprova quelli fermi e sblocca i blocchi. Il riepilogo dice quanti annunci ha mandato avanti, quanti doppioni "
            "ha deciso, quante schede vanno aggiornate.", "ogni ora, dopo la raccolta", 60, dati="giri"),
    Sistema("smistamento", "Smistamento",
            "Decide con le parole chiave se un annuncio parla di aiuti alle imprese (rilevante), no (non rilevante) o non "
            "si sa (da rivedere, poi all'IA). Gli incerti anche per l'IA vanno avanti: li filtrano i passi successivi.",
            "ogni ora, nel giro del regista", 60, dati="smistamenti"),
    Sistema("doppioni", "Doppioni",
            "Collega gli annunci che parlano dello stesso bando (stesso bando da piu' fonti, proroghe, graduatorie, FAQ). "
            "I casi chiari li decidono le regole, i dubbi l'IA (40 per giro); le decisioni di Matteo non si toccano.",
            "ogni ora, nel giro del regista", 60, dati="doppioni"),
    Sistema("pagine", "Pagina ufficiale",
            "Per ogni bando cerca la pagina ufficiale dell'ente con il testo del bando (regole per fonte nel registro). "
            "Se non la trova riprova dopo 14 giorni; dopo un errore di rete il giorno dopo.",
            "ogni ora, nel giro del regista (50 bandi)", 60, dati="pagine"),
    Sistema("documenti", "Documenti",
            "Scarica dalla pagina ufficiale il bando, i decreti, le FAQ e la modulistica, ne legge il testo (con l'OCR "
            "per le scansioni) e li conserva. Ogni 14 giorni ricontrolla i documenti dei bandi aperti con la scheda: se "
            "ne arrivano di nuovi, la scheda va aggiornata.", "ogni ora, nel giro del regista (25 bandi)", 60,
            dati="documenti"),
    Sistema("stato_pagine", "Ricontrollo dello stato",
            "Senza IA, una volta a settimana per ogni bando proponibile non chiuso: riscarica la pagina ufficiale, la "
            "confronta con quella salvata e cerca nelle righe nuove gli avvisi di chiusura ('piattaforma chiusa', "
            "'dotazione esaurita', 'bando chiuso'). Se ne trova uno, la scheda va aggiornata con il motivo.",
            "ogni ora, nel giro del regista (10 pagine)", 60, dati="stato_pagine"),
    Sistema("filtro", "C'e' il bando?",
            "Senza IA: guarda i documenti scaricati e decide se c'e' il testo ufficiale del bando. Solo quelli vanno "
            "all'IA per la scheda; gli altri (solo sintesi o pagine web) restano in disparte e non si propongono.",
            "ogni ora, nel giro del regista", 60, dati="filtro"),
    Sistema("ia", "IA (Batch API)",
            "Claude Opus 5.5 a meta' prezzo, risposte entro 24 ore: smista gli annunci 'da rivedere', fa il controllo "
            "preliminare (aperto? per imprese? c'e' il testo?) e scrive o aggiorna le schede. Un lotto alla volta, "
            "con il tetto di spesa del mese.", "ogni ora, nel giro del regista", 60, dati="ia"),
    Sistema("stato_bandi", "Stato dei bandi",
            "Ricalcola dalle date di ogni scheda se il bando e' aperto, in arrivo o chiuso. Ogni cambio resta nello "
            "storico del bando.", "una volta al giorno", 24 * 60, "Ogni giorno e ogni settimana", dati="stati"),
    Sistema("email_settimana", "Email del lunedi'",
            "Il lunedi' mattina manda a Matteo il riepilogo delle novita' della settimana e lo stato delle fonti.",
            "lunedi' dalle 7", 7 * 24 * 60, "Ogni giorno e ogni settimana", dati="email"),
    Sistema("aggiornamento", "Aggiornamento automatico del sito",
            "Sul server, ogni 5 minuti: scarica da GitHub la versione 'main' e, se e' cambiata, ricostruisce e riavvia i "
            "servizi. Unire una pull request vuol dire metterla in produzione entro pochi minuti.",
            "ogni 5 minuti (timer sul server)", None, "Sul server", True),
    Sistema("backup", "Backup notturno",
            "Sul server, ogni notte: copia del database. In piu' OVH fa il backup del disco intero.",
            "ogni notte (sul server)", None, "Sul server", True),
    Sistema("sessioni", "Sessioni di Claude Code e agenti",
            "Lavori fatti a mano con Claude Code (come gli arretrati di schede del 26-30/09): non sono automatici e "
            "partono solo quando Matteo apre una sessione. Le schede scritte cosi' sono riconoscibili.",
            "su richiesta", None, "Sul server", True, dati="sessioni"),
]
PER_ID = {s.id: s for s in SISTEMI}
INTERROTTA_DOPO = timedelta(hours=3)   # un'esecuzione "in corso" da piu' tempo e' stata interrotta (riavvio, errore)


@dataclass
class Esecuzione:
    id: int | None
    riepilogo: str | None = None
    numeri: dict = field(default_factory=dict)


@contextmanager
def esecuzione(sistema: str):
    """Registra inizio, fine, esito e riepilogo di un sistema. Non deve mai far fallire il lavoro: se il database non
    risponde, il lavoro va avanti senza registro."""
    from app.db.connessione import connetti

    e = Esecuzione(None)
    try:
        with connetti() as conn, conn.cursor() as cur:
            cur.execute("INSERT INTO esecuzioni (sistema) VALUES (%s) RETURNING id", (sistema,))
            e.id = cur.fetchone()["id"]
            conn.commit()
    except Exception:  # noqa: BLE001
        traceback.print_exc()
    errore = None
    try:
        yield e
    except Exception as exc:
        errore = f"{type(exc).__name__}: {exc}"[:2000]
        raise
    finally:
        if e.id is not None:
            riepilogo = e.riepilogo or (", ".join(f"{k} {v}" for k, v in e.numeri.items()) if e.numeri else None)
            try:
                with connetti() as conn, conn.cursor() as cur:
                    cur.execute("""UPDATE esecuzioni SET finito_il = now(), esito = %s, riepilogo = %s, errore = %s
                                   WHERE id = %s""", ("errore" if errore else "ok", riepilogo, errore, e.id))
                    conn.commit()
            except Exception:  # noqa: BLE001
                traceback.print_exc()


# --- dati di ogni sistema (cliccando nella pagina Supervisione) ------------------------------------------------
# Ogni voce: (titolo, query). Le colonne della query sono le colonne della tabella mostrata.
DATI: dict[str, tuple[str, str]] = {
    "controlli": ("Ultimi controlli delle fonti",
                  """SELECT c.iniziato_il AS quando, f.nome AS fonte, c.tipo, c.esito, c.elementi_letti AS letti,
                            c.novita, left(c.messaggio, 160) AS messaggio
                     FROM controlli c JOIN fonti f ON f.id = c.fonte_id ORDER BY c.iniziato_il DESC LIMIT 100"""),
    "giri": ("Ultimi giri del regista",
             """SELECT quando, esito, motivo AS riepilogo FROM eventi_catena WHERE oggetto = 'giro'
                ORDER BY id DESC LIMIT 50"""),
    "smistamenti": ("Ultime decisioni dello smistamento",
                    """SELECT s.deciso_il AS quando, left(a.titolo, 110) AS annuncio, s.esito, s.deciso_da AS da,
                              left(s.motivo, 140) AS motivo
                       FROM smistamenti s JOIN annunci a ON a.id = s.annuncio_id ORDER BY s.deciso_il DESC LIMIT 100"""),
    "doppioni": ("Ultimi doppioni decisi",
                 """SELECT e.quando, left(a.titolo, 110) AS annuncio, e.esito, left(e.motivo, 160) AS motivo
                    FROM eventi_catena e LEFT JOIN annunci a ON a.id = e.oggetto_id
                    WHERE e.passo = 'doppione' ORDER BY e.id DESC LIMIT 100"""),
    "pagine": ("Ultime ricerche della pagina ufficiale",
               """SELECT pagina_cercata_il AS quando, left(titolo, 110) AS bando, coalesce(pagina_stato, 'da riprovare') AS esito,
                         left(pagina_motivo, 160) AS motivo
                  FROM bandi WHERE pagina_cercata_il IS NOT NULL ORDER BY pagina_cercata_il DESC LIMIT 100"""),
    "documenti": ("Ultimi documenti scaricati",
                  """SELECT al.scaricato_il AS quando, left(b.titolo, 80) AS bando, left(al.nome, 80) AS documento,
                            al.categoria, coalesce(al.errore, 'ok') AS esito
                     FROM allegati al LEFT JOIN bandi b ON b.id = al.bando_id ORDER BY al.scaricato_il DESC LIMIT 100"""),
    "stato_pagine": ("Ultimi ricontrolli dello stato sulla pagina ufficiale",
                     """SELECT e.quando, left(b.titolo, 100) AS bando, e.esito, left(e.motivo, 200) AS motivo
                        FROM eventi_catena e LEFT JOIN bandi b ON b.id = e.oggetto_id
                        WHERE e.passo = 'ricontrollo stato' ORDER BY e.id DESC LIMIT 100"""),
    "filtro": ("Esito del filtro sui bandi",
               """SELECT coalesce(documentazione, 'non ancora valutati') AS esito, count(*) AS bandi,
                         count(*) FILTER (WHERE completezza = 'bando_ufficiale') AS con_scheda_proponibile
                  FROM bandi WHERE allegati_cercati_il IS NOT NULL GROUP BY 1 ORDER BY 2 DESC"""),
    "ia": ("Ultime chiamate all'IA",
           """SELECT fatta_il AS quando, scopo, CASE WHEN batch THEN 'batch' ELSE 'diretta' END AS modo, esito,
                     riferimento, round(costo_usd::numeric, 4) AS costo_dollari, left(messaggio, 120) AS messaggio
              FROM chiamate_ia ORDER BY id DESC LIMIT 100"""),
    "stati": ("Ultimi cambi di stato dei bandi",
              """SELECT v.salvata_il AS quando, left(b.titolo, 110) AS bando, b.stato AS stato_attuale, v.causa
                 FROM bandi_versioni v JOIN bandi b ON b.id = v.bando_id
                 WHERE v.causa ILIKE '%stato%' ORDER BY v.salvata_il DESC LIMIT 100"""),
    "email": ("Email inviate",
              "SELECT inviata_il AS quando, nome, chiave AS settimana, esito FROM notifiche_inviate ORDER BY inviata_il DESC LIMIT 50"),
    "sessioni": ("Schede per chi le ha scritte",
                 """SELECT coalesce(dati->>'modello', '?') AS scritte_da, count(*) AS schede,
                           count(*) FILTER (WHERE completezza = 'bando_ufficiale') AS sul_bando_ufficiale,
                           max(scheda_il) AS ultima
                    FROM bandi WHERE dati IS NOT NULL GROUP BY 1 ORDER BY 2 DESC"""),
}

# Numeri di sintesi mostrati nell'elenco, per ogni sistema.
NUMERI: dict[str, str] = {
    "raccolta": """SELECT format('%s fonti attive, %s in pausa; %s annunci nuovi nelle ultime 24 ore',
                          count(*) FILTER (WHERE NOT in_pausa AND stato = 'attiva'), count(*) FILTER (WHERE in_pausa),
                          (SELECT count(*) FROM annunci WHERE trovato_il > now() - interval '1 day' AND NOT da_scorta)) AS t FROM fonti""",
    "smistamento": """SELECT format('%s annunci da rivedere, %s da smistare',
                             count(*) FILTER (WHERE s.esito = 'da_rivedere'), count(*) FILTER (WHERE s.annuncio_id IS NULL)) AS t
                      FROM annunci a LEFT JOIN smistamenti s ON s.annuncio_id = a.id""",
    "doppioni": "SELECT format('%s doppioni dubbi da decidere', count(*)) AS t FROM bandi_dubbi WHERE decisione IS NULL",
    "pagine": """SELECT format('%s bandi da cercare, %s non trovati', count(*) FILTER (WHERE pagina_stato IS NULL),
                        count(*) FILTER (WHERE pagina_stato = 'non_trovata')) AS t FROM bandi""",
    "documenti": """SELECT format('%s bandi con documenti da scaricare; %s file in tutto',
                           (SELECT count(*) FROM bandi WHERE pagina_stato = 'trovata' AND allegati_cercati_il IS NULL),
                           count(*)) AS t FROM allegati WHERE errore IS NULL""",
    "stato_pagine": """SELECT format('%s proponibili da ricontrollare questa settimana, %s ricontrollati negli ultimi 7 giorni',
                              count(*) FILTER (WHERE stato_ricontrollato_il IS NULL OR stato_ricontrollato_il < now() - interval '7 days'),
                              count(*) FILTER (WHERE stato_ricontrollato_il >= now() - interval '7 days')) AS t
                       FROM bandi WHERE completezza = 'bando_ufficiale' AND coalesce(stato, '') <> 'chiuso'""",
    "filtro": """SELECT format('%s con il bando, %s solo sintesi, %s senza documenti', count(*) FILTER (WHERE documentazione = 'bando'),
                        count(*) FILTER (WHERE documentazione = 'sintesi'), count(*) FILTER (WHERE documentazione = 'nessuno')) AS t
                 FROM bandi""",
    "ia": """SELECT format('%s $ spesi nel mese; %s richieste in attesa di risposta',
                    round(coalesce(sum(costo_usd) FILTER (WHERE fatta_il >= date_trunc('month', now())), 0)::numeric, 2),
                    count(*) FILTER (WHERE esito = 'inviata')) AS t FROM chiamate_ia""",
    "stato_bandi": """SELECT format('%s aperti, %s in arrivo, %s chiusi (bandi con scheda)', count(*) FILTER (WHERE stato = 'aperto'),
                             count(*) FILTER (WHERE stato = 'in_arrivo'), count(*) FILTER (WHERE stato = 'chiuso')) AS t
                      FROM bandi WHERE dati IS NOT NULL""",
    "email_settimana": "SELECT format('ultima: %s', coalesce(max(inviata_il)::date::text, 'mai')) AS t FROM notifiche_inviate",
    "sessioni": """SELECT format('%s schede scritte in sessione', count(*)) AS t FROM bandi
                   WHERE dati->>'modello' ILIKE 'claude-code%'""",
}


def _stato(s: Sistema, ultima: dict | None, adesso: datetime) -> tuple[str, datetime | None]:
    """(stato, prossima esecuzione stimata)."""
    if s.esterno:
        return "esterno", None
    if not ultima:
        return "mai partito", None
    prossima = ultima["iniziato_il"] + timedelta(minutes=s.ogni_minuti) if s.ogni_minuti else None
    if ultima["esito"] == "in_corso":
        return ("interrotto" if adesso - ultima["iniziato_il"] > INTERROTTA_DOPO else "in corso"), prossima
    if prossima and adesso > prossima + timedelta(minutes=max(30, s.ogni_minuti // 2)):
        return "in ritardo", prossima
    return ultima["esito"], prossima


def elenco(conn) -> list[dict]:
    adesso = datetime.now(timezone.utc)
    with conn.cursor() as cur:
        cur.execute("""SELECT DISTINCT ON (sistema) sistema, id, iniziato_il, finito_il, esito, riepilogo, errore
                       FROM esecuzioni ORDER BY sistema, iniziato_il DESC""")
        ultime = {r["sistema"]: dict(r) for r in cur.fetchall()}
        cur.execute("""SELECT sistema, count(*) FILTER (WHERE esito = 'errore') AS errori, count(*) AS esecuzioni
                       FROM esecuzioni WHERE iniziato_il > now() - interval '1 day' GROUP BY 1""")
        giorno = {r["sistema"]: dict(r) for r in cur.fetchall()}
        numeri = {}
        for k, q in NUMERI.items():
            cur.execute(q)
            numeri[k] = cur.fetchone()["t"]
    risultato = []
    for s in SISTEMI:
        ultima = ultime.get(s.id)
        stato, prossima = _stato(s, ultima, adesso)
        risultato.append({
            "id": s.id, "nome": s.nome, "spiegazione": s.spiegazione, "programmazione": s.programmazione,
            "gruppo": s.gruppo, "esterno": s.esterno, "stato": stato, "prossima": prossima, "numeri": numeri.get(s.id),
            "ultima": ultima, "ultime_24_ore": giorno.get(s.id, {"errori": 0, "esecuzioni": 0}),
        })
    return risultato


def dettaglio(conn, sistema_id: str) -> dict | None:
    s = PER_ID.get(sistema_id)
    if not s:
        return None
    with conn.cursor() as cur:
        cur.execute("""SELECT id, iniziato_il, finito_il, esito, riepilogo, errore,
                              extract(epoch FROM (coalesce(finito_il, now()) - iniziato_il))::int AS secondi
                       FROM esecuzioni WHERE sistema = %s ORDER BY iniziato_il DESC LIMIT 50""", (sistema_id,))
        esecuzioni = [dict(r) for r in cur.fetchall()]
        dati = None
        if s.dati in DATI:
            titolo, query = DATI[s.dati]
            cur.execute(query)
            righe = [dict(r) for r in cur.fetchall()]
            colonne = [c.name for c in cur.description]
            dati = {"titolo": titolo, "colonne": colonne, "righe": righe}
    return {"id": s.id, "nome": s.nome, "spiegazione": s.spiegazione, "programmazione": s.programmazione,
            "esterno": s.esterno, "esecuzioni": esecuzioni, "dati": dati}
