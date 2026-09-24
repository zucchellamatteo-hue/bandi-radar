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

## Da quel momento

- **Sviluppo**: Claude lavora nel repository, su un branch; quando il codice è pronto si unisce in `main`.
- **Messa in produzione**: entro 5 minuti dall'unione in `main`, il server scarica il codice e riavvia i container. Nessun comando da dare.
- **Verifica**: sul server, `journalctl -u bandi-radar-deploy.service -n 20` mostra gli ultimi aggiornamenti; `docker compose -f /srv/bandi-radar/docker-compose.yml ps` lo stato dei servizi.
- **Segreti** (chiave API Anthropic, Resend, password del database): stanno solo sul server, nel file `/srv/bandi-radar/.env`, che non è nel repository. Il file lo compila Matteo seguendo `deploy/env.example` (arriverà in Fase 0).
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
