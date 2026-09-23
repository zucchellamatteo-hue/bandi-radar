# Open data: i Comuni (e le Regioni) pubblicano i bandi come dati aperti?

**Data:** 23/09/2026
**Domanda:** Matteo ha segnalato che Milano ha un portale open data con API. Altri Comuni capoluogo hanno la stessa cosa? E i bandi per imprese si trovano lì, in forma strutturata, invece che nelle pagine HTML?
**Metodo:** tre sonde eseguite direttamente dalla sessione, senza agenti:
1. **Catalogo nazionale dati.gov.it** (API CKAN): dieci ricerche ("bandi", "bando contributi", "contributi imprese", "incentivi imprese", "agevolazioni imprese", "finanza agevolata", "voucher imprese", "sovvenzioni", "avvisi pubblici", "bandi e avvisi"), 494 dataset unici, raggruppati per ente che li pubblica.
2. **Sonda diretta dei portali open data dei ~100 capoluoghi** con gli indirizzi standard (dati.comune.X.it, opendata.comune.X.it, comune.X.it/opendata…), interrogando l'API CKAN con la parola "bandi".
3. **Portali regionali**: Lombardia e FVG (piattaforma Socrata), Toscana, Emilia-Romagna, Lazio, Trentino, Puglia (CKAN) e un tentativo sugli altri.
**Limiti:** alcuni portali rifiutano le connessioni da server (Basilicata, Marche, Abruzzo, Sicilia, Umbria, Liguria, incentivi.gov.it) e vanno riprovati dal VPS. La sonda cerca solo la parola "bandi": un dataset chiamato diversamente può essere sfuggito.

## Risposta breve

**No: gli open data non sono la strada per trovare i bandi aperti.** I portali esistono (una ventina di capoluoghi ha un portale vero, molti altri solo una pagina), ma quando contengono qualcosa che si chiama "bandi" o "contributi" è quasi sempre **Amministrazione trasparente**: elenchi di gare d'appalto e contratti, oppure **sovvenzioni già concesse** (atti di concessione, elenchi di beneficiari). Sono dati a posteriori, utili per capire cosa un ente ha finanziato negli anni passati, inutili per sapere cosa è aperto oggi.

Le eccezioni vere, che entrano nel registro delle fonti, sono tre e sono tutte regionali o provinciali autonome:

| Fonte | Cosa contiene | Formato | Stato |
|---|---|---|---|
| **Regione Basilicata, "Avvisi e Bandi pubblici"** | elenco dei bandi con tipologia, titolo, dipartimento, data di pubblicazione, **data di scadenza, destinatari** | CSV e JSON su opservice.regione.basilicata.it | non scaricabile da qui (connessione rifiutata), da verificare dal VPS. Se è aggiornato, è la fonte ideale per la Basilicata |
| **Provincia autonoma di Trento, calendari FESR, FSE+ e FEASR** | cronoprogramma degli avvisi in uscita: numero, titolo, apertura, chiusura, importo, beneficiari, link alla pagina | CSV pubblicato da un foglio Google, aggiornato al 2026 | **funziona da qui**, testato: l'ultimo avviso FESR è del 05/08/2026 |
| **Regione Emilia-Romagna, "Aree ammissibili per attività produttive"** | perimetri dei centri abitati in cui sono agevolabili nuove attività (bando rivitalizzazione sisma) | servizio WMS e webGIS | non è un elenco di bandi, ma serve per il **matching territoriale** |

Utili come **dati di contesto** per il matching, non come fonti di bandi: Milano `ds576` (perimetri dei Distretti Urbani del Commercio), Finlombarda su dati.lombardia.it (concessioni di finanziamenti, storico), Regione Puglia (elenchi beneficiari NIDI, Tecnonidi, Custodiamo le imprese, Fondo efficientamento energetico), Regione Siciliana ("Contributi e sussidi, anno in corso").

## Dettaglio per livello

**Regioni.** Nessun portale regionale espone come open data l'elenco dei bandi aperti, con l'eccezione di Basilicata (da verificare) e dei calendari trentini. Lombardia ha 43 dataset con la parola "bandi" e sono tutti indagini di soddisfazione sui bandi regionali o gare d'appalto di Comuni: i bandi veri restano su bandi.regione.lombardia.it, che nel piano è già una fonte con osservatore. FVG (dati.friuliveneziagiulia.it) non ha nulla sui bandi. Marche pubblica 99 dataset, tutti gare e beneficiari. Lazio, Toscana, Campania, Veneto: solo gare, concorsi, atti di concessione.

