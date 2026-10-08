"""Procedura nuova del regista (08/10/2026, PIANO_QUALITA azione 0, via di Matteo).

Un bando si propone alle imprese solo dopo quattro passi, in quest'ordine:
  1. tipo di agevolazione (bandi.tipo_procedura): misura di legge, sportello a regole fisse o bando vero; dice qual e'
     il documento giusto (la norma o la circolare; il decreto nel testo in vigore; l'avviso di questa edizione);
  2. verifica del documento (bandi.verifica_documento): tra i documenti c'e' davvero quel testo, di questo bando,
     dell'edizione in corso, approvato? Se no, il bando va nella lista "da recuperare" con il motivo;
  3. scheda solo con il documento verificato;
  4. secondo controllo della scheda con il testo del bando (bandi.secondo_controllo), obbligatorio; gli errori gravi
     vanno corretti prima di proporre.

Questo modulo dice, per ogni bando con la scheda sul bando ufficiale, a che punto e' della procedura (`esito`) e conta
quanti proponibili di oggi cambierebbero con la regola nuova (`ripasso`). Finche' la regola non e' accesa (migrazione a
parte, dopo il via di Matteo) non cambia niente di cio' che vedono le imprese.

  python -m app.catena.procedura                       # ripasso dei proponibili con la regola nuova
  python -m app.catena.procedura --da-recuperare       # bandi aperti senza documento verificato, con il motivo
  python -m app.catena.procedura --bando 4092
"""

from __future__ import annotations

import argparse
import sys
from datetime import datetime

TIPI = {
    "misura_di_legge": "misura di legge (vale per chi ha i requisiti, senza bando)",
    "sportello": "sportello a regole fisse (domanda finche' ci sono fondi)",
    "bando": "bando con la sua edizione e scadenza",
}

PROBLEMI_DOCUMENTO = {
    "manca": "manca il testo ufficiale tra i documenti",
    "solo_sintesi": "solo pagine di sintesi o notizie",
    "altro_bando": "il documento e' di un altro bando",
    "edizione_vecchia": "il documento e' di un'edizione passata",
    "bozza": "il documento e' una bozza o una consultazione",
    "atto_generico": "legge, decreto o circolare che non contiene le regole del bando",
    "graduatoria": "solo graduatorie, elenchi o impegni",
}

# (chiave, nome per Matteo, prossimo passo). L'ordine e' quello della procedura.
ESITI = [
    ("documento_da_verificare", "Documento da verificare", "verifica del documento (sessione, o controllo preliminare dell'IA)"),
    ("da_recuperare", "Da recuperare: documento non valido", "cercare il testo ufficiale giusto (lista da recuperare)"),
    ("secondo_controllo_da_fare", "Secondo controllo da fare", "verifica della scheda in sessione (ISTRUZIONI_VERIFICA_IA.md)"),
    ("errori_da_correggere", "Errori gravi da correggere", "applica_verifica.py, poi importa_verifica.py --corrette"),
    ("pronto", "Pronto: si propone", "abbinamento ai profili"),
]
NOMI = {k: n for k, n, _ in ESITI}


def _data(v) -> datetime | None:
    if v is None or isinstance(v, datetime):
        return v
    return datetime.fromisoformat(str(v))


def esito(b: dict) -> tuple[str, str]:
    """(esito, motivo) della procedura per un bando con la scheda: colonne verifica_documento, secondo_controllo,
    scheda_il. Uguale a ESITO_SQL (controllato dai test)."""
    vd = b.get("verifica_documento") or {}
    if vd.get("verificato") not in ("si", "no"):
        return "documento_da_verificare", "nessuno ha ancora verificato che il documento sia il testo ufficiale giusto"
    if vd["verificato"] == "no":
        problema = PROBLEMI_DOCUMENTO.get(vd.get("problema") or "", vd.get("problema") or "documento non valido")
        return "da_recuperare", problema + (f": {vd['motivo']}" if vd.get("motivo") else "")
    sc = b.get("secondo_controllo") or {}
    fatto, scheda = _data(sc.get("fatto_il")), _data(b.get("scheda_il"))
    if not sc.get("esito") or not fatto:
        return "secondo_controllo_da_fare", "scheda mai controllata con il testo del bando"
    if scheda and fatto < scheda:
        return "secondo_controllo_da_fare", "scheda rifatta dopo l'ultimo secondo controllo"
    if sc["esito"] == "grave" and not sc.get("correzioni_applicate"):
        return "errori_da_correggere", f"{sc.get('gravi') or 'alcuni'} errori gravi trovati dal secondo controllo"
    return "pronto", "documento verificato e scheda controllata"


