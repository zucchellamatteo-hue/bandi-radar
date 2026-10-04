"""Pagina pubblica di presentazione e testi legali (05/10/2026, tappa 6 del prodotto indipendente).

HTML semplice servito dal server (niente React): si carica subito ed e' leggibile dai motori di ricerca.
- /presentazione: sempre visibile (anteprima per Matteo, non indicizzata finche' la pagina non e' accesa);
- /: la presentazione per chi non ha fatto l'accesso, solo con PAGINA_PUBBLICA=1 (prezzi e prova gratuita sono
  decisioni di Matteo: finche' non le prende, la pagina resta spenta e "/" porta all'accesso come prima);
- /termini, /privacy, /cookie, /condizioni-supporto: bozze in app/pubblico/testi/, da far rivedere a un professionista.
Cookie di misurazione (Google Ads, GOOGLE_ADS_ID) solo dopo il consenso nel banner.
"""

from __future__ import annotations

import html
import os
from pathlib import Path

TESTI = Path(__file__).resolve().parent / "testi"
LEGALI = {"termini": ("termini.html", "Termini e condizioni"), "privacy": ("privacy.html", "Informativa privacy"),
          "cookie": ("cookie.html", "Cookie"), "condizioni-supporto": ("supporto.html", "Condizioni del servizio di supporto")}

# Prezzi del modello commerciale del 04/10 (IVA, prova gratuita, impresa e sede in piu': da confermare con Matteo).
PREZZI = {"mensile": 30, "annuale": 20, "impresa_in_piu": 10, "sede_in_piu": 5}


def pubblica() -> bool:
    return os.environ.get("PAGINA_PUBBLICA", "0") == "1"


def _e(testo) -> str:
    return html.escape(str(testo or ""))


def _euro(n) -> str:
    try:
        return f"{float(n):,.0f} €".replace(",", ".")
    except (TypeError, ValueError):
        return ""


STILE = """
:root{--blu:#163e7a;--accento:#1f5fbf;--verde:#2e9e5b;--grigio:#5b6878;--sfondo:#f3f7fc;--bordo:#d5e1f0}
*{box-sizing:border-box}body{margin:0;font-family:system-ui,-apple-system,"Segoe UI",sans-serif;color:#1f2933;background:#fff;line-height:1.55}
a{color:var(--accento)}header{display:flex;align-items:center;gap:1.5rem;padding:.9rem 6vw;border-bottom:1px solid var(--bordo);position:sticky;top:0;background:#fff;z-index:5}
header .logo{font-weight:800;font-size:1.3rem;color:var(--blu);text-decoration:none}header nav{margin-left:auto;display:flex;gap:1.2rem;align-items:center}
header nav a{text-decoration:none;color:var(--grigio);font-weight:500}.bottone{display:inline-block;background:var(--accento);color:#fff!important;padding:.6rem 1.2rem;border-radius:8px;text-decoration:none;font-weight:650;border:0;cursor:pointer;font-size:1rem}
.bottone.chiaro{background:#fff;color:var(--accento)!important;border:1px solid var(--accento)}
section{padding:3.5rem 6vw}section.grigia{background:var(--sfondo)}h1{font-size:2.5rem;line-height:1.15;color:var(--blu);margin:.2rem 0 1rem;letter-spacing:-.02em}
h2{font-size:1.7rem;color:var(--blu);margin:0 0 1.2rem}h3{color:var(--accento);margin:.2rem 0 .4rem}.sottotitolo{font-size:1.2rem;color:var(--grigio);max-width:46rem}
.griglia{display:grid;grid-template-columns:repeat(auto-fit,minmax(240px,1fr));gap:1.2rem}.carta{background:#fff;border:1px solid var(--bordo);border-radius:12px;padding:1.2rem 1.3rem;box-shadow:0 2px 10px rgba(22,62,122,.06)}
.numero{font-size:2.2rem;font-weight:800;color:var(--blu)}.etichetta{color:var(--grigio);font-size:.85rem;text-transform:uppercase;letter-spacing:.04em;font-weight:600}
.tipo{display:inline-block;background:#e3edf9;color:var(--blu);border-radius:4px;padding:.1rem .45rem;font-size:.78rem;margin-right:.3rem}
.scadenza{color:#b0392f;font-weight:600}.prezzo{font-size:2.4rem;font-weight:800;color:var(--blu)}.prezzo small{font-size:1rem;color:var(--grigio);font-weight:500}
.evidenza{border:2px solid var(--accento)}.piccolo{font-size:.85rem;color:var(--grigio)}ul.spunte{list-style:none;padding:0}ul.spunte li{padding:.2rem 0}ul.spunte li:before{content:"✓ ";color:var(--verde);font-weight:700}
footer{padding:2rem 6vw;border-top:1px solid var(--bordo);color:var(--grigio);font-size:.9rem;display:flex;flex-wrap:wrap;gap:1.2rem}
.testo-legale{max-width:50rem}.testo-legale h1{font-size:2rem}.bozza{background:#fff6e0;border-left:4px solid #e0a800;padding:.7rem 1rem;border-radius:6px}
#banner-cookie{position:fixed;left:1rem;right:1rem;bottom:1rem;background:#fff;border:1px solid var(--bordo);border-radius:12px;box-shadow:0 4px 24px rgba(0,0,0,.15);padding:1rem 1.2rem;display:none;gap:1rem;align-items:center;flex-wrap:wrap;z-index:10;max-width:60rem;margin:0 auto}
details{border-bottom:1px solid var(--bordo);padding:.7rem 0}summary{font-weight:600;cursor:pointer}
@media(max-width:700px){h1{font-size:1.9rem}header nav a.nascondi{display:none}}
"""

