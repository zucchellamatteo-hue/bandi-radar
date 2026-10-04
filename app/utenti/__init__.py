"""Utenti, password, sessioni e link via email (05/10/2026).

Le password si salvano con scrypt (libreria standard di Python, lento apposta per chi prova a indovinarle).
Sessioni e link: al browser o nell'email va un codice casuale, nel database solo la sua impronta sha256,
cosi' chi leggesse il database non potrebbe entrare con quei codici.
"""

from __future__ import annotations

import hashlib
import hmac
import os
import re
import secrets
from datetime import datetime, timedelta, timezone

RUOLI = ("admin", "revisore", "impresa")
DURATA_SESSIONE = timedelta(days=30)
DURATA_LINK = {"invito": timedelta(days=7), "recupero": timedelta(hours=2), "conferma": timedelta(days=3)}
MAX_ERRORI = 5                         # errori di password per indirizzo prima della pausa
MAX_ERRORI_IP = 20                     # errori da uno stesso indirizzo IP (chi prova molti account)
PAUSA = timedelta(minutes=15)
LUNGHEZZA_MINIMA_PASSWORD = 10

_SCRYPT = {"n": 2 ** 15, "r": 8, "p": 1}
_EMAIL = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


class ErroreUtenti(ValueError):
    """Errore da mostrare cosi' com'e' a chi usa la plancia o il comando."""


def adesso() -> datetime:
    return datetime.now(timezone.utc)


def sito_url() -> str:
    return (os.environ.get("SITO_URL") or "https://finanzagevolata.qiaro.it").rstrip("/")


# --- password ---

def hash_password(password: str) -> str:
    sale = secrets.token_bytes(16)
    h = hashlib.scrypt(password.encode(), salt=sale, maxmem=64 * 1024 * 1024, dklen=32, **_SCRYPT)
    return f"scrypt${_SCRYPT['n']}${_SCRYPT['r']}${_SCRYPT['p']}${sale.hex()}${h.hex()}"


def verifica_password(password: str, salvata: str | None) -> bool:
    if not salvata:
        return False
    try:
        nome, n, r, p, sale, h = salvata.split("$")
        if nome != "scrypt":
            return False
        calcolata = hashlib.scrypt(password.encode(), salt=bytes.fromhex(sale), n=int(n), r=int(r), p=int(p),
                                   maxmem=64 * 1024 * 1024, dklen=len(bytes.fromhex(h)))
    except (ValueError, TypeError):
        return False
    return hmac.compare_digest(calcolata.hex(), h)


def controlla_password(password: str) -> None:
    if len(password or "") < LUNGHEZZA_MINIMA_PASSWORD:
        raise ErroreUtenti(f"La password deve avere almeno {LUNGHEZZA_MINIMA_PASSWORD} caratteri.")


def impronta(codice: str) -> str:
    return hashlib.sha256(codice.encode()).hexdigest()


def normalizza_email(email: str) -> str:
    return (email or "").strip().lower()


# --- utenti ---

def _pubblico(r: dict) -> dict:
    return {k: r[k] for k in ("id", "email", "nome", "ruolo", "attivo", "creato_il", "ultimo_accesso") if k in r} | (
        {"password_impostata": r["password_hash"] is not None} if "password_hash" in r else {})


def crea_utente(conn, email: str, ruolo: str, nome: str | None = None, password: str | None = None,
                creato_da: int | None = None, controlla_email: bool = True) -> dict:
    email = normalizza_email(email)
    if controlla_email and not _EMAIL.match(email):
        raise ErroreUtenti("Indirizzo email non valido.")
    if ruolo not in RUOLI:
        raise ErroreUtenti(f"Ruolo non valido: usare {', '.join(RUOLI)}.")
    if password is not None:
        controlla_password(password)
    with conn.cursor() as cur:
        cur.execute("SELECT 1 FROM utenti WHERE lower(email) = %s", (email,))
        if cur.fetchone():
            raise ErroreUtenti("Esiste gia' un utente con questo indirizzo.")
        cur.execute(
            "INSERT INTO utenti (email, nome, ruolo, password_hash, creato_da) VALUES (%s, %s, %s, %s, %s) RETURNING *",
            (email, (nome or "").strip() or None, ruolo, hash_password(password) if password else None, creato_da))
        return dict(cur.fetchone())


