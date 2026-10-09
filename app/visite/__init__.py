"""Statistiche delle pagine pubbliche senza cookie (08/10/2026, richiesta di Matteo per misurare SEO e GEO).

Per le sole pagine pubbliche (/, /blog, /blog/<slug>, /bandi-aperti e /bandi-aperti/<regione>, /llms.txt, /sitemap.xml, /robots.txt) si conta ogni visita in
una riga aggregata per giorno della tabella `visite` (migrazione 033): percorso, dominio di provenienza (solo il
dominio del Referer, es. google.com, chatgpt.com; "diretto" se manca), parametri utm_source/utm_medium/utm_campaign,
tipo di visitatore (persona, motore di ricerca, IA, altro programma) con il nome del programma, e il conteggio.

Privacy: NON si salvano indirizzi IP, User-Agent completi, cookie o altri identificativi; nessun cookie viene creato.
Dallo User-Agent si ricava solo il nome di un programma noto (Googlebot, GPTBot...), poi lo User-Agent si butta.
Non si contano le visite di chi ha fatto l'accesso (Matteo e i collaboratori che rileggono il blog) ne' le pagine
che non esistono (si conta solo la risposta 200). Dal 09/10 (Matteo: "sta contando anche i nostri accessi") non si
contano nemmeno: i browser in cui qualcuno ha gia' fatto l'accesso almeno una volta (cookie tecnico NON_CONTARE, messo
all'accesso e lasciato dopo l'uscita), la pagina "/" finche' la presentazione e' spenta (e' solo la pagina d'accesso)
e le persone che aprono robots.txt, sitemap.xml e llms.txt (file per i programmi: le apriamo noi per controllarle).

La pagina "Visite" della plancia (permesso "lavoro") legge `riepilogo()` tramite /api/visite.
"""

from __future__ import annotations

import logging
import os
import re
from urllib.parse import parse_qs, urlparse

log = logging.getLogger(__name__)

NON_CONTARE = "br_non_contare"
FILE_PER_PROGRAMMI = {"/robots.txt", "/sitemap.xml", "/llms.txt"}

# Pagine contate: percorsi esatti, piu' gli articoli /blog/<slug> e le pagine /bandi-aperti/<regione> (09/10).
PERCORSI = {"/", "/blog", "/llms.txt", "/sitemap.xml", "/robots.txt", "/bandi-aperti"}
_ARTICOLO = re.compile(r"^/(blog|bandi-aperti)/[a-z0-9][a-z0-9-]{0,150}$")

TIPI_VISITATORE = {"persona": "persone", "motore": "motori di ricerca", "ia": "programmi delle IA",
                   "altro": "altri programmi"}

