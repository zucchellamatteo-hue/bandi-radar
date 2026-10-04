"""Accesso alla plancia (login con email e password, cookie di sessione) e pagina Utenti dell'amministratore.

Chi puo' fare cosa:
- admin: tutto;
- revisore: legge catalogo, schede e documenti (rotte in REVISORE_PUO), niente modifiche;
- impresa: solo l'area impresa (tappa 3), nessuna rotta della plancia di lavoro.
"""

from __future__ import annotations

import os
from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, Request, Response
from pydantic import BaseModel

from app import utenti as u
from app.db.connessione import connetti

COOKIE = "br_sessione"

# Rotte della plancia che il revisore puo' usare (solo lettura): percorsi come scritti nelle rotte FastAPI.
REVISORE_PUO = {
    ("GET", "/api/bandi"), ("GET", "/api/bandi/{bando_id}"), ("GET", "/api/valori"),
    ("GET", "/api/allegati/{allegato_id}/file"),
}

# Rotte che ogni utente entrato puo' usare (elenchi dei valori ammessi: servono al modulo dell'impresa).
TUTTI_POSSONO = {("GET", "/api/valori")}

router = APIRouter(prefix="/api")


def _ip(request: Request) -> str | None:
    # Davanti c'e' Caddy, che mette l'indirizzo vero del visitatore in X-Forwarded-For.
    inoltrato = request.headers.get("x-forwarded-for")
    if inoltrato:
        return inoltrato.split(",")[0].strip()
    return request.client.host if request.client else None


def _cookie_sicuro() -> bool:
    return os.environ.get("COOKIE_SICURO", "1") != "0"


def utente_corrente(request: Request) -> dict:
    codice = request.cookies.get(COOKIE)
    if codice:
        with connetti() as conn:
            utente = u.utente_della_sessione(conn, codice)
            conn.commit()
        if utente:
            return utente
    raise HTTPException(status_code=401, detail="Accesso richiesto.")


def solo_admin(utente: dict = Depends(utente_corrente)) -> dict:
    if utente["ruolo"] != "admin":
        raise HTTPException(status_code=403, detail="Solo gli amministratori possono farlo.")
    return utente


def controlla_plancia(request: Request, utente: dict = Depends(utente_corrente)) -> dict:
    """Protezione delle rotte della plancia di lavoro: l'admin passa sempre, il revisore solo in lettura sul catalogo."""
    if utente["ruolo"] == "admin":
        return utente
    rotta = request.scope.get("route")
    chiave = (request.method, rotta.path) if rotta is not None else None
    if chiave in TUTTI_POSSONO or (utente["ruolo"] == "revisore" and chiave in REVISORE_PUO):
        return utente
    raise HTTPException(status_code=403, detail="Il tuo profilo non permette questa operazione.")


# --- accesso ---

class Credenziali(BaseModel):
    email: str
    password: str


class NuovaPassword(BaseModel):
    codice: str
    password: str


class RichiestaRecupero(BaseModel):
    email: str


@router.post("/accesso/entra")
def entra(dati: Credenziali, request: Request, response: Response) -> dict:
    with connetti() as conn:
        try:
            utente, codice = u.accedi(conn, dati.email, dati.password, _ip(request))
        except u.ErroreUtenti as e:
            raise HTTPException(status_code=429 if "tentativi" in str(e) else 401, detail=str(e)) from e
        conn.commit()
    response.set_cookie(COOKIE, codice, max_age=int(u.DURATA_SESSIONE.total_seconds()), httponly=True,
                        secure=_cookie_sicuro(), samesite="lax", path="/")
    return utente


@router.post("/accesso/esci")
def esci(request: Request, response: Response) -> dict:
    with connetti() as conn:
        u.esci(conn, request.cookies.get(COOKIE))
        conn.commit()
    response.delete_cookie(COOKIE, path="/")
    return {"ok": True}


@router.get("/accesso/io")
def io(utente: dict = Depends(utente_corrente)) -> dict:
    return utente


@router.post("/accesso/recupero")
def recupero(dati: RichiestaRecupero, request: Request) -> dict:
    """Manda il link per una nuova password. Risponde sempre allo stesso modo: non rivela quali email esistono."""
    with connetti() as conn:
        if not u.bloccato(conn, dati.email, _ip(request)):
            utente = u.trova(conn, dati.email)
            with conn.cursor() as cur:   # conta come tentativo: limita anche le richieste a ripetizione
                cur.execute("INSERT INTO tentativi_accesso (email, ip, riuscito) VALUES (%s, %s, false)",
                            (u.normalizza_email(dati.email), _ip(request)))
            if utente and utente["attivo"]:
                link = u.crea_link(conn, utente["id"], "recupero")
                conn.commit()
                u.manda(utente["email"], *u.email_recupero(link))
            conn.commit()
    return {"ok": True, "messaggio": "Se l'indirizzo e' registrato, arriva un'email con il link per la nuova password."}


@router.get("/accesso/link")
def controlla_link(codice: str) -> dict:
    with connetti() as conn:
        r = u.link_valido(conn, codice, ("invito", "recupero"))
    if not r:
        raise HTTPException(status_code=404, detail="Il link non e' valido o e' scaduto: chiedine uno nuovo.")
    return r


