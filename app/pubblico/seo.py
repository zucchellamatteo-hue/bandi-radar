"""SEO tecnica e GEO della parte pubblica (07/10/2026): indirizzo del sito, robots.txt, sitemap.xml, /llms.txt e dati
strutturati JSON-LD (schema.org).

Il dominio viene da SITO_URL (bandinqiaro.it dal 07/10; prima finanzagevolata.qiaro.it): URL canonici, sitemap e
llms.txt lo seguono da soli, cosi' cambiare dominio e' cambiare una variabile.

Regole di indicizzazione:
- finche' la pagina pubblica e' spenta (PAGINA_PUBBLICA=0) robots.txt chiude tutto;
- con il solo blog aperto (BLOG_PUBBLICO=1 e PAGINA_PUBBLICA=0, 08/10) si aprono solo /blog, /llms.txt, la sitemap e
  i file che servono alle pagine del blog (favicon, immagini): landing, plancia e tutto il resto restano chiusi;
- da accesa si aprono SOLO le pagine pubbliche elencate in PAGINE_PUBBLICHE (elenco bianco): plancia, area impresa,
  registrazione e API restano chiuse anche se domani nascono pagine nuove nella plancia. La plancia ha comunque
  "noindex" nella sua pagina (plancia/index.html);
- i programmi dei motori di risposta IA (ChatGPT, Claude, Perplexity, Gemini...) sono nominati uno per uno con le
  stesse regole: devono poter leggere le pagine pubbliche per citarci.
"""

from __future__ import annotations

import json
import os
import re
from datetime import date
from xml.sax.saxutils import escape

NOME = "bandinQiaro"

# Pagine pubbliche indicizzabili: (percorso, frequenza di cambio per la sitemap, priorita').
PAGINE_PUBBLICHE = [("/", "daily", "1.0"), ("/condizioni-supporto", "monthly", "0.4"), ("/termini", "yearly", "0.2"),
                    ("/privacy", "yearly", "0.2"), ("/cookie", "yearly", "0.1"), ("/note-legali", "yearly", "0.1")]
# File per i programmi (non vanno nella sitemap ma devono essere leggibili).
FILE_PUBBLICI = ["/llms.txt", "/sitemap.xml", "/favicon.svg", "/immagini/"]
# Sezioni pubbliche con pagine figlie (07/10): il blog. Nella sitemap vanno solo gli articoli pubblicati
# (app/pubblico/blog.voci_sitemap); bozze e articoli archiviati rispondono 404/410 e non vi compaiono mai.
# Dal 09/10 anche /bandi-aperti (pagine per regione, app/pubblico/regioni.py), aperte con il blog.
SEZIONI_PUBBLICHE = ["/blog", "/bandi-aperti"]

# Programmi dei motori di ricerca e di risposta IA a cui diciamo esplicitamente di si' (stesse regole di tutti).
# OAI-SearchBot / ChatGPT-User: ricerca di ChatGPT; GPTBot: addestramento OpenAI; ClaudeBot, Claude-SearchBot,
# Claude-User: Anthropic; PerplexityBot / Perplexity-User; Google-Extended: Gemini; Applebot-Extended: Apple.
PROGRAMMI_IA = ["OAI-SearchBot", "ChatGPT-User", "GPTBot", "ClaudeBot", "Claude-SearchBot", "Claude-User",
                "PerplexityBot", "Perplexity-User", "Google-Extended", "Applebot-Extended", "Bingbot", "Googlebot"]


def sito_url() -> str:
    return (os.environ.get("SITO_URL") or "https://finanzagevolata.qiaro.it").rstrip("/")


def assoluto(percorso: str) -> str:
    return sito_url() + (percorso if percorso.startswith("/") else "/" + percorso)


