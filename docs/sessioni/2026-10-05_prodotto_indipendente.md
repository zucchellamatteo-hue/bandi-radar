# Sessione: Bandi Radar diventa un prodotto indipendente

*Piano preparato il 04/10/2026 dopo la richiesta di Matteo. Da incollare in una nuova sessione di Claude Code sul server (cartella `~/bandi-radar` dell'utente `ubuntu`). Il lavoro è lungo: si fa a tappe, una PR per tappa, nell'ordine sotto. Ogni tappa finisce con qualcosa che Matteo può provare.*

---

Leggi prima `CLAUDE.md`, `docs/PIANO_PROGETTO.md` (§2, §6, §7, §8, §10), `docs/PROFILO_IMPRESA.md`, `docs/PIANO_PRATICHE.md`, `docs/ORCHESTRAZIONE.md`, `docs/ricerche/2026-10-02_verifica_schede.md` (sezione "Seconda misura") e `strumenti/sessione/README.md`. Parla con Matteo in italiano semplice, proponi una strada sola e spiega perché. Matteo ha autorizzato in anticipo: procedi e unisci le PR con i controlli verdi senza chiedere; **chiedi solo per spese, azioni irreversibili e per le decisioni elencate in fondo**. Sequenze di comandi solo in script in `/tmp/claude-1000/` (niente `&&` o `|` sulla riga di comando). Al massimo 5 agenti insieme; le schede in sessione si importano subito dopo ogni agente.

## Cosa cambia (decisione di Matteo del 04/10/2026)

Bandi Radar non aspetta più Contract to Cash (C2C, ancora indietro): **diventa un prodotto a sé** su `finanzagevolata.qiaro.it`, per misurare l'interesse; più avanti potrà entrare in C2C. Quindi:

1. **Utenti veri** con ruoli: amministratore (Matteo e collaboratori), **revisore** (un amico esperto di bandi che giudica le schede), **impresa** (versione limitata: configura i suoi dati, vede solo i bandi pertinenti, riceve la notifica settimanale).
2. **Abbonamenti con addebito ricorrente su carta**, con **Stripe**.
3. **Tutto il lavoro pesante dell'IA a lotti (Batch API, metà prezzo)**: schede, controlli preliminari, analisi; le chiamate dirette solo dove serve una risposta subito e costa poco (doppioni).
4. **Feedback sulle schede**: voto e segnalazione dei problemi da parte di revisori e imprese, rianalizzati dagli agenti.
5. **Pulsanti "Richiedi supporto per la domanda"** nella piattaforma e nelle email: il servizio di Matteo e dei collaboratori, a success fee.

Questo supera una scelta del 23/09: Bandi Radar **conoscerà i clienti** (email, ragione sociale, dati di fatturazione). Restano due regole: i dati identificativi stanno in tabelle separate dal profilo usato per l'abbinamento, e **all'IA non arriva mai nulla che identifichi un cliente**.

## Modello commerciale (da scrivere in §10 del piano)

| Voce | Prezzo |
|---|---|
| Abbonamento mensile | 30 €/mese |
| Abbonamento annuale | 20 €/mese, pagato mese per mese con impegno di 12 mesi |
| Impresa in più (profilo completo: abbinamento, notifiche) | **10 €/mese** (proposta) |
| Sede operativa in più della stessa impresa (cambia solo il territorio) | **5 €/mese** (proposta) |
| Supporto per la domanda | success fee: 10-15% del contributo a fondo perduto ottenuto, 1-2% del finanziamento agevolato, minimo 400-500 € |
| Acquisizione | Google Ads e annunci nei motori di IA che li prevedono (verificare quali sono disponibili in Italia), budget iniziale di qualche migliaio di euro |

Prezzi IVA esclusa o inclusa: da decidere con Matteo (vedi in fondo).

## Le tappe, in ordine

### 1. Utenti, ruoli e accesso (prima di tutto: serve per dare l'accesso all'amico)

Oggi la plancia ha **un solo utente**, letto da `BASIC_AUTH_USER` / `BASIC_AUTH_PASSWORD` nel `.env` (`app/main.py`, autenticazione base del browser): non si possono creare altri utenti, e chi entra può fare tutto (rilanciare fonti, mettere in pausa, correggere schede).
- Tabella `utenti` (email, nome, ruolo `admin | revisore | impresa`, password con hash forte, attivo, creato_il, ultimo accesso) e `sessioni` (cookie sicuro, scadenza). Login con email e password; recupero password con link via email (Resend, dominio `finanzagevolata.qiaro.it` da verificare su Resend: chiedere a Matteo i record DNS su GoDaddy).
- Ruoli: **admin** vede e fa tutto; **revisore** vede catalogo, schede, documenti e la pagina Feedback, può votare e segnalare, **non** può rilanciare, mettere in pausa, correggere o cancellare; **impresa** vede solo l'area impresa (tappa 3).
- Creazione utenti: pagina "Utenti" per l'admin (invito via email con link per scegliere la password) **e** un comando per il server (`python -m app.utenti crea --email ... --ruolo revisore`), così Matteo può dare l'accesso subito anche prima delle email.
- Transizione: l'utente del `.env` diventa il primo admin; `/health` resta senza login; protezione contro i tentativi ripetuti (limite e pausa dopo 5 errori).
- Prova: Matteo crea l'utenza dell'amico (revisore) e la prova lui stesso in una finestra anonima.

### 2. Feedback sulle schede

- Nella pagina del bando: voto 1-5 ("mi fiderei per proporlo?"), problemi con categorie fisse (stato sbagliato, non per imprese, importo o percentuale, beneficiari, territorio, ATECO, scadenza, documento mancante, altro) più un testo libero e il campo a cui si riferisce. Un voto per utente e versione della scheda (si può cambiare).
- Pagina **Feedback** per l'admin: elenco, filtri, stato (nuovo / preso in carico / corretto / respinto, con la risposta).
- Strumento di sessione `strumenti/sessione/ar/esporta_feedback.py` + istruzioni per gli agenti: per ogni segnalazione l'agente rilegge i documenti, decide se ha ragione, propone la correzione (campo e valore con citazione) e, se il problema si ripete, la regola da cambiare nel prompt o nei controlli; `importa_feedback.py` applica le correzioni accettate e segna lo stato. Il voto esistente `bandi.qualita` (di Matteo) si conserva.
- Le segnalazioni dei revisori pesano più di quelle delle imprese; quelle delle imprese "il bando è chiuso" fanno partire subito il ricontrollo dello stato (`app/schede/ricontrollo_stato.py`).

### 3. Area impresa (versione limitata)

- Registrazione con email, conferma via email, poi il **profilo guidato** con il modulo di `docs/PROFILO_IMPRESA.md` (sedi, ATECO, dimensione, forma giuridica, fatturato e dipendenti a fasce, requisiti speciali). Più imprese e più sedi per utente, contate per l'abbonamento.
- Pagina "I miei bandi": solo i bandi **compatibili o da verificare** per il profilo (`app/abbinamento/catalogo.abbina`, gli stessi motivi), mai gli esclusi; **scheda ridotta** (sintesi, forma dell'incentivo, a chi si rivolge, scadenza, cosa serve, link ufficiale, la frase "Informazione indicativa, verificare il bando ufficiale"); niente pagine di lavoro (fonti, annunci, lavorazione, supervisione).
- **Email settimanale** per impresa (i bandi nuovi o in scadenza per i suoi profili, mai due volte lo stesso bando), con disiscrizione; nella fase di prova le email partono solo dopo l'approvazione di Matteo, come deciso il 23/09.
- Pulsanti **"Richiedi supporto per la domanda"** nella scheda e nell'email: una richiesta (impresa, bando, messaggio) che arriva a Matteo per email e in una pagina "Richieste", con lo stato.
- Prova: una o due imprese amiche, con l'abbonamento gratuito impostato da Matteo.

### 4. Abbonamenti con Stripe

- Prima in **modalità test** di Stripe (chiavi di test nel `.env`, mai nel repository o in chat); Matteo crea l'account Stripe e i prodotti, oppure li crea lo script con le sue chiavi.
- Prezzi: mensile 30 €, annuale 20 €/mese con impegno 12 mesi (abbonamento mensile più "programmazione" di 12 rate in Stripe, o prezzo annuale fatturato a rate: scegliere la soluzione più semplice da gestire e spiegarla a Matteo), quantità aggiuntive per imprese e sedi.
- Stripe Checkout per il primo pagamento, Customer Portal per carta, disdetta e fatture; webhook firmati che aggiornano lo stato dell'abbonamento; accesso all'area impresa solo con abbonamento attivo o prova gratuita (durata da decidere).
- **Fattura elettronica**: in Italia le fatture alle imprese passano dal Sistema di Interscambio; Stripe da solo non lo fa. Proporre a Matteo una strada (per esempio un servizio di fatturazione collegato a Stripe, o le fatture fatte dal suo gestionale) prima di accendere i pagamenti veri.
- Passaggio ai pagamenti veri solo con: termini di servizio, informativa privacy e cookie, condizioni del servizio di supporto (success fee), fatturazione risolta.

### 5. IA a lotti e costi

- Tutto il lavoro pesante con la **Batch API**: schede, aggiornamenti, controlli preliminari (oggi i preliminari partono con chiamate dirette, decisione del 02/10: riportarli a lotti), analisi dei feedback se fatta con l'API. Le risposte arrivano entro 24 ore: va bene.
- Finché non ci sono clienti paganti le schede restano in sessione (`IA_SCHEDE_API=0`); al primo abbonamento vero si propone a Matteo di accendere `IA_SCHEDE_API=1` con il tetto adeguato (stima del 02/10: ~70 schede al mese, 30-35 $; misurato in ottobre 0,50 $ a scheda lunga con la Batch API). **Spesa: chiedere sempre prima.**
- L'abbinamento ai profili e le email non usano l'IA: il costo per impresa in più è quasi zero.

### 6. Pagina pubblica

- Una pagina di presentazione su `finanzagevolata.qiaro.it` (cosa fa, prezzi, esempi di schede, "prova gratuita"), con il login; i dati per misurare le campagne (Google Ads) solo con il consenso ai cookie.
- Testi legali: bozze di termini, privacy, cookie e condizioni della success fee, da far rivedere a un professionista prima dei pagamenti veri (piano §8).

## Arretrati della sessione del 03-04/10 (da fare quando servono pause tra le tappe)

- **3533** (Contratti di Programma Puglia, "aperto dal 2015"): chiedere a Matteo se contattare Puglia Sviluppo; nel frattempo non proporlo (stato da verificare).
- **Possibili doppioni**: 1930/1931, 2402/2406, 4198/4202, 979/4043: controllarli con le regole del regista e unirli.
- **Bandi lunghissimi** (180, 1276, 4160, 4162, 4180): oltre i 300.000 caratteri del fascicolo. Proposta: per questi soli bandi, scheda in due passaggi (prima l'indice dei documenti, poi gli articoli che servono).
- **1768**: verificare se il codice ATECO 10.41 è giusto (il bando chiede imprese agricole).
- **Voto di Matteo** su 10 schede: con la tappa 2 diventa il primo uso della pagina Feedback, insieme all'amico revisore.
- **40 fonti mai produttive** (da `docs/ORCHESTRAZIONE.md`) e **piano delle pratiche** (`docs/PIANO_PRATICHE.md`): restano in attesa.

## Decisioni da chiedere a Matteo (una alla volta, quando servono)

1. Prezzi con o senza IVA; durata della prova gratuita; cosa vede chi non paga.
2. Impresa in più a 10 € e sede in più a 5 € (proposta), e se serve un piano per commercialisti con molti clienti.
3. Success fee: percentuali esatte, minimo, se si calcola sul concesso o sull'erogato, e quando si paga.
4. Fatturazione elettronica: quale servizio collegare a Stripe.
5. Chi può essere revisore oltre all'amico, e se i revisori vedono anche le pagine di lavoro.

## Cosa NON fare

- Non mandare all'IA email, nomi, ragioni sociali o altri dati che identificano un cliente.
- Non mettere chiavi di Stripe, Resend o Anthropic nel repository o in chat: solo nel `.env` del server.
- Non accendere i pagamenti veri né `IA_SCHEDE_API` senza il via di Matteo.
- Non cambiare l'abbinamento a regole: è lo stesso per catalogo, profili e area impresa.
