# Landing page, SEO e GEO per Bandi Radar

**Data:** 07/10/2026
**Domanda:** come costruire una pagina di atterraggio per chi arriva da Google Ads, salire su Google (SEO) e farsi trovare e citare dai motori di risposta IA (ChatGPT, Claude, Perplexity, Gemini, AI Overviews di Google: GEO o AEO)? Cosa fanno i concorrenti italiani?
**Metodo:** ricerca web (pagine ufficiali di Google, OpenAI e Anthropic, Garante privacy, siti dei concorrenti, blog di settore) e lettura del codice e del database di Bandi Radar.
**Limiti:** non ci sono dati pubblici affidabili sui volumi di ricerca delle parole chiave: le stime vanno verificate con Keyword Planner di Google Ads. Alcuni numeri citati dal settore (es. quante conversioni recupera la Consent Mode avanzata, quanto le citazioni di ChatGPT coincidono con Bing) sono di fornitori o blog e non sono verificati.

**Dominio.** Oggi il sito è su `finanzagevolata.qiaro.it`; è in corso lo spostamento su `bandinqiaro.it`. Il dominio è nella variabile `SITO_URL`: URL canonici, sitemap e `/llms.txt` lo seguono da soli. **La SEO va fatta sul dominio definitivo**: Search Console, Bing Webmaster Tools, Google Business Profile e annunci vanno registrati su `bandinqiaro.it`. Il vecchio dominio deve rimandare al nuovo con un rinvio permanente 301 (riga nel Caddyfile), altrimenti Google vede due siti uguali.

---

## 1. Cosa dice la ricerca, in breve

### Landing per Google Ads

- **Quality Score** (voto 1-10): dipende da CTR atteso, pertinenza dell'annuncio ed **esperienza sulla pagina di destinazione**. Su quest'ultima contano la coerenza tra annuncio e pagina (il titolo della pagina riprende l'annuncio), la velocità, l'uso da telefono e la sostanza dei contenuti. Conviene **una pagina per gruppo di annunci** (es. "bandi Lombardia", "contributi a fondo perduto").
- **Velocità**: LCP sotto 2,5 s e INP sotto 200 ms, misurati su telefono (PageSpeed Insights). Più di metà dei clic a pagamento arriva dal telefono.
- **Sopra la piega**: promessa in una riga, prezzo visibile, un solo invito all'azione chiaro, prova concreta (numeri veri con la data, una scheda di esempio, il commercialista con nome e iscrizione all'Albo).
- **Regole di Google sulle pagine di destinazione**: servono chi gestisce il sito (ragione sociale, P.IVA, contatti), privacy, prezzo chiaro, niente promesse ingannevoli ("contributi garantiti"). Per i servizi finanziari il rischio che un annuncio venga respinto è concreto.
- **Consent Mode v2** (obbligatoria nello Spazio economico europeo da marzo 2024): quattro segnali, `ad_storage`, `analytics_storage`, `ad_user_data`, `ad_personalization`.
  - *Base*: i tag di Google non partono finché la persona non accetta. È quello che fa oggi Bandi Radar.
  - *Avanzata*: i tag partono "negati" e mandano segnali senza cookie, che Google usa per stimare le conversioni perse. Richiede un banner certificato da Google (CMP). Conforme anche lei, recupera più dati, ma è un passo in più da valutare con un consulente privacy.
- **Banner secondo il Garante** (linee guida 10/06/2021): X per chiudere che vale come rifiuto, "Rifiuta" facile come "Accetta", niente cookie non tecnici prima del consenso, la scelta si ripropone dopo 6 mesi, link per cambiare idea sempre raggiungibile (nella pagina Cookie). Tutto già fatto nella pagina.
- **Conversioni avanzate** (novità 2026: da giugno un solo interruttore per web e contatti): alla registrazione si manda a Google l'email cifrata (hash), solo se la persona ha dato `ad_user_data`.

### SEO tecnica

