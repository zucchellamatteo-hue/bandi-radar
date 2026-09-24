# Camere di Commercio e Comuni capoluogo: mappatura con lettura diretta dei siti

**Data:** 24/09/2026
**Domanda:** per ogni Camera di Commercio (e Unione regionale) e per ogni Comune capoluogo non ancora verificato il 23/09: qual è la pagina, il feed o l'API da far osservare? Ci sono bandi per imprese recenti?
**Metodo:** sette agenti in parallelo (Camere: Nord-Ovest, Nord-Est, Centro, Sud e Isole; capoluoghi: Nord, Centro, Sud e Isole) con lettura diretta delle pagine dalla sessione cloud (curl con User-Agent dichiarato, 6-12 richieste per ente). URL riportati solo se aperti davvero con 200 o con feed/API valido. Risultato nel registro `fonti/camere.yaml` e `fonti/capoluoghi.yaml`; ogni indirizzo ricontrollato con `python -m app.fonti.verifica`: Camere 66 su 69, capoluoghi 85 su 89.
**Limiti:** nessun browser, quindi i siti a pagina singola restano "difficili"; letta solo la prima pagina di ogni elenco, quindi "nessun bando visto" non copre l'anno; robots.txt non controllati (lo farà l'osservatore); frequenze stimate. Bloccano i server dal cloud: Camera di Milano Monza Brianza Lodi (Imperva), Cremona, Mantova, Pavia, Salerno, Bari (solo http), Rieti-Viterbo, Unioncamere Lazio ed Emilia-Romagna; Comuni di Venezia, Parma, Grosseto, Campobasso, Macerata, Rieti, Viterbo, Chieti, Isernia, Benevento, Crotone, Catania, Enna, Milano.

## Sintesi complessiva

1. **Camere di Commercio: 77 voci per 55 Camere e 9 Unioni regionali**, dopo gli accorpamenti (Monte Rosa Laghi Alto Piemonte, Emilia, Toscana Nord-Ovest sono Camere uniche; la "Sicilia Occidentale" non è operativa e le tre Camere restano separate). Quasi tutte usano la distribuzione Drupal di Infocamere con vista `/bandi` e feed `/bandi/rss.xml`, ma solo una decina la riempie davvero: altrove i bandi sono notizie o pagine statiche.
2. **Feed e API "solo bandi" verificati** per: Modena, Ferrara-Ravenna, Firenze, Maremma e Tirreno, Frosinone-Latina, Molise, Marche, Irpinia Sannio, Cagliari-Oristano, Brindisi-Taranto; API Plone per Padova, Verona, Emilia, Umbria. Le altre Camere si leggono in HTML.
3. **Le Unioni regionali contano**: Unioncamere Piemonte e Lombardia pubblicano i bandi "Regione + Camere" (voucher digitalizzazione, fiere, export), spesso prima delle singole Camere.
4. **Comuni capoluogo: 115 voci per tutti i capoluoghi e le Province eccezione.** Bandi per imprese recenti visti a Torino, Biella, Rimini, Firenze, Siena, Pisa, Latina, Nuoro, Città metropolitane di Milano e Torino, oltre a quelli già noti del 23/09 (Roma, Udine, Brescia, Bergamo, Pordenone, La Spezia, Pesaro, Ragusa, Messina, Taranto). Conferma: elenchi misti ovunque, servono filtro per parole chiave e smistamento IA.
5. **Famiglie di piattaforma comunali** (un lettore per famiglia): Municipium (feed `/it/news/feed`, 5 voci, filtro type ignorato), WordPress Design Comuni (feed per categoria), Drupal Design Comuni (feed per tassonomia), OpenCity (HTML `/Novita/Avvisi`), Plone 6 (API `++api++/@search`), myPortal e Angular (browser).
6. **Trappole annotate nel registro**: domini senza `www` o con certificato errato (Trapani, Massa, Napoli, Unioncamere Piemonte), feed dei commenti scambiati per feed degli avvisi (Brindisi), URL che cambiano ogni anno (Cosenza "versoleimprese-bandi-2026"), Rieti-Viterbo che rifiuta gli User-Agent Linux.

## Conseguenze per il registro delle fonti

- Il registro arriva a **287 voci**: 205 attive, 54 difficili, 18 da verificare, 10 escluse; 83 feed RSS, 22 API, 138 pagine HTML, 44 da browser. Più delle ~180 stimate perché molti enti hanno due voci (pagina + feed, o pagina + calendario) e perché i capoluoghi sono tutti dentro, anche quelli a bassa frequenza.
- Dal server, a inizio Fase 1: riprovare le 72 voci `difficile` e `da_verificare`; per le pagine singole provare il browser senza interfaccia.
- Le frequenze restano stime: la Fase 1 le misura.

---

# Parte: camere_nord_ovest

# Camere di Commercio del Nord-Ovest: pagine bandi da osservare

Verifica a mano del 2026-09-24, dal cloud (nessun accesso al server). Voci pronte per `fonti/camere.yaml` in `camere_nord_ovest.yaml`.

## Metodo

- Per ogni Camera: home page con `curl` (User-Agent `BandiRadar/0.1`), lettura dei link con "bandi/contributi/voucher", apertura della pagina elenco, prova di `/rss.xml` (Drupal), `index.php?azione=paginarss` (ISWEB), ricerca Plone. Mai più di 8-10 richieste per ente.
- Un indirizzo è riportato solo se aperto davvero con 200 e con l'elenco leggibile nell'HTML. Se il sito rifiuta o l'elenco manca: `stato: difficile`, `url` vuoto, tentativi nelle note.
- Per i quattro siti irraggiungibili con curl ho riprovato con User-Agent da browser e con WebFetch.

## Limiti

- **Milano Monza Brianza Lodi** è dietro Imperva/Incapsula: risponde 200 ma con la sola pagina di verifica JavaScript. Non osservabile senza browser (e forse nemmeno con).
- **Cremona, Mantova, Pavia** chiudono la connessione senza risposta (http e https, qualunque User-Agent; WebFetch: 503). Stesso hosting, probabile blocco degli indirizzi dei data center. Da riprovare dal server OVH prima di dichiararle escluse.
- I feed `rss.xml` dei siti Drupal camerali esistono quasi ovunque ma sono feed di home page (news, verbali, prenotazioni appuntamenti): in nessun caso un feed dedicato ai bandi. Nessuna API trovata.
- Assetto: **"Biella e Vercelli" e "Novara e VCO" sono un'unica Camera** (Monte Rosa Laghi Alto Piemonte, `pno.camcom.it`) dal 2020: una voce sola. Alessandria-Asti vive su `aa.camcom.it` (il vecchio `al.camcom.it` non risponde). Unioncamere Piemonte va letta su `pie.camcom.it` senza `www` (certificato TLS non valido per `www`).

## Tabella

