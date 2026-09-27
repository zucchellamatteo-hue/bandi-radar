# Sessione sul server: perimetro completo, API con Opus, nuova valutazione

*Prompt preparato il 27/09/2026 dopo la valutazione dell'efficacia (`docs/ricerche/2026-09-27_valutazione_efficacia.md`). Da incollare in una nuova sessione di Claude Code sul server (cartella `~/bandi-radar` dell'utente `ubuntu`). Prima di iniziare Matteo unisce la PR #26.*

---

Leggi prima `CLAUDE.md`, `deploy/MANUALE.md`, `docs/PIANO_PROGETTO.md` (§3b, §9, §10) e soprattutto `docs/ricerche/2026-09-27_valutazione_efficacia.md` con la cartella accanto: `fonti/<fonte>/verdetto_finale.json` dice, bando per bando, dove e perché si perde; `strumenti/` contiene tutto quello che serve per rifare la valutazione. Leggi anche `docs/ricerche/2026-09-26_schede_in_produzione.md`. Parla con Matteo in italiano semplice, proponi una strada sola e di' perché. Lavori nella copia `~/bandi-radar` su branch nuovi da `main` (`git pull origin main` prima), mai in `/srv`; ogni modifica al codice passa da una pull request, e unire in `main` vuol dire mettere in produzione.

**Permessi (Matteo non vuole approvare comandi).** Da riga di comando solo comandi singoli già consentiti in `.claude/settings.local.json`. Ogni sequenza (`&&`, `|`, `;`, `cd`, pause) va scritta in uno script dentro `/tmp/claude-1000/` con lo strumento Write e lanciata col percorso assoluto; stessa regola nei prompt degli agenti. Gli script di comodo usati il 26-27/09 sono in `docs/ricerche/2026-09-27_valutazione_efficacia/strumenti/`: `prod.sh` (modulo Python nel servizio raccolta di produzione), `sql.sh` (query sul database di produzione), `schede.sh` (script montato in `/out` nel servizio raccolta), `test_vuoto.sh` (tutti i test su un Postgres di prova vuoto). Copiali in `/tmp/claude-1000/` e rendili eseguibili.

**Quota dell'abbonamento.** La valutazione del 26-27/09 (circa 300 agenti, 12 milioni di token) insieme alle schede del 26/09 ha esaurito il limite settimanale. Oltre ~15 agenti Sonnet/Opus insieme il server risponde 429. Tieni al massimo ~10 agenti in parallelo e dillo a Matteo prima di lanciare lavori grandi.

## Il risultato da cui si parte (27/09)

Sui siti di 44 fonti stratificate, 427 bandi per imprese aperti o in arrivo: **solo il 22% ha una scheda**. Il 45% non viene raccolto da nessuna fonte, il 12% resta "da rivedere" senza che nessuno lo riprenda, il 13% viene raccolto ma si perde lungo la catena. Pertinenza: Opus quasi senza errori; Haiku scarta aiuti veri (6 su 466 annunci); le schede Sonnet hanno voto 3,45 contro 4,74 di Opus. Costo stimato con Opus per tutti i passi: 45-75 $ al mese, circa la metà con la Batch API.

## Il lavoro, in serie (un passo finito prima del successivo)

### Passo 1 — Perimetro completo, senza IA (una o più PR)

Obiettivo: che Bandi Radar raccolga **tutti** i bandi per imprese aperti delle fonti, non solo le novità. Per ogni punto: prova su casi veri del campione, test, PR.