- Title unico (~60 caratteri), description (~155), URL canonico, sitemap con `lastmod` vero, robots.txt che non blocca CSS e JS, `noindex` sulle pagine interne e sui filtri.
- **Dati strutturati**: dal 7/5/2026 Google non mostra più le FAQ "arricchite" nei risultati, ma FAQPage resta valido e aiuta a capire la pagina. Utili Organization, WebSite, Service/Offer, BreadcrumbList, Article con autore e data, ItemList per gli elenchi. **GovernmentService no**: non siamo un ente pubblico.
- **YMYL ed E-E-A-T**: la finanza d'impresa è un argomento "Your Money Your Life", dove Google è più severo. Servono un autore vero con competenze (il commercialista, con iscrizione all'Albo), una pagina "chi siamo e metodo", il link alla fonte ufficiale in ogni scheda, le date di verifica e aggiornamento.
- **Rischio "contenuti in serie"** (*scaled content abuse*, regola dal 2024 rafforzata ad agosto 2025): pagine generate in massa, quasi uguali o vuote, possono essere penalizzate qualunque sia il metodo. Vedi §5.

### GEO / AEO (motori di risposta IA)

- **Google AI Overviews e AI Mode** usano lo stesso indice e gli stessi sistemi di qualità della ricerca normale: Google dice esplicitamente che non servono file o dati speciali. La buona SEO basta.
- **llms.txt**: costa poco ma oggi nessuna grande piattaforma dichiara di leggerlo (test del 2025: zero visite dai programmi delle IA). L'abbiamo messo perché costa pochi minuti e non fa danni, **non è una priorità**.
- **robots.txt**: si consentono esplicitamente i programmi di ricerca e citazione (OAI-SearchBot, ChatGPT-User, Claude-SearchBot, Claude-User, PerplexityBot, Bingbot, Googlebot) e anche quelli di addestramento (GPTBot, ClaudeBot, Google-Extended): per un sito di vetrina aiutano a far conoscere il marchio. Ogni programma va nominato da solo.
- **Bing conta**: ChatGPT cerca sull'indice di Bing. Servono **Bing Webmaster Tools** e **IndexNow** (avvisa Bing a ogni pagina nuova o cambiata).
- **Contenuti facili da citare**: risposta breve in testa, numeri con la data ("al 07/10/2026 i bandi aperti in Lombardia sono 86"), tabelle (importo, percentuale, scadenza, beneficiari), "aggiornato il…" visibile, aggiornamento frequente.
- **Menzioni esterne**: le IA citano molto stampa di settore (PMI.it, IPSOA, FiscoeTasse), Ordini professionali, directory, forum e Reddit. Un **dato originale ogni mese** (es. "bandi aperti per regione, ottobre 2026") è il modo più semplice per farsi riprendere.

## 2. Concorrenti italiani

| Sito | Cosa fanno bene | Punti deboli | Prezzo visto |
|---|---|---|---|
| incentivi.gov.it (MIMIT, Invitalia) | Oltre 1.000 incentivi da 374 amministrazioni, chatbot, massima autorità per Google | Nessun avviso via email sul profilo, linguaggio burocratico, copertura camerale e comunale incompleta | gratis |
| contributiregione.it (Europrofessional) | Pagine per regione e provincia (`bandi.contributiregione.it/regione/lombardia`), una pagina per bando, newsletter gratuita, consulenza gratuita per raccogliere contatti | Tono molto commerciale, abbinamento generico | INFO BANDI 29 €/mese + IVA o 297 €/anno |
| FASI (fasi.biz / fasi.eu) | Banca dati storica con avvisi email, articoli "bandi Regione X" | Listino complicato e caro per una micro impresa (prezzi da riverificare) | da 198 €/anno + IVA |
| bandofacile.com | Ricerca personalizzata con l'IA, notifiche gratuite. **Concorrente diretto sul prezzo** | Non dichiara le fonti coperte | Premium 18 €/mese; compilazione 500 € a bando |
| Bandibot | Anteprima gratuita, notifiche WhatsApp | Prezzo di riferimento molto basso: il nostro valore va spiegato | 4,99-5,99 €/mese o 35 €/anno |
| BandIntelligence.it | Freemium, avvisi per settore, regione e forma giuridica, pagine per settore (`/bandi/settore/ristorazione`) | Abbinamento automatico solo "in arrivo" | gratis, PRO in arrivo |
| finera.it, incentivimpresa.it, getbandit | Articoli mensili "fondo perduto [mese] 2026" e guide che si posizionano bene | Contenuto generico, poca verifica | vari |

