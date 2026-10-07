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
from fastapi import Depends, FastAPI, HTTPException, Request
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse, PlainTextResponse, Response

from app.abbonamenti.api import router as api_abbonamenti
from app.account.api import router as api_account
from app.campagne.api import router as api_campagne
from app.misure.api import router as api_misure
from app.fatture.api import router as api_fatture
from app.guida.api import router as api_guida
from app.passi.api import router as api_passi
from app.news.api import router as api_news
from app.feedback.api import router as api_feedback
from app.segnalazioni.api import router as api_segnalazioni
from app.notifiche.api import router as api_notifiche
from app.impresa.api import router as api_impresa
from app.plancia.api import router as api_plancia
from app import pubblico
from app.pubblico import landing, seo
from app.db.connessione import connetti
from app.utenti.api import COOKIE, controlla_plancia
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
app.include_router(api_feedback)
app.include_router(api_segnalazioni)   # pulsante "Segnala": scrive chiunque abbia fatto l'accesso
app.include_router(api_notifiche)   # email alle imprese (solo admin) e disiscrizione pubblica
app.include_router(api_impresa)
app.include_router(api_abbonamenti)
app.include_router(api_campagne)
app.include_router(api_misure)
app.include_router(api_fatture)
app.include_router(api_passi)
app.include_router(api_news)
app.include_router(api_guida)
app.include_router(api_account)
app.include_router(api_plancia, dependencies=[Depends(controlla_plancia)])


def _presentazione() -> HTMLResponse:
    with connetti() as conn:
        return HTMLResponse(pubblico.presentazione(conn))


@app.get("/presentazione", response_class=HTMLResponse)
def presentazione():
    """La pagina pubblica (app/pubblico): sempre visibile qui, anche quando non e' ancora accesa su "/"."""
    return _presentazione()


@app.get("/robots.txt", response_class=PlainTextResponse)
def robots_txt():
    """Finche' la pagina pubblica e' spenta chiude tutto; da accesa apre solo le pagine pubbliche (app/pubblico/seo.py)."""
    return PlainTextResponse(seo.robots_txt(pubblico.pubblica()))


@app.get("/sitemap.xml")
def sitemap_xml():
    return Response(seo.sitemap_xml(), media_type="application/xml")


@app.get("/llms.txt", response_class=PlainTextResponse)
def llms_txt():
    """Descrizione del servizio per i motori di risposta IA (proposta llmstxt.org), con i numeri del giorno."""
    with connetti() as conn:
        return PlainTextResponse(landing.llms_txt(conn), media_type="text/markdown; charset=utf-8")


@app.get("/favicon.svg")
def favicon():
    return Response(pubblico.LOGO.replace('width="28" height="28" ', 'xmlns="http://www.w3.org/2000/svg" ')
                    .replace(' aria-hidden="true"', ""), media_type="image/svg+xml",
                    headers={"Cache-Control": "public, max-age=604800"})


@app.get("/immagini/{nome}")
def immagine(nome: str):
    """Immagini della parte pubblica (anteprima per i social, logo): solo i file di app/pubblico/immagini."""
    file = (pubblico.IMMAGINI / nome).resolve()
    if file.parent != pubblico.IMMAGINI or not file.is_file():
        raise HTTPException(status_code=404, detail="non trovato")
    return FileResponse(file, headers={"Cache-Control": "public, max-age=604800"})


@app.get("/termini", response_class=HTMLResponse)
@app.get("/privacy", response_class=HTMLResponse)
@app.get("/cookie", response_class=HTMLResponse)
@app.get("/condizioni-supporto", response_class=HTMLResponse)
@app.get("/note-legali", response_class=HTMLResponse)
def testo_legale(request: Request):
    return HTMLResponse(pubblico.legale(request.url.path.strip("/")))


@app.get("/{percorso:path}", response_class=HTMLResponse)
def plancia(percorso: str, request: Request):
    """Serve la plancia: i file costruiti da Vite; qualunque altro percorso torna index.html (app a pagina singola).
    Con PAGINA_PUBBLICA=1 chi arriva su "/" senza aver fatto l'accesso vede la presentazione."""
    if percorso.startswith("api/"):
        raise HTTPException(status_code=404, detail="non trovato")
    if percorso == "" and pubblico.pubblica() and not request.cookies.get(COOKIE):
        return _presentazione()
    if CARTELLA_PLANCIA.is_dir():
        candidato = (CARTELLA_PLANCIA / percorso).resolve() if percorso else None
        if candidato and candidato.is_file() and CARTELLA_PLANCIA in candidato.parents:
            return FileResponse(candidato)
        return FileResponse(CARTELLA_PLANCIA / "index.html")
    return HTMLResponse(_PAGINA_IN_COSTRUZIONE)
