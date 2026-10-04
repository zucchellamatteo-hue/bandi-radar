# Verifica a campione delle schede proponibili

*02/10/2026. Domanda: le schede proponibili (scheda sul bando ufficiale) dicono il vero? Quali errori portano un commercialista a una conclusione sbagliata?*

**Metodo.** 20 schede scelte a caso tra le proponibili aperte o in arrivo (`strumenti/sessione/ar/esporta_verifica.py 20`, ordine `md5(id || 'verifica-02-10')`). Un agente per scheda ha confrontato 12 campi (stato, apertura, scadenza, tipo, contributo massimo, percentuale, beneficiari, territorio, dimensioni, ATECO, spese, sintesi) con i testi dei documenti nel database e ha dato un voto 1-5 ("mi fiderei per proporre il bando?"). I verdetti completi sono in `2026-10-02_verifica_schede/<id>.json`.

**Limiti.** 20 schede su 387 aperte: l'ordine di grandezza è affidabile, le percentuali no (±10 punti). Gli agenti hanno letto solo i documenti già scaricati, non le pagine web di oggi: un bando chiuso dopo l'ultimo scaricamento non si vede. Nessuna scheda è stata votata da Matteo.

## Controlli automatici (tutte le 683 proponibili)

| Misura | Valore |
|---|---|
| Campo con la fonte dichiarata | 681 su 683 |
| Scadenza compilata / contributo massimo / percentuale | 73% / 67% / 65% |
| Con almeno un problema segnalato da `verifica_scheda` | 465 (68%): 216 su 241 delle schede del 26/09, 249 su 438 delle successive |
| Problema più frequente | ATECO "vincolo" senza codici (232): il bando descrive i settori a parole |
| Vincoli "non noto" | 70-124 per vincolo (fatturato, dipendenti, forma giuridica i più frequenti) |
| Senza stato (aperto/chiuso) | 97 |

## Risultato della verifica

| Esito sui campi | Numero |
|---|---|
| giusto | 208 (87%) |
| impreciso (vero ma incompleto) | 28 (12%) |
| sbagliato | 3 (1%) |
| non verificabile | 1 |

Voti: 11 da 5, 7 da 4, 2 da 3, 1 da 2 (media 4,3). **4 bandi su 20 non andrebbero proposti:**

| Id | Problema | Tipo di errore |
|---|---|---|
| 427 | Scheda "aperto" senza scadenza; la pagina ufficiale e l'Atto 12926 dicono che la piattaforma ha chiuso il 13/03/2026 | stato sbagliato |
| 3533 | "Aperto" solo per l'etichetta della vecchia pagina POR 2014-2020, nessun atto dopo il 2022 | stato non dimostrato |
| 2138 | Riservato a società sportive dilettantistiche (modulo: regime L. 398/1991, "non ente commerciale") | non per imprese |
| 2147 | Beneficiari enti e associazioni titolari di musei, biblioteche, archivi | non per imprese |

