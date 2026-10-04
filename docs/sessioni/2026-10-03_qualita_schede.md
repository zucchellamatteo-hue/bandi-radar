# Sessione sul server: qualità delle schede proponibili

*Eseguito il 03-04/10/2026: risultati in `docs/ricerche/2026-10-02_verifica_schede.md`, sezione "Seconda misura".*

*Piano preparato il 02/10/2026 dopo la verifica a campione (`docs/ricerche/2026-10-02_verifica_schede.md`). Da incollare in una nuova sessione di Claude Code sul server (cartella `~/bandi-radar` dell'utente `ubuntu`).*

---

Leggi prima `CLAUDE.md`, `docs/ricerche/2026-10-02_verifica_schede.md` (e i verdetti in `docs/ricerche/2026-10-02_verifica_schede/`), `docs/ORCHESTRAZIONE.md`, `strumenti/sessione/README.md` e `app/schede/campi.py`. Parla con Matteo in italiano semplice, proponi una strada sola. Matteo ha autorizzato in anticipo: procedi e unisci le PR con i controlli verdi senza chiedere; chiedi solo per spese o azioni irreversibili. Le schede si scrivono in sessione con gli agenti (`IA_SCHEDE_API=0`), al massimo 5 agenti insieme, e **si importano subito** dopo ogni agente (un riavvio svuota `/tmp`).

**Prima di tutto**: `bash strumenti/sessione/installa.sh`, poi `python3 /tmp/claude-1000/ar/coda.py conta` (il 02/10 restavano 6 schede da fare nella coda: chiudile).

## Il problema, in breve

Verifica di 20 schede proponibili aperte: 87% dei campi giusti, 1% sbagliati, voto medio 4,3. Ma **4 bandi su 20 non andrebbero proposti**: 2 chiusi o non più attivi (427, 3533) e 2 non per imprese (2138 società sportive, 2147 enti titolari di musei). In entrambi i casi la smentita non sta nel testo del bando ma altrove: l'avviso di chiusura sulla pagina ufficiale, il modulo di domanda. Poi: avvertenze "manca l'allegato" false in 5 su 20, bandi a più misure ridotti a un numero solo, 232 schede con ATECO "vincolo" senza codici.

**Obiettivo della sessione**: nessun bando chiuso o non per imprese tra i proponibili aperti, almeno il 90% dei campi giusti su un nuovo campione.

## Il lavoro, in ordine (il più grave prima)

### 1. Bandi chiusi che risultano aperti (regole + sessione, poi automatico)

- **Regole senza IA** sulle 387 proponibili aperte o in arrivo: rileggere il testo della pagina ufficiale già scaricata (allegato `tipo='pagina'`) e i documenti più recenti, cercando frasi di chiusura ("piattaforma chiusa", "termini scaduti", "chiusura dello sportello", "esaurimento delle risorse", "graduatoria definitiva", "sospeso"), date di chiusura già passate, e programmi vecchi ("2014-2020", "POR FESR 2014") senza atti degli ultimi 12 mesi. Prima conta quante ne prende ogni regola con `sql.sh`, poi decidi le soglie.
- **I dubbi in sessione**: un agente per gruppo di 10 legge la pagina ufficiale **di oggi** (scaricata con lo User-Agent di Bandi Radar, una pagina per sito alla volta) e decide `aperto / chiuso / esaurito / non chiaro` con la citazione. I chiusi: `stato='chiuso'`, scadenza se nota, nota nella scheda.
- **Rendere il controllo permanente** (PR): un passo del regista "ricontrollo dello stato" che ogni settimana riscarica la pagina ufficiale dei bandi aperti (rispettando robots.txt e la frequenza), confronta con la versione precedente come l'osservatore (senza IA) e, se compare una frase di chiusura, segna `da_aggiornare='chiusura'`. Va nella pagina Supervisione (`app/sistemi.py`) e nella Lavorazione.
- **I 97 proponibili senza stato**: stessa procedura, decidere lo stato.

### 2. Bandi che non sono per imprese

- **Regole** sui testi di tutti i documenti delle proponibili aperte, **modulistica compresa**: "L. 398/1991", "non ente commerciale", "associazioni sportive dilettantistiche", "enti del terzo settore" come unici beneficiari, "Comuni", "enti locali", "istituti scolastici", "persone fisiche"/"famiglie" senza impresa. Prima misura quante ne prende; attenzione alle cooperative e imprese sociali, che **sono** imprese.
- **I dubbi in sessione**, con la stessa regola del preliminare: se un bando non è per imprese esce dai proponibili (stato del preliminare `per_imprese='no'`, la scheda resta nello storico).
- **Preliminare più severo** (PR su `istruzioni_preliminare.md` e sul prompt del preliminare dell'API): il campo `per_imprese` va deciso leggendo **anche il modulo di domanda** e le dichiarazioni richieste, non solo l'articolo "beneficiari". Aggiungere i casi visti (2138, 2147) come esempi.

### 3. Fascicoli incompleti ("manca l'allegato" quando c'è)

- **Causa già trovata il 02/10 per 4109**: gli "Avviso Asse II Allegato B)" e "Asse III Allegato C)" sono nel database ma con `categoria = 'modulistica'` (il nome "Allegato" li fa sembrare moduli), e `documenti_per_scheda` (`app/schede/allegati.py`) lascia fuori la modulistica. Correggere la classificazione (un "Allegato" che contiene un avviso, articoli, intensità o beneficiari non è modulistica: guardare il testo, non solo il nome), riclassificare i documenti già scaricati, poi verificare se spiega anche 833, 3603, 4043, 4163.
- Capire la causa su 833, 3603, 4043, 4109, 4163: confronta i documenti nel database con quelli che `esporta.py` mette nel fascicolo (troncamento prima della PR #43 del 02/10? documenti di categoria `modulistica` esclusi? limite di caratteri?). Correggere l'esportazione se serve.
- Trovare tutte le schede proponibili aperte le cui avvertenze dicono che manca un documento che invece c'è (cerca nelle avvertenze "non è tra i documenti", "non disponibile", "manca" e confronta con i nomi degli allegati) e rifarle con `rifai_scheda.py`.

### 4. Istruzioni della scheda: misure multiple, premialità, fondi esauriti, ATECO a parole

Una PR su `app/schede/prompt_scheda.md` (lo usano sia la sessione sia l'API) e su `verifica_scheda`:
- **Percentuale** = intensità **base**; le maggiorazioni vanno nei dettagli e nelle avvertenze. **Contributo massimo** = il più alto tra le misure, con la ripartizione per misura nella sintesi. Bando a più misure o assi: dirlo nella prima riga della sintesi.
- **Fondi esauriti / lista d'attesa**: se un atto lo dice, va nella prima riga della sintesi e nelle avvertenze.
- **ATECO a parole**: quando il bando descrive i settori ("imprese turistiche", "commercio al dettaglio"), tradurli in sezioni o divisioni ATECO con la citazione e un'avvertenza "codici ricavati dalla descrizione". Poi un giro di sessione sulle 232 schede con ATECO "vincolo" senza codici (solo il campo ATECO, non tutta la scheda): è il buco che pesa di più sull'abbinamento con i profili.
- **Territorio**: se il bando è limitato a una regione o provincia, il campo strutturato va compilato anche quando è solo nel testo (3677).

### 5. Rifare le schede vecchie (dopo i punti 1-4)

Le 241 schede del 26/09 (99 aperte) hanno problemi segnalati nel 90% dei casi: istruzioni più vecchie. Rifare con `rifai_scheda.py` **prima le 99 aperte**, a gruppi di 10 per agente, importando dopo ogni agente. Le chiuse possono aspettare.

### 6. Forma dell'incentivo sulle schede aperte

Dal 02/10 la scheda ha la sezione "Forma dell'incentivo" (blocco `forma_incentivo`: forme dell'aiuto, quota della spesa, massimale, una riga per gruppo di beneficiari o linea). Le schede nuove o rifatte la compilano da sole; per le altre la plancia la ricava dai campi, in modo meno preciso. Prova del 02/10 su 10 bandi (599, 607, 833, 1008, 2476, 3603, 3659, 4105, 4109, 4159): molto meglio della versione ricavata (per esempio 3659: quattro intensità e il premio fisso, dove la ricavata aveva un numero solo).
- **Dopo il punto 3** (così gli allegati riclassificati entrano nei testi): `ar.sh esporta_forma.py` (tutte le proponibili aperte senza la sezione compilata, circa 375), agenti con il prompt "Leggi /tmp/claude-1000/ar/ISTRUZIONI_FORMA.md e app/schede/prompt_scheda.md (punto 12, forma_incentivo), poi seguile per i bandi …" (10 bandi per agente, lavoro da solo), `ar.sh importa_forma.py` dopo ogni agente. Le schede rifatte al punto 5 non servono: la compilano già.
- Rifare con `esporta_forma.py <id>` i 10 della prova se il punto 3 cambia i loro documenti (4109 e 833 di sicuro).

### 7. Misurare di nuovo

- Nuovo campione di 20 (cambia il seme in `esporta_verifica.py`, per esempio `'verifica-03-10'`) più i 4 bandi sbagliati del 02/10, stesse istruzioni (`/tmp/claude-1000/ar/verifica/ISTRUZIONI.md`, la copia è nei verdetti del 02/10). Riporta i numeri a confronto con il 02/10 nello stesso file di ricerca.
- Chiedi a Matteo di votare 10 schede nella plancia (campo `qualita`, oggi 0 voti): è l'unico giudizio esperto che abbiamo.

## Cosa NON fare

- Non togliere bandi dal catalogo senza traccia: chiusi e non per imprese restano nel database, con il motivo.
- Non scaricare in modo aggressivo le pagine ufficiali per il controllo dello stato: una pagina per sito alla volta, robots.txt, User-Agent di Bandi Radar.
- Non usare la parola "gara" come filtro.
- Non accendere `IA_SCHEDE_API`: le schede restano in sessione finché il servizio non è venduto.
