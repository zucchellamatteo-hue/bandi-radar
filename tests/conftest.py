"""Aiuti comuni ai test."""

from __future__ import annotations

import uuid

# Un bando che ha finito la procedura nuova del regista (app/catena/procedura.py, migrazione 036): documento verificato
# e secondo controllo fatto. Serve ai test che vogliono un bando proponibile.
PROCEDURA_FATTA = {"verifica_documento": {"verificato": "si"},
                   "secondo_controllo": {"esito": "corretta", "fatto_il": "2099-01-01T00:00:00+00:00"}}


class CookieSessione:
    """'auth' per httpx (TestClient): aggiunge il cookie di sessione alla richiesta, come farebbe il browser."""

    def __init__(self, codice: str):
        self.codice = codice

    def __call__(self, richiesta):
        richiesta.headers["Cookie"] = f"br_sessione={self.codice}"
        return richiesta


def accesso_di_prova(ruolo: str = "admin") -> CookieSessione:
    """Crea nel database di prova un utente con il ruolo chiesto e apre una sessione (serve PGHOST)."""
    from app import utenti as u
    from app.db.connessione import connetti
    from app.db.migrazioni import applica_migrazioni

    with connetti() as conn:
        applica_migrazioni(conn)
        email = f"prova-{ruolo}-{uuid.uuid4().hex[:8]}@esempio.it"
        utente = u.crea_utente(conn, email, ruolo, password="password-di-prova")
        with conn.cursor() as cur:   # come se avesse aperto il link dell'invito
            cur.execute("UPDATE utenti SET email_confermata_il = now() WHERE id = %s", (utente["id"],))
        _, codice = u.accedi(conn, email, "password-di-prova")
        conn.commit()
    return CookieSessione(codice)
