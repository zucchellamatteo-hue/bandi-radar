"""La situazione di ogni bando: UNA voce per bando, calcolata in un solo posto (la vista SQL `bandi_situazione`,
migrazioni 028 e 031), con il perche' accanto: motivo, chi ha deciso, quando.

Per contare o descrivere i bandi (plancia, revisioni, sessioni, agenti) si usa SOLO questa: niente query improvvisate
su stato, completezza, documentazione o preliminare, che hanno fatto chiamare "senza scheda" bandi fermati come chiusi
o non per imprese (06/10/2026).

  python -m app.catena.situazione                          # conteggi per situazione e fase
  python -m app.catena.situazione --situazione scartato_chiuso [--fase chiuso] [--limite 50]
  python -m app.catena.situazione --bando 4092             # la situazione di un bando, con il perche'
"""

from __future__ import annotations

import argparse
import sys

# (chiave, nome per Matteo, spiegazione), nell'ordine in cui le mostra la plancia. Nella vista vince la prima
# condizione vera: unito, per_non_profit, fuori_target, poi le altre.
SITUAZIONI = [
    ("proponibile", "Proponibili",
     "scheda fatta sul bando ufficiale, documento verificato, secondo controllo fatto e senza problemi gravi, non "
     "chiuso: si propone alle imprese"),
    ("nascosto_per_errori", "Nascosti per errori",
     "scheda sul bando ufficiale con problemi gravi trovati dal controllo senza IA: non si propone finche' non e' sistemata"),
    ("in_disparte", "In disparte",
     "manca il testo ufficiale del bando: scheda fatta su una sintesi, o solo sintesi tra i documenti. Non si propone"),
    ("in_lavorazione", "In lavorazione", "ancora in catena: la fase dice dove (pagina, documenti, preliminare, scheda)"),
    ("per_non_profit", "Per il non profit",
     "non per imprese ma per associazioni, enti del Terzo settore, fondazioni, ASD/SSD, cooperative sociali: si "
     "mappano con priorita' piu' bassa (scheda dopo quelle per le imprese; con l'API solo se SCHEDE_NON_PROFIT=1)"),
    ("chiuso_con_scheda", "Chiusi, con scheda", "scheda fatta, ma il bando ora e' chiuso: resta nello storico"),
    ("scartato_chiuso", "Scartati: chiusi",
     "fermati prima della scheda perche' chiusi o edizione passata (segnali gratuiti, IA o sessione)"),
    ("fuori_target", "Fuori target",
     "non per imprese ne' per il non profit: solo enti pubblici o persone fisiche, oppure non e' un'agevolazione "
     "(gara, concorso, elenco fornitori). Anche se ha una scheda"),
    ("scartato_altro", "Scartati: altri motivi", "fermati prima della scheda: nessun testo del bando da leggere"),
    ("unito", "Uniti ad altri", "doppioni: i loro annunci sono passati a un altro bando, restano solo come storico"),
]
NOMI = {k: n for k, n, _ in SITUAZIONI}

