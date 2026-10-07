"""Pagina pubblica di presentazione (landing), testi legali e file per i motori di ricerca (05/10 e 07/10/2026).

HTML semplice servito dal server (niente React): si carica subito ed e' leggibile dai motori di ricerca e dai motori
di risposta IA.
- /presentazione: sempre visibile (anteprima per Matteo, non indicizzata finche' la pagina non e' accesa);
- /: la presentazione per chi non ha fatto l'accesso, solo con PAGINA_PUBBLICA=1 (finche' e' spenta "/" porta
  all'accesso come prima);
- /termini, /privacy, /cookie, /condizioni-supporto, /note-legali: bozze in app/pubblico/testi/, da far rivedere a un
  professionista;
- /robots.txt, /sitemap.xml, /llms.txt, /favicon.svg, /immagini/...: SEO tecnica e GEO (app/pubblico/seo.py).
La pagina di atterraggio e' in app/pubblico/landing.py; il dominio dei link canonici viene da SITO_URL.

Strumenti di misura (Google Ads, Google Analytics 4): si attivano SOLO mettendo GOOGLE_ADS_ID e/o
GOOGLE_ANALYTICS_ID nel .env; senza ID non si carica nulla di Google e il banner dei cookie non compare. Con un ID il
banner chiede il consenso e i tag partono solo dopo "Accetta" (Consent Mode v2 in modalita' "base").
"""

from __future__ import annotations

import html
import os
from pathlib import Path
from urllib.parse import urlparse

from app.pubblico import seo

TESTI = Path(__file__).resolve().parent / "testi"
IMMAGINI = Path(__file__).resolve().parent / "immagini"
LEGALI = {"termini": ("termini.html", "Termini e condizioni"), "privacy": ("privacy.html", "Informativa privacy"),
          "cookie": ("cookie.html", "Cookie"), "condizioni-supporto": ("supporto.html", "Condizioni del servizio di supporto"),
          "note-legali": ("note_legali.html", "Note legali")}

# Prezzi del modello commerciale, IVA esclusa (Matteo, 05/10: impresa in piu' 10 euro e sede in piu' 5 euro confermati).
# Il prezzo di lancio mostrato nella landing (20 euro al mese) e' in landing.PREZZO_LANCIO.
PREZZI = {"mensile": 30, "annuale": 20, "impresa_in_piu": 10, "sede_in_piu": 5}


def pubblica() -> bool:
    return os.environ.get("PAGINA_PUBBLICA", "0") == "1"


def home() -> str:
    """Dove sta la presentazione: "/" quando e' accesa, altrimenti l'anteprima."""
    return "/" if pubblica() else "/presentazione"


def _e(testo) -> str:
    return html.escape(str(testo or ""))


def _euro(n) -> str:
    try:
        return f"{float(n):,.0f} €".replace(",", ".")
    except (TypeError, ValueError):
        return ""


def _id_google(nome: str) -> str:
    """ID di Google dal .env, solo lettere, cifre e trattini (niente caratteri pericolosi nella pagina)."""
    return "".join(c for c in os.environ.get(nome, "") if c.isalnum() or c == "-")


LOGO = ('<svg width="28" height="28" viewBox="0 0 32 32" aria-hidden="true"><circle cx="16" cy="16" r="15" fill="#163e7a"/>'
        '<circle cx="16" cy="16" r="10" fill="none" stroke="#7fb2ff" stroke-width="1.6"/><circle cx="16" cy="16" r="5" '
        'fill="none" stroke="#7fb2ff" stroke-width="1.6"/><path d="M16 16 L27 9" stroke="#fff" stroke-width="2.2" '
        'stroke-linecap="round"/><circle cx="22.5" cy="11.5" r="2.2" fill="#3fd17f"/></svg>')

