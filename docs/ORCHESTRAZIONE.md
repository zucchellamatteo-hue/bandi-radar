# Orchestrazione: dalla raccolta alla scheda

*Decisa il 01/10/2026 con Matteo, aggiornata il 06/10 (passo 8, controllo delle schede). Codice: `app/catena/regista.py` (i passi), `app/catena/stato.py` (a che punto è ogni oggetto), pagina **Lavorazione** della plancia.*

## Le due fasi

**Fase 1, raccolta.** Ogni fonte del registro (`fonti/*.yaml`) si legge nel modo che la sua piattaforma richiede: feed RSS, API (Plone, WordPress, OpenCity, CKAN, Portale UE, OData...), pagine HTML, browser senza interfaccia, sitemap; più la "scorta" (lettura completa dei bandi ancora aperti). Ogni fonte ha la sua frequenza e il semaforo nella plancia. Controllo del 01/10: 256 fonti verdi, 22 gialle, 20 in pausa, nessuna rossa; **40 fonti non hanno mai dato un annuncio** e vanno verificate (fonte silenziosa ≠ fonte sana).

**Fase 2, lavorazione.** Gli annunci grezzi diventano bandi con una scheda, o vengono messi da parte con un motivo. La guida il **regista**, ogni ora dopo la raccolta (`CATENA_AUTOMATICA=1`).

## I passi del regista

| # | Passo | Senza IA? | Riprova / sblocco |
|---|---|---|---|
| 1 | Smistamento a regole degli annunci nuovi (rilevante, non rilevante, da rivedere) | sì | — |
| 2 | Ripiego: gli annunci incerti anche per l'IA vanno avanti come possibili bandi | sì | li filtrano i passi 6 e 7 |
| 3 | Deduplica e doppioni dubbi: titoli quasi uguali (≥ 0,9), stesso ente, stesso anno ed edizione → stesso bando; titoli poco simili (< 0,5) → bandi diversi; graduatorie o proroghe di bandi che non abbiamo → archiviate; gli altri all'IA (Opus 5.5, effort basso, 40 per giro) | in parte | le decisioni di Matteo non si toccano |
| 4 | Pagina ufficiale (50 per giro) e documenti (25 per giro) | sì | errore di rete: il giorno dopo; pagina non trovata: dopo 14 giorni |
| 5 | Ricontrollo dei documenti dei bandi aperti con la scheda, ogni 14 giorni (5 per giro); proroghe, rettifiche, chiusure e FAQ arrivate dopo la scheda | sì | la scheda diventa "da aggiornare" |
| 5b | Ricontrollo dello stato (dal 03/10): ogni settimana la pagina ufficiale di ogni bando proponibile non chiuso si riscarica e si confronta con quella salvata; un avviso di chiusura nelle righe nuove ("piattaforma chiusa", "dotazione esaurita", "bando chiuso") rende la scheda "da aggiornare" (10 pagine per giro, `app/schede/ricontrollo_stato.py`) | sì | errore di rete: la settimana dopo |
| 6 | Filtro "c'è il bando?" sui documenti | sì | si rifà quando arrivano documenti nuovi |
| 7 | IA con la Batch API (metà prezzo): smistamento dei "da rivedere", controllo preliminare, schede nuove e da aggiornare, solo per i bandi con il testo ufficiale. Con `IA_SCHEDE_API=0` (oggi) le schede si scrivono nelle sessioni di Claude Code e il lotto porta solo preliminari e seconde letture | no | un lotto in volo per tipo; tetto di spesa del mese |
| 8 | Controllo delle schede (dal 06/10, `app/schede/controlli.py`): le schede nuove o cambiate dall'ultimo controllo si ricontrollano con i soli dati del database e l'esito va in `bandi.controllo`. **Gravi**: "bando ufficiale" senza il testo del bando tra i documenti, stessa pagina e stesso titolo di un altro bando, apertura dopo la scadenza, contributo oltre la dotazione, percentuale fuori scala. **Da migliorare**: vincolo senza numeri né nota (regola 21e), fornitori non noti (21f), fasi o dotazione ripartita senza linee (21d), pagina condivisa con altri bandi | sì | si rifà quando la scheda cambia; a mano `python -m app.schede.controlli [--tutti] [--bando ID]` |

L'ordine reale del giro è: smistamento (1-2), doppioni (3), pagine e documenti (4-5), ricontrollo dello stato (5b), filtro (6), IA (7), controllo delle schede (8). Ogni passo è registrato nella Supervisione; un passo che fallisce non ferma gli altri. Ogni azione del regista resta in `eventi_catena`.

## A che punto è ogni bando

Le fasi si calcolano dai dati (`app/catena/stato.py`), quindi non c'è uno stato da tenere in ordine: pagina da cercare → pagina non trovata → documenti da scaricare → documenti da valutare → (in disparte: solo sintesi / nessun documento) → controllo preliminare → (fermato: chiuso, non per imprese, edizione vecchia, senza testo) → scheda in attesa → **proponibile** (salvo i bandi con la scheda ma segnati "non per imprese" dal ricontrollo del 03/10: tornano tra i fermati e escono dal catalogo) (scheda sul bando ufficiale) → scheda da aggiornare. Dal 06/10 una scheda proponibile con **problemi gravi** trovati dal passo 8 non si propone alle imprese (catalogo, profili, area impresa, email) finché non è sistemata (`catalogo.proponibile`). I bandi segnati "unito a" un altro (doppioni già schedati, 06/10) escono da tutti i passi. Per gli annunci: da smistare → da rivedere → forse doppione → collegato a un bando, oppure non rilevante. Le fasi servono a seguire la catena; per **contare e descrivere** i bandi (una sola voce per bando, con motivo, chi ha deciso e quando) si usa la **situazione** (vista `bandi_situazione`, `app/catena/situazione.py`, dal 06/10).

La pagina **Lavorazione** mostra i due imbuti con i numeri; cliccando una fase si vedono gli oggetti fermi lì, con il motivo e la data dell'ultimo passo, più le ultime azioni del regista e la spesa IA del mese. Sotto, la sezione **Da rivedere** (dal 06/10) elenca le schede con problemi trovati dal controllo, prima le gravi (casella "solo i gravi"): si sistemano con gli strumenti di sessione o a mano. Il controllo senza IA vede solo errori di forma; per il contenuto c'è la verifica con l'IA in sessione (pilota del 06/10, `strumenti/sessione/ar/ISTRUZIONI_VERIFICA_IA.md`).

## Cosa resta da fare

- Verifica delle 40 fonti che non hanno mai dato annunci.
- Riprova immediata delle pagine non trovate quando cambia la regola della fonte nel registro (oggi si aspettano 14 giorni).
- Un pulsante nella plancia per riprovare subito un passo o escludere un bando a mano.
- Verifica con l'IA delle schede: oggi solo in sessione e senza strumento di importazione.
