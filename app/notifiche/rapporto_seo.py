"""Rapporto SEO/GEO per Matteo (07/10/2026, richiesta di Matteo): ogni mattina (o ogni lunedi') un'email con
l'andamento delle pagine pubbliche, dai contatori anonimi della tabella `visite` (app/visite).

Contenuto: visite di persone (ieri contro il giorno prima e totale degli ultimi 7 giorni; in modalita' settimanale
ultimi 7 giorni contro i 7 prima), pagine piu' viste, provenienze (Google, Bing, motori IA evidenziati), letture dei
programmi IA e dei motori di ricerca pagina per pagina, nuove registrazioni delle imprese e la riga di Google Search
Console (dal 09/10 con la chiave GSC_CHIAVE_JSON_B64, app/pubblico/search_console.py; senza: "non ancora collegato").

Frequenza: RAPPORTO_SEO nel .env = giornaliero (di base) | settimanale (il lunedi') | spento. Parte dalle 7 dal
servizio di raccolta (app/raccolta/demone.py), una volta sola per giorno o settimana (tabella notifiche_inviate,
nome "rapporto_seo"), a EMAIL_MATTEO.

Uso:  python -m app.notifiche.rapporto_seo            # invia (o stampa senza chiave Resend)
      python -m app.notifiche.rapporto_seo --stampa   # solo a schermo, niente email, niente registrazione
"""

from __future__ import annotations

import argparse
import html
import os
import sys
from datetime import date, datetime, timedelta

from app import visite
from app.db.connessione import connetti
from app.notifiche.email import invia
from app.notifiche.novita_settimana import gia_inviato, registra_invio

NOME = "rapporto_seo"
FREQUENZE = ("giornaliero", "settimanale", "spento")
ORA = 7                      # dalle 7 del mattino
MASSIMO_RIGHE = 15


def frequenza() -> str:
    f = (os.environ.get("RAPPORTO_SEO") or "giornaliero").strip().lower()
    return f if f in FREQUENZE else "giornaliero"


def chiave(oggi: date, freq: str | None = None) -> str:
    """Una chiave per giorno (giornaliero) o per settimana ISO (settimanale): il rapporto parte una volta sola."""
    if (freq or frequenza()) == "settimanale":
        c = oggi.isocalendar()
        return f"{c.year}-W{c.week:02d}"
    return oggi.isoformat()


def da_inviare(adesso: datetime, freq: str | None = None) -> bool:
    """E' l'ora di mandarlo? (giornaliero: ogni giorno dalle 7; settimanale: il lunedi' dalle 7; spento: mai)."""
    f = freq or frequenza()
    if f == "spento" or adesso.hour < ORA:
        return False
    return f == "giornaliero" or adesso.weekday() == 0


def periodi(oggi: date, freq: str) -> dict:
    """Periodo del rapporto e periodo di confronto (date comprese), piu' gli ultimi 7 giorni interi."""
    ieri = oggi - timedelta(days=1)
    sette = (oggi - timedelta(days=7), ieri)
    if freq == "settimanale":
        return {"corrente": sette, "precedente": (oggi - timedelta(days=14), oggi - timedelta(days=8)), "sette": sette,
                "nome_corrente": "ultimi 7 giorni", "nome_precedente": "7 giorni prima"}
    return {"corrente": (ieri, ieri), "precedente": (ieri - timedelta(days=1), ieri - timedelta(days=1)), "sette": sette,
            "nome_corrente": f"ieri {ieri:%d/%m}", "nome_precedente": f"il giorno prima {ieri - timedelta(days=1):%d/%m}"}


def dati_search_console(conn, da: date, a: date) -> dict | None:
    """Google Search Console (09/10, app/pubblico/search_console.py): impressioni, clic, posizione media, query e
    pagine principali degli ultimi 7 giorni disponibili (i dati arrivano con 2-3 giorni di ritardo). None senza la
    chiave GSC_CHIAVE_JSON_B64 nel .env; {"errore": ...} se Google non risponde (il rapporto parte lo stesso)."""
    from app.pubblico import search_console

    try:
        return search_console.dati()
    except Exception as e:  # noqa: BLE001 - il rapporto non deve cadere per Search Console
        return {"errore": f"Search Console non letta ({type(e).__name__})"}