# Programmi riconosciuti dallo User-Agent: (pezzo da cercare, minuscolo; nome; tipo). Il primo che corrisponde vince:
# i nomi piu' specifici stanno prima (Applebot-Extended prima di Applebot, ChatGPT-User prima di GPTBot...).
PROGRAMMI = [
    # Motori di risposta IA e raccolta di testi per l'addestramento.
    ("oai-searchbot", "OAI-SearchBot", "ia"), ("chatgpt-user", "ChatGPT-User", "ia"), ("gptbot", "GPTBot", "ia"),
    ("claude-searchbot", "Claude-SearchBot", "ia"), ("claude-user", "Claude-User", "ia"), ("claudebot", "ClaudeBot", "ia"),
    ("claude-web", "Claude-Web", "ia"), ("anthropic-ai", "anthropic-ai", "ia"),
    ("perplexity-user", "Perplexity-User", "ia"), ("perplexitybot", "PerplexityBot", "ia"),
    ("google-extended", "Google-Extended", "ia"), ("googleother", "GoogleOther", "ia"),
    ("gemini-deep-research", "Gemini-Deep-Research", "ia"), ("google-notebooklm", "Google-NotebookLM", "ia"),
    ("applebot-extended", "Applebot-Extended", "ia"), ("meta-externalagent", "Meta-ExternalAgent", "ia"),
    ("meta-externalfetcher", "Meta-ExternalFetcher", "ia"), ("ccbot", "CCBot", "ia"), ("bytespider", "Bytespider", "ia"),
    ("amazonbot", "Amazonbot", "ia"), ("mistralai-user", "MistralAI-User", "ia"), ("duckassistbot", "DuckAssistBot", "ia"),
    ("cohere-ai", "cohere-ai", "ia"), ("youbot", "YouBot", "ia"), ("diffbot", "Diffbot", "ia"), ("timpibot", "Timpibot", "ia"),
    ("deepseekbot", "DeepSeekBot", "ia"), ("ai2bot", "AI2Bot", "ia"), ("omgili", "Omgili", "ia"),
    # Motori di ricerca.
    ("googlebot", "Googlebot", "motore"), ("google-inspectiontool", "Google-InspectionTool", "motore"),
    ("storebot-google", "Storebot-Google", "motore"), ("adsbot-google", "AdsBot-Google", "motore"),
    ("google-site-verification", "Google-Site-Verification", "motore"), ("bingbot", "Bingbot", "motore"),
    ("bingpreview", "BingPreview", "motore"), ("msnbot", "msnbot", "motore"), ("adidxbot", "AdIdxBot", "motore"),
    ("applebot", "Applebot", "motore"), ("duckduckbot", "DuckDuckBot", "motore"), ("yandex", "YandexBot", "motore"),
    ("baiduspider", "Baiduspider", "motore"), ("qwant", "Qwantbot", "motore"), ("seznambot", "SeznamBot", "motore"),
    ("petalbot", "PetalBot", "motore"), ("mojeek", "MojeekBot", "motore"),
    ("yeti", "Naver Yeti", "motore"), ("sogou", "Sogou", "motore"),
    # Anteprime dei social e strumenti SEO: non sono persone.
    ("facebookexternalhit", "Facebook", "altro"), ("linkedinbot", "LinkedInBot", "altro"), ("twitterbot", "Twitterbot", "altro"),
    ("slackbot", "Slackbot", "altro"), ("whatsapp", "WhatsApp", "altro"), ("telegrambot", "TelegramBot", "altro"),
    ("discordbot", "Discordbot", "altro"), ("ahrefsbot", "AhrefsBot", "altro"), ("semrushbot", "SemrushBot", "altro"),
    ("mj12bot", "MJ12bot", "altro"), ("dotbot", "DotBot", "altro"), ("dataforseobot", "DataForSeoBot", "altro"),
    ("screaming frog", "Screaming Frog", "altro"),
]
_GENERICI = ("bot", "crawl", "spider", "slurp", "fetch", "curl/", "wget/", "python-", "httpx", "go-http-client",
             "java/", "okhttp", "headless", "scrapy", "node-fetch", "axios", "libwww", "uptime", "monitor")

# Provenienze per gruppo, per la pagina Visite (si confronta il dominio senza "www." e i sottodomini noti).
DOMINI_IA = {"chatgpt.com", "chat.openai.com", "openai.com", "perplexity.ai", "copilot.microsoft.com", "gemini.google.com",
             "bard.google.com", "claude.ai", "chat.mistral.ai", "you.com", "chat.deepseek.com", "deepseek.com", "meta.ai",
             "grok.com", "x.ai", "phind.com", "duck.ai", "notebooklm.google.com", "aistudio.google.com", "kagi.com"}
_MOTORI = re.compile(r"^(google\.[a-z.]+|bing\.com|cn\.bing\.com|duckduckgo\.com|search\.yahoo\.com|[a-z]+\.search\.yahoo\.com|"
                     r"yahoo\.com|ecosia\.org|qwant\.com|yandex\.[a-z.]+|baidu\.com|startpage\.com|search\.brave\.com|"
                     r"com\.google\.android\.googlequicksearchbox|search\.lilo\.org|libero\.it|virgilio\.it)$")