1. **Lettura della "scorta".** Oggi un feed dà le ultime 10 voci, una pagina le ultime 30: i bandi aperti pubblicati prima non entrano mai. Serve una lettura completa (paginazione, API, archivio) almeno alla prima volta e poi a intervalli lunghi (per esempio mensile), distinta dal controllo delle novità. Casi: Comune di Parma (API Plone, `++api++/@search` con `portal_type=Bando`), Comune di Siena (RSS di 10 voci), Regione Sardegna (51 bandi persi), Invitalia, MIMIT, SIMEST.
2. **incentivi.gov.it.** L'indirizzo osservato (`/it/cerca-incentivi`) risponde 404. L'esploratore ha trovato l'endpoint Solr pubblico `/solr/coredrupal/select` (citato dalla pagina `/it/catalogo`, non vietato da robots.txt): una richiesta dà tutti i ~6.025 incentivi con date di apertura e chiusura, beneficiari, regioni, forma dell'aiuto e link all'ente. Leggere da lì tutti quelli aperti o in arrivo per imprese, e usarne le date come segnale di stato.
3. **Portale UE** (funding & tenders) e **anagrafica bandi di Regione Lombardia**: leggerli per intero (le call aperte, le righe del dataset), non solo le voci nuove. dati.gov.it serve solo per scoprire dataset, non come fonte di bandi.
4. **Sezioni non osservate**: aggiungere al registro le fonti che mancano, verificate su casi veri: Camera dell'Emilia sezione internazionalizzazione (Digital Export), Camera di Verona sezione PID, notizie dei Comuni di Ferrara e Parma (bandi pubblicati solo come notizia), "Politiche comunitarie" della Spezia, News di Promocosenza. Guarda `osservazioni` nei verdetti per gli altri.
5. **Pagina ufficiale sui siti Plone/Volto**: la raccolta usa l'API, ma la ricerca della pagina scarica l'HTML vuoto e dà "non trovata" (Verona, La Spezia, Siena). Leggere la pagina dall'API del sito (`++api++`), come già fa `documenti: plone_api` per gli allegati.
6. **Segnali di stato gratuiti** (per fermare i bandi chiusi prima dell'IA): data barrata con la nuova accanto (Camera di Cosenza), "bandi-chiusi" nell'indirizzo (Camera dell'Emilia), campo scadenza nelle API dei siti, "CHIUSO/ATTIVO/Aperto" in testa alla pagina, date del catalogo incentivi.gov.it.
7. **Deduplica**: "prorogato" nel titolo non vuol dire proroga di un bando da cercare (Veneto veicoli aziendali 2026, aperto, rimasto senza bando).
8. **Date di pubblicazione future** (tutti gli annunci della Camera di Caserta risultano del 30/10/2026): correggere la lettura, perché la plancia mostra una data dell'ultimo record sbagliata.
9. Fondazioni dietro Cloudflare (Cariplo, Cariverona): dire a Matteo cosa si può fare; l'indirizzo di Cariplo è del vecchio sito (`/contributi/bandi/` quello nuovo).

Alla fine del passo: rilanciare in produzione raccolta, smistamento a regole, deduplica, pagina ufficiale e allegati (vedi manuale; per velocità i lavoratori per sito, `strumenti/lavoratore.py`) e riportare a Matteo quanti bandi in più ci sono.

### Passo 2 — API accesa con Opus 5.5 (una PR, poi prove piccole)

Decisione di Matteo: si usa il modello forte dove serve efficacia. In `app/schede/ia.py`:

- `claude-opus-5-5` per smistamento dei "da rivedere", controllo preliminare e schede;
- aggiornare `PREZZI`: Opus 5.5 costa 4 $ per milione di token in ingresso e 20 in uscita, metà con la Batch API. Prima verifica i prezzi con la skill `claude-api`;
- rispettare le regole dell'API per Opus 5.5 (vedi la skill `claude-api`): il ragionamento non si spegne, `effort` a `medium` di base, niente `tool_choice` forzato, output strutturato con `output_config.format`.

Il controllo preliminare va incrociato con i segnali del passo 1: un bando con scadenza futura nei dati della fonte non si ferma come "chiuso" senza una seconda lettura.

Chiave API: Matteo la crea nella Console Anthropic con un tetto di spesa e la mette lui nel `.env` (`sudo nano /srv/bandi-radar/.env`, variabili `ANTHROPIC_API_KEY` e `IA_TETTO_MESE_USD`; tu non leggi mai il `.env`). Se non c'è ancora, spiegagli come fare e fermati qui.

Poi, con la chiave:
1. `python -m app.schede.ia stato`;
2. una prova piccola (`smista --limite 20`, `schede --limite 3`), con il costo reale riportato a Matteo.

**Niente lotti grandi né Batch API senza il suo via libera sul costo stimato.** Poi l'arretrato: tutti i "da rivedere", i preliminari e le schede dei bandi nuovi. Le schede del 26/09 fatte dalla sessione (`dati.modello` = "claude-code...") restano. Chiedi a Matteo se rifarle con Opus: costano circa 0,2 $ l'una.

### Passo 3 — Rifare la valutazione, identica

Stesse 44 fonti (`campione_fonti.json`), stessi ruoli e stessi prompt (`strumenti/workflow_valuta_efficacia.js`, da lanciare con lo strumento Workflow in 4 gruppi, `strumenti/args.py`). Esploratori e giudici restano agenti Opus della sessione; il lavoro "leggero" questa volta è **quello che ha fatto la produzione con l'API** (smistamento, preliminare e schede salvati nel database), non agenti. Prima di lanciare, di' a Matteo quanta quota consumerà (la volta scorsa ~12 milioni di token) e aspetta il suo via.

Confronta con il 27/09, fonte per fonte, con `strumenti/finale.py` e `strumenti/incrocio_globale.py`: quota di bandi aperti con scheda (obiettivo di Matteo: persi meno del 5%), errori gravi di smistamento e preliminare, voto medio delle schede (obiettivo almeno 4 su 5). Scrivi `docs/ricerche/2026-09-XX_valutazione_efficacia_2.md` con lo stesso formato.

## Alla fine

- Test eseguiti ed esito onesto; PR aperte; manuale e piano aggiornati (§9, §10).
- Riepilogo per Matteo in 10 righe:
  - quanti bandi aperti ha ora Bandi Radar e con che percentuale del perimetro;
  - quanto è costata davvero l'API;
  - cosa migliora rispetto al 27/09 e cosa resta;
  - cosa deve fare lui.

Regole ferme: mai stampare il `.env`; mai `docker compose down -v`; mai modificare `/srv/bandi-radar`; mai perdere le correzioni di Matteo (smistamento e doppioni); niente chiamate all'API Anthropic senza chiave e senza il suo via libera sul costo; rispettare robots.txt e un solo lettore per sito alla volta.
