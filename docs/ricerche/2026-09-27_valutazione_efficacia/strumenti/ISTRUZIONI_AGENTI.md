# Istruzioni per gli agenti che compilano le schede di Bandi Radar (sessione del 26/09/2026)

Lavori al posto dell'API Anthropic: fai esattamente quello che farebbe il modello chiamato dal programma, leggendo
gli stessi testi. Cartella di lavoro: `/tmp/claude-1000/sp/schede/`. Per ogni bando c'è una cartella
`fascicoli/<id>/`.

**Strumenti: usa solo Read e Write.** Niente Bash, niente WebFetch, niente ricerche in rete: le informazioni
devono venire solo dai file del fascicolo (regola "niente invenzioni"). Non modificare nessun altro file.

## Fase A — controllo preliminare (se ti è stato chiesto)

1. Leggi una volta `istruzioni_preliminare.md` (sono le istruzioni di sistema).
2. Per ogni id: leggi `fascicoli/<id>/preliminare.md` e scrivi `fascicoli/<id>/preliminare.json` con **solo** questo
   oggetto JSON (nessun testo prima o dopo):
   `{"per_imprese": "si|no|incerto", "edizione_in_corso": "si|no|incerto", "stato": "aperto|in_arrivo|chiuso|non_noto", "testo_bando": "si|solo_sintesi|no", "motivo": "una frase, massimo 25 parole"}`
3. Se `preliminare.json` esiste già, salta quell'id.
4. **Ogni file va letto davvero** prima di rispondere: non scrivere mai un preliminare "a occhio" o con motivo
   "file non letto". Se non riesci a leggere un file, non scrivere il .json e dillo nella risposta finale.
   `testo_bando` ammette solo `si`, `solo_sintesi`, `no`; `stato` solo `aperto`, `in_arrivo`, `chiuso`, `non_noto`.

## Fase B — scheda (se ti è stato chiesto)

1. Leggi una volta `istruzioni_scheda.md` (istruzioni di sistema: 26 regole e il formato JSON). Rispettale tutte.
2. Per ogni id: leggi **per intero** `fascicoli/<id>/scheda.md`. Se il file è lungo, leggilo a pezzi con
   offset/limit (per esempio 800 righe alla volta) finché non arrivi in fondo: il bando è il primo documento, ma
   FAQ e decreti successivi possono cambiare date e importi.
3. Scrivi `fascicoli/<id>/scheda.json` con **solo** l'oggetto JSON della scheda, con tutte le chiavi del formato
   (anche quelle vuote: `null` o `[]`), valori ammessi scritti esattamente come negli elenchi, date `AAAA-MM-GG`,
   ore `HH:MM`, importi come numeri senza separatori. JSON valido: virgolette doppie, niente commenti, niente
   virgole finali, niente blocchi ```.
4. In `fonti` una coppia per ogni campo pieno (anche `sintesi`, `temi`, `tipi_agevolazione`, territorio e ogni
   blocco di dettagli compilato).
5. Se `scheda.json` esiste già, salta quell'id.

## Fase B a coda (se ti è stato chiesto "prendi dalla coda")

Unica eccezione alla regola "niente Bash": puoi lanciare **solo** questo comando, esattamente così:
`python3 /tmp/claude-1000/sp/coda.py B 5 1`
Stampa una riga con 5 id da schedare (e li prenota per te). Fai la Fase B su quegli id, poi lancialo **una seconda
volta** e fai la Fase B sui nuovi id. Poi fermati. Se il comando non stampa nulla, la coda è vuota: fermati.

## Alla fine

Rispondi con **una sola riga**: `fatto: <N> file scritti` e, solo se ci sono stati, `; problemi: <id> <una frase>`.
I risultati stanno nei file: non ripeterli nella risposta.
