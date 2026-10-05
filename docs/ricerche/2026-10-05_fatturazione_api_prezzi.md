# Fatturazione elettronica via API: chi costa meno (Bandi Radar + gestionale dello studio)

**Data:** 05/10/2026

**Domanda.** Qual è il fornitore più conveniente per **inviare e ricevere** fatture elettroniche allo SdI **tramite API REST**, usabile sia da Bandi Radar (Python, da poche centinaia a qualche migliaio di fatture l'anno, B2B Italia) sia dal gestionale contabile che Matteo sta sviluppando (più partite IVA dei clienti dello studio, fatture passive, eventualmente conservazione)? Quanto costa a 1.000 / 10.000 / 50.000 fatture l'anno?

**Metodo.** Parte dalla ricerca dello stesso giorno `2026-10-05_fatturazione_elettronica.md` (che aveva già scelto Invoicetronic per i soli abbonamenti). Ricerca web e lettura diretta, oggi, dei listini e della documentazione ufficiale dei fornitori; dove il listino ufficiale non c'è lo dico e riporto la fonte terza (rivenditore, blog) segnandola come **non verificata**.

**Limiti.**
- Prezzi IVA esclusa, letti il 05/10/2026: cambiano spesso.
- Nessun account aperto, nessuna prova in sandbox: le funzioni sono quelle **dichiarate** nella documentazione.
- Openapi pubblica **tre prezzi diversi** per lo stesso invio (pagina prodotto 0,07 €, console 0,070 € base / 0,022 € con abbonamento, FAQ 0,025 € con abbonamento) e **due codici destinatario diversi** (PIC7CPS sulla pagina prodotto, JKKZDGR nelle FAQ): riporto tutto, è già un segnale.
- A-Cube, Zucchetti, TeamSystem (API), InfoCert (API enterprise), Effatta (API), Aruba Premium: listino API **non pubblicato** → preventivo.
- "Fattura" = un documento che passa dallo SdI. Per i fornitori a consumo una fattura **ricevuta** costa quanto una inviata (Invoicetronic, ITALA; per Openapi le FAQ dicono che le fatture in arrivo consumano credito, senza prezzo esplicito). Nei conti sotto i volumi sono **documenti totali** (attivi + passivi).
- Le parti fiscali (emissione per conto del cliente, deleghe) sono un quadro, non un parere: decide Matteo.
- La pagina di FatturaPerTutti (API) ha risposto 403: non verificata.

---

## 1. Schede dei fornitori

### 1.1 Invoicetronic (CIR 2000) — https://invoicetronic.com
- **Prezzi** (pacchetti prepagati, **senza scadenza**): 1.000 transazioni 100 € (0,10), 5.000 a 275 € (0,055), 20.000 a 800 € (0,04), **50.000 a 1.250 € (0,025)**, 100.000 a 2.000 € (0,02). Transazione = invio, ricezione o validazione. **Gratis**: stati, webhook, storico webhook, registro eventi, sandbox. Firma opzionale 0,02 € (serve solo verso la PA). Nessun canone, nessuna attivazione.
- **Multi-partita IVA**: "una sola API key gestisce una o più aziende" che inviano e ricevono; "multi-company incluso nel prezzo delle transazioni".
- **API**: REST, OpenAPI, SDK open source anche **Python**, CLI per invii massivi, server MCP. **Accetta JSON o XML** (conversione inclusa), validazione preventiva.
- **Webhook**: sì, sugli stati SdI e sulle fatture in arrivo. **Sandbox**: gratis, subito.
- **Passive**: sì, endpoint `receive` (pull o webhook). Ogni partita IVA registra il codice destinatario **7HD37X0** nel cassetto fiscale.
- **Conservazione**: **non inclusa**, rimandano al servizio gratuito dell'Agenzia.
- **Extra utile per lo studio**: "Desk", interfaccia web **open source** per gestire le fatture senza codice (self-hosted gratis, in cloud 5 €/mese per chiave di produzione).
- **Solidità**: marchio di CIR 2000 (software gestionali da oltre 30 anni), dichiarato partner ufficiale SdI, dati solo in UE, pagina di stato pubblica. Testimonianze solo sul loro sito (nessuna recensione indipendente trovata).
- **Giudizio: sì** — non il più economico in assoluto, ma il miglior rapporto costo/strumenti.

### 1.2 Fattura Elettronica API (ITALA, intermediario accreditato) — https://www.fattura-elettronica-api.it
- **Prezzi** — abbonamenti mensili: M50 10 €/mese (50 fatture/mese), **M500 25 €/mese** (500), M5000 100 €/mese (5.000), M50000 850 €/mese (50.000). Ricariche: R100 20 €, **R1000 60 €**, **R10000 300 €**, R100000 2.000 €. Ogni fattura **ricevuta** consuma 1 credito (disattivabile); verso la PA 3 crediti (firma inclusa). Attivazione: non indicata; registrazione e test gratis. **Validità delle ricariche: non trovata.**
- **Multi-partita IVA**: sì, "multi-azienda" con plafond condiviso, anagrafica aziende anche via API (`/aziende`).
- **API**: REST 2.0, autenticazione Basic o Bearer; **accetta JSON minimo e genera l'XML**, oppure XML nostro; libreria open source. Librerie client **PHP e Java, niente Python**.
- **Webhook**: sì (URL + token). **Sandbox**: sì, endpoint `/ws2.0/test`.
- **Conservazione**: rimandano all'Agenzia (gratis).
- **Solidità**: ITALA è intermediario accreditato SdI; azienda piccola, poche informazioni indipendenti.
- **Giudizio: sì** — **il più economico** con listino chiaro; riserva naturale.

### 1.3 Openapi — SDI — https://openapi.com/products/italian-electronic-invoicing
- **Prezzi**: invio a consumo 0,07 €; abbonamenti annui da 5.000 chiamate (0,06 €) fino a 1.000.000 (0,0135 €), 250.000 a 0,022 €; FAQ: 0,025 € con abbonamento. Firma 0,09 € (console) o 0,02 € (FAQ); conservazione 0,105 € (console) o 0,035 € (FAQ). Importazione fatture 0,07 €. Ricezione: consuma credito, prezzo non esplicito.
- **Multi-partita IVA**: sì, una configurazione per P.IVA (`/IT-configurations`).
- **API**: REST, JSON → XML generato da loro; **webhook** sì; **sandbox** con simulazione fatture passive.
- **Passive**: sì, codice destinatario PIC7CPS o JKKZDGR (le due pagine non concordano).
- **Conservazione**: a pagamento per fattura (o Agenzia gratis).
- **Giudizio: non chiaro** — prezzi potenzialmente bassi, ma listino contraddittorio; da usare solo dopo una conferma scritta dei prezzi.

### 1.4 CloudFinance — FreeInvoice API — https://www.cloudfinance.it/free-invoice-api
- **Prezzi**: **attivazione 99 € per API key**; pacchetti con firma inclusa, **validi 12 mesi**: 1.000 a 60 € (0,06), 5.000 a 250 €, 10.000 a 400 € (0,04), 50.000 a 1.500 € (0,03), 100.000 a 2.000 €. Certificato di firma personale opzionale 300 € + 0,01-0,005 €/fattura.
- **Multi-partita IVA**: account master con sotto-account e limiti per ciascuno (adatto allo studio).
- **API**: HTTP con scambio di **file XML** (l'XML lo facciamo noi). Webhook e sandbox: non indicati.
- **Passive**: sì (trasmissione e ricezione). Conservazione: non indicata.
- **Giudizio: non chiaro** — prezzi buoni, ma documentazione e webhook non verificati; pacchetti che scadono a 12 mesi.

### 1.5 A-Cube API — https://www.acubeapi.com
- **Prezzi**: API **non pubblicate**: abbonamento annuo su preventivo in base a prodotti, volume e numero di soggetti giuridici. Solo l'app per Stripe ha listino (da 19,90 €/mese + sovrapprezzi per documento, vedi ricerca precedente).
- **API**: REST, JSON o XML, webhook, sandbox gratis, ricezione, conservazione opzionale; forte su multi-paese (Peppol ecc.).
- **Giudizio: non chiaro** — tecnicamente valido, prezzo ignoto; da chiedere solo se servisse l'estero.

### 1.6 Fatture in Cloud (TeamSystem) — https://www.fattureincloud.it/costo/
- **Prezzi annui** (primo anno): Standard 144 € (100 documenti/anno), Premium 252 € (400), Premium Plus 348 € (800), **Complete 612 € (3.000)**. Pacchetti extra non indicati nel listino. Firma e conservazione incluse.
- **API**: v2 REST ben documentata (developers.fattureincloud.it), OAuth, webhook; le API sono incluse nelle licenze. Ma è un **gestionale**, non un canale: le fatture si creano nel loro modello dati.
- **Multi-partita IVA**: "Multiazienda", ogni azienda con la sua licenza. Commercialista collegabile gratis ai clienti.
- **Giudizio: no** — tetti di documenti bassi, una licenza per azienda: non regge 10.000 né 50.000.

### 1.7 Aruba Fatturazione Elettronica — https://www.aruba.it/listino-fatturazione-elettronica.aspx
- **Prezzi**: base 29,90 €/anno (1 € i primi 3 mesi), 1 GB, conservazione inclusa, **solo pannello web**. Utente in più 4,90 €/anno. **API solo con "Premium"**, assente dal listino ufficiale; fonti terze: **300 € attivazione + da 600 €/anno**, più una quota per partita IVA (non verificato).
- **API**: REST JSON documentata (fatturazioneelettronica.aruba.it/apidoc), upload, invio, stato, download ricevute.
- **Giudizio: no** — ingresso caro e prezzo non trasparente.

### 1.8 Fattura24 — https://www.fattura24.com/prezzi/
- Business 144 € il primo anno / 192 € rinnovo (6.000 documenti), Complete 288/384 € (10.000).
- Le API creano la fattura **ma non la inviano allo SdI** (serve un clic manuale, dichiarato da loro). Conservazione non offerta.
- **Giudizio: no**.

### 1.9 InfoCert — Legalinvoice — https://www.fatturazione.infocert.it
- Piani PMI: GO! 24 €/anno (50 fatture), START 50 € (200), BUSINESS 86 € (400), pacchetti da 50 fatture a 9,76 €/anno; firma e conservazione 10 anni incluse. Sono **solo web**.
- API/FTP solo nell'offerta "grandi aziende" con prezzi a volume **non pubblicati**.
- **Giudizio: no** (per l'API: preventivo enterprise).

### 1.10 Namirial — https://www.namirial.it/fatturazione-elettronica/
- FatturePlus (web) 110 €/anno con 100 fatture e conservazione. Su un sito convenzionato (edilizianamirial.it) i piani **multiutente con più partite IVA** costano 4.900 €/anno (100 fatture), 19.900 € (1.000), 67.500 € (5.000); servizio base singola P.IVA 3.000 €/anno. Dichiarata "architettura API-driven", listino API non pubblico.
- **Giudizio: no** — fuori scala di due ordini di grandezza.

### 1.11 TeamSystem — TS Digital Invoice / Agyo
- Piattaforma per studi e aziende, "Connessioni" studio–clienti, conservazione AgID, API per integratori. Prezzi ufficiali non pubblici; da rivenditori (non verificati): 1.000 fatture 330 €/anno, 3.000 a 770 €, 5.000 a 1.210 €, conservazione inclusa.
- **Giudizio: no** per noi (pensato per chi usa i gestionali TeamSystem; API su accordo).

### 1.12 Zucchetti — Digital Hub
- Invio/ricezione, firma, conservazione, integrabile anche con gestionali non Zucchetti; prezzo "in base alle esigenze", solo tramite rivenditori.
- **Giudizio: no** (nessun listino, canale commerciale).

### 1.13 Effatta — https://effatta.it
- Piani web da 0 a 6,99 €/mese; API REST documentata (creazione, note di credito, invio XML, ricevute), ma **prezzo API non pubblicato** (pubblicato solo quello degli scontrini: 8 €/mese + da 0,009 €/documento).
- **Giudizio: non chiaro**.

### 1.14 Fattutto — https://www.fattutto.com/prezzi/
- API solo nel piano **Premium 420 €/anno, 3.000 fatture**; multi-azienda da Essential. Oltre 3.000 nessun piano.
- **Giudizio: no** (tetto basso).

### 1.15 Fiscozen
- Commercialista online con fatturazione inclusa per i propri clienti; **nessuna API pubblica** trovata.
- **Giudizio: no**.

### 1.16 Fai da te: open source + PEC (o SDICoop)
- **XML**: librerie libere, es. **python-a38** (Apache 2.0, genera, valida e legge FatturaPA, copre gli esempi ufficiali ma "solo parte della specifica"); FatturaElettronica.NET (dello stesso autore di Invoicetronic).
- **Canale**: PEC verso lo SdI senza accreditamento (costo di una casella PEC), ma niente sandbox, notifiche da leggere nella posta, fragile; SDICoop richiede accreditamento e certificati (settimane). Dettagli nella ricerca precedente §1.
- **Giudizio: no per il canale**, **sì per l'XML**.

### 1.17 Agenzia delle Entrate (servizi gratuiti)
- Invio a mano o PEC, nessuna API senza accreditamento; **conservazione gratuita 15 anni** su adesione, anche tramite intermediario delegato.
- **Giudizio: sì per la conservazione**, no per l'invio automatico.

---

## 2. Tabella comparativa

Costi annui stimati, IVA esclusa, per **documenti totali** (attivi + passivi).

| Fornitore | 1.000/anno | 10.000/anno | 50.000/anno | Canone / attivazione | Multi-P.IVA | JSON→XML | Webhook | Sandbox | Passive | Conservazione | Giudizio |
|---|---|---|---|---|---|---|---|---|---|---|---|
| **Fattura Elettronica API (ITALA)** | **60 €** (R1000) | **300 €** (R10000 o M500×12) | **1.000-1.200 €** (metà R100000 o M5000×12) | nessuno dichiarato | sì, plafond condiviso | sì | sì | sì | sì (1 credito) | Agenzia (gratis) | **sì** |
| **Invoicetronic** | 100 € | 550 € (2×5.000; ~400 €/anno con il pacchetto 20.000 su due anni) | 1.250 € | nessuno | sì, incluso | sì | sì, gratis | sì, gratis | sì (1 transazione) | Agenzia (gratis) | **sì** |
| Openapi SDI | ~70 € | 250-700 € (dipende dal prezzo vero dell'abbonamento) | ~1.100-2.000 € (stima) | wallet o abbonamento annuo | sì | sì | sì | sì | sì (costo non chiaro) | 0,035-0,105 €/doc o Agenzia | non chiaro |
| CloudFinance FreeInvoice | 159 € (99 + 60) | 499 € il 1° anno, poi 400 € | 1.599 € il 1° anno, poi 1.500 € | 99 € per chiave | sì, sotto-account | no (XML nostro) | non indicato | non indicato | sì | non indicata | non chiaro |
| A-Cube | preventivo | preventivo | preventivo | abbonamento annuo | sì (prezzo per soggetto) | sì | sì | sì | sì | opzionale | non chiaro |
| TeamSystem Agyo | 330 € (*terzi*) | non pubblicato | non pubblicato | annuo | sì (Connessioni) | — | — | — | sì | inclusa | no |
| Fattutto | 420 € (Premium, 3.000) | non regge | non regge | annuo | sì | sì | — | — | sì | — | no |
| Fatture in Cloud | 612 € (Complete, 3.000) per azienda | non regge | non regge | annuo per azienda | una licenza per azienda | sì (modello loro) | sì | — | sì | inclusa | no |
| Aruba Premium | ~900 € il 1° anno (*terzi*) | non pubblicato | non pubblicato | 300 € + ≥600 €/anno (*terzi*) + quota per P.IVA | sì, a pagamento | sì | — | — | sì | inclusa | no |
| Fattura24 | 144-192 € | 288-384 € | non regge | annuo | — | — | — | — | sì | no | **no** (non invia via API) |
| InfoCert Legalinvoice | API solo enterprise | preventivo | preventivo | — | — | — | — | — | sì | inclusa | no |
| Namirial | 19.900 € (multiutente, sito convenzionato) | — | — | annuo | sì | — | — | — | sì | inclusa | no |
| Zucchetti / Effatta | preventivo | preventivo | preventivo | — | sì | — | — | — | sì | inclusa / sì | no / non chiaro |
| Fiscozen | nessuna API | — | — | — | — | — | — | — | — | — | no |
| Fai da te PEC | ~10-30 € (PEC) + settimane di lavoro | idem | idem | — | una PEC per P.IVA | XML nostro | no | **no** | sì, da leggere in posta | Agenzia | no |

## 3. Classifica per costo totale (solo fornitori con listino API pubblico e invio automatico)

| Volume | 1° | 2° | 3° | 4° |
|---|---|---|---|---|
| **1.000/anno** | ITALA 60 € | Openapi ~70 € | Invoicetronic 100 € | CloudFinance 159 € |
| **10.000/anno** | ITALA 300 € | Invoicetronic 400-550 € | CloudFinance 400-499 € | Openapi 250-700 € (incerto) |
| **50.000/anno** | ITALA 1.000-1.200 € | Invoicetronic 1.250 € | CloudFinance 1.500-1.600 € | Openapi 1.100-2.000 € (incerto) |

La differenza tra i primi due è di **40-250 € l'anno**: meno di una giornata di lavoro di sviluppo. Tutti i "gestionali con API" (Fatture in Cloud, Fattutto, Aruba, Agyo, Namirial) costano da 3 a 100 volte di più o non reggono i volumi.

---

## 4. Raccomandazione

**Invoicetronic, con l'XML FatturaPA generato da noi e la conservazione gratuita dell'Agenzia. Riserva: Fattura Elettronica API (ITALA).**

Perché Invoicetronic e non il più economico sulla carta:
1. **Costo quasi uguale** a ITALA (40-250 €/anno di differenza) e **pacchetti che non scadono**: comprati una volta, durano finché servono (di ITALA non ho trovato la validità delle ricariche).
2. **SDK Python ufficiale** e sandbox gratis: Bandi Radar e il gestionale sono in Python, ITALA offre solo PHP e Java.
3. **Multi-azienda incluso** con una sola chiave: la società di Bandi Radar e ogni cliente dello studio sono "aziende" nello stesso account, senza costi per soggetto. Serve proprio al gestionale.
4. **Ricezione delle passive** con webhook gratuito: il gestionale riceve in automatico le fatture d'acquisto dei clienti.
5. **Desk open source**: un'interfaccia pronta per lo studio (vedere, scaricare, reinviare) senza doverla scrivere subito.
6. Dietro c'è un'azienda di software gestionale con 30 anni di storia e l'autore della libreria FatturaPA open source più usata.

**Riserva — ITALA**: listino chiaro, il più economico, JSON e XML, webhook, sandbox, multi-azienda via API. Se Invoicetronic cambiasse prezzi o chiudesse, si passa cambiando solo la chiamata d'invio (l'XML è nostro). Openapi solo dopo una conferma scritta del listino.

### Conservazione
Non pagarla al fornitore: adesione al **servizio gratuito dell'Agenzia** (15 anni) per ogni partita IVA, una volta sola, anche fatta da Matteo come intermediario delegato.

### Bandi Radar deve generare l'XML da sé? **Sì.**
- È l'unico modo per non dipendere dal fornitore: il JSON "semplificato" di ogni fornitore è diverso, l'XML FatturaPA è lo standard dell'Agenzia e lo accettano tutti.
- Si può partire da **python-a38** (genera e valida) o da un modello nostro controllato con lo schema XSD ufficiale; prima dell'invio, la validazione preventiva del fornitore (costa una transazione, quindi solo in sandbox o sui casi dubbi).
- Lo stesso modulo serve al gestionale: conviene farne **una libreria condivisa** (dati fattura → XML, XML → dati) usata da entrambi.

### Cosa deve fare Matteo per attivarlo
1. **Registrarsi** su invoicetronic.com: arriva subito la chiave di test (sandbox). Lo sviluppo parte da qui, senza spendere nulla.
2. **Decidere l'emittente** di Bandi Radar (studio o società apposita, vedi la ricerca precedente §4).
3. **Comprare il primo pacchetto** (1.000 transazioni, 100 €) quando si va in produzione e prendere la chiave live (va messa solo in `/srv/bandi-radar/.env`).
4. **Per ogni partita IVA che deve ricevere** (la società di Bandi Radar e ogni cliente del gestionale): registrare il codice destinatario **7HD37X0** nel portale *Fatture e Corrispettivi* (registrazione dell'indirizzo telematico). Lo può fare il cliente o Matteo come **intermediario delegato** dal cliente al servizio di fatturazione elettronica. **Attenzione**: il codice registrato vale per *tutte* le fatture in arrivo di quella P.IVA; un cliente che già riceve con un altro software smetterebbe di riceverle lì. Va concordato caso per caso.
5. **Aderire alla conservazione gratuita** dell'Agenzia per ogni partita IVA (stesso portale, anche come intermediario).
6. Per le fatture **emesse per conto dei clienti** dal gestionale: un incarico scritto del cliente all'emissione per suo conto (la fattura emessa da un terzo per conto del cedente è prevista dalla norma; *quadro, da confermare da Matteo*). Nell'XML il cedente resta il cliente.
7. Nessuna firma digitale da comprare (non serve tra privati) e nessun accreditamento SdI.

---

## Sintesi

- Il canale più economico con listino pubblico è **Fattura Elettronica API di ITALA** (circa 60 €, 300 € e 1.000-1.200 € l'anno a 1.000, 10.000 e 50.000 documenti).
- **Invoicetronic** costa poco di più (100 €, 400-550 €, 1.250 €) ma ha SDK Python, pacchetti senza scadenza, multi-azienda e webhook gratis, interfaccia open source: è la scelta raccomandata per Bandi Radar e gestionale.
- Openapi può costare poco, ma pubblica prezzi e codici destinatario contraddittori; CloudFinance è competitivo ma meno documentato.
- I gestionali con API (Fatture in Cloud, Fattutto, Aruba Premium, Agyo, Namirial, Zucchetti, InfoCert) costano molto di più o non reggono i volumi; Fattura24 non invia via API; Fiscozen non ha API.
- La conservazione va fatta gratis con l'Agenzia (15 anni), per ogni partita IVA.
- Bandi Radar deve generare l'XML FatturaPA da sé, in una libreria condivisa con il gestionale: così si cambia fornitore in un giorno.
- Per il gestionale il punto delicato non è il prezzo ma il **codice destinatario** dei clienti: registrarlo dirotta tutte le loro fatture in arrivo.

## Conseguenze per il progetto

- Conferma la scelta della ricerca precedente (Invoicetronic) e la estende al gestionale; riserva ITALA al posto di Openapi.
- Da fare: libreria condivisa XML FatturaPA (partendo da python-a38 o dallo schema XSD), con test sugli esempi ufficiali; un solo "adattatore" d'invio per fornitore.
- Azioni di Matteo: registrazione Invoicetronic (sandbox), scelta dell'emittente, poi codice destinatario 7HD37X0 e adesione alla conservazione per ogni partita IVA coinvolta.
- Da aggiungere all'indice di `docs/ricerche/README.md` (non fatto in questa sessione per istruzione: un solo file nuovo).

## Pagine viste

- https://invoicetronic.com/en/pricing/
- https://invoicetronic.com/en/features/
- https://invoicetronic.com/en/docs/prerequisites/
- https://www.fattura-elettronica-api.it/piani-e-prezzi/
- https://www.fattura-elettronica-api.it/faq/
- https://www.fattura-elettronica-api.it/documentazione/
- https://openapi.com/products/italian-electronic-invoicing
- https://console.openapi.com/apis/sdi/pricing
- https://console.openapi.com/apis/sdi/faq
- https://www.cloudfinance.it/free-invoice-api
- https://www.acubeapi.com/prodotti/api-e-invoicing-italia
- https://www.fattureincloud.it/costo/
- https://www.aruba.it/listino-fatturazione-elettronica.aspx
- https://www.fattutto.com/prezzi/
- https://www.edilizianamirial.it/condizioni-economiche-fe/
- https://effatta.it/fatturazione-elettronica-rest-api-integrazione/
- https://effatta.it/effatta-api/
- https://github.com/Truelite/python-a38
- Solo da risultati di ricerca (pagina non letta per intero o fonte terza): prezzi Legalinvoice (infocert.it), Aruba Premium (blog terzi), Agyo/TS Digital (rivenditori), Zucchetti Digital Hub, Fiscozen, prezzi A-Cube enterprise (e-invoice.app, 403), FatturaPerTutti (403).
