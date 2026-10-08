"""IndexNow (09/10/2026, valutazione SEO/GEO): avvisa subito Bing, Yandex, Seznam, Naver e gli altri motori che
aderiscono quando una pagina del blog nasce o cambia. Bing e' l'indice da cui pescano ChatGPT e Copilot: senza avviso
un sito nuovo aspetta giorni o settimane prima di essere letto. Google non usa IndexNow (per Google c'e' la sitemap).

Come funziona:
- la chiave e' una stringa casuale nel .env (INDEXNOW_KEY, 8-128 lettere, cifre o trattini) e il sito la mostra su
  /<chiave>.txt: e' la prova che l'avviso viene davvero da noi;
- quando l'admin pubblica, ripubblica, modifica o ritira un articolo (pagina Blog della plancia) partono gli indirizzi
  dell'articolo e di /blog, in un filo a parte: la pubblicazione non aspetta e non fallisce mai per l'avviso;
- una volta al giorno il servizio raccolta manda gli indirizzi della sitemap del blog cambiati dall'ultimo invio (rete
  di sicurezza se un avviso e' andato perso). Ogni esito finisce nel log e nella pagina Supervisione.
Si avvisa solo con il blog aperto ai motori (BLOG_PUBBLICO=1 o PAGINA_PUBBLICA=1) e la chiave impostata.
"""

from __future__ import annotations

import os
import re
import threading
from datetime import date
from urllib.parse import urlparse

from app.pubblico import seo

INDIRIZZO = "https://api.indexnow.org/indexnow"
ATTESA_SECONDI = 15
MAX_URL = 10000                 # limite del protocollo per una richiesta
_CHIAVE = re.compile(r"^[A-Za-z0-9-]{8,128}$")
NOME_INVIO = "indexnow"         # in notifiche_inviate: un invio della sitemap al giorno


def chiave() -> str | None:
    k = os.environ.get("INDEXNOW_KEY", "").strip()
    return k if _CHIAVE.match(k) else None


def attivo() -> bool:
    from app.pubblico import blog_pubblico

    return bool(chiave()) and blog_pubblico()


def _post(url: str, dati: dict) -> int:
    """La chiamata vera (separata per sostituirla nei test): ritorna il codice HTTP."""
    import httpx

    r = httpx.post(url, json=dati, timeout=ATTESA_SECONDI,
                   headers={"User-Agent": "BandiRadar/1.0 (+" + seo.sito_url() + ")"})
    return r.status_code


# Significato dei codici di risposta (documentazione di indexnow.org).
_ESITI = {200: "ricevuti", 202: "ricevuti, chiave in verifica", 400: "richiesta non valida",
          403: "chiave non valida o file della chiave non trovato", 422: "indirizzi non del nostro sito o chiave sbagliata",
          429: "troppe richieste"}


def invia(urls: list[str]) -> str:
    """Manda gli indirizzi a IndexNow e ritorna l'esito in parole. Non solleva mai eccezioni."""
    k = chiave()
    if not k:
        return "IndexNow non attivo: manca INDEXNOW_KEY (o non e' valida)"
    from app.pubblico import blog_pubblico

    if not blog_pubblico():
        return "IndexNow non attivo: il blog non e' aperto ai motori (BLOG_PUBBLICO=0)"
    host = urlparse(seo.sito_url()).hostname or ""
    nostri = list(dict.fromkeys(u for u in urls if urlparse(u).hostname == host))[:MAX_URL]
    if not nostri:
        return "IndexNow: nessun indirizzo da avvisare"
    dati = {"host": host, "key": k, "keyLocation": seo.assoluto(f"/{k}.txt"), "urlList": nostri}
    try:
        codice = _post(INDIRIZZO, dati)
    except Exception as e:  # noqa: BLE001 - un avviso perso non deve fermare niente
        esito = f"IndexNow: errore di rete ({type(e).__name__}: {e}) per {len(nostri)} indirizzi"
    else:
        esito = f"IndexNow: {len(nostri)} indirizzi, risposta {codice} ({_ESITI.get(codice, 'inattesa')})"
    print(esito, flush=True)                            # nel log del container (docker compose logs)
    return esito


def avvisa_in_disparte(urls: list[str]) -> threading.Thread | None:
    """Avvisa in un filo a parte (chi pubblica non aspetta la risposta). None se IndexNow non e' attivo."""
    if not attivo() or not urls:
        return None
    t = threading.Thread(target=invia, args=(list(urls),), name="indexnow", daemon=True)
    t.start()
    return t


def indirizzi_articolo(slug: str, slug_prima: str | None = None) -> list[str]:
    """L'articolo, l'elenco del blog e, se l'indirizzo e' cambiato, anche quello vecchio (cosi' sparisce prima)."""
    urls = [seo.assoluto(f"/blog/{slug}"), seo.assoluto("/blog")]
    if slug_prima and slug_prima != slug:
        urls.append(seo.assoluto(f"/blog/{slug_prima}"))
    return urls


def articolo_cambiato(prima: dict | None, dopo: dict) -> threading.Thread | None:
    """Da chiamare dopo aver salvato un articolo: avvisa se era o e' pubblicato (pubblicato, ripubblicato,
    modificato da pubblicato, rimesso in bozza o archiviato). Le bozze non interessano ai motori."""
    if dopo.get("stato") != "pubblicato" and (prima or {}).get("stato") != "pubblicato":
        return None
    return avvisa_in_disparte(indirizzi_articolo(dopo["slug"], (prima or {}).get("slug")))


def gia_fatto_oggi(conn, oggi: date | None = None) -> bool:
    from app.notifiche.novita_settimana import gia_inviato

    return gia_inviato(conn, NOME_INVIO, (oggi or date.today()).isoformat())


def invio_del_giorno(conn, oggi: date | None = None) -> str | None:
    """Una volta al giorno (servizio raccolta): gli indirizzi della sitemap del blog cambiati dall'ultimo invio (tutti,
    la prima volta). None se oggi e' gia' stato fatto o se IndexNow non e' attivo."""
    from app.notifiche.novita_settimana import gia_inviato, registra_invio
    from app.pubblico import blog

    if not attivo():
        return None
    oggi = oggi or date.today()
    if gia_inviato(conn, NOME_INVIO, oggi.isoformat()):
        return None
    with conn.cursor() as cur:
        cur.execute("SELECT max(chiave) AS ultimo FROM notifiche_inviate WHERE nome = %s", (NOME_INVIO,))
        r = cur.fetchone()
    ultimo = r["ultimo"] if r else None
    voci = blog.voci_sitemap(conn)
    da_avvisare = [seo.assoluto(p) for p, modificato in voci if not ultimo or modificato >= ultimo]
    esito = invia(da_avvisare) if da_avvisare else "IndexNow: nessuna pagina del blog cambiata dall'ultimo invio"
    registra_invio(conn, NOME_INVIO, oggi.isoformat(), esito[:500])
    return esito


def file_chiave(nome: str) -> str | None:
    """Il testo di /<chiave>.txt se `nome` e' proprio quel file, altrimenti None (404)."""
    k = chiave()
    return k if k and nome == f"{k}.txt" else None