**Comuni capoluogo con un portale open data vero** (API funzionante): Milano, Trento, Modena, Reggio Emilia, Rimini, Ascoli Piceno, Napoli, Bari, Lecce, Catanzaro, Messina (CKAN); Genova, Parma, Cagliari (DKAN); Bologna (Opendatasoft); Palermo (piattaforma propria); Venezia, Torino, Roma, Firenze, Padova, Trieste, Udine, Pisa, Siena, Lucca, Arezzo, Piacenza, Pescara, Cosenza, Oristano (portale o pagina, API non risposta o non standard). **In nessuno di questi la ricerca "bandi" restituisce bandi di finanza agevolata aperti.** Lecce ha "Bandi ed esiti di gare", Bologna "Gare e appalti", Milano un elenco di concorsi del 2018.

**Il caso Palermo**, che sembrava promettente: il dataset "Comunicati, avvisi, scadenze" è l'esportazione delle notizie del sito, 16.245 record con tipo, date e testo. Sarebbe esattamente il formato che serve, ma **è fermo a dicembre 2018**. Un buon esempio di open data abbandonato: nel registro delle fonti ogni dataset deve avere la data dell'ultimo aggiornamento controllata dalla plancia, altrimenti si osserva una fonte morta.

**Attenzione a un falso positivo**: molti indirizzi comune.X.it/opendata reindirizzano al catalogo nazionale, quindi rispondono con gli stessi 91 risultati "Bandi di gara e contratti" di Comuni a caso. Non sono portali del Comune.

## Conseguenze per il registro delle fonti e per il sistema

1. **Non cercare i bandi negli open data comunali.** La fonte resta la pagina HTML del sito (o RSS, o API JSON del CMS), come già emerso nelle mappature sui capoluoghi.
2. **Aggiungere tre fonti open data**: Basilicata avvisi/bandi (JSON, giornaliero, dopo verifica dal VPS), Trento calendari FESR/FSE+/FEASR (CSV, settimanale), Emilia-Romagna aree ammissibili (dato di contesto, mensile).
3. **Aggiungere una categoria "dati di contesto"** al registro, separata dai bandi: perimetri DUC di Milano, aree ammissibili Emilia-Romagna, elenchi beneficiari (utili in Fase 7 per il de minimis e per stimare le probabilità di successo).
4. **Il catalogo nazionale dati.gov.it è a sua volta una fonte da osservare**, una volta al mese, con le stesse dieci ricerche di oggi: se un ente pubblica un nuovo dataset di bandi aperti, lo si scopre lì senza controllare cento portali.
5. **incentivi.gov.it rifiuta le connessioni da questa rete** (come Milano). Nel piano è la fonte nazionale principale: va testato per primo dal VPS OVH. Se anche da lì è bloccato, servono i suoi open data pubblicati altrove o un browser senza interfaccia.
6. **Per la plancia**: ogni fonte open data deve mostrare la data dell'ultimo record, non solo l'esito dell'ultimo scaricamento. Palermo insegna.

---

## Seconda passata con i sinonimi (stessa giornata)

Matteo ha chiesto se la sonda avesse usato anche i sinonimi. La prima passata usava dieci termini sul catalogo nazionale ma **solo "bandi" sui portali comunali**. La seconda passata ha usato **34 termini** (incentivi, agevolazioni, finanza agevolata, finanziamenti imprese, fondo perduto, voucher, contributi imprese, sostegno imprese, aiuti imprese, ristori, microcredito, credito imposta, start up, PMI, attività produttive, artigianato, commercio, distretto del commercio, botteghe, nuove imprese, imprenditoria, SUAP, avvisi pubblici, bando, opportunità, sovvenzioni, bandi aperti, avvisi aperti, calendario bandi, catalogo incentivi, misure agevolative, aiuti di stato…) su 17 portali con API funzionante (11 comunali, 5 regionali, il catalogo nazionale): 2.137 dataset unici esaminati sul catalogo nazionale.

**Sui portali comunali il risultato non cambia**: i sinonimi fanno emergere elenchi di esercizi commerciali, attività artigianali, botteghe storiche, pratiche SUAP, statistiche sulle imprese. Nessun elenco di bandi aperti. Dati di contesto in più: Milano "Elenco attività storiche e di tradizione" (2026), Modena e Regione Emilia-Romagna "Limiti delle zone con agevolazioni fiscali", Genova "Numeri civici ammessi ad aiuti di Stato a finalità regionale".

**Sul catalogo nazionale invece i sinonimi hanno fatto emergere cinque fonti nuove**, che con "bandi" non uscivano:

