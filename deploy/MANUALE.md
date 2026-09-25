# Bandi Radar: manuale del server

*Aggiornato al 24/09/2026, Fase 3 (smistamento e allegati, senza IA). Per i dettagli passo-passo vedi `deploy/README.md`.*

## 1. Cosa c'è sul server

Un VPS OVH (Ubuntu 24.04, IP 146.59.145.138) che ospita il sito https://finanzagevolata.qiaro.it. Ci si collega con `ssh ubuntu@146.59.145.138`. Dentro girano quattro "container" Docker, cioè quattro programmi isolati che partono insieme:

| Nome | Cosa fa | Se si rompe |
|---|---|---|
| `caddy` | Riceve le richieste dal browser, tiene il certificato HTTPS (Let's Encrypt, si rinnova da solo) | il sito non si apre o manca il lucchetto |
| `app` | L'applicazione Python: la plancia (pagine Fonti, Catalogo, Novità) e la sua API, più `/health` | il sito risponde con un errore |
| `db` | Il database Postgres, con i dati in un volume che sopravvive ai riavvii | l'applicazione risulta "unhealthy" |
| `raccolta` | Il raccoglitore: ogni ora guarda quali fonti del registro sono da controllare, le legge (feed, API o pagina) e salva i controlli e gli annunci nel database. Con lo stesso contenitore si lanciano a mano lo smistamento e lo scaricamento degli allegati (§5) | i bandi nuovi non arrivano; la plancia lo mostra |

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
cd /srv/bandi-radar && sudo -u deploy docker compose ps      # quattro righe Up, db e app "(healthy)"
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
Per controllare subito una fonte: lo stesso comando con `--fonte ID_FONTE`.

La raccolta è collegata anche a una seconda rete Docker, `ipv6`: alcuni siti (Napoli, Siracusa) rifiutano l'indirizzo IPv4 del server ma accettano l'IPv6. Le fonti che ne hanno bisogno hanno `richiesta: {ipv6: true}` nel registro. Database e app restano sulla rete di sempre.

### Smistamento e allegati (Fase 3)

Per ora si lanciano a mano; quando le regole saranno tarate entreranno nel giro orario della raccolta.

**Smistamento**: decide per ogni annuncio nuovo se è rilevante (aiuti alle imprese), non rilevante o da rivedere, con le parole chiave di `app/schede/regole_smistamento.yaml`. Non usa l'IA e non costa nulla.
```
cd /srv/bandi-radar && sudo -u deploy docker compose run --rm raccolta python -m app.schede.smista --prova --esempi 20   # solo guardare: percentuali ed esempi
cd /srv/bandi-radar && sudo -u deploy docker compose run --rm raccolta python -m app.schede.smista                      # smista e salva
```
Dopo aver cambiato le parole chiave (con una pull request, come ogni modifica), `--rifai` ricalcola gli annunci decisi dalle regole; le tue correzioni dalla plancia non vengono mai toccate. `--prova` dice anche quante delle tue correzioni le regole di adesso indovinerebbero.

**Allegati**: per i bandi con la pagina ufficiale trovata scarica bando, moduli, decreti e FAQ (al massimo 50 bandi per giro; 25 MB per file, 100 MB e 30 file per bando; 2 secondi tra una richiesta e l'altra). Ogni documento riceve una categoria (bando, FAQ, decreto, graduatoria, modulistica...): la scheda leggerà prima il bando e mai la modulistica. È lento apposta: un giro da 50 bandi può durare una ventina di minuti.
```
cd /srv/bandi-radar && sudo -u deploy docker compose run --rm raccolta python -m app.schede.allegati --limite 10     # i primi 10 bandi
cd /srv/bandi-radar && sudo -u deploy docker compose run --rm raccolta python -m app.schede.allegati --bando 45      # un bando preciso
cd /srv/bandi-radar && sudo -u deploy docker compose run --rm raccolta python -m app.schede.allegati --annuncio 123  # la pagina di un annuncio, come prima
```
**Stato dei bandi**: aperto, chiuso o in arrivo lo calcola il sistema dalle date della scheda, da solo, una volta al giorno (nel servizio `raccolta`). Ogni cambio resta nello storico del bando. A mano: `cd /srv/bandi-radar && sudo -u deploy docker compose run --rm raccolta python -m app.schede.stato`.

I file stanno nel volume Docker `allegati` (una cartella per bando, `b<numero>`, e le vecchie per annuncio), che sopravvive ai riavvii e agli aggiornamenti come il database. Per vedere quanto spazio occupa:
```
sudo du -sh /var/lib/docker/volumes/bandi-radar_allegati/_data     # totale
df -h /                                                            # spazio libero sul disco (75 GB in tutto)
```
e, dentro `psql`:
```
SELECT count(*) AS file, pg_size_pretty(sum(dimensione)) AS spazio FROM allegati WHERE errore IS NULL;
SELECT errore, count(*) FROM allegati WHERE errore IS NOT NULL GROUP BY errore ORDER BY 2 DESC;   -- cosa non si è scaricato e perché
```
Il volume non è nel backup notturno del database (lo è nel backup del disco di OVH): i documenti si possono comunque riscaricare dai siti degli enti.

### La plancia

Su https://finanzagevolata.qiaro.it (utente e password del `.env`) ci sono quattro pagine:
- **Fonti**: una riga per fonte con il semaforo (verde regolare; giallo da guardare: un errore, silenzio sospetto, mai controllata; rosso: tre errori di fila o struttura cambiata; grigio in pausa), ultimo controllo, ultima novità, giorni di silenzio rispetto alla soglia della fonte, novità negli ultimi 30 e 90 giorni. Con ▶ si controlla una fonte subito, con ⏸ si mette in pausa (la pausa resta finché non la togli, anche se il registro cambia). Cliccando il nome si vedono gli ultimi controlli e annunci.
- **Doppioni**: gli annunci che forse parlano di un bando già noto (titoli simili ma non uguali, proroghe e graduatorie di cui non si trova il bando). Per ognuno scegli "Stesso bando" o "Bando diverso". Nella pagina di un annuncio vedi il bando a cui è collegato e gli altri annunci dello stesso bando, e puoi unirlo a un altro annuncio (con il suo numero) o separarlo. Le tue scelte non vengono mai cambiate dalla deduplica automatica. Il titolo del bando apre la sua pagina: annunci, allegati e versioni precedenti.
- **Catalogo**: tutti gli annunci trovati, con ricerca nel testo, filtri per tipo di fonte, territorio, date, "scade entro N giorni" e smistamento (solo rilevanti, da rivedere, non rilevanti, non ancora smistati). Nella colonna Smistamento i pulsanti ✓ ? ✗ correggono l'esito: la tua scelta vale su tutto e serve a tarare le regole. Il titolo apre la pagina dell'annuncio (motivo dello smistamento, allegati scaricati da aprire direttamente dalla plancia, documenti non scaricati con il motivo); "originale ↗" apre la pagina dell'ente.
- **Novità**: una voce per settimana, come un blog: le stesse novità dell'email del lunedì.

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
