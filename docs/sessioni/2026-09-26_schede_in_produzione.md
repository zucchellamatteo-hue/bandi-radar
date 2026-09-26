# Sessione sul server: accendere in produzione la catena delle schede (senza IA) e preparare la chiave API

*Prompt preparato il 26/09/2026, dopo l'unione delle PR #18–#24. Da incollare in una nuova sessione di Claude Code sul server (cartella `~/bandi-radar` dell'utente `ubuntu`).*

---

Leggi prima `CLAUDE.md`, `deploy/MANUALE.md` (§5, "Smistamento e allegati" e "L'IA"), `docs/PIANO_PROGETTO.md` (§9 e §10), `docs/SCHEDA_BANDO.md`, e le mappature del 25/09: `docs/ricerche/2026-09-25_deduplica.md`, `docs/ricerche/2026-09-25_pagina_ufficiale.md`, `docs/ricerche/2026-09-25_prova_ia_2.md`, `docs/ricerche/2026-09-25_fonti_difficili.md`. Parla con Matteo in italiano semplice, proponi una strada sola e dì perché. Lavori nella copia `~/bandi-radar` su un branch nuovo da `main` (`git pull origin main` prima), mai in `/srv`; ogni modifica al codice passa da una pull request.

**Permessi (importante: Matteo non vuole approvare comandi).** Da riga di comando solo comandi singoli già consentiti in `.claude/settings.local.json`. Ogni sequenza (`&&`, `|`, `;`, `cd`, pause) va scritta in uno script dentro `/tmp/claude-1000/` con lo strumento Write e lanciata col percorso assoluto. Stessa regola nei prompt degli agenti. Script già pronti della sessione precedente in `/tmp/claude-1000/fd/` (se ci sono ancora): `controlli.sh` (registro e pytest con tutta la copia di lavoro), `db_prova.sh su|giu` (Postgres temporaneo con una copia del database di produzione), `migra_prova.sh`, `prova.sh ID` (lettura di una fonte senza database).

## Dove siamo (26/09 mattina)

- In produzione (commit `0790e20`): raccolta da 287 fonti, 255 verdi in plancia; ~6.600 annunci, 4.378 smistati a regole; migrazioni fino alla `008` applicate; **tabella `bandi` vuota**: deduplica, pagina ufficiale e allegati per bando esistono nel codice ma in produzione non sono mai stati lanciati.
- Scheda: campi per l'abbinamento più i sei blocchi di dettagli chiesti da Matteo (`intensita`, `finanziamento`, `vincoli_spese`, `esclusioni`, `obblighi`, `domanda`), in `app/schede/campi.py`, prompt e `ia.py`.
- IA pronta ma spenta: manca `ANTHROPIC_API_KEY` nel `.env`.

## Il lavoro

### 1. La catena senza IA, in produzione (a mano, un passo alla volta, con i comandi del manuale)

1. `python -m app.schede.bandi --prova --esempi 20`: quanti bandi e quanti dubbi usciranno (il 25/09 sulla copia: 1.257 annunci rilevanti → 1.057 bandi, 116 dubbi). Riporta a Matteo i numeri, poi lancia senza `--prova`.
2. `python -m app.schede.pagina_ufficiale` a giri da 100 finché servono: quante pagine trovate, quante no e perché, per fonte. Le fonti con molti "non trovato" sono candidate a una regola `pagina_ufficiale` nel registro (solo regole verificate su casi veri).
3. `python -m app.schede.allegati` a giri da 50 (lento apposta): spazio occupato, errori più frequenti.
4. Controlla in plancia che le pagine Bando e Doppioni si aprano e mostrino dati sensati (il 26/09 nessuno le ha ancora viste nel browser): usa Chromium nel container `raccolta` contro `https://finanzagevolata.qiaro.it` solo se Matteo ti dà le credenziali in un file che non va stampato; altrimenti chiedigli di aprirle lui e di dirti cosa vede.
5. Chiedi a Matteo di decidere i dubbi dalla pagina Doppioni (i suoi legami non si toccano mai).

Valuta se deduplica, pagina ufficiale e allegati devono entrare nel giro orario della raccolta (come lo stato dei bandi) e proponilo a Matteo con i tempi misurati.

### 2. Piccole correzioni emerse il 25-26/09 (una PR)

- `tests/test_bandi_db.py` fa `DELETE FROM smistamenti` su tutto il database di prova: limitalo agli annunci di prova, così un errore di configurazione non può mai cancellare smistamenti veri.
- Plancia: una fonte che dal primo controllo risponde ma legge 0 elementi oggi appare come "nessuna novità trovata finora", come una fonte tranquilla (`app/raccolta/esegui.py`, `app/plancia/semaforo.py`). Serve un motivo distinto, per esempio "risponde ma non si legge nulla: controllare la voce".
- Aggiorna `docs/PIANO_PROGETTO.md` (§3b, §9, §10) con le decisioni del 25-26/09: fonti difficili (25 recuperate, 8 escluse, 12 bloccate dagli indirizzi esteri: dal PC di Matteo si aprono; l'uscita da un indirizzo italiano resta da valutare), dettagli della scheda chiesti da Matteo, PR #18–#21 unite.

### 3. Preparare la chiave API

Spiega a Matteo, passo per passo e in parole semplici, come creare nella Console Anthropic una chiave API con tetto di spesa mensile (mai le credenziali dell'abbonamento) e come aggiungerla al `.env` con `sudo nano` (lui, non tu: tu non leggi mai il `.env`). Quando c'è: `python -m app.schede.ia stato`, poi una prima prova piccola (`smista --limite 20`, `schede --limite 3`), con costo reale riportato. **Non lanciare lotti grandi né la Batch API senza il suo via libera sul costo stimato.**

## Alla fine

- Test eseguiti ed esito onesto; pull request aperte; manuale aggiornato con i comandi nuovi.
- Riepilogo per Matteo in 10 righe: quanti bandi in produzione, quante pagine ufficiali trovate, quanti allegati, cosa deve fare lui (dubbi, chiave API, 30 schede da controllare quando l'IA sarà accesa).

Regole ferme: mai stampare il `.env`; mai `docker compose down -v`; mai modificare `/srv/bandi-radar`; mai perdere le correzioni di Matteo; niente chiamate all'API Anthropic senza chiave e senza il suo via libera sul costo.