STILE = """
:root{--blu:#163e7a;--accento:#1f5fbf;--verde:#1e8a4c;--grigio:#56606e;--sfondo:#f3f7fc;--bordo:#d5e1f0;--testo:#1c2430}
*{box-sizing:border-box}html{scroll-behavior:smooth;scroll-padding-top:4.5rem}
body{margin:0;font-family:system-ui,-apple-system,"Segoe UI",Roboto,sans-serif;color:var(--testo);background:#fff;line-height:1.6;font-size:17px}
a{color:var(--accento)}img,svg{max-width:100%}
.contenitore{max-width:72rem;margin:0 auto}.stretto{max-width:50rem}
header{display:flex;align-items:center;gap:1rem;padding:.7rem 5vw;border-bottom:1px solid var(--bordo);position:sticky;top:0;background:rgba(255,255,255,.97);z-index:5}
header .logo{display:flex;align-items:center;gap:.5rem;font-weight:800;font-size:1.25rem;color:var(--blu);text-decoration:none}
header nav{margin-left:auto;display:flex;gap:1.1rem;align-items:center}header nav a{text-decoration:none;color:var(--grigio);font-weight:500}
.bottone{display:inline-flex;align-items:center;justify-content:center;min-height:44px;background:var(--accento);color:#fff!important;padding:.55rem 1.15rem;border-radius:10px;text-decoration:none;font-weight:650;border:0;cursor:pointer;font-size:1rem}
.bottone:hover{background:#174ea0}.bottone.chiaro{background:#fff;color:var(--accento)!important;border:1.5px solid var(--accento)}
.bottone.grande{font-size:1.08rem;padding:.8rem 1.5rem}.bottone.bianco{background:#fff;color:var(--blu)!important}
section{padding:3.5rem 5vw}section.grigia{background:var(--sfondo)}
h1{font-size:2.6rem;line-height:1.12;color:var(--blu);margin:.3rem 0 1rem;letter-spacing:-.02em}h1 span{color:var(--accento)}
h2{font-size:1.75rem;line-height:1.2;color:var(--blu);margin:0 0 1.2rem;letter-spacing:-.01em}h3{color:var(--blu);margin:.2rem 0 .4rem;font-size:1.1rem}
.titoletto{margin-top:2.2rem}.sottotitolo{font-size:1.15rem;color:var(--grigio);max-width:46rem}
.eroe{background:linear-gradient(180deg,#eef4fd 0%,#fff 100%);padding-top:3rem}
.due{display:grid;grid-template-columns:1.15fr .85fr;gap:2.5rem;align-items:center}
.occhiello{color:var(--accento);font-weight:650;font-size:.9rem;text-transform:uppercase;letter-spacing:.05em;margin:0}
.azioni{display:flex;flex-wrap:wrap;gap:.8rem;margin:1.5rem 0 .8rem}.rassicura{color:var(--grigio);font-size:.92rem}
.anteprima .carta{transform:rotate(1deg);box-shadow:0 12px 40px rgba(22,62,122,.16)}
.griglia{display:grid;grid-template-columns:repeat(auto-fit,minmax(240px,1fr));gap:1.2rem}
.carta{background:#fff;border:1px solid var(--bordo);border-radius:14px;padding:1.2rem 1.3rem;box-shadow:0 2px 10px rgba(22,62,122,.06)}
.scheda h3{font-size:1.02rem}.riga-tipi{display:flex;flex-wrap:wrap;gap:.3rem;align-items:center}
.piede-scheda{display:flex;flex-wrap:wrap;justify-content:space-between;gap:.5rem;font-size:.88rem;border-top:1px solid var(--bordo);padding-top:.6rem}
.adatto{color:var(--verde);font-weight:650}
.numeri{padding:2rem 5vw;background:var(--blu);color:#fff}.cifre{display:grid;grid-template-columns:repeat(4,1fr);gap:1.2rem}
.cifra b{display:block;font-size:2.3rem;line-height:1.1}.cifra span{display:block;font-weight:600}.cifra small{color:#c5d6f2}
.aggiornato{color:#c5d6f2;font-size:.85rem;margin:1rem 0 0}
ol.passi{list-style:none;counter-reset:p;padding:0;display:grid;grid-template-columns:repeat(3,1fr);gap:1.2rem}
ol.passi li{counter-increment:p;background:#fff;border:1px solid var(--bordo);border-radius:14px;padding:1.2rem 1.3rem}
ol.passi li:before{content:counter(p);display:inline-flex;width:2.1rem;height:2.1rem;border-radius:50%;background:var(--accento);color:#fff;font-weight:800;align-items:center;justify-content:center;margin-bottom:.6rem}
ol.passi b{display:block;color:var(--blu);font-size:1.1rem;margin-bottom:.3rem}ol.passi span{color:var(--grigio)}
ul.fonti{list-style:none;padding:0;margin:.6rem 0 0;font-size:.95rem}ul.fonti b{color:var(--blu)}
ul.regioni{list-style:none;padding:0;display:grid;grid-template-columns:repeat(auto-fill,minmax(150px,1fr));gap:.5rem}
ul.regioni li{display:flex;justify-content:space-between;background:#fff;border:1px solid var(--bordo);border-radius:8px;padding:.45rem .8rem}
ul.regioni b{color:var(--blu)}
.numero{font-size:2.2rem;font-weight:800;color:var(--blu)}.etichetta{color:var(--grigio);font-size:.82rem;text-transform:uppercase;letter-spacing:.04em;font-weight:650}
.tipo{display:inline-block;background:#e3edf9;color:var(--blu);border-radius:4px;padding:.1rem .45rem;font-size:.78rem}
.scadenza{color:#b0392f;font-weight:600}.prezzo{font-size:2.6rem;font-weight:800;color:var(--blu)}.prezzo small{font-size:1rem;color:var(--grigio);font-weight:500}
.evidenza{border:2px solid var(--accento)}.piccolo{font-size:.86rem;color:var(--grigio)}
ul.spunte{list-style:none;padding:0}ul.spunte li{padding:.2rem 0}ul.spunte li:before{content:"✓ ";color:var(--verde);font-weight:700}
table{border-collapse:collapse;width:100%;font-size:.93rem}th,td{text-align:left;padding:.45rem .4rem;border-bottom:1px solid var(--bordo);vertical-align:top}
.finale{background:var(--blu);color:#fff;text-align:center}.finale h2{color:#fff}
footer{padding:2rem 5vw;border-top:1px solid var(--bordo);color:var(--grigio);font-size:.9rem;display:flex;flex-wrap:wrap;gap:.6rem 1.2rem}
.testo-legale{max-width:50rem}.testo-legale h1{font-size:2rem}.bozza{background:#fff6e0;border-left:4px solid #e0a800;padding:.7rem 1rem;border-radius:6px}
#banner-cookie{position:fixed;left:1rem;right:1rem;bottom:1rem;background:#fff;border:1px solid var(--bordo);border-radius:12px;box-shadow:0 4px 24px rgba(0,0,0,.15);padding:1rem 2.6rem 1rem 1.2rem;display:none;gap:1rem;align-items:center;flex-wrap:wrap;z-index:10;max-width:60rem;margin:0 auto}
#cookie-chiudi{position:absolute;top:.3rem;right:.4rem;background:none;border:0;font-size:1.5rem;cursor:pointer;color:var(--grigio);min-width:44px;min-height:44px}
details{border-bottom:1px solid var(--bordo);padding:.4rem 0}summary{font-weight:650;cursor:pointer;padding:.5rem 0;min-height:44px;display:flex;align-items:center}details p{margin:.2rem 0 .8rem;color:#2d3846}
@media(max-width:860px){.due,ol.passi{grid-template-columns:1fr}.cifre{grid-template-columns:repeat(2,1fr)}.anteprima .carta{transform:none}}
@media(max-width:700px){body{font-size:16px}h1{font-size:1.95rem}h2{font-size:1.45rem}section{padding:2.4rem 5vw}header nav a.nascondi{display:none}
.cifra b{font-size:1.8rem}.azioni .bottone{flex:1 1 100%}}
"""