| Ente | Pagina | Feed/API | Esito | Note |
|---|---|---|---|---|
| CCIAA Torino | https://www.to.camcom.it/finanziamenti-bandi-e-contributi | no (rss.xml 404) | attiva | Drupal 9; pagina testuale con tutte le misure (camerali e non); sotto-pagine /contributi (formazione), /bandi-e-incentivi-il-turismo |
| CCIAA Cuneo | https://www.cn.camcom.it/bandi | rss.xml generico | attiva | Drupal; bandi con codice (2605-2607 anno 2026); pagina pesante con archivio; riepilogo annuale /bandi-camerali-2026-scadenze-partecipazione |
| CCIAA Alessandria-Asti | https://www.aa.camcom.it/bandi | rss.xml generico | attiva | Drupal impaginato (?page=N); bandi regionali 2026 nelle notizie e su Unioncamere Piemonte |
| CCIAA Monte Rosa Laghi Alto Piemonte (BI-VC-NO-VCO) | https://www.pno.camcom.it/promozione/bandi | rss.xml generico e vecchio | attiva | Drupal; unica Camera per le due voci dell'elenco; bv.camcom.gov.it rimanda qui |
| Unioncamere Piemonte | https://pie.camcom.it/bandi-per-imprese | rss.xml generico | attiva | Drupal 9; bandi Regione + Camere (Voucher digitalizzazione PMI 2026, flotte, fiere artigiani) |
| Chambre valdôtaine | https://www.ao.camcom.it/it/far-crescere-l-impresa/bandi-contributi-agevolazioni/bandi-avvisi-chambre-valdotaine-sua-gestione | rss.xml generico | attiva | Drupal; Voucher Doppia Transizione 2026, formazione, fiere |
| CCIAA Genova | https://www.ge.camcom.gov.it/it/gestisci/finanziamenti-e-contributi-per-limpresa | no (search_rss 404) | attiva | Plone; nessun elenco unico; bandi PID in /it/innovazione/pid-punto-impresa-digitale/finanziamenti-innovazione-1; ricerca Plone per data come alternativa |
| CCIAA Riviere di Liguria | https://www.rivlig.camcom.gov.it/contributi-alle-imprese/contributi-camera-di-commercio | rss.xml solo appuntamenti | attiva | Drupal; oggi soprattutto indennizzi calamità + bando Entroterra; voucher nelle notizie |
| CCIAA Milano Monza Brianza Lodi | (nessuna) | — | difficile | Incapsula: tentati /, /it/, /bandi, /bandi-aperti: solo pagina di verifica JS |
| CCIAA Bergamo | https://www.bg.camcom.it/bandi | rss.xml misto (alcune schede /bandi/) | attiva | Drupal; 4 bandi aperti 2026; feed solo come complemento |
| CCIAA Brescia | https://www.bs.camcom.it/bandi-e-contributi/bandi-di-contributo-camerali | rss.xml generico | attiva | Drupal; organizzata per tema (fiere, start up, formazione...), le pagine tematiche cambiano ogni anno: osservare anche le sotto-pagine |
| CCIAA Como-Lecco | https://www.comolecco.camcom.it/pagina478_bandi-aperti.html | no (pagina "RSS" senza feed) | attiva | ISWEB; 6 bandi aperti (Fiere estero, Export su misura, Voucher AI, Nuova Impresa 2026) |
| CCIAA Cremona | (nessuna) | — | difficile | connessione chiusa senza risposta; WebFetch 503; tentati /, /bandi, .gov.it |
| CCIAA Mantova | (nessuna) | — | difficile | idem (mn.camcom.gov.it e mn.camcom.it) |
| CCIAA Pavia | (nessuna) | — | difficile | idem (pv.camcom.gov.it e pv.camcom.it) |
| CCIAA Sondrio | https://www.so.camcom.it/bandi | rss.xml misto, non aggiornato | attiva | Drupal; schede /bando/<anno>/<slug>, elenco include anche i chiusi 2025 |
| CCIAA Varese | https://www.va.camcom.it/pagina737_contributi-ed-agevolazioni.html | no (pagina "RSS" senza feed) | attiva | ISWEB; 5 contributi aperti 2026; filtro area ?ar=N |
| Unioncamere Lombardia | https://www.unioncamerelombardia.it/bandi-e-incentivi-alle-imprese?stato=2 | no | attiva | TYPO3 "modellobando"; ?stato=1 in apertura, =2 aperti, archivio =3; fonte dei bandi Regione + Camere lombarde |

## Sintesi

1. 14 pagine elenco verificate e aperte (200) su 18 enti; 4 Camere lombarde (Milano, Cremona, Mantova, Pavia) non raggiungibili dal cloud: da riprovare dal server OVH, altrimenti coprirle tramite Unioncamere Lombardia.
2. Nessun feed RSS o API dedicato ai bandi: tutte le voci sono `modalita: html`; i `rss.xml` Drupal sono feed di home page e al massimo un complemento (Bergamo, Sondrio).
3. Piattaforme: Drupal (Torino, Cuneo, Alessandria-Asti, Monte Rosa Laghi, Unioncamere Piemonte, Aosta, Riviere, Bergamo, Brescia, Sondrio), Plone (Genova), ISWEB (Como-Lecco, Varese), TYPO3 (Unioncamere Lombardia).
4. Le due Unioncamere regionali sono le fonti più ricche per i bandi "Regione + Camere" (Voucher digitalizzazione PMI 2026 in Piemonte; Fiere, Export su misura, SI4.0, Voucher AI in Lombardia): consiglio frequenza giornaliera per Unioncamere Lombardia finché Milano resta bloccata.
5. Correzioni all'elenco di partenza: Biella-Vercelli e Novara-VCO sono un'unica Camera (Monte Rosa Laghi Alto Piemonte); Alessandria-Asti è su aa.camcom.it; Unioncamere Piemonte solo su pie.camcom.it senza www.

---

# Parte: camere_nord_est

# Camere di Commercio del Nord-Est: mappatura delle pagine bandi

Data verifica: 2026-09-24. Voci pronte per `fonti/camere.yaml` in `camere_nord_est.yaml` (stessa cartella).

## Metodo

- Per ogni Camera: apertura della home con `curl -sSL` e User-Agent `Mozilla/5.0 (X11; Linux x86_64) BandiRadar/0.1`, estrazione dei link con parole chiave (bandi, contributi, voucher, incentivi, rss, feed), riconoscimento del CMS dal meta `generator`, poi apertura della pagina elenco e dei feed candidati. Tra 4 e 9 richieste per ente.
- Un indirizzo è scritto nello YAML solo se ha risposto 200 con contenuto sensato (per i feed: XML con `item`; per le API: JSON con elementi).
- Per i siti Plone 6 Volto (Padova, Verona, Emilia, Unioncamere ER), dove l'HTML arriva senza elenco, è stata provata l'API REST `++api++/@search` con la stessa query che il sito usa nel sorgente.
- Per Treviso-Belluno, irraggiungibile su `tb.camcom.it`, una ricerca web ha indicato il dominio corretto `tb.camcom.gov.it`.

## Limiti

- Verifica di un solo giorno da un container cloud dietro proxy: i due siti "difficili" (Unioncamere ER; tb.camcom.it senza .gov) vanno riprovati dal server.
- Non ho controllato robots.txt delle singole Camere né la frequenza reale di aggiornamento: le frequenze sono quelle richieste (giornaliera Pordenone-Udine, settimanale le altre).
- I feed "generali" (Bologna, Trento, Bolzano, Emilia, Pordenone-Udine) sono stati aperti ma scartati perché non contengono i bandi; è annotato nelle note.
- Le API Plone (Padova, Verona, Emilia) sono URL lunghi con parametri di ricerca: funzionano oggi ma un aggiornamento del sito potrebbe cambiarli.

## Tabella

