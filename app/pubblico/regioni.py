"""Pagine "Bandi aperti in <regione>" (09/10/2026, PIANO_SEO_GEO punto 7).

/bandi-aperti elenca le regioni con il numero di bandi aperti; /bandi-aperti/<regione> (es. /bandi-aperti/lombardia)
elenca i bandi aperti o in arrivo di quella regione, presi SOLO dai proponibili (vista bandi_situazione, regola in
CLAUDE.md): titolo, ente, agevolazione in una riga, scadenza e una riga di sintesi. La scheda completa resta nell'area
riservata: ogni voce porta alla registrazione. In fondo il numero dei bandi nazionali ed europei validi anche li'.

Le pagine si rifanno da sole: i dati restano in memoria CACHE_SECONDI. Si indicizzano solo con il blog aperto ai
motori (BLOG_PUBBLICO=1 o PAGINA_PUBBLICA=1) e con almeno MINIMO_INDICIZZA bandi: una pagina con 2 bandi sarebbe
"contenuto scarso" per Google. Le regioni sotto la soglia restano visibili ma con noindex e fuori dalla sitemap.
"""

from __future__ import annotations

import re
import time
import unicodedata
from datetime import date

from app.pubblico import seo

MINIMO_INDICIZZA = 8
CACHE_SECONDI = 900
SCADENZA_VICINA = 30            # giorni: "in scadenza" in cima alla pagina
MESI = ["gennaio", "febbraio", "marzo", "aprile", "maggio", "giugno", "luglio", "agosto", "settembre", "ottobre",
        "novembre", "dicembre"]
_cache: dict = {}

STILE_REGIONI = """<style>
.bandi-regione{list-style:none;padding:0;display:grid;gap:.9rem}
.bandi-regione li{background:#fff;border:1px solid var(--bordo);border-radius:12px;padding:.9rem 1.1rem}
.bandi-regione h3{font-size:1.02rem;line-height:1.35;margin:.15rem 0 .35rem}
.bandi-regione .ente{color:var(--grigio);font-size:.86rem}.bandi-regione .riga{margin:.2rem 0;color:var(--blu);font-weight:600}
.bandi-regione .quando{color:#b0392f;font-weight:600;font-size:.9rem}.bandi-regione .quando.calmo{color:var(--grigio);font-weight:500}
.bandi-regione p.sintesi{margin:.35rem 0 .4rem;font-size:.93rem;color:#2d3846}
.briciole{font-size:.9rem;color:var(--grigio);margin:0 0 .4rem}.briciole a{color:var(--grigio)}
ul.regioni a{text-decoration:none;display:flex;justify-content:space-between;width:100%}
</style>"""


def slug(nome: str) -> str:
    """"Friuli Venezia Giulia" -> "friuli-venezia-giulia"; "Valle d'Aosta" -> "valle-d-aosta"."""
    testo = unicodedata.normalize("NFKD", nome).encode("ascii", "ignore").decode().lower()
    return re.sub(r"[^a-z0-9]+", "-", testo).strip("-")


def regioni() -> dict[str, tuple[str, str]]:
    """slug -> (codice, nome) per le 19 regioni e le 2 province autonome (app/abbinamento/territorio.NOMI_REGIONI)."""
    from app.abbinamento.territorio import NOMI_REGIONI

    return {slug(nome): (codice, nome) for codice, nome in NOMI_REGIONI.items()}


def _dove(nome: str) -> str:
    """"in Lombardia", "nella Provincia di Trento"."""
    return f"nella {nome}" if nome.startswith("Provincia") else f"in {nome}"


def _calcola(conn) -> dict:
    """Bandi aperti per regione (solo proponibili, aperti o in arrivo, non scaduti) e quanti valgono in tutta Italia."""
    from app.pubblico.vetrina import _COLONNE, _VALIDO

    with conn.cursor() as cur:
        cur.execute(f"""SELECT {_COLONNE}, b.sintesi FROM bandi b JOIN bandi_situazione s USING (id)
                        WHERE {_VALIDO} ORDER BY b.scadenza NULLS LAST, b.id""")
        bandi = [dict(r) for r in cur.fetchall()]
    per_regione: dict[str, list[dict]] = {}
    nazionali = 0
    for b in bandi:
        if b.get("territorio") == "nessun_vincolo":
            nazionali += 1
            continue
        for codice in b.get("territorio_regioni") or []:
            per_regione.setdefault(codice, []).append(b)
    return {"per_regione": per_regione, "nazionali": nazionali, "aggiornato": date.today()}


def dati(conn) -> dict:
    """I dati di tutte le pagine, in memoria CACHE_SECONDI (una sola query per tutte le regioni)."""
    adesso = time.monotonic()
    if _cache.get("scade", 0) > adesso and _cache.get("giorno") == date.today():
        return _cache["dati"]
    d = _calcola(conn)
    _cache.update(dati=d, scade=adesso + CACHE_SECONDI, giorno=date.today())
    return d


def indicizzabile(numero: int) -> bool:
    from app.pubblico import blog_pubblico

    return blog_pubblico() and numero >= MINIMO_INDICIZZA


