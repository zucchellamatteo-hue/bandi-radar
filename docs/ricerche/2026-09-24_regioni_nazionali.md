# Regioni, enti nazionali, UE e fondazioni: mappatura con lettura diretta dei siti

**Data:** 24/09/2026
**Domanda:** per ogni Regione e Provincia autonoma, per gli enti nazionali (incentivi.gov.it, MIMIT, Invitalia, GSE, SIMEST, altri ministeri), per il Portale UE e per una selezione di fondazioni bancarie: qual è la pagina, il feed o l'API da far osservare al sistema automatico? Esiste il calendario degli avvisi previsto dall'art. 49 Reg. UE 2021/1060?
**Metodo:** quattro agenti in parallelo (Nord, Centro, Sud e Isole, nazionali/UE/fondazioni) con lettura diretta delle pagine da questa sessione cloud (curl con User-Agent dichiarato, massimo 10-12 richieste per ente). URL riportati solo se aperti davvero con esito 200 o con risposta valida del feed/API. Il risultato è confluito nel registro `fonti/` (file `regioni.yaml`, `nazionali.yaml`, `fondazioni.yaml`, `contesto.yaml`) e ogni indirizzo è stato ricontrollato con `python -m app.fonti.verifica`: 77 raggiungibili su 85 (escluse le voci scartate e quelle senza indirizzo).
**Limiti:** dalla rete della sessione cloud non rispondono incentivi.gov.it, rna.gov.it, regione.campania.it, GSE e MASE (403 Akamai), Marche (bot manager dopo la prima pagina), Cariplo e Cariverona (Cloudflare), FIRA e Sviluppo Italia Molise (intermittenti), ART-ER, AVEPA, Veneto Innovazione, svimarche.it, dati.umbria.it. Sono da riprovare dal server. Nessuna navigazione con browser: i siti a pagina singola (Bolzano, Veneto portale bandi, Sardegna sito regionale, Finlombarda, FILSE) restano "difficili".

## Sintesi complessiva

