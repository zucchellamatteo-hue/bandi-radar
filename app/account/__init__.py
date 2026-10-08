"""I miei dati (05/10/2026, GDPR artt. 15, 17 e 20): ogni utente scarica tutto cio' che bandinQiaro tiene su di lui e
puo' cancellare il proprio account.

Cosa resta dopo la cancellazione: le fatture emesse (obbligo di conservazione fiscale, 10 anni), senza piu' il
collegamento all'utente. Tutto il resto si cancella: utente, sessioni, link, imprese con i loro profili anonimi,
richieste di supporto, email settimanali, giudizi, abbonamento, dati di fatturazione, tentativi di accesso.
"""

from __future__ import annotations

from datetime import datetime, timezone

from app import utenti as u


class ErroreAccount(ValueError):
    pass


def _righe(cur, sql: str, valori) -> list[dict]:
    cur.execute(sql, valori)
    return [dict(r) for r in cur.fetchall()]


def esporta(conn, utente_id: int) -> dict:
    with conn.cursor() as cur:
        cur.execute("""SELECT id, email, nome, ruolo, permessi, attivo, creato_il, ultimo_accesso, email_confermata_il
                       FROM utenti WHERE id = %s""", (utente_id,))
        utente = dict(cur.fetchone())
        dati = {
            "esportati_il": datetime.now(timezone.utc).isoformat(),
            "nota": "Tutti i dati che bandinQiaro conserva sul tuo account (password esclusa: si salva solo in forma cifrata).",
            "utente": utente,
            "imprese": _righe(cur, """SELECT i.id, i.nome, i.dati, i.email_settimanale, i.creata_il, p.profilo
                                       FROM imprese i JOIN profili p ON p.codice = i.profilo_codice WHERE i.utente_id = %s""",
                              (utente_id,)),
            "richieste_di_supporto": _righe(cur, """SELECT r.id, r.impresa_id, r.bando_id, b.titolo AS bando, r.messaggio, r.stato,
                                                    r.creata_il FROM richieste_supporto r JOIN imprese i ON i.id = r.impresa_id
                                                    JOIN bandi b ON b.id = r.bando_id WHERE i.utente_id = %s""", (utente_id,)),
            "email_settimanali": _righe(cur, """SELECT e.id, e.settimana, e.oggetto, e.stato, e.creata_il FROM email_imprese e
                                                JOIN imprese i ON i.id = e.impresa_id WHERE i.utente_id = %s""", (utente_id,)),
            "giudizi_sulle_schede": _righe(cur, """SELECT f.bando_id, b.titolo AS bando, f.versione, f.voto, f.problemi,
                                                   f.commento, f.stato, f.risposta, f.creato_il FROM feedback f
                                                   JOIN bandi b ON b.id = f.bando_id WHERE f.utente_id = %s""", (utente_id,)),
            "abbonamento": _righe(cur, """SELECT stato, piano, prova_fino_al, fine_impegno, fine_periodo, imprese_extra,
                                          sedi_extra, creato_il FROM abbonamenti WHERE utente_id = %s""", (utente_id,)),
            "dati_di_fatturazione": _righe(cur, "SELECT * FROM dati_fatturazione WHERE utente_id = %s", (utente_id,)),
            "fatture": _righe(cur, """SELECT anno, numero, data, imponibile, iva, totale, stato FROM fatture
                                      WHERE utente_id = %s""", (utente_id,)),
            "accessi_recenti": _righe(cur, """SELECT quando, ip, riuscito FROM tentativi_accesso WHERE lower(email) = lower(%s)
                                              ORDER BY quando DESC LIMIT 200""", (utente["email"],)),
        }
    return dati


def cancella(conn, utente: dict, password: str) -> None:
    """Cancella l'account dell'utente, dopo aver ricontrollato la password."""
    with conn.cursor() as cur:
        cur.execute("SELECT * FROM utenti WHERE id = %s FOR UPDATE", (utente["id"],))
        r = cur.fetchone()
        if not r or not u.verifica_password(password or "", r["password_hash"]):
            raise ErroreAccount("Password non corretta.")
        if r["ruolo"] == "admin":
            raise ErroreAccount("Un amministratore non può cancellarsi da qui: chiedi a un altro amministratore di togliergli l'accesso.")
        cur.execute("SELECT stato, stripe_abbonamento FROM abbonamenti WHERE utente_id = %s", (r["id"],))
        a = cur.fetchone()
        if a and a["stripe_abbonamento"] and a["stato"] in ("attivo", "in_ritardo"):
            raise ErroreAccount("Hai un abbonamento attivo: prima disdicilo da \"Gestisci abbonamento\", poi cancella l'account.")
        cur.execute("SELECT profilo_codice FROM imprese WHERE utente_id = %s", (r["id"],))
        profili = [x["profilo_codice"] for x in cur.fetchall()]
        cur.execute("DELETE FROM imprese WHERE utente_id = %s", (r["id"],))           # richieste ed email a cascata
        if profili:
            cur.execute("DELETE FROM profili WHERE codice = ANY(%s) AND origine = 'impresa'", (profili,))
        cur.execute("DELETE FROM tentativi_accesso WHERE lower(email) = lower(%s)", (r["email"],))
        cur.execute("DELETE FROM utenti WHERE id = %s", (r["id"],))                  # sessioni, link, giudizi, dati a cascata
