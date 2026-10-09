# bandinQiaro — piano d'azione (aggiornato all'08/10/2026 sera)

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
| 0 | **Procedura nuova del regista** | **attiva** dal 09/10 (25 bandi usciti finché non si recupera il documento) | Claude |
| 1 | Secondo controllo su tutte le schede proponibili | **fatto** il 08/10 (379 + 97 solo documento; 58 gravi corretti) | Claude |
| 2 | Automatizzare il secondo controllo con un modello economico (prova Gemini 3.8 Flash su server UE, < 10 $) | in attesa del via di Matteo | Matteo / Claude |
| 3 | Regola automatica "chi presenta la domanda": se solo enti, associazioni o intermediari, non si propone alle imprese | in parte: 22 casi corretti il 08/10; la regola resta nel controllo preliminare e nel secondo controllo | Claude |
| 4 | Testi ufficiali mancanti: filtro più severo; ricerca a mano dei ~220 casi che il codice non risolve, dai più importanti; Portale UE (~345, ricerca Horizon) a bassa priorità | in corso (correzioni del 08/10: +71 bandi con documenti, molti falsi positivi del filtro) | Claude |
| 5 | Doppioni ed edizioni mescolate: stessa pagina ufficiale in due schede = grave (salvo pagine elenco) | da fare | Claude |
| 6 | Ricerca settimanale dei bandi più discussi + aggiornamento della vetrina | da fare (primo giro 06/10) | Claude |
| 7 | Fonti bloccate: certificati incompleti (MIT, ENEA, ISMEA), anti-robot (MUR, MAECI, Camera di Milano) | da fare | Claude |
| 8 | Schede delle misure nazionali approfondite sul modello della Nuova Sabatini | **fatto** il 09/10 (11 misure; punti da verificare in docs/ricerche/2026-10-09_misure_nazionali_approfondite.md) | Claude |
| 9 | Ordinamenti in catalogo e pagina impresa (scadenza, pertinenza, beneficio, tipo di contributo) | **fatto** il 09/10; agevolazioni senza soldi in secondo piano | Claude |
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
| 1 | Collegare Google Search Console e Bing Webmaster Tools, inviare la sitemap, chiedere l'indicizzazione | **fatto** da Matteo il 08/10 | Matteo |
| 2 | Rendere privato il repository GitHub (oggi pubblico: contiene le bozze e la strategia) dopo aver dato al server la chiave di accesso | Claude prepara la chiave, **Matteo** la aggiunge su GitHub |
| 3 | Pubblicare 2-3 articoli a settimana (uno per argomento: guida completa, non anche il breve) | **Matteo** pubblica, agenti rivedono |
| 4 | Firma degli articoli: oggi "Redazione bandinQiaro – contenuti verificati da un dottore commercialista iscritto all'Albo"; con nome e iscrizione il segnale per Google è più forte | **Matteo** decide |
| 5 | Dati di Search Console nel rapporto quotidiano (API) | Claude, dopo il punto 1 |
| 6 | ~~Pagine pubbliche delle misure nazionali~~ e "bandi aperti in [regione]" | pagine delle misure **tolte** (Matteo, 09/10: bastano le guide del blog); resta "bandi aperti in [regione]" | Claude |
| 7 | Articolo "software su commessa: iperammortamento + R&S + patent box" | **in bozza** (n. 18) dal 09/10: da rileggere e pubblicare | Matteo |
| 8 | Prime menzioni: LinkedIn, Google Business Profile, rapporto mensile con i numeri per stampa di settore e Ordini | Matteo con testi di Claude |
| 9 | Aprire la landing: prezzo allineato con Stripe e Termini, "Chi c'è dietro", titolare con P.IVA nel piede | **Matteo** decide, Claude esegue |
| 10 | Google Ads con Consent Mode v2 | dopo la società |

## 3. Cose che deve fare Matteo, in ordine

