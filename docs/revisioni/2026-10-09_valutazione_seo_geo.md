# Valutazione SEO e GEO di bandinqiaro.it

**Data:** 08-09/10/2026 · **Metodo:** solo lettura, dall'esterno: curl (User-Agent BandiRadar) su pagine, intestazioni, robots, sitemap, llms.txt; analisi dell'HTML e del JSON-LD; ricerche web (il motore di WebSearch, non Google né Bing direttamente) per `site:`, marchio e "iperammortamento 2026"; lettura di 2 articoli concorrenti. Nessuna modifica fatta.
**Limiti:** non ho potuto interrogare Google e Bing in modo diretto né usare PageSpeed Insights (velocità misurata solo dal server, non su un telefono vero). Alcuni concorrenti bloccano la lettura automatica (incentivimpresa 403, ayming con verifica anti-bot).

---

## 1. Indicizzazione — voto 5/10 (impostazione 8, risultati 0)

**Bene**
- `robots.txt` corretto: un solo gruppo con tutti i programmi (Googlebot, Bingbot, GPTBot, OAI-SearchBot, ChatGPT-User, ClaudeBot, Claude-SearchBot, Claude-User, PerplexityBot, Google-Extended, Applebot-Extended) e `*`; aperti solo `/blog`, `/llms.txt`, `/sitemap.xml`, `/immagini/`, `/favicon.svg`; `Sitemap:` dichiarata.
- `sitemap.xml` valida: 2 indirizzi (`/blog`, l'articolo), `lastmod` 2026-10-07.
- Rinvii: `www` → 301 → `https://bandinqiaro.it/`; `http` → 308 → https; `finanzagevolata.qiaro.it/blog` → 301 → `bandinqiaro.it/blog` (il percorso si mantiene). Corretto.
- Meta robots: blog e articolo `index, follow, max-snippet:-1, max-image-preview:large`; landing, privacy, note legali, plancia `noindex, nofollow`. Canonical presente e coerente sulle pagine del blog.
- Articolo inesistente `/blog/xyz` → 404 vero. Le bozze non sono raggiungibili (404).

**Male / da sistemare**
- `site:bandinqiaro.it`: **zero risultati** (sito aperto da un giorno, Search Console e Bing non collegati, nessun link in ingresso). Oggi il sito, per i motori, non esiste.
- L'unica cosa trovata cercando "bandinqiaro.it" o "finanzagevolata.qiaro.it" sono le **pull request del repository GitHub pubblico** `zucchellamatteo-hue/bandi-radar` (vedi §4: rischio).
- `/blog/` e `/blog/<articolo>/` (con la barra finale) rispondono 200 con la pagina vuota della plancia (noindex): non fa danni gravi, ma meglio un 301 verso l'indirizzo senza barra.
- Qualsiasi indirizzo sconosciuto fuori dal blog risponde 200 con la plancia (soft 404). È chiuso da robots e noindex, quindi impatto basso.
- Le richieste `HEAD` rispondono **405** (solo GET): alcuni strumenti di controllo link e alcuni crawler usano HEAD. Da abilitare.

## 2. SEO tecnica — voto 7/10

| Aspetto | Esito |
|---|---|
| Tempi di risposta (dal server) | Blog e articolo: 0,14-0,16 s. **Landing /presentazione: 1,1 s** (lenta: calcola i numeri dal database a ogni visita; serve una cache) |
| Peso | Articolo 52 KB (16 KB compresso), nessun JavaScript, CSS in linea, nessuna immagine: leggerissimo. Landing 39 KB (12 KB compresso) |
| Mobile | `viewport` presente, regole `@media` a 700 e 860 px, font di sistema. Da verificare su PageSpeed Insights da Matteo |
| Titoli h1/h2 | Un solo h1, 14 h2 e h3 ben ordinati (articolo); struttura buona |
| Title | **126 caratteri** sull'articolo: Google ne mostra ~60. Da accorciare (es. "Iperammortamento 2026: risparmio, software, IRAP \| Bandi Radar", ~60) |
| Description | 185 caratteri: un po' lunga (ideale 150-160), ma con il numero forte in testa. Bene |
| JSON-LD | Sintassi valida (Organization, Article, BreadcrumbList, FAQPage con 11 domande; Blog sull'indice). **Problemi:** `headline` tagliato a metà parola ("...per l'IRA"); `dateModified` (07/10 15:41) **precedente** a `datePublished` (07/10 21:57); `author` è una "Person" che si chiama "Redazione Bandi Radar – contenuti verificati da…" (non è una persona: Google lo considera debole); manca `sameAs` nell'Organization; il `<time>` visibile usa la data di modifica |
| Open Graph | Completo, immagine 1200×630 (252 KB, va bene). `og:type` è `website` sull'articolo: dovrebbe essere `article` con `article:published_time` |
| Immagini | Nessuna immagine nell'articolo (nessun problema di alt, ma niente grafico/tabella visiva). **Nessuna tabella HTML**: gli scaglioni 180/100/50% sono in un elenco; i concorrenti li mettono in tabella |
| Link interni | Pochi: articolo → blog, registrati, pagine legali. Nessun link verso altri articoli (normale con 1 articolo). La landing non linka l'articolo sull'iperammortamento pur avendolo in vetrina |
| Link esterni | Ottimi: Normattiva, Gazzetta Ufficiale, MIMIT, GSE, Agenzia Entrate |
| HTTPS | Sì, HTTP/2 e HTTP/3 |
| Intestazioni di sicurezza | **Assenti**: niente HSTS, X-Content-Type-Options, Referrer-Policy, Content-Security-Policy, Permissions-Policy. Nessun `Cache-Control` sulle pagine. `server: uvicorn` esposto |

## 3. Contenuti — voto 8/10 (articolo 9, E-E-A-T 5)

**L'articolo** (~3.800 parole, 18 minuti): è il migliore tra quelli che ho visto sull'argomento per **chiarezza e precisione**: risposta forte in testa (200.000 € → 86.400 € di IRES in meno), scaglioni, allegati IV e V con dove leggerli, focus software ed ERP, nodo cloud/SaaS ben spiegato, sezione IRAP con norme citate e calcolo, 7 esempi per tipo d'impresa, passi sul GSE, cumulo, errori, esclusi, 11 FAQ, norme e fonti ufficiali con link. "Aggiornato il 07/10/2026" e "verificato sulle fonti ufficiali" visibili.

**Parole chiave coperte:** "iperammortamento 2026" (titolo, h1, URL), "iperammortamento software / SaaS / gestionale / ERP" (h3 e FAQ), "iperammortamento IRAP" (h2 dedicato: angolo originale, quasi nessun concorrente lo tratta così bene), "fotovoltaico", "leasing", "Conto Termico", "GSE", "quanto si risparmia/calcolo". **Mancano o sono deboli:** "iperammortamento perizia/certificazione costi" (citate ma senza sezione), "iperammortamento 2026 scadenze/comunicazioni GSE" (le 5 comunicazioni e le date 12/06 e 21/07 sono il cuore di incentivimpresa), "differenza con Transizione 5.0 / credito d'imposta 4.0", "coefficienti di ammortamento" (l'esempio a 5 anni è "per semplicità", ma un macchinario va di solito al 10% annuo, ~10-11 anni: un concorrente lo fa notare; meglio usare il caso reale).

**Confronto con chi compare oggi per "iperammortamento 2026"** (reteagevolazioni.it, intesasanpaoloinnovationcenter.com, incentivimpresa.it, ayming.it, tikappapi.com, merlinconnect.it):
- *reteagevolazioni.it*: 4.500-5.000 parole, **autore con nome e qualifica** (Franco Rasotto, consulente, con LinkedIn e libro), data di pubblicazione e aggiornamento, tabella degli scaglioni, 13 FAQ, IRAP e SaaS trattati. È il concorrente da battere: pari a noi nei contenuti, superiore per autorevolezza.
- *Intesa Sanpaolo Innovation Center*: ~2.500 parole, senza autore né data, niente IRAP e SaaS, nessun link alle norme: vince per autorevolezza del dominio, non per qualità.
- *incentivimpresa.it*: punta sulla procedura GSE e le 5 comunicazioni (non leggibile in automatico: 403).

**E-E-A-T (esperienza e affidabilità) — il punto debole.** Argomento "Your Money Your Life": Google pesa molto chi scrive. Oggi l'autore è "Redazione… verificati da un dottore commercialista iscritto all'Albo" **senza nome**; non c'è una pagina "chi siamo" pubblica (quella nella landing ha ancora i segnaposto [NOME E COGNOME], [CITTÀ]); le note legali sono `noindex` e bloccate da robots, quindi Google non vede chi gestisce il sito (ragione sociale, P.IVA).

## 4. GEO (motori di risposta IA) — voto 3/10 (preparazione 7, presenza 0)

- **llms.txt**: presente, chiaro, con numero di siti controllati, descrizione e l'articolo con il numero chiave. Bene (utilità reale oggi bassa, costo zero).
- **Accesso dei bot IA**: tutti ammessi in robots e il server risponde 200 a GPTBot, ClaudeBot, PerplexityBot, OAI-SearchBot, Googlebot (provato). Nessun blocco del CDN/firewall.
- **Contenuti citabili**: ottimi. Frasi brevi con numeri ("+180% fino a 2,5 milioni", "43,2% della spesa", "IRAP: no, comma 427"), FAQ con risposta in prima riga, data di verifica, norme precise. È esattamente il formato che le IA riprendono.
- **Presenza del marchio e menzioni esterne: nessuna.** Le ricerche "Bandi Radar bandinqiaro" e "bandinqiaro.it" trovano solo il repository GitHub e **altri progetti chiamati "Radar bandi"** (caracatta/Radar-bandi, AntonioKZ/bandi-radar, domitillaz/radar-bandi): il nome "Bandi Radar" è già usato e generico, il dominio "bandinqiaro" aiuta a distinguersi.
- **ChatGPT/Perplexity/Claude oggi non possono citarci**: nessun indice (Bing, Google, Brave) ci conosce; la ricerca del titolo esatto dell'articolo restituisce solo concorrenti.
- **Rischio dal repository pubblico.** `zucchellamatteo-hue/bandi-radar` è **PUBBLICO** su GitHub ed è indicizzato. Contiene `strumenti/sessione/blog/bozze_2026-10-07.json` e `guide_misure_2026-10-07.json` con il **testo completo delle 16 bozze** (es. Nuova Sabatini), più i documenti di strategia, prezzi, concorrenti e piano SEO. Quando gli articoli usciranno sul blog, Google e le IA potrebbero averne già visto una copia su GitHub (contenuto duplicato, autore "originale" sbagliato) e i concorrenti possono copiarli. Da valutare con Matteo: rendere il repository privato (decisione sua: è anche una questione di riservatezza, non solo di SEO).

## 5. Landing /presentazione (anteprima) — voto 6/10 oggi, 8/10 con i testi definitivi

**Impatto e chiarezza: buoni.** Promessa in una riga ("I bandi giusti per la tua impresa, ogni settimana nella tua email"), prezzo e "senza carta di credito" sopra la piega, numeri veri e datati (279 siti, 476 bandi aperti, 4.533 esaminati, ripartizione per regione e per tipo), 3 passi, vetrina che scorre, FAQ, compensi a successo trasparenti. Title 60 caratteri e description 160: perfetti.

**Cosa frena la conversione e la SEO futura**
- "Chi c'è dietro" con segnaposto `[NOME E COGNOME]`, `[CITTÀ]`, `[ANNI]` e riquadro "Bozza da confermare": è la prima cosa da completare.
- Prezzo 20 €/mese + IVA in pagina, mentre Stripe e i Termini prevedono 30 € mensile / 20 € con annuale (già noto): con Google Ads è un rischio di annuncio respinto.
- Esempi di schede poco adatti al pubblico (micro e piccole imprese): Fondo Salvaguardia (30 milioni, ingresso nel capitale, con l'etichetta "altro · fondo perduto" che confonde), Idrogeno Sicilia (10 milioni), Venture capital Lombardia. Meglio 3 esempi "da PMI" (voucher, bando camerale, contributo regionale da 20-50 mila €).
- Tempo di risposta 1,1 s lato server (prima che il telefono disegni la pagina): da portare sotto 0,3 s con una cache dei numeri.
- 9 inviti all'azione tutti verso `/registrati` (bene uno solo, ma la pagina di registrazione non è stata valutata).
- Nessun link agli articoli del blog dalla landing (né il contrario se non "Prova gratis").

**Cosa manca per Google Ads:** titolare del sito con ragione sociale e P.IVA nel piede, prezzo coerente con il pagamento, nome del commercialista, pagina per gruppo di annunci (es. "bandi Lombardia" con i 99 bandi), conversione "registrazione completata" con Consent Mode v2, tempo di caricamento su telefono (LCP < 2,5 s) verificato con PageSpeed.

---

## Voto complessivo oggi

- **SEO: 5/10.** Fondamenta tecniche buone e un articolo di qualità superiore alla media, ma il sito non è ancora visto da nessun motore, ha 1 sola pagina di contenuto e manca un autore con nome.
- **GEO: 3/10.** Il contenuto è pronto per essere citato e i bot sono ammessi, ma le IA attingono agli indici di Bing/Google e alle menzioni esterne: oggi entrambi zero.

## Le 10 azioni più utili, in ordine di impatto

| # | Azione | Chi |
|---|---|---|
| 1 | Collegare **Google Search Console** (proprietà "Dominio" con record TXT) e **Bing Webmaster Tools** (importando da Search Console), inviare la sitemap e chiedere l'indicizzazione dell'articolo e di /blog | Matteo (account); Claude può preparare la guida passo passo |
| 2 | **Firmare gli articoli con nome e cognome** del commercialista, iscrizione all'Albo e città; pagina pubblica "Chi siamo e metodo" indicizzabile con titolare, P.IVA, contatti; JSON-LD `author` = persona vera con `url`/`sameAs` (LinkedIn) | Matteo (dati); Claude (pagina e JSON-LD) |
| 3 | Decidere sul **repository GitHub pubblico** (rendere privato o togliere bozze e documenti di strategia) prima di pubblicare altri articoli | Matteo decide; Claude esegue la pulizia se serve |
| 4 | **Pubblicare le bozze** a ritmo regolare (2-3 a settimana), partendo dalle misure più cercate (Nuova Sabatini, ISI INAIL, Conto Termico), con link incrociati tra articoli | Matteo pubblica; Claude/agenti rivedono |
| 5 | Attivare **IndexNow** (Bing, e quindi ChatGPT) a ogni articolo pubblicato o aggiornato | Claude |
| 6 | Correggere i dettagli tecnici dell'articolo: title ≤ 60 caratteri, `headline` intero (o accorciato con senso), `datePublished` ≤ `dateModified`, `og:type=article`, tabella HTML per scaglioni e calcolo, esempio con il coefficiente di ammortamento reale | Claude |
| 7 | Intestazioni di sicurezza in Caddy (HSTS, nosniff, Referrer-Policy, Permissions-Policy), `Cache-Control` sulle pagine pubbliche, risposta alle richieste HEAD, 301 da `/blog/` a `/blog` | Claude |
| 8 | Prime **menzioni esterne**: profilo LinkedIn di Matteo e pagina aziendale che rilanciano l'articolo; Google Business Profile dello studio; segnalazione dell'articolo IRAP a una testata o newsletter di settore; poi il rapporto mensile "bandi aperti per regione" (punto 8 del piano) | Matteo (profili, contatti); Claude/agenti (testi e numeri) |
| 9 | Completare la landing: chi c'è dietro, prezzo allineato a Stripe/Termini, titolare nel piede, 3 esempi da PMI, cache dei numeri (sotto 0,3 s), link al blog | Matteo (decisioni); Claude (codice) |
| 10 | Pagine "bandi aperti in <regione>" e "agevolazioni nazionali/<misura>" (punti 6-7 del piano), partendo da Lombardia (99), Piemonte (41), Toscana (37), Puglia (34), Sardegna (33) | Claude/agenti, con testo d'apertura rivisto da Matteo |

## Cosa aspettarsi

- **Prossimi 7-30 giorni:** con Search Console e Bing collegati, l'articolo viene indicizzato in pochi giorni; prime impressioni su ricerche lunghe ("iperammortamento IRAP", "iperammortamento SaaS", "gestionale iperammortamento") dove la concorrenza è più debole. Su "iperammortamento 2026" difficilmente oltre la seconda-terza pagina: dominio nuovo, nessun link. Visite organiche: poche decine al mese.
- **30-60 giorni:** con 8-10 articoli firmati e qualche menzione, Bing e quindi ChatGPT/Copilot possono iniziare a citare le risposte più precise (IRAP, SaaS). Perplexity tende a essere il primo a citare siti nuovi ben strutturati. Search Console darà le prime parole chiave vere per decidere i nuovi articoli.
- **60-90 giorni:** con 15-20 articoli, pagine regionali e un primo rapporto mensile ripreso da qualcuno, realisticamente alcune centinaia di visite organiche al mese e le prime registrazioni da ricerca. Le prime pagine di Google sulle parole principali ("bandi imprese 2026", "contributi a fondo perduto") richiedono più mesi e menzioni esterne: lì conviene Google Ads con pagine dedicate.

### Fonti consultate
- https://bandinqiaro.it/robots.txt, /sitemap.xml, /llms.txt, /blog, /blog/iperammortamento-2026-guida-completa, /presentazione
- https://github.com/zucchellamatteo-hue/bandi-radar/pull/108 (risultato di ricerca del marchio)
- https://www.reteagevolazioni.it/iperammortamento-2026/
- https://www.intesasanpaoloinnovationcenter.com/it/business-transformation/open-innovation/iperammortamento-come-funziona/
- https://www.incentivimpresa.it/iperammortamento-2026-come-funziona/ (403)
- https://www.ecnews.it/fiscale/fisco-e-patrimonio/agevolazioni/iperammortamento-no-ai-saas-si-alle-licenze-duso/
- https://www.bravomanufacturing.it/iperammortamento-2026/