def _sintesi(testo: str | None, massimo: int = 200) -> str:
    t = " ".join((testo or "").split())
    if len(t) <= massimo:
        return t
    return t[:massimo].rsplit(" ", 1)[0].rstrip(" ,;:.") + "…"


def _voce(b: dict, oggi: date) -> str:
    from app.pubblico import _e
    from app.pubblico.vetrina import _quando_bando, riga_bando

    quando = _quando_bando(b, oggi)
    vicina = b.get("scadenza") and (b["scadenza"] - oggi).days <= SCADENZA_VICINA
    sintesi = _sintesi(b.get("sintesi"))
    return (f'<li><div class="ente">{_e(b.get("ente"))}</div><h3>{_e(b["titolo"])}</h3>'
            f'<div class="riga">{_e(riga_bando(b))}</div>'
            f'<div class="quando{"" if vicina else " calmo"}">{_e(quando)}</div>'
            + (f'<p class="sintesi">{_e(sintesi)}</p>' if sintesi else "")
            + '<a href="/registrati">Scopri se fa per la tua impresa →</a></li>')


def _mese(oggi: date) -> str:
    return f"{MESI[oggi.month - 1]} {oggi.year}"


def pagina_regione(conn, slug_regione: str) -> str | None:
    """La pagina di una regione, o None se lo slug non e' una regione."""
    from app.abbonamenti import giorni_prova
    from app.pubblico import _e, blog_pubblico, pagina, pubblica

    voce = regioni().get(slug_regione)
    if not voce:
        return None
    codice, nome = voce
    d = dati(conn)
    oggi = d["aggiornato"]
    bandi = d["per_regione"].get(codice, [])
    vicini = [b for b in bandi if b.get("scadenza") and (b["scadenza"] - oggi).days <= SCADENZA_VICINA]
    altri = [b for b in bandi if b not in vicini]
    percorso = f"/bandi-aperti/{slug_regione}"
    dove = _dove(nome)
    n = len(bandi)
    titolo_h1 = f"Bandi aperti {dove} per le imprese"
    sezioni = ""
    if vicini:
        sezioni += (f"<h2>In scadenza entro {SCADENZA_VICINA} giorni ({len(vicini)})</h2>"
                    f'<ul class="bandi-regione">{"".join(_voce(b, oggi) for b in vicini)}</ul>')
    if altri:
        sezioni += (f'<h2 class="titoletto">{"Altri bandi aperti o in arrivo" if vicini else "Bandi aperti o in arrivo"} ({len(altri)})</h2>'
                    f'<ul class="bandi-regione">{"".join(_voce(b, oggi) for b in altri)}</ul>')
    if not bandi:
        sezioni = f"<p>Oggi non ci sono bandi regionali o locali aperti {dove} nel nostro archivio.</p>"
    avviso = "" if blog_pubblico() else ('<p class="bozza">Anteprima: pagina non ancora pubblica né indicizzata '
                                          '(BLOG_PUBBLICO=0).</p>')
    nazionali = d["nazionali"]
    corpo = f"""<section class="eroe"><div class="contenitore stretto">{avviso}
<p class="briciole"><a href="/bandi-aperti">Bandi aperti per regione</a> › {_e(nome)}</p>
<h1>{_e(titolo_h1)}</h1>
<p class="sottotitolo">Al {oggi:%d/%m/%Y} ci sono <b>{n} bandi aperti o in arrivo</b> riservati alle imprese {_e(dove)}
(Regione, Camere di commercio, Comuni e altri enti del territorio), più <b>{nazionali} bandi nazionali ed europei</b>
validi in tutta Italia. Elenco aggiornato ogni giorno, solo bandi con la scheda controllata sul testo ufficiale.</p>
<p class="azioni"><a class="bottone grande" href="/registrati">Scopri quali fanno per la tua impresa</a></p></div></section>
<section><div class="contenitore stretto">{sezioni}
<div class="invito carta" style="margin-top:2rem"><h2>Non perdere i prossimi bandi {_e(dove)}</h2>
<p>bandinQiaro controlla ogni giorno i siti di Regioni, Camere di commercio, Comuni, ministeri e Unione europea e ti
segnala solo i bandi adatti alla tua impresa, con una scheda chiara: requisiti, spese ammesse, importi e scadenze.
Prova gratis per {giorni_prova()} giorni, senza carta.</p>
<p><a class="bottone" href="/registrati">Registrati e prova gratis</a></p></div>
<p class="piccolo">Elenco informativo. Prima di presentare la domanda leggi sempre il bando ufficiale: requisiti, importi e
scadenze possono cambiare. <a href="/bandi-aperti">Bandi aperti nelle altre regioni</a> · <a href="/blog">Guide alle
agevolazioni nazionali</a></p></div></section>"""
    url = seo.assoluto(percorso)
    titolo = seo.titolo_pagina(f"Bandi aperti {dove} per imprese ({_mese(oggi)})")
    descrizione = seo.descrizione_meta(
        f"{n} bandi aperti per le imprese {dove} al {oggi:%d/%m/%Y}: contributi a fondo perduto, voucher, "
        "finanziamenti agevolati e garanzie di Regione, Camere di commercio e Comuni, con le scadenze.")
    passi = ([("bandinQiaro", seo.assoluto("/"))] if pubblica() else []) + [
        ("Bandi aperti per regione", seo.assoluto("/bandi-aperti")), (nome, url)]
    elenco = {"@type": "ItemList", "name": titolo_h1, "numberOfItems": n, "itemListElement": [
        {"@type": "ListItem", "position": i, "name": b["titolo"][:200]} for i, b in enumerate(bandi[:50], 1)]}
    grafo = [{"@type": "CollectionPage", "@id": url + "#pagina", "url": url, "name": titolo_h1, "inLanguage": "it-IT",
              "description": descrizione, "dateModified": oggi.isoformat(), "about": {"@type": "Place", "name": nome},
              "isPartOf": {"@id": seo.assoluto("/#sito")}, "mainEntity": elenco},
             {"@type": "BreadcrumbList", "itemListElement": [
                 {"@type": "ListItem", "position": i, "name": x, "item": u} for i, (x, u) in enumerate(passi, 1)]}]
    return pagina(titolo, corpo, descrizione, indicizza=indicizzabile(n), percorso=percorso,
                  testa=STILE_REGIONI + seo.json_ld(grafo))