**Spazio libero per noi:** nessuno unisce in modo credibile copertura delle Camere di commercio e dei Comuni, schede in italiano semplice, abbinamento al profilo e un commercialista vero a successo. Il prezzo di 20 € sta tra Bandofacile (18 €) e contributiregione (29 €).

## 3. Parole chiave principali (volumi da verificare)

| Parola chiave | Intento | Stima indicativa | Dove usarla |
|---|---|---|---|
| contributi a fondo perduto | informativo, molto ampio | alto | home, pagina per tipo di agevolazione |
| finanziamenti a fondo perduto 2026 | informativo e commerciale | medio-alto, stagionale | pagina per tipo, articolo mensile |
| bandi per imprese / bandi imprese 2026 | commerciale | medio | home (titolo), annunci |
| bandi regione [nome] (lombardia, veneto, piemonte...) | locale, converte bene | medio, varia per regione | pagine per regione, annunci per regione |
| bandi camera di commercio [città] | locale, poca concorrenza | basso a città, alto in totale | pagine per Camera (in un secondo momento) |
| agevolazioni imprese, incentivi imprese | informativo | medio | home, guida |
| nomi delle misure (Nuova Sabatini, bando ISI INAIL, Conto Termico, Iperammortamento) | navigazionale, picchi forti | alto nei periodi di apertura | pagine delle misure nazionali |

Indicazione pratica: **annunci sulle parole regionali** (più pertinenti, probabilmente più economiche) con pagine dedicate; **contenuti SEO** sulle misure famose e sugli elenchi "bandi aperti a [mese] 2026".

## 4. Cosa è stato fatto oggi (in `app/pubblico/`)

- **Landing** su `/` (quando `PAGINA_PUBBLICA=1`) e in anteprima su `/presentazione`: promessa e prezzo sopra la piega, una scheda vera come esempio, numeri presi dal database con la data (siti controllati, bandi aperti con la scheda, bandi esaminati, misure nazionali), come funziona in 3 passi, cosa trovi, bandi aperti regione per regione, prezzo di lancio 20 €/mese + IVA, compensi a successo del supporto, chi c'è dietro (bozza con segnaposto), 9 domande frequenti, invito finale. HTML e CSS leggeri, niente font esterni: circa 33 KB, 0,07 s dal server con i numeri in memoria (15 minuti). Adatta al telefono (controllata su iPhone 13 e computer).
- **SEO tecnica**: title e description, URL canonico (dominio da `SITO_URL`), Open Graph con immagine 1200×630, favicon, `robots.txt` (tutto chiuso finché la pagina è spenta; da accesa apre solo le pagine pubbliche e nomina i programmi delle IA), `sitemap.xml`, dati strutturati JSON-LD (Organization, WebSite, Service con Offer a 20 € IVA esclusa, FAQPage con le stesse domande della pagina).
- **GEO**: `/llms.txt` con descrizione, numeri del giorno, domande frequenti e pagine utili.
- **Misurazione**: nessuno strumento di Google acceso. Il punto è pronto: mettendo `GOOGLE_ADS_ID` e/o `GOOGLE_ANALYTICS_ID` nel `.env` compare il banner (Accetta, Rifiuta, X = rifiuta) e i tag partono solo dopo "Accetta" (Consent Mode v2 base). La conversione "registrazione completata" va ancora aggiunta nella pagina di registrazione della plancia quando ci saranno gli account.

## 5. Proposta: pagine pubbliche generate dai dati (da fare dopo)

