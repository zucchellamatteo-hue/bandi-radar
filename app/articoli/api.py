"""API del blog per la plancia: elenco e anteprima con il permesso "lavoro", scrittura con "modifiche"; pubblicare,
rimettere in bozza e archiviare solo l'admin (app/articoli)."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException

from app import articoli
from app.pubblico import indexnow
from app.db.connessione import connetti
from app.utenti.api import richiede

router = APIRouter(prefix="/api")


def _chi(u: dict) -> str:
    return u.get("nome") or u["email"]


def _errore(e: Exception) -> HTTPException:
    if isinstance(e, PermissionError):
        return HTTPException(status_code=403, detail=str(e))
    return HTTPException(status_code=404 if "non trovato" in str(e) else 422, detail=str(e))


@router.get("/articoli")
def elenco(_: dict = Depends(richiede("lavoro"))) -> dict:
    from app import misure

    with connetti() as conn:
        voci = articoli.elenco(conn)
        for a in voci:
            a["parole"] = articoli.parole(a["corpo"])
            a["chiuso"] = articoli.situazione_collegata(conn, a)
    return {"articoli": voci, "stati": articoli.STATI, "autore_predefinito": articoli.autore_predefinito(),
            "misure": [{"id": m["id"], "nome": m["nome"]} for m in misure.tutte()]}


@router.post("/articoli")
def crea(dati: dict, utente: dict = Depends(richiede("modifiche"))) -> dict:
    with connetti() as conn:
        try:
            r = articoli.crea(conn, dati, _chi(utente))
        except (articoli.ErroreArticoli, PermissionError) as e:
            raise _errore(e) from e
        conn.commit()
    return r


@router.patch("/articoli/{articolo_id}")
def modifica(articolo_id: int, dati: dict, utente: dict = Depends(richiede("modifiche"))) -> dict:
    with connetti() as conn:
        prima = articoli.leggi(conn, articolo_id)
        try:
            r = articoli.modifica(conn, articolo_id, dati, _chi(utente), admin=utente["ruolo"] == "admin")
        except (articoli.ErroreArticoli, PermissionError) as e:
            raise _errore(e) from e
        conn.commit()
    indexnow.articolo_cambiato(prima, r)       # avvisa Bing e gli altri motori, in disparte (09/10)
    return r


@router.delete("/articoli/{articolo_id}")
def cancella(articolo_id: int, utente: dict = Depends(richiede("modifiche"))) -> dict:
    with connetti() as conn:
        prima = articoli.leggi(conn, articolo_id)
        try:
            articoli.cancella(conn, articolo_id, admin=utente["ruolo"] == "admin")
        except (articoli.ErroreArticoli, PermissionError) as e:
            raise _errore(e) from e
        conn.commit()
    if prima:
        indexnow.articolo_cambiato(prima, prima | {"stato": "cancellato"})
    return {"cancellato": True}


@router.post("/articoli/anteprima")
def anteprima(dati: dict, _: dict = Depends(richiede("lavoro"))) -> dict:
    """La pagina pubblica come apparira', anche per un testo non ancora salvato (nessuna scrittura)."""
    from app.pubblico import blog

    try:
        v = articoli._controlla({k: dati.get(k) for k in articoli.CAMPI_TESTO if k in dati}, True)
    except articoli.ErroreArticoli as e:
        raise _errore(e) from e
    v["fonti"] = articoli._fonti(dati.get("fonti"))
    with connetti() as conn:
        precedente = articoli.leggi(conn, int(dati["id"])) if str(dati.get("id") or "").isdigit() else None
        a = (precedente or {}) | v
        a.setdefault("stato", "bozza")
        return {"html": blog.pagina_articolo(conn, a, anteprima=True)}
