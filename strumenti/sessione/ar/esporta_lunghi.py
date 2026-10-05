"""Bandi lunghissimi (06/10/2026): scheda in due passaggi, per i bandi i cui documenti superano il testo che entra in
un fascicolo (ia.MASSIMO_TESTO_SCHEDA). Invece di un fascicolo tagliato, per ogni bando si prepara in /out/lunghi/<id>/:
- istruzioni.md: le istruzioni della scheda (prompt_scheda.md) e i dati del bando, senza i documenti;
- indice.md: un documento per riga (numero, nome, categoria, url, caratteri) con i titoli e gli articoli trovati;
- documenti/NN.txt: il testo completo di ogni documento (i testi ripetuti una volta sola).
L'agente legge prima l'indice, poi apre solo le parti che servono (ISTRUZIONI_LUNGHI.md) e scrive scheda.json;
importa_lunghi.py la salva con gli stessi controlli delle altre schede. Uso: esporta_lunghi.py ID [ID ...]"""
import os
import re
import sys
from datetime import date
from pathlib import Path

from app.db.connessione import connetti
from app.schede import ia
from app.schede.allegati import ordina_per_scheda

OUT = Path("/out/lunghi")
TITOLO = re.compile(r"^\s*((art(icolo)?\.?\s*\d+[^\n]{0,90})|([A-Z][A-Z0-9 ,.'’()\-–]{8,90})|(\d{1,2}(\.\d{1,2})*\.?\s+[A-Z][^\n]{3,90}))\s*$")


def titoli(testo: str, massimo: int = 60) -> list[tuple[int, str]]:
    """(riga, titolo) dei capitoli e articoli, per orientarsi senza leggere tutto."""
    trovati = []
    for n, riga in enumerate(testo.split("\n"), start=1):   # come le righe che legge l'agente (non splitlines)
        if TITOLO.match(riga) and len(riga.strip()) > 5:
            trovati.append((n, riga.strip()[:100]))
            if len(trovati) >= massimo:
                break
    return trovati


def main() -> int:
    os.umask(0)
    ids = [int(x) for x in sys.argv[1:] if x.isdigit()]
    _, modello = ia.leggi_prompt("prompt_scheda.md")
    oggi = date.today()
    with connetti() as conn:
        for bando_id in ids:
            with conn.cursor() as cur:
                cur.execute("SELECT * FROM bandi WHERE id = %s", (bando_id,))
                b = dict(cur.fetchone())
                cur.execute("""SELECT nome, url, tipo, categoria, testo_estratto FROM allegati
                               WHERE bando_id = %s AND annuncio_id IS NULL AND errore IS NULL""", (bando_id,))
                allegati = [dict(r) for r in cur.fetchall()]
                cur.execute("SELECT id, titolo FROM annunci WHERE bando_id = %s", (bando_id,))
                collegati = "; ".join(f"{x['id']} {x['titolo'][:80]}" for x in cur.fetchall())
            cartella = OUT / str(bando_id)
            (cartella / "documenti").mkdir(parents=True, exist_ok=True)
            indice, visti, n = [f"# Indice dei documenti del bando {bando_id}: {b['titolo']}\n"], set(), 0
            for a in ordina_per_scheda(allegati):
                testo = a.get("testo_estratto") or ""
                impronta = re.sub(r"\s+", " ", testo[:5000]).strip().lower()
                if len(impronta) > 2000 and impronta in visti:
                    indice.append(f"- (saltato: {a['nome']}, stesso testo di un documento gia' elencato)")
                    continue
                visti.add(impronta)
                n += 1
                (cartella / "documenti" / f"{n:02d}.txt").write_text(testo)
                righe = testo.count("\n") + 1
                indice.append(f"\n## {n:02d}. {a['nome']}  ({a.get('categoria') or a['tipo']}, {len(testo):,} caratteri, "
                              f"{righe:,} righe) — documenti/{n:02d}.txt\n{a['url']}")
                indice.extend(f"  riga {r}: {t}" for r, t in titoli(testo))
            (cartella / "indice.md").write_text("\n".join(indice) + "\n")
            istruzioni = ia.riempi(modello, {
                "data_oggi": oggi.isoformat(), "titolo": b["titolo"], "ente": b["ente"], "territorio": b["territorio"],
                "url": b["url"], "pagina_motivo": b.get("pagina_motivo"), "annunci": collegati,
                "avvertenze_documenti": "- i documenti sono troppo lunghi per un fascicolo: sono nei file di documenti/, "
                                        "elencati in indice.md con titoli e articoli",
                "documenti": [{"nome": "(vedi indice.md)", "url": "", "tipo": "pagina", "categoria": "altro",
                               "testo": "I documenti non sono qui: leggi indice.md e apri i file di documenti/."}]})
            (cartella / "istruzioni.md").write_text(istruzioni)
            print(f"{bando_id}: {n} documenti, {sum(len(a.get('testo_estratto') or '') for a in allegati):,} caratteri")
    return 0


if __name__ == "__main__":
    sys.exit(main())
