# Sessione sul server: la struttura delle schede prima di collegare l'IA

*Prompt preparato il 25/09/2026 dalla sessione sul server, dopo la prova dell'IA. Da incollare in una nuova sessione di Claude Code sul server (cartella `~/bandi-radar` dell'utente `ubuntu`).*

---

Leggi prima `CLAUDE.md`, poi `docs/PIANO_PROGETTO.md` (§5b, §7, §9 e §10, in particolare le decisioni del 25/09), `docs/SCHEDA_BANDO.md`, `docs/RICHIESTA_SCHEMA_ANAGRAFICHE.md` e `deploy/MANUALE.md`. Poi i risultati della prova dell'IA: `docs/ricerche/2026-09-25_prova_ia.md` e i rapporti in `docs/ricerche/2026-09-25_prova_ia/` (soprattutto `revisione_struttura.md`, poi `revisione_schede_A.md`, `revisione_schede_B.md`, `revisione_smistamento.md`).

Sei sul server di produzione. La produzione è in `/srv/bandi-radar` (non toccarla a mano); tu lavori nella copia `~/bandi-radar` su un branch per parte e apri pull request verso `main`. Parla con Matteo in italiano semplice, proponi una strada sola e spiega perché. Aggiorna `~/bandi-radar` con `git pull origin main` prima di ogni parte.

## Dove siamo

- In produzione: raccolta da 287 fonti (~4.400 annunci), smistamento a regole già eseguito (tabella `smistamenti`), scaricamento allegati (tabella `allegati`, volume Docker `allegati`), tabella `bandi` ancora vuota (migrazione `app/db/migrazioni/004_schede.sql`). La plancia mostra lo smistamento nel Catalogo.
- Il 25/09 Haiku e Sonnet sono stati provati su dati reali, senza chiave API, con revisione di Opus. Esito: **l'impianto regge e i modelli sono quelli giusti**. Sonnet non inventa, ma in 5 schede su 10 non ha ricevuto il bando ufficiale, e i campi della scheda non bastano per l'abbinamento. Haiku sbaglia ancora troppo per decidere da solo.
- Matteo ha approvato i **tre cambi di struttura** qui sotto, da fare **prima** di collegare l'API. La chiave `ANTHROPIC_API_KEY` non c'è ancora: non chiamare mai l'API.

## Il lavoro, in quattro parti

Ogni parte è una pull request, con test `pytest` (senza rete) e una prova sulla **copia** del database di produzione, mai sull'originale. Come si fa una copia: `pg_dump` dal container `db` di produzione verso un Postgres temporaneo in Docker, immagini costruite con un nome di progetto separato (`docker compose -p bandiprova ...`). Poi rimuovi tutto quello che hai creato. Le migrazioni nuove devono essere **aggiuntive**: i dati esistenti (annunci, smistamenti, allegati, correzioni di Matteo) non si perdono, e vanno travasati nella nuova struttura dentro la migrazione.

### Parte 1. Annuncio e bando separati

Oggi ogni annuncio rilevante diventerebbe una scheda a sé. Lo stesso bando però arriva da più fonti (catalogo nazionale, Regione, Camera, notizia di Unioncamere), e proroghe, rettifiche, graduatorie e FAQ devono aggiornare la scheda esistente.

1. **Modello dei dati.**
   - Un bando ha molti annunci: legame annuncio → bando, con un ruolo (`origine`, `doppione`, `proroga`, `rettifica`, `graduatoria`, `faq`, `chiusura`).
   - Gli allegati appartengono al bando, non all'annuncio.
   - Aggiungi alla scheda la chiave per riconoscere i doppioni: codice ufficiale del bando se c'è (es. `RLO12026055023` della Lombardia), indirizzo della pagina ufficiale ripulito, ente + edizione + titolo normalizzato.
   - A ogni aggiornamento della scheda si conserva la versione precedente (lo storico completo arriva più avanti).
2. **Deduplica senza IA**, da lanciare a mano come gli altri comandi (per esempio `python -m app.schede.bandi`): crea o collega i bandi a partire dagli annunci rilevanti usando le chiavi sopra. I casi dubbi restano da decidere; più avanti li deciderà Haiku, oggi li decide Matteo dalla plancia.
3. **Plancia.** Nella pagina dell'annuncio, il bando a cui è collegato e gli altri annunci dello stesso bando. Un modo per unire o separare a mano due annunci.
4. **Prova sulla copia:** quanti bandi escono dai ~1.250 annunci rilevanti, 20 esempi di doppioni trovati, 10 di dubbi. La revisione di Opus stimava circa 500 bandi.

### Parte 2. Trovare la pagina ufficiale del bando

