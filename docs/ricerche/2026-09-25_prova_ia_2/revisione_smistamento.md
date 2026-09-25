# Revisione dello smistamento fatto da Haiku: seconda prova (25/09/2026)

## Sintesi

Haiku ha risposto a **tutti i 100 annunci** (5 lotti da 20, nessun id mancante, nessun id inventato). Sono d'accordo con lui su **92 annunci su 100**. Nella prima prova l'accordo era del 75%.

**Nessun errore grave**: nessun bando per imprese è stato scartato. I 26 annunci che secondo me sono rilevanti li ha trovati tutti come `rilevante`. Gli **errori medi sono 2** (annunci non per imprese promossi a rilevanti): un premio della Camera di Padova che va alle scuole e una concessione demaniale per uno stabilimento balneare. I **6 errori lievi** sono tutti dello stesso tipo: `da_rivedere` dato a casi che si potevano scartare.

Le correzioni del prompt hanno funzionato quasi tutte. Hanno funzionato le regole su posteggi e fornitori, sulla fonte come indizio e sul "rileggere prima di scartare". La regola "`da_rivedere` solo sul destinatario" ha funzionato solo in parte: `da_rivedere` è sceso dal 20% al 13%, ma circa metà di questi casi era ancora decidibile. Resta anche qualche incoerenza tra annunci gemelli.

**Giudizio: Haiku può decidere da solo tra `rilevante` e `non_rilevante`**, a quattro condizioni: resta il controllo degli id, i `da_rivedere` vanno in coda a Matteo, per il primo mese la plancia mostra gli scarti che vengono da fonti "ad alto rendimento", e si applicano le 5 correzioni proposte sotto. Un limite da dire: il campione contiene solo 26 bandi veri. Zero errori gravi su 26 è un buon segnale, ma non garantisce che non ce ne saranno mai.

## Metriche

| Voce | Prova 2 (oggi) | Prova 1 (25/09) |
|---|---|---|
| Annunci inviati | 100 (5 lotti da 20) | 90 (2 lotti da 45) |
| Risposte ricevute | **100/100** | 88/90 |
| Accordo con il revisore | **92/100 = 92%** | 66/88 = 75% |
| Errori GRAVI (bando per imprese dato non_rilevante) | **0** | 3 |
| Errori MEDI (non per imprese dato rilevante) | **2** | 5 |
| Errori LIEVI (da_rivedere contro una decisione chiara, o viceversa) | **6** | 14 |
| `da_rivedere` di Haiku | 13 su 100 = **13%** | 18 su 88 = 20% |
| `da_rivedere` del revisore | 7 su 100 = 7% | 15 su 90 = 17% |
| Precisione dei `rilevante` di Haiku | **26/28 = 93%** | 21/29 = 72% |
| Bandi rilevanti trovati da Haiku | **26 su 26 = 100%** | 21 su 27 = 78% |
| `non_rilevante` di Haiku sbagliati | **0 su 59** | 3 su 41 = 7% |
| `da_rivedere` di Haiku davvero indecidibili | 7 su 13 | 9 su 18 |

Esiti a confronto: Haiku ha dato 28 `rilevante`, 59 `non_rilevante` e 13 `da_rivedere`; io 26, 67 e 7.

Tabella di confronto (righe = Haiku, colonne = revisore):

| Haiku \ Revisore | rilevante | non_rilevante | da_rivedere |
|---|---|---|---|
| rilevante | 26 | 2 (MEDIO) | 0 |
| non_rilevante | 0 | 59 | 0 |
| da_rivedere | 0 | 6 (LIEVE) | 7 |

**Obiettivi fissati nella prima revisione**:
- nessun bando aperto perso: **raggiunto** (0 bandi persi);
- al massimo 3% di rilevanti falsi: **raggiunto** se si conta sul totale degli annunci (2 su 100 = 2%), **non raggiunto** se si conta sui soli rilevanti (2 su 28 = 7%);
- al massimo 10% di `da_rivedere`: **non raggiunto** (13%). Correggendo i 6 lievi si scenderebbe al 7%.

