"""Glossario negli articoli del blog (10/10/2026, prova degli articoli con tre imprese: "sigle mai spiegate").

Alla prima comparsa nel testo di una parola del GLOSSARIO la parola diventa un link tratteggiato verso la sua
spiegazione in fondo all'articolo ("Parole difficili"); sul computer la spiegazione compare anche passando sopra con il
mouse o con la tastiera (attributo data-spiega, solo CSS). Titoli, link, tabelle e calcolatori non si toccano.
"""

from __future__ import annotations

import html
import re

# parola (come compare nel testo) -> spiegazione semplice. L'ordine conta: prima le espressioni piu' lunghe.
GLOSSARIO: dict[str, str] = {
    "de minimis": "Aiuti di piccolo importo che l'Unione europea permette senza notifica: ogni impresa può riceverne al "
                  "massimo 300.000 euro in tre anni, sommando tutti gli aiuti de minimis.",
    "in conto impianti": "Contributo dato per comprare beni che durano più anni (macchinari, impianti): non si tassa tutto "
                         "subito, ma un po' ogni anno insieme all'ammortamento del bene.",
    "risconto passivo": "Scrittura di bilancio che rinvia agli anni successivi una parte di un ricavo già incassato, "
                        "per farlo pesare un po' ogni anno.",
    "perizia asseverata": "Relazione tecnica firmata da un ingegnere o perito iscritto all'albo, che ne risponde anche "
                          "penalmente: attesta che il bene ha i requisiti richiesti.",
    "Manuale di Frascati": "Manuale dell'OCSE che definisce che cosa è ricerca e sviluppo: serve a capire se un progetto "
                           "dà diritto al credito d'imposta.",
    "GBER": "Regolamento europeo (UE 651/2014) che permette agli Stati di dare certi aiuti alle imprese senza chiedere "
            "ogni volta l'autorizzazione a Bruxelles, entro percentuali massime.",
    "DURC": "Documento unico di regolarità contributiva: dice se l'impresa è in regola con i contributi INPS e INAIL.",
    "ESL": "Equivalente sovvenzione lordo: il valore in euro dell'aiuto ricevuto, quello che conta per i limiti europei.",
    "SCOP": "Efficienza stagionale di una pompa di calore: quante unità di calore produce per ogni unità di elettricità "
            "consumata, in media nella stagione. Più è alto, meglio è.",
    "APE": "Attestato di prestazione energetica: il documento firmato da un tecnico che dice quanta energia consuma "
           "l'edificio e la sua classe energetica.",
    "ATECO": "Codice dell'attività economica dell'impresa, scritto nella visura camerale.",
    "IRAP": "Imposta regionale sulle attività produttive: la pagano le società e gli enti, non le imprese individuali.",
}

_SALTA = {"a", "h1", "h2", "h3", "h4", "script", "style", "table", "summary", "label", "button", "select", "option",
          "details", "code"}
_TAG = re.compile(r"(<[^>]+>)")


def _ancora(parola: str) -> str:
    return "g-" + re.sub(r"[^a-z0-9]+", "-", parola.lower()).strip("-")


def applica(testo_html: str) -> tuple[str, list[str]]:
    """(html con le parole del glossario evidenziate alla prima comparsa, parole usate in ordine)."""
    pezzi = _TAG.split(testo_html)
    aperti: list[str] = []
    usate: list[str] = []
    for i, pezzo in enumerate(pezzi):
        if pezzo.startswith("<"):
            m = re.match(r"<\s*(/)?\s*([a-zA-Z0-9]+)", pezzo)
            if m:
                nome = m.group(2).lower()
                if nome in _SALTA:
                    if m.group(1):
                        if nome in aperti:
                            aperti.remove(nome)
                    elif not pezzo.endswith("/>"):
                        aperti.append(nome)
            continue
        if aperti or not pezzo.strip():
            continue
        segnaposti = []          # i link si inseriscono alla fine: le spiegazioni non devono essere ricercate
        for parola, spiegazione in GLOSSARIO.items():
            if parola in usate:
                continue
            m = re.search(r"(?<![\w-])" + re.escape(parola) + r"(?![\w-])", pezzo)
            if not m:
                continue
            segnaposti.append(f'<a class="glossa" href="#{_ancora(parola)}" data-spiega="{html.escape(spiegazione)}">'
                              f'{m.group(0)}</a>')
            pezzo = pezzo[:m.start()] + f"\x00{len(segnaposti) - 1}\x00" + pezzo[m.end():]
            usate.append(parola)
        pezzi[i] = re.sub(r"\x00(\d+)\x00", lambda x: segnaposti[int(x.group(1))], pezzo)
    return "".join(pezzi), usate


def sezione(usate: list[str]) -> str:
    """La sezione "Parole difficili" in fondo all'articolo, solo con le parole comparse."""
    if not usate:
        return ""
    voci = "".join(f'<dt id="{_ancora(p)}">{html.escape(p)}</dt><dd>{html.escape(GLOSSARIO[p])}</dd>' for p in usate)
    return f'<h2 id="parole-difficili">Parole difficili</h2><dl class="glossario">{voci}</dl>'


STILE = """.glossa{color:inherit;text-decoration:underline dotted;text-underline-offset:3px;position:relative}
.glossa:hover::after,.glossa:focus::after{content:attr(data-spiega);position:absolute;left:0;top:1.6em;z-index:3;width:min(22rem,80vw);
background:#163e7a;color:#fff;padding:.6rem .75rem;border-radius:8px;font-size:.88rem;line-height:1.4;font-weight:400}
dl.glossario dt{font-weight:700;color:var(--blu);margin-top:.6rem}dl.glossario dd{margin:.1rem 0 0}"""
