"""Pagina di atterraggio (landing) per chi arriva da Google, dagli annunci e dai motori di risposta IA (07/10/2026).

Una sola pagina HTML leggera (niente React, niente font esterni, niente immagini pesanti): promessa, come funziona
in 3 passi, cosa trovi con i numeri veri presi dal database, i numeri delle agevolazioni in Italia, bandi aperti
regione per regione, prezzi,
chi c'e' dietro, domande frequenti, invito a provare. I numeri si calcolano al volo e restano in memoria per
CACHE_SECONDI: la pagina resta veloce anche con molte visite dagli annunci.

Le domande frequenti sono scritte UNA volta (FAQ) e finiscono sia nella pagina sia nei dati strutturati FAQPage e in
/llms.txt: il testo che leggono Google e i motori IA e' lo stesso che vede la persona.
"""

from __future__ import annotations

import logging
import os
import threading
import time
from datetime import date

from app.pubblico import seo, vetrina

log = logging.getLogger(__name__)
CACHE_SECONDI = 900
CACHE_PAGINA = 120          # la pagina intera, gia' scritta (09/10): da 1,1 s a pochi millisecondi
# Variabili del .env che cambiano la pagina: se ne cambia una, la pagina in memoria non vale piu'.
_VARIABILI_PAGINA = ("PAGINA_PUBBLICA", "BLOG_PUBBLICO", "SITO_URL", "TITOLARE_SITO", "ESEMPI_BANDI", "GOOGLE_ADS_ID",
                     "GOOGLE_ANALYTICS_ID", "GOOGLE_SITE_VERIFICATION", "BING_SITE_VERIFICATION", "EMAIL_CONTATTO",
                     "PROFILI_SOCIAL", "PROVA_GIORNI")
_cache: dict = {}           # "dati"/"scade": numeri; "esempi": schede d'esempio; "pagina": l'HTML pronto
_ricalcolo = threading.Lock()

# Prezzi dell'abbonamento (decisione di Matteo del 10/10/2026, come Termini e Stripe): mensile 30 euro al mese,
# annuale 20 euro al mese (240 euro l'anno in 12 rate). IVA esclusa. PREZZO_LANCIO resta il prezzo piu' basso.
PREZZO_MENSILE = 30
PREZZO_LANCIO = 20
# Numeri delle agevolazioni in Italia (fonti ufficiali, verificate il 10/10/2026), mostrati nella landing.
MERCATO = [
    ("17,2 miliardi", "di euro di agevolazioni concesse alle imprese nel 2024",
     "MIMIT, Relazione sugli interventi di sostegno 2025",
     "https://www.mimit.gov.it/images/stories/documenti/RELAZIONE_266_2025.pdf"),
    ("1,24 milioni", "di domande di agevolazione approvate nel 2024",
     "MIMIT, Relazione sugli interventi di sostegno 2025",
     "https://www.mimit.gov.it/images/stories/documenti/RELAZIONE_266_2025.pdf"),
    ("2.374", "misure di aiuto attive, di cui 2.074 regionali: ogni ente pubblica le sue, ognuna con le sue regole",
     "MIMIT, Relazione sugli interventi di sostegno 2025",
     "https://www.mimit.gov.it/images/stories/documenti/RELAZIONE_266_2025.pdf"),
    ("3,5%", "delle imprese con almeno 3 addetti indica gli incentivi pubblici tra le sue fonti di finanziamento",
     "ISTAT, Censimento permanente delle imprese 2023",
     "https://www.istat.it/it/files/2023/11/REPORTCensimprese.pdf"),
]
TIPI_FONTE = [("regione", "Regioni e Province autonome"), ("nazionale", "Ministeri e agenzie nazionali"),
              ("ue", "Unione europea"), ("camera", "Camere di commercio"), ("capoluogo", "Comuni capoluogo"),
              ("provincia", "Province")]
