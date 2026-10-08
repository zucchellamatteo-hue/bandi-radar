"""Blog pubblico (07/10/2026): /blog (elenco) e /blog/<slug> (articolo), HTML leggero nello stile della landing.

Solo gli articoli pubblicati sono visibili e finiscono in sitemap.xml e /llms.txt; si indicizzano con
PAGINA_PUBBLICA=1 (tutto aperto) oppure con BLOG_PUBBLICO=1 (08/10: solo il blog aperto, landing ancora chiusa; in quel
caso /llms.txt descrive solo il blog, vedi llms_txt_blog). Ogni articolo mostra in testa "Aggiornato il", il riquadro "Bando chiuso" se il
bando collegato e' chiuso o scaduto (app/articoli.situazione_collegata), in fondo le fonti ufficiali e l'invito a
registrarsi. Dati strutturati: Article, FAQPage (se c'e' la sezione "Domande frequenti") e BreadcrumbList.
"""

from __future__ import annotations

from datetime import datetime, timezone

from app import articoli
from app.pubblico import seo

PAROLE_AL_MINUTO = 200

STILE_BLOG = """<style>
.tabella{overflow-x:auto;margin:1em 0}
.tabella table{border-collapse:collapse;width:100%;font-size:.95em}
.tabella th,.tabella td{border:1px solid #d5e1f0;padding:.45em .6em;text-align:left;vertical-align:top}
.tabella th{background:#eef4fb}
.blog-testa{padding-bottom:1rem}.blog-testa h1{font-size:2.2rem}
.briciole{font-size:.9rem;color:var(--grigio);margin:0 0 .4rem}.briciole a{color:var(--grigio)}
.dati-articolo{color:var(--grigio);font-size:.92rem;margin:.2rem 0 1rem}
.articolo{padding-top:0}.articolo h2{font-size:1.45rem;margin:2rem 0 .7rem}.articolo h3{font-size:1.1rem;margin:1.3rem 0 .3rem}
.articolo p,.articolo li{max-width:44rem}.articolo li{margin:.25rem 0}
.chiuso{background:#fdecea;border-left:5px solid #b0392f;border-radius:8px;padding:.9rem 1.1rem;margin:1rem 0}
.chiuso b{color:#b0392f}.invito{background:var(--sfondo);border:1px solid var(--bordo);border-radius:14px;padding:1.3rem 1.4rem;margin:2.2rem 0 1rem}
.invito h2{margin-top:0!important}.etichetta-chiuso{display:inline-block;background:#fdecea;color:#b0392f;border-radius:4px;padding:.05rem .45rem;font-size:.78rem;font-weight:650}
.elenco-articoli .carta h2{font-size:1.15rem;margin:.2rem 0 .4rem}.elenco-articoli .carta h2 a{text-decoration:none;color:var(--blu)}
.elenco-articoli .carta p{margin:.3rem 0}
@media(max-width:700px){.blog-testa h1{font-size:1.7rem}.articolo h2{font-size:1.25rem}}
</style>"""


def _data(x) -> str:
    return f"{x:%d/%m/%Y}" if x else ""


def _iso(x) -> str | None:
    return x.isoformat() if x else None


def _riquadro_chiuso(chiuso: dict | None) -> str:
    from app.pubblico import _e

    if not chiuso:
        return ""
    cosa = "Bando chiuso" if chiuso["cosa"] == "bando" else "Misura non più aperta"
    return (f'<div class="chiuso" role="note"><b>{cosa}</b>: «{_e(chiuso["titolo"])}» — {_e(chiuso["motivo"])}. '
            "Le informazioni di questo articolo non valgono più per nuove domande e restano solo per consultazione. "
            '<a href="/registrati">Registrati</a> per ricevere i bandi aperti adatti alla tua impresa.</div>')


