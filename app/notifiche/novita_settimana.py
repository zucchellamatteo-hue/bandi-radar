"""Riepilogo del lunedi': cosa ha trovato la raccolta negli ultimi 7 giorni e come stanno le fonti.

Uso:  python -m app.notifiche.novita_settimana            # invia (o stampa) il riepilogo
      python -m app.notifiche.novita_settimana --stampa   # solo a schermo, niente email, niente registrazione
Il servizio di raccolta lo lancia da solo ogni lunedi' mattina (app/raccolta/demone.py).
"""

from __future__ import annotations

import argparse
import html
import os
import sys
from datetime import date, datetime, timedelta, timezone

from app.db.connessione import connetti
from app.notifiche.email import invia

NOMI_TIPO = {"ue": "Unione europea", "nazionale": "Nazionali", "regione": "Regioni", "camera": "Camere di Commercio",
             "capoluogo": "Comuni capoluogo", "provincia": "Province", "fondazione": "Fondazioni", "contesto": "Dati di contesto"}
MASSIMO_PER_GRUPPO = 25


def raccogli_dati(conn, da: datetime) -> dict:
    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT a.fonte_id, f.nome AS fonte, f.ente, f.tipo, f.territorio, a.titolo, a.url, a.pubblicato_il, a.trovato_il
            FROM annunci a JOIN fonti f ON f.id = a.fonte_id
            WHERE a.trovato_il >= %s
            ORDER BY f.tipo, a.pubblicato_il DESC NULLS LAST, a.trovato_il DESC
            """,
            (da,),
        )
        annunci = cur.fetchall()
        cur.execute(
            """
            SELECT esito, count(*) AS n FROM (
                SELECT DISTINCT ON (fonte_id) fonte_id, esito FROM controlli ORDER BY fonte_id, iniziato_il DESC
            ) u GROUP BY esito ORDER BY esito
            """
        )
        esiti = {r["esito"]: r["n"] for r in cur.fetchall()}
        cur.execute(
            """
            SELECT f.id, f.nome, c.esito, c.messaggio FROM fonti f
            JOIN LATERAL (SELECT esito, messaggio FROM controlli WHERE fonte_id = f.id ORDER BY iniziato_il DESC LIMIT 1) c ON true
            WHERE c.esito IN ('errore', 'struttura_cambiata') ORDER BY c.esito, f.nome
            """
        )
        problemi = cur.fetchall()
        cur.execute("SELECT count(*) AS n FROM fonti WHERE stato <> 'esclusa' AND NOT in_pausa")
        fonti_attive = cur.fetchone()["n"]
    return {"annunci": annunci, "esiti": esiti, "problemi": problemi, "fonti_attive": fonti_attive}


def _gruppi(annunci: list[dict]) -> list[tuple[str, list[dict]]]:
    gruppi: dict[str, list[dict]] = {}
    for a in annunci:
        gruppi.setdefault(a["tipo"], []).append(a)
    ordine = ["ue", "nazionale", "regione", "camera", "capoluogo", "provincia", "fondazione", "contesto"]
    return [(NOMI_TIPO.get(t, t), gruppi[t]) for t in ordine if t in gruppi]


def componi(dati: dict, da: datetime, a: datetime) -> tuple[str, str, str]:
    """Ritorna (oggetto, testo semplice, html)."""
    annunci = dati["annunci"]
    periodo = f"{da.date().strftime('%d/%m')}–{a.date().strftime('%d/%m/%Y')}"
    oggetto = f"Bandi Radar: {len(annunci)} novità nella settimana {periodo}"
    esiti = dati["esiti"]
    stato = (f"Fonti attive: {dati['fonti_attive']}. Ultimo controllo: {esiti.get('ok', 0)} ok, "
             f"{esiti.get('errore', 0)} in errore, {esiti.get('struttura_cambiata', 0)} con struttura cambiata, "
             f"{esiti.get('saltato', 0)} saltate.")

    righe = [oggetto, "", "Attenzione: sono elementi nuovi trovati sulle fonti (avvisi, notizie, bandi), non ancora smistati. "
             "La Fase 3 li trasforma in schede.", "", stato, ""]
    parti_html = [f"<h2 style='font-family:sans-serif'>{html.escape(oggetto)}</h2>",
                  "<p style='font-family:sans-serif;color:#555'>Elementi nuovi trovati sulle fonti, non ancora smistati: "
                  "la Fase 3 li trasforma in schede.</p>",
                  f"<p style='font-family:sans-serif'>{html.escape(stato)}</p>"]
    for nome, voci in _gruppi(annunci):
        righe.append(f"== {nome} ({len(voci)})")
        parti_html.append(f"<h3 style='font-family:sans-serif'>{html.escape(nome)} ({len(voci)})</h3><ul style='font-family:sans-serif'>")
        for v in voci[:MASSIMO_PER_GRUPPO]:
            ente = v["ente"]
            data = v["pubblicato_il"].strftime("%d/%m") if v["pubblicato_il"] else "  -  "
            righe.append(f"- [{ente}] {data} {v['titolo']}\n  {v['url']}")
            parti_html.append(f"<li><b>{html.escape(ente)}</b> {data} <a href='{html.escape(v['url'])}'>{html.escape(v['titolo'])}</a></li>")
        if len(voci) > MASSIMO_PER_GRUPPO:
            righe.append(f"  ... e altri {len(voci) - MASSIMO_PER_GRUPPO}")
            parti_html.append(f"<li>... e altri {len(voci) - MASSIMO_PER_GRUPPO}</li>")
        righe.append("")
        parti_html.append("</ul>")
    if dati["problemi"]:
        righe.append(f"== Fonti con problemi ({len(dati['problemi'])})")
        parti_html.append(f"<h3 style='font-family:sans-serif'>Fonti con problemi ({len(dati['problemi'])})</h3><ul style='font-family:sans-serif'>")
        for p in dati["problemi"]:
            righe.append(f"- {p['nome']}: {p['esito']} ({p['messaggio'] or ''})")
            parti_html.append(f"<li>{html.escape(p['nome'])}: {p['esito']} <i>{html.escape(p['messaggio'] or '')}</i></li>")
        parti_html.append("</ul>")
    return oggetto, "\n".join(righe), "\n".join(parti_html)


def gia_inviato(conn, nome: str, chiave: str) -> bool:
    with conn.cursor() as cur:
        cur.execute("SELECT 1 FROM notifiche_inviate WHERE nome = %s AND chiave = %s", (nome, chiave))
        return cur.fetchone() is not None


def registra_invio(conn, nome: str, chiave: str, esito: str) -> None:
    with conn.cursor() as cur:
        cur.execute("INSERT INTO notifiche_inviate (nome, chiave, esito) VALUES (%s, %s, %s) ON CONFLICT DO NOTHING",
                    (nome, chiave, esito))
    conn.commit()


def invia_riepilogo(solo_stampa: bool = False, forza: bool = False) -> int:
    a = datetime.now(timezone.utc)
    da = a - timedelta(days=7)
    chiave = date.today().isocalendar()
    chiave_settimana = f"{chiave.year}-W{chiave.week:02d}"
    with connetti() as conn:
        if not solo_stampa and not forza and gia_inviato(conn, "novita_settimana", chiave_settimana):
            return 0
        dati = raccogli_dati(conn, da)
        oggetto, testo, corpo_html = componi(dati, da, a)
        if solo_stampa:
            print(testo)
            return 0
        destinatario = os.environ.get("EMAIL_MATTEO")
        if not destinatario:
            print("EMAIL_MATTEO non impostata: riepilogo solo a schermo.\n\n" + testo)
            return 0
        esito = invia(destinatario, oggetto, testo, corpo_html)
        registra_invio(conn, "novita_settimana", chiave_settimana, esito)
        print(f"Riepilogo settimana {chiave_settimana}: {esito} a {destinatario}.")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Riepilogo settimanale delle novita' trovate dalla raccolta.")
    parser.add_argument("--stampa", action="store_true", help="solo a schermo, senza email e senza registrare l'invio")
    parser.add_argument("--forza", action="store_true", help="invia anche se questa settimana e' gia' stato inviato")
    args = parser.parse_args(argv)
    return invia_riepilogo(solo_stampa=args.stampa, forza=args.forza)


if __name__ == "__main__":
    sys.exit(main())