# Consenso ai cookie: Google Ads (Consent Mode) parte negato; il tag si carica solo dopo "Accetta" e solo se c'e' l'ID.
_SCRIPT_COOKIE = """
<div id="banner-cookie" role="dialog" aria-label="Cookie">
  <div style="flex:1;min-width:16rem">Usiamo un cookie tecnico per l'accesso. Con il tuo consenso usiamo anche cookie di misurazione
  per capire quali annunci funzionano. <a href="/cookie">Dettagli</a></div>
  <button class="bottone chiaro" id="cookie-no">Rifiuta</button> <button class="bottone" id="cookie-si">Accetta</button>
</div>
<script>
(function(){
  var ID = "__GOOGLE_ADS_ID__", chiave = "br_consenso", banner = document.getElementById("banner-cookie");
  function carica(){
    if (!ID) return;
    window.dataLayer = window.dataLayer || []; function gtag(){dataLayer.push(arguments);} window.gtag = gtag;
    gtag("consent", "default", {ad_storage:"denied", ad_user_data:"denied", ad_personalization:"denied", analytics_storage:"denied"});
    gtag("consent", "update", {ad_storage:"granted", ad_user_data:"granted", ad_personalization:"granted", analytics_storage:"granted"});
    var s = document.createElement("script"); s.async = true; s.src = "https://www.googletagmanager.com/gtag/js?id=" + ID; document.head.appendChild(s);
    gtag("js", new Date()); gtag("config", ID);
  }
  function scegli(v){ try { localStorage.setItem(chiave, v); } catch(e) {} banner.style.display = "none"; if (v === "si") carica(); }
  var scelta = null; try { scelta = localStorage.getItem(chiave); } catch(e) {}
  if (scelta === "si") carica(); else if (scelta !== "no" && ID) banner.style.display = "flex";
  document.getElementById("cookie-si").onclick = function(){ scegli("si"); };
  document.getElementById("cookie-no").onclick = function(){ scegli("no"); };
  var rivedi = document.getElementById("rivedi-cookie");
  if (rivedi) rivedi.onclick = function(e){ e.preventDefault(); try { localStorage.removeItem(chiave); } catch(x) {} banner.style.display = "flex"; };
})();
</script>"""


def pagina(titolo: str, corpo: str, descrizione: str = "", indicizza: bool = False) -> str:
    """La cornice comune: intestazione, piede con i testi legali, banner dei cookie."""
    ads = "".join(c for c in os.environ.get("GOOGLE_ADS_ID", "") if c.isalnum() or c == "-")
    robots = "index, follow" if indicizza else "noindex, nofollow"
    return f"""<!doctype html><html lang="it"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1"><meta name="robots" content="{robots}">
<title>{_e(titolo)}</title><meta name="description" content="{_e(descrizione)}"><style>{STILE}</style></head><body>
<header><a class="logo" href="/">Bandi Radar</a><nav><a class="nascondi" href="/presentazione#come">Come funziona</a>
<a class="nascondi" href="/presentazione#prezzi">Prezzi</a><a href="/accedi">Accedi</a>
<a class="bottone" href="/registrati">Prova gratis</a></nav></header>
{corpo}
<footer><span>© Bandi Radar · finanzagevolata.qiaro.it</span><a href="/termini">Termini</a><a href="/privacy">Privacy</a>
<a href="/cookie">Cookie</a><a href="/condizioni-supporto">Condizioni del supporto</a></footer>
{_SCRIPT_COOKIE.replace("__GOOGLE_ADS_ID__", ads)}</body></html>"""