# Sottotitolo del primo schermo, testo di Matteo (08/10/2026); {fonti} = numero dei siti controllati.
SOTTOTITOLO = ("Teniamo d'occhio {fonti} siti di Unione Europea, Ministeri, Regioni, Camere di Commercio e Comuni. "
               "Ogni bando viene esaminato e riorganizzato in modo chiaro e semplice e ti segnaliamo quelli che fanno al "
               "caso della tua impresa. Se vuoi, poi, un consulente ti aiuta con la predisposizione e la presentazione "
               "della domanda.")
NOMI_TIPI = {"fondo_perduto": "fondo perduto", "finanziamento_agevolato": "finanziamento agevolato", "voucher": "voucher",
             "garanzia": "garanzia", "credito_imposta": "credito d'imposta", "premio": "premio", "servizi": "servizi"}


def _n(x) -> str:
    """Numero all'italiana: 4.517."""
    return f"{int(x or 0):,}".replace(",", ".")


def _calcola(conn) -> dict:
    from app.abbinamento.territorio import NOMI_REGIONI
    from app import misure

    with conn.cursor() as cur:
        cur.execute("SELECT tipo, count(*) AS n FROM fonti WHERE stato = 'attiva' AND NOT in_pausa GROUP BY tipo")
        per_tipo = {r["tipo"]: r["n"] for r in cur.fetchall()}
        # Conteggi solo dalla situazione dei bandi (regola in CLAUDE.md): proponibile = scheda sul bando ufficiale,
        # senza problemi gravi, non chiuso.
        cur.execute("""SELECT count(*) FILTER (WHERE s.situazione <> 'unito') AS esaminati,
                              count(*) FILTER (WHERE s.situazione = 'proponibile') AS proponibili,
                              count(*) FILTER (WHERE s.situazione = 'proponibile'
                                               AND b.vincoli->>'territorio' = 'nessun_vincolo') AS tutta_italia
                       FROM bandi_situazione s JOIN bandi b USING (id)""")
        conti = dict(cur.fetchone())
        cur.execute("""SELECT r, count(*) AS n FROM bandi_situazione s JOIN bandi b USING (id), unnest(b.territorio_regioni) r
                       WHERE s.situazione = 'proponibile' GROUP BY r ORDER BY n DESC, r""")
        regioni = [(r["r"], NOMI_REGIONI.get(r["r"], r["r"]), r["n"]) for r in cur.fetchall() if r["r"] in NOMI_REGIONI]
        cur.execute("""SELECT t, count(*) AS n FROM bandi_situazione s JOIN bandi b USING (id), unnest(b.tipi_agevolazione) t
                       WHERE s.situazione = 'proponibile' GROUP BY t ORDER BY n DESC""")
        tipi = [(NOMI_TIPI[r["t"]], r["n"]) for r in cur.fetchall() if r["t"] in NOMI_TIPI]
    aperte = [m for m in misure.tutte() if m.get("stato") == "aperto"]
    return {"fonti": sum(per_tipo.values()), "fonti_per_tipo": per_tipo, **conti, "regioni": regioni, "tipi": tipi,
            "misure": len(aperte), "nomi_misure": [m["nome"].split("(")[0].strip() for m in aperte],
            "aggiornato": date.today()}


def _ricalcola_in_disparte() -> None:
    """Ricalcola i numeri in un filo a parte, con una connessione sua: chi visita intanto vede quelli di prima."""
    if not _ricalcolo.acquire(blocking=False):          # un ricalcolo alla volta
        return

    def lavoro():
        try:
            from app.db.connessione import connetti

            with connetti() as conn:
                dati = _calcola(conn)
            _cache.update(dati=dati, scade=time.monotonic() + CACHE_SECONDI)
        except Exception:  # noqa: BLE001 - restano i numeri di prima
            log.exception("numeri della pagina pubblica non ricalcolati")
        finally:
            _ricalcolo.release()
    threading.Thread(target=lavoro, name="numeri-landing", daemon=True).start()


