"""SEO tecnica e GEO della parte pubblica (07/10/2026): indirizzo del sito, robots.txt, sitemap.xml, /llms.txt e dati
strutturati JSON-LD (schema.org).

Il dominio viene da SITO_URL (oggi finanzagevolata.qiaro.it, in arrivo bandinqiaro.it): URL canonici, sitemap e
llms.txt lo seguono da soli, cosi' cambiare dominio e' cambiare una variabile.

Regole di indicizzazione:
- finche' la pagina pubblica e' spenta (PAGINA_PUBBLICA=0) robots.txt chiude tutto;
- da accesa si aprono SOLO le pagine pubbliche elencate in PAGINE_PUBBLICHE (elenco bianco): plancia, area impresa,
  registrazione e API restano chiuse anche se domani nascono pagine nuove nella plancia. La plancia ha comunque
  "noindex" nella sua pagina (plancia/index.html);
- i programmi dei motori di risposta IA (ChatGPT, Claude, Perplexity, Gemini...) sono nominati uno per uno con le
  stesse regole: devono poter leggere le pagine pubbliche per citarci.
"""

from __future__ import annotations

import json
import os
from datetime import date
from xml.sax.saxutils import escape

NOME = "Bandi Radar"

# Pagine pubbliche indicizzabili: (percorso, frequenza di cambio per la sitemap, priorita').
PAGINE_PUBBLICHE = [("/", "daily", "1.0"), ("/condizioni-supporto", "monthly", "0.4"), ("/termini", "yearly", "0.2"),
                    ("/privacy", "yearly", "0.2"), ("/cookie", "yearly", "0.1"), ("/note-legali", "yearly", "0.1")]
# File per i programmi (non vanno nella sitemap ma devono essere leggibili).
FILE_PUBBLICI = ["/llms.txt", "/sitemap.xml", "/favicon.svg", "/immagini/"]

# Programmi dei motori di ricerca e di risposta IA a cui diciamo esplicitamente di si' (stesse regole di tutti).
# OAI-SearchBot / ChatGPT-User: ricerca di ChatGPT; GPTBot: addestramento OpenAI; ClaudeBot, Claude-SearchBot,
# Claude-User: Anthropic; PerplexityBot / Perplexity-User; Google-Extended: Gemini; Applebot-Extended: Apple.
PROGRAMMI_IA = ["OAI-SearchBot", "ChatGPT-User", "GPTBot", "ClaudeBot", "Claude-SearchBot", "Claude-User",
                "PerplexityBot", "Perplexity-User", "Google-Extended", "Applebot-Extended", "Bingbot", "Googlebot"]


def sito_url() -> str:
    return (os.environ.get("SITO_URL") or "https://finanzagevolata.qiaro.it").rstrip("/")


def assoluto(percorso: str) -> str:
    return sito_url() + (percorso if percorso.startswith("/") else "/" + percorso)


def robots_txt(pubblica: bool) -> str:
    if not pubblica:
        return ("# Bandi Radar: sito non ancora aperto ai motori di ricerca (PAGINA_PUBBLICA=0).\n"
                "User-agent: *\nDisallow: /\n")
    righe = ["# Bandi Radar: si leggono solo le pagine pubbliche; plancia, area riservata e API restano chiuse.",
             "# I motori di risposta IA sono benvenuti con le stesse regole.", "User-agent: *"]
    righe += [f"User-agent: {p}" for p in PROGRAMMI_IA]
    righe += ["Allow: /$", "Allow: /?"]                     # la home, anche con i parametri degli annunci
    righe += [f"Allow: {p}$" for p, _, _ in PAGINE_PUBBLICHE if p != "/"]
    righe += [f"Allow: {p}" for p in FILE_PUBBLICI]
    righe += ["Disallow: /", "", f"Sitemap: {assoluto('/sitemap.xml')}", ""]
    return "\n".join(righe)


def sitemap_xml(ultimo_aggiornamento: date | None = None) -> str:
    oggi = (ultimo_aggiornamento or date.today()).isoformat()
    voci = []
    for percorso, freq, prio in PAGINE_PUBBLICHE:
        lastmod = f"<lastmod>{oggi}</lastmod>" if percorso == "/" else ""
        voci.append(f"<url><loc>{escape(assoluto(percorso))}</loc>{lastmod}<changefreq>{freq}</changefreq>"
                    f"<priority>{prio}</priority></url>")
    return ('<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
            + "\n".join(voci) + "\n</urlset>\n")


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


def domande_frequenti(faq: list[tuple[str, str]]) -> dict:
    return {"@type": "FAQPage", "@id": assoluto("/#domande"),
            "mainEntity": [{"@type": "Question", "name": d, "acceptedAnswer": {"@type": "Answer", "text": r}} for d, r in faq]}