| Ente | Pagina osservata | Feed/API | Esito | Note |
|---|---|---|---|---|
| CCIAA Venezia Rovigo (dl.camcom.it) | /sonoimpresa/.../incentivi-ed-agevolazioni/contributi | nessuno | attiva, html | elenco per anno; PID in /bandi-attivi; pagine da 700 KB |
| CCIAA Padova | cartella "Bandi contributi e premi 2026" | API `++api++/@search?portal_type=Bando` (132 voci) | attiva, api | Plone Volto, elenchi HTML vuoti; no RSS |
| CCIAA Treviso-Belluno | tb.camcom.gov.it/bandi.asp | nessuno (rss.asp 404) | attiva, html | tb.camcom.it senza .gov rifiuta; elenco misto camerali+regionali+esterni con scadenza |
| CCIAA Verona | /promuovere-impresa-e-territorio/contributi-e-patrocini | API `++api++/@search?path=...` (10 voci) | attiva, api | Plone Volto, HTML vuoto; pochi bandi come pagine fisse |
| CCIAA Vicenza | /bandi-contributivi-e-bandi-di-gara/bandi-contributivi-camera-vicenza/ | Feed-bandi-contributi.xml (200 ma vuoto) | attiva, html | sito PHP su misura; stato nel titolo |
| Unioncamere Veneto | /attivita-e-servizi/attivita/gestione-bandi-regionali/ | /category/bandi/feed/ (RSS WordPress) | attiva, rss | bandi regionali + rilanci delle Camere (doppioni) |
| CCIAA Pordenone-Udine | /contributi-e-rendicontazione + /news | nessuno utile (/rss.xml elenca nodi tecnici) | attiva, html, giornaliera | i bandi aperti sono le voci del menu; chiusi -> "in rendicontazione" |
| CCIAA Venezia Giulia | vg.camcom.it/contributi-e-agevolazioni | /rss.xml (notizie, valido) | attiva, html + rss notizie | Drupal 10; misure delegate Regione FVG, Fondo Gorizia, PID |
| CCIAA Trento | /imprenditore/impresa-digitale-pid/bandi-contributi | /rss.xml solo eventi | attiva, html | Drupal 9; 2 bandi 2026 |
| CCIAA Bolzano | /it/amministrazione-trasparente/sovvenzioni-contributi-sussidi-vantaggi-economici | /it/rss.xml misto, bilingue | attiva, html | Drupal 10; voucher digitalizzazione e internazionalizzazione |
| CCIAA Bologna | /it/promozione-interna/contributi-della-camera-di-bologna | /rss.xml generale | attiva, html | Drupal 7; pagina a fisarmonica con stato "bando chiuso" |
| CCIAA Modena | /promozione/contributi-camerali/contributi-camerali-bandi-attivi | .../bandi-attivi/RSS (RDF, 5 bandi) | attiva, rss | Plone + redturtle.bandi: feed pulito dei soli bandi aperti |
| CCIAA dell'Emilia (PR, PC, RE) | /promuovere-limpresa-e-il-territorio/contributi-alle-imprese | API `++api++/@search?Subject=CONTRIBUTICAMERALI` (17 bandi) | attiva, api | accorpamento: pr/pc/re.camcom.it -> emilia.camcom.it; /RSS generale |
| CCIAA Ferrara e Ravenna | /bandi | /rss.xml (solo /bandi/, 10 voci) | attiva, rss | Drupal 9; descrizione completa nel feed |
| CCIAA della Romagna (FC, RN) | /it/opportunita/finanziamenti-1 | nessuno | attiva, html | portale su misura (Yii/AMOS) |
| Unioncamere Emilia-Romagna | /internazionalizzazione-delle-imprese/bandi | non raggiunti (/rss-feed, ++api++) | difficile | TLS reset intermittente; elenco bandi via JS; Digital Export ora sulle Camere |

## Sintesi

1. Tutte le 15 Camere del Nord-Est hanno una pagina bandi aperta e leggibile; 18 voci in totale (una per Camera, più feed/notizie per Pordenone-Udine, Venezia Giulia e le due Unioncamere).
2. Cambio di assetto da segnalare: Parma, Piacenza e Reggio Emilia sono oggi la "Camera di Commercio dell'Emilia" (emilia.camcom.it); Treviso-Belluno risponde solo su tb.camcom.gov.it.
3. Feed davvero utili solo in tre casi: Modena (RSS dei bandi attivi), Ferrara-Ravenna (RSS dei /bandi), Unioncamere Veneto (categoria Bandi); gli altri RSS sono notizie generali.
4. Tre siti Plone Volto (Padova, Verona, Emilia) hanno l'HTML vuoto ma un'API JSON aperta che restituisce i bandi con data: modalità `api`.
5. Unica fonte difficile: Unioncamere Emilia-Romagna (connessioni interrotte, elenco via JavaScript); poco grave perché i suoi bandi (Digital Export) sono pubblicati dalle singole Camere.

---

# Parte: camere_centro

# Camere di Commercio del Centro: mappatura delle pagine bandi

Verifica del 2026-09-24, dalla sessione cloud. Registro proposto in `camere_centro.yaml` (15 voci).

## Metodo

- Per ogni Camera: home page con `curl -sSL -m 25 -A "Mozilla/5.0 (X11; Linux x86_64) BandiRadar/0.1"`, lettura dei link con "bandi/contributi/voucher", apertura della pagina elenco, prova dei feed dichiarati nel codice (`<link rel="alternate">`) e di quelli tipici della piattaforma riconosciuta (`/rss.xml`, `/bandi/rss.xml`, `/RSS`, `rss.php`, `wp-json`, `++api++`).
- Ogni indirizzo scritto nel YAML è stato aperto davvero con risposta 200 (o JSON/XML valido). Nessun indirizzo ricostruito a memoria.
- Tra 5 e 10 richieste per ente. Per i tre siti irraggiungibili con curl (Rieti-Viterbo, Gran Sasso, Molise) ho usato una ricerca web per trovare il dominio giusto o un User-Agent alternativo.
- File temporanei nella sottocartella `cc_centro/` dello scratchpad.

## Limiti

- Verifica di un solo giorno: il numero di bandi "aperti" cambia; conta la struttura, non il conteggio.
- Unioncamere Lazio non è stato letto (captcha): non so se pubblica un elenco proprio.
- Per Umbria l'elenco HTML non è nel codice sorgente: ho verificato l'API, non ho provato un browser.
- Rieti-Viterbo si apre solo con User-Agent "Windows": l'osservatore dovrà permettere un User-Agent per fonte.
- Non ho controllato robots.txt: da fare prima di attivare l'osservatore.

## Tabella