def numeri(conn) -> dict | None:
    """I numeri della pagina, tenuti in memoria CACHE_SECONDI. Calcolarli costa circa un secondo (09/10): quando
    scadono la pagina usa ancora quelli di prima e li ricalcola in disparte, cosi' nessun visitatore aspetta; si
    aspetta solo la prima volta dopo un riavvio. Se il database non risponde: None (la pagina si mostra lo stesso,
    senza numeri)."""
    adesso = time.monotonic()
    if _cache.get("scade", 0) > adesso:
        return _cache["dati"]
    if _cache.get("dati"):
        _ricalcola_in_disparte()
        return _cache["dati"]
    try:
        dati = _calcola(conn)
    except Exception:  # noqa: BLE001 - la pagina pubblica non deve mai cadere per i numeri
        log.exception("numeri della pagina pubblica non calcolati")
        conn.rollback()
        return _cache.get("dati")
    _cache.update(dati=dati, scade=adesso + CACHE_SECONDI)
    return dati


def descrizione_breve(n: dict | None) -> str:
    fonti = f"{_n(n['fonti'])} siti pubblici" if n else "centinaia di siti pubblici"
    return (f"bandinQiaro controlla con regolarità {fonti} (Unione europea, ministeri, Regioni, Camere di commercio, Comuni), "
            "trasforma i bandi per imprese in schede chiare e segnala ogni settimana solo quelli adatti alla tua impresa. "
            "Un commercialista può aiutarti a presentare la domanda.")


def faq(n: dict | None, giorni_prova: int) -> list[tuple[str, str]]:
    """Domande frequenti: testo semplice (senza HTML), uguale nella pagina, nel JSON-LD e in /llms.txt."""
    from app.pubblico import PREZZI

    fonti = _n(n["fonti"]) if n else "centinaia di"
    aperti = f" Oggi ({n['aggiornato']:%d/%m/%Y}) ci sono {_n(n['proponibili'])} bandi aperti da visionare." if n else ""
    misure = (", ".join(n["nomi_misure"][:4]) + " e altre") if n and n["nomi_misure"] else "Conto Termico, Iperammortamento, Nuova Sabatini e altre"
    return [
        ("Che cos'è bandinQiaro?",
         "È un servizio in abbonamento per imprese e professionisti che raccoglie i bandi di finanza agevolata "
         "(contributi a fondo perduto, finanziamenti agevolati, voucher, garanzie, crediti d'imposta) pubblicati da Unione "
         "europea, Stato, Regioni, Camere di commercio e Comuni capoluogo, li riassume in schede chiare e segnala a ogni "
         "impresa solo quelli adatti al suo profilo, con un'email ogni settimana." + aperti),
        ("Quali bandi controllate e ogni quanto?",
         f"Controlliamo {fonti} siti pubblici: Regioni e Province autonome, ministeri e agenzie nazionali (Invitalia, "
         "MIMIT, GSE, INAIL...), Unione europea, Camere di commercio e Comuni capoluogo. Ogni sito è letto con la frequenza "
         "adatta, da una volta al giorno a una volta al mese, rispettando le regole dei siti. Ogni bando nuovo diventa una "
         "scheda fatta sul testo ufficiale."),
        ("Quanto costa?",
         f"L'abbonamento mensile costa {PREZZO_MENSILE} euro al mese più IVA e si rinnova ogni mese finché non lo disdici; "
         f"con l'abbonamento annuale costa {PREZZO_LANCIO} euro al mese più IVA ({PREZZO_LANCIO * 12} euro l'anno, in 12 rate "
         f"mensili). Prima c'è una prova gratuita di {giorni_prova} giorni senza carta di credito. Ogni impresa in più costa "
         f"{PREZZI['impresa_in_piu']} euro al mese e ogni sede in più della stessa impresa {PREZZI['sede_in_piu']} euro al "
         "mese (IVA esclusa)."),
        ("Come scegliete i bandi adatti alla mia impresa?",
         "Descrivi la tua impresa con un modulo guidato: sedi, attività (codice ATECO), dimensione, forma giuridica e "
         "spese che hai in programma. Il sistema confronta il profilo con i requisiti di ogni bando (territorio, settore, "
         "dimensione, tipo di beneficiario) e ti mostra i bandi compatibili e quelli da verificare, con il motivo."),
        ("Le schede dei bandi sono affidabili?",
         "Ogni scheda è scritta sul testo ufficiale del bando, con l'aiuto dell'intelligenza artificiale, e passa da controlli "
         "automatici: le schede con errori gravi non vengono proposte finché non sono corrette. Restano informazioni "
         "indicative: prima di presentare la domanda va sempre letto il bando ufficiale, che trovi collegato in ogni scheda."),
        ("Mi aiutate a presentare la domanda? Quanto costa?",
         "Sì: da ogni scheda puoi chiedere una chiamata per valutare il bando e il supporto di un esperto per la domanda. "
         "Per gli abbonati la preparazione e l'invio della domanda sono compresi nell'abbonamento, se resta attivo fino "
         "all'esito della domanda: si paga solo un compenso se la domanda è accolta. Sui contributi a fondo perduto il 12% fino a 50.000 euro, il 10% da 50.000 a 150.000 "
         "euro e l'8% oltre; sui finanziamenti agevolati dall'1% allo 0,5% secondo l'importo; sui crediti d'imposta il 6%. "
         "Per chi non è abbonato la pratica costa da 100 a 300 euro, più lo stesso compenso a successo. Importi IVA "
         "esclusa; le condizioni complete sono nella pagina Condizioni del supporto."),
        ("Che differenza c'è tra un bando e una misura nazionale?",
         "Un bando ha requisiti, una dotazione e di solito una scadenza. Le misure nazionali (" + misure + ") sono "
         "agevolazioni sempre aperte o a sportello che spesso si possono sommare a un bando per lo stesso investimento: "
         "bandinQiaro le indica nella scheda del bando quando le spese coincidono."),
        ("Che fine fanno i dati della mia impresa?",
         "Servono solo a scegliere i bandi. Il nome dell'impresa è tenuto separato dal profilo e non viene mai mandato a "
         "servizi esterni, nemmeno all'intelligenza artificiale. Puoi scaricare i tuoi dati o cancellare l'account in "
         "qualsiasi momento."),
        ("Cosa succede alla fine della prova gratuita?",
         "Niente di automatico: non chiediamo la carta all'inizio, quindi alla fine della prova non parte nessun addebito. "
         "Se il servizio ti è utile scegli tu di abbonarti."),
    ]