# Consenso ai cookie (Consent Mode v2, modalita' "base"): senza GOOGLE_ADS_ID / GOOGLE_ANALYTICS_ID non si carica
# nulla e il banner non compare. Con un ID: banner con Accetta, Rifiuta e X (= rifiuta, linee guida del Garante
# 10/06/2021); i tag di Google si caricano solo dopo "Accetta". La scelta vale 6 mesi, poi il banner torna.
# Le conversioni (registrazione completata) si misurano nella plancia: vedi docs/ricerche/2026-10-07_landing_seo_geo.md.
_SCRIPT_COOKIE = """
<div id="banner-cookie" role="dialog" aria-label="Cookie">
  <button id="cookie-chiudi" aria-label="Chiudi e rifiuta">×</button>
  <div style="flex:1;min-width:16rem">Usiamo un cookie tecnico per l'accesso. Con il tuo consenso usiamo anche cookie di misurazione
  per capire quali annunci funzionano. <a href="/cookie">Dettagli</a></div>
  <button class="bottone chiaro" id="cookie-no">Rifiuta</button> <button class="bottone chiaro" id="cookie-si">Accetta</button>
</div>
<script>
(function(){
  var IDS = ["__GOOGLE_ADS_ID__", "__GOOGLE_ANALYTICS_ID__"].filter(Boolean), chiave = "br_consenso", banner = document.getElementById("banner-cookie");
  function carica(){
    if (!IDS.length || window.gtag) return;
    window.dataLayer = window.dataLayer || []; function gtag(){dataLayer.push(arguments);} window.gtag = gtag;
    gtag("consent", "default", {ad_storage:"denied", ad_user_data:"denied", ad_personalization:"denied", analytics_storage:"denied"});
    gtag("consent", "update", {ad_storage:"granted", ad_user_data:"granted", ad_personalization:"granted", analytics_storage:"granted"});
    var s = document.createElement("script"); s.async = true; s.src = "https://www.googletagmanager.com/gtag/js?id=" + IDS[0]; document.head.appendChild(s);
    gtag("js", new Date()); IDS.forEach(function(id){ gtag("config", id); });
  }
  function scegli(v){ try { localStorage.setItem(chiave, v + "|" + Date.now()); } catch(e) {} banner.style.display = "none"; if (v === "si") carica(); }
  var scelta = null;
  try { var s = (localStorage.getItem(chiave) || "").split("|"); if (s[1] && Date.now() - Number(s[1]) < 182 * 864e5) scelta = s[0]; } catch(e) {}
  if (scelta === "si") carica(); else if (scelta !== "no" && IDS.length) banner.style.display = "flex";
  document.getElementById("cookie-si").onclick = function(){ scegli("si"); };
  document.getElementById("cookie-no").onclick = function(){ scegli("no"); };
  document.getElementById("cookie-chiudi").onclick = function(){ scegli("no"); };
  var rivedi = document.getElementById("rivedi-cookie");
  if (rivedi) rivedi.onclick = function(e){ e.preventDefault(); try { localStorage.removeItem(chiave); } catch(x) {} banner.style.display = "flex"; };
})();
</script>"""