| Pagina | Contenuto | Beneficio | Rischio e rimedio |
|---|---|---|---|
| `/bandi-aperti/lombardia` (una per regione, 21) | Frase di risposta in testa ("Al 07/10/2026 in Lombardia ci sono 86 bandi aperti per le imprese, di cui X a fondo perduto"), tabella sintetica (titolo, ente, tipo, importo massimo, scadenza), i nazionali validi anche lì, invito a registrarsi per la scheda completa e l'abbinamento | Le ricerche "bandi regione X" sono le più vicine all'acquisto; pagine perfette per gli annunci regionali (Quality Score) e per essere citate dalle IA (numero datato, tabella) | **Contenuto sottile**: regioni con 3-4 bandi (Abruzzo, Umbria, Molise) → `noindex` sotto una soglia (es. 8 bandi) o accorpamento per area. **Doppioni**: i bandi nazionali ripetuti in 21 pagine → in un riquadro separato e breve, con link a una pagina unica dei nazionali |
| `/agevolazioni/fondo-perduto`, `/agevolazioni/finanziamento-agevolato`, `/agevolazioni/credito-imposta`, `/agevolazioni/voucher` | Spiegazione breve scritta dal commercialista + elenco dei bandi aperti di quel tipo | Parole chiave ampie e informative ("contributi a fondo perduto") | Testo generico uguale a mille siti: serve la parte scritta a mano e firmata |
| `/misure/<misura>` pubbliche (oggi la pagina Misure è nella plancia) → indirizzo nuovo `/agevolazioni-nazionali/nuova-sabatini` per non scontrarsi con `/misure/:id` della plancia | La scheda già verificata a mano in `app/misure/misure.yaml`: cos'è, a chi spetta, beneficio stimato, cumulo con i bandi, esempi per tipo di impresa, link ufficiale, data di verifica | Ricerche navigazionali con picchi forti (Sabatini, Conto Termico, Iperammortamento); contenuto originale (gli esempi per profilo) | Poche pagine (11 aperte), contenuto ricco: rischio basso. Tenere la data di verifica visibile e aggiornata |
| `/bandi-aperti/<regione>/<bando>` (una pagina per bando) | Scheda pubblica ridotta | Molte ricerche sui nomi dei bandi | **Da non fare subito**: migliaia di pagine, che invecchiano e chiudono; serve una regola per i chiusi (pagina tenuta con lo stato "chiuso" e i bandi simili aperti) e la qualità 9/10 prima di esporle a Google |
| Articolo mensile "Bandi aperti per le imprese, [mese] 2026" | Numeri per regione e per tipo, le 10 novità del mese, firmato | Dato originale citabile da stampa e IA; menzioni esterne | Va scritto (o rivisto) davvero ogni mese |

Indirizzi: non usare `/bandi/...` né `/misure/...`, che sono pagine della plancia. Ogni pagina generata deve avere: URL canonico, data di aggiornamento visibile, link al bando ufficiale, `ItemList` nei dati strutturati, ingresso nella sitemap con `lastmod` vero, apertura in `robots.txt` (elenco bianco in `app/pubblico/seo.py`).

## 6. Strategia in passi

1. **Dominio definitivo** (`bandinqiaro.it`): `SITO_URL`, Caddy con rinvio 301 dal vecchio dominio, Resend sul nuovo dominio.
2. **Account di Matteo**: Google Search Console e Bing Webmaster Tools (proprietà sul dominio definitivo, invio della sitemap), Google Ads (con Keyword Planner per i volumi), Google Business Profile dello studio, Google Analytics 4 se serve.
3. **Testi da confermare** (vedi sotto) e accensione della pagina (`PAGINA_PUBBLICA=1`) solo dopo: chi c'è dietro, prezzo, testi legali rivisti, dati del titolare nel piede.
4. **Misurazione**: banner + Consent Mode base già pronti; aggiungere la conversione "registrazione completata" (con conversioni avanzate) nella plancia.
5. **Annunci**: un gruppo per le parole regionali più cercate (Lombardia, Piemonte, Veneto, Puglia...) e uno per "contributi a fondo perduto", ciascuno con la sua pagina (§5).
6. **Pagine generate dai dati**: prima le 11 misure nazionali e le regioni sopra soglia, poi i tipi di agevolazione.
7. **Autorevolezza**: pagina "chi siamo e metodo" firmata, articolo mensile con i numeri, menzioni (Ordine, associazioni di categoria, stampa locale, LinkedIn), IndexNow.

## 7. Cosa serve da Matteo