1. **Tutte le 21 amministrazioni hanno almeno una voce nel registro**, ma con qualità diversa: 15 con pagina o feed pulito e verificato, 6 dove la strada passa da agenzie regionali o da un browser (Bolzano, Veneto, Campania, Marche, Molise, Sardegna).
2. **Le API e i feed valgono più delle pagine**: Lombardia (Socrata), Emilia-Romagna (Plone `++api++`), Trento (OpenCity), Basilicata e Calabria (WordPress `wp-json`), Piemonte, Puglia, Sicilia, Toscana, Lazio, Valle d'Aosta (RSS). Per queste il lettore è quasi gratis e non dipende dall'aspetto del sito.
3. **Il calendario art. 49** è verificato per 12 amministrazioni (Lombardia, Emilia-Romagna, Piemonte, Veneto, Liguria, Valle d'Aosta, Trento, Toscana, Lazio, Sicilia, Calabria in parte, FVG non trovato): anticipa le aperture di mesi ed è quasi sempre un file (XLSX, CSV, PDF) che cambia poche volte l'anno.
4. **Enti nazionali**: MIMIT ha due RSS aggiornati; Invitalia e SIMEST solo HTML; incentivi.gov.it e RNA vanno verificati dal server; GSE e MASE bloccano i server. Il Portale UE risponde via API SEDIA con richiesta POST.
5. **Fondazioni bancarie**: quasi tutte finanziano solo enti non profit. Restano nel registro come "esclusa" con il motivo, per non rivalutarle ogni volta. Da riconsiderare solo Cariplo e Cariverona, non leggibili da qui.
6. **Gli elenchi sono quasi sempre misti** (concorsi, gare, contributi a cittadini): lo smistamento per titolo (Haiku, Fase 3) resta necessario; solo pochi portali (Piemonte, Umbria, Puglia POR, Sicilia, SardegnaImpresa) accettano un filtro "imprese" nell'indirizzo.

## Conseguenze per il registro delle fonti

- 95 voci inserite in `fonti/` (70 regionali, 16 nazionali/UE, 7 fondazioni, 2 di contesto): 60 attive, 17 difficili, 11 da verificare, 7 escluse. Modalità: 26 feed RSS, 12 API, 45 pagine HTML, 12 che richiedono un browser.
- Dal server, a inizio Fase 1: riprovare le voci "da_verificare" e "difficile" elencate sopra e, per le pagine singole, provare il browser senza interfaccia.
- Per i calendari art. 49 basta un controllo settimanale (il file cambia poche volte l'anno).
- Mancano ancora Camere di Commercio e capoluoghi: prossime mappature.

---

# Parte A. Regioni del Nord

# Regioni del Nord: verifica delle pagine bandi (24 settembre 2026)

Enti: Piemonte, Valle d'Aosta, Liguria, Lombardia, Veneto, Friuli Venezia Giulia, Provincia autonoma di Trento, Provincia autonoma di Bolzano, Emilia-Romagna. Le voci pronte per il registro sono in `regioni_nord.yaml` (29 voci).

## Metodo

- Ogni indirizzo è stato aperto con `curl` (timeout 25 s, User-Agent `Mozilla/5.0 (X11; Linux x86_64) BandiRadar/0.1`), leggendo poi il sorgente: link alle schede, etichette di stato, form e filtri, chiamate JavaScript, link RSS.
- Per i portali che caricano l'elenco via JavaScript ho cercato l'endpoint JSON usato dalla pagina e l'ho chiamato direttamente (Veneto, Trento, Bolzano).
- Per i feed/API ho controllato che la risposta fosse XML/JSON/CSV valido e che contenesse date recenti.
- Cataloghi open data provati: Socrata di Lombardia e FVG, CKAN di Bolzano, API Plone di Emilia-Romagna, API OpenCity di Trento.
- Circa 10-15 richieste per ente (Lombardia e Veneto un po' di più per inseguire gli endpoint JavaScript).
- Nel YAML ci sono solo indirizzi aperti davvero con esito 200 (o feed/API con risposta valida). Gli indirizzi "attesi" ma non aperti sono indicati come tali nelle note.

## Limiti

- Non ho un browser: i siti che costruiscono l'elenco in JavaScript sono segnati `difficile` con `modalita: browser`, anche se la pagina risponde 200.
- Tre siti non sono raggiungibili dalla rete di questa sessione (connessione rifiutata, codice 000): ART-ER, AVEPA, Veneto Innovazione. Finaosta risponde 202 con pagina vuota (protezione anti-bot). Vanno riprovati dal server.
- Il calendario art. 49 del PR FESR 2021-2027 del Friuli Venezia Giulia e quello di Bolzano non li ho trovati; ho lasciato una voce `da_verificare` per il FVG.
- Le frequenze seguono l'indicazione ricevuta (giornaliera per LOM, VEN, FVG, PIE, EMR; tre volte a settimana per le altre); per i calendari art. 49, aggiornati al massimo ogni quattro mesi, ho messo `settimanale`.
- Gli elenchi regionali sono quasi sempre misti (cittadini, enti, imprese): dove esiste un filtro nell'indirizzo l'ho usato (Piemonte, Lombardia), altrove il filtro va applicato dopo (FVG, Liguria in POST, Emilia-Romagna per sezione).

## Tabella

| Ente | Pagina trovata | Feed / API | Calendario art. 49 | Esito | Note |
|---|---|---|---|---|---|
| Regione Lombardia | Bandi Online, categoria "Attività produttive e imprese" (HTML, 15 schede con stato) | Socrata `bukx-h2uy` "Anagrafica dei bandi regionali", API SODA senza chiave, aggiornata 01/09/2026 | fesr.regione.lombardia.it, "Calendario degli inviti" con XLSX del 15/05/2026; anche FSE+ | attiva | Nessun RSS. Elenco FESR su ue.regione.lombardia.it via JavaScript. Finlombarda: elenco via JavaScript (difficile) |
| Regione Emilia-Romagna | Portale imprese, "Tutti i bandi" (Plone) | API REST Plone `++api++/@search?portal_type=Bando`: 106 bandi sul portale imprese, 85 sul sito principale, con data di modifica | fesr.regione.emilia-romagna.it, calendario in HTML per mese, con pregresso | attiva | bandi.regione.emilia-romagna.it reindirizza al sito istituzionale. RSS solo a livello di cartelle. ART-ER non raggiungibile |
| Regione Piemonte | bandi.regione.piemonte.it filtrato `destinatari=imprese&stato=aperto` (8 pagine da 20) | RSS `tutti/rss.xml` valido (10 voci, tutte le sezioni) | regione.piemonte.it, PDF "terzo aggiornamento 2026" | attiva | Finpiemonte: /agevolazioni elenco HTML completo, senza stato |
| Regione Veneto | bandi.regione.veneto.it/Public/Elenco?Tipo=1 (tabella via DataTables) | Endpoint JSON `GetListaAttiJson` risponde ma sempre 0 righe; dizionari destinatari/stati ok | venetocoesione.regione.veneto.it/fesr/calendario-inviti: tabella HTML + PDF + CSV ("decimo cronoprogramma", lug-dic 2026) | difficile (portale) / attiva (calendario) | Serve il browser per l'elenco. AVEPA e Veneto Innovazione non raggiungibili |
| Regione FVG | Modulo `MODULI/bandi_avvisi/`: elenco unico di tutti i bandi/avvisi in corso, 13 pagine, molto misto | RSS solo "notizie in evidenza" (valido) | Non trovato per il PR FESR 21-27 (esiste solo quello 2014-2020) | attiva (elenco) / da_verificare (calendario) | Open data FVG senza dataset bandi. Pagine economia-imprese con schede per misura |
| Regione Liguria | `homepage-bandi-e-avvisi/publiccompetitions.html`, filtro imprese+attivi solo in POST; categoria "Bandi PR FESR 2021-2027" (20 schede) | Nessuno | Pagina art. 49 con allegato "versione aggiornata al 22 aprile 2026" | attiva | FILSE: elenco via JavaScript (difficile) |
| Regione Valle d'Aosta | Portale imprese, "Bandi a scadenza" (lista con scadenza e destinatari); sezione Europa "Bandi e avvisi" | RSS del portale imprese (20 voci) e RSS "Notizie Bandi e avvisi" della sezione Europa (20 voci) | new.regione.vda.it, PDF "Calendario preavvisi FESR" (1° agg. 2025) | attiva | regione.vda.it/bandi/ risponde 500. Finaosta protetto (202 vuoto) |
| Provincia di Trento | /Servizi (via JavaScript) ma API OpenCity `opendata/api/content/search/` in JSON: 139 servizi con "bando", 1213 totali | API OpenCity (query nel percorso); CSV dei calendari | Tre dataset con export CSV: FESR (07/08/2026), FSE+ (28/07/2026), FEASR (04/07/2026); il CSV FESR ha titolo, date, importo, beneficiari e link alla scheda | attiva | fesr.provincia.tn.it fermo al 2014-2020. Trentino Sviluppo: solo appalti |
| Provincia di Bolzano | Tutti i siti provinciali sono applicazioni JavaScript con sorgente vuoto (home, economia, europa, news, myCIVIS) | Motore di ricerca interno (siag.it) risponde 400; CKAN data.civis.bz.it senza dataset bandi | Non trovato | difficile | Serve il browser. IDM aperto ma senza elenco bandi |

## Sintesi

1. Sei enti su nove hanno un elenco osservabile in HTML puro o via API (Lombardia, Emilia-Romagna, Piemonte, FVG, Liguria, Valle d'Aosta, più Trento via API); Veneto e Bolzano richiedono il browser senza interfaccia.
2. Le fonti migliori in assoluto sono le API: Socrata di Lombardia (anagrafica con date di apertura e chiusura), Plone di Emilia-Romagna (bandi con data di modifica e link) e OpenCity di Trento (servizi + CSV dei calendari).
3. I calendari art. 49 FESR 2021-2027 sono stati trovati e aperti per 7 enti su 9 (LOM, EMR, PIE, VEN, LIG, VDA, TN); mancano FVG e Bolzano. Quelli di Emilia-Romagna, Veneto e Trento sono già in forma tabellare (HTML/CSV), gli altri sono allegati PDF/XLSX da scaricare.
4. Le agenzie regionali sono deludenti per l'osservazione automatica: Finlombarda e FILSE caricano via JavaScript, Finaosta si protegge, ART-ER/AVEPA/Veneto Innovazione non raggiungibili da qui; solo Finpiemonte ha un elenco HTML. In compenso le loro misure compaiono quasi sempre anche sul portale regionale.
5. Da fare in Fase 1: riprovare dal server i quattro siti non raggiungibili, aggiungere la POST per Liguria, il browser per Veneto/Bolzano/Finlombarda/FILSE, e cercare a mano il calendario FESR del FVG.

---

# Parte B. Regioni del Centro

# Regioni del Centro: verifica delle pagine bandi (24 settembre 2026)

Enti: Regione Toscana, Umbria, Marche, Lazio, Abruzzo, Molise e le rispettive agenzie
(Sviluppo Toscana, Sviluppumbria, SVIM, Lazio Innova / Lazio Europa, FIRA, Sviluppo Italia Molise, Finmolise).
Le voci pronte per il registro sono in `regioni_centro.yaml` (19 voci).

## Metodo

- Ogni indirizzo e' stato aperto con `curl -sSL -m 25 -A "Mozilla/5.0 (X11; Linux x86_64) BandiRadar/0.1"`
  dalla sessione cloud (che esce su internet tramite un proxy), leggendo poi l'HTML scaricato:
  titoli, link, moduli di filtro, riferimenti a RSS/feed, meta "generator" per riconoscere la piattaforma.
- Un indirizzo compare nel YAML **solo se ha risposto 200** (o, per i feed, con un RSS valido).
  I feed sono stati letti per contare le voci e vedere l'ultima data.
- Massimo 10-12 richieste per ente; siti che rifiutano o caricano l'elenco via JavaScript sono segnati
  `difficile` o `da_verificare`, senza inventare indirizzi.
- Frequenze come richiesto (giornaliera TOS/LAZ, tre_a_settimana le altre); per i calendari art. 49,
  che cambiano di rado, ho messo `settimanale`.

## Limiti di questa verifica

- **Marche**: dopo 3 richieste il sito ha rimandato tutto (pagine e feed) a `validate.perfdrive.com`
  (Radware Bot Manager). Le pagine principali sono state viste prima del blocco, i feed no.
- **Abruzzo**: `https://www.regione.abruzzo.it` e `https://www2.regione.abruzzo.it` non passano la
  verifica del certificato (catena incompleta lato server); in **http** rispondono. Gli indirizzi nel
  YAML sono in http: da ricontrollare dal server di produzione.
- **Non raggiungibili dalla sessione** (nessuna risposta o 502 dal proxy): svimarche.it, dati.umbria.it,
  fesr.regione.umbria.it, moliseeuropa.regione.molise.it, finmolise.it; a intermittenza fira.it e
  sviluppoitaliamolise.com. Non e' detto che siano giu': vanno riprovati dal server.
- Nessuna sessione di browser: gli elenchi caricati via JavaScript (Sviluppumbria avvisi, avvisi
  tematici Umbria, FIRA, filtri di Sviluppo Toscana e Lazio Innova) risultano vuoti nell'HTML.
- I portali open data regionali non sono stati esplorati (Umbria irraggiungibile; per gli altri non
  cercato per restare nel limite di richieste).

## Tabella riassuntiva

| Ente | Pagina trovata | Feed/API | Calendario art. 49 | Esito | Note |
|---|---|---|---|---|---|
| Regione Toscana | `regione.toscana.it/bandi-aperti` (elenco misto, 20/pagina) e `pr-fesr-2021-2027/bandi-aperti` (solo FESR, 7 bandi PMI) | nessun RSS regionale; RSS di Sviluppo Toscana `sviluppo.toscana.it/bandi/feed/` | si': `pr-fesr-2021-2027/calendario-delle-opportunita'` con xlsx+csv (csv letto: 92 righe, colonne data apertura/chiusura, tipo richiedente, link) | attiva | Liferay; niente filtro "imprese" nell'URL. Sviluppo Toscana: filtri via JS, feed ok. |
| Regione Umbria | motore bandi `applicazioni.regione.umbria.it/widget/bandi1?...tipoBeneficiario=Imprese` (31 risultati, 20/pagina); `regione.umbria.it/la-regione/bandi` e' solo un iframe | nessuno (solo RSS agenzia stampa) | non trovato (pagina Europa senza link; fesr.regione.umbria.it e dati.umbria.it irraggiungibili) | attiva (motore) / difficile (avvisi tematici) | Sviluppumbria: `/avvisi-pubblici` vuota via JS, la home ha 19 avvisi statici. |
| Regione Marche | `regione.marche.it/Entra-in-Regione/Bandi` (dettagli ?idb=, temi ?t=) e `/Bandi-e-opportunita` (Bandi-attivi, Bandi-in-uscita, Bandi-scaduti) | pagina `/rss` elenca feed per tema (blog=13 Attivita' Produttive) ma il feed e' stato bloccato | probabile in `Bandi-e-opportunita/Bandi-in-uscita` ("pianificazione dei vantaggi economici"), bloccata dal bot manager | difficile | Radware Bot Manager dopo poche richieste; SVIM irraggiungibile. |
| Regione Lazio | `regione.lazio.it/avvisi-e-bandi` e' solo gare/concorsi/aste (esclusa); i bandi sono su `lazioeuropa.it/bandi/` (13 bandi) e `lazioinnova.it/bandi/` (11, 7 aperti) | RSS validi: `lazioeuropa.it/bandi/feed/`, `lazioinnova.it/bandi/feed/`; notizie Giunta `regione.lazio.it/rss-giunta-regionale` | si': `lazioeuropa.it/pr-fesr/calendario-delle-opportunita-di-finanziamento/` (xlsx datati, pagina aggiornata 17/09/2026); FSE+ con pdf fermi al 2024 | attiva | WordPress; filtri destinatari/stato via URL su Lazio Europa (valori non etichettati), via JS su Lazio Innova. |
| Regione Abruzzo | `www2.regione.abruzzo.it/avvisi/contributi-e-finanziamenti` (Drupal 7, con date) — solo in http | RSS della vista `www2.../taxonomy/term/3573/feed` (4 voci, 17/09/2026); notizie `www.regione.abruzzo.it/rss.xml` (Drupal 11) | non trovato; `content/opportunita-di-finanziamento-fesr` e' fermo al POR 2014-2020 | attiva con riserva (https non verificabile) | FIRA: pagina bandi via JS, feed categoria "Bandi e Misure" valido ma misto con misure nazionali; sito intermittente. |
| Regione Molise | nessun elenco bandi: "Consultare bandi e avvisi" porta all'Albo pretorio (URBI esterno); resta la home con le notizie (`.../IDPagina/1`) | nessuno | non trovato (pagine Coesione 2021-2027 e FESR senza link; moliseeuropa irraggiungibile) | difficile | Sviluppo Italia Molise: `/bandi-pubblici/` e `/bandi-pr-molise/` (STEP Molise) aperte ma sito intermittente; Finmolise irraggiungibile. |

## Sintesi

1. Toscana e Lazio sono le fonti migliori: feed RSS validi delle agenzie (Sviluppo Toscana, Lazio Innova, Lazio Europa) piu' un calendario art. 49 vero, in Toscana addirittura in csv scaricabile.
2. Umbria ha un motore di ricerca bandi con filtro "Imprese" nell'indirizzo (31 bandi), ma niente feed e niente calendario art. 49 trovato; Sviluppumbria si osserva dalla home.
3. Marche e' l'unica Regione con un blocco anti-bot attivo: le pagine esistono (compresi "Bandi in uscita" e feed per tema) ma vanno riprovate dal server con ritmo basso o con browser senza interfaccia.
4. Abruzzo si legge solo in http per un problema di certificato lato loro; l'elenco contributi ha un RSS ma e' povero (graduatorie agricole), il portale nuovo non ha ancora un elenco bandi e FIRA e' instabile.
5. Molise e' la fonte piu' debole: nessun elenco bandi sul sito regionale, calendario art. 49 non trovato, agenzia raggiungibile a intermittenza; da coprire soprattutto con fonti nazionali (incentivi.gov.it) e con Sviluppo Italia Molise quando risponde.

---

# Parte C. Regioni del Sud e Isole

# Mappatura fonti: Regioni del Sud e isole (24/09/2026)

Enti: Regione Campania, Regione Puglia, Regione Basilicata, Regione Calabria, Regione Siciliana, Regione Sardegna, con le rispettive societa' regionali (Sviluppo Campania, Puglia Sviluppo, Sviluppo Basilicata, Fincalabra, IRFIS/CRIAS, SFIRS).
Voci YAML pronte per `fonti/regioni.yaml` in `regioni_sud.yaml` (stessa cartella).

## Metodo

- Sessione cloud, rete verso internet tramite proxy. Ogni indirizzo aperto con `curl -sSL -m 25 -A "Mozilla/5.0 (X11; Linux x86_64) BandiRadar/0.1"`, poi lettura del contenuto scaricato (titoli, link, opzioni dei filtri, meta generator) con un piccolo script Python.
- Per ogni ente: home page → link "bandi/avvisi/RSS/feed" → apertura della pagina elenco e dei feed/API trovati → prova dei filtri "imprese" gia' nell'indirizzo → ricerca del calendario art. 49 → sito della societa' regionale. Circa 10-14 richieste per ente.
- Un indirizzo e' riportato nello YAML solo se ha risposto 200 con contenuto sensato (per feed/API: XML o JSON con voci). Dove il sito ha rifiutato o non risponde, `url` e' vuoto e l'indirizzo tentato sta nelle note.
- Piattaforma riconosciuta dal meta `generator` o dalla struttura (`wp-json`, Liferay `p_p_id`, Drupal `f[0]=`, Next.js `__NEXT_DATA__`).

## Limiti

- Non ho un browser: le pagine che caricano l'elenco via JavaScript (Calabria Europa `/bandi/`, Sardegna nuovo sito, sardegnaprogrammazione.it, calendario Calabria) risultano vuote; dove esisteva ho cercato l'API sottostante.
- La rete cloud viene bloccata o non risponde per: regione.campania.it (403 Akamai anche con User-Agent Chrome), sistema.puglia.it (reset), tutti i domini regione.basilicata.it (reset/503, compreso il JSON open data). Vanno riprovati dal VPS: potrebbe essere un blocco geografico o anti-bot verso questa rete.
- I feed sono stati letti ma non seguiti nel tempo: la frequenza di aggiornamento reale si vedra' in Fase 1-2.
- Non ho cercato dentro i portali open data (dati.regione.campania.it risponde ma e' solo una pagina di rimando; dati.regione.basilicata.it non risponde).

## Tabella

| Ente | Pagina trovata | Feed / API | Calendario art. 49 | Esito | Note |
|---|---|---|---|---|---|
| Regione Campania | www.regione.campania.it/regione/it/bandi-e-avvisi: **403 Akamai** (anche home). Alternativa: Sviluppo Campania `/bandi-aperti/` (200) e porfesr.regione.campania.it "Opportunita' di finanziamento" (200, ma ferma al 2014-20) | nessuno: i feed di Sviluppo Campania rispondono 500/403, wp-json 401 | non trovato (sito regionale bloccato) | **difficile** per la Regione, attiva per Sviluppo Campania | Riprovare dal VPS. Sviluppo Campania mescola misure per imprese e avvisi interni |
| Regione Puglia | regione.puglia.it/bandi-e-avvisi (200, ma e' solo un modulo di ricerca via POST); por.regione.puglia.it/bandi-e-avvisi con filtro tema Imprenditoria `?p_r_p_categoryId=61182` (200) | **RSS ufficiale "Regione Puglia - Bandi"** (getRSS Liferay, 50 voci, 200) | non trovato su regione.puglia.it ne' su por.regione.puglia.it | **attiva** (feed + POR) | sistema.puglia.it: reset/503, difficile. Puglia Sviluppo non ha un elenco proprio (solo JTF Taranto e gare) |
| Regione Basilicata | **portalebandi.regione.basilicata.it/avvisi-e-bandi/** (200, WordPress, 16 voci in pagina) | **API JSON** `wp-json/wp/v2/avvisi-e-bandi?per_page=50` (200, 50 voci) e RSS `feed/?post_type=avvisi-e-bandi` (200). Il vecchio JSON opservice: **reset** anche oggi | non verificabile (pr-fesr.basilicata.it non risponde) | **attiva** (portale nuovo) | www.regione.basilicata.it, opservice, dati, europa.basilicata.it: tutti reset/503 dal cloud, come il 23/09. Sviluppo Basilicata: pagina "Incentivi" (200) con le misure gestite |
| Regione Calabria | calabriaeuropa.regione.calabria.it/bandi/ (200 ma elenco via JavaScript); regione.calabria.it/bandi-e-avvisi-di-gara/ (200, misto); Fincalabra "Aiuti alle imprese > Bandi" (200); calabriaimpresa.eu/agevolazioni (200) | **API JSON** Calabria Europa `wp-json/wp/v2/bando?per_page=50` (200, 50 voci); **RSS** regione.calabria.it `feed/?post_type=rc-procedure` (200). Attenzione: RSS `?post_type=bando` di Calabria Europa da' notizie, non bandi | pagina "Calendario Avvisi 21-27" trovata (200) ma il calendario e' un iframe Angular `/fe-inviti/` vuoto senza browser | **attiva** (API + RSS + Fincalabra + Calabria Impresa); calendario difficile | Elenco misto in tutte le fonti: smistare per titolo |
| Regione Siciliana | regione.sicilia.it `.../bandi?f[0]=expired:0` (200, Drupal, gia' filtrato sui non scaduti); euroinfosicilia.it/bandi-e-avvisi-aperti/ (200) | **RSS** euroinfosicilia categoria "Bandi e avvisi aperti" (pulito, 200); **RSS** IRFIS "Misure agevolative" (200). rss.xml della Regione e' generale | **trovato**: euroinfosicilia "Calendario degli inviti a presentare proposte" ex art. 49.2, ultimo aggiornamento 31/05/2026 (allegati) | **attiva** | Filtri verificati sul sito regionale: category:22 (avvisi pubblici), group:12 (attivita' produttive). CRIAS: sito statico fermo al 2018, esclusa |
| Regione Sardegna | regione.sardegna.it/atti-bandi-archivi/atti-amministrativi/bandi (200 ma elenco via GraphQL lato browser: vuoto); **sardegnaimpresa.eu/it/agevolazioni** (200, Drupal, filtri per macrosettore e tipologia nell'indirizzo, ordinabile per scadenza) | nessuno utile: rss.xml di SardegnaImpresa e' rotto (IP interno, voci 2018-2020); SFIRS ha solo feed di notizie | non verificabile: sardegnaprogrammazione.it e' un'app JavaScript vuota senza browser | **attiva** via SardegnaImpresa; sito regionale difficile | SFIRS "Bandi e gare" quasi vuoto: segnale secondario |

## Sintesi

1. Quattro Regioni su sei hanno una fonte leggibile a macchina senza browser: Puglia (RSS ufficiale), Basilicata (API JSON del nuovo Portale Bandi), Calabria (API JSON di Calabria Europa + RSS del sito istituzionale), Sicilia (RSS di EuroInfoSicilia e di IRFIS). Sono da preferire alle pagine HTML.
2. Campania e' l'unico ente senza nulla di verificato dalla Regione: il sito e' protetto da Akamai e rifiuta la rete cloud; va riprovato dal VPS. Nel frattempo Sviluppo Campania (HTML) copre le misure per le imprese.
3. Basilicata: il sito storico e il JSON open data restano irraggiungibili dal cloud (come il 23/09), ma il nuovo portalebandi.regione.basilicata.it risponde bene e ha API e RSS: e' la fonte da usare.
4. Calendario art. 49: verificato solo per la Sicilia (documenti allegati, aggiornamento quadrimestrale); per la Calabria la pagina esiste ma il calendario e' un'app JavaScript; per Puglia, Campania, Basilicata e Sardegna non trovato o non raggiungibile.
5. Tutti gli elenchi sono misti (concorsi, gare, enti locali insieme alle agevolazioni per imprese) e solo Puglia POR, Sardegna Impresa e Sicilia offrono filtri nell'indirizzo: lo smistamento per titolo (Haiku, Fase 3) restera' necessario. Da rifare dal VPS: regione.campania.it, sistema.puglia.it, regione.basilicata.it e opservice, piu' una prova in modalita' browser per Sardegna e per il calendario calabrese.

---

# Parte D. Enti nazionali, UE, cataloghi e fondazioni

# Verifica fonti nazionali, UE, cataloghi e fondazioni — 24 settembre 2026

## Metodo

- Sessione cloud (solo repository, rete tramite proxy). Ogni indirizzo è stato aperto con
  `curl -sSL -m 25 -A "Mozilla/5.0 (X11; Linux x86_64) BandiRadar/0.1"` e poi letto
  (grep di link, titoli, feed). Per i siti che chiudevano la connessione ho provato anche
  WebFetch (altra rete) e la ricerca web per trovare documentazione.
- Al massimo 10-12 richieste per ente; nessun ritentativo aggressivo.
- Negli YAML `url`/`feed_url` sono riportati come aperti davvero (200, o feed/API con risposta
  valida) salvo dove le note dicono esplicitamente "non aperto" (stato `da_verificare` o
  `difficile`).

## Limiti

- **incentivi.gov.it e rna.gov.it** chiudono la connessione (reset) su ogni pagina, WebFetch
  riceve 503: nulla verificato direttamente. Le informazioni sui dati aperti vengono da ricerca
  web e vanno confermate dal server di produzione.
- **GSE, MASE, Fondazione Cariplo, Fondazione Cariverona** rispondono 403 (Akamai/Cloudflare)
  con qualsiasi User-Agent: stato `difficile`.
- **Ministero del Turismo** ha un bot manager Radware: la pagina risponde 200 ma senza link
  leggibili; da riprovare con browser senza interfaccia.
- L'API SEDIA funziona solo con POST multipart e parti dichiarate `application/json`;
  con parti di testo semplice risponde 500 "internal error" (falso negativo facile).

## Tabella

| Ente | Pagina trovata | Feed / API | Esito | Note |
|---|---|---|---|---|
| incentivi.gov.it (ricerca) | /it/cerca-incentivi | — | non raggiungibile (reset) | app JavaScript; da verificare dal server |
| incentivi.gov.it (open data) | /it/open-data | export CSV/JSON in /sites/default/files/open-data/ | non raggiungibile (reset) | da ricerca web: CSV compresso + JSON, IODL 2.0, campi ID_Incentivo, Titolo, Data_apertura/chiusura, Codici_ATECO |
| MIMIT incentivi | /it/incentivi | /it/incentivi?format=feed&type=rss | 200, feed valido (10 voci, 22/09/2026) | Joomla, elenco paginato ~300 schede |
| MIMIT aggiornamenti | /it/incentivi-aggiornamenti | ?format=feed&type=rss | 200, feed valido | decreti, proroghe, sportelli: il più tempestivo |
| Invitalia | /per-le-imprese/incentivi-e-strumenti | nessuno (/rss 404) | 200 | 16 schede con stato Attivo/In apertura/Chiuso nel HTML |
| GSE | — | — | 403 Akamai | difficile; appalti.gse.it è solo gare fornitori |
| SIMEST | /per-le-imprese/finanziamenti-agevolati/ | /feed/ vuoto, wp-json vuoto | 200 | WordPress; strumenti dentro la pagina, osservare il testo intero |
| Fondo di garanzia (MCC) | fondidigaranzia.it/archivio-delle-news/ | /feed/ | 200, feed valido | novità operative, non bandi; mcc.it/feed/ vuoto |
| CDP | /sitointernet/it/imprese.page | — | 200 | esclusa: prodotti finanziari, avvisi via JS, bandi solo di Fondazione CDP |
| MASAF | IDPagina/473 "Gare" | ServeFeed.php .../rss20/feed/pages%3A11 | 200, feed valido (20 voci) | misto appalti + bandi di finanziamento (filiera, mense bio) |
| Ministero del Turismo | /strumenti-di-sostegno/ | /feed/ (rassegna stampa) | 200 ma senza link (Radware) | da_verificare con browser |
| MASE | — | — | 403 Akamai | difficile |
| Portale Funding & Tenders UE | topic-search (app JS) | POST api.tech.ec.europa.eu/search-api/prod/rest/search?apiKey=SEDIA&text=*** | 200, 1088 topic aperti/in apertura | parti multipart `query`, `languages`, `sort` con content-type application/json |
| EISMEA | /funding-opportunities/calls-proposals_en | /node/7/rss_en | 200, feed valido (5) | open call I3, progetti a cascata |
| EIC | /eic-funding-opportunities/calls-proposals_en | /node/21/rss_en | 200, feed valido (2) | Accelerator 2026, STEP Scale Up |
| CINEA / LIFE | /funding-opportunities/calls-proposals_en | /node/161/rss_en | 200, feed valido (10) | pagina LIFE dedicata ferma al 2023 |
| dati.gov.it | /view-dataset | /opendata/api/3/action/package_search | 200, JSON valido | "bandi imprese" → 6 dataset, "incentivi" → 25; nessun dataset RNA o incentivi.gov.it |
| RNA | /open-data, /open-data/aiuti | file XML OpenData_aaaa_mm.xml (Misure e Aiuti) | non raggiungibile (reset) | da ricerca web: aggiornamento settimanale, CC BY 4.0 |
| Fondazione Cariplo | /it/bandi/bandi.html | — | 403 Cloudflare | difficile; da web: bandi 2026 per non profit |
| Compagnia di San Paolo | /it/cosa-facciamo/contributi/ | /it/feed/ | 200 | esclusa: solo enti non profit |
| Fondazione CRT | /progetti-e-bandi/ | /feed/ | 200 | esclusa: non profit, scuole, enti locali |
| Fondazione CR Firenze | /cosa-facciamo/bandi/ | /feed/ | 200 | esclusa: Terzo settore; pagina con "Scadenza:" leggibile |
| Fondazione Friuli | /contributi-e-bandi/bandi-online/ | nessuno (404) | 200 | esclusa: "enti e istituzioni non profit" |
| Fondazione Cariparo | /bandi/ | /feed/ | 200 | esclusa: scuole, non profit |
| Fondazione Cariverona | /bandi/ | — | 403 Cloudflare | difficile |

## Sintesi

1. Le fonti nazionali più solide sono i due feed RSS del MIMIT (incentivi e aggiornamenti), Invitalia in HTML con stato per scheda, SIMEST in HTML e il feed MASAF (misto gare/bandi).
2. L'API SEDIA del portale UE risponde e restituisce campi puliti (identificativo, titolo, stato, date di apertura e scadenza): è la fonte UE da usare, integrata dai feed RSS di EISMEA, EIC e CINEA.
3. incentivi.gov.it e RNA non sono raggiungibili da questa sessione: i dati aperti (CSV/JSON degli incentivi; XML mensili delle misure e degli aiuti) sono documentati ma vanno confermati dal server prima di scrivere i lettori.
4. GSE, MASE, Cariplo e Cariverona bloccano i server automatici (403): servono prove dal server di produzione, eventualmente con browser senza interfaccia; il Ministero del Turismo ha un bot manager.
5. Le fondazioni bancarie verificate finanziano quasi solo enti non profit: cinque su sette sono segnate come escluse con motivo, le altre due restano da verificare.
