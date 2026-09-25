# Richiesta per la chat di progetto delle anagrafiche

*Prima richiesta preparata il 24/09/2026; risposta ricevuta il 25/09/2026 (`docs/ricerche/2026-09-25_schema_anagrafiche_leadgen.md`). Aggiornata il 25/09/2026 perché a ogni campo della scheda usato nell'abbinamento corrisponda un dato del profilo (tabella "campo della scheda ↔ dato del profilo ↔ regola di confronto" in `docs/SCHEDA_BANDO.md`). Sotto: cosa abbiamo imparato dalla risposta, il profilo anonimo che serve a Bandi Radar e il testo della seconda richiesta da incollare.*

## Cosa dice la risposta del 25/09

1. **Il database `leadgen` non contiene clienti ma imprese prospect** (da Google Maps, arricchite con Cerved). Per il pilota va deciso quali imprese profilare: i clienti dello studio stanno in un altro archivio? Oppure si usano alcuni prospect come prova? Profilare i prospect per proporre loro dei bandi è un uso diverso (commerciale) e va valutato anche per la privacy prima dei clienti reali (§8 del piano).
2. **Buona parte del profilo si può ricavare sul lato di Matteo, senza far uscire dati identificativi.** Lo script che costruisce il profilo gira accanto al database delle anagrafiche e manda a Bandi Radar solo il risultato:
   - **forma giuridica** dal suffisso della ragione sociale (S.R.L., S.N.C., S.A.S., S.P.A., "società cooperativa"...): a Bandi Radar arriva solo `srl`;
   - **impresa femminile e giovanile** dai soci e dagli amministratori: il codice fiscale di una persona contiene sesso e data di nascita (per le donne il giorno è aumentato di 40), e con le quote di `leads_soci` si applicano le regole di legge (per esempio maggioranza di quote e di amministratori donne o under 35). A Bandi Radar arriva solo `femminile: sì/no`;
   - **regione** dalla provincia, con una tabella di conversione;
   - **classe dimensionale** da dipendenti e ricavi (stimata: manca il totale di bilancio).