_SOCIAL = re.compile(r"^((l|lm|m)\.)?(facebook\.com|instagram\.com|linkedin\.com|lnkd\.in|t\.co|x\.com|twitter\.com|"
                     r"reddit\.com|youtube\.com|whatsapp\.com|web\.whatsapp\.com|t\.me|telegram\.org|threads\.net)$")

MASSIMO_UTM = 80


def percorso_contato(percorso: str) -> str | None:
    """Il percorso da contare, o None se la pagina non e' tra quelle pubbliche."""
    p = percorso.rstrip("/") or "/"
    if p in PERCORSI or _ARTICOLO.match(p):
        return p
    return None


def visitatore(user_agent: str | None) -> tuple[str, str]:
    """(tipo, programma) dallo User-Agent: ("persona", "") se non e' un programma riconosciuto."""
    ua = (user_agent or "").lower()
    if not ua.strip():
        return "altro", "senza nome"
    for pezzo, nome, tipo in PROGRAMMI:
        if pezzo in ua:
            return tipo, nome
    if any(g in ua for g in _GENERICI):
        return "altro", "altro programma"
    return "persona", ""


def _dominio(host: str | None) -> str:
    h = (host or "").strip().lower().rstrip(".")
    for prefisso in ("www.", "m."):
        if h.startswith(prefisso):
            h = h[len(prefisso):]
    return h[:100]


def provenienza(referer: str | None, propri: set[str]) -> str:
    """Solo il dominio del Referer (es. google.it, chatgpt.com); "diretto" se manca, "interno" se e' il nostro sito."""
    if not referer:
        return "diretto"
    try:
        u = urlparse(referer.strip())
        host = u.hostname or (u.netloc if u.scheme == "android-app" else "")
    except ValueError:
        return "altro"
    d = _dominio(host)
    if not d:
        return "diretto"
    return "interno" if d in propri else d


def gruppo_provenienza(dominio: str) -> str:
    """ia / motore / social / diretto / interno / altro: serve alla pagina Visite per evidenziare i motori IA."""
    if dominio in ("diretto", "interno"):
        return dominio
    if dominio in DOMINI_IA or any(dominio.endswith("." + x) for x in DOMINI_IA):
        return "ia"
    if _MOTORI.match(dominio):
        return "motore"
    if _SOCIAL.match(dominio):
        return "social"
    return "altro"


def utm(query: str) -> tuple[str, str, str]:
    """(utm_source, utm_medium, utm_campaign), minuscoli e accorciati; vuoti se mancano."""
    q = parse_qs(query or "", keep_blank_values=False)

    def uno(nome: str) -> str:
        v = (q.get(nome) or [""])[0].strip().lower()
        return "".join(c for c in v if c.isprintable())[:MASSIMO_UTM]

    return uno("utm_source"), uno("utm_medium"), uno("utm_campaign")


def domini_propri() -> set[str]:
    from app.pubblico import seo

    propri = {_dominio(urlparse(seo.sito_url()).hostname), "bandinqiaro.it", "finanzagevolata.qiaro.it"}
    return {d for d in propri if d}


def _presentazione_accesa() -> bool:
    from app.pubblico import pubblica

    return pubblica()


def registra(percorso: str, referer: str | None, user_agent: str | None, query: str) -> None:
    """Conta una visita (una riga per giorno e combinazione). Non solleva mai errori: la pagina non deve cadere."""
    if not os.environ.get("PGHOST"):
        return
    tipo, programma = visitatore(user_agent)
    if tipo == "persona" and (percorso in FILE_PER_PROGRAMMI or (percorso == "/" and not _presentazione_accesa())):
        return
    # Le provenienze e le campagne contano solo per le persone: i programmi non le mandano o le mandano a caso.
    da = provenienza(referer, domini_propri()) if tipo == "persona" else "diretto"
    sorgente, mezzo, campagna = utm(query) if tipo == "persona" else ("", "", "")
    try:
        from app.db.connessione import connetti

        with connetti(autocommit=True) as conn:
            conn.execute("""INSERT INTO visite (giorno, percorso, provenienza, utm_source, utm_medium, utm_campaign,
                                                visitatore, programma, conteggio)
                            VALUES (current_date, %s, %s, %s, %s, %s, %s, %s, 1)
                            ON CONFLICT (giorno, percorso, provenienza, utm_source, utm_medium, utm_campaign, visitatore, programma)
                            DO UPDATE SET conteggio = visite.conteggio + 1""",
                         (percorso, da, sorgente, mezzo, campagna, tipo, programma))
    except Exception:  # noqa: BLE001 - una statistica persa non deve rompere la pagina
        log.warning("visita non registrata", exc_info=True)