def robots_txt(pubblica: bool, blog: bool = False) -> str:
    """`pubblica`: tutta la parte pubblica aperta; `blog`: aperto solo il blog (con i file che gli servono)."""
    if not pubblica and not blog:
        return ("# bandinQiaro: sito non ancora aperto ai motori di ricerca (PAGINA_PUBBLICA=0).\n"
                "User-agent: *\nDisallow: /\n")
    if pubblica:
        righe = ["# bandinQiaro: si leggono solo le pagine pubbliche; plancia, area riservata e API restano chiuse."]
    else:
        righe = ["# bandinQiaro: per ora e' aperto solo il blog (BLOG_PUBBLICO=1); il resto del sito e' chiuso."]
    righe += ["# I motori di risposta IA sono benvenuti con le stesse regole.", "User-agent: *"]
    righe += [f"User-agent: {p}" for p in PROGRAMMI_IA]
    if pubblica:
        righe += ["Allow: /$", "Allow: /?"]                 # la home, anche con i parametri degli annunci
        righe += [f"Allow: {p}$" for p, _, _ in PAGINE_PUBBLICHE if p != "/"]
    righe += [f"Allow: {p}" for p in FILE_PUBBLICI + SEZIONI_PUBBLICHE]
    from app.pubblico import indexnow

    if indexnow.chiave():                                   # il file della chiave IndexNow (09/10) va letto da Bing
        righe.append(f"Allow: /{indexnow.chiave()}.txt$")
    righe += ["Disallow: /", "", f"Sitemap: {assoluto('/sitemap.xml')}", ""]
    return "\n".join(righe)


def meta_verifica() -> str:
    """Meta tag di verifica della proprieta' per Google Search Console e Bing Webmaster Tools, solo se i codici sono
    nel .env (GOOGLE_SITE_VERIFICATION, BING_SITE_VERIFICATION). Del codice si tengono solo lettere, cifre, - e _."""
    tag = []
    for variabile, nome in (("GOOGLE_SITE_VERIFICATION", "google-site-verification"),
                            ("BING_SITE_VERIFICATION", "msvalidate.01")):
        codice = "".join(c for c in os.environ.get(variabile, "").strip() if c.isalnum() or c in "-_")
        if codice:
            tag.append(f'<meta name="{nome}" content="{codice}">')
    return "".join(tag)


def sitemap_xml(ultimo_aggiornamento: date | None = None, articoli: list[tuple[str, str]] | None = None,
                solo_blog: bool = False) -> str:
    """`articoli`: (percorso, data dell'ultima modifica) delle pagine del blog pubblicate (app/pubblico/blog.py).
    `solo_blog` (blog aperto, landing chiusa): nella mappa vanno solo /blog e gli articoli."""
    oggi = (ultimo_aggiornamento or date.today()).isoformat()
    voci = []
    if solo_blog and not any(p == "/blog" for p, _ in articoli or []):
        articoli = [("/blog", oggi)] + list(articoli or [])
    for percorso, freq, prio in ([] if solo_blog else PAGINE_PUBBLICHE):
        lastmod = f"<lastmod>{oggi}</lastmod>" if percorso == "/" else ""
        voci.append(f"<url><loc>{escape(assoluto(percorso))}</loc>{lastmod}<changefreq>{freq}</changefreq>"
                    f"<priority>{prio}</priority></url>")
    for percorso, modificato in articoli or []:
        if percorso.startswith("/bandi-aperti"):        # pagine per regione: cambiano ogni giorno
            freq, prio = "daily", "0.6"
        else:
            freq, prio = ("weekly", "0.6") if percorso == "/blog" else ("monthly", "0.7")
        voci.append(f"<url><loc>{escape(assoluto(percorso))}</loc><lastmod>{escape(modificato)}</lastmod>"
                    f"<changefreq>{freq}</changefreq><priority>{prio}</priority></url>")
    return ('<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
            + "\n".join(voci) + "\n</urlset>\n")


# --- titoli e descrizioni per Google (09/10/2026, valutazione SEO/GEO) ---

TITOLO_MAX = 60             # Google mostra circa 60 caratteri del <title>
HEADLINE_MAX = 110          # limite di Google per "headline" nei dati strutturati Article
DESCRIZIONE_MIN, DESCRIZIONE_MAX = 140, 160
MARCHIO = " | " + NOME
# Parole che non possono chiudere un titolo accorciato ("... si risparmia su" -> "... si risparmia").
_PAROLE_DEBOLI = {"a", "ad", "al", "allo", "alla", "ai", "agli", "alle", "con", "da", "dal", "dalla", "dai", "dalle",
                  "di", "del", "dello", "della", "dei", "degli", "delle", "e", "ed", "o", "od", "in", "nel", "nella",
                  "nei", "nelle", "per", "su", "sul", "sulla", "sui", "sulle", "tra", "fra", "il", "lo", "la", "i",
                  "gli", "le", "un", "uno", "una", "che", "come", "ma", "se", "non", "anche", "più", "-", "–", "—"}