ESITO_SQL = """CASE
    WHEN coalesce(b.verifica_documento->>'verificato', '') NOT IN ('si', 'no') THEN 'documento_da_verificare'
    WHEN b.verifica_documento->>'verificato' = 'no' THEN 'da_recuperare'
    WHEN b.secondo_controllo->>'esito' IS NULL OR b.secondo_controllo->>'fatto_il' IS NULL THEN 'secondo_controllo_da_fare'
    WHEN b.scheda_il IS NOT NULL AND (b.secondo_controllo->>'fatto_il')::timestamptz < b.scheda_il
         THEN 'secondo_controllo_da_fare'
    WHEN b.secondo_controllo->>'esito' = 'grave'
         AND coalesce(b.secondo_controllo->>'correzioni_applicate', 'false') <> 'true' THEN 'errori_da_correggere'
    ELSE 'pronto' END"""


def ripasso(conn) -> dict:
    """I proponibili di oggi (vista bandi_situazione) passati con la regola nuova: quanti restano, quanti escono e
    perche', e i tipi di agevolazione."""
    with conn.cursor() as cur:
        cur.execute(f"""SELECT {ESITO_SQL} AS esito, coalesce(b.tipo_procedura, 'non_noto') AS tipo, count(*) AS n
                        FROM bandi_situazione s JOIN bandi b ON b.id = s.id
                        WHERE s.situazione = 'proponibile' GROUP BY 1, 2""")
        righe = cur.fetchall()
    per_esito = {k: 0 for k, _, _ in ESITI}
    per_tipo: dict[str, int] = {}
    for r in righe:
        per_esito[r["esito"]] += r["n"]
        per_tipo[r["tipo"]] = per_tipo.get(r["tipo"], 0) + r["n"]
    totale = sum(per_esito.values())
    return {"proponibili_oggi": totale, "restano": per_esito["pronto"], "escono": totale - per_esito["pronto"],
            "per_esito": per_esito, "per_tipo": per_tipo}


def da_recuperare(conn, limite: int = 100) -> list[dict]:
    """Bandi aperti o in arrivo, per imprese, senza un documento ufficiale verificato: quelli "in disparte" (filtro o
    scheda su sintesi) e quelli con la verifica del documento negativa. I piu' vicini alla scadenza prima."""
    with conn.cursor() as cur:
        cur.execute("""SELECT s.id, s.titolo, s.ente, s.stato, s.scadenza, s.situazione, s.fase, s.motivo,
                              b.url, b.verifica_documento, b.tipo_procedura
                       FROM bandi_situazione s JOIN bandi b ON b.id = s.id
                       WHERE s.stato IS DISTINCT FROM 'chiuso'
                         AND (s.situazione = 'in_disparte'
                              OR (s.situazione = 'proponibile' AND b.verifica_documento->>'verificato' = 'no'))
                       ORDER BY s.scadenza NULLS LAST, s.id LIMIT %s""", (limite,))
        righe = [dict(r) for r in cur.fetchall()]
    for r in righe:
        if (r["verifica_documento"] or {}).get("verificato") == "no":
            r["motivo"] = esito(r)[1]
    return righe


def main(argomenti: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Procedura nuova del regista: ripasso dei proponibili e lista da recuperare.")
    p.add_argument("--da-recuperare", action="store_true")
    p.add_argument("--bando", type=int)
    p.add_argument("--limite", type=int, default=50)
    a = p.parse_args(argomenti)

    from app.db.connessione import connetti

    with connetti() as conn:
        if a.bando:
            with conn.cursor() as cur:
                cur.execute("SELECT id, titolo, tipo_procedura, verifica_documento, secondo_controllo, scheda_il "
                            "FROM bandi WHERE id = %s", (a.bando,))
                b = cur.fetchone()
            if not b:
                print(f"Bando {a.bando} non trovato.")
                return 1
            e, motivo = esito(dict(b))
            print(f"[{b['id']}] {b['titolo']}\n  tipo: {TIPI.get(b['tipo_procedura'] or '', 'non noto')}"
                  f"\n  procedura: {NOMI[e]} ({e}): {motivo}")
            return 0
        if a.da_recuperare:
            righe = da_recuperare(conn, a.limite)
            print(f"Da recuperare (aperti o in arrivo senza documento verificato): {len(righe)} mostrati, "
                  f"al massimo {a.limite}, scadenza piu' vicina prima")
            for r in righe:
                print(f"[{r['id']}] {r['titolo'][:90]} · scade {r['scadenza'] or '-'}\n    {(r['motivo'] or '-')[:200]}")
            return 0
        r = ripasso(conn)
    print(f"Proponibili oggi: {r['proponibili_oggi']}. Con la regola nuova restano {r['restano']}, "
          f"escono {r['escono']} finche' non finiscono la procedura:")
    for k, nome, prossimo in ESITI:
        print(f"  {r['per_esito'][k]:>6}  {nome} ({k}) -> {prossimo}")
    print("Tipi di agevolazione:")
    for k, n in sorted(r["per_tipo"].items(), key=lambda x: -x[1]):
        print(f"  {n:>6}  {TIPI.get(k, k)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
