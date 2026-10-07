# Strumenti delle sessioni sul server

*Portati nel repository il 02/10/2026 (analisi della struttura): stavano in `/tmp/claude-1000/`, che Ubuntu svuota dopo 30 giorni, eppure scrivono le schede nel database di produzione.*

Servono alle sessioni di Claude Code **sul server** per fare a mano, con gli agenti, il lavoro che altrimenti fa l'API (arretrati, smistamento, doppioni, schede), con gli stessi prompt e gli stessi controlli del programma. Non fanno parte del sistema automatico.

## Installazione all'inizio di una sessione

Gli script usano percorsi fissi in `/tmp/claude-1000/` (la cartella di lavoro di Claude Code sul server). Basta `bash strumenti/sessione/installa.sh`, che fa questo:

```
mkdir -p /tmp/claude-1000/ar /tmp/claude-1000/fd /tmp/claude-1000/cp
cp strumenti/sessione/ar/* /tmp/claude-1000/ar/
cp strumenti/sessione/sh/*.sh /tmp/claude-1000/
cp strumenti/sessione/sh/controlli.sh /tmp/claude-1000/fd/
cp strumenti/sessione/sh/foto.py /tmp/claude-1000/cp/
chmod +x /tmp/claude-1000/*.sh /tmp/claude-1000/fd/*.sh
```

## Il lavoro tipico: "fai le schede in attesa"

Finché `IA_SCHEDE_API` non è 1 nel `.env` (decisione di Matteo del 02/10), l'API fa smistamento, doppioni e controlli preliminari; **le schede si scrivono in sessione**. Dopo `installa.sh`:

1. `/tmp/claude-1000/ar.sh esporta.py` → fascicoli dei bandi con il testo ufficiale: nuovi, già passati dal controllo preliminare dell'API, e con la scheda "da aggiornare";
2. `python3 /tmp/claude-1000/ar/coda.py conta` → quanti per la Fase A e la Fase B;
3. agenti (al massimo 5 insieme) con il prompt "Leggi /tmp/claude-1000/ar/ISTRUZIONI_AGENTI.md e fai la Fase A (o B)…";
4. **`/tmp/claude-1000/ar.sh importa.py` appena ogni agente finisce** (il 02/10 un riavvio del server ha cancellato 49 schede non ancora importate).

## Cosa c'è

