# Valutazione dell'efficacia: perimetro, smistamento, controllo preliminare, schede

**Data:** 26-27/09/2026, sessione sul VPS, su richiesta di Matteo: prima di tarare i costi con l'API, verificare che il risultato sia efficace (selezioni pertinenti e perimetro esaustivo).
**Domanda:** su un campione significativo di fonti, per ogni tipo di ente e tecnologia di sito: quanti bandi per imprese aperti trova Bandi Radar, dove perde gli altri, e quanto sbagliano i modelli leggeri (Haiku, Sonnet) rispetto a un riferimento forte (Opus)?

**Metodo:**
1. **Campione stratificato di 44 fonti** su 252 attive: per ogni combinazione tipo di ente × modalità di lettura (camera, capoluogo, provincia, regione, nazionale, UE, fondazione, contesto × rss, api, html, browser) una fonte con bandi rilevanti e una a caso (anche con zero risultati), più una fonte per ogni piattaforma CMS non coperta (agidv2, dotnetnuke, flexcmp, liferay, typo3, isweb, joomla, myportal...) e il catalogo incentivi.gov.it. Elenco in `2026-09-27_valutazione_efficacia/campione_fonti.json`.
2. Per ogni fonte, in parallelo:
   - **esploratore Opus**: legge il sito dell'ente (senza sapere cosa ha Bandi Radar) ed elenca tutti i bandi per imprese aperti, in arrivo o chiusi negli ultimi 6 mesi;
   - **Haiku** (modello leggero): smistamento di un campione di annunci della fonte (fino a 32, esattamente con il prompt di produzione) e controllo preliminare dei bandi (fino a 8, a piccoli lotti);
   - **Opus di riferimento**: lo stesso lavoro, leggendo i fascicoli per intero;
   - **scheda Opus** di un bando per fonte, da confrontare con quella di produzione (Sonnet).
3. **Controllore Opus**: segue ogni bando del sito lungo la catena di Bandi Radar (raccolto? smistato rilevante? collegato a un bando? pagina ufficiale? preliminare? scheda?) e giudica chi ha ragione dove regole, Haiku e Opus non concordano. **Giudice Opus** delle schede, campo per campo, sui documenti. **Verifica di riserva Opus**: prova a smentire ogni perdita e ogni disaccordo, anche tornando sul sito.
4. Incrocio finale su tutto il database: un bando che la fonte non raccoglie può arrivare da un'altra fonte (catalogo nazionale, anagrafica lombarda...).

In tutto circa 300 agenti; circa 12 milioni di token dell'abbonamento. La prima corsa si è fermata al limite settimanale dell'abbonamento ed è ripresa il 27/09 dopo l'azzeramento.

**Limiti:**
- Il riferimento è Opus e anche i giudici sono Opus: c'è il rischio che un modello giudichi con favore sé stesso. La verifica di riserva è tornata sulle fonti (sito e documenti), non sulle opinioni.
- Nei cataloghi grandi (incentivi.gov.it, portale UE, dati.gov.it) l'esploratore ha elencato un campione di 40 bandi, non tutti.
- Le schede di produzione erano state scritte da agenti a lotti di 5-10, non da chiamate API una alla volta: la qualità di Sonnet via API potrebbe essere un po' migliore.
- Lo stato "aperto" dell'esploratore è quello dei siti; in 7 casi (Cosenza) il sito indicava una data barrata e l'esploratore l'ha sbagliata; la riserva lo ha corretto.

## Numeri

### Perimetro: bandi per imprese APERTI o IN ARRIVO sui siti del campione

