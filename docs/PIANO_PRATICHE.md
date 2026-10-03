# Pratiche: dalla scheda del bando alla domanda pronta

*Proposta del 03/10/2026, dalla richiesta di Matteo: checklist dei documenti per bando, pagina di caricamento nell'area riservata dell'impresa, controlli automatici dei documenti, richieste di chiarimento, notifiche e chat. Da discutere: le decisioni aperte sono in fondo (§8). Nessuna riga di codice è stata scritta per questa parte.*

---

## 1. L'idea in breve

Oggi Bandi Radar trova i bandi, scrive la scheda e la abbina ai profili. Il passo successivo è **lavorare la pratica**: quando un'impresa si affida allo studio per un bando, il sistema le chiede i documenti giusti, li controlla, ne estrae i dati per compilare i moduli del bando e chiede chiarimenti quando qualcosa non va. Matteo resta il professionista che firma: rivede e decide, gli agenti preparano.

```
 scheda del bando ──► CHECKLIST DEL BANDO ──► PRATICA DELL'IMPRESA ──► CONTROLLI ──► MODULI COMPILATI ──► revisione di Matteo ──► invio
 (c'è già)            (agente, una volta      (checklist adattata,     (subito: leggibile,   (dati estratti      (sempre)            (lo fa l'impresa
                       per bando, salvata)     caricamento, promemoria) scaduto?; poi a       dai documenti)                          o Matteo: SPID,
                                                                        pratica completa:                                              firma digitale)
                                                                        contenuto e coerenza)
                          ▲                                   │
                          └──── chat della pratica, notifiche, email ────┘
```

## 2. Cosa penso delle proposte

| Proposta | Parere | Perché |
|---|---|---|
| Checklist creata da un agente **alla prima richiesta**, per bando e non per impresa, e salvata | **Sì**, con due aggiunte | Generarla per tutti i bandi sprecherebbe token su bandi che nessuno lavora (oggi ~440 proponibili aperti, forse 20-30 lavorati al mese). Aggiunte: (a) la checklist ha una **versione legata alla scheda**: se la scheda viene aggiornata (rettifica, proroga, FAQ) la checklist si rifà, e le pratiche aperte vedono cosa è cambiato; (b) sopra la checklist del bando c'è un piccolo strato **per impresa senza IA**: regole che tolgono o aggiungono voci in base al profilo (società di capitali → bilanci depositati; ditta individuale → dichiarazione dei redditi; impresa femminile → documento che lo dimostra). |
| Pagina di caricamento nell'area riservata, con spunte e promemoria dei mancanti | **Sì** | È il cuore della pratica. In più propongo un **archivio dei documenti dell'impresa** (§3): la visura o il documento d'identità caricati per un bando valgono anche per il successivo, finché non scadono. |
| Controllo subito dopo ogni caricamento o solo a pratica "completa" | **Tutti e due, in due livelli** | **Subito, senza IA e quasi gratis**: il file si apre, è leggibile, è il tipo di documento atteso, non è scaduto (DURC oltre 120 giorni, visura oltre 6 mesi), è intestato all'impresa giusta. L'impresa sa subito se deve rifare il caricamento, invece di scoprirlo giorni dopo. **A pratica completa, con l'IA, a lotti**: lettura del contenuto, coerenza tra documenti (fatturato del bilancio e dichiarazione, codice ATECO della visura e requisiti del bando), estrazione dei dati per i moduli. Così l'IA legge ogni documento una volta sola, quando c'è tutto. |
| Se qualcosa non va, la piattaforma chiede chiarimenti o documenti nuovi, per email e nelle notifiche | **Sì**, con l'approvazione di Matteo all'inizio | Come per i match (decisione del 23/09): nel pilota le richieste scritte dagli agenti passano da Matteo prima di arrivare all'impresa. Quando si vede che sono affidabili, quelle di routine ("il DURC è scaduto, caricane uno nuovo") partono da sole. |
| Chat interna storicizzata, con agenti e Matteo | **Sì, ma una per pratica** | Una conversazione unica per impresa diventerebbe un groviglio quando le pratiche sono due o tre. Propongo una conversazione per pratica (più una generale per impresa), con i messaggi degli agenti distinti da quelli di Matteo, e i documenti citati come allegati della conversazione. Email di promemoria solo per i messaggi non letti dopo 24-48 ore, raccolti in un riepilogo, per non intasare la casella. |

## 3. Altre idee