def righe_search_console(sc: dict | None) -> list[str]:
    """Le righe di testo della sezione Search Console del rapporto."""
    if sc is None:
        return ["Search Console: non ancora collegato. Si accende con GSC_CHIAVE_JSON_B64 nel .env."]
    if "errore" in sc:
        return [f"Search Console: {sc['errore']}."]
    righe = [f"Search Console dal {sc['da']:%d/%m} al {sc['a']:%d/%m} (i dati arrivano con 2-3 giorni di ritardo): "
             f"{sc['impressioni']} impressioni, {sc['clic']} clic, CTR {sc['ctr']}%, posizione media {sc['posizione']}."]
    for titolo, chiave_sc in (("Ricerche principali", "query"), ("Pagine principali", "pagine")):
        if sc[chiave_sc]:
            righe.append(f"{titolo}: " + "; ".join(f"{t} ({c} clic, {i} impressioni, pos. {p})"
                                                   for t, c, i, p in sc[chiave_sc][:10]))
    return righe


def raccogli(conn, oggi: date, freq: str) -> dict:
    p = periodi(oggi, freq)
    (c1, c2), (p1, p2), (s1, s2) = p["corrente"], p["precedente"], p["sette"]
    da, a = min(p1, s1), max(c2, s2)
    with conn.cursor() as cur:
        cur.execute("""SELECT giorno, percorso, provenienza, utm_source, visitatore, programma, sum(conteggio) AS n
                       FROM visite WHERE giorno BETWEEN %s AND %s GROUP BY 1, 2, 3, 4, 5, 6""", (da, a))
        righe = cur.fetchall()
        cur.execute("""SELECT count(*) FILTER (WHERE creato_il::date BETWEEN %(c1)s AND %(c2)s) AS corrente,
                              count(*) FILTER (WHERE creato_il::date BETWEEN %(p1)s AND %(p2)s) AS precedente,
                              count(*) FILTER (WHERE creato_il::date BETWEEN %(s1)s AND %(s2)s) AS sette,
                              count(*) FILTER (WHERE creato_il::date BETWEEN %(s1)s AND %(s2)s AND creato_da IS NULL) AS sette_da_sola
                       FROM utenti WHERE ruolo = 'impresa'""", {"c1": c1, "c2": c2, "p1": p1, "p2": p2, "s1": s1, "s2": s2})
        registrazioni = dict(cur.fetchone())

    def somma(filtro, inizio, fine) -> int:
        return sum(r["n"] for r in righe if inizio <= r["giorno"] <= fine and filtro(r))

    def tre(filtro) -> dict:
        return {"corrente": somma(filtro, c1, c2), "precedente": somma(filtro, p1, p2), "sette": somma(filtro, s1, s2)}

    persona = lambda r: r["visitatore"] == "persona"  # noqa: E731
    blog = lambda r: persona(r) and r["percorso"].startswith("/blog")  # noqa: E731

    def da_ia(r) -> bool:
        return persona(r) and (visite.gruppo_provenienza(r["provenienza"]) == "ia"
                               or visite.gruppo_provenienza(visite._dominio(r["utm_source"])) == "ia")

    pagine: dict[str, dict] = {}
    provenienze: dict[str, dict] = {}
    programmi: dict[tuple, dict] = {}
    for r in righe:
        in_c, in_s = c1 <= r["giorno"] <= c2, s1 <= r["giorno"] <= s2
        if persona(r):
            v = pagine.setdefault(r["percorso"], {"corrente": 0, "sette": 0})
            dove = provenienze.setdefault(r["provenienza"], {"corrente": 0, "sette": 0,
                                                             "gruppo": visite.gruppo_provenienza(r["provenienza"])})
            for x in (v, dove):
                x["corrente"] += r["n"] if in_c else 0
                x["sette"] += r["n"] if in_s else 0
        elif r["visitatore"] in ("ia", "motore"):
            v = programmi.setdefault((r["visitatore"], r["programma"], r["percorso"]), {"corrente": 0, "sette": 0})
            v["corrente"] += r["n"] if in_c else 0
            v["sette"] += r["n"] if in_s else 0
    ordina = lambda d: sorted(d.items(), key=lambda kv: (-kv[1]["sette"], -kv[1]["corrente"], str(kv[0])))  # noqa: E731
    return {
        "frequenza": freq, "periodi": p,
        "persone": tre(persona), "blog": tre(blog), "da_ia": tre(da_ia),
        "da_google": tre(lambda r: persona(r) and r["provenienza"].startswith("google.")),
        "da_bing": tre(lambda r: persona(r) and r["provenienza"] in ("bing.com", "cn.bing.com")),
        "letture_ia": tre(lambda r: r["visitatore"] == "ia"), "letture_motori": tre(lambda r: r["visitatore"] == "motore"),
        "pagine": ordina(pagine), "provenienze": ordina(provenienze), "programmi": ordina(programmi),
        "registrazioni": registrazioni, "search_console": dati_search_console(conn, s1, s2),
    }