def _numeri(conn) -> dict:
    with conn.cursor() as cur:
        cur.execute("SELECT count(*) AS n FROM fonti WHERE stato <> 'esclusa'")
        fonti = cur.fetchone()["n"]
        cur.execute("""SELECT count(*) AS n FROM bandi WHERE completezza = 'bando_ufficiale' AND stato IN ('aperto', 'in_arrivo')
                       AND coalesce(preliminare->>'per_imprese', '') <> 'no'""")
        aperti = cur.fetchone()["n"]
    return {"fonti": fonti, "aperti": aperti}


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
                            WHERE completezza = 'bando_ufficiale' AND stato = 'aperto' AND sintesi IS NOT NULL
                              AND contributo_massimo IS NOT NULL AND scadenza > current_date + 21
                              AND coalesce(preliminare->>'per_imprese', '') <> 'no'
                            ORDER BY ente, coalesce(qualita, 3) DESC, contributo_massimo DESC""")
        righe = [dict(r) for r in cur.fetchall()]
    righe.sort(key=lambda r: (-(r["contributo_massimo"] or 0)))
    return righe[:quanti]


def _carta_esempio(b: dict) -> str:
    tipi = "".join(f'<span class="tipo">{_e(t.replace("_", " "))}</span>' for t in (b.get("tipi_agevolazione") or []))
    importo = f"fino a {_euro(b['contributo_massimo'])}" if b.get("contributo_massimo") else ""
    if b.get("percentuale"):
        importo += f" · {float(b['percentuale']):g}% delle spese"
    scadenza = f'<div class="scadenza">scade il {b["scadenza"]:%d/%m/%Y}</div>' if b.get("scadenza") else ""
    sintesi = (b.get("sintesi") or "")[:330] + ("…" if len(b.get("sintesi") or "") > 330 else "")
    return f"""<div class="carta"><div class="piccolo">{_e(b.get('ente'))}</div><h3>{_e(b['titolo'])}</h3>
<div>{tipi} <b>{_e(importo)}</b></div>{scadenza}<p class="piccolo">{_e(sintesi)}</p></div>"""


def presentazione(conn) -> str:
    n = _numeri(conn)
    carte = "".join(_carta_esempio(b) for b in esempi(conn)) or "<p>Gli esempi arrivano presto.</p>"
    p = PREZZI
    corpo = f"""
<section><h1>I bandi giusti per la tua impresa,<br>ogni settimana.</h1>
<p class="sottotitolo">Bandi Radar legge ogni giorno i bandi di Unione europea, Stato, Regioni, Camere di commercio e Comuni,
li riassume in schede chiare e ti segnala solo quelli adatti alla tua impresa. Niente più ore perse tra siti e PDF.</p>
<p><a class="bottone" href="/registrati">Prova gratis</a> &nbsp; <a class="bottone chiaro" href="#come">Come funziona</a></p></section>

<section class="grigia"><div class="griglia">
<div class="carta"><div class="etichetta">Fonti controllate</div><div class="numero">{n['fonti']}</div><div class="piccolo">siti di enti pubblici, ogni giorno</div></div>
<div class="carta"><div class="etichetta">Bandi aperti ora</div><div class="numero">{n['aperti']}</div><div class="piccolo">con la scheda fatta sul testo ufficiale</div></div>
<div class="carta"><div class="etichetta">Email</div><div class="numero">1 a settimana</div><div class="piccolo">solo i bandi nuovi adatti a te</div></div>
</div></section>

