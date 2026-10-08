"""Gestione utenti dal server, anche prima che le email funzionino.

Esempi (in produzione, da /srv/bandi-radar):
  sudo -u deploy docker compose exec app python -m app.utenti crea --email amico@esempio.it --ruolo revisore --nome "Mario"
  sudo -u deploy docker compose exec app python -m app.utenti elenco
  sudo -u deploy docker compose exec app python -m app.utenti link --email amico@esempio.it
  sudo -u deploy docker compose exec app python -m app.utenti disattiva --email amico@esempio.it

"crea" e "link" stampano il link per scegliere la password (vale 7 giorni): si puo' mandare a mano se l'email non parte.
"""

from __future__ import annotations

import argparse
import sys

from app import utenti as u
from app.db.connessione import connetti


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(prog="python -m app.utenti", description="Utenti di bandinQiaro")
    sub = p.add_subparsers(dest="comando", required=True)
    c = sub.add_parser("crea", help="crea un utente e stampa il link per scegliere la password")
    c.add_argument("--email", required=True)
    c.add_argument("--ruolo", required=True, choices=u.RUOLI)
    c.add_argument("--nome")
    c.add_argument("--senza-email", action="store_true", help="non provare a mandare l'invito per email")
    sub.add_parser("elenco", help="elenca gli utenti")
    lk = sub.add_parser("link", help="nuovo link per scegliere la password")
    lk.add_argument("--email", required=True)
    d = sub.add_parser("disattiva", help="toglie l'accesso (l'utente resta nell'elenco)")
    d.add_argument("--email", required=True)
    a = sub.add_parser("attiva", help="ridà l'accesso")
    a.add_argument("--email", required=True)
    args = p.parse_args(argv)

    with connetti() as conn:
        try:
            if args.comando == "elenco":
                for r in u.elenco(conn):
                    stato = "attivo" if r["attivo"] else "disattivato"
                    pw = "" if r["password_impostata"] else " (password da scegliere)"
                    print(f"{r['id']:>4}  {r['ruolo']:<9} {r['email']:<40} {r['nome'] or '':<25} {stato}{pw}")
                return 0
            if args.comando == "crea":
                utente = u.crea_utente(conn, args.email, args.ruolo, args.nome)
                link = u.crea_link(conn, utente["id"], "invito")
                conn.commit()
                print(f"Creato: {utente['email']} ({utente['ruolo']})")
                if not args.senza_email:
                    print(f"Email d'invito: {u.manda(utente['email'], *u.email_invito(utente, link))}")
                print(f"Link per scegliere la password (vale 7 giorni):\n{link}")
                return 0
            utente = u.trova(conn, args.email)
            if not utente:
                print("Utente non trovato.", file=sys.stderr)
                return 1
            if args.comando == "link":
                link = u.crea_link(conn, utente["id"], "invito")
                conn.commit()
                print(f"Link per scegliere la password (vale 7 giorni):\n{link}")
            else:
                u.modifica(conn, utente["id"], attivo=args.comando == "attiva")
                conn.commit()
                print(f"{utente['email']}: {'attivo' if args.comando == 'attiva' else 'disattivato'}")
        except u.ErroreUtenti as e:
            print(f"Errore: {e}", file=sys.stderr)
            return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
