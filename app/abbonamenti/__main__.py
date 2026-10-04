"""Comandi per gli abbonamenti (in produzione: sudo -u deploy docker compose exec app python -m app.abbonamenti ...).

  prepara-stripe            crea in Stripe (chiavi di PROVA) i prezzi e le configurazioni del portale; stampa gli id per il .env
  elenco                    abbonamenti delle imprese
  gratuito --email X        abbonamento gratuito (imprese amiche, prove)
"""

from __future__ import annotations

import argparse
import sys

from app import abbonamenti as ab
from app.db.connessione import connetti


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(prog="python -m app.abbonamenti")
    sub = p.add_subparsers(dest="comando", required=True)
    sub.add_parser("prepara-stripe")
    sub.add_parser("elenco")
    g = sub.add_parser("gratuito")
    g.add_argument("--email", required=True)
    args = p.parse_args(argv)
    try:
        if args.comando == "prepara-stripe":
            for riga in ab.prepara_stripe():
                print(riga)
            return 0
        with connetti() as conn:
            if args.comando == "elenco":
                for r in ab.elenco(conn):
                    print(f"{r['utente_id']:>4}  {r['email']:<40} {r['stato'] or 'mai entrato':<11} {r['piano'] or '':<8} "
                          f"imprese {r['imprese']}")
                return 0
            with conn.cursor() as cur:
                cur.execute("SELECT id FROM utenti WHERE lower(email) = lower(%s) AND ruolo = 'impresa'", (args.email,))
                r = cur.fetchone()
            if not r:
                print("Utente impresa non trovato.", file=sys.stderr)
                return 1
            ab.imposta(conn, r["id"], stato="gratuito", nota="gratuito dal comando")
            conn.commit()
            print(f"{args.email}: abbonamento gratuito")
    except ab.ErroreAbbonamento as e:
        print(f"Errore: {e}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