**Questa settimana**
1. ~~Ok e via alla procedura nuova~~ (accesa il 09/10).
2. ~~Search Console e Bing~~ (fatto l'08/10). **Email nello spam**: chiedere a Luca "Non è spam", scegliere la casella per `EMAIL_CONTATTO` (prossimo passo n. 44).
3. **Repository privato**: dire "ok chiave" → Claude prepara la chiave del server → Matteo la aggiunge su GitHub
   (Settings → Deploy keys) → poi rende privato il repository.
4. ~~Scheda Nuova Sabatini~~ (approvata il 09/10, applicata alle altre misure). Rileggere l'**articolo Sabatini** rivisto (bozza n. 11, con il calcolatore) e l'**articolo sul cumulo** (bozza n. 18); decidere la **firma** degli articoli (formula stabile se la cancellazione dall'Albo è vicina); pubblicare prima gli articoli linkati (Fondo di garanzia, ZES, Conto Termico).
5. Pubblicare 2-3 articoli del blog (pagina Blog: Anteprima → Pubblica).
6. Mandare a **Luca** la richiesta di 20-30 giudizi sulle schede proponibili (Claude prepara il messaggio).

**Entro due settimane**
7. Via (o no) alla **prova Gemini** (< 10 $): serve per automatizzare il secondo controllo.
8. Decisioni per aprire la **landing**: prezzo (20 € di lancio bloccato 12 mesi?), "Chi c'è dietro", dati del titolare.
9. **Società SRLS**: verificare con l'Ordine compatibilità e oggetto sociale (prompt e bozza di oggetto sociale già
   forniti), poi notaio.

**Dopo la società**
10. Stripe, fattura elettronica (provider già scelto), Google Ads, LinkedIn e Google Business Profile.

## 4. Prompt per avviare la nuova sessione (aggiornato al 09/10/2026)

```
Leggi CLAUDE.md e poi docs/PIANO_AZIONE.md, docs/PIANO_QUALITA.md, docs/PIANO_SEO_GEO.md e le voci del 08/10 e
09/10 di docs/CRONOLOGIA.md: sono il piano deciso con me. Lavora sul server, in batch, al massimo 5 agenti insieme;
unisci le PR con i controlli verdi senza chiedermi niente; fermati solo per spese, azioni irreversibili e decisioni
mie. Le schede via API sono spente (IA_SCHEDE_API=0): schede e secondi controlli si fanno in sessione
(strumenti/sessione/, istruzioni ISTRUZIONI_VERIFICA_IA.md e ISTRUZIONI_DOCUMENTO.md).
Stato: dal 09/10 la procedura nuova del regista e' ACCESA (app/catena/procedura.py): un bando si propone solo con
documento verificato e secondo controllo fatto, quindi ogni scheda nuova o rifatta resta fuori finche' non la
controlli tu.
Ordine di lavoro:
1. Leggi prossimi passi e segnalazioni aperte (python -m app.passi, python -m app.segnalazioni) e dimmi se c'e'
   qualcosa di urgente.
2. Procedura: python -m app.catena.procedura (ripasso). Fai il secondo controllo delle schede in attesa
   (esporta_verifica.py --prossimi, agenti, applica_verifica.py, importa_verifica.py --corrette; per i casi
   "non per imprese" e i doppioni come nella sessione del 08/10: unisci.py in /tmp/claude-1000/ar se c'e' ancora,
   altrimenti decidi_collegamento).
3. Riscrivi in sessione le schede "da aggiornare" emerse dai controlli (1552, 4147, 4153, 4159, 3626, 2023, 1064)
   e chiarisci i 3 casi con errori aperti (477 premio gia' assegnato, 1290 ordinanza Ischia 2023, 1306 SIMEST
   alluvione 2023).
4. Lista "da recuperare" (python -m app.catena.procedura --da-recuperare): cerca il testo ufficiale giusto dei
   bandi italiani aperti, prima quelli in scadenza (Puglia 2021-2027, fondi Veneto Sviluppo, ecc.); poi
   rifai_disparte.py sui bandi in disparte non UE.
5. Piano qualita': doppioni periodici (azione 4), ricerca settimanale dei bandi piu' discussi (azione 5), fonti
   bloccate MIT/ENEA/ISMEA e anti-robot (azione 6); prepara la revisione del 20/10 (azione 7).
6. SEO/GEO: pagine "bandi aperti in [regione]" (PIANO_SEO_GEO punto 7); dati di Search Console nel rapporto
   quotidiano (punto 5, Search Console e Bing sono gia' collegati).
Alla fine di ogni passo aggiorna i tre piani e docs/CRONOLOGIA.md e dimmi in parole semplici cosa posso provare.
```
