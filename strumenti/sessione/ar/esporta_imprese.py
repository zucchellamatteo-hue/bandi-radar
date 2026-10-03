"""Punto 2 del piano del 03/10: per i bandi presi dalle regole "non per imprese" (/out/stato/imprese.json) scrive
/out/imprese/<id>.md con i campi beneficiari della scheda, i frammenti trovati dalle regole e l'inizio dei moduli
di domanda e dell'articolo sui beneficiari. Non scrive nel database."""
import json
import os
import re
from pathlib import Path

from app.db.connessione import connetti

OUT = Path("/out/imprese")
BENEF = re.compile(r"(?:soggetti beneficiari|beneficiari|soggetti ammissibili|chi pu[oò] presentare|destinatari)", re.IGNORECASE)


def main():
    os.umask(0)
    OUT.mkdir(exist_ok=True)
    ris = json.loads(Path("/out/stato/imprese.json").read_text())
    with connetti() as conn, conn.cursor() as cur:
        for i, v in ris.items():
            cur.execute("""SELECT id, titolo, ente, a_chi_si_rivolge, soggetti_ammessi, forme_giuridiche_ammesse,
                                  dimensioni_ammesse, sintesi, preliminare->>'per_imprese' AS pi
                           FROM bandi WHERE id=%s""", (int(i),))
            b = cur.fetchone()
            if b["pi"] == "no":
                continue
            cur.execute("""SELECT nome, categoria, testo_estratto FROM allegati WHERE bando_id=%s AND errore IS NULL
                           AND testo_estratto IS NOT NULL ORDER BY id""", (int(i),))
            docs = cur.fetchall()
            parti = [f"# Bando {b['id']}: {b['titolo']}\nEnte: {b['ente']}\n",
                     f"## Scheda\nA chi si rivolge: {b['a_chi_si_rivolge']}\nSoggetti ammessi: {b['soggetti_ammessi']}\n"
                     f"Forme giuridiche ammesse: {b['forme_giuridiche_ammesse']}\nDimensioni: {b['dimensioni_ammesse']}\n"
                     f"Sintesi: {(b['sintesi'] or '')[:1500]}\n",
                     "## Frasi trovate dalle regole\n" + "\n".join(f"- [{x['regola']}] ({x.get('doc', '')}, {x.get('categoria', '')}): {x['testo']}" for x in v[1:])]
            for d in docs:
                t = d["testo_estratto"]
                m = BENEF.search(t)
                pezzo = re.sub(r"[ \t]+", " ", t[m.start(): m.start() + 2500]) if m else ""
                if d["categoria"] == "modulistica":
                    pezzo = re.sub(r"[ \t]+", " ", t[:2500])
                if pezzo:
                    parti.append(f"## Documento: {d['nome'][:100]} ({d['categoria']})\n{pezzo}\n")
            (OUT / f"{i}.md").write_text("\n".join(parti)[:40000])
    print("scritti", len(list(OUT.glob("*.md"))))


if __name__ == "__main__":
    main()