def _variazione(corrente: int, precedente: int) -> str:
    if corrente == precedente:
        return "="
    segno = "+" if corrente > precedente else "−"
    if not precedente:
        return f"{segno}{abs(corrente - precedente)}"
    return f"{segno}{abs(corrente - precedente)} ({segno}{abs(round(100 * (corrente - precedente) / precedente))}%)"


def componi(d: dict, oggi: date) -> tuple[str, str, str]:
    """(oggetto, testo semplice, html)."""
    p = d["periodi"]
    settimanale = d["frequenza"] == "settimanale"
    nc, np_ = p["nome_corrente"], p["nome_precedente"]
    oggetto = (f"bandinQiaro SEO/GEO {'settimana al' if settimanale else 'del'} {oggi:%d/%m}: "
               f"{d['persone']['corrente']} visite di persone, {d['da_ia']['corrente']} dai motori IA")
    s1, s2 = p["sette"]
    righe_numeri = [
        ("Visite di persone (tutte le pagine pubbliche)", d["persone"]),
        ("  di cui al blog e agli articoli", d["blog"]),
        ("Persone arrivate da Google", d["da_google"]),
        ("Persone arrivate da Bing", d["da_bing"]),
        ("Persone arrivate da motori IA (ChatGPT, Perplexity, Gemini, Copilot, Claude...)", d["da_ia"]),
        ("Letture dei programmi IA (GPTBot, ClaudeBot, PerplexityBot...)", d["letture_ia"]),
        ("Letture dei motori di ricerca (Googlebot, Bingbot...)", d["letture_motori"]),
    ]
    reg = d["registrazioni"]
    righe_numeri.append(("Nuove imprese registrate", {"corrente": reg["corrente"], "precedente": reg["precedente"], "sette": reg["sette"]}))
    righe_sc = righe_search_console(d["search_console"])

    t = [oggetto, "", f"Confronto: {nc} contro {np_}" + ("" if settimanale else f"; ultimi 7 giorni = {s1:%d/%m}–{s2:%d/%m}."), ""]
    for nome, v in righe_numeri:
        sette = "" if settimanale else f" · 7 giorni: {v['sette']}"
        t.append(f"- {nome}: {v['corrente']} ({_variazione(v['corrente'], v['precedente'])} su {v['precedente']}){sette}")
    t.append(f"  (registrate da sole dal sito negli ultimi 7 giorni: {reg['sette_da_sola']}; le altre su invito)")
    t += [""] + righe_sc + [""]

    def tabella_testo(titolo, voci, nome_voce):
        t.append(f"== {titolo}")
        if not voci:
            t.append("  nessuna")
        for chiave_v, v in voci[:MASSIMO_RIGHE]:
            t.append(f"- {nome_voce(chiave_v, v)}: {v['corrente']} {'' if settimanale else '(7 giorni: ' + str(v['sette']) + ')'}".rstrip())
        t.append("")

    tabella_testo("Pagine più viste dalle persone", d["pagine"], lambda k, v: k)
    tabella_testo("Da dove arrivano le persone", d["provenienze"],
                  lambda k, v: k + (" [MOTORE IA]" if v["gruppo"] == "ia" else ""))
    tabella_testo("Programmi IA e motori, pagina per pagina", d["programmi"],
                  lambda k, v: f"{'IA' if k[0] == 'ia' else 'motore'} {k[1]} su {k[2]}")
    t.append("Solo conteggi anonimi, senza cookie: dettagli nella pagina Visite della plancia. "
             "RAPPORTO_SEO nel .env: giornaliero, settimanale o spento.")

    # HTML semplice, leggibile anche nei programmi di posta piu' spartani.
    st = "font-family:system-ui,-apple-system,'Segoe UI',Roboto,Arial,sans-serif;"
    cella = "padding:4px 8px;border-bottom:1px solid #e2e8f0;text-align:left"
    h = [f"<div style=\"{st}max-width:680px;margin:0 auto;color:#1c2430\"><h2 style='color:#163e7a'>{html.escape(oggetto)}</h2>",
         f"<p style='color:#56606e'>Confronto: {html.escape(nc)} contro {html.escape(np_)}"
         + ("" if settimanale else f"; ultimi 7 giorni = {s1:%d/%m}–{s2:%d/%m}") + ".</p>",
         f"<table style='border-collapse:collapse;width:100%'><tr><th style='{cella}'></th><th style='{cella}'>{html.escape(nc)}</th>"
         f"<th style='{cella}'>{html.escape(np_)}</th>" + ("" if settimanale else f"<th style='{cella}'>7 giorni</th>") + "</tr>"]
    for nome, v in righe_numeri:
        evid = " style='background:#eef4fd'" if "IA" in nome else ""
        h.append(f"<tr{evid}><td style='{cella}'>{html.escape(nome)}</td><td style='{cella}'><b>{v['corrente']}</b> "
                 f"<small style='color:#56606e'>{html.escape(_variazione(v['corrente'], v['precedente']))}</small></td>"
                 f"<td style='{cella}'>{v['precedente']}</td>" + ("" if settimanale else f"<td style='{cella}'>{v['sette']}</td>") + "</tr>")
    h.append("</table>")
    h.append(f"<p style='color:#56606e;font-size:13px'>Imprese registrate da sole dal sito negli ultimi 7 giorni: "
             f"{reg['sette_da_sola']}; le altre su invito.</p><p><b>{html.escape(righe_sc[0])}</b></p>"
             + "".join(f"<p style='font-size:14px'>{html.escape(r)}</p>" for r in righe_sc[1:]))

    def tabella_html(titolo, voci, nome_voce, evidenzia=lambda k, v: False):
        h.append(f"<h3 style='color:#163e7a;margin-bottom:4px'>{html.escape(titolo)}</h3>")
        if not voci:
            h.append("<p style='color:#56606e'>nessuna</p>")
            return
        h.append(f"<table style='border-collapse:collapse;width:100%'><tr><th style='{cella}'></th><th style='{cella}'>{html.escape(nc)}</th>"
                 + ("" if settimanale else f"<th style='{cella}'>7 giorni</th>") + "</tr>")
        for k, v in voci[:MASSIMO_RIGHE]:
            evid = " style='background:#eef4fd;font-weight:600'" if evidenzia(k, v) else ""
            h.append(f"<tr{evid}><td style='{cella}'>{html.escape(nome_voce(k, v))}</td><td style='{cella}'>{v['corrente']}</td>"
                     + ("" if settimanale else f"<td style='{cella}'>{v['sette']}</td>") + "</tr>")
        h.append("</table>")

    tabella_html("Pagine più viste dalle persone", d["pagine"], lambda k, v: k)
    tabella_html("Da dove arrivano le persone", d["provenienze"],
                 lambda k, v: k + (" (motore IA)" if v["gruppo"] == "ia" else ""), lambda k, v: v["gruppo"] == "ia")
    tabella_html("Programmi IA e motori, pagina per pagina", d["programmi"],
                 lambda k, v: f"{k[1]} ({'IA' if k[0] == 'ia' else 'motore'}) su {k[2]}", lambda k, v: k[0] == "ia")
    h.append("<p style='color:#56606e;font-size:13px'>Solo conteggi anonimi, senza cookie: dettagli nella pagina "
             "<b>Visite</b> della plancia. Frequenza: RAPPORTO_SEO nel .env (giornaliero, settimanale o spento).</p></div>")
    return oggetto, "\n".join(t), "\n".join(h)


