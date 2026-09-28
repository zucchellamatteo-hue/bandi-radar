# Perimetro completo: lettura della scorta e sezioni nuove, primo giro in produzione

**Data:** 28/09/2026, sessione sul VPS (passo 1 di `docs/sessioni/2026-09-28_perimetro_api_rivalutazione.md`).
**Domanda:** dopo la valutazione del 27/09 (solo il 22% dei bandi aperti per imprese del campione aveva una scheda, il 45% non era raccolto da nessuna fonte), quanti bandi in più entrano leggendo per intero le fonti, invece delle sole novità?
**Metodo:**
1. Ogni fonte segnalata dalla valutazione aperta dal server, con lo User-Agent di Bandi Radar e rispettando robots.txt: come si pagina, se c'è un filtro per stato o destinatari, se l'API restituisce le scadenze. Ogni blocco `scorta` e ogni fonte nuova provati con `esegui --prova ID --scorta` prima di scriverli nel registro (PR #27).
2. Regressione del lettore HTML su tutte le 139 fonti html: differenze solo dove volute.
3. In produzione dopo l'unione della PR #27: primo giro della raccolta con le scorte, poi smistamento a regole, deduplica, pagina ufficiale e allegati (6+6 lavoratori divisi per sito).
4. Incrocio con i 193 bandi aperti o in arrivo che il 27/09 nessuna fonte raccoglieva (`strumenti/incrocio_globale.py` sul database del 28/09).

**Limiti:** lo smistamento dei "da rivedere" e le schede aspettano la chiave API, quindi qui si misura la raccolta, non le schede. Lo stato "aperto" dei bandi nuovi è quello dei segnali gratuiti (scadenza nei dati della fonte, etichette della pagina), non ancora verificato dall'IA.

## Scorte lette il 28/09

| Fonte | Letti | Nuovi | Scartati (scaduti o vecchi) | Note |
|---|---|---|---|---|
| incentivi.gov.it (Solr, una richiesta) | 823 | 726 | 5.087 | sì |
| Regione Sardegna (API, 22 pagine da 100) | 788 | 742 | 1.312 | sì; molte gare e affidamenti, li scarta lo smistamento |
| Portale UE (API, 20 pagine da 100) | 509 | 485 | 773 | sì; quasi tutti "da rivedere" (inglese) |
| MIMIT (feed paginato) | 296 | 286 | – | sì |
| Calabria Europa (API WordPress) | 297 | 247 | – | sì |
| Anagrafica bandi Lombardia | 241 | 147 | 1.671 | sì |
| Molise (archivio notizie mese per mese) | 152 | 145 | – | sì |
| Finlombarda (7 pagine) | 121 | 108 | – | sì |
| Siena (pagine dell'elenco Avvisi) | 64 | 54 | – | sì |
| Parma (API Plone, tipo Bando) | 57 | 43 | 602 | sì |
| Piemonte (filtro imprese + aperto) | 33 | 33 | – | sì (prima 3 link) |
| Ministero del Turismo (sitemap) | 21 | 20 | – | sì |
| FVG (filtro misure contributive) | 11 | 11 | – | sì |
| Como-Lecco (6 schede per pagina) | 9 | 3 | – | sì |
| Unioncamere Lombardia | 0 | 0 | – | no: certificato HTTPS del sito scaduto il 28/09, si riprova da solo |

## Numeri

| Passo | Prima (27/09) | Dopo (28/09) |
|---|---|---|
| Annunci | 6.630 | circa 9.800 |
| Smistamento a regole | – | 5.427 annunci: 1.749 rilevanti, 833 non rilevanti, **2.845 da rivedere** (all'IA) |
| Bandi | 1.057 | **2.487** (1.430 nuovi; 221 dubbi per la pagina Doppioni) |
| Pagina ufficiale trovata | 1.003 | **1.992** |
| Pagina non trovata | 54 | 490 (193 servizi myCIVIS di Bolzano, 55 Portale UE, 34 Trento "410 Gone", 28 Liguria vietata da robots.txt) |
| Bandi pronti per preliminare e scheda | – | **991**: segnali gratuiti "aperto" 455, "chiuso" 103 (si fermano senza IA), incerti 431 |

**I 193 bandi aperti che il 27/09 nessuna fonte raccoglieva:** ora **151 sono raccolti** (78%): 52 rilevanti con pagina ufficiale trovata, 15 rilevanti con pagina ancora da cercare, 11 rilevanti con pagina non trovata, 73 "da rivedere" in attesa dell'IA. Ne restano fuori 42: 14 della Città metropolitana di Bologna (sono rilanci di bandi di altri enti nella sezione "Progetti d'impresa"), 5 della Regione Abruzzo (nuovo portale non ancora nel registro), 4 dell'anagrafica lombarda via dati.gov.it, 4 Invitalia, 3 Unioncamere Lombardia (sito fermo il 28/09), il resto uno o due per fonte.

## Cosa non è stato fatto

- Regione Marche: l'elenco si pagina con un "postback" (pulsanti della pagina), non con l'indirizzo: si legge solo la prima pagina.
- Comunicati del Comune di Ferrara: vuoti anche col browser. Il bando "Affittami" arriva dalla Camera di Ferrara e Ravenna.
- Sezione economia-imprese della Regione FVG: schede per misura senza un elenco datato.
- Fondazioni Cariplo e Cariverona (Cloudflare): col browser si legge l'elenco, le pagine dei singoli bandi rispondono 403; i bandi sono quasi tutti per enti non profit.
- Bolzano myCIVIS: 193 schede di servizio in un'applicazione JavaScript, pagina ufficiale non leggibile senza browser.

## Sintesi

La lettura della scorta raddoppia i bandi di Bandi Radar (da 1.057 a 2.487) e quelli con pagina ufficiale (da 1.003 a 1.992). Dei 193 bandi aperti del campione che nessuna fonte vedeva, il 78% ora entra. Il collo di bottiglia si sposta sull'IA: 2.845 annunci "da rivedere" (tutto il Portale UE, i cataloghi con titoli senza parole chiave) e 991 bandi da controllare e schedare. I segnali gratuiti ne fermano 103 senza spesa. Il Portale UE ha bisogno della correzione della PR #29: le sue pagine sono vuote senza browser, il testo sta nei dati della ricerca.

## Conseguenze per il registro delle fonti

- Nuove voci (28/09): Invitalia in apertura e "fare impresa", SIMEST strumenti e comunicati, Piemonte pre-informazione, Camera dell'Emilia internazionalizzazione, Verona PID, News della Camera di Cosenza, La Spezia bandi e finanziamenti, notizie di Parma, Unioncamere Veneto bandi di contributi.
- Da valutare: Regione Abruzzo sul nuovo portale (www.regione.abruzzo.it; il vecchio www2 vieta tutto in robots.txt), "Progetti d'impresa" della Città metropolitana di Bologna, Bolzano myCIVIS col browser.