@router.post("/accesso/imposta-password")
def nuova_password(dati: NuovaPassword, response: Response, request: Request) -> dict:
    with connetti() as conn:
        try:
            u.controlla_password(dati.password)
            utente = u.usa_link(conn, dati.codice, ("invito", "recupero"))
            u.imposta_password(conn, utente["id"], dati.password)
            conn.commit()
            pubblico, codice = u.accedi(conn, utente["email"], dati.password, _ip(request))
        except u.ErroreUtenti as e:
            raise HTTPException(status_code=422, detail=str(e)) from e
        conn.commit()
    response.set_cookie(COOKIE, codice, max_age=int(u.DURATA_SESSIONE.total_seconds()), httponly=True,
                        secure=_cookie_sicuro(), samesite="lax", path="/")
    return pubblico


class Registrazione(BaseModel):
    email: str
    password: str
    nome: str | None = None


class Conferma(BaseModel):
    codice: str


def _metti_cookie(response: Response, codice: str) -> None:
    response.set_cookie(COOKIE, codice, max_age=int(u.DURATA_SESSIONE.total_seconds()), httponly=True,
                        secure=_cookie_sicuro(), samesite="lax", path="/")


@router.get("/accesso/registrazione")
def stato_registrazione() -> dict:
    return {"aperta": u.registrazioni_aperte()}


@router.post("/accesso/registrazione")
def registrazione(dati: Registrazione, request: Request) -> dict:
    """Registrazione di un'impresa: l'accesso arriva dopo la conferma dell'indirizzo (link via email)."""
    if not u.registrazioni_aperte():
        raise HTTPException(status_code=403, detail="Le registrazioni non sono ancora aperte: scrivici per avere un invito.")
    with connetti() as conn:
        if u.bloccato(conn, dati.email, _ip(request)):
            raise HTTPException(status_code=429, detail="Troppi tentativi: riprova tra 15 minuti.")
        try:
            utente, link = u.registra(conn, dati.email, dati.password, dati.nome)
        except u.ErroreUtenti as e:
            raise HTTPException(status_code=422, detail=str(e)) from e
        conn.commit()
    u.manda(utente["email"], *u.email_conferma(link))
    return {"ok": True, "messaggio": "Ti abbiamo mandato un'email: apri il link per confermare l'indirizzo ed entrare."}


@router.post("/accesso/conferma")
def conferma(dati: Conferma, response: Response) -> dict:
    with connetti() as conn:
        try:
            utente = u.usa_link(conn, dati.codice, ("conferma",))
        except u.ErroreUtenti as e:
            raise HTTPException(status_code=422, detail=str(e)) from e
        codice = u.apri_sessione(conn, utente["id"])
        conn.commit()
    _metti_cookie(response, codice)
    return u._pubblico(utente)


# --- pagina Utenti (solo admin) ---

class NuovoUtente(BaseModel):
    email: str
    nome: str | None = None
    ruolo: Literal["admin", "revisore", "impresa"]


class ModificaUtente(BaseModel):
    ruolo: Literal["admin", "revisore", "impresa"] | None = None
    attivo: bool | None = None
    nome: str | None = None


def _invita(conn, utente: dict, admin: dict) -> dict:
    link = u.crea_link(conn, utente["id"], "invito")
    conn.commit()
    esito = u.manda(utente["email"], *u.email_invito(utente, link, admin.get("nome") or admin["email"]))
    # Il link torna anche all'amministratore: se l'email non parte (Resend non ancora configurato) lo manda lui.
    return {"link": link, "email": esito}


@router.get("/utenti")
def elenco_utenti(_: dict = Depends(solo_admin)) -> list[dict]:
    with connetti() as conn:
        return u.elenco(conn)


@router.post("/utenti")
def crea(dati: NuovoUtente, admin: dict = Depends(solo_admin)) -> dict:
    with connetti() as conn:
        try:
            utente = u.crea_utente(conn, dati.email, dati.ruolo, dati.nome, creato_da=admin["id"])
        except u.ErroreUtenti as e:
            raise HTTPException(status_code=422, detail=str(e)) from e
        invito = _invita(conn, utente, admin)
    return {"utente": u._pubblico(utente)} | invito


@router.patch("/utenti/{utente_id}")
def cambia(utente_id: int, dati: ModificaUtente, admin: dict = Depends(solo_admin)) -> dict:
    with connetti() as conn:
        try:
            r = u.modifica(conn, utente_id, dati.ruolo, dati.attivo, dati.nome)
        except u.ErroreUtenti as e:
            raise HTTPException(status_code=422, detail=str(e)) from e
        conn.commit()
    return r


@router.post("/utenti/{utente_id}/invito")
def reinvita(utente_id: int, admin: dict = Depends(solo_admin)) -> dict:
    """Nuovo link per scegliere la password (anche per chi l'ha dimenticata): i link precedenti smettono di valere."""
    with connetti() as conn, conn.cursor() as cur:
        cur.execute("SELECT * FROM utenti WHERE id = %s AND attivo", (utente_id,))
        utente = cur.fetchone()
        if not utente:
            raise HTTPException(status_code=404, detail="Utente non trovato o non attivo.")
        return _invita(conn, dict(utente), admin)