def _carta_esempio(b: dict) -> str:
    from app.pubblico import _e, _euro

    tipi = "".join(f'<span class="tipo">{_e(t.replace("_", " "))}</span>' for t in (b.get("tipi_agevolazione") or [])[:2])
    importo = f"fino a {_euro(b['contributo_massimo'])}" if b.get("contributo_massimo") else ""
    if b.get("percentuale"):
        importo += f" · {float(b['percentuale']):g}% delle spese"
    scadenza = f'<span class="scadenza">scade il {b["scadenza"]:%d/%m/%Y}</span>' if b.get("scadenza") else ""
    sintesi = (b.get("sintesi") or "")[:220] + ("…" if len(b.get("sintesi") or "") > 220 else "")
    return f"""<article class="carta scheda"><div class="piccolo">{_e(b.get('ente'))}</div><h3>{_e(b['titolo'])}</h3>
<div class="riga-tipi">{tipi}<b>{_e(importo)}</b></div><p class="piccolo">{_e(sintesi)}</p>
<div class="piede-scheda">{scadenza}<span class="adatto">✓ compatibile con il tuo profilo</span></div></article>"""


def _chi_siamo() -> str:
    from app.pubblico import TESTI

    f = TESTI / "chi_siamo.html"
    return f.read_text(encoding="utf-8") if f.is_file() else ""