| Esito | Bandi | % |
|---|---|---|
| **con scheda in Bandi Radar** (dalla fonte o da un'altra) | **96** | **22%** |
| non raccolti da nessuna fonte | 193 | 45% |
| raccolti da un'altra fonte ma rimasti senza scheda | 54 | 13% |
| persi allo smistamento (regole: "da rivedere", mai ripresi) | 50 | 12% |
| fermati giustamente / fuori perimetro | 16 | 4% |
| persi al controllo preliminare | 7 | 2% |
| persi alla deduplica (dubbi non decisi) | 6 | 1% |
| persi alla pagina ufficiale | 5 | 1% |
| **Totale** | **427** | |

Per tipo di fonte (aperti o in arrivo / con scheda): Camere html 35/15, regioni html 34/15, catalogo nazionale 60/18, enti nazionali html 37/1, regioni api 50/4 (Sardegna), regioni rss 41/6, province api 42/15, UE 51/0, capoluoghi 14/3. Le Camere e le Regioni lette in HTML vanno meglio; i cataloghi e i siti nazionali molto peggio.

### Pertinenza

| Passo | Valutati | Regole / produzione | Haiku | Opus |
|---|---|---|---|---|
| Smistamento (annunci) | 466 | 48 errori medi o gravi (10%) | 14 (3%), di cui **6 gravi** (aiuti scartati) | **1** (0,2%) |
| Controllo preliminare (bandi) | 113 | produzione (Haiku a lotti da 20): 3 bandi buoni fermati, 32 chiusi fatti passare | Haiku a piccoli lotti: **0** fermati per errore, 11 chiusi fatti passare | **0 / 0** |
| Schede (voto 1-5) | 21 | Sonnet: **3,45**, 17 errori gravi in 9 schede | | Opus: **4,74**, 1 errore grave |

Gli errori gravi di Sonnet: date di apertura e scadenza lasciate vuote anche quando il bando le scrive, chiusure anticipate non viste, codici ATECO ristretti per sbaglio (così l'abbinamento escluderebbe settori ammessi), province mancanti (una Camera che copre 3 province diventa valida per tutta la regione), sintesi che contraddice il bando.

## Dove si perde, e perché (osservazioni confermate dalla riserva)

1. **La raccolta vede solo le novità, non la scorta dei bandi già aperti.** Un feed dà le ultime 10 voci, una pagina le ultime 30. I bandi pubblicati prima che il sistema partisse e ancora aperti non entrano mai (Parma, Siena, Sardegna, Invitalia, MIMIT, SIMEST).
2. **Cataloghi letti in parte.** L'indirizzo osservato di incentivi.gov.it (`/it/cerca-incentivi`) oggi risponde 404; il catalogo si è spostato. L'esploratore ha trovato un servizio pubblico (Solr, non vietato da robots.txt) che in una richiesta dà tutti i 6.025 incentivi con date, beneficiari e regioni. Il portale UE e dati.gov.it (righe dell'anagrafica lombarda) hanno lo stesso difetto.
3. **Sezioni dei siti non osservate.** Alcuni bandi stanno fuori dalla pagina osservata: Digital Export della Camera dell'Emilia, sezione PID di Verona, "Affittami" di Ferrara (solo notizia), cargo bike di Parma (solo notizia), "Politiche comunitarie" della Spezia.
4. **"Da rivedere" mai ripreso.** Le regole lasciano "da rivedere" bandi evidenti (Doppia Transizione e AI Lab di Cosenza, call UE in inglese, servizi camerali), e nessuno li riprende perché l'IA è spenta. Con l'IA accesa il grosso rientra.
5. **Siti Plone/Volto.** La raccolta usa l'API del sito, ma la ricerca della pagina ufficiale scarica l'HTML, che è vuoto: pagina "non trovata" (Verona, La Spezia, Siena).
6. **Deduplica**: "prorogato" nel titolo letto come proroga di un bando che non esiste (Veneto veicoli aziendali, aperto).
7. **Controllo preliminare**: fa passare bandi chiusi. Segnali gratuiti ignorati: date barrate, "bandi-chiusi" nell'indirizzo, scadenza nell'API del sito, "CHIUSO/ATTIVO" in testa alla pagina. Costa schede inutili, non fa perdere bandi.
8. **Siti dietro Cloudflare** (Fondazioni Cariplo e Cariverona): serve un browser, e forse non basta. L'indirizzo osservato di Cariplo è del vecchio sito.
9. **Date**: tutti gli annunci della Camera di Caserta hanno data di pubblicazione 30/10/2026 (futura), quindi la plancia mostra una data dell'ultimo record sbagliata.

## Costi (prezzi API del 27/09/2026, dollari per milione di token, ingresso/uscita; Batch API a metà prezzo)

Haiku 4.5: 1/5. Sonnet 5: 2/10. Opus 5.5: 4/20 (Opus 5: 5/25).

| Passo | Haiku | Sonnet | Opus 5.5 |
|---|---|---|---|
| Smistamento, per annuncio | 0,0006 $ | ~0,0012 $ | ~0,0025 $ |
| Controllo preliminare, per bando | 0,005 $ | ~0,011 $ | ~0,022 $ |
| Scheda, per bando | | 0,09 $ | ~0,18-0,25 $ (con il ragionamento) |

Stima a regime (3.000 annunci e 150-300 bandi nuovi al mese): con **Opus per tutti e tre i passi** circa 45-75 $ al mese, circa la metà con la Batch API per quello che non è urgente. Con Haiku + Sonnet circa 15-30 $. La differenza è di qualche decina di dollari al mese, mentre la qualità misurata cambia molto (schede 3,45 contro 4,74; aiuti scartati 6 contro 0). L'arretrato una tantum (circa 1.000 preliminari e 400 schede) costerebbe circa 20 $ + 40 $ con Opus in Batch.

## Sintesi

- **Il problema principale non sono i modelli ma il perimetro.** Solo il 22% dei bandi aperti per imprese del campione ha una scheda.
  - Il 45% non viene raccolto da nessuna fonte. Le cause sono strutturali: si leggono solo le novità, i cataloghi solo in parte, alcune sezioni dei siti non si osservano.
  - Un altro 26% viene raccolto ma si perde strada facendo, soprattutto perché i "da rivedere" non vengono mai ripresi.
- **Dove i modelli contano, Opus raggiunge gli obiettivi e i modelli leggeri no:**
  - smistamento: Haiku scarta aiuti veri (6 su 466), Opus no;
  - controllo preliminare: Haiku a piccoli lotti non ferma bandi buoni, ma fa passare bandi chiusi;
  - schede: Sonnet ha errori gravi in 9 schede su 21, Opus in 1.
- **Il costo dei modelli forti è piccolo in valore assoluto.** La scelta si può fare sull'efficacia.

## Conseguenze (proposta)

1. **Perimetro, senza IA**:
   - una lettura completa iniziale ("scorta") per ogni fonte, poi solo le novità;
   - incentivi.gov.it letto dal suo servizio completo;
   - portale UE e anagrafica lombarda letti per intero;
   - le sezioni mancanti aggiunte come fonti nel registro;
   - la pagina ufficiale dei siti Plone/Volto letta dall'API;
   - le date barrate e gli stati "chiuso" delle pagine usati come segnali.
2. **IA**: Opus 5.5 per smistamento dei "da rivedere", controllo preliminare e schede. Ogni passo si ricontrolla con i segnali gratuiti (date già note, stato della pagina).
3. **Rifare questa stessa valutazione** sulle stesse 44 fonti dopo i punti 1-2, per misurare il miglioramento.