**Com'è fatto il campione.** Sono 100 annunci che le regole a parole chiave di oggi lasciano in `da_rivedere`, esclusi quelli della prima prova, estratti in proporzione al tipo di fonte: 39 da Regioni e finanziarie regionali, 27 da capoluoghi, 20 da Camere, 14 da altre fonti. 68 annunci non hanno riassunto; per 49 di questi Haiku ha ricevuto l'inizio della pagina. Rispetto alla prima prova ci sono più annunci facili da scartare (notizie dei Comuni, pagine di servizio), quindi il 92% non si confronta alla pari con il 75%. Il miglioramento sugli errori però è netto.

**Metodo.** Ho giudicato ogni annuncio con le stesse istruzioni date a Haiku e con le sole informazioni del prompt. Per i casi dubbi ho fatto 9 richieste esterne:
- pagine della Camera di Padova, della Camera dell'Umbria, del Comune della Spezia, della Camera di Catanzaro e di Sviluppo Toscana;
- una sola interrogazione agli open data della Lombardia, che copriva 3 annunci;
- il PDF della Camera di Cuneo, che non sono riuscito a leggere.

Dove il giudizio viene dalla pagina lo indico con "(pagina)".

## Annunci su cui non sono d'accordo con Haiku (8)

| id | Titolo breve | Haiku | Revisore | Gravità | Motivo |
|---|---|---|---|---|---|
| 286 | CCIAA Padova – Premio storie di alternanza 2026 | rilevante | non_rilevante | **MEDIO** | (pagina) Si candidano istituti tecnici, professionali, licei e ITS; i premi (1.200/800/500 €) vanno alle scuole. Haiku ha applicato la regola 5 ("bando di una Camera, quindi imprese") senza segni del contrario, ma il titolo non li dava. |
| 3750 | Basilicata – Concessione demaniale marittima stagionale (Nova Siri) | rilevante | non_rilevante | **MEDIO** | Pubblicazione della domanda di concessione di una spiaggia per uno stabilimento balneare: è l'impresa che paga il canone all'ente. Incoerente con **3732** (concessioni demaniali per chioschi, stessa fonte), che Haiku ha scartato correttamente. |
| 3357 | Sviluppo Toscana – Verifiche tecniche edifici pubblici strategici | da_rivedere | non_rilevante | LIEVE | (pagina) Possono chiedere il contributo solo Comuni, Unioni di Comuni, Province, Città metropolitana e Regione. Già il titolo ("edifici pubblici") bastava. |
| 3215 | FVG – Le Politiche di Coesione 2021-2027 (PDF di un evento) | da_rivedere | non_rilevante | LIEVE | Presentazione di un evento sulla programmazione: nessun bando (regola 7). |
| 1276 | Ragusa – Nuovo corso ITS per diplomati | da_rivedere | non_rilevante | LIEVE | Corso di formazione per persone diplomate: nessun contributo a imprese. |
| 2709 | Lombardia – AMAES, ricerca di partner per un progetto di inclusione | da_rivedere | non_rilevante | LIEVE | (open data) Direzione Famiglia, Solidarietà sociale e Disabilità: l'ente cerca partner del terzo settore per un suo progetto (regola 3). |
| 3516 | Sviluppo Italia Molise – Molise Contamination Lab | da_rivedere | non_rilevante | LIEVE | Il testo ricevuto dice che è uno spazio di formazione per studenti gestito con l'Università. Nessun contributo. |
| 2771 | Lombardia – Servizi Integrativi, Provincia di Cremona | da_rivedere | non_rilevante | LIEVE | (open data) È una misura della legge 68/99 (lavoro delle persone con disabilità), cioè servizi erogati da operatori accreditati. L'annuncio gemello **2768** (Provincia di Bergamo) ha ricevuto `non_rilevante`: altra incoerenza (regola 8). |