def _numeri_html(n: dict | None) -> str:
    if not n:
        return ""
    voci = [(_n(n["fonti"]), "siti pubblici controllati", "UE, ministeri, Regioni, Camere, Comuni"),
            (_n(n["proponibili"]), "bandi aperti da visionare", "aperti o in arrivo, aggiornati ogni giorno"),
            (_n(n["esaminati"]), "bandi e avvisi esaminati", "anche i chiusi, per non perderne nessuno"),
            (_n(n["misure"]), "misure nazionali", "da sommare ai bandi (crediti d'imposta e simili)")]
    celle = "".join(f'<div class="cifra"><b>{a}</b><span>{b}</span><small>{c}</small></div>' for a, b, c in voci)
    return (f'<section class="numeri" aria-label="bandinQiaro in numeri"><div class="contenitore"><div class="cifre">{celle}</div>'
            f'<p class="aggiornato">Dati aggiornati al {n["aggiornato"]:%d/%m/%Y}, dal nostro archivio.</p></div></section>')


def _regioni_html(n: dict | None) -> str:
    if not n or not n["regioni"]:
        return ""
    from app.pubblico.regioni import slug

    voci = "".join(f'<li><a href="/bandi-aperti/{slug(nome)}"><span>{nome}</span><b>{num}</b></a></li>'
                   for _, nome, num in sorted(n["regioni"], key=lambda r: r[1]))
    tipi = ", ".join(f"{nome} {_n(num)}" for nome, num in n["tipi"][:5])
    return f"""<section id="regioni" class="grigia"><div class="contenitore">
<h2>Bandi aperti oggi, regione per regione</h2>
<p class="sottotitolo">Al {n['aggiornato']:%d/%m/%Y} ci sono <b>{_n(n['proponibili'])} bandi aperti da visionare</b>,
di cui <b>{_n(n['tutta_italia'])} validi in tutta Italia</b> (nazionali ed europei). Per tipo di agevolazione: {tipi}.</p>
<ul class="regioni">{voci}</ul>
<p class="piccolo">Un bando può valere per più regioni. I numeri cambiano ogni giorno: bandi nuovi, proroghe, chiusure.</p>
<p><a class="bottone" href="/registrati">Scopri quali fanno per la tua impresa</a></p></div></section>"""


def _mercato_html() -> str:
    """I numeri delle agevolazioni in Italia (MERCATO), con la fonte ufficiale di ognuno."""
    from app.pubblico import _e

    celle = "".join(f'<div class="carta"><div class="numero">{_e(cifra)}</div><p>{_e(testo)}</p>'
                    f'<p class="piccolo">Fonte: <a href="{_e(url)}" rel="noopener" target="_blank">{_e(fonte)}</a></p></div>'
                    for cifra, testo, fonte, url in MERCATO)
    return f"""<section id="mercato"><div class="contenitore"><h2>Le agevolazioni ci sono, ma poche imprese le usano</h2>
<p class="sottotitolo">Ogni anno lo Stato e le Regioni concedono miliardi alle imprese, ma le regole sono sparse su migliaia di
misure diverse. bandinQiaro le legge tutte e ti mostra solo quelle che fanno per te.</p>
<div class="griglia">{celle}</div></div></section>"""