def invia_rapporto(solo_stampa: bool = False, forza: bool = False, oggi: date | None = None) -> str:
    """Manda il rapporto a EMAIL_MATTEO, una volta per giorno o settimana. Senza destinatario lo registra come "non
    inviato" con il motivo, come il riepilogo del lunedi'."""
    freq = frequenza()
    if freq == "spento" and not (solo_stampa or forza):
        return "spento (RAPPORTO_SEO=spento)"
    if freq == "spento":
        freq = "giornaliero"
    oggi = oggi or date.today()
    k = chiave(oggi, freq)
    with connetti() as conn:
        if not solo_stampa and not forza and gia_inviato(conn, NOME, k):
            return "gia' inviato"
        oggetto, testo, corpo = componi(raccogli(conn, oggi, freq), oggi)
        if solo_stampa:
            print(testo)
            return "solo a schermo"
        destinatario = os.environ.get("EMAIL_MATTEO")
        if not destinatario:
            registra_invio(conn, NOME, k, "non inviato: manca EMAIL_MATTEO nel .env")
            return "non inviato: manca EMAIL_MATTEO nel .env"
        esito = invia(destinatario, oggetto, testo, f"<html><body>{corpo}</body></html>")
        registra_invio(conn, NOME, k, esito)
    return f"{esito} a {destinatario}"


def gia_inviato_adesso(oggi: date | None = None) -> bool:
    """Il rapporto di oggi (o di questa settimana) e' gia' partito? Serve al demone per non registrare esecuzioni vuote."""
    with connetti() as conn:
        return gia_inviato(conn, NOME, chiave(oggi or date.today()))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Rapporto SEO/GEO delle pagine pubbliche per Matteo.")
    parser.add_argument("--stampa", action="store_true", help="solo a schermo, senza email e senza registrare l'invio")
    parser.add_argument("--forza", action="store_true", help="invia anche se e' gia' stato inviato")
    args = parser.parse_args(argv)
    print(invia_rapporto(solo_stampa=args.stampa, forza=args.forza))
    return 0


if __name__ == "__main__":
    sys.exit(main())