| Ente | Pagina | Feed/API | Esito | Note |
|---|---|---|---|---|
| Firenze | /bandi (Drupal 10, filtro `field_bando_stato_value=aperto`) | /bandi/rss.xml (8 voci, 22/06/2026) | attiva (rss) | modello Drupal "camcom" |
| Arezzo-Siena | /notizie?field_notizia_categoria_tid=195 (Drupal 7) | /notizie/rss.xml esiste ma ignora la categoria | attiva (html) | bandi pubblicati come notizie |
| Lucca, Massa-Carrara, Pisa → Toscana Nord-Ovest | tno.camcom.it/bandi/bandi-aperti (Drupal 9) | nessuno (/rss.xml 404, /bandi 403) | attiva (html) | i tre vecchi siti rimandano a tno.camcom.it |
| Pistoia-Prato | /servizi/contributi/index (sito su misura) | /rss/rss.xml generale, 2.150 voci: sconsigliato | attiva (html) | anche NewsBandi mensile in PDF |
| Maremma e Tirreno | /bandi (Drupal 11, filtro "aperto") | /bandi/rss.xml (10 voci, 31/07/2026) | attiva (rss) | modello Drupal "camcom" |
| Unioncamere Toscana | unioncamere-toscana.it/news/ (WordPress) | /feed/ (10 voci, 15/09/2026), wp-json aperta | da_verificare | nessuna sezione bandi propria (categoria vuota) |
| Umbria | /promuovere-limpresa-e-il-territorio/bandi-e-contributi (Plone 6) | `++api++/@search?portal_type=Bando…` (53 bandi, con scadenza) | attiva (api) | HTML senza elenco nel sorgente; RSS 1.0 disordinato |
| Marche | /fai-crescere-la-tua-impresa/bandi-e-contributi (Plone, redturtle.bandi) | …/bandi-e-contributi/rss.xml (15 voci, 07/07/2026) | attiva (rss) | vecchio URL /strumenti-e-servizi reindirizza |
| Roma | pagina82_avvisi-pubblici-bandi… (IsWeb) | rss.php?id=4 "Focus" solo parziale | attiva (html) | ~20 voci, alcune non per imprese |
| Frosinone-Latina | /bandi (Drupal 9, filtro "aperto") | /bandi/rss.xml (10 voci, 08/07/2026) | attiva (rss) | modello Drupal "camcom" |
| Rieti-Viterbo | /it/attivita_34/supporto-alle-imprese_433/ (CMS proprietario) | nessuno | difficile | reset con UA Linux/BandiRadar, 200 con UA Windows; elenco povero |
| Unioncamere Lazio | unioncamerelazio.it | — | difficile | 202 + captcha SiteGround; un fetch alternativo ha ricevuto 301 verso dominio estraneo |
| Chieti-Pescara | pagina189754_bandi.html (ePORTAL) | nessuno (/rss.xml 404) | attiva (html) | annate 2025/archivio in pagine separate |
| Gran Sasso d'Italia | cameragransasso.camcom.it/it/la-camera/promozione-economica/bandi/ (IsWeb) | rss.php?id=1..4 vuoti | attiva (html) | gransasso.camcom.it e cciaagransasso.camcom.it non risolvono |
| Molise | molise.camcom.gov.it/bandi (Drupal 9, filtro "aperto") | /bandi/rss.xml (10 voci, 17/07/2026) | attiva (rss) | molise.camcom.it ha certificato errato |

## Sintesi