<section id="come"><h2>Come funziona</h2><div class="griglia">
<div class="carta"><h3>1. Descrivi la tua impresa</h3><p>Dove hai le sedi, cosa fai (codice ATECO), quanto sei grande. Bastano pochi minuti.
I dati servono solo a scegliere i bandi.</p></div>
<div class="carta"><h3>2. Vedi i bandi adatti</h3><p>Per ogni bando una scheda chiara: a chi si rivolge, quanto dà, cosa finanzia, entro quando.
Ti diciamo anche cosa resta da verificare.</p></div>
<div class="carta"><h3>3. Ricevi le novità</h3><p>Ogni settimana un'email con i bandi nuovi o in scadenza per la tua impresa. Mai due volte lo stesso.</p></div>
<div class="carta"><h3>4. Se vuoi, ti aiutiamo</h3><p>Con un clic chiedi il supporto dei nostri consulenti per la domanda. Si paga solo se il
contributo arriva.</p></div>
</div></section>

<section class="grigia"><h2>Esempi di schede</h2><div class="griglia">{carte}</div>
<p class="piccolo">Le schede sono indicative: prima di presentare la domanda va sempre letto il bando ufficiale.</p></section>

<section id="prezzi"><h2>Prezzi</h2><div class="griglia">
<div class="carta"><div class="etichetta">Mensile</div><div class="prezzo">{p['mensile']} € <small>/ mese</small></div>
<ul class="spunte"><li>bandi adatti alla tua impresa</li><li>schede chiare e aggiornate</li><li>email settimanale</li><li>disdici quando vuoi</li></ul>
<a class="bottone chiaro" href="/registrati">Prova gratis</a></div>
<div class="carta evidenza"><div class="etichetta">Annuale</div><div class="prezzo">{p['annuale']} € <small>/ mese</small></div>
<ul class="spunte"><li>tutto quello del mensile</li><li>pagato mese per mese</li><li>impegno di 12 mesi</li></ul>
<a class="bottone" href="/registrati">Prova gratis</a></div>
<div class="carta"><div class="etichetta">In più</div><ul class="spunte"><li>altra impresa: {p['impresa_in_piu']} € / mese</li>
<li>altra sede della stessa impresa: {p['sede_in_piu']} € / mese</li></ul>
<p class="piccolo">Supporto per la domanda a successo: una percentuale del contributo ottenuto, solo se arriva
(<a href="/condizioni-supporto">condizioni</a>).</p></div>
</div><p class="piccolo">[PREZZI IVA ESCLUSA O INCLUSA, DURATA DELLA PROVA GRATUITA: DA DECIDERE]</p></section>

<section class="grigia"><h2>Domande frequenti</h2>
<details><summary>Da dove arrivano i bandi?</summary><p>Da {n['fonti']} siti pubblici: Unione europea, ministeri e agenzie nazionali, Regioni,
Camere di commercio, Comuni capoluogo. Li controlliamo con regolarità e rispettando le regole dei siti.</p></details>
<details><summary>Le schede sono affidabili?</summary><p>Ogni scheda è fatta sul testo ufficiale del bando e controllata da regole automatiche
e da revisori esperti. Resta un'informazione indicativa: la domanda va sempre preparata sul bando ufficiale.</p></details>
<details><summary>Che fine fanno i dati della mia impresa?</summary><p>Servono solo a scegliere i bandi. Il nome dell'impresa è tenuto separato dal
profilo e non viene mai mandato a servizi esterni, nemmeno all'intelligenza artificiale (<a href="/privacy">informativa</a>).</p></details>
<details><summary>Posso disdire?</summary><p>Il mensile si disdice quando vuoi; l'annuale ha un impegno di 12 mesi pagati mese per mese.</p></details>
</section>

<section><h2>Inizia adesso</h2><p class="sottotitolo">Descrivi la tua impresa e guarda subito quanti bandi aperti fanno per te.</p>
<p><a class="bottone" href="/registrati">Prova gratis</a></p></section>"""
    return pagina("Bandi Radar - i bandi giusti per la tua impresa", corpo,
                  "Bandi e contributi per le imprese italiane: schede chiare e solo i bandi adatti alla tua impresa, ogni settimana.",
                  indicizza=pubblica())


def legale(nome: str) -> str | None:
    if nome not in LEGALI:
        return None
    file, titolo = LEGALI[nome]
    percorso = TESTI / file
    testo = percorso.read_text(encoding="utf-8") if percorso.is_file() else f"<h1>{_e(titolo)}</h1><p>Testo in preparazione.</p>"
    return pagina(f"{titolo} - Bandi Radar", f'<section class="testo-legale">{testo}</section>', titolo, indicizza=pubblica())
