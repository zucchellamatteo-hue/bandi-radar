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
| `ar/coda.py`, `ar/libera.py` | coda dei fascicoli tra gli agenti (`coda.py conta`), liberazione delle prenotazioni di un agente fermo |
| `ar/rifai.py` | rifare preliminare e scheda di alcuni bandi (per esempio dopo la rilettura OCR) |

## Regole

- Ogni sequenza di comandi va in uno script (niente `&&`, `|`, `cd` sulla riga di comando).
- Al massimo 5-6 agenti insieme (quota dell'abbonamento).
- Dal 02/10 ogni passo della catena prende un blocco nel database (`app/db/blocchi.py`): un comando lanciato a mano mentre il regista fa lo stesso passo si salta da solo e lo dice.
