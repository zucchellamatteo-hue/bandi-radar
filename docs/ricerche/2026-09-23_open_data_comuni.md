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
