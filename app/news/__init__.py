"""News (07/10/2026, richiesta di Matteo): brevi notizie per chi segue i bandi, scritte senza codice.

Si scrivono nella pagina "News" della plancia (chi ha il permesso "modifiche", o l'admin) o, per le sessioni di Claude,
con un INSERT nella tabella `news`. Una news nasce in **bozza**; quando e' **pubblicata** e oggi e' nel suo periodo
(da / a) entra nell'email del lunedi' alle imprese (app/notifiche/email_imprese.py), una volta sola per impresa, e
compare in cima alla Guida: alle imprese quelle con pubblico "imprese" o "tutti", ai collaboratori solo "tutti".

Uso:  python -m app.news            # elenco di tutte le news, con stato e periodo
"""

from __future__ import annotations

from datetime import date

PUBBLICI = {"imprese": "solo imprese", "tutti": "imprese e collaboratori"}
STATI = {"bozza": "bozza", "pubblicata": "pubblicata"}
CAMPI = ("titolo", "testo", "link", "da", "a", "pubblico", "stato")
LUNGHEZZA_TESTO = 1200      # "poche righe": l'email resta breve


class ErroreNews(ValueError):
    pass


def _data(x) -> date | None:
    if x in (None, ""):
        return None
    if isinstance(x, date):
        return x
    try:
        return date.fromisoformat(str(x)[:10])
    except ValueError as e:
        raise ErroreNews("Data non valida (serve AAAA-MM-GG).") from e


def _controlla(d: dict, nuova: bool) -> dict:
    v = {k: d[k] for k in CAMPI if k in d}
    for k, massimo in (("titolo", 200), ("testo", LUNGHEZZA_TESTO)):
        if k in v:
            v[k] = " ".join((v[k] or "").split()) if k == "titolo" else (v[k] or "").strip()
            if not v[k]:
                raise ErroreNews("Scrivi il titolo." if k == "titolo" else "Scrivi il testo.")
            if len(v[k]) > massimo:
                raise ErroreNews(f"{'Titolo' if k == 'titolo' else 'Testo'} troppo lungo (al massimo {massimo} caratteri).")
        elif nuova:
            raise ErroreNews("Scrivi il titolo." if k == "titolo" else "Scrivi il testo.")
    if "link" in v:
        v["link"] = (v["link"] or "").strip() or None
        if v["link"] and not (v["link"].startswith(("https://", "http://")) or v["link"].startswith("/")):
            raise ErroreNews("Il link deve iniziare con https:// (oppure / per una pagina di bandinQiaro).")
    if "da" in v:
        v["da"] = _data(v["da"]) or date.today()
    if "a" in v:
        v["a"] = _data(v["a"])
    if v.get("da") and v.get("a") and v["a"] < v["da"]:
        raise ErroreNews("La data di fine viene prima di quella di inizio.")
    if "pubblico" in v and v["pubblico"] not in PUBBLICI:
        raise ErroreNews("Pubblico non valido.")
    if "stato" in v and v["stato"] not in STATI:
        raise ErroreNews("Stato non valido.")
    return v


def elenco(conn) -> list[dict]:
    with conn.cursor() as cur:
        cur.execute("SELECT * FROM news ORDER BY (stato = 'bozza') DESC, da DESC, id DESC")
        return [dict(r) for r in cur.fetchall()]


def crea(conn, d: dict, chi: str) -> dict:
    v = _controlla(d, True)
    colonne = list(v)
    with conn.cursor() as cur:
        cur.execute(f"INSERT INTO news ({', '.join(colonne)}, creata_da, aggiornata_da) VALUES "
                    f"({', '.join(['%s'] * len(colonne))}, %s, %s) RETURNING *", (*v.values(), chi, chi))
        return dict(cur.fetchone())


def modifica(conn, news_id: int, d: dict, chi: str) -> dict:
    v = _controlla(d, False)
    if not v:
        raise ErroreNews("Niente da modificare.")
    with conn.cursor() as cur:
        cur.execute("SELECT da, a FROM news WHERE id = %s", (news_id,))
        prima = cur.fetchone()
        if not prima:
            raise ErroreNews("News non trovata.")
        da, a = v.get("da", prima["da"]), v.get("a", prima["a"])
        if a and da and a < da:
            raise ErroreNews("La data di fine viene prima di quella di inizio.")
        cur.execute(f"UPDATE news SET {', '.join(f'{k} = %s' for k in v)}, aggiornata_il = now(), aggiornata_da = %s "
                    "WHERE id = %s RETURNING *", (*v.values(), chi, news_id))
        return dict(cur.fetchone())


def cancella(conn, news_id: int) -> None:
    with conn.cursor() as cur:
        cur.execute("DELETE FROM news WHERE id = %s", (news_id,))


def attive(conn, oggi: date | None = None, pubblici: tuple[str, ...] = ("imprese", "tutti")) -> list[dict]:
    """Le news pubblicate e nel loro periodo oggi, per i pubblici chiesti; le piu' recenti prima."""
    oggi = oggi or date.today()
    with conn.cursor() as cur:
        cur.execute("""SELECT id, titolo, testo, link, da, a, pubblico FROM news
                       WHERE stato = 'pubblicata' AND da <= %s AND (a IS NULL OR a >= %s) AND pubblico = ANY(%s)
                       ORDER BY da DESC, id DESC""", (oggi, oggi, list(pubblici)))
        return [dict(r) for r in cur.fetchall()]


def per_utente(conn, utente: dict, oggi: date | None = None) -> list[dict]:
    """Le news da mostrare in cima alla Guida: alle imprese "imprese" e "tutti", agli altri solo "tutti"."""
    return attive(conn, oggi, ("imprese", "tutti") if utente.get("ruolo") == "impresa" else ("tutti",))
