# Istruzioni per gli agenti che smaltiscono l'arretrato di Bandi Radar (sessione del 28/09/2026)

Lavori al posto dell'API Anthropic: fai esattamente quello che farebbe il modello chiamato dal programma, leggendo
gli stessi testi. Cartella di lavoro: `/tmp/claude-1000/ar/`. Per ogni bando c'è una cartella `fascicoli/<id>/`.

**Strumenti: Read e Write.** Unica eccezione per Bash: il comando della coda scritto sotto, esattamente così.
Niente WebFetch, niente ricerche in rete: le informazioni devono venire solo dai file del fascicolo (regola
"niente invenzioni"). Non modificare nessun altro file. Ogni sequenza di comandi e' vietata (niente `&&`, `|`, `cd`).

## Fase A — controllo preliminare

1. Leggi una volta `/tmp/claude-1000/ar/istruzioni_preliminare.md` (sono le istruzioni di sistema).
2. Prendi gli id dalla coda: `python3 /tmp/claude-1000/ar/coda.py A 20 1` (stampa una riga con fino a 20 id e li
   prenota per te). Se non stampa nulla, la coda e' vuota: fermati.
3. Per ogni id: leggi `fascicoli/<id>/preliminare.md` e scrivi `fascicoli/<id>/preliminare.json` con **solo** questo
   oggetto JSON (nessun testo prima o dopo):
   `{"destinatari": ["imprese", "non_profit", "enti_pubblici", "persone_fisiche", "altri"], "agevolazione": "si|no", "edizione_in_corso": "si|no|incerto", "stato": "aperto|in_arrivo|chiuso|non_noto", "testo_bando": "si|solo_sintesi|no", "motivo": "una frase, massimo 25 parole"}`
   In `destinatari` metti solo le categorie che possono presentare domanda (spiegate nelle istruzioni del
   preliminare), lista vuota `[]` se il testo non basta. Dal 07/10 non si scrive piu' `per_imprese`: lo ricava il
   programma. I bandi solo per il non profit (associazioni, ETS, ASD...) vanno avanti alla scheda, dopo quelli per
   imprese.
4. **Seconda lettura.** Se hai scritto `"stato": "chiuso"` e nella cartella esiste il file `aperto`, leggilo: sono
   dati raccolti dalla fonte che dicono il contrario (per esempio una scadenza futura). Rileggi con attenzione date
   di apertura e chiusura, proroghe e avvisi di chiusura anticipata; rispondi "chiuso" solo se il testo dice
   chiaramente che le domande non si possono piu' presentare, altrimenti "aperto", "in_arrivo" o "non_noto", e nel
   motivo scrivi quale data hai trovato. Riscrivi `preliminare.json` con la decisione finale.
5. Ogni file va letto davvero prima di rispondere: mai un preliminare "a occhio" o "file non letto". Se non riesci a
   leggere un file, non scrivere il .json e dillo nella risposta finale. Valori ammessi solo quelli dell'esempio.
6. Finito il gruppo, lancia **una seconda volta** il comando della coda e fai il nuovo gruppo. Poi fermati.

## Fase B — scheda

1. Leggi una volta `/tmp/claude-1000/ar/istruzioni_scheda.md` (istruzioni di sistema: regole e formato JSON).
   Rispettale tutte.
2. Prendi gli id dalla coda: `python3 /tmp/claude-1000/ar/coda.py B 5 1`. Se non stampa nulla, fermati.
3. Per ogni id: leggi **per intero** `fascicoli/<id>/scheda.md`. Se il file e' lungo, leggilo a pezzi con
   offset/limit (per esempio 800 righe alla volta) fino in fondo: il bando e' il primo documento, ma FAQ e decreti
   successivi possono cambiare date e importi.
4. Scrivi `fascicoli/<id>/scheda.json` con **solo** l'oggetto JSON della scheda, con tutte le chiavi del formato
   (anche quelle vuote: `null` o `[]`), valori ammessi scritti esattamente come negli elenchi, date `AAAA-MM-GG`,
   ore `HH:MM`, importi come numeri senza separatori. JSON valido: virgolette doppie, niente commenti, niente
   virgole finali, niente blocchi ```.
5. In `fonti` una coppia per ogni campo pieno (anche `sintesi`, `temi`, `tipi_agevolazione`, territorio e ogni
   blocco di dettagli compilato).
6. Se `scheda.json` esiste gia', salta quell'id. Finito il gruppo, lancia **una seconda volta** il comando della
   coda e fai il nuovo gruppo. Poi fermati.

## Alla fine

Rispondi con **una sola riga**: `fatto: <N> file scritti` e, solo se ci sono stati, `; problemi: <id> <una frase>`.
I risultati stanno nei file: non ripeterli nella risposta.

## Fase S — smistamento degli annunci "da rivedere"

1. Prendi i lotti dalla coda: `python3 /tmp/claude-1000/ar/coda_s.py 3` (stampa fino a 3 nomi di lotto, es.
   `lotto_007 lotto_008 lotto_009`, e li prenota). Se non stampa nulla, fermati.
2. Per ogni lotto: leggi **per intero** `/tmp/claude-1000/ar/smista/<lotto>.md`. Contiene le istruzioni di sistema
   (seguile alla lettera) e il messaggio con circa 20 annunci. Scrivi `/tmp/claude-1000/ar/smista/<lotto>.json`
   con **solo** l'oggetto JSON richiesto: `{"risposte": [{"id": 123, "esito": "rilevante|non_rilevante|da_rivedere", "motivo": "..."}]}`,
   una risposta per **ogni** annuncio del lotto, con il suo id esatto, nessun id inventato o ripetuto.
3. Finiti i lotti, lancia **una seconda volta** il comando della coda e fai i nuovi lotti. Poi fermati.