def _cookie() -> str:
    ads, ga = _id_google("GOOGLE_ADS_ID"), _id_google("GOOGLE_ANALYTICS_ID")
    return _SCRIPT_COOKIE.replace("__GOOGLE_ADS_ID__", ads).replace("__GOOGLE_ANALYTICS_ID__", ga)


def pagina(titolo: str, corpo: str, descrizione: str = "", indicizza: bool = False, percorso: str | None = None,
           testa: str = "") -> str:
    """La cornice comune: intestazione, piede con i testi legali, banner dei cookie. Con `percorso` aggiunge l'URL
    canonico e i dati per le anteprime (Open Graph); `testa` va nell'<head> (es. il JSON-LD)."""
    robots = "index, follow, max-snippet:-1, max-image-preview:large" if indicizza else "noindex, nofollow"
    meta = ""
    if percorso:
        url = seo.assoluto(percorso)
        immagine = seo.assoluto("/immagini/anteprima.png")
        meta = (f'<link rel="canonical" href="{_e(url)}"><meta property="og:type" content="website">'
                f'<meta property="og:site_name" content="{seo.NOME}"><meta property="og:locale" content="it_IT">'
                f'<meta property="og:title" content="{_e(titolo)}"><meta property="og:description" content="{_e(descrizione)}">'
                f'<meta property="og:url" content="{_e(url)}"><meta property="og:image" content="{_e(immagine)}">'
                '<meta property="og:image:width" content="1200"><meta property="og:image:height" content="630">'
                '<meta name="twitter:card" content="summary_large_image">')
    h = home()
    titolare = os.environ.get("TITOLARE_SITO", "").strip()     # es. "Studio ... · P.IVA ..." (Google Ads lo chiede)
    dominio = urlparse(seo.sito_url()).hostname or ""
    return f"""<!doctype html><html lang="it"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1"><meta name="robots" content="{robots}">
<title>{_e(titolo)}</title><meta name="description" content="{_e(descrizione)}">{meta}
<link rel="icon" href="/favicon.svg" type="image/svg+xml"><meta name="theme-color" content="#163e7a">
<style>{STILE}</style>{testa}</head><body>
<header><a class="logo" href="{h}">{LOGO}<span>Bandi Radar</span></a><nav><a class="nascondi" href="{h}#come">Come funziona</a>
<a class="nascondi" href="{h}#prezzo">Prezzo</a><a class="nascondi" href="{h}#domande">Domande</a><a href="/accedi">Accedi</a>
<a class="bottone" href="/registrati">Prova gratis</a></nav></header>
<main>{corpo}</main>
<footer><span>© Bandi Radar · {_e(dominio)}{(' · ' + _e(titolare)) if titolare else ''}</span><a href="/termini">Termini</a>
<a href="/privacy">Privacy</a><a href="/cookie">Cookie</a><a href="/condizioni-supporto">Condizioni del supporto</a>
<a href="/note-legali">Note legali</a></footer>
{_cookie()}</body></html>"""