_PUNTEGGIATURA = " ,;:.–—-|/(…"


def _pulisci_coda(testo: str) -> str:
    """Toglie punteggiatura e parole deboli in fondo (articoli, preposizioni, congiunzioni)."""
    parole = testo.rstrip(_PUNTEGGIATURA).split()
    while len(parole) > 1 and parole[-1].lower().strip(_PUNTEGGIATURA) in _PAROLE_DEBOLI | {""}:
        parole.pop()
    return " ".join(parole).rstrip(_PUNTEGGIATURA)


def titolo_breve(testo: str, massimo: int) -> str:
    """Accorcia un titolo entro `massimo` caratteri senza tagliare le parole: via le parentesi, poi si taglia a una
    pausa naturale (due punti, virgola, trattino) se resta abbastanza testo, altrimenti all'ultima parola intera, e
    si tolgono le parole che non possono chiudere una frase. Niente puntini: il titolo deve sembrare intero."""
    t = " ".join((testo or "").split())
    if len(t) <= massimo:
        return t
    senza = " ".join(re.sub(r"\s*\([^)]*\)", "", t).split())
    if len(senza) <= massimo:
        return _pulisci_coda(senza)
    pezzo = senza[:massimo + 1]
    taglio = pezzo.rsplit(" ", 1)[0] if " " in pezzo else senza[:massimo]
    pause = [m.start() for m in re.finditer(r"[,;:–—]|\s-\s", taglio)]
    if pause and pause[-1] >= massimo * 0.5:            # una pausa naturale abbastanza in fondo
        taglio = taglio[:pause[-1]]
    risultato = _pulisci_coda(taglio)
    return risultato or senza[:massimo]


def titolo_pagina(titolo: str, titolo_seo: str | None = None, massimo: int = TITOLO_MAX) -> str:
    """Il <title> di un articolo, entro `massimo` caratteri: il titolo per Google se c'e' (scritto a mano), altrimenti
    il titolo accorciato alla parola; col marchio " | bandinQiaro" in fondo solo se ci sta."""
    base = " ".join((titolo_seo or "").split())
    if not base:
        intero = " ".join((titolo or "").split())
        base = intero if len(intero) + len(MARCHIO) <= massimo else titolo_breve(intero, massimo - len(MARCHIO))
        if len(base) < 25:                              # troppo corto col marchio: meglio piu' titolo e niente marchio
            base = titolo_breve(intero, massimo)
    if NOME.lower() not in base.lower() and len(base) + len(MARCHIO) <= massimo:
        return base + MARCHIO
    return base if len(base) <= massimo else titolo_breve(base, massimo)


def headline(titolo: str, titolo_seo: str | None = None) -> str:
    """"headline" dei dati strutturati: il titolo intero se sta in 110 caratteri, altrimenti il titolo per Google,
    altrimenti il titolo accorciato alla parola (mai tagliato a meta' parola)."""
    intero = " ".join((titolo or "").split())
    if len(intero) <= HEADLINE_MAX:
        return intero
    breve = " ".join((titolo_seo or "").split())
    return breve if breve and len(breve) <= HEADLINE_MAX else titolo_breve(intero, HEADLINE_MAX)


def descrizione_meta(testo: str, coda: str = "", minimo: int = DESCRIZIONE_MIN, massimo: int = DESCRIZIONE_MAX) -> str:
    """Meta description tra `minimo` e `massimo` caratteri. Troppo lunga: si tiene la frase intera piu' lunga che ci
    sta, o si taglia all'ultima parola con "…". Troppo corta: si aggiunge `coda` (es. la data di aggiornamento) se ci sta."""
    t = " ".join((testo or "").split())
    if len(t) > massimo:
        frasi = [m.end() for m in re.finditer(r"[.!?](?=\s|$)", t[:massimo + 1]) if m.end() <= massimo]
        if frasi and frasi[-1] >= minimo:
            t = t[:frasi[-1]]
        else:
            t = _pulisci_coda(t[:massimo].rsplit(" ", 1)[0]) + "…"
    if len(t) < minimo and coda:
        unione = t + ("" if t.endswith((".", "!", "?")) else ".") + " " + coda.strip()
        if len(unione) <= massimo:
            t = unione
    return t


