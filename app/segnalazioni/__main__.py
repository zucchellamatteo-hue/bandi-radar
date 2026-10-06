"""Segnalazioni per le sessioni di Claude Code.

python -m app.segnalazioni                          stampa le segnalazioni aperte (nuove e prese in carico)
python -m app.segnalazioni rispondi ID STATO TESTO  cambia stato (presa_in_carico, risolta, respinta) e risposta
"""

import sys

from app import segnalazioni as sg
from app.db.connessione import connetti


def main(argomenti: list[str]) -> int:
    with connetti() as conn:
        if not argomenti:
            print(sg.testo(sg.elenco(conn, stato="aperte", per_pagina=500)["segnalazioni"]))
            return 0
        if argomenti[0] == "rispondi" and len(argomenti) >= 3 and argomenti[1].isdigit():
            try:
                r = sg.gestisci(conn, int(argomenti[1]), argomenti[2], " ".join(argomenti[3:]) or None, "agente")
            except sg.ErroreSegnalazione as e:
                print(e, file=sys.stderr)
                return 1
            conn.commit()
            print(f"Segnalazione #{r['id']}: {sg.STATI[r['stato']]}.")
            return 0
    print(__doc__, file=sys.stderr)
    return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
