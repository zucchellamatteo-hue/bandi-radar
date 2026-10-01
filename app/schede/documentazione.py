"""C'e' il bando? Filtro senza IA, prima della scheda (richiesta di Matteo del 01/10/2026).

Un bando si propone ai clienti solo se abbiamo le sue regole ufficiali. Per ogni bando con gli allegati scaricati si
guarda cosa c'e' davvero tra i documenti:
  - 'bando':   almeno un documento (PDF, Word...: non pagine web, non modulistica o graduatorie) leggibile, lungo almeno
               MINIMO_CARATTERI e con almeno MINIMO_SEGNI segni di un regolamento (articoli, beneficiari, requisiti,
               spese ammissibili, domanda, termini, importi, regime d'aiuto, istruttoria, erogazione);
  - 'sintesi': c'e' del testo, ma solo pagine web, notizie o documenti brevi (anche le pagine descrittive lunghe:
               non sono il bando);
  - 'nessuno': niente di leggibile.
Solo i bandi 'bando' vanno al controllo preliminare e alla scheda (sessione o API). Gli altri restano in disparte.

Tarata il 01/10/2026 sulle 3.475 decisioni gia' prese dall'IA: riconosce il 91% dei bandi in cui l'IA ha trovato il
testo ufficiale; circa 250 sintesi passano lo stesso (decreti su altro, accordi): li ferma poi il controllo preliminare.

Uso:
  python -m app.schede.documentazione            # i bandi con allegati non ancora valutati
  python -m app.schede.documentazione --tutti    # rivaluta tutti
  python -m app.schede.documentazione --bando 45
"""

from __future__ import annotations

import argparse
import re
import sys

MINIMO_CARATTERI = 3000
MINIMO_SEGNI = 5
MINIMO_SINTESI = 300

_SEGNI = {
    "articoli": r"\bart(?:icolo|\.)\s*\d",
    "beneficiari": r"\bbeneficiar|soggetti (?:ammessi|beneficiari)|destinatari",
    "requisiti": r"\brequisiti\b",
    "spese": r"spese ammissibil|spese ammesse|costi ammissibil",
    "domanda": r"present\w+ (?:della|delle|la|le) domand|domanda di (?:contributo|agevolazione|finanziamento|partecipazione)",
    "termini": r"\btermin[ei]\b|\bscadenz",
    "importi": r"intensit|percentuale|contributo massimo|importo massimo|fino a euro|€",
    "regime": r"de minimis|regolamento \(ue\)|reg\. \(ue\)|aiuti di stato|651/2014|2831/2023",
    "istruttoria": r"istruttori|valutazione|graduatori|punteggi|sportello",
    "erogazione": r"rendicontazion|erogazion|liquidazion|revoc",
}
_SEGNI = {k: re.compile(v, re.IGNORECASE) for k, v in _SEGNI.items()}
_ESCLUSE = ("modulistica", "graduatoria")


def segni(testo: str) -> list[str]:
    return [nome for nome, regola in _SEGNI.items() if regola.search(testo)]


def valuta(allegati: list[dict]) -> tuple[str, str]:
    """(esito, motivo) dai documenti del bando: dict con nome, tipo, categoria, testo_estratto, errore."""
    from app.schede.allegati import testo_leggibile

    migliore, sintesi = None, None
    for a in allegati:
        testo = a.get("testo_estratto") or ""
        if a.get("errore") or not testo or not testo_leggibile(testo):
            continue
        if len(testo) >= MINIMO_SINTESI and (sintesi is None or len(testo) > sintesi[1]):
            sintesi = (a.get("nome") or "", len(testo))
        if a.get("tipo") in ("pagina", "faq") or a.get("categoria") in _ESCLUSE:
            continue
        trovati = segni(testo)
        if len(testo) >= MINIMO_CARATTERI and len(trovati) >= MINIMO_SEGNI:
            if migliore is None or (len(trovati), len(testo)) > (len(migliore[1]), migliore[2]):
                migliore = (a.get("nome") or "", trovati, len(testo))
    if migliore:
        nome, trovati, n = migliore
        return "bando", f"«{nome[:80]}»: {n} caratteri, {len(trovati)} segni di un bando ({', '.join(trovati)})"
    if sintesi:
        return "sintesi", f"solo pagine o documenti brevi (il piu' lungo: «{sintesi[0][:80]}», {sintesi[1]} caratteri)"
    return "nessuno", "nessun documento leggibile"


def esegui(bando_id: int | None = None, tutti: bool = False, prova: bool = False) -> int:
    from collections import Counter

    from app.db.connessione import connetti
    from app.db.migrazioni import applica_migrazioni

    conteggi: Counter = Counter()
    with connetti() as conn:
        applica_migrazioni(conn)
        with conn.cursor() as cur:
            if bando_id:
                cur.execute("SELECT id FROM bandi WHERE id = %s", (bando_id,))
            else:
                cur.execute("SELECT id FROM bandi WHERE allegati_cercati_il IS NOT NULL"
                            + ("" if tutti else " AND documentazione IS NULL") + " ORDER BY id")
            ids = [r["id"] for r in cur.fetchall()]
        for inizio in range(0, len(ids), 200):
            gruppo = ids[inizio:inizio + 200]
            with conn.cursor() as cur:
                cur.execute("""SELECT bando_id, nome, tipo, categoria, testo_estratto, errore FROM allegati
                               WHERE bando_id = ANY(%s) AND annuncio_id IS NULL""", (gruppo,))
                per_bando: dict[int, list[dict]] = {}
                for r in cur.fetchall():
                    per_bando.setdefault(r["bando_id"], []).append(dict(r))
                for b in gruppo:
                    esito, motivo = valuta(per_bando.get(b, []))
                    conteggi[esito] += 1
                    if bando_id:
                        print(f"[{b}] {esito}: {motivo}")
                    if not prova:
                        # Non e' un cambio della scheda: il trigger delle versioni ignora queste colonne (migrazione 011).
                        cur.execute("UPDATE bandi SET documentazione = %s, documentazione_motivo = %s WHERE id = %s",
                                    (esito, motivo[:500], b))
            conn.commit()
    print(("PROVA: " if prova else "") + f"bandi valutati {sum(conteggi.values())}: "
          + ", ".join(f"{k} {v}" for k, v in conteggi.most_common()))
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="C'e' il bando tra i documenti? Filtro senza IA prima della scheda.")
    parser.add_argument("--bando", type=int, metavar="ID")
    parser.add_argument("--tutti", action="store_true", help="rivaluta anche i bandi gia' valutati")
    parser.add_argument("--prova", action="store_true", help="conta senza salvare")
    args = parser.parse_args(argv)
    return esegui(args.bando, args.tutti, args.prova)


if __name__ == "__main__":
    sys.exit(main())