| File | A cosa serve |
|---|---|
| `sh/sql.sh` | query sul database di produzione (`sql.sh "SELECT ..."` o `sql.sh -f file.sql`) |
| `sh/ar.sh` | lancia uno script di `ar/` nel servizio raccolta di produzione (codice di `main`) |
| `sh/ar_copia.sh`, `sh/modulo_copia.sh`, `sh/copia.sh` | come sopra ma con il **codice della copia di lavoro** (`~/bandi-radar`): solo per provare un branch. Attenzione: un comando che applica le migrazioni porterebbe in produzione quelle del branch |
| `sh/test_vuoto.sh` + `sh/controlli.sh` | tutti i test, anche quelli sul database, su un Postgres di prova vuoto |
| `sh/app_prova.sh`, `sh/foto.sh`, `foto.py` | plancia del branch su 127.0.0.1:8090 (dati di produzione, senza migrazioni) e fotografie con Chromium |
| `sh/plancia_build.sh` | controllo dei tipi e build della plancia |
| `sh/ramo.sh`, `sh/aspetta_deploy.sh` | branch nuovo da `main`; attesa che una migrazione arrivi in produzione |
| `ar/ISTRUZIONI_AGENTI.md` | istruzioni per gli agenti: Fase A (controllo preliminare), Fase B (scheda), Fase S (smistamento) |
| `ar/esporta.py`, `ar/importa.py` | fascicoli dei bandi con il testo ufficiale (`documentazione = 'bando'`) e importazione di preliminari e schede |
| `ar/esporta_smista.py`, `ar/importa_smista.py`, `ar/coda_s.py` | lotti di annunci "da rivedere" per lo smistamento |
| `ar/esporta_doppioni.py`, `ar/importa_doppioni.py` | doppioni che le regole del regista non decidono |
| `ar/coda.py`, `ar/libera.py` | coda dei fascicoli tra gli agenti (`coda.py conta`), liberazione delle prenotazioni di un agente fermo. Dal 07/10 la Fase B dà prima i bandi per imprese, poi quelli solo per il non profit (priorità bassa) |
| `ar/deriva_destinatari.py` | (07/10) destinatari dei bandi decisi prima del 07/10, senza IA, dal preliminare e dalla scheda: dove è sicuro li scrive, altrimenti "da_determinare"; non cambia mai `per_imprese`. Prima `ar.sh deriva_destinatari.py` (prova, niente scritto, dettaglio in `ar/destinatari_prova.tsv`), poi `--applica` |
| `ar/regole_stato.py`, `ar/pagine_oggi.py`, `ar/ISTRUZIONI_STATO.md`, `ar/importa_stato.py` | ricontrollo a mano dello stato dei proponibili (03/10): regole di chiusura senza IA, pagina ufficiale di oggi (una per sito alla volta), agenti che decidono aperto/chiuso con la citazione, salvataggio con il motivo |
| `ar/regole_imprese.py`, `ar/esporta_imprese.py`, `ar/ISTRUZIONI_IMPRESE.md`, `ar/importa_imprese.py` | ricontrollo a mano dei beneficiari (03/10): regole sui testi, modulistica compresa; i "non per imprese" escono dal catalogo |
| `ar/esporta_lunghi.py`, `ar/ISTRUZIONI_LUNGHI.md`, `ar/importa_lunghi.py` | bandi lunghissimi (06/10): scheda in due passaggi, con indice dei documenti (titoli e articoli con il numero di riga) e testi completi in file separati; l'agente apre solo le parti che servono. `ar_copia.sh esporta_lunghi.py ID ...`, agenti, poi `importa_lunghi.py` |
| `ar/rifai.py` | rifare preliminare e scheda di alcuni bandi (per esempio dopo la rilettura OCR) |
| `ar/esporta_feedback.py`, `ar/ISTRUZIONI_FEEDBACK.md`, `ar/importa_feedback.py` | feedback sulle schede (05/10): segnalazioni di revisori e imprese rilette dagli agenti sui documenti; correzioni nella scheda con la causa "feedback N", schede da rifare rimesse "da aggiornare", regole proposte da riportare a Matteo |

## Feedback sulle schede

Revisori e imprese votano le schede e segnalano errori (tabella `feedback`, pagina Feedback della plancia). Dopo `installa.sh`:

1. `/tmp/claude-1000/ar.sh esporta_feedback.py` → una cartella `/tmp/claude-1000/ar/feedback/<id>/` per ogni segnalazione nuova con problemi o commento (senza dati di chi scrive); il feedback passa a "preso in carico". Il riepilogo dice quali bandi hanno più segnalazioni: vanno allo stesso agente;
2. agenti (al massimo 5 insieme) con il prompt "Leggi /tmp/claude-1000/ar/ISTRUZIONI_FEEDBACK.md e lavora le cartelle 12, 15, 18";
3. **`/tmp/claude-1000/ar.sh importa_feedback.py` subito dopo ogni agente** (prima con `--prova` se l'esito è dubbio): applica le correzioni, rimette "da aggiornare" le schede da rifare, scrive la risposta per chi ha segnalato. Gli esiti con errori restano "preso in carico": si correggono e si reimportano;
4. riporta a Matteo le **regole proposte** stampate alla fine (sono anche in `/tmp/claude-1000/ar/feedback/regole_proposte.md`): cambiare il prompt o i controlli lo decide lui.

## Regole

- Ogni sequenza di comandi va in uno script (niente `&&`, `|`, `cd` sulla riga di comando).
- Al massimo 5-6 agenti insieme (quota dell'abbonamento).
- Dal 02/10 ogni passo della catena prende un blocco nel database (`app/db/blocchi.py`): un comando lanciato a mano mentre il regista fa lo stesso passo si salta da solo e lo dice.
