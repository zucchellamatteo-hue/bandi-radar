# Server: come si usa

Il VPS (OVH VPS-2, Ubuntu 24.04, Gravelines) non si amministra a mano: **il server scarica da solo le novità da GitHub ogni 5 minuti** e riavvia i servizi quando cambiano. Tutto il lavoro di sviluppo passa dal repository, quindi si può fare da qualunque sessione di Claude Code (cloud o PC) senza accesso diretto al server.

## Prima accensione (una volta sola, 10 minuti)

1. OVH manda un'email con l'indirizzo IP e le credenziali del primo accesso. **Non incollarle in nessuna chat.**
2. Dal PC, apri un terminale (Windows: PowerShell; Mac: Terminale) e collegati:
   ```
   ssh ubuntu@INDIRIZZO_IP
   ```
   (se OVH ha creato un utente diverso lo dice nell'email). Alla prima connessione rispondi `yes`.
3. Lancia lo script di preparazione:
   ```
   curl -fsSL https://raw.githubusercontent.com/zucchellamatteo-hue/bandi-radar/main/deploy/bootstrap.sh | sudo bash
   ```
   Installa aggiornamenti, firewall, Docker, l'utente di servizio, copia il repository in `/srv/bandi-radar` e attiva l'aggiornamento automatico e il backup notturno. Dura qualche minuto. Si può rilanciare senza problemi.
4. Cambia la password iniziale con `passwd` e, se OVH non l'ha già fatto, disattiva più avanti l'accesso con password a favore di una chiave SSH (istruzioni in Fase 0).

## Primo avvio dei servizi (una volta sola, 5 minuti)

Dal momento in cui in `main` c'è il file `docker-compose.yml`, il server prova ad avviare i servizi a ogni controllo (ogni 5 minuti). Senza il file `.env` l'avvio fallisce e riprova al giro dopo: nessun danno, ma il sito non parte finché il file non c'è. I passi, collegato al server con `ssh ubuntu@146.59.145.138`:

1. **Crea il file `.env` dal modello** (il file appartiene all'utente di servizio `deploy` e lo legge solo lui):
   ```
   sudo cp /srv/bandi-radar/deploy/env.example /srv/bandi-radar/.env
   sudo chown deploy:deploy /srv/bandi-radar/.env
   sudo chmod 600 /srv/bandi-radar/.env
   ```
2. **Compila i valori** con `sudo nano /srv/bandi-radar/.env` (ogni variabile ha il suo commento). Le righe obbligatorie sono `ACME_EMAIL`, `BASIC_AUTH_USER`, `BASIC_AUTH_PASSWORD` e `POSTGRES_PASSWORD`; le altre possono restare vuote. Per generare una password lunga: `openssl rand -base64 24` (lanciato due volte: una per il sito, una per il database). Salva con `Ctrl+O`, `Invio`, esci con `Ctrl+X`.
3. **Aspetta il prossimo controllo** (al massimo 5 minuti) oppure forzalo subito:
   ```
   sudo systemctl start bandi-radar-deploy.service
   ```
   Il primo avvio costruisce l'immagine dell'applicazione e chiede il certificato a Let's Encrypt: ci vuole circa un minuto.

**Come verificare che tutto giri**

- Stato dei servizi: `cd /srv/bandi-radar && sudo -u deploy docker compose ps`. Devono comparire tre righe, `db`, `app` e `caddy`, tutte `Up`; `db` e `app` con `(healthy)`.
- Salute dell'applicazione e del database, senza password: `curl -s https://finanzagevolata.qiaro.it/health` risponde `{"status":"ok","database":"ok"}`.
- Nel browser: https://finanzagevolata.qiaro.it chiede utente e password (quelli di `BASIC_AUTH_USER` e `BASIC_AUTH_PASSWORD`) e poi mostra la pagina "Bandi Radar - Sito in costruzione" con il lucchetto del certificato valido.
- Se qualcosa non va: `journalctl -u bandi-radar-deploy.service -n 30` mostra l'errore dell'ultimo avvio (per esempio una variabile mancante in `.env`); `cd /srv/bandi-radar && sudo -u deploy docker compose logs --tail 50` i log dei tre servizi.

**Se cambi il file `.env`** (nuova password, nuova variabile): i container vanno riavviati a mano una volta, perché l'aggiornamento automatico riparte solo quando cambia il codice su GitHub:
```
cd /srv/bandi-radar && sudo -u deploy docker compose up -d
```

**Prova sul PC o nella copia di lavoro** (senza dominio e senza toccare le porte 80/443): copia `deploy/env.example` in `.env.locale`, metti `SITE_ADDRESS=:8080` e valori qualsiasi per le password, poi:
```
docker compose -p bandi-radar-test --env-file .env.locale -f docker-compose.yml -f deploy/compose.local.yml up -d --build
```
Il sito risponde su http://localhost:8080 in HTTP semplice. Per fermare e cancellare tutto: stesso comando con `down -v --rmi local` al posto di `up -d --build`.

## Da quel momento

- **Sviluppo**: Claude lavora nel repository, su un branch; quando il codice è pronto si unisce in `main`.
- **Messa in produzione**: entro 5 minuti dall'unione in `main`, il server scarica il codice e riavvia i container. Nessun comando da dare.
- **Verifica**: sul server, `journalctl -u bandi-radar-deploy.service -n 20` mostra gli ultimi aggiornamenti; `cd /srv/bandi-radar && sudo -u deploy docker compose ps` lo stato dei servizi.
- **Segreti** (chiave API Anthropic, Resend, password del database): stanno solo sul server, nel file `/srv/bandi-radar/.env`, che non è nel repository. Il file lo compila Matteo seguendo `deploy/env.example` (vedi "Primo avvio dei servizi").
- **Backup**: OVH fa il backup del disco ogni giorno; in più, ogni notte alle 3:30 il server salva un dump del database in `/var/backups/bandi-radar`, conservato 14 giorni.

## Sessioni di Claude Code direttamente sul server (opzionale, consigliato)

Per le mappature e i test dal server, e per far vedere a Claude i log dal vivo, conviene installare Claude Code sul VPS e usarlo via SSH con l'abbonamento:
```
curl -fsSL https://claude.ai/install.sh | bash
claude
```
Al primo avvio chiede l'accesso con l'account Claude. Le sessioni sul server vedono tutto: Docker, log, rete del server. Le sessioni cloud invece vedono solo il repository.

## Perché non si accede dal cloud

Le sessioni di Claude Code sul web escono su internet solo in HTTPS tramite un proxy; la porta SSH non è raggiungibile. Per questo il flusso è "GitHub in mezzo": è anche più sicuro, perché nessuna credenziale del server sta nel cloud.