def _prezzo_html(giorni: int) -> str:
    from app.pubblico import PREZZI

    return f"""<section id="prezzo"><div class="contenitore"><h2>Un prezzo semplice</h2><div class="due">
<div class="carta evidenza"><div class="etichetta">Abbonamento annuale</div>
<div class="prezzo">{PREZZO_LANCIO} € <small>al mese + IVA</small></div>
<p class="piccolo">{PREZZO_LANCIO * 12} € l'anno, in 12 rate mensili. Con l'abbonamento mensile: <b>{PREZZO_MENSILE} € al mese + IVA</b>, disdici quando vuoi.</p>
<ul class="spunte"><li>solo i bandi adatti alla tua impresa, non tutti quelli che escono</li><li>email ogni lunedì con le novità e le scadenze</li>
<li>misure nazionali da sommare ai bandi</li><li>chiamata con un esperto per valutare un bando</li>
<li><b>preparazione e invio della domanda compresi</b>: paghi solo se viene accolta</li></ul>
<a class="bottone grande" href="/registrati">Prova gratis {giorni} giorni</a>
<p class="piccolo">Senza carta di credito. Impresa in più {PREZZI['impresa_in_piu']} € al mese, sede in più {PREZZI['sede_in_piu']} € al mese (IVA esclusa).</p></div>
<div class="carta"><div class="etichetta">Supporto alla domanda, a successo</div>
<p>Se un bando fa per te, un esperto prepara e segue la domanda. Per gli abbonati la pratica è compresa: il compenso si paga solo se la domanda è accolta.</p>
<table class="tariffe"><tr><th>Agevolazione</th><th>Compenso</th></tr>
<tr><td>Fondo perduto</td><td>12% fino a 50.000 €, 10% fino a 150.000 €, 8% oltre</td></tr>
<tr><td>Finanziamento agevolato</td><td>dall'1% allo 0,5% secondo l'importo</td></tr>
<tr><td>Credito d'imposta</td><td>6%</td></tr></table>
<p class="piccolo">Minimo 300 € a pratica accolta. Per chi non è abbonato la pratica costa da 100 a 300 €. IVA esclusa.
<a href="/condizioni-supporto">Condizioni complete</a>.</p></div></div></div></section>"""


def _firma_pagina() -> tuple:
    """Cosa rende valida la pagina in memoria: il giorno, il file della vetrina e le variabili che la cambiano."""
    return (date.today(), vetrina.FILE.stat().st_mtime if vetrina.FILE.is_file() else 0,
            tuple(os.environ.get(k, "") for k in _VARIABILI_PAGINA))


def da_cache() -> str | None:
    """La pagina gia' pronta, se e' in memoria e valida: chi la chiede non apre nemmeno la connessione al database."""
    p = _cache.get("pagina")
    if p and p[0] > time.monotonic() and p[1] == _firma_pagina():
        return p[2]
    return None


def _esempi(conn) -> list[dict]:
    """Le schede d'esempio, in memoria come i numeri (la query costa circa 50 ms)."""
    from app.pubblico import esempi

    e = _cache.get("esempi")
    if e and e[0] > time.monotonic() and e[1] == os.environ.get("ESEMPI_BANDI", ""):
        return e[2]
    voci = esempi(conn, 6)
    _cache["esempi"] = (time.monotonic() + CACHE_SECONDI, os.environ.get("ESEMPI_BANDI", ""), voci)
    return voci


def presentazione(conn) -> str:
    """La pagina di presentazione. Resta in memoria CACHE_PAGINA secondi (vedi da_cache)."""
    pronta = da_cache()
    if pronta:
        return pronta
    firma = _firma_pagina()
    testo = _componi(conn)
    if _cache.get("dati"):                              # senza numeri (database giu') non si tiene: si riprova subito
        _cache["pagina"] = (time.monotonic() + CACHE_PAGINA, firma, testo)
    return testo