def pagina_articolo(conn, a: dict, anteprima: bool = False) -> str:
    """La pagina di un articolo. Con anteprima=True (plancia) mostra anche le bozze, mai indicizzate."""
    from app.abbonamenti import giorni_prova
    from app.pubblico import _e, blog_pubblico, pagina, pubblica

    percorso = f"/blog/{a['slug']}"
    url = seo.assoluto(percorso)
    autore = a.get("autore") or articoli.autore_predefinito()
    aggiornato = a.get("aggiornato_il") or (datetime.now(timezone.utc) if anteprima else None)
    chiuso = articoli.situazione_collegata(conn, a)
    faq = articoli.domande_frequenti(a["corpo"])
    minuti = max(1, round(articoli.parole(a["corpo"]) / PAROLE_AL_MINUTO))
    fonti = a.get("fonti") or []
    fonti_html = "".join(f'<li><a href="{_e(f["url"])}" rel="noopener" target="_blank">{_e(f["nome"])}</a></li>' for f in fonti)
    ufficiale = (f'<a class="bottone chiaro" href="{_e(fonti[0]["url"])}" rel="noopener" target="_blank">Vai alla fonte ufficiale</a>'
                 if fonti else "")
    giorni = giorni_prova()
    avviso = ""
    if anteprima:
        avviso = (f'<p class="bozza">Anteprima dalla plancia: articolo in stato «{_e(a.get("stato", "bozza"))}», '
                  "non visibile al pubblico finché non è pubblicato.</p>")
    elif not blog_pubblico():
        avviso = '<p class="bozza">Anteprima: il sito non è ancora pubblico né indicizzato (BLOG_PUBBLICO=0).</p>'
    corpo = f"""<section class="blog-testa"><div class="contenitore stretto">{avviso}
<p class="briciole"><a href="/blog">Blog</a> › {_e(a['titolo'])}</p>
<h1>{_e(a['titolo'])}</h1>
<p class="dati-articolo">Aggiornato il <time datetime="{_e(_iso(aggiornato) or '')}">{_data(aggiornato)}</time> · di {_e(autore)} · {minuti} min di lettura</p>
{_riquadro_chiuso(chiuso)}
<p class="sottotitolo">{_e(a['sommario'])}</p></div></section>
<section class="articolo"><div class="contenitore stretto">
{articoli.in_html(a['corpo'])}
{f'<h2 id="fonti-ufficiali">Fonti ufficiali</h2><ul>{fonti_html}</ul>' if fonti_html else ''}
<div class="invito"><h2>Quali bandi fanno per la tua impresa?</h2>
<p>bandinQiaro controlla ogni giorno i siti di Unione europea, ministeri, Regioni e Camere di commercio e ti segnala
solo i bandi adatti alla tua impresa, con una scheda chiara. Prova gratis per {giorni} giorni, senza carta.</p>
<p class="azioni"><a class="bottone grande" href="/registrati">Registrati e prova gratis</a> {ufficiale}</p></div>
<p class="piccolo">Articolo informativo, scritto sui documenti ufficiali alla data di aggiornamento. Prima di presentare
la domanda leggi sempre il bando ufficiale: requisiti, importi e scadenze possono cambiare.</p>
</div></section>"""
    org = seo.organizzazione("bandinQiaro: bandi e agevolazioni per imprese, schede chiare e segnalazioni su misura.")
    articolo = {"@type": "Article", "@id": url + "#articolo", "headline": a["titolo"][:110], "description": a["sommario"],
                "inLanguage": "it-IT", "mainEntityOfPage": url, "url": url, "image": seo.assoluto("/immagini/anteprima.png"),
                "author": {"@type": "Person", "name": autore}, "publisher": {"@id": seo.assoluto("/#organizzazione")},
                "isAccessibleForFree": True}
    if a.get("pubblicato_il"):
        articolo["datePublished"] = _iso(a["pubblicato_il"])
    if aggiornato:
        articolo["dateModified"] = _iso(aggiornato)
    # Con la landing chiusa (solo blog aperto) le briciole partono dal blog: "/" non e' ancora una pagina pubblica.
    passi = ([("bandinQiaro", seo.assoluto("/"))] if pubblica() else []) + [("Blog", seo.assoluto("/blog")), (a["titolo"], url)]
    briciole = {"@type": "BreadcrumbList", "itemListElement": [
        {"@type": "ListItem", "position": i, "name": nome, "item": dove} for i, (nome, dove) in enumerate(passi, 1)]}
    grafo = [org, articolo, briciole] + ([seo.domande_frequenti(faq, percorso)] if faq else [])
    indicizza = blog_pubblico() and not anteprima and a.get("stato") == "pubblicato"
    return pagina(f"{a['titolo']} | bandinQiaro", corpo, a["sommario"], indicizza=indicizza, percorso=percorso,
                  testa=STILE_BLOG + seo.json_ld(grafo))


