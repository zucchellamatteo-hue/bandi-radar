# bandinQiaro — piano d'azione (aggiornato al 09/10/2026)

Riepilogo di fine sessione (05-09/10/2026) chiesto da Matteo. Va letto insieme a `docs/VISIONE.md`,
`docs/PIANO_QUALITA.md` e `docs/PIANO_SEO_GEO.md`, e aggiornato a ogni passo.

## 1. Qualità: da 7 a 9 su 10

**Dove siamo.** Voto della revisione del 06/10: 6,5/10 (Matteo: 7-8). Secondo controllo su 116 schede tra il 06 e
il 08/10: errori gravi trovati e corretti in circa 1 scheda su 8 (obiettivo: sotto il 3%). Le schede via API sono
**spente** dal 08/10 (su 31 schede rifatte dall'API, 8 con errori gravi): si fanno in sessione.

**Errori che ritornano**: bando non per imprese (la domanda la fanno enti, associazioni, intermediari, confidi);
importi o percentuali che valgono solo per una categoria; requisito decisivo dimenticato; documenti di altri bandi;
scadenza o stato sbagliati; filtro "c'è il testo del bando" che scambia decreti, leggi, circolari generali, bozze e
graduatorie per il bando.

| # | Azione | Stato | Chi |
|---|---|---|---|
| 0 | **Procedura nuova del regista**: tipo di agevolazione (misura di legge / sportello a regole fisse / bando vero) → verifica del documento (è l'avviso di questo bando, edizione giusta, approvato?) → scheda solo con documento verificato → secondo controllo obbligatorio → proponibile. Senza documento: lista "da recuperare" con il motivo | **da avviare** (manca l'ok di Matteo) | Claude |
| 1 | Secondo controllo su tutte le ~406 schede proponibili (in sessione, ~20 al giro, scadenza vicina prima) | in corso: 116 fatte | Claude |
| 2 | Automatizzare il secondo controllo con un modello economico (prova Gemini 3.8 Flash su server UE, < 10 $) | in attesa del via di Matteo | Matteo / Claude |
| 3 | Regola automatica "chi presenta la domanda": se solo enti, associazioni o intermediari, non si propone alle imprese | da fare (dentro la procedura) | Claude |
| 4 | Testi ufficiali mancanti: filtro più severo; ricerca a mano dei ~220 casi che il codice non risolve, dai più importanti; Portale UE (~345, ricerca Horizon) a bassa priorità | in corso (correzioni del 08/10: +71 bandi con documenti, molti falsi positivi del filtro) | Claude |
| 5 | Doppioni ed edizioni mescolate: stessa pagina ufficiale in due schede = grave (salvo pagine elenco) | da fare | Claude |
| 6 | Ricerca settimanale dei bandi più discussi + aggiornamento della vetrina | da fare (primo giro 06/10) | Claude |
| 7 | Fonti bloccate: certificati incompleti (MIT, ENEA, ISMEA), anti-robot (MUR, MAECI, Camera di Milano) | da fare | Claude |
| 8 | Schede delle misure nazionali approfondite sul modello della Nuova Sabatini (tabelle, distinzioni per dimensione e categoria, formula del beneficio) | Sabatini fatta (PR 119); altre 10 da fare | Claude |
| 9 | Ordinamenti in catalogo e pagina impresa (scadenza, pertinenza, beneficio, tipo di contributo) | da rifare (agente fermato) | Claude |
| 10 | Misura dell'affidabilità ogni 2 settimane (30 schede a caso, IA + giudizi di Luca) | prossima revisione 20/10 | Claude + Luca |

Il prodotto è vendibile quando la misura del punto 10 dà ≥ 9 per due revisioni di fila.

## 2. SEO e GEO

**Dove siamo** (valutazione del 09/10): SEO 5/10, GEO 3/10. Base tecnica e contenuti buoni (articolo
iperammortamento 8/10), ma il sito non è ancora indicizzato e non ha menzioni esterne.

**Fatto**: dominio bandinqiaro.it con rinvii 301; blog aperto ai motori (landing chiusa); 17 articoli rivisti (1
pubblicato); title, description e dati strutturati corretti; intestazioni di sicurezza; IndexNow; statistiche senza
cookie (pagina Visite) e rapporto SEO/GEO ogni mattina via email; landing in anteprima con "Bandi in vetrina".

| # | Mossa | Chi |
|---|---|---|
| 1 | Collegare Google Search Console e Bing Webmaster Tools, inviare la sitemap, chiedere l'indicizzazione (prompt Cowork) | **Matteo** |
| 2 | Rendere privato il repository GitHub (oggi pubblico: contiene le bozze e la strategia) dopo aver dato al server la chiave di accesso | Claude prepara la chiave, **Matteo** la aggiunge su GitHub |
| 3 | Pubblicare 2-3 articoli a settimana (uno per argomento: guida completa, non anche il breve) | **Matteo** pubblica, agenti rivedono |
| 4 | Firma degli articoli: oggi "Redazione bandinQiaro – contenuti verificati da un dottore commercialista iscritto all'Albo"; con nome e iscrizione il segnale per Google è più forte | **Matteo** decide |
| 5 | Dati di Search Console nel rapporto quotidiano (API) | Claude, dopo il punto 1 |
| 6 | Pagine pubbliche delle misure nazionali e "bandi aperti in [regione]" | Claude |
| 7 | Articolo "software su commessa: iperammortamento + R&S + patent box" (ricerca già fatta) | Claude, in bozza |
| 8 | Prime menzioni: LinkedIn, Google Business Profile, rapporto mensile con i numeri per stampa di settore e Ordini | Matteo con testi di Claude |
| 9 | Aprire la landing: prezzo allineato con Stripe e Termini, "Chi c'è dietro", titolare con P.IVA nel piede | **Matteo** decide, Claude esegue |
| 10 | Google Ads con Consent Mode v2 | dopo la società |

## 3. Cose che deve fare Matteo, in ordine

**Questa settimana**
1. Dare l'**ok alla procedura nuova** del regista (punto 0 del piano qualità).
2. **Search Console e Bing** con il prompt per Cowork (10 minuti).
3. **Repository privato**: dire "ok chiave" → Claude prepara la chiave del server → Matteo la aggiunge su GitHub
   (Settings → Deploy keys) → poi rende privato il repository.
4. Leggere la **scheda Nuova Sabatini** rifatta (pagina Misure) e dire se il modello va bene per le altre misure.
5. Pubblicare 2-3 articoli del blog (pagina Blog: Anteprima → Pubblica).
6. Mandare a **Luca** la richiesta di 20-30 giudizi sulle schede proponibili (Claude prepara il messaggio).

**Entro due settimane**
7. Via (o no) alla **prova Gemini** (< 10 $): serve per automatizzare il secondo controllo.
8. Decisioni per aprire la **landing**: prezzo (20 € di lancio bloccato 12 mesi?), "Chi c'è dietro", dati del titolare.
9. **Società SRLS**: verificare con l'Ordine compatibilità e oggetto sociale (prompt e bozza di oggetto sociale già
   forniti), poi notaio.