In 5 schede su 10 il bando vero non è arrivato al modello. Aggiungi un passo "trova la pagina ufficiale" **prima** di scaricare gli allegati, con regole scritte nel registro delle fonti (un campo nuovo, documentato in `fonti/README.md`), non nel codice:

- **incentivi.gov.it:** seguire il link all'ente (campo `link_ente` nei dati grezzi dell'annuncio).
- **Lombardia:** i link `.../faiDomanda?strumentoCod=CODICE` portano alla domanda con login; la pagina di dettaglio con lo stesso codice è quella giusta. Esempio verificato il 25/09: `https://www.bandi.regione.lombardia.it/servizi/servizio/bandi/dettaglio/attivita-produttive-imprese/fiere/pr-fesr-2021-2027-azione-1-3-1-contributi-partecipazione-pmi-fiere-internazionali-lombardia-secondo-sportello-RLO12026055023`. Trova il modo di arrivarci dal codice (dati aperti di Regione Lombardia, fonte `lombardia_anagrafica_bandi_api`, o la ricerca del sito), senza ricostruire indirizzi a memoria.
- **Notizie di Unioncamere e Camere:** seguire il link "bando e modulistica" verso il sito dell'ente.
- **Pagine che non contengono un bando** (login, pagina vuota, solo menu): segnare il bando come "bando ufficiale non trovato". Niente scheda finché non si trova.

Negli allegati, metti in ordine i documenti: prima il bando, poi le FAQ e l'ultimo decreto, poi il resto. La modulistica non va nel testo per Sonnet. Controlla anche perché l'annuncio 2814 (Emilia-Romagna) non ha scaricato allegati. Prova sulla copia con i 10 bandi della prova (id in `docs/ricerche/2026-09-25_prova_ia.md`) e con altri 20 a caso: quante pagine ufficiali trovate, quante no, e perché.

### Parte 3. Campi della scheda per l'abbinamento

I campi che servono ad abbinare un bando a un profilo anonimo oggi sono testo libero o mancano. Partendo dalla sezione 1 di `revisione_struttura.md` e da come struttura i dati incentivi.gov.it (vedi `docs/ricerche/2026-09-25_prova_ia/` e i dati grezzi degli annunci della fonte `incentivi_gov_ricerca`):

1. **Nuovi campi a valori controllati** in migrazione, `docs/SCHEDA_BANDO.md` e `app/schede/prompt_scheda.md`:
   - territorio in codici (regione, provincia, comune; tipo di sede richiesta);
   - soggetti ammessi (impresa, professionista, ente, associazione...) e forme giuridiche;
   - dimensioni ammesse, età dell'impresa, requisiti speciali (impresa femminile, giovanile, start-up innovativa...);
   - soglie di dipendenti e fatturato, spesa minima e massima;
   - regime di aiuto (de minimis, GBER...) e versione ATECO (2007 o 2025);
   - più tipi di agevolazione e più temi;
   - quota a fondo perduto separata dal prestito;
   - modalità di selezione (sportello, graduatoria, click day);
   - ente finanziatore separato dal gestore;
   - ora di scadenza.