1. **Catalogo dei documenti standard.** Una tabella fissa di ~40 tipi di documento con un codice (visura camerale, DURC, bilancio, dichiarazione dei redditi, documento d'identità del legale rappresentante, dichiarazione de minimis, preventivi, DSAN antimafia, certificazione parità di genere, ...), con la validità (DURC 120 giorni, visura 6 mesi) e i controlli senza IA per ciascuno. L'agente della checklist **sceglie dal catalogo** e aggiunge solo le voci davvero particolari del bando. Vantaggi: checklist più uniformi, documenti riusabili tra pratiche, controlli automatici scritti una volta.
2. **I moduli del bando li abbiamo già.** La modulistica viene scaricata e classificata (dal 03/10 anche meglio). L'agente della checklist mette tra le voci i moduli da compilare con il link al file ufficiale; l'agente di compilazione li riempie con i dati estratti (Word ed Excel si compilano bene; i PDF modificabili anche; i PDF piatti diventano un foglio "dati da ricopiare").
3. **Scadenze della pratica nel calendario.** La scheda ha già scadenza, ora di chiusura e modalità (sportello o graduatoria). La pratica eredita una data obiettivo ("documenti entro il ..., per presentare con 5 giorni di margine"), e i promemoria si calcolano da lì. Per gli sportelli e i click day il promemoria è più stretto.
4. **Dopo la domanda: obblighi e rendicontazione.** La scheda ha già il blocco `obblighi` (durata del progetto, rendicontazione, mantenimento dei beni e degli occupati). Una pratica concessa diventa uno **scadenziario** con i promemoria fino alla fine del mantenimento: è un servizio ricorrente, utile per l'abbonamento.
5. **Stati chiari della pratica**: interesse → documenti da raccogliere → documenti completi → in verifica → da integrare → moduli pronti → revisione di Matteo → presentata → esito → (se concessa) obblighi e rendicontazione → chiusa. Ogni passaggio resta nello storico, come per i bandi.
6. **Pannello per Matteo**: tutte le pratiche aperte con il semaforo (documenti mancanti, richieste in attesa di risposta, scadenze vicine), come la plancia delle fonti.

## 4. Criticità da segnalare (le più importanti prima)

1. **Privacy: è un cambio di architettura.** Oggi Bandi Radar **non conosce i clienti per nome** (scelta del 23/09, §2 del piano) e all'IA non arrivano dati identificativi (CLAUDE.md). Le pratiche invece trattano documenti pieni di dati personali: documenti d'identità, codici fiscali dei soci, bilanci, dichiarazioni dei redditi. Servono quindi: (a) un **modulo separato** "Pratiche" con il suo database e i suoi accessi, collegato a Bandi Radar solo con il codice anonimo del profilo; (b) una **decisione esplicita** sull'IA: per controllare e estrarre i dati, gli agenti devono leggere quei documenti. Si può fare (accordo sul trattamento dati con Anthropic, nessun addestramento sui dati inviati, conservazione minima), ma cambia una regola decisa e va scritto nell'informativa ai clienti; (c) documenti cifrati sul disco, accessi registrati, tempi di conservazione (per esempio cancellazione 10 anni dopo la chiusura per le pratiche concesse, prima per quelle abbandonate), backup cifrati. La revisione del professionista privacy prevista per la Fase 6 diventa più importante.
2. **Contract to Cash.** L'area riservata dell'impresa potrebbe vivere in C2C (Sergio), che già conosce i clienti. Prima di costruirla in Bandi Radar conviene chiedere a Sergio se C2C ha già accessi dei clienti, caricamento di file e notifiche: rifarle due volte sarebbe uno spreco.
3. **Sicurezza dei caricamenti.** File da sconosciuti su un server pubblico: limiti di dimensione e di tipo, controllo antivirus (ClamAV) prima di aprirli, mai eseguirli, nomi di file ripuliti, accesso dell'impresa solo alle sue pratiche, accesso di Matteo con secondo fattore.
4. **Responsabilità professionale.** I controlli degli agenti aiutano, non garantiscono. La domanda la presenta l'impresa (o lo studio con delega) con SPID o firma digitale del legale rappresentante: il sistema prepara, non invia. Ogni modulo compilato porta la revisione di Matteo, e nei termini del servizio va scritto che l'esito dipende dal bando e dai dati forniti.
5. **Qualità a monte.** La checklist è buona quanto la scheda e la modulistica. La sessione del 03/10 ha visto bandi chiusi o non per imprese tra i proponibili e allegati mancanti: la checklist va generata solo su schede verificate (meglio dopo il voto di Matteo, campo `qualita`) e rifatta quando la scheda cambia.
6. **Costi.** Checklist: una chiamata per bando lavorato (stimo 0,10-0,30 $ con Opus, a seconda della lunghezza dei testi). Controlli a pratica completa: dipendono da quanti documenti e se sono scansioni (le immagini costano di più): stimo 0,50-2 $ a pratica. Con 20-30 pratiche al mese restiamo sotto i 50 $; va comunque nel tetto di spesa e nella plancia dei costi. Finché il servizio non è venduto si può fare in sessione, come le schede.
7. **Troppe notifiche.** Email e promemoria vanno raccolti (un riepilogo al giorno al massimo per impresa, salvo scadenze vicine), altrimenti finiscono nello spam o vengono ignorati.
8. **Modello commerciale.** Il confine tra abbonamento base e servizio a pagamento decide cosa costruire prima. Proposta: nel base la checklist e il caricamento con le spunte; a pagamento i controlli, la compilazione dei moduli, la chat con lo studio e lo scadenziario degli obblighi.

## 5. Come lo costruirei (una strada)

| Fase | Contenuto | Cosa prova Matteo alla fine | Tempo stimato |
|---|---|---|---|
| **P0 — Decisioni** | Le decisioni del §8; domanda a Sergio su C2C; schema dei dati e regole privacy scritti | Un documento da approvare | 1 giorno |
| **P1 — Checklist del bando** | Catalogo dei documenti standard; agente della checklist su richiesta (prompt, controlli automatici come per le schede, salvataggio con la versione della scheda); pulsante "Genera checklist" nella pagina del bando della plancia; prova su 10 bandi con il voto di Matteo | Le checklist di 10 bandi veri, da correggere | 2-3 giorni |
| **P2 — Modulo Pratiche e area riservata** | Database separato (imprese identificate, utenti, pratiche, documenti, messaggi, notifiche), accesso dell'impresa con email e codice, pagina della pratica con la checklist adattata al profilo, caricamento con controlli senza IA e spunte, archivio dei documenti dell'impresa, antivirus | Una pratica di prova: caricare i documenti come se fosse un cliente | 4-5 giorni |
| **P3 — Promemoria e notifiche** | Sezione Notifiche, email con Resend (dominio `finanzagevolata.qiaro.it` da verificare), riepilogo giornaliero, promemoria dei mancanti e delle scadenze, approvazione di Matteo dei messaggi degli agenti | Le email di prova e la coda delle richieste da approvare | 2 giorni |
| **P4 — Controlli e compilazione** | Agente di verifica a pratica completa (a lotti), richieste di integrazione, estrazione dei dati, compilazione dei moduli Word/Excel/PDF, pagina di revisione per Matteo | Una pratica vera (con un cliente che accetta di fare da prova) fino ai moduli pronti | 4-5 giorni |
| **P5 — Chat della pratica** | Conversazione per pratica con messaggi di impresa, Matteo e agenti, documenti citati, non letti e promemoria | Una conversazione completa su una pratica | 2-3 giorni |
| **P6 — Dopo la domanda** | Esito, obblighi e scadenziario della rendicontazione | Lo scadenziario di una pratica concessa | 2 giorni |

Ordine scelto perché ogni fase serve da sola: già dopo P1 Matteo può usare le checklist con i clienti per email, anche senza area riservata.

## 6. I dati (bozza)

- `checklist_bando` (in Bandi Radar, senza dati dei clienti): bando, versione della scheda, data, autore (agente o Matteo), stato (bozza / approvata), voci. Voce: codice del catalogo o "particolare", descrizione, obbligatoria o premiale, a chi si applica (tutti, società, ditte individuali, una linea del bando), modulo ufficiale collegato (allegato), fonte (articolo del bando).
- Nel modulo Pratiche (dati identificati, database separato): `imprese` (anagrafica e collegamento al codice del profilo anonimo), `utenti` (accessi dell'impresa e dello studio), `pratiche` (impresa, bando, versione della checklist, stato, date), `voci_pratica` (stato: da caricare / caricato / da rifare / approvato, con il motivo), `documenti` (archivio dell'impresa: tipo, file cifrato, validità, esito dei controlli, dati estratti), `messaggi` (pratica, autore: impresa / studio / agente, testo, allegati, letto il, approvato da Matteo), `notifiche` (destinatario, tipo, collegamento, inviata per email il).

## 7. Gli agenti

| Agente | Quando | Legge | Scrive |
|---|---|---|---|
| Checklist | alla prima richiesta per un bando, e quando la scheda cambia | scheda, testo del bando, modulistica, catalogo dei documenti | la checklist, con la fonte di ogni voce |
| Controllo leggero | a ogni caricamento | solo il file (tipo, leggibilità, date) — **senza IA** | esito e motivo |
| Verifica | a pratica completa, a lotti | documenti della pratica, checklist, scheda | esiti per voce, incoerenze, richieste di integrazione (in bozza per Matteo) |
| Compilazione | dopo la verifica | dati estratti, moduli ufficiali | moduli compilati e un foglio "da completare a mano" |
| Messaggi | quando c'è qualcosa da chiedere o ricordare | stato della pratica, conversazione | messaggio in bozza (approvato da Matteo nel pilota) |

Stesse regole delle schede: niente invenzioni, fonte per ogni affermazione, controlli automatici sull'uscita, ogni lavoro registrato nella Supervisione.

## 8. Decisioni che servono da Matteo

1. **IA sui documenti dei clienti**: si accetta che gli agenti leggano documenti con dati personali (cambia una regola del 23/09)? In alternativa i controlli restano senza IA e l'estrazione si fa in sessione da Matteo.
2. **Dove vive l'area riservata**: modulo Pratiche dentro Bandi Radar (database separato) o in Contract to Cash? Serve una domanda a Sergio.
3. **Cosa sta nell'abbonamento base** e cosa a pagamento (proposta al §4.8).
4. **Approvazione dei messaggi degli agenti**: tutti nel pilota (proposta) o solo le richieste di documenti nuovi?
5. **Conservazione dei documenti**: per quanto tempo, e chi li può cancellare.