# Fase dentro la situazione: (nome, prossimo passo).
FASI = {
    "scheda_pronta": ("Scheda pronta", "abbinamento ai profili"),
    "scheda_da_aggiornare": ("Scheda da aggiornare", "nuova scheda al prossimo lotto; intanto si propone la vecchia"),
    "problemi_gravi": ("Problemi gravi nella scheda", "correggere la scheda (pagina Lavorazione, Da rivedere)"),
    # Procedura nuova del regista (app/catena/procedura.py, migrazione 036)
    "documento_non_valido": ("Documento non valido: da recuperare", "cercare il testo ufficiale giusto "
                             "(python -m app.catena.procedura --da-recuperare)"),
    "documento_da_verificare": ("Documento da verificare", "verifica del documento (preliminare dell'IA o sessione)"),
    "secondo_controllo_da_fare": ("Secondo controllo da fare", "verifica della scheda in sessione"),
    "errori_da_correggere": ("Errori gravi del secondo controllo", "correggere la scheda (applica_verifica.py)"),
    "scheda_solo_sintesi": ("Scheda fatta su una sintesi", "si riguarda se arriva il testo ufficiale"),
    "scheda_nessun_documento": ("Scheda fatta senza documenti", "si riguarda se arrivano documenti"),
    "senza_scheda_sintesi": ("Solo sintesi o pagine web tra i documenti", "si riguarda se arrivano documenti"),
    "senza_scheda_nessuno": ("Nessun documento leggibile", "si riguarda se arrivano documenti"),
    "pagina_da_cercare": ("Pagina ufficiale da cercare", "ricerca della pagina al prossimo giro"),
    "pagina_non_trovata": ("Pagina ufficiale non trovata", "si riprova dopo 14 giorni; serve una regola per la fonte"),
    "documenti_da_scaricare": ("Documenti da scaricare", "scaricamento al prossimo giro"),
    "filtro_da_fare": ("Documenti da valutare", "filtro \"c'e' il bando?\" al prossimo giro"),
    "preliminare_in_coda": ("Controllo preliminare in coda", "prossimo lotto (API o sessione)"),
    "seconda_lettura_in_coda": ("Seconda lettura in coda", "l'IA rilegge: diceva chiuso, la fonte dice aperto"),
    "scheda_in_coda": ("Scheda in coda", "prossimo lotto (API o sessione)"),
    "scaduto": ("Scaduto", "nessuno"),
    "chiusura_anticipata": ("Chiuso prima della scadenza", "nessuno"),
    "chiuso": ("Chiuso", "nessuno"),
    "edizione_passata": ("Edizione passata", "nessuno"),
    "senza_testo_del_bando": ("Nessun testo del bando", "si riguarda se arrivano documenti"),
    "scheda_non_profit_in_coda": ("Scheda in coda (non profit)", "dopo le schede per le imprese: in sessione, o con "
                                  "l'API se SCHEDE_NON_PROFIT=1"),
    "non_profit_con_scheda": ("Scheda fatta (non profit)", "nel catalogo con il filtro Destinatari: non profit e ai "
                              "profili di enti del Terzo settore"),
    "non_profit_scheda_su_sintesi": ("Scheda fatta su una sintesi (non profit)", "si riguarda se arriva il testo ufficiale"),
    "non_profit_senza_testo": ("Senza testo del bando (non profit)", "si riguarda se arrivano documenti"),
    "non_profit_chiuso": ("Chiuso (non profit)", "nessuno"),
    "destinatari_da_determinare": ("Destinatari da determinare", "deciso prima del 07/10 solo come \"non per imprese\": "
                                   "lo script di derivazione o un nuovo controllo preliminare dira' se e' per il non profit"),
    "non_agevolazione": ("Non e' un'agevolazione", "nessuno (gara, concorso, elenco fornitori, avviso)"),
    "prima_della_scheda": ("Fermato prima della scheda", "nessuno"),
    "dopo_la_scheda": ("Scheda fatta, poi esclusa", "nessuno: la scheda resta nello storico"),
    "unito": ("Unito a un altro bando", "nessuno"),
}

# Chi ha deciso (colonna deciso_da della vista).
CHI = {"regole": "regole (senza IA)", "segnali": "segnali gratuiti (senza IA)", "ia": "IA (API)",
       "sessione": "sessione di Claude Code", "matteo": "Matteo"}


