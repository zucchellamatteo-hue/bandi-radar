# Bandi Radar — regole di lavoro

Leggi questo file prima di qualunque lavoro. Obiettivi, priorità e modello di ricavi decisi da Matteo sono in `docs/VISIONE.md` (affidabilità 9/10 prima di vendere, non perdere le misure famose, IA entro 100 $ al mese). Il piano completo e le decisioni prese sono in `docs/PIANO_PROGETTO.md`: è la memoria condivisa del progetto, va tenuto aggiornato quando una decisione cambia.

## Cos'è

Sistema che raccoglie i bandi di finanza agevolata per imprese (UE, nazionali, regionali, camerali, capoluoghi), li trasforma in schede standard e li abbina ai profili anonimi dei clienti di Matteo (commercialista). Prodotto: `finanzagevolata.qiaro.it`. Lingua del progetto: **italiano** (codice e nomi tecnici in inglese, tutto il resto in italiano).

## Come si lavora

- **Chi parla con Claude è Matteo**, non un programmatore: spiega le scelte in parole semplici, evita gergo, proponi una sola strada e dì perché.
- Le sessioni possono girare **sul server** (vede Docker, log, rete) o **nel cloud** (vede solo il repository, niente SSH). Entrambe lavorano su branch e pull request; il repository è l'unico canale tra le due.
- **Ogni modifica passa da un branch e una pull request verso `main`.** Il server scarica `main` ogni 5 minuti e riavvia i servizi: unire in `main` significa mettere in produzione.
- Commit piccoli, con messaggio in italiano che dice cosa cambia e perché.
- Prima di dichiarare finito un lavoro: test eseguiti, esito riportato con onestà. Se qualcosa è stato saltato, dirlo.
- A fine lavoro aggiornare `docs/CRONOLOGIA.md` (cosa è cambiato quel giorno e perché, decisioni di Matteo) e, se cambia un pezzo del sistema, `docs/COME_FUNZIONA.md`.
- Le mappature manuali delle fonti vanno in `docs/ricerche/` seguendo `docs/ricerche/README.md`.
- Gli strumenti delle sessioni sul server (agenti che fanno smistamento, doppioni e schede al posto dell'API) stanno in `strumenti/sessione/` (README per installarli in `/tmp/claude-1000/`).
- **Prossimi passi** (pagina della plancia, tabella `prossimi_passi`): sono i promemoria e le richieste di Matteo. All'inizio di una sessione sul server leggerli (`sudo -u deploy docker compose exec app python -m app.passi` in `/srv/bandi-radar`, o `sql.sh`), lavorare sui "da sviluppare" in ordine di priorità se Matteo non chiede altro, e a lavoro finito segnarli "fatto" (o aggiungerne di nuovi) con un UPDATE/INSERT che dica chi l'ha fatto.
- La **Guida** (`app/guida/guida.yaml`) va aggiornata quando cambia una pagina o un comando: ogni sezione dice chi la vede.
- La catena della fase 2 la guida il regista (`app/catena/regista.py`, `docs/ORCHESTRAZIONE.md`); i sistemi automatici e le loro esecuzioni sono in `app/sistemi.py` e nella pagina Supervisione.

## Scelte tecniche (decise, non riaprirle senza motivo)

- Python per raccolta, schede e abbinamento; Postgres come database; React per plancia e cruscotto; tutto in **Docker Compose**; Caddy davanti per HTTPS.
- **L'osservatore delle pagine non usa l'IA**: scarica, confronta con la versione precedente, passa all'IA solo il frammento cambiato. IA (API Anthropic, Claude Opus 5.5 per smistamento, controllo preliminare e schede: decisione del 28/09) solo dalla Fase 3, e solo sui bandi con il testo ufficiale tra i documenti (filtro senza IA, 01/10).
- I profili clienti sono **anonimi**: niente nomi, email o dati identificativi in Bandi Radar né nelle chiamate all'IA.
- Email transazionali con Resend, dal dominio `finanzagevolata.qiaro.it`.
- Il registro delle fonti (~180 voci) è un file di configurazione: aggiungere una fonte è aggiungere una riga, non scrivere codice. Ogni fonte ha modalità di lettura (API, RSS, HTML, browser senza interfaccia), frequenza, e data dell'ultimo record trovato.

## Server

- OVH VPS-2, Ubuntu 24.04, Gravelines, IP 146.59.145.138. Preparato con `deploy/bootstrap.sh`; istruzioni in `deploy/README.md`.
- Produzione in `/srv/bandi-radar` (utente `deploy`, aggiornata dal timer `bandi-radar-deploy`). Le sessioni sul server lavorano nella copia `~/bandi-radar` dell'utente `ubuntu`, mai in `/srv`.
- **Segreti solo in `/srv/bandi-radar/.env`** sul server, mai nel repository, mai in chat. `deploy/env.example` elenca le variabili senza valori.
- Accesso SSH solo con chiave. Non riaprire l'accesso con password.

## Cosa non fare

- Non usare le credenziali dell'abbonamento Claude dentro il sistema automatico: in produzione serve una chiave API con tetto di spesa.
- Non filtrare i bandi per la parola "gara": alcuni enti archiviano i contributi sotto "Bandi di gara".
- Non trattare una fonte "silenziosa" come sana: la plancia deve mostrare la data dell'ultimo record, non solo l'esito dello scaricamento.
- Non scaricare siti pubblici in modo aggressivo: rispettare robots.txt, un controllo per fonte alla frequenza prevista, identificarsi con uno User-Agent che dica chi siamo.

## Fasi (dettaglio in §9 del piano)

0 Fondamenta · 1 Raccolta · 2 Plancia v1 · 3 Schede · 4 Profili e match · 5 Cruscotto ed email · 6 Pilota · 7 Estensioni. Ogni fase finisce con qualcosa che Matteo può provare.