- **Conferme di testo**: nome e cognome, iscrizione all'Albo, città, anni di esperienza, foto (riquadro in `app/pubblico/testi/chi_siamo.html`); dati del titolare per il piede (`TITOLARE_SITO`) e per le note legali.
- **Prezzo**: la landing dice "20 € al mese + IVA, prezzo di lancio per i primi clienti". Oggi però Stripe e i Termini prevedono **mensile 30 €** e **annuale 20 €/mese con impegno di 12 mesi**. Prima di accendere gli annunci va deciso cosa vende davvero il pulsante (es. un prezzo mensile di lancio a 20 € in Stripe, oppure scrivere "20 € al mese con l'annuale") e allineati termini e Stripe.
- **Account**: Google Search Console, Bing Webmaster Tools, Google Ads, Google Business Profile, eventualmente Google Analytics 4 (con la cookie policy aggiornata), profilo LinkedIn (`PROFILI_SOCIAL`).
- **DNS** di `bandinqiaro.it` e conferma del passaggio.

## 8. Rischi

- **Promesse**: niente "contributi garantiti" o "trovi tutti i bandi": la pagina dice "schede indicative" e "leggi sempre il bando ufficiale". Con affidabilità 7-8/10 (VISIONE) l'esposizione pubblica di molte schede è un rischio d'immagine: per questo le pagine generate partono dalle misure verificate a mano e dagli elenchi sintetici.
- **Contenuti in serie**: pagine generate quasi vuote o uguali → penalizzazione di tutto il sito. Soglie, `noindex` e testo scritto a mano.
- **Due domini**: senza 301 il vecchio e il nuovo si fanno concorrenza.
- **Privacy e Ads**: banner e Consent Mode corretti, cookie policy aggiornata per ogni strumento nuovo, nessun dato dell'impresa mandato a Google oltre l'email cifrata e solo con consenso.
- **Prezzo incoerente** tra landing, Stripe e termini (vedi sopra): una pagina che promette un prezzo diverso da quello del pagamento è un problema sia per Google Ads sia per i clienti.
- **Numeri**: sono veri e datati, ma cambiano ogni giorno (es. regioni con pochi bandi). Contano solo dalla situazione dei bandi (`bandi_situazione`).

## Sintesi

La landing, la SEO tecnica di base e i file per le IA sono pronti in `app/pubblico/` e restano spenti finché Matteo non accende `PAGINA_PUBBLICA`. La strada più efficace per farsi trovare, sia su Google sia dalle IA, è la stessa: pagine utili con dati veri e datati (bandi aperti per regione, misure nazionali), firmate da una persona competente, sul dominio definitivo, registrate su Search Console e Bing. llms.txt e dati strutturati aiutano poco ma costano poco. Il primo blocco reale è il prezzo: va allineato tra pagina, Stripe e termini prima degli annunci.

### Fonti principali

- Google, funzioni IA nella Ricerca: https://developers.google.com/search/docs/appearance/ai-features
- Google Ads, conversioni avanzate: https://support.google.com/google-ads/answer/16884284?hl=en
- Garante privacy, linee guida cookie 10/06/2021: https://www.garanteprivacy.it/home/docweb/-/docweb-display/docweb/9677876
- Consent Mode v2: https://www.simoahava.com/analytics/consent-mode-v2-google-tags/ ; https://www.cookieyes.com/blog/basic-vs-advanced-google-consent-mode/
- FAQ arricchite ritirate: https://searchengineland.com/google-to-no-longer-support-faq-rich-results-476957
- Spam policy e contenuti in serie: https://www.searchenginejournal.com/in-depth-look-at-google-spam-policies-updates/511005/
- llms.txt: https://ahrefs.com/blog/what-is-llms-txt/ ; https://www.semrush.com/blog/llms-txt/
- Programmi di OpenAI: https://developers.openai.com/api/docs/bots
- Concorrenti: https://www.contributiregione.it/info-bandi-professional/ ; https://bandi.contributiregione.it/regione/lombardia ; https://bandofacile.com/ ; https://www.bandibot.com/ ; https://bandintelligence.it/ ; https://www.mimit.gov.it/it/notizie-stampa/portale-incentivi-gov-it-oltre-1000-gli-incentivi-pubblicati-e-374-le-amministrazioni-coinvolte