def _componi(conn) -> str:
    from app.abbonamenti import giorni_prova
    from app.pubblico import _e, pagina, pubblica

    n = numeri(conn)
    giorni = giorni_prova()
    domande = faq(n, giorni)
    in_vetrina = vetrina.scegli(conn)                   # in alto i bandi in vetrina (app/pubblico/vetrina.yaml)
    gia = {v["id"] for v in in_vetrina if v["tipo"] == "bando"}
    try:
        schede = [_carta_esempio(b) for b in _esempi(conn) if b["id"] not in gia][:3]
    except Exception:  # noqa: BLE001
        log.exception("esempi della pagina pubblica non letti")
        conn.rollback()
        schede = []
    fonti = _n(n["fonti"]) if n else "centinaia di"
    if in_vetrina:
        prima, carte = vetrina.html(in_vetrina), "".join(schede)
    else:                                               # senza vetrina: in alto la prima scheda d'esempio
        prima, carte = (schede[0] if schede else ""), "".join(schede[1:] if len(schede) > 1 else schede)
    tipi_fonte = ""
    if n:
        tipi_fonte = "".join(f"<li><b>{_n(n['fonti_per_tipo'].get(k, 0))}</b> {nome}</li>"
                             for k, nome in TIPI_FONTE if n["fonti_per_tipo"].get(k))
    faq_html = "".join(f"<details><summary>{_e(d)}</summary><p>{_e(r)}</p></details>" for d, r in domande)
    bozza = "" if pubblica() else ('<p class="bozza contenitore">Anteprima: la pagina non è ancora pubblica né indicizzata '
                                   '(PAGINA_PUBBLICA=0). Testi da confermare con Matteo.</p>')
    corpo = f"""{bozza}
<section class="eroe"><div class="contenitore due">
<div><p class="occhiello">Bandi per imprese · contributi a fondo perduto · finanziamenti agevolati</p>
<h1>I bandi giusti per la tua impresa, <span>ogni settimana nella tua email</span></h1>
<p class="sottotitolo">{_e(SOTTOTITOLO.format(fonti=fonti))}</p>
<p class="azioni"><a class="bottone grande" href="/registrati">Prova gratis {giorni} giorni</a>
<a class="bottone chiaro grande" href="#come">Come funziona</a></p>
<p class="rassicura">Senza carta di credito · da {PREZZO_LANCIO} € al mese + IVA dopo la prova · Il nome della tua impresa non va mai all'intelligenza artificiale</p></div>
<div class="anteprima"{'' if in_vetrina else ' aria-hidden="true"'}>{prima}</div>
</div></section>
{_numeri_html(n)}
<section id="come"><div class="contenitore"><h2>Come funziona, in 3 passi</h2><ol class="passi">
<li><b>Descrivi la tua impresa</b><span>Sedi, attività (codice ATECO), dimensione e spese in programma. Bastano pochi minuti; il nome dell'impresa non serve a scegliere i bandi.</span></li>
<li><b>Vedi subito i bandi adatti</b><span>Per ogni bando una scheda chiara: a chi si rivolge, quanto dà, cosa finanzia, entro quando, cosa resta da verificare e il link al bando ufficiale.</span></li>
<li><b>Ricevi le novità ogni lunedì</b><span>Un'email con i bandi nuovi e quelli in scadenza per la tua impresa, mai due volte lo stesso. Se un bando ti interessa, chiedi supporto con un clic.</span></li>
</ol></div></section>
<section id="cosa" class="grigia"><div class="contenitore"><h2>Cosa trovi in bandinQiaro</h2><div class="griglia">
<div class="carta"><h3>Tutte le fonti, in un posto</h3><p>Non devi più girare tra siti e PDF: leggiamo noi gli enti che pubblicano bandi per le imprese.</p>
<ul class="fonti">{tipi_fonte}</ul></div>
<div class="carta"><h3>Schede chiare sul testo ufficiale</h3><p>Beneficiari, territorio, spese ammesse, importi, percentuali, scadenze e modalità di domanda, in italiano semplice. Le schede con errori gravi non vengono proposte.</p></div>
<div class="carta"><h3>Solo i bandi adatti a te</h3><p>Ogni bando è confrontato con il profilo della tua impresa: vedi i compatibili e quelli da verificare, con il motivo.</p></div>
<div class="carta"><h3>Misure nazionali da sommare</h3><p>Conto Termico, Iperammortamento, Nuova Sabatini, crediti d'imposta: ti diciamo quando si possono aggiungere a un bando per lo stesso investimento.</p></div>
</div>{f'<h3 class="titoletto">Esempi di schede di questi giorni</h3><div class="griglia">{carte}</div><p class="piccolo">Schede indicative: prima della domanda va sempre letto il bando ufficiale.</p>' if carte else ''}
</div></section>
{_mercato_html()}
{_regioni_html(n)}
{_prezzo_html(giorni)}
<section id="chi" class="grigia"><div class="contenitore stretto">{_chi_siamo()}</div></section>
<section id="domande"><div class="contenitore stretto"><h2>Domande frequenti</h2>{faq_html}</div></section>
<section class="finale"><div class="contenitore"><h2>Scopri quanti bandi aperti fanno per la tua impresa</h2>
<p>Descrivi la tua impresa e guarda subito l'elenco. {giorni} giorni gratis, senza carta.</p>
<p><a class="bottone grande bianco" href="/registrati">Inizia la prova gratuita</a></p></div></section>"""
    descrizione = descrizione_breve(n)
    jsonld = seo.json_ld([seo.organizzazione(descrizione), seo.sito_web(),
                          seo.servizio(descrizione, PREZZO_LANCIO, giorni), seo.domande_frequenti(domande)])
    return pagina("Bandi per imprese e contributi a fondo perduto | bandinQiaro", corpo,
                  "Bandi e contributi a fondo perduto per imprese da UE, Stato, Regioni e Camere di commercio: "
                  "schede chiare e solo i bandi adatti a te, ogni settimana. Prova gratis.",
                  indicizza=pubblica(), percorso="/", testa=jsonld)


