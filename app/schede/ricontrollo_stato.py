"""Ricontrollo settimanale dello stato dei bandi proponibili, senza IA (piano del 03/10/2026, punto 1).

La verifica a campione del 02/10 ha trovato bandi "aperti" che la pagina ufficiale dava per chiusi: la smentita non
sta nel testo del bando ma nell'avviso pubblicato dopo sulla pagina ("piattaforma chiusa", "dotazione esaurita").
Qui, come l'osservatore delle fonti: si riscarica la pagina ufficiale (robots.txt, User-Agent di Bandi Radar, una
pagina per sito alla volta), si confronta con la versione salvata e si cercano frasi di chiusura **solo nelle righe
nuove** (le formule "salvo chiusura anticipata" stanno nel testo da sempre). Se compaiono, la scheda diventa "da
aggiornare" con il motivo e la pagina salvata prende il testo di oggi, cosi' la nuova scheda lo legge.

A mano:  python -m app.schede.ricontrollo_stato --bando 427
"""

from __future__ import annotations

import argparse
import re
import sys

GIORNI = 7          # ogni bando proponibile non chiuso si ricontrolla una volta a settimana
PER_GIRO = 10       # pagine per giro del regista (ogni ora): ~500 bandi in due giorni, poi pochi al giorno

# Frasi che dicono che le domande non si possono piu' presentare. Non "fino a esaurimento delle risorse", non "salvo
# chiusura anticipata", non "lo sportello potra' essere sospeso": sono le formule dei bandi aperti.
FRASI_CHIUSURA = re.compile(
    r"piattaforma (?:e' |è |risulta )?(?:chiusa|disattivata)"
    r"|termini (?:di presentazione )?(?:sono |risultano )?(?:scaduti|chiusi)"
    r"|sportell[oi] (?:e' |è |sono |risulta |risultano )(?:temporaneamente )?(?:chius|sospes)"
    r"|chiusura (?:anticipata|dello sportello|dei termini) (?:e' |è )?(?:stata )?disposta"
    r"|si procede alla chiusura"
    r"|(?:risorse|fondi|dotazione(?: finanziaria)?)[^.]{0,40}(?:sono|risultano|e'|è) (?:state )?esaurit[eai]"
    r"|non (?:e' |è )?(?:pi[uù]|piu') possibile presentare"
    r"|domande non (?:sono |verranno )?(?:pi[uù]|piu') (?:accettate|ricevibili)"
    r"|\bbando chiuso\b|opportunit[aà] scaduta"
    r"|stato(?: atto| del bando| bando)?\s*:?\s*(?:scaduto|chiuso|concluso)"
    r"|(?:bando|avviso|misura|sportello|presentazione delle domande) (?:e' |è |viene |risulta )(?:temporaneamente )?sospes[oa]",
    re.IGNORECASE)
_SPAZI = re.compile(r"\s+")


def _righe(testo: str | None) -> list[str]:
    return [r for r in (_SPAZI.sub(" ", x).strip() for x in (testo or "").splitlines()) if r]


def righe_nuove(prima: str | None, oggi: str | None) -> str:
    """Le righe del testo di oggi che non c'erano nella versione salvata (confronto per righe, come l'osservatore)."""
    vecchie = {r.lower() for r in _righe(prima)}
    return "\n".join(r for r in _righe(oggi) if r.lower() not in vecchie)


def frasi_di_chiusura(prima: str | None, oggi: str | None) -> list[str]:
    """Le frasi di chiusura comparse rispetto alla versione salvata, cercate solo nelle righe nuove."""
    nuovo = righe_nuove(prima, oggi)
    return [_SPAZI.sub(" ", nuovo[max(0, m.start() - 80): m.end() + 80]).strip() for m in FRASI_CHIUSURA.finditer(nuovo)]


def da_ricontrollare(conn, limite: int = PER_GIRO, bando_id: int | None = None) -> list[dict]:
    with conn.cursor() as cur:
        if bando_id:
            cur.execute("SELECT id, url FROM bandi WHERE id = %s", (bando_id,))
        else:
            cur.execute("""SELECT id, url FROM bandi
                           WHERE completezza = 'bando_ufficiale' AND coalesce(stato, '') <> 'chiuso' AND unito_a IS NULL
                             AND da_aggiornare IS NULL AND coalesce(preliminare->>'per_imprese', '') <> 'no'
                             AND (stato_ricontrollato_il IS NULL OR stato_ricontrollato_il < now() - make_interval(days => %s))
                           ORDER BY stato_ricontrollato_il NULLS FIRST, id LIMIT %s""", (GIORNI, limite))
        return [dict(r) for r in cur.fetchall()]


