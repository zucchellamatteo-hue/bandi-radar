"""Smistamento a regole, senza IA: decide se un annuncio parla di aiuti alle imprese.

Le parole chiave stanno in app/schede/regole_smistamento.yaml (li' anche l'ordine con cui si decide).
Gli annunci che le regole non sanno decidere restano "da_rivedere": li smistera' l'IA.

Uso:
  python -m app.schede.smista               # smista gli annunci che non hanno ancora una decisione
  python -m app.schede.smista --rifai       # ricalcola anche quelli gia' decisi dalle regole (mai quelli di Matteo o dell'IA)
  python -m app.schede.smista --prova       # non scrive nulla: stampa percentuali ed esempi
  python -m app.schede.smista --prova --esempi 20
"""

from __future__ import annotations

import argparse
import re
import sys
import unicodedata
from collections import Counter
from dataclasses import dataclass, field
from pathlib import Path

import yaml

FILE_REGOLE = Path(__file__).resolve().parent / "regole_smistamento.yaml"
SEZIONI = ("rilevante", "destinatari_imprese", "contributi_non_per_imprese", "non_rilevante")
ESITI = ("rilevante", "non_rilevante", "da_rivedere")

# Parole che non possono mai far scartare un annuncio che parla di contributi (CLAUDE.md).
_GARA = re.compile(r"(?<!\w)(gara|gare|appalt\w*)(?!\w)")


class ErroreRegole(ValueError):
    """Il file delle regole e' mal formato; il messaggio dice dove."""


def normalizza(testo: str) -> str:
    """Minuscole, senza accenti, apostrofi tipografici uniformati: "Bonus Bebè" -> "bonus bebe"."""
    testo = unicodedata.normalize("NFKD", testo.replace("’", "'").replace("`", "'"))
    return "".join(c for c in testo if not unicodedata.combining(c)).lower()


def _espressione(frase: str) -> re.Pattern:
    """Una frase del file diventa un'espressione a parole intere; l'asterisco finale vale "qualunque finale"."""
    jolly = frase.endswith("*")
    parole = normalizza(frase.rstrip("*")).split()
    testo = r"\s+".join(re.escape(p) for p in parole)
    if jolly:
        testo += r"\w*"
    return re.compile(r"(?<!\w)" + testo + r"(?!\w)")


@dataclass
class Regola:
    sezione: str
    gruppo: str
    frase: str
    espressione: re.Pattern
    con: list[tuple[str, re.Pattern]] = field(default_factory=list)  # serve anche una di queste

    def scatta(self, testo: str) -> str | None:
        """Ritorna la descrizione di cosa e' scattato, o None."""
        if not self.espressione.search(testo):
            return None
        if not self.con:
            return f"'{self.frase}'"
        for frase, espressione in self.con:
            if espressione.search(testo):
                return f"'{self.frase}' + '{frase}'"
        return None


@dataclass
class Decisione:
    esito: str
    motivo: str


def carica_regole(percorso: Path = FILE_REGOLE) -> dict[str, list[Regola]]:
    try:
        grezzo = yaml.safe_load(percorso.read_text(encoding="utf-8")) or {}
    except yaml.YAMLError as exc:
        raise ErroreRegole(f"{percorso.name}: YAML non valido: {exc}") from exc
    sconosciute = set(grezzo) - set(SEZIONI)
    if sconosciute:
        raise ErroreRegole(f"{percorso.name}: sezioni non previste: {', '.join(sorted(sconosciute))}")
    regole: dict[str, list[Regola]] = {s: [] for s in SEZIONI}
    for sezione in SEZIONI:
        for gruppo in grezzo.get(sezione) or []:
            if not isinstance(gruppo, dict) or not gruppo.get("gruppo") or not isinstance(gruppo.get("parole"), list):
                raise ErroreRegole(f"{percorso.name}, {sezione}: ogni voce deve avere 'gruppo' e un elenco 'parole'")
            con = [(str(f).strip(), _espressione(str(f).strip())) for f in gruppo.get("con") or [] if str(f).strip()]
            for frase in gruppo["parole"]:
                frase = str(frase).strip()
                if not frase:
                    continue
                if sezione == "contributi_non_per_imprese" and _GARA.search(normalizza(frase)):
                    raise ErroreRegole(
                        f"{percorso.name}: '{frase}' non puo' stare in contributi_non_per_imprese: "
                        "gare e appalti non devono mai scartare un contributo (CLAUDE.md)")
                regole[sezione].append(Regola(sezione, gruppo["gruppo"], frase, _espressione(frase), con))
    if not regole["rilevante"] or not regole["non_rilevante"]:
        raise ErroreRegole(f"{percorso.name}: servono almeno una parola rilevante e una non rilevante")
    return regole


def _prima(regole: list[Regola], testo: str) -> str | None:
    """La prima regola che scatta, descritta come "sezione/gruppo: 'parola'", o None."""
    for r in regole:
        cosa = r.scatta(testo)
        if cosa:
            return f"{r.sezione}/{r.gruppo}: {cosa}"
    return None


