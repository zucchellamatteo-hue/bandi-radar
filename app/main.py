"""Bandi Radar - applicazione web (Fase 0: impalcatura).

Espone:
- GET /health  : stato dell'applicazione e del database, senza autenticazione (usato dal healthcheck)
- GET /        : pagina "in costruzione", protetta da autenticazione base (utente/password dal file .env)
"""

import os
import secrets

import psycopg
from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.security import HTTPBasic, HTTPBasicCredentials

app = FastAPI(title="Bandi Radar", docs_url=None, redoc_url=None, openapi_url=None)

_basic = HTTPBasic(realm="Bandi Radar")


def _check_database() -> str | None:
    """Ritorna None se il database risponde, altrimenti il messaggio d'errore."""
    # psycopg legge da solo PGHOST, PGPORT, PGUSER, PGPASSWORD e PGDATABASE dall'ambiente.
    if not os.environ.get("PGHOST"):
        return "PGHOST non impostata"
    try:
        with psycopg.connect(connect_timeout=3) as conn:
            conn.execute("SELECT 1")
    except Exception as exc:  # noqa: BLE001 - qualunque errore va riportato nello stato
        return str(exc).strip()
    return None


def require_user(credentials: HTTPBasicCredentials = Depends(_basic)) -> str:
    """Autenticazione base: utente e password letti dalle variabili d'ambiente.

    Se le variabili mancano, l'accesso viene negato: mai una pagina aperta a tutti per sbaglio.
    """
    expected_user = os.environ.get("BASIC_AUTH_USER", "")
    expected_password = os.environ.get("BASIC_AUTH_PASSWORD", "")
    if not expected_user or not expected_password:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Autenticazione non configurata (BASIC_AUTH_USER / BASIC_AUTH_PASSWORD).",
        )
    user_ok = secrets.compare_digest(credentials.username.encode(), expected_user.encode())
    password_ok = secrets.compare_digest(credentials.password.encode(), expected_password.encode())
    if not (user_ok and password_ok):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Credenziali non valide.",
            headers={"WWW-Authenticate": 'Basic realm="Bandi Radar"'},
        )
    return credentials.username


@app.get("/health")
def health() -> JSONResponse:
    db_error = _check_database()
    body = {"status": "ok" if db_error is None else "error", "database": "ok" if db_error is None else db_error}
    return JSONResponse(body, status_code=200 if db_error is None else 503)


_PAGE = """<!doctype html>
<html lang="it">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <meta name="robots" content="noindex, nofollow">
  <title>Bandi Radar - in costruzione</title>
  <style>
    body { font-family: system-ui, sans-serif; margin: 0; min-height: 100vh; display: grid; place-items: center;
           background: #f6f7f9; color: #1f2933; }
    main { text-align: center; padding: 2rem; }
    h1 { font-weight: 600; margin-bottom: .5rem; }
    p { color: #52606d; }
  </style>
</head>
<body>
  <main>
    <h1>Bandi Radar</h1>
    <p>Sito in costruzione.</p>
  </main>
</body>
</html>
"""


@app.get("/", response_class=HTMLResponse)
def home(_: str = Depends(require_user)) -> str:
    return _PAGE
