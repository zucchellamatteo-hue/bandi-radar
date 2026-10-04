"""Bandi Radar - applicazione web.

Espone:
- GET /health  : stato dell'applicazione e del database, senza autenticazione (usato dal healthcheck)
- /api/accesso : login con email e password, cookie di sessione (app/utenti/api.py, 05/10/2026)
- /api/...     : API della plancia (app/plancia/api.py), solo per chi ha fatto l'accesso, secondo il ruolo
- /            : la plancia (React, cartella plancia/dist costruita nel Dockerfile). I file della pagina sono pubblici
                 (contengono solo il programma, la pagina di accesso compresa); i dati arrivano solo dall'API protetta.
"""

import os
from pathlib import Path

import psycopg
from fastapi import Depends, FastAPI, HTTPException
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse

from app.plancia.api import router as api_plancia
from app.utenti.api import controlla_plancia
from app.utenti.api import router as api_utenti

app = FastAPI(title="Bandi Radar", docs_url=None, redoc_url=None, openapi_url=None)
CARTELLA_PLANCIA = Path(__file__).resolve().parents[1] / "plancia" / "dist"


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


@app.get("/health")
def health() -> JSONResponse:
    db_error = _check_database()
    body = {"status": "ok" if db_error is None else "error", "database": "ok" if db_error is None else db_error}
    return JSONResponse(body, status_code=200 if db_error is None else 503)


_PAGINA_IN_COSTRUZIONE = """<!doctype html><html lang="it"><head><meta charset="utf-8"><meta name="robots" content="noindex">
<title>Bandi Radar</title></head><body style="font-family:system-ui;padding:2rem"><h1>Bandi Radar</h1>
<p>La plancia non e' stata costruita in questa immagine (manca plancia/dist).</p></body></html>"""

app.include_router(api_utenti)
app.include_router(api_plancia, dependencies=[Depends(controlla_plancia)])


@app.get("/{percorso:path}", response_class=HTMLResponse)
def plancia(percorso: str):
    """Serve la plancia: i file costruiti da Vite; qualunque altro percorso torna index.html (app a pagina singola)."""
    if percorso.startswith("api/"):
        raise HTTPException(status_code=404, detail="non trovato")
    if CARTELLA_PLANCIA.is_dir():
        candidato = (CARTELLA_PLANCIA / percorso).resolve() if percorso else None
        if candidato and candidato.is_file() and CARTELLA_PLANCIA in candidato.parents:
            return FileResponse(candidato)
        return FileResponse(CARTELLA_PLANCIA / "index.html")
    return HTMLResponse(_PAGINA_IN_COSTRUZIONE)