1. Nomi cambiati: Lucca, Massa-Carrara e Pisa non esistono più come Camere separate, oggi sono la **Camera di Commercio della Toscana Nord-Ovest** (tno.camcom.it): una sola voce al posto di tre. Gli altri nomi dell'elenco sono confermati.
2. Cinque Camere (Firenze, Maremma e Tirreno, Frosinone-Latina, Molise e, con varianti, Toscana Nord-Ovest) usano lo stesso modello Drupal "camcom" di Infocamere: pagina `/bandi` con filtro `field_bando_stato_value=aperto` e feed `/bandi/rss.xml` dei soli bandi. Chi scrive l'osservatore può trattarle con un'unica regola.
3. Feed o API puliti trovati per 7 enti su 15 (4 Drupal, Marche Plone RSS, Umbria Plone REST API, Unioncamere Toscana WordPress); per gli altri si osserva la pagina HTML.
4. Due fonti "difficili": Rieti-Viterbo (accetta solo User-Agent da browser Windows, elenco povero: il voucher doppia transizione 2026 non c'è nella pagina) e Unioncamere Lazio (captcha). Unioncamere Toscana non ha una sezione bandi propria: bassa priorità.
5. Domini da correggere rispetto alle attese: Molise su `molise.camcom.gov.it` (il `.camcom.it` ha certificato sbagliato), Gran Sasso su `cameragransasso.camcom.it`, Unioncamere Toscana su `unioncamere-toscana.it`.

---

# Parte: camere_sud

# Camere di Commercio del Sud e delle Isole — mappatura delle pagine bandi (2026-09-24)

## Metodo

- Per ogni Camera: apertura della home con `curl -sSL` (User-Agent "Mozilla/5.0 … BandiRadar/0.1", timeout 25 s), lettura dei link del menu che contengono "bandi / contributi / voucher / promozione", apertura della pagina elenco, prova dei feed standard della distribuzione Drupal di Infocamere (`/rss.xml`, `/bandi/rss.xml`, `/notizie/rss.xml`) o WordPress (`/feed/`, `/category/…/feed/`), controllo delle etichette Aperto/Chiuso e della data dell'ultima voce del feed. Massimo 8-10 richieste per ente.
- Dove curl falliva (connessione chiusa, DNS, TLS) ho riprovato con host alternativi (`.gov.it`, senza `www`) e, per tre siti, con un secondo strumento di lettura pagine e con il motore di ricerca per trovare il dominio giusto.
- Un indirizzo è riportato nello YAML solo se ha risposto 200 (o feed con XML valido). Le date "ultima voce" vengono dal `pubDate` del feed.
- File temporanei nella sottocartella `sud/` dello scratchpad.

## Limiti

- Il traffico passa da un proxy: alcuni rifiuti (Bari in HTTPS, Nuoro, home di Catanzaro) possono dipendere dal proxy o da un blocco geografico e vanno riprovati dal server di produzione.
- Salerno serve pagine vuote e 403 ai server: contenuti non verificabili senza browser.
- Non ho verificato i feed che non ho aperto (es. RSS di Nuoro).
- Le Camere usano quasi tutte la distribuzione Drupal di Infocamere ("camcom"), che prevede una vista `/bandi` con feed `/bandi/rss.xml`: **solo 3 Camere su 20 la riempiono davvero** (Irpinia Sannio, Cagliari-Oristano e, come tassonomia, Brindisi-Taranto). Le altre pubblicano i bandi come notizie o pagine statiche.

## Assetto degli enti

- Nomi confermati: Napoli, Salerno, Caserta, Irpinia Sannio; Bari, Brindisi-Taranto, Foggia, Lecce; Basilicata; Cosenza, Catanzaro Crotone Vibo Valentia, Reggio Calabria; Palermo Enna, Sud Est Sicilia (CT-RG-SR), Messina; Cagliari-Oristano, Nord Sardegna (Sassari), Nuoro.
- **Agrigento, Caltanissetta, Trapani: l'accorpamento del 2015 non è operativo.** Le tre Camere hanno siti, feed e bandi propri (Agrigento: Bando voucher PID 2026; Caltanissetta e Trapani: Bando Doppia Transizione 2026). Vanno tenute come tre fonti.
- Domini "non ovvi": Brindisi-Taranto = `brta.camcom.it`; Catanzaro Crotone Vibo = `czkrvv.camcom.it`; Sud Est Sicilia = `ctrgsr.camcom.gov.it`; Caltanissetta = `cameracommercio.cl.it`; Napoli = `na.camcom.it` senza www (il certificato di www.na.camcom.it non è valido).

## Tabella

| Ente | Pagina elenco | Feed / API | Esito | Note |
|---|---|---|---|---|
| CCIAA Napoli | https://na.camcom.it/notizie (la vista /bandi è vuota) | https://na.camcom.it/rss.xml (10 voci, 17/09/2026) | attiva (rss) | Drupal 9 camcom; bandi pubblicati come notizie |
| CCIAA Salerno | — | /rss.xml e /bandi/rss.xml validi ma vuoti | **difficile** | Drupal 10 camcom; menu e viste vuote, schede 403 "Accesso negato" |
| CCIAA Caserta | https://www.ce.camcom.it/bandi-incentivi | https://www.ce.camcom.it/rss.xml (10 voci, 28/08/2026) | attiva (html + rss) | Drupal 7 camcom; pagina statica con PDF dei bandi |
| CCIAA Irpinia Sannio | https://www.irpiniasannio.camcom.it/bandi (Aperto/Chiuso) | https://www.irpiniasannio.camcom.it/bandi/rss.xml (3 voci, 03/07/2026) | attiva (rss) | Drupal 9 camcom; vista bandi usata davvero |
| CCIAA Bari | http://www.ba.camcom.it/info/bandi (solo HTTP) | nessuno | **difficile** | HTTPS chiude la connessione; le sottopagine reindirizzano in HTTPS |
| CCIAA Brindisi-Taranto | https://www.brta.camcom.it/taxonomy/term/589 | https://www.brta.camcom.it/taxonomy/term/589/feed (10 voci, 22/09/2026) | attiva (rss) | Drupal 10; tassonomia "Bandi" delle notizie |
| CCIAA Foggia | https://www.fg.camcom.it/bandi-contributi/bandi-sostegno-imprese | nessuno dedicato (/rss.xml 1 voce) | attiva (html) | Drupal 9; elenco per anno, bandi 2026 presenti |
| CCIAA Lecce | https://www.le.camcom.it/promozione-e-sviluppo-del-territorio/bandi-e-contributi | /rss.xml generale (10 voci, 24/09/2026); /bandi/rss.xml solo voce di test | attiva (html) | Drupal 10 camcom; pagina statica, ultimi bandi 2025 |
| CCIAA Basilicata | https://www.basilicata.camcom.it/promozione | /rss.xml generale (10 voci, 21/05/2026) | attiva (html) | Drupal 10 camcom; /bandi e /avvisi-bandi solo scaduti |
| CCIAA Cosenza | https://www.cs.camcom.it/it/content/service/versoleimprese-bandi-2026 | /it/rss.xml fermo a 05/2024 | attiva (html) | Drupal 10 camcom; tabella annuale, URL cambia ogni anno |
| CCIAA Catanzaro Crotone Vibo | https://czkrvv.camcom.it/promuovi-limpresa/bandi-e-contributi/ | https://czkrvv.camcom.it/category/bandi/bandi-promozione/feed/ (10 voci, 11/09/2026) | attiva (rss) | WordPress; home e /category/bandi/ rifiutano la connessione |
| CCIAA Reggio Calabria | https://www.rc.camcom.gov.it/opportunita (paginata) | /rss.xml generale (10 voci, 24/09/2026) | attiva (html) | Drupal 10 camcom; schede /bandi-e-avvisi/… |
| CCIAA Palermo Enna | https://www.paen.camcom.it/it (home con avvisi 2026) | /it/rss.xml fermo a 11/2024 | da_verificare | Drupal 9 camcom; /it/bandi vuota, pagina PID non raggiunta |
| CCIAA Sud Est Sicilia | https://ctrgsr.camcom.gov.it/it/blog | https://ctrgsr.camcom.gov.it/it/rss.xml (10 voci, 23/09/2026) | attiva (rss) | Drupal 7 camcom; bandi voucher turismo 2026 come notizie |
| CCIAA Messina | https://www.me.camcom.it/notizie | https://www.me.camcom.it/rss.xml (10 voci, 27/07/2026); /bandi/rss.xml = gare | attiva (rss) | Drupal 7 camcom; pochi bandi propri |
| CCIAA Agrigento | https://www.ag.camcom.it/tag_servizio/voucher/ | https://www.ag.camcom.it/tag_servizio/voucher/feed/ (8 voci, 11/07/2026) | attiva (rss) | WordPress; Bando voucher PID 2026 |
| CCIAA Caltanissetta | https://www.cameracommercio.cl.it/amministrazione-trasparente-main/bandi-in-corso/bandi-in-corso/ | nessuno | attiva (html) | CMS proprietario (IIS); Bando Doppia Transizione 2026 |
| CCIAA Trapani | https://www.tp.camcom.it/notizie | /rss.xml fermo a 09/2022 | attiva (html) | Drupal 9 camcom; /bandi contiene solo schede di prova |
| CCIAA Cagliari-Oristano | https://www.caor.camcom.it/bandi (Aperto/Chiuso) | https://www.caor.camcom.it/bandi/rss.xml (10 voci, 26/08/2026) | attiva (rss) | Drupal 9 camcom; vista bandi usata davvero |
| CCIAA Nord Sardegna (Sassari) | https://www.ss.camcom.it/promozione-del-territorio/contributi | /rss.xml generale (10 voci, 22/09/2026) | attiva (html) | Drupal 10 camcom; /bandi solo "test-bando" |
| CCIAA Nuoro | https://nu.camcom.it/it/camera/bandi/ (aperta solo col secondo strumento) | RSS in menu, non verificato | da_verificare | CMS proprietario; curl via proxy non arriva al sito |
| Unioncamere Puglia | https://www.unioncamerepuglia.it/category/eventi-ed-iniziative/bandi-e-finanziamenti/ | …/bandi-e-finanziamenti/feed/ (12 voci, 17/04/2026) | attiva (rss) | WordPress; pochi avvisi, anche gare |
| Unioncamere Sicilia | https://unioncameresicilia.it/c/bandi/ | https://unioncameresicilia.it/c/bandi/feed/ (10 voci, 07/07/2026) | attiva (rss), bassa priorità | WordPress; quasi solo gare e selezioni proprie |
| Unioncamere Campania | https://www.unioncamere.campania.it/ | /rss.xml fermo a 01/2023 | esclusa | Drupal 7 non aggiornato |
| Unioncamere Sardegna | https://unioncameresardegna.it/ | solo /feed/ generale | esclusa | WordPress istituzionale senza bandi |

## Sintesi

1. 26 voci nello YAML: 20 Camere (una voce ciascuna, due per Caserta) e 4 Unioni regionali; 16 fonti attive, 2 da verificare (Palermo Enna, Nuoro), 2 difficili (Salerno, Bari), 2 escluse (Unioncamere Campania e Sardegna).
2. Feed usabili subito in 11 casi: Irpinia Sannio, Cagliari-Oristano e Brindisi-Taranto hanno un feed "solo bandi"; Napoli, Caserta, Sud Est Sicilia, Messina, Catanzaro, Agrigento, Unioncamere Puglia e Sicilia hanno feed di notizie o categorie da filtrare per "bando/voucher/contributi".
3. La distribuzione Drupal Infocamere è quasi ovunque, ma la vista `/bandi` è spesso vuota o di prova: la pagina giusta è quasi sempre in "Promozione" o nelle notizie, e va scelta a mano.
4. Siti da riprovare dal server di produzione: Bari (HTTPS rifiuta), Nuoro (proxy), Salerno (403 ai server), home di Catanzaro. Palermo Enna richiede un browser per trovare la pagina dei bandi PID.
5. Assetto: la Camera "Sicilia Occidentale" (Agrigento-Caltanissetta-Trapani) non esiste ancora in pratica; Cosenza cambia indirizzo ogni anno (`versoleimprese-bandi-<anno>`), da aggiornare a gennaio.

---

# Parte: capoluoghi_nord

# Capoluoghi del Nord e Province eccezione - mappatura del 24/09/2026

## Metodo

- Sessione nel cloud, senza browser: ogni sito e' stato aperto con `curl` (User-Agent `Mozilla/5.0 (X11; Linux x86_64) BandiRadar/0.1`, timeout 25 s, redirect seguiti), al massimo 6-8 richieste per ente.
- Per ogni ente: home page per riconoscere la piattaforma e i link "Novita' > Avvisi"; poi la pagina elenco degli avvisi; poi il feed o l'API tipici della piattaforma (Municipium `/it/news/feed`, WordPress `/feed/` di categoria, Plone `++api++/@search`, OpenCity `/opendata/api`, Drupal `/rss.xml`).
- Un indirizzo entra nel registro solo se ha risposto 200 con contenuto vero (o feed/API valido). Se il sito rifiuta o l'elenco e' vuoto perche' caricato via JavaScript: `stato: difficile`, `url` vuoto (o la sitemap, come per Gorizia), indirizzo tentato nelle note.
- I titoli visti sono quelli della prima pagina dell'elenco (10-25 voci), quindi la colonna "bandi imprese visti" dice cosa c'e' oggi, non cosa l'ente pubblica in un anno.

## Limiti

- Nessuna verifica col browser: i 10 siti a pagina singola (myPortal Veneto, my-render-library Lepida, Angular Padova, Next.js Ferrara) restano da provare dal VPS con il browser senza interfaccia.
- Venezia (Incapsula 403) e Parma (TLS fallisce) potrebbero rispondere dal VPS come e' successo per Milano: riprovare prima di dichiararli persi.
- Sui siti Municipium il feed `/it/news/feed` sembra unico: con `?type=3` restituisce le stesse notizie generali, quindi il filtro per tipo va fatto a valle con parole chiave.
- Le frequenze sono stime da tarare a fine Fase 2, come previsto dal piano.

## Tabella

| Ente | Pagina | Feed / API | Piattaforma | Bandi imprese visti (2025-26) | Esito |
|---|---|---|---|---|---|
| Comune di Torino | /novita/avvisi | no (rss.xml solo suolo pubblico eventi) | Drupal 9 | Agevolazioni canone unico per cantieri, immobile uso commerciale, dehors | attiva, settimanale |
| Comune di Cuneo | /notizie-tipi/avvisi/ | RSS categoria | WordPress Design Comuni | Fiera del Marrone adesioni, saldi, albo operatori economici | attiva, quindicinale (server instabile) |
| Comune di Asti | /novita/avvisi | no | Drupal 9 | sponsorizzazioni Palio | attiva, quindicinale |
| Comune di Alessandria | /novita/avvisi | no | Drupal 9 | nessuno | attiva, mensile |
| Comune di Novara | /novita/avvisi | no | Drupal 9 | nessuno (solo viabilita') | attiva, mensile |
| Comune di Vercelli | /novita/avvisi | no | Drupal 9 | nessuno | attiva, mensile |
| Comune di Biella | /tipi_notizia/avvisi/ | RSS categoria | WordPress Design Comuni | Contributi straordinari attivita' economiche quartieri collinari | attiva, quindicinale |
| Comune di Verbania | /Novita/Avvisi | no (opendata/api 410) | OpenCity | nessuno | attiva, mensile |
| Comune di Aosta | /it/news?type=3 | /it/news/feed (unico) | Municipium | nessuno | attiva, mensile |
| Comune di Genova | /novita/avvisi | no (rss 404) | Drupal 11 | avvisi a operatori commerciali fiere, patrocini con contributo | attiva, settimanale |
| Comune di Savona | /it/news?type=3 | /it/news/feed (unico) | Municipium | operatori economici per colonnine di ricarica | attiva, quindicinale |
| Comune di Imperia | /it/news?type=3 | /it/news/feed (unico) | Municipium | nessuno | attiva, mensile |
| Comune di Venezia | - | - | ? (Incapsula) | non verificabile | difficile, 403 |
| Comune di Padova | sitemap.xml | - | Angular (SPA) | in sitemap: bando L'Italia delle donne, manifestazioni d'interesse | difficile, browser |
| Comune di Verona | /Novita/Avvisi | no (opendata/api 410) | OpenCity | contributi a famiglie e associazioni, non a imprese | attiva, quindicinale |
| Comune di Vicenza | /Novita/Avvisi | no | OpenCity | nessuno | attiva, mensile |
| Comune di Treviso | - | - | myPortal | non verificabile | difficile, SPA |
| Comune di Belluno | - | - | myPortal | non verificabile | difficile, SPA |
| Comune di Rovigo | - | - | myPortal | non verificabile | difficile, SPA |
| Comune di Trento | /Novita/Avvisi | no | OpenCity | nessuno | attiva, quindicinale |
| Comune di Bolzano | /Novita/Avvisi | no | OpenCity | bandi WE, Youth In Action, contributi associazioni, concessioni immobili | attiva, quindicinale |
| Comune di Bologna | sitemap.xml | - | myPortal Lepida (SPA) | in sitemap: /argomenti/economia/imprese, /novita/avvisi | difficile, browser |
| Comune di Modena | /novita/avvisi | ++api++/@search (JSON) | Plone 6 Volto | spettacolo viaggiante, fiere, aste | attiva, settimanale |
| Comune di Parma | - | - | ? | non verificabile | difficile, TLS |
| Comune di Reggio Emilia | /novita/avvisi | ++api++/@search e /RSS | Plone 6 Volto | nessuno (viabilita', nidi, affitto) | attiva, quindicinale |
| Comune di Ferrara | /it/novita/avvisi (vuota) | - | Next.js | non verificabile | difficile, browser |
| Comune di Ravenna | /novita/ | no (feed categoria 404, /feed/ vuoto) | WordPress Design Comuni | bando affitto, asta concessione Casa Melandri (comunicati) | attiva, quindicinale |
| Comune di Forli' | /it/news?type=3 | /it/news/feed (unico) | Municipium | sponsorizzazioni Forli' che Brilla | attiva, quindicinale |
| Comune di Rimini | /amministrazione/bandi/bandi-contributi | no | Drupal 10 | contributi manifestazioni, grandi eventi, progetti turistici, festival | attiva, quindicinale |
| Comune di Piacenza | /it/news?type=3 | /it/news/feed (unico) | Municipium | istanza colonnine di ricarica | attiva, quindicinale |
| Provincia di Belluno | - | - | myPortal | non verificabile | difficile, SPA |
| Provincia di Treviso | /bandi-concorsi-e-avvisi/avvisi | no | Joomla | solo contributi a Comuni ed enti culturali | esclusa |
| Citta' metropolitana di Bologna | sitemap.xml | - | myPortal Lepida (SPA) | in sitemap: "Vetrina - spazi che diventano impresa" call e graduatoria | difficile, browser |
| Citta' metropolitana di Milano | /novita/ | no | CMS proprietario | contributi ai commercianti Metrotranvia Milano-Seregno (set. 2026) | attiva, mensile |
| Citta' metropolitana di Torino | /sviluppo-economico/attivita-produttive-e-innovazione | no | Drupal 10 | misura InnoSocialMetro (imprese sociali) | attiva, mensile |

## Sintesi

1. 35 enti: 24 voci attive, 10 difficili (siti a pagina singola o bloccati), 1 esclusa (Provincia di Treviso, contributi solo a Comuni ed enti culturali).
2. Le piattaforme si ripetono: Drupal Design Comuni (Piemonte, Genova, Rimini), OpenCity (Verona, Vicenza, Trento, Bolzano, Verbania), Municipium (Aosta, Savona, Imperia, Forli', Piacenza), Plone Volto con API JSON (Modena, Reggio Emilia), WordPress Design Comuni con RSS (Cuneo, Biella, Ravenna).
3. I bandi per il commercio veri e propri sono rari nella prima pagina: li ho visti a Torino (canone unico per cantieri), Biella (attivita' economiche quartieri collinari), Rimini (contributi eventi e turismo), Citta' metropolitana di Milano (commercianti Metrotranvia) e, in sitemap, Bologna e Citta' metropolitana di Bologna.
4. Il Veneto e' il buco piu' grosso: Venezia bloccata, Padova, Treviso, Belluno, Rovigo e Provincia di Belluno sono applicazioni JavaScript; servono browser senza interfaccia o le API interne di myPortal, da cercare dal VPS.
5. Da riprovare dal server prima di arrendersi: Venezia (403 Incapsula), Parma (TLS), Cuneo (connessioni chiuse a intermittenza), Verbania (timeout al primo tentativo).

---

# Parte: capoluoghi_centro

# Capoluoghi del Centro: mappatura delle pagine avvisi/bandi (24/09/2026)

## Metodo

- Lettura diretta da server con `curl -sSL -m 20 -A "Mozilla/5.0 (X11; Linux x86_64) BandiRadar/0.1"`, al massimo 6-8 richieste per ente.
- Per ogni Comune: home per riconoscere la piattaforma, poi la pagina elenco avvisi secondo la famiglia del sito
  (Municipium `/it/news?type=3` e `/it/news/feed`; WordPress Design Comuni `/tipi_notizia/avvisi/` e `/feed/`;
  Drupal Design Comuni `/novita/avvisi` o `/tipi-di-notizia/avvisi` e il feed della tassonomia; OpenCity `/Novita/Avvisi` e `/opendata/api`).
- Un indirizzo entra nel registro solo se ha risposto 200 con contenuto reale (o feed/API valido). Titoli letti dall'HTML scaricato,
  cercando parole chiave (imprese, commercio, botteghe, centro storico, contributo).

## Limiti

- Sette siti non rispondono al server: Grosseto e Campobasso danno 403 a tutto; Macerata, Rieti, Viterbo, Chieti e Isernia chiudono la
  connessione (Rieti, Viterbo e Chieti erano gia' bloccati il 23/09). Frosinone invece il 24/09 risponde. Per questi sette la voce e'
  `difficile` con `url` vuoto: vanno riprovati dal VPS (IP diverso) o con il browser.
- L'Aquila e' un'applicazione Angular con backend Strapi: l'HTML e' vuoto e i nomi delle collezioni API non sono stati trovati (tre tentativi 404).
- I feed Municipium (Livorno, Pistoia, Ancona, Teramo) hanno solo 5 voci e mescolano tutte le news; i feed WordPress di Lucca, Perugia,
  Frosinone e Pescara sono vuoti o rimandano alla home, quindi per quei siti si osserva l'HTML.
- Per Pisa l'API OpenCity risponde ma la classe `avviso` non esiste; da scoprire il nome giusto in una sessione successiva.
- Ho letto solo la prima pagina di ogni elenco: "nessun bando visto" vale per le ultime 10-25 voci, non per l'anno intero.

## Tabella

| Ente | Pagina | Feed/API | Piattaforma | Bandi imprese visti (2025-26) | Esito |
|---|---|---|---|---|---|
| Firenze | /novita/avvisi | nessuno | Drupal | contributi attivita' storiche e commerciali (scad. 25/09/2026) | attiva, settimanale |
| Pisa | /Novita/Avvisi | API presente, classe da trovare | OpenCity | "Pisa is much more" fondi sfitti/botteghe; bottega storica | attiva, settimanale |
| Livorno | /it/news?type=3 | /it/news/feed (5 voci) | Municipium | nessuno | attiva, quindicinale |
| Lucca | /novita/ | feed vuoti | WP Design Comuni | nessuno | attiva, quindicinale |
| Prato | /it/novita/avvisi/pagina4211.html | RSS 404 | sito proprio | nessuno (animazione natalizia) | attiva, quindicinale |
| Pistoia | /it/news?type=3 | /it/news/feed (5 voci) | Municipium | nessuno (allestimenti natalizi) | attiva, quindicinale |
| Arezzo | /novita/avvisi | /taxonomy/term/834/feed/all | Drupal | nessuno | attiva, quindicinale |
| Siena | /tipi-di-notizia/avvisi | /taxonomy/term/409/feed | Drupal | contributi attivita' economiche centro storico 2026; esercenti enogastronomia | attiva, settimanale |
| Grosseto | - | - | ? | - | difficile (403) |
| Massa | comune.massa.ms.it/tipi-di-notizia/avvisi | /taxonomy/term/409/feed | Drupal | nessuno | attiva, quindicinale |
| Perugia | /tipi_notizia/avvisi/ | feed rimanda alla home | WP Design Comuni | nessuno in prima pagina | attiva, quindicinale |
| Terni | /novita/avvisi | /rss.xml inutile (segnalazioni) | Drupal | nessuno, elenco quasi vuoto | attiva, mensile |
| Ancona | /it/news?type=3 | /it/news/feed (5 voci) | Municipium | elenco operatori economici, danni imprese agricole (no contributi) | attiva, quindicinale |
| Macerata | - | - | ? | - | difficile (reset / 503) |
| Fermo | /Novita/Avvisi | non provata | OpenCity | nessuno | attiva, mensile |
| Ascoli Piceno | /avvisi | nessuno | FlexCMP | nessuno | attiva, mensile |
| Latina | /home/novita.html?categoria=/TipiNotizia/003 | /home/novita.rss?q=&categoria=/TipiNotizia/003 | Magnolia/Kibernetes | censimento botteghe e attivita' storiche; Latina si illumina 2026 | attiva, quindicinale |
| Frosinone | /tipi_notizia/avvisi/ | feed rimanda alla home | WP Design Comuni | nessuno | attiva, quindicinale |
| Rieti | - | - | ? | - | difficile (reset) |
| Viterbo | - | - | ? | - | difficile (reset) |
| L'Aquila | home (vuota) | Strapi /api, collezioni ignote | Angular + Strapi | - | difficile |
| Pescara | /tipi_notizia/avvisi/ | feed rimanda alla pagina | WP Design Comuni | spunta 2027 ambulanti (no contributi) | attiva, quindicinale |
| Chieti | - | - | ? | - | difficile (reset) |
| Teramo | /it/news?type=3 | /it/news/feed (5 voci) | Municipium | nessuno | attiva, quindicinale |
| Campobasso | - | - | ? | - | difficile (403) |
| Isernia | - | - | ? | - | difficile (reset) |

## Sintesi

1. 19 Comuni su 26 sono osservabili subito; 7 (Grosseto, Macerata, Rieti, Viterbo, Chieti, Campobasso, Isernia) bloccano il server e L'Aquila richiede il browser.
2. Solo Firenze, Siena, Pisa e Latina mostrano oggi misure per il commercio (contributi attivita' storiche e centro storico, botteghe, fondi sfitti): frequenza settimanale per i primi tre.
3. Feed RSS completi solo sui Drupal Design Comuni (Arezzo, Siena, Massa) e su Latina; i Municipium danno 5 voci; i WordPress del Centro hanno i feed spenti.
4. Gli elenchi sono sempre misti (gare per conto di altri comuni, scuola, sociale): il filtro per parole chiave e lo smistamento IA restano necessari.
5. Prossimo passo: riprovare i 7 bloccati dal VPS, trovare la classe API di Pisa e le collezioni Strapi dell'Aquila.

---

# Parte: capoluoghi_sud

# Capoluoghi del Sud e delle Isole - mappatura delle pagine avvisi (24/09/2026)

## Metodo

- 23 Comuni capoluogo (Campania, Puglia, Basilicata, Calabria, Sicilia, Sardegna), esclusi Lecce, Barletta e Potenza gia' nel registro.
- Lettura diretta con `curl` (User-Agent `Mozilla/5.0 (X11; Linux x86_64) BandiRadar/0.1`), massimo 8 richieste per ente, dalla sessione cloud (rete tramite proxy).
- Per ogni ente si sono aperte, nell'ordine, la home (per riconoscere la piattaforma), la pagina elenco avvisi, l'eventuale feed RSS o API JSON. Un indirizzo entra nel registro solo se ha risposto 200 con contenuto sensato (un feed con voci, un JSON con elementi).
- I titoli in elenco sono stati letti per cercare bandi rivolti a imprese (commercio, centro storico, locali sfitti, nuove aperture, start-up, distretti del commercio).

## Limiti

- Quattro siti non si sono aperti dal cloud: Benevento, Crotone, Catania (connessione chiusa dal server o 502 al CONNECT del proxy) e l'API di Enna (502). Sono segnati `difficile` e vanno riprovati dal VPS OVH, che ha un IP italiano.
- Avellino e' un'applicazione Angular senza sitemap ne' API individuabile: serve il browser senza interfaccia.
- Sui feed Municipium (Foggia, Andria, Trani, Caltanissetta) il parametro `type` viene ignorato e il feed espone solo 5 notizie miste; per questi si osserva la pagina HTML `news?type=3`.
- I feed WordPress mostrano solo le ultime 10-20 voci: il campione di "bandi per imprese visti" copre in genere le ultime 3-8 settimane, non l'anno intero.
- Il file YAML e' stato validato solo come struttura (23 voci, id unici, campi obbligatori); `python -m app.fonti.verifica` non e' stato eseguito.

## Tabella

| Ente | Pagina elenco | Feed / API | Piattaforma | Bandi imprese visti (2025-26) | Esito |
|---|---|---|---|---|---|
| Napoli | /tipi_notizia/avviso/ | RSS /tipi_notizia/avviso/feed/ (9 voci, 14-22/09) | WordPress Design Comuni | No nel campione; locazione locale comunale ad uso commerciale, inclusione lavorativa | attiva, rss, settimanale |
| Salerno | /tipi-di-notizia/avvisi | RSS /taxonomy/term/409/feed (10 voci) | Drupal 10 | No; posti auto, concessioni cimiteriali | attiva, rss, quindicinale |
| Caserta | pagina133704_avvisi.html | JSON news.json.php?tipologia=avvisi (66 avvisi) | ISWEB eCOMUNE | No; avvisi SUAP, voucher famiglie | attiva, api, quindicinale |
| Avellino | /sito/ (guscio Angular vuoto) | nessuno trovato | Angular SPA | non verificabile | difficile, browser |
| Benevento | non raggiunto | - | - | - | difficile (connessione chiusa) |
| Foggia | /it/news?type=3 | feed misto senza filtro | Municipium | No; raccolta firme commercio di prossimita', accreditamento librerie | attiva, html, settimanale |
| Brindisi | /notizie/avvisi/ | RSS /feed/?tipi_notizia=avvisi (10 voci) | WordPress Design Comuni | No; beni confiscati, locazioni turistiche, mercatino artigianale | attiva, rss, settimanale |
| Andria | /it/news?type=3 | feed misto senza filtro | Municipium | No; viabilita', TARI | attiva, html, quindicinale |
| Trani | /it/news?type=3 | feed misto senza filtro | Municipium | No; esercenti cedole librarie, hub Porta Nova | attiva, html, quindicinale |
| Matera | /tipi_notizia/avvisi/ | RSS /tipi_notizia/avvisi/feed/ (10 voci) | WordPress Design Comuni | No; concessione locali comunali | attiva, rss, quindicinale |
| Cosenza | /it/novita/avvisi (4 voci) | nessuno (rss 404) | tema agidv2 (non riconosciuta) | No negli avvisi; nelle notizie "Adotta una via" e COSimpresa | attiva, html, quindicinale |
| Catanzaro | /categoria-notizia/avvisi/ (3 voci) | feed 403 | WordPress (tema proprio) | No; graduatorie buono pasto | attiva, html, quindicinale |
| Reggio Calabria | /Notizie?tipologia=3 | RSS /rss.xml misto (24/09) | portale custom ASP.NET | No; buono servizio poverta', chiusure uffici | attiva, rss, settimanale |
| Crotone | non raggiunto | - | - | - | difficile (connessione chiusa) |
| Vibo Valentia | /novita/avvisi (vuota via JS) | ++api++/@search News Item (499 voci) | Plone 6 | No; museo Tonnara, alloggi ERP, voucher sociali | attiva, api, quindicinale |
| Palermo | /tipi_notizia/avvisi/ (8.508 in archivio) | RSS /tipi_notizia/avvisi/feed/ (~20 voci) | WordPress Design Comuni | No nel campione; ordinanze, incarichi, borse di studio | attiva, rss, settimanale |
| Catania | non raggiunto | - | - | - | difficile (502 / connessione chiusa) |
| Siracusa | /tipi_notizia/avvisi | RSS /tipi_notizia/avvisi/feed (9 voci) | WordPress Design Comuni | No; democrazia partecipata, gare | attiva, rss, quindicinale |
| Trapani | comune.trapani.it/tipo_notizia/avvisi/ | RSS /tipo_notizia/avvisi/feed/ (10 voci) | WordPress | No; contributi/patrocini eventi, registro De.C.O. | attiva, rss, quindicinale |
| Caltanissetta | /it/news?type=3 | feed misto senza filtro | Municipium | No; acqua, asili nido | attiva, html, mensile |
| Enna | /novita/avvisi (200, elenco via JS) | api.comune.enna.it/api/Content+filtro base64 (502 dal proxy) | Maggioli cloud (SPA) | non verificabile | difficile, browser |
| Nuoro | /it/novita/avvisi (10 voci) | nessuno (rss 404) | tema agidv2 (non riconosciuta) | SI', "contributi in conto capitale alle attivita' commerciali" (set 2026) | attiva, html, settimanale |
| Oristano | /it/novita/avvisi/ (vuota) | RSS /it/service/rss/rss_novita.xml misto (24/09) | OpenCms Consulmedia | No; ludoteche, eventi, mercato via Costa | attiva, rss, quindicinale |

## Sintesi

1. 18 enti su 23 sono osservabili subito (11 con feed RSS o API JSON, 7 solo HTML); 5 sono `difficile` (Benevento, Crotone, Catania irraggiungibili dal cloud; Avellino ed Enna sono applicazioni JavaScript) e vanno riprovati dal VPS.
2. L'unico bando per imprese trovato nel campione e' a Nuoro (contributi in conto capitale alle attivita' commerciali, settembre 2026); Foggia e Cosenza toccano il tema commercio ma senza contributi diretti visibili.
3. Le piattaforme sono per lo piu' note (5 WordPress Design Comuni, 4 Municipium, 1 Drupal, 1 Plone, 1 ISWEB); Cosenza e Nuoro condividono un tema "agidv2" di fornitore non identificato, Reggio Calabria ha un portale ASP.NET proprio, Oristano un OpenCms Consulmedia.
4. Tre trappole da ricordare: il feed Municipium ignora il filtro per tipo, il feed "/avvisi/feed/" di Brindisi e' quello dei commenti, e Trapani va letto senza www per il certificato.
5. Gli elenchi sono quasi sempre dominati da viabilita', scuola e sociale: il filtro per parole chiave e lo smistamento con l'IA restano indispensabili anche al Sud.

---