2. **Tre stati per ogni vincolo:** "il bando pone un vincolo", "dice che non ce ne sono", "non lo sappiamo". L'abbinamento non tratterà mai "non lo sappiamo" come "va bene". Aggiungi alla scheda un grado di completezza.
3. **Linee del bando:** un elenco facoltativo di "linee" o misure, ciascuna con i suoi massimali, percentuali e beneficiari. Nella prova, 6 schede su 8 ne avevano più di una.
4. **Lo stato del bando** (aperto, chiuso, in arrivo) lo calcola il sistema ogni giorno dalle date, non lo scrive l'IA.
5. **Allinea con il profilo cliente:** aggiorna `docs/RICHIESTA_SCHEMA_ANAGRAFICHE.md` in modo che a ogni campo di abbinamento corrisponda un dato del profilo (aggiungi, se servono, libero professionista sì/no, ULA, categorie di investimento previste). Scrivi in `docs/SCHEDA_BANDO.md` una tabella "campo della scheda ↔ dato del profilo ↔ regola di confronto".
6. **Riscrivi a mano la scheda di esempio** di `docs/SCHEDA_BANDO.md` (bando fiere Lombardia) con i campi nuovi.
7. **Dettagli chiesti da Matteo il 25/09 sera** (sono quelli che un commercialista guarda per dire a un cliente se e quanto conviene). Aggiungili ai campi del punto 1, strutturati dove l'abbinamento o il calcolo li usano, testo con fonte dove bastano per la lettura. Valgono per il bando e, se diversi, per ogni linea:
   - **Vincoli sulle spese**: sul fornitore (niente parti correlate, soci o parenti; fornitori accreditati o iscritti a elenchi), sul bene (nuovo di fabbrica, usato ammesso o no, origine UE o "made in", leasing o noleggio ammessi), sul pagamento (tracciabile, data da cui le spese valgono: prima o dopo la domanda), IVA ammessa o no, tetti per voce di spesa (es. consulenze al massimo il 20%), spese forfettarie.
   - **Esclusioni**, separate per tipo: settori e ATECO, soggetti (imprese in difficoltà, procedure concorsuali, aiuti illegali da restituire, irregolarità contributive), spese escluse.
   - **Intensità dell'aiuto**: percentuale base per dimensione d'impresa e maggiorazioni (zone assistite, impresa femminile o giovanile, rating di legalità, altro), con la percentuale massima risultante.
   - **Fondo perduto e finanziamento distinti**: quota o importo di ciascuno sul totale (es. 30% fondo perduto + 70% prestito); per la parte finanziata **tasso** (zero, fisso, percentuale del tasso di riferimento), durata, preammortamento, garanzie richieste; se c'è una garanzia pubblica, la copertura.
   - **Massimali**: spesa minima e massima del progetto, contributo minimo e massimo per impresa (e per linea), dotazione complessiva del bando o dello sportello.
   - **Tempi e obblighi**: durata massima del progetto, anticipo / stati di avanzamento / saldo, obblighi dopo il contributo (mantenere beni, sede o occupati per N anni), cumulabilità con altri aiuti.
   - **Domanda**: piattaforma, SPID o firma digitale, marca da bollo, documenti da allegare (preventivi, perizie, business plan), requisiti di regolarità (DURC, rating di legalità), criteri di punteggio.

   Stessa regola dei tre stati (vincolo / nessun vincolo / non si sa) per ogni vincolo. Nella nuova prova (Parte 4) verifica quanti di questi campi Sonnet riesce a riempire con fonte, e quanto cresce il costo per scheda.

### Parte 4. Prompt corretti e nuova prova

1. Correggi `app/schede/prompt_scheda.md` e `app/schede/prompt_smistamento.md` con le proposte dei rapporti di revisione:
   - ente come finanziatore;
   - ogni esclusione di settore anche nel campo delle esclusioni;
   - requisiti separati dai criteri di punteggio;
   - agevolazioni miste con la sola quota a fondo perduto;
   - avvertenze senza supposizioni;
   - "chi riceve i soldi" negli esempi per Haiku;
   - posteggi e fornitori accreditati tra i non rilevanti.

   Aggiungi a `regole_smistamento.yaml` le parole proposte in `revisione_smistamento.md`.
2. Prepara nel codice, **senza attivarle**, le protezioni per quando arriverà l'API:
   - controllo che la risposta di Haiku contenga tutti gli id, con rinvio dei mancanti;
   - lotti da 20-25 annunci;
   - JSON vincolato e verifica automatica di valori, date e importi;
   - uso della Batch API;
   - un controllo preliminare con Haiku prima di Sonnet: è per imprese? è l'edizione in corso? è aperto? c'è il testo del bando?

   Il codice che chiamerà l'API va scritto con l'SDK ufficiale `anthropic`, ma resta spento finché manca la chiave.
3. **Rifai la prova con lo stesso metodo del 25/09**, descritto in `docs/ricerche/2026-09-25_prova_ia.md`:
   - agenti Haiku e Sonnet che leggono solo il prompt riempito, poi agenti Opus che rivedono;
   - su un campione **nuovo**: 100 annunci per lo smistamento, 10 bandi per le schede, tra cui 2 con più linee, un catalogo incentivi.gov.it e una notizia camerale;
   - obiettivo per lo smistamento: nessun annuncio omesso e meno errori gravi e medi del 25/09 (3 e 5 su 88).

   Salva tutto in `docs/ricerche/AAAA-MM-GG_prova_ia_2.md` con il confronto con la prima prova.

## Alla fine

Scrivi a Matteo un riepilogo di 10 righe: cosa è cambiato, i numeri della nuova prova rispetto a quella del 25/09, cosa non hai potuto provare. Poi elenca cosa serve da lui:

- la chiave API con il tetto di spesa (`ANTHROPIC_API_KEY` nel `.env`), se la prova è andata bene;
- lo schema delle anagrafiche aggiornato;
- le decisioni sui doppioni dubbi, se ce ne sono.

Aggiorna `docs/PIANO_PROGETTO.md` (§9 e §10) e `deploy/MANUALE.md` con i comandi nuovi.

Regole ferme:

- mai stampare il contenuto del `.env`;
- mai `docker compose down -v`;
- mai modificare `/srv/bandi-radar`;
- mai chiamare l'API Anthropic;
- mai perdere le correzioni di Matteo;
- commit piccoli con messaggio in italiano;
- prima di dire "finito", test eseguiti ed esito riportato con onestà.