**Imprecisioni ricorrenti** (non portano fuori strada, ma semplificano):
- **Bandi a più misure o assi ridotti a un numero solo**: percentuale 60% che è la base 50% più due premialità (1008); 100% invece di 50/40% per misura (3659); tetto dell'Asse I al posto di quelli degli Assi II-III (4109); spesa minima diversa per dimensione (833).
- **Avvertenze "manca l'allegato X" false in 5 schede su 20** (833, 3603, 4043, 4109, 4163): l'allegato è tra i documenti del bando. Nessuna scheda aperta ha documenti scaricati dopo la scheda, quindi la causa è il fascicolo dato all'agente (testo troncato prima della PR #43, o documento escluso dall'esportazione), non un documento arrivato dopo.
- **Fondi esauriti / lista d'attesa** non messi in evidenza (1008).
- **Territorio nei campi strutturati** vuoto quando è solo nel testo (3677).

## Seconda misura, dopo le correzioni (04/10/2026)

Sessione del 03-04/10 (piano `docs/sessioni/2026-10-03_qualita_schede.md`), con gli agenti in sessione (niente API, decisione di Matteo del 03/10):

| Lavoro | Risultato |
|---|---|
| Stato sulla pagina ufficiale di oggi (regole senza IA + 119 bandi ricontrollati dagli agenti) | 26 chiusi o esauriti, date mancanti aggiunte; passo settimanale "Ricontrollo dello stato" nel regista (PR #51), 260 pagine già ricontrollate il 04/10 |
| Bandi non per imprese (regole su tutti i testi, modulistica compresa; 185 candidati letti dagli agenti; verifica) | 34 bandi fuori dal catalogo, scheda nello storico; il preliminare legge anche il modulo di domanda |
| Fascicoli incompleti | 217 documenti tolti dalla modulistica (PR #52); spazio garantito ai documenti brevi; versioni superate dopo quelle in vigore e testi doppi una volta sola (PR #55) |
| Istruzioni della scheda (PR #53) | percentuale base, più misure in prima riga, fondi esauriti in evidenza, settori a parole in codici ATECO, regioni negli elenchi |
| Schede rifatte con le istruzioni nuove | 223 (tutte le 100 aperte del 26/09 comprese), di cui 34 una seconda volta con il fascicolo corretto |
| Complemento delle altre schede (forma dell'incentivo, ATECO, regioni) | 209 bandi letti; forma dell'incentivo su 408 proponibili su 421 |

**Numeri dei proponibili non chiusi** (scheda sul bando ufficiale, per imprese):

| | 02/10 | 04/10 |
|---|---|---|
| Totale | 474 (387 aperti o in arrivo, 97 senza stato) | 421 (380 aperti o in arrivo, 41 senza stato) |
| Schede del 26/09 (istruzioni vecchie) | 100 | 0 |
| Con la forma dell'incentivo compilata | 10 | 408 |
| ATECO "vincolo" senza codici ammessi | 216 | 167, di cui 106 con le esclusioni ("tutti i settori tranne..."): il buco vero è 61 |
| Con almeno un problema segnalato da `verifica_scheda` | 296 | 214 (i controlli sono più severi dal 03/10) |

**Nuovo campione** (seme `verifica-03-10`, 20 schede proponibili aperte, stesse istruzioni; verdetti in `2026-10-04_verifica_schede/`):

| Esito sui campi | 02/10 | 04/10 |
|---|---|---|
| giusto | 87% | **90%** (216 su 240) |
| impreciso | 12% | 8% |
| sbagliato | 1% | 1% (2: 180 contributo massimo, 1542 due codici ATECO in più) |
| Voto medio | 4,3 | 4,35 (10 da 5, 7 da 4, 3 da 3) |
| Bandi da non proporre | 4 su 20 (2 chiusi, 2 non per imprese) | 3 su 20, nessun chiuso: 804 e 4095 non per imprese (tolti il 04/10), 3055 progetto UE di coordinamento (imprese ammesse in consorzio) |
| Avvertenze "manca/tagliato" false | 5 su 20 | 5 su 20, ma vere rispetto al fascicolo: causa trovata e corretta (PR #55), 34 schede rifatte |

I 4 bandi sbagliati del 02/10: 427 chiuso, 2138 e 2147 fuori dal catalogo (non per imprese); **3533 resta "aperto"**: la pagina dice "Aperto dal 15/06/2015" e nessun documento parla di chiusura, ma è un avviso del 2015 su fondi 2007-2013. Va chiesto a Puglia Sviluppo.

**Cosa resta.** I bandi molto lunghi (4180, 1276, 4160, 4162, 180) superano i 300.000 caratteri del fascicolo anche dopo le correzioni: le parti in fondo restano tagliate e la scheda lo dice. Il voto di Matteo su 10 schede (campo `qualita`) è ancora a zero ed è l'unico giudizio esperto.

## Sintesi

Le schede sono affidabili nel contenuto (87% dei campi giusti, 1% sbagliati); il rischio vero è a monte: **1 bando su 5 tra i "proponibili aperti" è chiuso o non è per imprese**. I due errori hanno una causa comune: lo stato e i beneficiari si decidono sul testo del bando, mentre la smentita sta altrove (avviso di chiusura sulla pagina, modulo di domanda). Seconda debolezza: le schede scritte con fascicoli incompleti. Piano di correzione: `docs/sessioni/2026-10-03_qualita_schede.md`.
