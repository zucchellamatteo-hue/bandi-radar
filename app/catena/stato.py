"""A che punto e' ogni bando e ogni annuncio della fase 2, calcolato dai dati (niente stato a parte da tenere in
ordine). Serve alla pagina Lavorazione della plancia: imbuto, motivi di fermo, prossimo passo.
Per CONTARE o descrivere i bandi si usa invece la situazione (app/catena/situazione.py, vista bandi_situazione): una
sola voce per bando, con motivo, chi ha deciso e quando. Queste fasi restano per seguire la catena passo per passo."""

from __future__ import annotations

# (chiave, nome per Matteo, prossimo passo). L'ordine e' quello della catena.
FASI_BANDO = [
    ("pagina_da_cercare", "Pagina ufficiale da cercare", "ricerca della pagina al prossimo giro (50 per giro)"),
    ("pagina_non_trovata", "Pagina ufficiale non trovata", "si riprova dopo 14 giorni; serve una regola per la fonte"),
    ("documenti_da_scaricare", "Documenti da scaricare", "scaricamento al prossimo giro (25 per giro)"),
    ("filtro_da_fare", "Documenti da valutare", "filtro \"c'e' il bando?\" al prossimo giro"),
    ("in_disparte_sintesi", "In disparte: solo sintesi o pagine web", "nessuno: non si propone; si riguarda se arrivano documenti"),
    ("in_disparte_nessuno", "In disparte: nessun documento leggibile", "nessuno: non si propone"),
    ("preliminare_in_attesa", "Controllo preliminare in attesa (IA)", "prossimo lotto della Batch API"),
    ("fermato_chiuso", "Fermato: chiuso", "nessuno"),
    ("fermato_non_imprese", "Fermato: non per imprese", "nessuno"),
    ("fermato_edizione", "Fermato: edizione vecchia", "nessuno"),
    ("fermato_senza_testo", "Fermato: senza testo del bando", "si riguarda se arrivano documenti"),
    ("scheda_in_attesa", "Scheda in attesa", "prossima sessione di Claude Code (o l'API, se IA_SCHEDE_API=1)"),
    ("scheda_da_aggiornare", "Scheda da aggiornare", "nuova scheda al prossimo lotto"),
    ("proponibile", "Proponibile: scheda sul bando ufficiale", "abbinamento ai profili"),
    ("scheda_su_sintesi", "In disparte: scheda fatta su una sintesi", "nessuno: non si propone"),
]

FASE_BANDO_SQL = """CASE
    WHEN b.completezza IS NOT NULL AND b.preliminare->>'per_imprese' = 'no' THEN 'fermato_non_imprese'
    WHEN b.completezza = 'bando_ufficiale' AND b.da_aggiornare IS NOT NULL THEN 'scheda_da_aggiornare'
    WHEN b.completezza = 'bando_ufficiale' THEN 'proponibile'
    WHEN b.completezza IS NOT NULL THEN 'scheda_su_sintesi'
    WHEN b.pagina_stato IS NULL THEN 'pagina_da_cercare'
    WHEN b.pagina_stato = 'non_trovata' THEN 'pagina_non_trovata'
    WHEN b.allegati_cercati_il IS NULL THEN 'documenti_da_scaricare'
    WHEN b.preliminare IS NOT NULL AND b.preliminare->>'stato' = 'chiuso' THEN 'fermato_chiuso'
    WHEN b.preliminare IS NOT NULL AND b.preliminare->>'per_imprese' = 'no' THEN 'fermato_non_imprese'
    WHEN b.preliminare IS NOT NULL AND b.preliminare->>'edizione_in_corso' = 'no' THEN 'fermato_edizione'
    WHEN b.preliminare IS NOT NULL AND b.preliminare->>'testo_bando' = 'no' THEN 'fermato_senza_testo'
    WHEN b.documentazione IS NULL THEN 'filtro_da_fare'
    WHEN b.documentazione = 'sintesi' THEN 'in_disparte_sintesi'
    WHEN b.documentazione = 'nessuno' THEN 'in_disparte_nessuno'
    WHEN b.preliminare IS NULL THEN 'preliminare_in_attesa'
    ELSE 'scheda_in_attesa' END"""