def trova(conn, email: str) -> dict | None:
    with conn.cursor() as cur:
        cur.execute("SELECT * FROM utenti WHERE lower(email) = %s", (normalizza_email(email),))
        r = cur.fetchone()
    return dict(r) if r else None


def elenco(conn) -> list[dict]:
    with conn.cursor() as cur:
        cur.execute("SELECT * FROM utenti ORDER BY ruolo, lower(email)")
        return [_pubblico(dict(r)) for r in cur.fetchall()]


def modifica(conn, utente_id: int, ruolo: str | None = None, attivo: bool | None = None, nome: str | None = None) -> dict:
    if ruolo is not None and ruolo not in RUOLI:
        raise ErroreUtenti("Ruolo non valido.")
    with conn.cursor() as cur:
        cur.execute("SELECT * FROM utenti WHERE id = %s FOR UPDATE", (utente_id,))
        u = cur.fetchone()
        if not u:
            raise ErroreUtenti("Utente non trovato.")
        nuovo_ruolo = ruolo if ruolo is not None else u["ruolo"]
        nuovo_attivo = attivo if attivo is not None else u["attivo"]
        if u["ruolo"] == "admin" and u["attivo"] and (nuovo_ruolo != "admin" or not nuovo_attivo):
            cur.execute("SELECT count(*) AS n FROM utenti WHERE ruolo = 'admin' AND attivo AND id <> %s", (utente_id,))
            if cur.fetchone()["n"] == 0:
                raise ErroreUtenti("Deve restare almeno un amministratore attivo.")
        cur.execute("UPDATE utenti SET ruolo = %s, attivo = %s, nome = coalesce(%s, nome) WHERE id = %s RETURNING *",
                    (nuovo_ruolo, nuovo_attivo, nome, utente_id))
        r = dict(cur.fetchone())
        if not nuovo_attivo or nuovo_ruolo != u["ruolo"]:
            cur.execute("DELETE FROM sessioni WHERE utente_id = %s", (utente_id,))   # esce subito ovunque
    return _pubblico(r)


def imposta_password(conn, utente_id: int, password: str) -> None:
    controlla_password(password)
    with conn.cursor() as cur:
        cur.execute("UPDATE utenti SET password_hash = %s WHERE id = %s", (hash_password(password), utente_id))
        cur.execute("DELETE FROM sessioni WHERE utente_id = %s", (utente_id,))


# --- accesso con limite ai tentativi ---

def bloccato(conn, email: str, ip: str | None) -> bool:
    """True se da questo indirizzo email (o IP) ci sono troppi errori recenti, dopo l'ultimo accesso riuscito."""
    email = normalizza_email(email)
    with conn.cursor() as cur:
        cur.execute(
            """SELECT count(*) AS n FROM tentativi_accesso t
               WHERE lower(t.email) = %s AND NOT t.riuscito AND t.quando > now() - %s
                 AND t.quando > coalesce((SELECT max(quando) FROM tentativi_accesso
                                          WHERE lower(email) = %s AND riuscito), '-infinity')""",
            (email, PAUSA, email))
        if cur.fetchone()["n"] >= MAX_ERRORI:
            return True
        if ip:
            cur.execute("SELECT count(*) AS n FROM tentativi_accesso WHERE ip = %s AND NOT riuscito AND quando > now() - %s",
                        (ip, PAUSA))
            if cur.fetchone()["n"] >= MAX_ERRORI_IP:
                return True
    return False