def llms_txt(conn) -> str:
    """/llms.txt (proposta llmstxt.org): chi siamo, cosa facciamo, numeri datati e le pagine utili, in Markdown."""
    from app.abbonamenti import giorni_prova

    n = numeri(conn)
    giorni = giorni_prova()
    righe = [f"# {seo.NOME}", "", f"> {descrizione_breve(n)}", "",
             "Servizio italiano in abbonamento per imprese, PMI, professionisti e startup. Lingua: italiano. "
             "Copertura: tutta Italia (bandi europei, nazionali, regionali, delle Camere di commercio e dei Comuni capoluogo).", ""]
    if n:
        righe += [f"## Numeri al {n['aggiornato']:%d/%m/%Y}", "",
                  f"- Siti pubblici controllati: {_n(n['fonti'])}",
                  f"- Bandi aperti da visionare: {_n(n['proponibili'])} (di cui {_n(n['tutta_italia'])} validi in tutta Italia)",
                  f"- Bandi e avvisi esaminati dall'inizio: {_n(n['esaminati'])}",
                  f"- Misure nazionali sempre aperte seguite: {_n(n['misure'])}", ""]
        if n["regioni"]:
            righe += ["Bandi aperti per regione: " + "; ".join(f"{nome} {num}" for _, nome, num in n["regioni"]) + ".", ""]
    righe += ["## Le agevolazioni per imprese in Italia", ""]
    righe += [f"- {cifra} {testo} (fonte: [{fonte}]({url}))" for cifra, testo, fonte, url in MERCATO] + [""]
    righe += ["## Domande frequenti", ""]
    for d, r in faq(n, giorni):
        righe += [f"### {d}", "", r, ""]
    righe += ["## Pagine", "",
              f"- [Presentazione del servizio]({seo.assoluto('/')}): come funziona, prezzo, domande frequenti",
              f"- [Condizioni del supporto alla domanda]({seo.assoluto('/condizioni-supporto')}): compensi a successo",
              f"- [Termini e condizioni]({seo.assoluto('/termini')})",
              f"- [Informativa privacy]({seo.assoluto('/privacy')})", ""]
    try:                                                    # articoli del blog pubblicati (app/pubblico/blog.py)
        from app.pubblico import blog

        from app.pubblico import regioni

        righe += blog.righe_llms(conn) + regioni.righe_llms(conn)
    except Exception:  # noqa: BLE001 - /llms.txt non deve cadere per il blog
        log.exception("articoli del blog o pagine delle regioni non letti per /llms.txt")
        conn.rollback()
    righe += ["## Optional", "",
              f"- [Registrazione e prova gratuita]({seo.assoluto('/registrati')})", ""]
    return "\n".join(righe)