3. **Mancano del tutto:** data di costituzione o di inizio attività (età dell'impresa), ATECO secondari, ULA, totale di bilancio, startup o PMI innovativa, albo artigiani, export, aiuti de minimis ricevuti. Alcuni si possono aggiungere dall'arricchimento Cerved (data di costituzione, forma giuridica, totale attivo), altri dai registri pubblici (startup e PMI innovative), altri solo chiedendoli al cliente (export, investimenti previsti).
4. **Formato da verificare:** ATECO (punti? 2007 o 2025?), `dipendenti` scritto come testo, valori delle colonne a categorie (`stato`, `tipo` delle sedi, `tipologia` dei soci).

## Il profilo anonimo di Bandi Radar

Un codice interno (mai la partita IVA) più questi dati. Per ognuno: da dove si ricava oggi in `leadgen` e a quale campo della scheda corrisponde.

| Dato del profilo | Formato | Da dove, oggi (`leadgen`) | Campo della scheda |
|---|---|---|---|
| codice interno | testo | calcolato (per esempio un numero progressivo; la tabella di corrispondenza resta sul lato di Matteo) | — |
| tipo di soggetto | `impresa`, `libero_professionista` | manca: da chiedere (sì/no libero professionista) | `soggetti_ammessi` |
| forma giuridica | `srl`, `snc`, `ditta_individuale`, ... (valori di `docs/SCHEDA_BANDO.md`) | ricavata dal suffisso di `leads_enriched.denominazione`, sul lato di Matteo | `forme_giuridiche_ammesse/_escluse` |
| sedi: regione, provincia, comune, tipo (legale / operativa) | sigle e nomi | `leads_master.provincia`, `leads_enriched.sede` ("Codroipo (UD)"), `leads_sedi.tipo`; regione dalla provincia | `territorio_*`, `sede_richiesta` |
| ATECO principale e secondari, con versione | `"43.21.01"`, `2007`/`2025` | `leads_enriched.ateco` (solo il principale; formato da verificare) | `codici_ateco`, `codici_ateco_esclusi`, `ateco_versione` |
| data di costituzione | data | manca: da Cerved | `eta_impresa_min/max_mesi` |
| dipendenti e ULA | numeri | `leads_enriched.dipendenti` (testo); ULA mancano | `dipendenti_min/max`, `dimensioni_ammesse` |
| fatturato, totale di bilancio | euro | `leads_bilancio.ricavi` (in **milioni**: va moltiplicato); totale di bilancio manca | `fatturato_min/max`, `dimensioni_ammesse` |
| classe dimensionale | `micro`, `piccola`, `media`, `grande` | calcolata da dipendenti e fatturato (stimata senza totale di bilancio) | `dimensioni_ammesse` |
| requisiti speciali | `femminile`, `giovanile`, `startup_innovativa`, `pmi_innovativa`, `artigiana`, `agricola`, `rating_legalita`, ... (sì/no) | femminile e giovanile dai soci (vedi sopra); agricola dall'ATECO; gli altri mancano | `requisiti_speciali_obbligatori/_premiali` |
| aiuti de minimis negli ultimi 3 anni | euro | manca (in futuro da RNA, Fase 7) | `regime_aiuto` |
| investimenti previsti | categorie di spesa (valori di `docs/SCHEDA_BANDO.md`), importo indicativo | manca: da chiedere al cliente | `categorie_spesa`, `spesa_minima/_massima` |
| interessi | export sì/no, temi | manca: da chiedere al cliente | `temi` |
| stato | attiva / cessata | `leads_enriched.stato` | si abbinano solo le attive |

Se un dato manca, l'abbinamento non lo inventa: il bando che pone quel vincolo risulta "da verificare", mai "compatibile".

---

## Seconda richiesta (testo da incollare nella chat del progetto delle anagrafiche)

Grazie per lo schema del database `leadgen`. Per costruire i profili anonimi di Bandi Radar mi servono ancora alcune cose. Sempre **nessun dato identificativo**: solo conteggi, formati ed etichette.

1. **Valori delle colonne a categorie**, con quante righe per valore: `leads_enriched.stato`, `leads_sedi.tipo`, `leads_soci.tipologia`, `leads_persone.tipo`, `leads_persone.carica`, `leads_master.tier`. Sono etichette (come "Attiva" o "sede operativa"), non dati di persone.
2. **Formato dell'ATECO**: quante righe hanno il codice con i punti e quante senza, la lunghezza dei codici (2, 4, 6 cifre), e se ci sono codici che esistono solo in ATECO 2025 o solo in ATECO 2007. Solo conteggi, senza associarli alle imprese.
3. **Formato di `dipendenti` e `fatturato` in `leads_enriched`**: sono numeri scritti come testo o fasce ("10-19")? Dammi le forme che compaiono (per esempio "numero intero", "fascia con trattino"), con i conteggi.
4. **Suffissi delle ragioni sociali**: quante imprese finiscono con S.R.L., S.R.L.S., S.N.C., S.A.S., S.P.A., "società cooperativa", "società semplice", e quante senza suffisso (probabili ditte individuali). Solo i conteggi per suffisso.
5. **Codici fiscali dei soci e degli amministratori**: quante righe di `leads_soci` e `leads_persone` hanno un codice fiscale di persona fisica (16 caratteri) e quante di società (11 cifre). Serve a capire se si può calcolare "impresa femminile" e "impresa giovanile" sul tuo lato. Il calcolo lo farà lo script dei profili, che gira accanto al database: a Bandi Radar arriverà solo "femminile sì/no".
6. **Dati che l'arricchimento Cerved potrebbe aggiungere**: data di costituzione o di inizio attività, forma giuridica, totale attivo (totale di bilancio), ATECO secondari, numero di addetti. Dimmi quali sono disponibili nell'estrazione Power BIz e con che nome, così decido se aggiungerli.
7. **Clienti o prospect?** Questo database contiene imprese prospect. Esiste un archivio (anche un foglio di calcolo) con le imprese **clienti** dello studio? Se sì, dimmi dove e con quali colonne, con le stesse regole di questa richiesta.

Regole: solo struttura e conteggi, **nessuna riga di dati reali**, nemmeno come esempio. Se una delle informazioni non esiste, scrivilo chiaramente.