def _primo_admin_dal_env(conn, email: str, password: str) -> dict | None:
    """Transizione dall'autenticazione base: se non c'e' ancora nessun amministratore, chi entra con utente e password
    del .env (BASIC_AUTH_USER / BASIC_AUTH_PASSWORD) diventa il primo admin. Poi conta solo la password nel database."""
    utente_env = normalizza_email(os.environ.get("BASIC_AUTH_USER", ""))
    password_env = os.environ.get("BASIC_AUTH_PASSWORD", "")
    if not utente_env or not password_env:
        return None
    if not (hmac.compare_digest(email.encode(), utente_env.encode())
            and hmac.compare_digest(password.encode(), password_env.encode())):
        return None
    with conn.cursor() as cur:
        cur.execute("SELECT 1 FROM utenti WHERE ruolo = 'admin' AND attivo")
        if cur.fetchone():
            return None
        cur.execute("SELECT 1 FROM utenti WHERE lower(email) = %s", (email,))
        if cur.fetchone():
            return None
        cur.execute("INSERT INTO utenti (email, nome, ruolo, password_hash) VALUES (%s, 'Amministratore', 'admin', %s) "
                    "RETURNING *", (email, hash_password(password)))
        return dict(cur.fetchone())


def accedi(conn, email: str, password: str, ip: str | None = None) -> tuple[dict, str]:
    """Controlla email e password; se vanno bene apre una sessione e ritorna (utente, codice per il cookie)."""
    email = normalizza_email(email)
    if bloccato(conn, email, ip):
        raise ErroreUtenti("Troppi tentativi sbagliati: riprova tra 15 minuti.")
    u = trova(conn, email)
    ok = bool(u and u["attivo"] and verifica_password(password or "", u["password_hash"]))
    if not u:
        u = _primo_admin_dal_env(conn, email, password or "")
        ok = u is not None
    with conn.cursor() as cur:
        cur.execute("INSERT INTO tentativi_accesso (email, ip, riuscito) VALUES (%s, %s, %s)", (email, ip, ok))
        if not ok:
            conn.commit()   # il tentativo sbagliato resta registrato anche se poi la richiesta finisce in errore
            raise ErroreUtenti("Email o password non corretti.")
        codice = secrets.token_urlsafe(32)
        cur.execute("INSERT INTO sessioni (impronta, utente_id, scade_il) VALUES (%s, %s, %s)",
                    (impronta(codice), u["id"], adesso() + DURATA_SESSIONE))
        cur.execute("UPDATE utenti SET ultimo_accesso = now() WHERE id = %s", (u["id"],))
        cur.execute("DELETE FROM sessioni WHERE scade_il < now()")
        cur.execute("DELETE FROM tentativi_accesso WHERE quando < now() - interval '30 days'")
    return _pubblico(u), codice


def utente_della_sessione(conn, codice: str | None) -> dict | None:
    if not codice:
        return None
    with conn.cursor() as cur:
        cur.execute(
            """SELECT u.*, s.ultimo_uso FROM sessioni s JOIN utenti u ON u.id = s.utente_id
               WHERE s.impronta = %s AND s.scade_il > now() AND u.attivo""", (impronta(codice),))
        r = cur.fetchone()
        if not r:
            return None
        if r["ultimo_uso"] < adesso() - timedelta(hours=1):
            cur.execute("UPDATE sessioni SET ultimo_uso = now() WHERE impronta = %s", (impronta(codice),))
            cur.execute("UPDATE utenti SET ultimo_accesso = now() WHERE id = %s", (r["id"],))
    return _pubblico(dict(r))


def esci(conn, codice: str | None) -> None:
    if codice:
        with conn.cursor() as cur:
            cur.execute("DELETE FROM sessioni WHERE impronta = %s", (impronta(codice),))


# --- link via email ---