FASI_ANNUNCIO = [
    ("da_smistare", "Da smistare", "regole al prossimo giro"),
    ("da_rivedere", "Da rivedere (in attesa dell'IA)", "prossimo lotto della Batch API; se l'IA resta incerta, va avanti"),
    ("doppione_dubbio", "Rilevante: forse doppione", "regole o IA al prossimo giro"),
    ("rilevante_senza_bando", "Rilevante, non ancora collegato", "deduplica al prossimo giro"),
    ("collegato", "Collegato a un bando", "segue il bando"),
    ("non_rilevante", "Non rilevante", "nessuno"),
]

FASE_ANNUNCIO_SQL = """CASE
    WHEN s.annuncio_id IS NULL THEN 'da_smistare'
    WHEN s.esito = 'da_rivedere' THEN 'da_rivedere'
    WHEN s.esito = 'non_rilevante' THEN 'non_rilevante'
    WHEN a.bando_id IS NOT NULL THEN 'collegato'
    WHEN EXISTS (SELECT 1 FROM bandi_dubbi d WHERE d.annuncio_id = a.id AND d.decisione IS NULL) THEN 'doppione_dubbio'
    ELSE 'rilevante_senza_bando' END"""

MOTIVO_BANDO_SQL = """CASE
    WHEN b.preliminare->>'per_imprese' = 'no' THEN b.preliminare->>'motivo'
    WHEN b.da_aggiornare IS NOT NULL THEN b.da_aggiornare
    WHEN b.completezza IS NOT NULL THEN NULL
    WHEN b.pagina_stato = 'non_trovata' THEN b.pagina_motivo
    WHEN b.preliminare IS NOT NULL THEN b.preliminare->>'motivo'
    ELSE b.documentazione_motivo END"""


def imbuto(conn) -> dict:
    with conn.cursor() as cur:
        cur.execute(f"SELECT {FASE_BANDO_SQL} AS fase, count(*) AS n FROM bandi b GROUP BY 1")
        bandi = {r["fase"]: r["n"] for r in cur.fetchall()}
        cur.execute(f"""SELECT {FASE_ANNUNCIO_SQL} AS fase, count(*) AS n
                        FROM annunci a LEFT JOIN smistamenti s ON s.annuncio_id = a.id GROUP BY 1""")
        annunci = {r["fase"]: r["n"] for r in cur.fetchall()}
        cur.execute("""SELECT quando, oggetto, oggetto_id, passo, esito, motivo FROM eventi_catena
                       ORDER BY id DESC LIMIT 60""")
        eventi = [dict(r) for r in cur.fetchall()]
        cur.execute("""SELECT count(*) FILTER (WHERE fatta_il >= date_trunc('month', now())) AS chiamate_mese,
                              coalesce(sum(costo_usd) FILTER (WHERE fatta_il >= date_trunc('month', now())), 0) AS costo_mese,
                              count(*) FILTER (WHERE esito = 'inviata') AS in_volo
                       FROM chiamate_ia""")
        ia = dict(cur.fetchone())
    return {
        "bandi": [{"fase": k, "nome": nome, "prossimo": p, "n": bandi.get(k, 0)} for k, nome, p in FASI_BANDO],
        "annunci": [{"fase": k, "nome": nome, "prossimo": p, "n": annunci.get(k, 0)} for k, nome, p in FASI_ANNUNCIO],
        "eventi": eventi, "ia": {**ia, "costo_mese": float(ia["costo_mese"])},
    }


def elenco(conn, tipo: str, fase: str, limite: int = 200) -> list[dict]:
    with conn.cursor() as cur:
        if tipo == "bandi":
            cur.execute(f"""SELECT b.id, b.titolo, b.ente, b.stato, b.scadenza, {MOTIVO_BANDO_SQL} AS motivo,
                                   greatest(b.aggiornato_il, b.pagina_cercata_il, b.allegati_cercati_il) AS ultimo
                            FROM bandi b WHERE {FASE_BANDO_SQL} = %s ORDER BY b.id DESC LIMIT %s""", (fase, limite))
        else:
            cur.execute(f"""SELECT a.id, a.titolo, f.nome AS fonte, a.trovato_il AS ultimo, s.motivo
                            FROM annunci a JOIN fonti f ON f.id = a.fonte_id LEFT JOIN smistamenti s ON s.annuncio_id = a.id
                            WHERE {FASE_ANNUNCIO_SQL} = %s ORDER BY a.id DESC LIMIT %s""", (fase, limite))
        return [dict(r) for r in cur.fetchall()]