| Fonte | Cosa contiene | Verifica | Uso |
|---|---|---|---|
| **Regione Lombardia, "Anagrafica dei bandi regionali"** (dati.lombardia.it, id `bukx-h2uy`) | **tutti i bandi e le misure pubblicati su Bandi Online dal 2015**: 1.912 record con codice, titolo, direzione generale, ente, apertura, chiusura, tipo di strumento, numero di domande. Oggi **122 aperti**, di cui 11 di Sviluppo Economico, 6 Agricoltura, 3 Università e Ricerca; comprende anche i bandi con apertura futura (es. giovani agricoltori dal 13/10/2026). Il codice porta alla scheda: `bandi.regione.lombardia.it/servizi/servizio/bandi/dettaglio/<codice>`, raggiungibile da qui | **funziona**, API Socrata con filtri (`$where=chiusura_adesione>…`), righe aggiornate al 01/09/2026, quindi cadenza mensile circa | **Fonte primaria per la Lombardia**: il registro dice cosa c'è e quando apre e chiude, la scheda su Bandi Online dà requisiti e documenti. L'osservatore HTML di Bandi Online resta per le novità tra un aggiornamento mensile e l'altro |
| **MIMIT, "Open Data RNA Aiuti"** (rna.gov.it) | un file XML al mese con **tutti gli aiuti concessi registrati nel Registro Nazionale Aiuti** dal 2017 a marzo 2026 | rna.gov.it rifiuta le connessioni da qui, da riprovare dal VPS | **Fase 7, de minimis**: per ogni cliente, gli aiuti già ricevuti; e per ogni misura, chi la ottiene davvero (dimensione, settore, provincia) |
| **Regione Lombardia, "Aiuti di Stato individuali"** (id `f468-u5ng`) | aiuti sopra 500.000 € con beneficiario, partita IVA, dimensione, provincia, settore, strumento, obiettivo | funziona | contesto, complementare al RNA |
| **Regione Calabria, "Calendario avvisi 21-27"** | calendario degli avvisi programmati FESR e FSE+ 2021-27 (obbligo dell'art. 49 del Reg. UE 2021/1060: **ogni Regione deve pubblicare questo calendario**) | dati.regione.calabria.it rifiuta le connessioni da qui; il file più recente visto è dell'ottobre 2023 | calendario, come quelli di Trento. **Da cercare per tutte le Regioni**: l'obbligo è europeo, il calendario esiste anche dove non è open data |
| **GAL Terra dei Messapi, feed RSS bandi** | feed dei bandi di un Gruppo di Azione Locale (sviluppo rurale) | funziona, ultimo aggiornamento gennaio 2026 | apre la categoria **GAL** (circa 200 in Italia): bandi PSR per micro-imprese rurali, agriturismo, artigianato locale. Da valutare in Fase 7 per i clienti in zone rurali |

Non pertinente ma istruttivo: "Avvisi PA digitale 2026" del Dipartimento Trasformazione Digitale (57 avvisi in JSON su GitHub, con date, stato, importi, destinatari) è il formato ideale, ma i destinatari sono Comuni e scuole, non imprese.

**Conclusione della seconda passata.** I sinonimi non cambiano il giudizio sui Comuni, ma cambiano quello sulle Regioni: **la Lombardia ha un registro strutturato di tutti i suoi bandi**, ed è la regione più importante per il progetto. La lezione per il sistema: le ricerche sul catalogo nazionale vanno fatte sempre con l'intera lista di sinonimi, perché i dataset migliori si chiamano "anagrafica", "calendario", "aiuti", non "bandi".

## Conseguenze aggiuntive per il registro delle fonti

7. **Lombardia**: aggiungere l'Anagrafica dei bandi regionali come fonte strutturata (API, controllo giornaliero, costo zero), collegata alle schede di Bandi Online per i dettagli. Attivarla in Fase 1 per prima: è il caso di prova ideale per il flusso "registro strutturato + scheda HTML".
8. **Calendari degli avvisi 2021-27**: cercarli per tutte le 21 Regioni e Province autonome, in qualunque formato (open data, PDF, pagina web). Sono la fonte più anticipata che esista: dicono cosa aprirà nei prossimi mesi.
9. **RNA open data**: fonte di Fase 7, da testare dal VPS; scaricare i file mensili e caricarli in una tabella "aiuti concessi".
10. **GAL**: nuova categoria di fonti, da valutare in Fase 7 in base alla distribuzione dei clienti.
11. **Sonda mensile del catalogo nazionale**: con i 34 termini, non con dieci.