def riepilogo(conn, giorni: int = 30) -> dict:
    """I numeri della pagina Visite: ultimi `giorni` giorni (oggi compreso)."""
    giorni = max(1, min(int(giorni), 366))
    filtro = "giorno > current_date - %(g)s::int"
    p = {"g": giorni}
    with conn.cursor() as cur:
        cur.execute(f"""SELECT giorno, sum(conteggio) FILTER (WHERE visitatore = 'persona') AS persone,
                               sum(conteggio) FILTER (WHERE visitatore = 'motore') AS motori,
                               sum(conteggio) FILTER (WHERE visitatore = 'ia') AS ia,
                               sum(conteggio) FILTER (WHERE visitatore = 'altro') AS altri
                        FROM visite WHERE {filtro} GROUP BY giorno ORDER BY giorno DESC""", p)
        per_giorno = [{k: (v or 0) if k != "giorno" else v.isoformat() for k, v in r.items()} for r in cur.fetchall()]
        cur.execute(f"""SELECT percorso, sum(conteggio) FILTER (WHERE visitatore = 'persona') AS persone,
                               sum(conteggio) FILTER (WHERE visitatore = 'motore') AS motori,
                               sum(conteggio) FILTER (WHERE visitatore = 'ia') AS ia,
                               sum(conteggio) FILTER (WHERE visitatore = 'altro') AS altri, sum(conteggio) AS totale
                        FROM visite WHERE {filtro} GROUP BY percorso
                        ORDER BY persone DESC NULLS LAST, totale DESC LIMIT 50""", p)
        pagine = [{k: (v or 0) if k != "percorso" else v for k, v in r.items()} for r in cur.fetchall()]
        cur.execute(f"""SELECT provenienza, sum(conteggio) AS visite FROM visite
                        WHERE {filtro} AND visitatore = 'persona' GROUP BY provenienza ORDER BY visite DESC LIMIT 50""", p)
        provenienze = [dict(r, gruppo=gruppo_provenienza(r["provenienza"])) for r in cur.fetchall()]
        cur.execute(f"""SELECT percorso, visitatore, programma, sum(conteggio) AS visite, max(giorno) AS ultima
                        FROM visite WHERE {filtro} AND visitatore IN ('ia', 'motore')
                        GROUP BY percorso, visitatore, programma ORDER BY visitatore, percorso, visite DESC""", p)
        programmi = [dict(r, ultima=r["ultima"].isoformat()) for r in cur.fetchall()]
        cur.execute(f"""SELECT utm_source, utm_medium, utm_campaign, sum(conteggio) AS visite FROM visite
                        WHERE {filtro} AND (utm_source <> '' OR utm_medium <> '' OR utm_campaign <> '')
                        GROUP BY 1, 2, 3 ORDER BY visite DESC LIMIT 50""", p)
        campagne = [dict(r) for r in cur.fetchall()]
    totali = {k: sum(g[k] for g in per_giorno) for k in ("persone", "motori", "ia", "altri")}
    da_ia = sum(x["visite"] for x in provenienze if x["gruppo"] == "ia")
    return {"giorni": giorni, "totali": totali | {"persone_da_ia": da_ia}, "per_giorno": per_giorno, "pagine": pagine,
            "provenienze": provenienze, "programmi": programmi, "campagne": campagne, "tipi": TIPI_VISITATORE}