Casi su cui sono d'accordo ma che segnalo:
- **2567 e 2563** (Horizon WIDERA: "Science comes to town", politiche di accesso aperto): Haiku ha dato `da_rivedere`. Formalmente la regola 5 dice `rilevante`, perché nei bandi Horizon un'impresa può entrare in consorzio. Nella pratica sono bandi per città e istituti di ricerca, inutili per i clienti di Matteo. `da_rivedere` è una scelta prudente, ma la regola 5 va precisata (proposta 4).
- **916** (Camera di Catanzaro, iniziative promozionali di enti del terzo settore "e altri soggetti privati"): `da_rivedere` corretto. (pagina) Anche il testo dell'avviso non dice se tra i "soggetti privati" ci sono imprese.
- **2654** (Lombardia, "Ti porto io"): `da_rivedere` accettabile con il solo titolo. (open data) È della Direzione Famiglia e Disabilità, quindi quasi certamente non per imprese.
- **5** (Camera di Cuneo, "Modulo di candidatura") e **3977** (Fincalabra, formulario "Spettacoli ed eventi 2022"): `da_rivedere` corretto, perché sono allegati senza il bando di riferimento. Non sono riuscito a leggere il PDF di Cuneo.
- **636** (Camera dell'Umbria, destinazione turistica): `rilevante` confermato dalla pagina, il bando è per le imprese del territorio.
- **1241** (La Spezia, "Un dolce di Natale"): `non_rilevante` confermato dalla pagina. Il concorso è per pasticcerie e panifici, ma senza premi in denaro.
- **992** (Camera di Trapani, turnazione dei distributori di carburante): l'esito `non_rilevante` è giusto, ma il motivo è sbagliato. Haiku parla di "posteggi", invece si tratta dei turni di apertura.

## Le correzioni del prompt hanno funzionato?

| Regola | Esito | Esempi |
|---|---|---|
| 4 – posteggi, fornitori, beni pubblici, chiarimenti | **Sì, con una falla** | Scartati correttamente: 3540 (albo di esperti di Sviluppo Campania), 1080 (accreditamento del terzo settore a Pordenone), 3732 (chioschi sul demanio), 4115 (vendita di legna), 2151 (chiarimenti sulla rottamazione), 2303 (piano spiaggia). Nella prima prova erano 5 errori medi, ora nessuno di questo tipo. Falla: la **concessione demaniale** 3750 è passata, perché il testo parla "degli ospiti delle attività ricettive" e sembra un vantaggio per l'impresa. |
| 5 – la fonte come indizio | **Sì** | Allegati di Fincalabra con il solo titolo (3988, 3991, 4036, 3968), il PDF di concessione della Camera di Cosenza (896), il link a una graduatoria della Camera di Bologna (503): tutti `rilevante`, giustamente. Fondazioni: Cariplo "Musei" in `da_rivedere`, Cariplo "Nuovi ponti culturali" scartata (il testo dice "enti non profit"), Cariverona SMAQ `rilevante` (il testo dice "40 aziende"). Unico eccesso: 286, premio camerale per le scuole. |
| 6 – rileggere prima di scartare | **Sì** | Nessun errore grave. Haiku ha scartato con motivo corretto anche annunci di fonti "ad alto rendimento" quando il testo lo giustificava: 3124 (Finpiemonte, edilizia scolastica), 3986 (Fincalabra, avviso per i Comuni), 1698 (Rimini, amianto: il testo dice "privati cittadini"). |
| 7 – `da_rivedere` solo sul destinatario | **In parte** | Home page, categorie, menu, eventi senza bando: ora quasi tutti `non_rilevante` (315, 465, 3870, 4087, 3905, 1756, 3478). Restano però 6 `da_rivedere` evitabili: un PDF di un evento (3215), corsi per persone (1276), ricerca di partner (2709), un laboratorio per studenti (3516), un bando riservato a enti pubblici (3357) e un titolo della Lombardia (2771). |
| 8 – stesso esito per annunci gemelli | **No** | 2768 e 2771 (Servizi integrativi, Bergamo e Cremona) hanno esiti diversi; lo stesso vale per 3732 e 3750 (concessioni demaniali di Nova Siri, stessa fonte). Negli ultimi due casi gli annunci erano in lotti diversi: con lotti separati la regola 8 da sola non può funzionare. |
| Lotti da 20 e controllo degli id | **Sì** | 100 risposte su 100, id tutti corretti. |

### Errori che restano e perché

1. **"Concessione" letta come vantaggio** (3750). La regola 4 parla di posteggi e di beni pubblici venduti, ma non di concessioni demaniali o di suolo pubblico. Dove l'impresa ottiene un permesso pagando un canone, Haiku vede un beneficio.
2. **Regola della fonte applicata senza guardare chi si candida** (286). Per Haiku "Camera di commercio + premio" basta. Il premio "Storie di alternanza" di Unioncamere si ripete ogni anno in quasi tutte le Camere, quindi l'errore si ripresenterà.
3. **`da_rivedere` usato come rifugio quando il testo non parla di soldi** (corsi, eventi, partner, laboratori). La regola 7 elenca eventi e pagine di servizio, ma non corsi per persone, bandi riservati a enti pubblici e ricerche di partner.
4. **Annunci della Lombardia con il solo titolo.** Sette annunci degli open data lombardi arrivano senza riassunto né testo (2652, 2654, 2668, 2709, 2716, 2768, 2771). Eppure il dato pubblico contiene la direzione regionale responsabile (per esempio "Famiglia, Solidarietà sociale, Disabilità", "Provincia di Cremona L.68"), che basterebbe a decidere. Da qui vengono un errore lieve e l'incoerenza tra 2768 e 2771.
5. **Coerenza tra lotti diversi.** Haiku vede un lotto alla volta, quindi non può confrontare annunci gemelli finiti in chiamate separate.

## Proposte (5)

1. **Prompt, regola 4: aggiungere le concessioni.** Nuova voce:
   > concessioni demaniali marittime, di suolo pubblico o di acque (stabilimenti balneari, chioschi, dehors, derivazioni d'acqua) e pubblicazione delle domande di concessione: è l'impresa che paga un canone all'ente.

   Aggiungere tra gli esempi 3750 con esito `non_rilevante`.
2. **Parole chiave (`regole_smistamento.yaml`): premi per le scuole.** Nel gruppo `non_rilevante` aggiungere `storie di alternanza` e `premio` con `istituti scolastici` / `studenti` / `ITS`. Nel prompt, alla regola 5, aggiungere premi e concorsi per scuole e studenti agli esempi di "segni chiari del contrario".
3. **Prompt, regola 7: più casi `non_rilevante` "senza dubbio".** Aggiungere:
   > corsi di formazione per persone (ITS, OSS, corsi per disoccupati); bandi riservati a enti pubblici ("edifici pubblici", "rivolto ai Comuni", "Unioni di Comuni"); ricerca di partner o co-progettazione con il terzo settore; presentazioni e slide di eventi.

   Aggiungere 3357 e 2709 agli esempi.
4. **Prompt, regola 5: precisare i bandi UE.** Aggiungere:
   > Horizon WIDERA ed ERA (accesso aperto, città della scienza, politiche degli istituti di ricerca) sono per istituti di ricerca ed enti pubblici: `non_rilevante` salvo imprese citate nel testo.

   Così 2563 e 2567 non restano in coda a Matteo.
5. **Programma: passare più dati sugli annunci della Lombardia.** Il lettore degli open data lombardi deve mettere nel riassunto la direzione generale, il tipo di strumento e le date di apertura e chiusura, che il dato pubblico già contiene. Costa una riga di configurazione e toglie il problema del "solo titolo" per una fonte con molti annunci.

## Giudizio

**Sì, Haiku può decidere da solo** tra `rilevante` e `non_rilevante`, senza che Matteo ricontrolli ogni annuncio. Rispetto alla prima prova sono spariti gli errori più pericolosi (0 bandi persi contro 3) e le risposte incomplete (100 su 100). Anche gli errori medi (2) costano poco: qualche scheda Sonnet inutile e qualche secondo di lettura per Matteo.

**Condizioni:**
1. **Restano attivi** il controllo degli id con nuovo invio dei mancanti e i lotti da 20. Oggi hanno funzionato, ma sono la ragione per cui non si è perso nulla.
2. **I `da_rivedere` vanno in coda a Matteo** nella plancia. Con le proposte 3 e 4 dovrebbero scendere sotto il 10%, cioè una decina di annunci ogni 100 casi dubbi.
3. **Per il primo mese la plancia mostra l'elenco degli scarti dell'IA** che vengono da Camere, Unioncamere, finanziarie regionali, ministeri economici e incentivi.gov.it, da scorrere in pochi minuti la settimana. In questo campione erano 11 su 59 scarti, tutti giusti. Se dopo un mese non emergono bandi persi, l'elenco si può togliere.
4. **Si applicano le 5 correzioni** e si tiene d'occhio il tasso di `da_rivedere` sui primi giorni reali. Non serve un'altra prova completa: basta confrontare in plancia, per un paio di settimane, gli esiti con le correzioni di Matteo.

Limite da tenere presente: il campione contiene 26 bandi veri. Zero errori su 26 è un buon risultato, ma con numeri così piccoli un errore grave ogni 50-100 bandi non si vedrebbe. Per questo la condizione 3 va mantenuta almeno per il primo mese.