def conteggi(conn) -> dict:
    """Totale, e per ogni situazione il numero e le fasi (le fasi solo se piu' di una)."""
    with conn.cursor() as cur:
        cur.execute("SELECT situazione, fase, count(*) AS n FROM bandi_situazione GROUP BY 1, 2")
        righe = cur.fetchall()
    per: dict[str, dict] = {k: {"situazione": k, "nome": n, "spiegazione": s, "n": 0, "fasi": []} for k, n, s in SITUAZIONI}
    for r in righe:
        voce = per[r["situazione"]]
        voce["n"] += r["n"]
        nome, prossimo = FASI.get(r["fase"], (r["fase"], ""))
        voce["fasi"].append({"fase": r["fase"], "nome": nome, "prossimo": prossimo, "n": r["n"]})
    for voce in per.values():
        voce["fasi"].sort(key=lambda f: -f["n"])
    return {"totale": sum(v["n"] for v in per.values()), "situazioni": list(per.values())}


def elenco(conn, situazione: str, fase: str | None = None, limite: int = 200) -> list[dict]:
    """I bandi in una situazione (e fase), i piu' recenti per decisione, con motivo, chi ha deciso e quando."""
    with conn.cursor() as cur:
        cur.execute("""SELECT id, titolo, ente, stato, scadenza, situazione, fase, motivo, deciso_da, deciso_il, unito_a
                       FROM bandi_situazione WHERE situazione = %s AND (%s::text IS NULL OR fase = %s)
                       ORDER BY deciso_il DESC NULLS LAST, id DESC LIMIT %s""", (situazione, fase, fase, limite))
        return [_con_nomi(dict(r)) for r in cur.fetchall()]


def di_un_bando(conn, bando_id: int) -> dict | None:
    with conn.cursor() as cur:
        cur.execute("SELECT * FROM bandi_situazione WHERE id = %s", (bando_id,))
        r = cur.fetchone()
    return _con_nomi(dict(r)) if r else None


def _con_nomi(r: dict) -> dict:
    r["nome_situazione"] = NOMI.get(r["situazione"], r["situazione"])
    r["nome_fase"], r["prossimo"] = FASI.get(r["fase"], (r["fase"], ""))
    r["chi"] = CHI.get(r["deciso_da"], r["deciso_da"])
    return r


def main(argomenti: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Situazione dei bandi (vista bandi_situazione).")
    p.add_argument("--situazione", choices=list(NOMI))
    p.add_argument("--fase")
    p.add_argument("--limite", type=int, default=50)
    p.add_argument("--bando", type=int)
    a = p.parse_args(argomenti)

    from app.db.connessione import connetti

    with connetti() as conn:
        if a.bando:
            r = di_un_bando(conn, a.bando)
            if not r:
                print(f"Bando {a.bando} non trovato.")
                return 1
            print(f"[{r['id']}] {r['titolo']}\n  situazione: {r['nome_situazione']} ({r['situazione']}) · fase: {r['nome_fase']}"
                  f"\n  motivo: {r['motivo'] or '-'}\n  deciso da: {r['chi'] or '-'} · quando: {_quando(r['deciso_il'])}"
                  f"\n  prossimo passo: {r['prossimo'] or '-'}")
            return 0
        if a.situazione:
            righe = elenco(conn, a.situazione, a.fase, a.limite)
            print(f"{NOMI[a.situazione]}{' / ' + FASI.get(a.fase, (a.fase,))[0] if a.fase else ''}: "
                  f"{len(righe)} mostrati (al massimo {a.limite}, i piu' recenti)")
            for r in righe:
                print(f"[{r['id']}] {r['titolo'][:90]}\n    {r['nome_fase']} · {r['chi'] or '-'} · {_quando(r['deciso_il'])}"
                      f" · {(r['motivo'] or '-')[:200]}")
            return 0
        c = conteggi(conn)
    print(f"Bandi: {c['totale']}")
    for v in c["situazioni"]:
        print(f"  {v['n']:>6}  {v['nome']} ({v['situazione']}): {v['spiegazione']}")
        if len(v["fasi"]) > 1:
            for f in v["fasi"]:
                print(f"  {'':>6}    {f['n']:>6}  {f['nome']} ({f['fase']})")
    return 0


def _quando(d) -> str:
    return d.strftime("%d/%m/%Y %H:%M") if d else "-"


if __name__ == "__main__":
    sys.exit(main())
