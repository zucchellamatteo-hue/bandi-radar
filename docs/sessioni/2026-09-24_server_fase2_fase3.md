# Sessione sul server, 24/09/2026: chiudere la Fase 2 e fare il possibile della Fase 3

*Prompt preparato dalla sessione cloud. Da incollare in una sessione di Claude Code sul server (ambiente `bandi-radar-vps`, cartella `~/bandi-radar` dell'utente `ubuntu`).*

---

Leggi prima `CLAUDE.md`, poi `docs/PIANO_PROGETTO.md` (§3a, §5, §5b, §9) e `deploy/MANUALE.md`. Sei sul server di produzione: la produzione è in `/srv/bandi-radar` (non toccarla a mano), tu lavori nella copia `~/bandi-radar` su un branch e apri pull request verso `main`. Parla con Matteo in italiano semplice, proponi una strada sola e spiega perché.

Oggi la sessione cloud ha unito in `main` il registro delle fonti (287 voci), la raccolta (Fase 1) e la plancia (Fase 2, pull request #13). Il tuo lavoro ha tre parti, in quest'ordine. Prima di ogni parte aggiorna `~/bandi-radar` con `git pull origin main`.

## Parte A. Verificare che la produzione sia sana

1. Controlla che l'ultima pull request sia arrivata in produzione: `cd /srv/bandi-radar && git log --oneline -3` e `sudo -u deploy docker compose ps`. Devono esserci **quattro** container (`db`, `app`, `raccolta`, `caddy`), con `db` e `app` "healthy".
2. Se l'immagine non si è costruita (il `Dockerfile` ora ha due fasi, Node per la plancia e Python per l'app; `deploy/Dockerfile.raccolta` parte dall'immagine Playwright con Chromium, circa 1 GB), leggi `journalctl -u bandi-radar-deploy.service -n 100` e `sudo -u deploy docker compose logs --tail 100 app raccolta`, correggi sul branch, apri la pull request e dillo a Matteo. Non modificare file dentro `/srv/bandi-radar`.
3. Apri `https://finanzagevolata.qiaro.it` con le credenziali del `.env` (senza stamparle in chat): deve comparire la plancia con le pagine Fonti, Catalogo, Novità. Controlla `/health`.
4. Guarda il primo giro della raccolta: `sudo -u deploy docker compose logs --tail 300 raccolta`. Al primo avvio controlla tutte le 277 fonti attive: ci vogliono 15-30 minuti. Riporta a Matteo quante `ok`, `errore`, `saltato`, `struttura_cambiata`, con le query di `deploy/MANUALE.md` §5.

## Parte B. Le fonti che dal cloud non rispondevano

La rete della sessione cloud veniva rifiutata da alcuni siti. Dal server la rete è diversa: prova queste fonti con `sudo -u deploy docker compose run --rm raccolta python -m app.raccolta.esegui --prova ID` (non scrive nel database) e poi, se leggono, con `--fonte ID`:

- `comune_milano_impresa` (comune.milano.it, 403 dal cloud; Matteo ha verificato a mano che i bandi per imprese ci sono in "Lavoro e impresa" e su economiaelavoro.comune.milano.it)
- `gse_bandi_avvisi` (403 Akamai dal cloud, anche con browser)
- `umbria_avvisi_attivita_produttive` e `umbria_bandi_imprese`
- `incentivi_gov_ricerca` e `incentivi_gov_open_data` (dal server rispondevano il 24/09; i dati aperti sono in `/sites/default/files/open-data/`, CSV compresso e JSON, i nomi dei file contengono la data)
- `comune_enna_avvisi` (endpoint noto: `https://api.comune.enna.it/api/Content<base64 del filtro JSON {"itemPerPagina":6,"pagina":1,"avvisi":true,"ordinamento":1}>`, vedi `docs/ricerche/2026-09-24_api_nascoste.md`)
- `rna_open_data`, `fondazione_cariplo_bandi`, `fondazione_cariverona_bandi`, `cciaa_bari_bandi`, `cciaa_milano_monza_brianza_lodi_bandi`, `cciaa_cremona_bandi`, `cciaa_mantova_bandi`, `cciaa_pavia_bandi`, `cciaa_salerno_bandi`, `cciaa_rieti_viterbo_supporto_imprese`, `comune_venezia_avvisi`, `comune_parma_avvisi`, `comune_grosseto_avvisi`, `comune_campobasso_avvisi`, `comune_macerata_avvisi`, `comune_rieti_avvisi`, `comune_viterbo_avvisi`, `comune_chieti_avvisi`, `comune_isernia_avvisi`, `comune_benevento_avvisi`, `comune_crotone_avvisi`, `comune_catania_avvisi`, `comune_lecce`, `comune_potenza`, `comune_barletta` (controlla gli id esatti con `grep -n "stato: difficile\|stato: da_verificare" -B12 fonti/*.yaml | grep "id:"`).

Per ognuna: se legge, aggiorna la voce nel registro (`stato: attiva`, `verificato_il`, `note` con cosa hai visto, eventuale `modalita` o `feed_url` migliore); se serve il browser, `modalita: browser`; se resta bloccata anche dal server, lascia `difficile` e scrivi nelle note "bloccata anche dal VPS il gg/mm". Ricorda le regole: User-Agent dichiarato, un controllo alla frequenza prevista, `ignora_robots: true` solo se Matteo lo dice. Se una fonte importante (Milano, GSE, incentivi.gov.it) resta bloccata, proponi a Matteo l'alternativa (per esempio lanciare la lettura dal suo PC con `--prova`) invece di forzare.

Una pull request per questa parte, con la tabella "fonte | esito dal server | cosa ho cambiato".

## Parte C. Fase 3, la parte che non ha bisogno della chiave API

La Fase 3 trasforma gli annunci in **schede** (§5b del piano: elementi fondamentali, link originale, allegati, FAQ, storico). L'IA (Anthropic, Haiku per smistare, Sonnet per le schede) entra solo quando Matteo mette `ANTHROPIC_API_KEY` nel `.env` con un tetto di spesa. Se la chiave c'è già, dillo a Matteo e fermati prima di usarla: la userà la prossima sessione dopo aver concordato i costi. Intanto costruisci tutto ciò che sta prima e dopo l'IA:

1. **Tabelle** (`app/db/migrazioni/004_schede.sql`): `bandi` (id, annuncio_id di origine, titolo, ente, territorio, url originale, stato aperto/chiuso/prorogato/in arrivo, data apertura, scadenza, sintesi, a chi si rivolge, cosa finanzia, tipo agevolazione, contributo massimo e percentuale, spese ammesse, codici ATECO ammessi come elenco, dimensioni ammesse, requisiti, tema, qualita' (voto di Matteo), creato/aggiornato, dati grezzi in jsonb); `allegati` (bando_id, url, nome, tipo, dimensione, impronta, percorso locale, scaricato_il, testo estratto); `smistamenti` (annuncio_id, esito rilevante/non rilevante/da rivedere, motivo, come deciso: regole o IA, costo, quando). Rispetta lo stile delle migrazioni esistenti (SQL con commenti in italiano).
2. **Smistamento a regole, senza IA**: uno script `python -m app.schede.smista` che passa gli annunci non ancora smistati e li segna "non rilevante" quando titolo e riassunto parlano chiaramente di altro (concorsi di personale, gare d'appalto vere, matrimoni, cimiteri, mense, graduatorie di asili, interruzioni idriche...) e "rilevante" quando parlano di contributi, voucher, agevolazioni, incentivi, finanziamenti, bandi per imprese. Il resto resta "da rivedere": lo deciderà Haiku. Attenzione alla regola di `CLAUDE.md`: non scartare per la sola parola "gara", alcuni enti archiviano i contributi sotto "Bandi di gara". Salva le parole chiave in un file di configurazione, non nel codice. Lancialo sugli annunci reali e riporta a Matteo le percentuali e 20 esempi per categoria: deve poterle correggere.
3. **Allegati**: `python -m app.schede.allegati` che, per gli annunci rilevanti, apre la pagina originale, trova i link a PDF/DOC/XLS/ZIP (e le pagine "FAQ"), li scarica in un volume Docker (`allegati/` sotto un volume persistente da aggiungere a `docker-compose.yml`, con dimensione massima per file e per bando), calcola l'impronta e salva la riga in `allegati`. Rispetta robots.txt e la pausa tra richieste. Estrai il testo dai PDF con `pypdf` (o `pdfplumber` se serve per le tabelle) e salvalo in `testo_estratto`, troncato a una lunghezza ragionevole.
4. **Plancia**: nel Catalogo, una colonna con l'esito dello smistamento (con filtro "solo rilevanti") e un pulsante per correggerlo a mano (rilevante / non rilevante): le correzioni di Matteo vanno salvate come `deciso_da: matteo` e serviranno a tarare le regole. Nella pagina dell'annuncio, l'elenco degli allegati scaricati con il link locale.
5. **Formato della scheda e prompt**: scrivi in `docs/SCHEDA_BANDO.md` il formato della scheda (i campi della tabella `bandi`, con esempio compilato a mano su un bando vero della Lombardia) e in `app/schede/prompt_scheda.md` il testo che chiederà a Sonnet di compilarla dal bando e dagli allegati, con la regola "Informazione indicativa, verificare il bando ufficiale". Non chiamare l'API.
6. Aggiorna `docs/PIANO_PROGETTO.md` (§9 stato della Fase 3, decisioni prese) e `deploy/MANUALE.md` (nuovi comandi e volume degli allegati). Test con `pytest` per smistamento e allegati (su dati finti, senza rete).

Una o più pull request piccole, ognuna con: cosa cambia, esito dei test, cosa non hai potuto provare. Alla fine scrivi a Matteo un riepilogo di 10 righe e l'elenco di ciò che serve da lui: la chiave API con il tetto di spesa (`ANTHROPIC_API_KEY` nel `.env`), la registrazione del dominio su Resend (`RESEND_API_KEY`, `EMAIL_MATTEO`), lo schema delle anagrafiche (`docs/RICHIESTA_SCHEMA_ANAGRAFICHE.md`).

Regole ferme: mai stampare il contenuto del `.env`; mai `docker compose down -v`; mai modificare `/srv/bandi-radar`; commit piccoli con messaggio in italiano; prima di dire "finito", test eseguiti ed esito riportato con onestà.
