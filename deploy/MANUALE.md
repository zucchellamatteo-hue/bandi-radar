# Bandi Radar: manuale del server

*Aggiornato al 24/09/2026, inizio della Fase 1 (raccolta). Per i dettagli passo-passo vedi `deploy/README.md`.*

## 1. Cosa c'è sul server

Un VPS OVH (Ubuntu 24.04, IP 146.59.145.138) che ospita il sito https://finanzagevolata.qiaro.it. Ci si collega con `ssh ubuntu@146.59.145.138`. Dentro girano quattro "container" Docker, cioè quattro programmi isolati che partono insieme:

| Nome | Cosa fa | Se si rompe |
|---|---|---|
| `caddy` | Riceve le richieste dal browser, tiene il certificato HTTPS (Let's Encrypt, si rinnova da solo) | il sito non si apre o manca il lucchetto |
| `app` | L'applicazione Python: oggi la pagina "in costruzione" e l'indirizzo `/health`; in futuro raccolta, schede, plancia | il sito risponde con un errore |
| `db` | Il database Postgres, con i dati in un volume che sopravvive ai riavvii | l'applicazione risulta "unhealthy" |
| `raccolta` | Il raccoglitore: ogni ora guarda quali fonti del registro sono da controllare, le legge (feed, API o pagina) e salva i controlli e gli annunci nel database | i bandi nuovi non arrivano; la plancia (Fase 2) lo mostrerà |

Due cartelle da distinguere:

- `/srv/bandi-radar` è la **produzione**: appartiene all'utente di servizio `deploy`, contiene il file dei segreti `.env` e viene aggiornata da sola. Non si modifica a mano.
- `/home/ubuntu/bandi-radar` è la **copia di lavoro** dove Claude sviluppa e prova, senza toccare la produzione.

Automatismi già attivi: ogni 5 minuti il server scarica `main` da GitHub e riavvia i servizi se il codice è cambiato (timer `bandi-radar-deploy`); ogni notte alle 3:30 salva una copia del database in `/var/backups/bandi-radar`, tenuta 14 giorni; OVH fa in più il backup dell'intero disco; il firewall lascia aperte solo le porte SSH, 80 e 443; gli aggiornamenti di sicurezza di Ubuntu si installano da soli.

Claude Code Remote Control gira come servizio (`claude-remote-control`), parte all'accensione e si riavvia se si chiude: dall'app o da claude.ai/code si apre una sessione sull'ambiente "bandi-radar-vps" senza fare nulla sul server.

## 2. Come arriva una modifica in produzione

Sempre e solo così: Claude lavora su un branch, apre una pull request, tu la leggi e la unisci in `main` da GitHub. Entro 5 minuti il server la mette in produzione. Non si copia mai codice a mano sul server. Se vuoi accelerare: `sudo systemctl start bandi-radar-deploy.service`.

## 3. Il file dei segreti

`/srv/bandi-radar/.env` contiene email per il certificato, utente e password del sito, password del database. Non è su GitHub e non va mai incollato in chat. Le variabili disponibili, con i commenti, sono in `deploy/env.example`: quando una fase nuova aggiunge una chiave (Anthropic in Fase 3, Resend in Fase 5), Claude aggiorna quel file e ti dice cosa aggiungere.

Per modificarlo: `sudo nano /srv/bandi-radar/.env`, salva con Ctrl+O e Invio, esci con Ctrl+X. Poi i servizi vanno riavviati una volta a mano, perché l'aggiornamento automatico scatta solo quando cambia il codice:
```
cd /srv/bandi-radar && sudo -u deploy docker compose up -d
```

## 4. Cambiare le impostazioni più comuni

- **Password o utente del sito**: cambia `BASIC_AUTH_USER` o `BASIC_AUTH_PASSWORD` nel `.env` e riavvia come sopra. Il browser chiederà le nuove credenziali.
- **Email per il certificato**: cambia `ACME_EMAIL` e riavvia. Nessun altro effetto.
- **Nome del sito**: `SITE_ADDRESS` vuoto vale finanzagevolata.qiaro.it. Per un nome diverso serve prima il record DNS che punti al server, poi il nuovo valore e un riavvio: Caddy chiede da solo il certificato nuovo.
- **Password del database**: non basta cambiarla nel `.env`, perché il database ha memorizzato quella vecchia. Chiedi a Claude, che la cambia con un comando nel database e poi nel file. Finché il database è vuoto (Fase 0) si può anche cancellare tutto e ripartire.
- **Utente e nome del database** (`POSTGRES_USER`, `POSTGRES_DB`): lasciali vuoti. L'utente `postgres` è quello che il backup notturno si aspetta.

## 5. Controlli di routine

Bastano quattro comandi, tutti da lanciare come utente `ubuntu`:

```
cd /srv/bandi-radar && sudo -u deploy docker compose ps      # tre righe Up, db e app "(healthy)"
curl -s https://finanzagevolata.qiaro.it/health               # {"status":"ok","database":"ok"}
journalctl -u bandi-radar-deploy.service -n 20                # ultimi aggiornamenti da GitHub
systemctl --user status claude-remote-control                 # "active (running)"
```
E ogni tanto `ls -lh /var/backups/bandi-radar` per vedere che i backup notturni ci siano.

### La raccolta

Il servizio `raccolta` scrive nel log una riga per ogni fonte controllata (esito, elementi letti, novità):
```
cd /srv/bandi-radar && sudo -u deploy docker compose logs --tail 100 raccolta
```
Per guardare i dati nel database (solo lettura, senza modificare nulla):
```
cd /srv/bandi-radar && sudo -u deploy docker compose exec db psql -U postgres bandi_radar
```
e poi, dentro `psql`:
```
SELECT esito, count(*) FROM controlli WHERE iniziato_il > now() - interval '1 day' GROUP BY esito;   -- com'è andata oggi
SELECT fonte_id, titolo, trovato_il FROM annunci ORDER BY trovato_il DESC LIMIT 30;                  -- ultimi annunci
\q
```
Per provare una fonte a mano, senza scrivere nel database (utile quando si corregge una voce del registro):
```
cd /srv/bandi-radar && sudo -u deploy docker compose run --rm raccolta python -m app.raccolta.esegui --prova ID_FONTE
```
Per controllare subito una fonte: lo stesso comando con `--fonte ID_FONTE`. Finché la plancia non c'è (Fase 2), questi comandi sono l'unico modo di vedere la raccolta.

## 6. Se qualcosa non va

1. Guarda i log: `cd /srv/bandi-radar && sudo -u deploy docker compose logs --tail 50` (tutti) oppure `... logs --tail 50 caddy` (uno solo).
2. Riavvia i servizi: `cd /srv/bandi-radar && sudo -u deploy docker compose restart`.
3. Se non basta, riavvia il server: `sudo reboot`. Dopo un paio di minuti tutto riparte da solo: Docker, i tre servizi, il timer, il Remote Control.
4. Copia in chat a Claude il messaggio d'errore (mai il contenuto del `.env`).

Per il Remote Control: `journalctl --user -u claude-remote-control -n 20` mostra gli errori; `systemctl --user restart claude-remote-control` lo riavvia, ma chiude le sessioni di Claude aperte sul server in quel momento.

## 7. Cosa non fare

- Non modificare file dentro `/srv/bandi-radar`: il prossimo aggiornamento li sovrascrive. L'unica eccezione è `.env`.
- Non lanciare `docker compose down -v` in produzione: cancella il volume del database.
- Non condividere `.env`, né incollarlo in chat, né metterlo su GitHub.
- Non riaprire l'accesso SSH con password: solo con chiave.
- Non avviare `claude remote-control` a mano nella cartella `~/bandi-radar`: c'è già il servizio, e Claude accetta una sola istanza per cartella.