def pagina_elenco(conn) -> str:
    """/bandi-aperti: le regioni con il numero di bandi aperti, ognuna col link alla sua pagina."""
    from app.pubblico import _e, blog_pubblico, pagina

    d = dati(conn)
    oggi = d["aggiornato"]
    voci = []
    totale = 0
    for s, (codice, nome) in sorted(regioni().items(), key=lambda x: x[1][1]):
        n = len(d["per_regione"].get(codice, []))
        totale += n
        voci.append(f'<li><a href="/bandi-aperti/{s}"><span>{_e(nome)}</span><b>{n}</b></a></li>')
    avviso = "" if blog_pubblico() else ('<p class="bozza">Anteprima: pagina non ancora pubblica né indicizzata '
                                          '(BLOG_PUBBLICO=0).</p>')
    corpo = f"""<section class="eroe"><div class="contenitore">{avviso}
<h1>Bandi aperti per le imprese, regione per regione</h1>
<p class="sottotitolo">Al {oggi:%d/%m/%Y}: bandi regionali e locali aperti o in arrivo in ogni regione, più
<b>{d['nazionali']} bandi nazionali ed europei</b> validi in tutta Italia. Un bando può valere per più regioni.
Solo bandi con la scheda controllata sul testo ufficiale, aggiornati ogni giorno.</p></div></section>
<section class="grigia"><div class="contenitore"><ul class="regioni">{"".join(voci)}</ul>
<p><a class="bottone" href="/registrati">Scopri quali fanno per la tua impresa</a></p></div></section>"""
    url = seo.assoluto("/bandi-aperti")
    grafo = [{"@type": "CollectionPage", "@id": url + "#pagina", "url": url, "inLanguage": "it-IT",
              "name": "Bandi aperti per le imprese, regione per regione", "dateModified": oggi.isoformat(),
              "isPartOf": {"@id": seo.assoluto("/#sito")}}]
    return pagina(seo.titolo_pagina(f"Bandi aperti per regione ({_mese(oggi)})"), corpo,
                  seo.descrizione_meta("Bandi aperti per le imprese in ogni regione italiana: contributi a fondo perduto, "
                                       "voucher e finanziamenti di Regioni, Camere di commercio e Comuni, aggiornati ogni giorno."),
                  indicizza=blog_pubblico() and totale > 0, percorso="/bandi-aperti",
                  testa=STILE_REGIONI + seo.json_ld(grafo))


def voci_sitemap(conn) -> list[tuple[str, str]]:
    """(percorso, data) dell'elenco e delle regioni con almeno MINIMO_INDICIZZA bandi (le altre hanno noindex)."""
    d = dati(conn)
    oggi = d["aggiornato"].isoformat()
    regioni_ok = [(f"/bandi-aperti/{s}", oggi) for s, (codice, _) in sorted(regioni().items())
                  if len(d["per_regione"].get(codice, [])) >= MINIMO_INDICIZZA]
    return [("/bandi-aperti", oggi)] + regioni_ok if regioni_ok else []


def righe_llms(conn) -> list[str]:
    """Sezione di /llms.txt con le pagine regionali indicizzabili."""
    d = dati(conn)
    righe = []
    for s, (codice, nome) in sorted(regioni().items(), key=lambda x: x[1][1]):
        n = len(d["per_regione"].get(codice, []))
        if n >= MINIMO_INDICIZZA:
            righe.append(f"- [Bandi aperti {_dove(nome)}]({seo.assoluto('/bandi-aperti/' + s)}): {n} bandi regionali "
                         f"e locali aperti o in arrivo al {d['aggiornato']:%d/%m/%Y}")
    if not righe:
        return []
    return ["## Bandi aperti per regione", "", f"- [Tutte le regioni]({seo.assoluto('/bandi-aperti')})"] + righe + [""]