def crea_link(conn, utente_id: int, scopo: str) -> str:
    """Ritorna l'indirizzo completo da mandare per email. I link precedenti con lo stesso scopo smettono di valere."""
    codice = secrets.token_urlsafe(32)
    with conn.cursor() as cur:
        cur.execute("UPDATE link_email SET usato_il = now() WHERE utente_id = %s AND scopo = %s AND usato_il IS NULL",
                    (utente_id, scopo))
        cur.execute("INSERT INTO link_email (impronta, utente_id, scopo, scade_il) VALUES (%s, %s, %s, %s)",
                    (impronta(codice), utente_id, scopo, adesso() + DURATA_LINK[scopo]))
    pagina = {"invito": "imposta-password", "recupero": "imposta-password", "conferma": "conferma-email"}[scopo]
    return f"{sito_url()}/{pagina}?codice={codice}"


def usa_link(conn, codice: str, scopi: tuple[str, ...]) -> dict:
    """Consuma un link (vale una volta) e ritorna l'utente; errore se scaduto, gia' usato o inesistente."""
    with conn.cursor() as cur:
        cur.execute(
            """UPDATE link_email SET usato_il = now()
               WHERE impronta = %s AND usato_il IS NULL AND scade_il > now() AND scopo = ANY(%s)
               RETURNING utente_id, scopo""", (impronta(codice or ""), list(scopi)))
        r = cur.fetchone()
        if not r:
            raise ErroreUtenti("Il link non e' valido o e' scaduto: chiedine uno nuovo.")
        cur.execute("SELECT * FROM utenti WHERE id = %s AND attivo", (r["utente_id"],))
        u = cur.fetchone()
        if not u:
            raise ErroreUtenti("Utente non attivo.")
    return dict(u) | {"scopo": r["scopo"]}


def link_valido(conn, codice: str, scopi: tuple[str, ...]) -> dict | None:
    """Come usa_link ma senza consumarlo: serve alla pagina per dire subito se il link e' ancora buono."""
    with conn.cursor() as cur:
        cur.execute(
            """SELECT u.email, u.nome, l.scopo FROM link_email l JOIN utenti u ON u.id = l.utente_id
               WHERE l.impronta = %s AND l.usato_il IS NULL AND l.scade_il > now() AND l.scopo = ANY(%s) AND u.attivo""",
            (impronta(codice or ""), list(scopi)))
        r = cur.fetchone()
    return dict(r) if r else None


# --- testi delle email ---

NOMI_RUOLO = {"admin": "amministratore", "revisore": "revisore delle schede", "impresa": "impresa"}


def email_invito(utente: dict, link: str, invitato_da: str | None = None) -> tuple[str, str]:
    chi = f" da {invitato_da}" if invitato_da else ""
    testo = (f"Buongiorno{(' ' + utente['nome']) if utente.get('nome') else ''},\n\n"
             f"sei stato invitato{chi} su Bandi Radar (finanza agevolata per le imprese) "
             f"come {NOMI_RUOLO.get(utente['ruolo'], utente['ruolo'])}.\n\n"
             f"Per scegliere la password ed entrare apri questo link (vale 7 giorni):\n{link}\n\n"
             f"Il tuo nome utente e' questo indirizzo email.\n\nBandi Radar - finanzagevolata.qiaro.it\n")
    return "Invito a Bandi Radar", testo


def email_recupero(link: str) -> tuple[str, str]:
    testo = ("Buongiorno,\n\nabbiamo ricevuto una richiesta per cambiare la password di Bandi Radar.\n\n"
             f"Per sceglierne una nuova apri questo link (vale 2 ore):\n{link}\n\n"
             "Se non sei stato tu, ignora questa email: la password resta quella di prima.\n\n"
             "Bandi Radar - finanzagevolata.qiaro.it\n")
    return "Nuova password per Bandi Radar", testo


def manda(destinatario: str, oggetto: str, testo: str) -> str:
    """Manda l'email con Resend; ritorna 'inviata', 'stampata' (manca la chiave) o 'errore'. Non solleva mai errori."""
    from app.notifiche.email import invia

    try:
        return invia(destinatario, oggetto, testo)
    except Exception as exc:  # noqa: BLE001 - l'email che non parte non deve rompere la pagina
        print(f"[email non partita per {destinatario}: {exc}]")
        return "errore"
