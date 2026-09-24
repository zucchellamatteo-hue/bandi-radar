# Richiesta per la chat di progetto delle anagrafiche

*Testo da incollare nella chat (Claude Code o altro) del progetto che ha generato il database Postgres delle anagrafiche dei clienti. Serve a Bandi Radar per la Fase 4 (profili anonimi e abbinamento). Preparato il 24/09/2026.*

---

Sto costruendo un sistema separato, **Bandi Radar**, che abbina i bandi di finanza agevolata ai miei clienti. Non deve conoscere nomi, email o dati identificativi: riceve solo **profili anonimi** (un codice interno più le caratteristiche dell'impresa). Per scrivere lo script che legge le anagrafiche da questo database e produce i profili, mi serve la **struttura delle tabelle, senza dati**.

Per favore preparami un file `schema_anagrafiche.md` con:

1. **Come si raggiunge il database**: nome del container Docker, nome del database, nome dello schema Postgres (se non è `public`), utente di sola lettura se esiste (non scrivere la password: dimmi solo dove sta).

2. **Le tabelle che descrivono le imprese clienti** e quelle collegate (sedi, soci, attività, referenti, documenti). Per ogni tabella: nome, a cosa serve in una riga, chiave primaria, numero indicativo di righe.

3. **Per ogni colonna di quelle tabelle**: nome, tipo Postgres, se può essere vuota, cosa contiene in parole semplici, un esempio di valore **inventato** (mai un valore reale). Segna con una stella le colonne che contengono dati identificativi (ragione sociale, partita IVA, codice fiscale, email, telefono, indirizzo, nomi di persone): Bandi Radar non le leggerà mai.

4. **In particolare, dove trovo queste informazioni** e in che formato sono scritte (se mancano, dillo):
   - codice ATECO principale e secondari (con o senza punti? versione 2007 o 2025?)
   - forma giuridica (srl, snc, ditta individuale, ecc.)
   - comune, provincia e regione della sede legale e delle sedi operative
   - data di costituzione o di inizio attività
   - dimensione: numero di dipendenti o ULA, fatturato e totale attivo dell'ultimo bilancio (o classe dimensionale se già calcolata)
   - impresa femminile, giovanile, start-up innovativa, PMI innovativa, iscrizione all'albo artigiani, cooperativa, impresa agricola
   - export: vende all'estero sì/no, o percentuale
   - regime contabile e settore (commercio, manifattura, servizi, turismo, agricoltura)
   - aiuti già ricevuti (de minimis) se li registriamo
   - stato del cliente (attivo, cessato, in prova) e data dell'ultimo aggiornamento della riga

5. **Le relazioni tra le tabelle** (chiavi esterne) in un elenco o in un disegno testuale.

6. **Il comando esatto** con cui hai estratto lo schema (per esempio `pg_dump --schema-only` dentro il container), così posso rifarlo quando le tabelle cambiano.

Regole: solo struttura, **nessuna riga di dati reali**, nemmeno come esempio. Se una delle informazioni del punto 4 non esiste nel database, scrivilo chiaramente: deciderò se aggiungerla lì o chiederla a mano.
