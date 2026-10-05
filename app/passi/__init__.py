"""Prossimi passi (05/10/2026): promemoria e lavori da fare, modificabili da Matteo nella plancia.

Le sessioni di Claude Code li leggono come elenco dei lavori aperti: python -m app.passi (testo) o la pagina
"Prossimi passi". Chi vede: l'admin (modifica) e chi ha il permesso "lavoro" (sola lettura).
"""

from __future__ import annotations

TIPI = {"promemoria": "promemoria", "da_sviluppare": "da sviluppare", "decisione": "decisione"}
STATI = {"da_fare": "da fare", "in_corso": "in corso", "fatto": "fatto", "rimandato": "rimandato"}
CAMPI = ("titolo", "dettaglio", "tipo", "stato", "priorita", "chi")


class ErrorePasso(ValueError):
    pass


def _controlla(d: dict, nuovo: bool) -> dict:
    v = {k: d[k] for k in CAMPI if k in d}
    if "titolo" in v:
        v["titolo"] = (v["titolo"] or "").strip()[:300]
        if not v["titolo"]:
            raise ErrorePasso("Scrivi il titolo.")
    elif nuovo:
        raise ErrorePasso("Scrivi il titolo.")
    if "tipo" in v and v["tipo"] not in TIPI:
        raise ErrorePasso("Tipo non valido.")
    if "stato" in v and v["stato"] not in STATI:
        raise ErrorePasso("Stato non valido.")
    if "priorita" in v and v["priorita"] not in (1, 2, 3):
        raise ErrorePasso("Priorità da 1 (alta) a 3 (bassa).")
    for k in ("dettaglio", "chi"):
        if k in v:
            v[k] = (v[k] or "").strip()[:4000] or None
    return v


def elenco(conn, anche_fatti: bool = True) -> list[dict]:
    with conn.cursor() as cur:
        cur.execute(f"""SELECT * FROM prossimi_passi {'' if anche_fatti else "WHERE stato NOT IN ('fatto')"}
                        ORDER BY CASE stato WHEN 'in_corso' THEN 0 WHEN 'da_fare' THEN 1 WHEN 'rimandato' THEN 2 ELSE 3 END,
                                 priorita, id""")
        return [dict(r) for r in cur.fetchall()]


def crea(conn, d: dict, chi: str) -> dict:
    v = _controlla(d, True)
    colonne = list(v)
    with conn.cursor() as cur:
        cur.execute(f"INSERT INTO prossimi_passi ({', '.join(colonne)}, aggiornato_da) VALUES "
                    f"({', '.join(['%s'] * len(colonne))}, %s) RETURNING *", (*v.values(), chi))
        return dict(cur.fetchone())


def modifica(conn, passo_id: int, d: dict, chi: str) -> dict:
    v = _controlla(d, False)
    if not v:
        raise ErrorePasso("Niente da modificare.")
    with conn.cursor() as cur:
        cur.execute(f"UPDATE prossimi_passi SET {', '.join(f'{k} = %s' for k in v)}, aggiornato_il = now(), aggiornato_da = %s "
                    "WHERE id = %s RETURNING *", (*v.values(), chi, passo_id))
        r = cur.fetchone()
    if not r:
        raise ErrorePasso("Passo non trovato.")
    return dict(r)


def cancella(conn, passo_id: int) -> None:
    with conn.cursor() as cur:
        cur.execute("DELETE FROM prossimi_passi WHERE id = %s", (passo_id,))


def testo(passi: list[dict]) -> str:
    """Elenco leggibile per le sessioni di Claude Code: i passi aperti, dal piu' urgente."""
    righe = []
    for p in passi:
        if p["stato"] == "fatto":
            continue
        righe.append(f"- [{STATI[p['stato']]}, priorità {p['priorita']}, {TIPI[p['tipo']]}{', ' + p['chi'] if p.get('chi') else ''}] "
                     f"#{p['id']} {p['titolo']}" + (f"\n  {p['dettaglio']}" if p.get("dettaglio") else ""))
    return "\n".join(righe) or "Nessun passo aperto."