def decidi(titolo: str, riassunto: str | None, regole: dict[str, list[Regola]]) -> Decisione:
    """Applica le regole nell'ordine descritto in cima al file YAML."""
    testo = normalizza(f"{titolo}\n{riassunto or ''}")
    rilevante = _prima(regole["rilevante"], testo)
    if rilevante:
        privati = _prima(regole["contributi_non_per_imprese"], testo)
        if privati and not _prima(regole["destinatari_imprese"], testo):
            return Decisione("non_rilevante", f"regole: {privati} (aiuto non per imprese; c'era {rilevante})")
        return Decisione("rilevante", f"regole: {rilevante}")
    escluso = _prima(regole["non_rilevante"], testo)
    if escluso:
        return Decisione("non_rilevante", f"regole: {escluso}")
    return Decisione("da_rivedere", "regole: nessuna parola chiave")


# --- database ---------------------------------------------------------------------------------

def annunci_da_smistare(conn, rifai: bool) -> list[dict]:
    """Senza --rifai: quelli senza decisione. Con --rifai: anche quelli decisi dalle regole."""
    condizione = "s.annuncio_id IS NULL" + (" OR s.deciso_da = 'regole'" if rifai else "")
    with conn.cursor() as cur:
        cur.execute(f"SELECT a.id, a.titolo, a.riassunto FROM annunci a LEFT JOIN smistamenti s ON s.annuncio_id = a.id "
                    f"WHERE {condizione} ORDER BY a.id")
        return list(cur.fetchall())


def salva(conn, annuncio_id: int, d: Decisione) -> None:
    with conn.cursor() as cur:
        # La clausola WHERE e' la cintura di sicurezza: una decisione di Matteo o dell'IA non si sovrascrive mai.
        cur.execute(
            """
            INSERT INTO smistamenti (annuncio_id, esito, motivo, deciso_da, costo, deciso_il)
            VALUES (%s, %s, %s, 'regole', NULL, now())
            ON CONFLICT (annuncio_id) DO UPDATE SET esito = EXCLUDED.esito, motivo = EXCLUDED.motivo, deciso_il = now()
            WHERE smistamenti.deciso_da = 'regole'
            """,
            (annuncio_id, d.esito, d.motivo),
        )


def concordanza_con_matteo(conn, regole) -> tuple[int, int, list[str]]:
    """Quante correzioni di Matteo le regole di adesso indovinerebbero: serve a tararle."""
    with conn.cursor() as cur:
        cur.execute("SELECT a.titolo, a.riassunto, s.esito FROM smistamenti s JOIN annunci a ON a.id = s.annuncio_id "
                    "WHERE s.deciso_da = 'matteo'")
        righe = cur.fetchall()
    sbagliate = []
    for r in righe:
        d = decidi(r["titolo"], r["riassunto"], regole)
        if d.esito != r["esito"]:
            sbagliate.append(f"Matteo: {r['esito']:<13} regole: {d.esito:<13} {r['titolo'][:90]}")
    return len(righe) - len(sbagliate), len(righe), sbagliate


def stampa_riepilogo(conteggi: Counter, esempi: dict[str, list[str]]) -> None:
    totale = sum(conteggi.values())
    print(f"Annunci smistati: {totale}")
    for esito in ESITI:
        n = conteggi.get(esito, 0)
        print(f"  {esito:<14} {n:>6}  {100 * n / totale if totale else 0:5.1f}%")
    for esito in ESITI:
        if esempi.get(esito):
            print(f"\nEsempi {esito}:")
            for riga in esempi[esito]:
                print("  " + riga)


def esegui(rifai: bool = False, prova: bool = False, n_esempi: int = 10) -> int:
    from app.db.connessione import connetti
    from app.db.migrazioni import applica_migrazioni

    regole = carica_regole()
    conteggi: Counter = Counter()
    esempi: dict[str, list[str]] = {e: [] for e in ESITI}
    with connetti() as conn:
        applica_migrazioni(conn)
        for a in annunci_da_smistare(conn, rifai):
            d = decidi(a["titolo"], a["riassunto"], regole)
            conteggi[d.esito] += 1
            if len(esempi[d.esito]) < n_esempi:
                esempi[d.esito].append(f"[{a['id']}] {a['titolo'][:100]}  <- {d.motivo}")
            if not prova:
                salva(conn, a["id"], d)
        if not prova:
            conn.commit()
        giuste, totale, sbagliate = concordanza_con_matteo(conn, regole)
    if prova:
        print("PROVA: nessuna modifica al database.")
    stampa_riepilogo(conteggi, esempi)
    if totale:
        print(f"\nCorrezioni di Matteo: le regole di adesso ne indovinano {giuste} su {totale}.")
        for riga in sbagliate[:n_esempi]:
            print("  " + riga)
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Smistamento a regole degli annunci (senza IA).")
    parser.add_argument("--rifai", action="store_true", help="ricalcola anche gli annunci gia' decisi dalle regole")
    parser.add_argument("--prova", action="store_true", help="non scrive nel database: stampa percentuali ed esempi")
    parser.add_argument("--esempi", type=int, default=10, metavar="N", help="quanti esempi stampare per esito (default 10)")
    args = parser.parse_args(argv)
    try:
        return esegui(args.rifai, args.prova, args.esempi)
    except ErroreRegole as exc:
        print(f"Errore nelle regole: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