def autore(nome: str | None) -> dict:
    """L'autore per i dati strutturati. Una redazione (o il segnaposto ancora da riempire) e' una Organization:
    "Redazione bandinQiaro – contenuti verificati da..." diventa "Redazione bandinQiaro" (la parte prima del trattino),
    legata all'organizzazione del sito. Un nome di persona ("Mario Rossi, commercialista") resta una Person."""
    testo = " ".join((nome or "").split())
    principale = re.split(r"\s+[–—-]\s+|,", testo, maxsplit=1)[0].strip() if testo else ""
    if not principale or "[" in principale or principale.lower().startswith(("redazione", NOME.lower())):
        nome_org = principale if principale.lower().startswith("redazione") else f"Redazione {NOME}"
        return {"@type": "Organization", "name": nome_org, "url": assoluto("/blog"),
                "parentOrganization": {"@id": assoluto("/#organizzazione")}}
    persona = {"@type": "Person", "name": principale}
    if principale != testo:
        persona["description"] = testo
    return persona


def json_ld(oggetti: list[dict]) -> str:
    """Un blocco <script type="application/ld+json"> con un @graph; '</' e' protetto per non chiudere lo script."""
    dati = {"@context": "https://schema.org", "@graph": oggetti}
    testo = json.dumps(dati, ensure_ascii=False, separators=(",", ":")).replace("</", "<\\/")
    return f'<script type="application/ld+json">{testo}</script>'


def organizzazione(descrizione: str) -> dict:
    org = {"@type": "Organization", "@id": assoluto("/#organizzazione"), "name": NOME, "url": assoluto("/"),
           "logo": assoluto("/immagini/logo.png"), "description": descrizione, "areaServed": {"@type": "Country", "name": "Italia"},
           "knowsAbout": ["finanza agevolata", "bandi per imprese", "contributi a fondo perduto", "finanziamenti agevolati",
                          "crediti d'imposta", "fondi europei", "bandi regionali", "bandi delle Camere di commercio"]}
    if os.environ.get("EMAIL_CONTATTO"):
        org["email"] = os.environ["EMAIL_CONTATTO"]
    profili = [u.strip() for u in os.environ.get("PROFILI_SOCIAL", "").split(",") if u.strip().startswith("https://")]
    if profili:                                    # LinkedIn, Google Business Profile...: aiutano a riconoscerci
        org["sameAs"] = profili
    return org


def sito_web() -> dict:
    return {"@type": "WebSite", "@id": assoluto("/#sito"), "url": assoluto("/"), "name": NOME, "inLanguage": "it-IT",
            "publisher": {"@id": assoluto("/#organizzazione")}}


def servizio(descrizione: str, prezzo_mese: float, giorni_prova: int) -> dict:
    return {"@type": "Service", "@id": assoluto("/#servizio"), "name": "Monitoraggio dei bandi per imprese",
            "serviceType": "Monitoraggio di bandi e agevolazioni per imprese (finanza agevolata)",
            "provider": {"@id": assoluto("/#organizzazione")}, "areaServed": {"@type": "Country", "name": "Italia"},
            "audience": {"@type": "BusinessAudience", "audienceType": "Imprese, PMI, professionisti e startup italiane"},
            "description": descrizione,
            "offers": {"@type": "Offer", "name": "Abbonamento - prezzo di lancio", "price": f"{prezzo_mese:.2f}",
                       "priceCurrency": "EUR", "url": assoluto("/registrati"), "availability": "https://schema.org/InStock",
                       "eligibleCustomerType": "https://schema.org/Business",
                       "description": f"Prova gratuita di {giorni_prova} giorni senza carta. Prezzo IVA esclusa.",
                       "priceSpecification": {"@type": "UnitPriceSpecification", "price": f"{prezzo_mese:.2f}",
                                              "priceCurrency": "EUR", "unitCode": "MON", "referenceQuantity":
                                              {"@type": "QuantitativeValue", "value": 1, "unitCode": "MON"},
                                              "valueAddedTaxIncluded": False}}}


def domande_frequenti(faq: list[tuple[str, str]], percorso: str = "/") -> dict:
    return {"@type": "FAQPage", "@id": assoluto(percorso + "#domande"),
            "mainEntity": [{"@type": "Question", "name": d, "acceptedAnswer": {"@type": "Answer", "text": r}} for d, r in faq]}
