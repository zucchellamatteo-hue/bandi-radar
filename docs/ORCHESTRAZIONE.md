# Orchestrazione: dalla raccolta alla scheda

*Decisa il 01/10/2026 con Matteo. Codice: `app/catena/regista.py` (i passi), `app/catena/stato.py` (a che punto è ogni oggetto), pagina **Lavorazione** della plancia.*

## Le due fasi

**Fase 1, raccolta.** Ogni fonte del registro (`fonti/*.yaml`) si legge nel modo che la sua piattaforma richiede: feed RSS, API (Plone, WordPress, OpenCity, CKAN, Portale UE, OData...), pagine HTML, browser senza interfaccia, sitemap; più la "scorta" (lettura completa dei bandi ancora aperti). Ogni fonte ha la sua frequenza e il semaforo nella plancia. Controllo del 01/10: 256 fonti verdi, 22 gialle, 20 in pausa, nessuna rossa; **40 fonti non hanno mai dato un annuncio** e vanno verificate (fonte silenziosa ≠ fonte sana).

**Fase 2, lavorazione.** Gli annunci grezzi diventano bandi con una scheda, o vengono messi da parte con un motivo. La guida il **regista**, ogni ora dopo la raccolta (`CATENA_AUTOMATICA=1`).

## I passi del regista

| # | Passo | Senza IA? | Riprova / sblocco |
|---|---|---|---|
| 1 | Smistamento a regole degli annunci nuovi (rilevante, non rilevante, da rivedere) | sì | — |
| 2 | Ripiego: gli annunci incerti anche per l'IA vanno avanti come possibili bandi | sì | li filtrano i passi 6 e 7 |
| 3 | Deduplica e doppioni dubbi: titoli quasi uguali (≥ 0,9), stesso ente, stesso anno ed edizione → stesso bando; titoli poco simili (< 0,5) → bandi diversi; graduatorie o proroghe di bandi che non abbiamo → archiviate; gli altri all'IA (Opus 5.5, effort basso, 40 per giro) | in parte | le decisioni di Matteo non si toccano |
| 4 | Pagina ufficiale (20 per giro) e documenti (10 per giro) | sì | errore di rete: il giorno dopo; pagina non trovata: dopo 14 giorni |
| 5 | Ricontrollo dei documenti dei bandi aperti con la scheda, ogni 14 giorni (5 per giro); proroghe, rettifiche, chiusure e FAQ arrivate dopo la scheda | sì | la scheda diventa "da aggiornare" |
| 6 | Filtro "c'è il bando?" sui documenti | sì | si rifà quando arrivano documenti nuovi |
| 7 | IA con la Batch API (metà prezzo): smistamento dei "da rivedere", controllo preliminare, schede nuove e da aggiornare, solo per i bandi con il testo ufficiale | no | un lotto alla volta; tetto di spesa del mese |

Ogni azione del regista resta in `eventi_catena`.

## A che punto è ogni bando

Le fasi si calcolano dai dati (`app/catena/stato.py`), quindi non c'è uno stato da tenere in ordine: pagina da cercare → pagina non trovata → documenti da scaricare → documenti da valutare → (in disparte: solo sintesi / nessun documento) → controllo preliminare → (fermato: chiuso, non per imprese, edizione vecchia, senza testo) → scheda in attesa → **proponibile** (scheda sul bando ufficiale) → scheda da aggiornare. Per gli annunci: da smistare → da rivedere → forse doppione → collegato a un bando, oppure non rilevante.

La pagina **Lavorazione** mostra i due imbuti con i numeri; cliccando una fase si vedono gli oggetti fermi lì, con il motivo e la data dell'ultimo passo, più le ultime azioni del regista e la spesa IA del mese.

## Cosa resta da fare

- Verifica delle 40 fonti che non hanno mai dato annunci.
- Riprova immediata delle pagine non trovate quando cambia la regola della fonte nel registro (oggi si aspettano 14 giorni).
- Un pulsante nella plancia per riprovare subito un passo o escludere un bando a mano.