def ricontrolla(conn, bandi: list[dict], scarica_testo=None) -> dict:
    """Per ogni bando: pagina di oggi, confronto, eventuale "da aggiornare". `scarica_testo(url) -> str | None` si
    puo' sostituire nei test. Ritorna i conteggi."""
    from app.catena.regista import evento

    if scarica_testo is None:
        scarica_testo = _scaricatore()
    conti = {"controllati": 0, "chiusure": 0, "cambiati": 0, "errori": 0}
    for b in bandi:
        with conn.cursor() as cur:
            cur.execute("""SELECT id, url, testo_estratto FROM allegati WHERE bando_id = %s AND annuncio_id IS NULL
                           AND tipo = 'pagina' AND errore IS NULL ORDER BY id DESC LIMIT 1""", (b["id"],))
            pagina = cur.fetchone()
        url = (pagina and pagina["url"]) or b["url"]
        try:
            oggi = scarica_testo(url) if url else None
        except Exception as exc:  # noqa: BLE001 - rete, robots.txt: si riprova la settimana dopo
            oggi, errore = None, f"{type(exc).__name__}: {exc}"[:200]
        else:
            errore = None if oggi else "pagina vuota o non scaricata"
        conti["controllati"] += 1
        with conn.cursor() as cur:
            cur.execute("UPDATE bandi SET stato_ricontrollato_il = now() WHERE id = %s", (b["id"],))
            if errore:
                conti["errori"] += 1
                evento(cur, "bando", b["id"], "ricontrollo stato", "errore", errore)
                conn.commit()
                continue
            prima = pagina["testo_estratto"] if pagina else None
            frasi = frasi_di_chiusura(prima, oggi)
            cambiato = _righe(prima) != _righe(oggi)
            conti["cambiati"] += cambiato
            if frasi:
                conti["chiusure"] += 1
                motivo = f"chiusura? {frasi[0]}"[:300]
                cur.execute("SELECT set_config('bandi_radar.causa', %s, true)", ("ricontrollo dello stato: " + motivo,))
                cur.execute("UPDATE bandi SET da_aggiornare = %s WHERE id = %s", (motivo, b["id"]))
                if pagina:   # la nuova scheda deve leggere la pagina di oggi, con l'avviso di chiusura
                    cur.execute("UPDATE allegati SET testo_estratto = %s, scaricato_il = now() WHERE id = %s",
                                (oggi, pagina["id"]))
                evento(cur, "bando", b["id"], "ricontrollo stato", "possibile chiusura", motivo)
            else:
                evento(cur, "bando", b["id"], "ricontrollo stato", "pagina cambiata" if cambiato else "nessun cambio")
        conn.commit()
    return conti


def _scaricatore():
    """Scarica una pagina con le buone maniere: robots.txt, User-Agent, pausa tra due pagine dello stesso sito."""
    from app.raccolta.scarica import nuovo_client, scarica
    from app.schede.allegati import Pausa, testo_html, testo_pdf

    client = nuovo_client()
    pausa = Pausa(client)

    def scarica_testo(url: str) -> str | None:
        pausa.attendi(url)
        r = scarica(client, url)
        r.raise_for_status()
        if "pdf" in r.headers.get("content-type", ""):
            return testo_pdf(r.content)
        return testo_html(r.text)

    return scarica_testo


def main(argv: list[str] | None = None) -> int:
    from app.db.connessione import connetti

    parser = argparse.ArgumentParser(description="Ricontrollo dello stato dei bandi proponibili (senza IA).")
    parser.add_argument("--bando", type=int, metavar="ID")
    parser.add_argument("--limite", type=int, default=PER_GIRO)
    args = parser.parse_args(argv)
    with connetti() as conn:
        print(ricontrolla(conn, da_ricontrollare(conn, args.limite, args.bando)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