def esempi(conn, quanti: int = 3) -> list[dict]:
    """Schede di esempio: quelle scelte da Matteo (ESEMPI_BANDI=12,34,56) o, se mancano, bandi aperti proponibili
    con importo e sintesi, di enti diversi, con la scadenza piu' lontana di tre settimane."""
    scelti = [int(x) for x in os.environ.get("ESEMPI_BANDI", "").split(",") if x.strip().isdigit()]
    colonne = "id, titolo, ente, stato, scadenza, sintesi, tipi_agevolazione, contributo_massimo, percentuale"
    with conn.cursor() as cur:
        if scelti:
            cur.execute(f"SELECT {colonne} FROM bandi WHERE id = ANY(%s) AND completezza = 'bando_ufficiale'", (scelti,))
        else:
            cur.execute(f"""SELECT DISTINCT ON (ente) {colonne} FROM bandi
                            WHERE completezza = 'bando_ufficiale' AND stato = 'aperto' AND sintesi IS NOT NULL AND unito_a IS NULL
                              AND contributo_massimo IS NOT NULL AND scadenza > current_date + 21
                              AND id IN (SELECT id FROM bandi_situazione WHERE situazione = 'proponibile')
                            ORDER BY ente, coalesce(qualita, 3) DESC, contributo_massimo DESC""")
        righe = [dict(r) for r in cur.fetchall()]
    righe.sort(key=lambda r: (-(r["contributo_massimo"] or 0)))
    return righe[:quanti]


def presentazione(conn) -> str:
    from app.pubblico import landing

    return landing.presentazione(conn)


def legale(nome: str) -> str | None:
    if nome not in LEGALI:
        return None
    file, titolo = LEGALI[nome]
    percorso = TESTI / file
    testo = percorso.read_text(encoding="utf-8") if percorso.is_file() else f"<h1>{_e(titolo)}</h1><p>Testo in preparazione.</p>"
    return pagina(f"{titolo} - Bandi Radar", f'<section class="testo-legale">{testo}</section>', titolo,
                  indicizza=pubblica(), percorso=f"/{nome}")
