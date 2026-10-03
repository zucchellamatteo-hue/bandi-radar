"""Punto 2 del piano del 03/10: regole senza IA sui testi di TUTTI i documenti (modulistica compresa) dei proponibili
non chiusi, per trovare i bandi che non sono per imprese. Conta e scrive /out/stato/imprese.json. Non scrive nel DB."""
import json
import os
import re
from collections import Counter, defaultdict
from pathlib import Path

from app.db.connessione import connetti

OUT = Path("/out/stato")
REGOLE = {
    "l398": r"(?:L\.|legge)\s*(?:n\.\s*)?398\s*/\s*(?:19)?91",
    "non_ente_commerciale": r"\bnon (?:e' |è )?(?:un )?ente commerciale|enti? non commercial[ei]",
    "asd_ssd": r"associazion[ei] sportiv[ae] dilettantistic|societ[aà] sportiv[ae] dilettantistic|\bA\.?S\.?D\.?\b",
    "terzo_settore": r"enti del terzo settore|\bETS\b|organizzazioni di volontariato|associazioni di promozione sociale",
    "enti_pubblici": r"(?:possono presentare domanda|soggetti beneficiari|beneficiari)[^.]{0,80}(?:i comuni|enti locali|unioni di comuni|amministrazioni pubbliche|enti pubblici)",
    "scuole": r"istituti scolastici|istituzioni scolastiche|universit[aà] e (?:gli )?enti di ricerca",
    "persone_fisiche": r"(?:beneficiari|destinatari|possono presentare domanda)[^.]{0,60}(?:persone fisiche|famiglie|nuclei familiari|cittadini residenti)",
    "destinatari_ente": r"Destinatari:\s*ENTE\b",
}
REGOLE = {k: re.compile(v, re.IGNORECASE) for k, v in REGOLE.items()}
IMPRESE = re.compile(r"\b(?:imprese|PMI|micro,? piccole e medie|lavoratori autonomi|liberi professionisti|cooperativ[ae]|startup)\b", re.IGNORECASE)


def main():
    os.umask(0)
    conti, ris = Counter(), defaultdict(list)
    with connetti() as conn, conn.cursor() as cur:
        cur.execute("""SELECT id, titolo, a_chi_si_rivolge, soggetti_ammessi FROM bandi WHERE completezza='bando_ufficiale'
                       AND coalesce(stato,'x') <> 'chiuso' AND coalesce(preliminare->>'per_imprese','') <> 'no' ORDER BY id""")
        bandi = cur.fetchall()
        for b in bandi:
            cur.execute("""SELECT nome, categoria, testo_estratto FROM allegati WHERE bando_id=%s AND errore IS NULL
                           AND testo_estratto IS NOT NULL""", (b["id"],))
            docs = cur.fetchall()
            for k, rx in REGOLE.items():
                for d in docs:
                    m = rx.search(d["testo_estratto"])
                    if m:
                        t = d["testo_estratto"]
                        ris[b["id"]].append({"regola": k, "doc": d["nome"][:80], "categoria": d["categoria"],
                                             "testo": re.sub(r"\s+", " ", t[max(0, m.start() - 150): m.end() + 150])})
                        conti[k] += 1
                        break
            chi = (b["a_chi_si_rivolge"] or "") + " " + " ".join(b["soggetti_ammessi"] or [])
            if b["id"] in ris:
                ris[b["id"]].insert(0, {"regola": "scheda", "testo": chi[:400], "imprese_nella_scheda": bool(IMPRESE.search(chi))})
        conti["esaminati"] = len(bandi)
        conti["presi"] = len(ris)
        conti["presi_senza_imprese_nella_scheda"] = sum(1 for v in ris.values() if not v[0]["imprese_nella_scheda"])
        conti["presi_da_2_regole"] = sum(1 for v in ris.values() if len(v) >= 3)
    (OUT / "imprese.json").write_text(json.dumps({str(k): v for k, v in ris.items()}, ensure_ascii=False, indent=1))
    for k, v in sorted(conti.items()):
        print(f"{v:5d}  {k}")


if __name__ == "__main__":
    main()