**Dopo la società**
10. Stripe, fattura elettronica (provider già scelto), Google Ads, LinkedIn e Google Business Profile.

## 4. Prompt per avviare la nuova sessione

```
Leggi CLAUDE.md e poi docs/PIANO_AZIONE.md, docs/PIANO_QUALITA.md e docs/PIANO_SEO_GEO.md: sono il piano d'azione
deciso con me fino al 09/10/2026. Lavora sul server, in batch, al massimo 5 agenti insieme; unisci le PR con i
controlli verdi senza chiedermi niente; fermati solo per spese, azioni irreversibili e decisioni mie.
Le schede via API sono spente (IA_SCHEDE_API=0): le schede si fanno in sessione.
Ordine di lavoro:
1. Leggi prossimi passi e segnalazioni aperte (python -m app.passi, python -m app.segnalazioni) e dimmi se c'è
   qualcosa di urgente.
2. Piano qualità, azione 0: realizza la procedura nuova del regista (tipo di agevolazione: misura di legge /
   sportello a regole fisse / bando vero; verifica del documento; lista "da recuperare" con il motivo; scheda
   solo con documento verificato; secondo controllo obbligatorio prima di "proponibile"), in passi piccoli con
   test. Prima di attivarla ripassa i bandi proponibili con la regola nuova e dimmi quanti cambiano.
3. In parallelo: secondo controllo in sessione sulle schede proponibili non ancora controllate (scadenza più
   vicina prima), correggendo subito gli errori gravi con strumenti/sessione/ar/applica_verifica.py.
4. Schede delle misure nazionali approfondite sul modello della Nuova Sabatini (se l'ho approvata).
5. Ordinamenti in catalogo e pagina impresa (scadenza, pertinenza, beneficio potenziale, tipo di contributo).
6. SEO/GEO: articolo sul cumulo iperammortamento + R&S + patent box (bozza), pagine delle misure nazionali.
Alla fine di ogni passo aggiorna i tre piani e docs/CRONOLOGIA.md e dimmi in parole semplici cosa posso provare.
```