def pagina_elenco(conn) -> str:
    from app.pubblico import _e, blog_pubblico, pagina

    voci = articoli.pubblicati(conn)
    carte = []
    for a in voci:
        chiuso = articoli.situazione_collegata(conn, a)
        etichetta = ' <span class="etichetta-chiuso">bando chiuso</span>' if chiuso else ""
        carte.append(f"""<article class="carta"><div class="piccolo">Aggiornato il {_data(a['aggiornato_il'])}{etichetta}</div>
<h2><a href="/blog/{_e(a['slug'])}">{_e(a['titolo'])}</a></h2><p>{_e(a['sommario'])}</p>
<p><a href="/blog/{_e(a['slug'])}">Leggi l'articolo →</a></p></article>""")
    avviso = "" if blog_pubblico() else '<p class="bozza">Anteprima: il sito non è ancora pubblico né indicizzato (BLOG_PUBBLICO=0).</p>'
    elenco = (f'<div class="griglia elenco-articoli">{"".join(carte)}</div>' if carte
              else "<p>Stiamo preparando i primi articoli. Intanto puoi provare bandinQiaro gratis.</p>")
    corpo = f"""<section class="blog-testa eroe"><div class="contenitore">{avviso}
<p class="occhiello">Blog di bandinQiaro</p><h1>Bandi e agevolazioni per imprese, spiegati semplici</h1>
<p class="sottotitolo">A chi servono, quanto valgono, come si chiedono e gli errori da evitare: articoli brevi sui bandi più
cercati e su quelli che pochi conoscono, scritti sui documenti ufficiali.</p></div></section>
<section><div class="contenitore">{elenco}</div></section>
<section class="finale"><div class="contenitore"><h2>Scopri quali bandi aperti fanno per la tua impresa</h2>
<p>Descrivi la tua impresa e guarda subito l'elenco, con una scheda chiara per ogni bando.</p>
<p><a class="bottone grande bianco" href="/registrati">Inizia la prova gratuita</a></p></div></section>"""
    blog = {"@type": "Blog", "@id": seo.assoluto("/blog#blog"), "name": "Blog di bandinQiaro", "url": seo.assoluto("/blog"),
            "inLanguage": "it-IT", "publisher": {"@id": seo.assoluto("/#organizzazione")},
            "blogPost": [{"@type": "Article", "headline": a["titolo"][:110], "url": seo.assoluto(f"/blog/{a['slug']}"),
                          "datePublished": _iso(a["pubblicato_il"]), "dateModified": _iso(a["aggiornato_il"])} for a in voci]}
    org = seo.organizzazione("bandinQiaro: bandi e agevolazioni per imprese, schede chiare e segnalazioni su misura.")
    return pagina("Blog: bandi e agevolazioni per imprese spiegati semplici | bandinQiaro", corpo,
                  "Articoli brevi sui bandi per imprese più cercati e su quelli di nicchia: a chi servono, quanto valgono, "
                  "scadenze, come si chiedono ed errori da evitare.", indicizza=blog_pubblico(), percorso="/blog",
                  testa=STILE_BLOG + seo.json_ld([org, blog]))


def voci_sitemap(conn) -> list[tuple[str, str]]:
    """(percorso, data dell'ultima modifica) degli articoli pubblicati, piu' /blog se ce n'e' almeno uno."""
    voci = articoli.pubblicati(conn)
    if not voci:
        return []
    ultimo = max(a["aggiornato_il"] for a in voci)
    return [("/blog", ultimo.date().isoformat())] + [(f"/blog/{a['slug']}", a["aggiornato_il"].date().isoformat()) for a in voci]


def righe_llms(conn) -> list[str]:
    """Sezione "Articoli" di /llms.txt: solo i pubblicati, con il sommario."""
    voci = articoli.pubblicati(conn)
    if not voci:
        return []
    righe = ["## Articoli", ""]
    for a in voci:
        chiuso = " (bando chiuso: solo consultazione)" if articoli.situazione_collegata(conn, a) else ""
        righe.append(f"- [{a['titolo']}]({seo.assoluto('/blog/' + a['slug'])}): {a['sommario']} "
                     f"Aggiornato il {_data(a['aggiornato_il'])}.{chiuso}")
    return righe + [""]


def llms_txt_blog(conn) -> str:
    """/llms.txt quando e' aperto solo il blog (BLOG_PUBBLICO=1, PAGINA_PUBBLICA=0): chi siamo in breve, il blog e gli
    articoli pubblicati. Niente prezzi ne' domande frequenti della landing, che aspettano le decisioni di Matteo."""
    from app.pubblico import landing

    righe = [f"# {seo.NOME}", "", f"> {landing.descrizione_breve(landing.numeri(conn))}", "",
             "Servizio italiano per imprese, PMI, professionisti e startup. Lingua: italiano. Il blog spiega in modo "
             "semplice i bandi e le agevolazioni per imprese (europei, nazionali, regionali, delle Camere di commercio): "
             "a chi servono, quanto valgono, scadenze, come si chiedono ed errori da evitare. Ogni articolo e' scritto sui "
             "documenti ufficiali, riporta la data di aggiornamento e le fonti.", "",
             "## Pagine", "", f"- [Blog di bandinQiaro]({seo.assoluto('/blog')}): elenco degli articoli", ""]
    righe += righe_llms(conn)
    return "\n".join(righe)
