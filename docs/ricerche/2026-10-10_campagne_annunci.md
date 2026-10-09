# Campagne pubblicitarie sui bandi aperti più interessanti (preparate il 10/10/2026)

Strategia decisa da Matteo il 10/10 (`docs/VISIONE.md` §4): campagne sui **bandi aperti più interessanti del
momento**, con parole chiave che li richiamano o che cercano le imprese che possono accedervi, e annunci che portano
alla pagina del bando o della guida, con l'invito alla prova gratuita. Si parte **solo quando la SRLS esiste** e la
landing è accesa (decisioni di Matteo). Questo documento è pronto da copiare in Google Ads; va **aggiornato con la
ricerca settimanale dei bandi più discussi** (le date qui sotto valgono al 10/10).

## Prima di accendere (in ordine)

1. SRLS costituita; landing accesa con i dati della società (`PAGINA_PUBBLICA=1`, `TITOLARE_SITO`), Stripe.
2. Misura delle registrazioni: `GOOGLE_ADS_ID` nel `.env` e banner dei cookie con Consent Mode v2 (già pronto, PR 97);
   conversione = registrazione completata; una seconda conversione "abbonamento attivato" quando c'è Stripe.
3. Pagine di arrivo pronte: le guide del blog citate sotto (Iperammortamento, Sabatini, Conto Termico già
   pubblicate); da completare **Voucher Cloud** (bozza n. 2, breve: va riscritta completa prima del 20/10, quando apre
   la precompilazione) e l'articolo **startup e digitale** (passo 8).
4. Ogni link degli annunci con `?utm_source=google&utm_medium=cpc&utm_campaign=<nome>` (la pagina Visite li conta).

## Budget e regola di stop

- Totale circa **2.000 €**: Google circa **1.400 €**, ChatGPT circa **600 €**.
- Ripartizione Google iniziale (si sposta dopo 7-10 giorni verso le campagne con il costo per registrazione più
  basso): Voucher Cloud 400, Iperammortamento 250, Nuova Sabatini 250, Conto Termico 200, Brevetti+ 150, Startup e
  digitale 150; regioni da 0 a 200 dopo i primi dati.
- **Stop** se un abbonato costa più di **150 €** (decisione di Matteo): controllo ogni settimana, con il costo per
  registrazione e la quota di registrati che si abbonano.
- Offerte: CPC massimo manuale (o "Massimizza i clic" con tetto 1,50-2 €) finché non ci sono almeno 30 conversioni;
  solo rete di ricerca, niente rete display; Italia; lingua italiano; orari lavorativi lun-ven.

## Campagne

### Voucher Cloud e Cybersecurity

- **Cosa**: bando 175 — precompilazione dal 20/10, invio dal 10/11/2026 al 20/01/2027, a sportello
- **Pagina di arrivo**: /blog/<articolo Voucher Cloud completo> (oggi bozza n. 2, da riscrivere completa) poi registrazione con prova gratuita
- **Budget**: Google 400 €
- **Parole chiave a corrispondenza esatta**: [voucher cloud], [voucher cybersecurity], [voucher cloud cybersecurity], [voucher cloud mimit], [bando cybersecurity pmi], [contributi sicurezza informatica]
- **Parole chiave a frase**: "voucher cloud 2026", "voucher cyber security imprese", "contributo software gestionale cloud", "incentivi sicurezza informatica pmi", "fondo perduto cybersecurity"
- **Parole chiave negative**: lavoro, corso, gratis download, privati, famiglie, scuola, stipendio

| Titoli (max 30) | car. |
|---|---|
| Voucher Cloud e Cybersecurity | 29 |
| 50% a fondo perduto sul cloud | 29 |
| Domande dal 10 novembre | 23 |
| Precompilazione dal 20/10 | 25 |
| Scopri se la tua PMI può | 24 |
| Requisiti e spese ammesse | 25 |
| Fino a 50% delle spese | 22 |
| Guida gratuita al voucher | 25 |
| Verifica in 2 minuti | 20 |
| Bandi scelti per te | 19 |
| Scheda chiara, fonti MIMIT | 26 |
| Prova gratis senza carta | 24 |

| Descrizioni (max 90) | car. |
|---|---|
| Chi può chiedere il voucher, quali servizi cloud e cyber sono ammessi e come prepararsi. | 88 |
| Domande a sportello dal 10 novembre: arriva pronto. Scheda verificata sul testo ufficiale. | 90 |
| Ti segnaliamo solo i bandi adatti alla tua impresa. Prova gratis, nessuna carta richiesta. | 90 |
| Un commercialista ti aiuta con la domanda se vuoi. Scopri importi, requisiti e scadenze. | 88 |

### Iperammortamento 2026

- **Cosa**: misura iperammortamento_2026 — investimenti 2026-2028 (fino al 30/09/2028)
- **Pagina di arrivo**: /blog/ articolo n. 8 (pubblicato, con calcolatore)
- **Budget**: Google 250 €
- **Parole chiave a corrispondenza esatta**: [iperammortamento 2026], [iperammortamento], [nuovo iperammortamento], [transizione 5.0 iperammortamento], [iperammortamento software]
- **Parole chiave a frase**: "iperammortamento macchinari", "iperammortamento fotovoltaico", "calcolo iperammortamento", "maggiorazione 180%", "piano transizione 5.0 2026"
- **Parole chiave negative**: 2017, 2018, 2019, 2020, tesi, pdf esame, corso

| Titoli (max 30) | car. |
|---|---|
| Iperammortamento 2026 | 21 |
| Calcola il tuo risparmio | 24 |
| Fino al 180% del costo | 22 |
| Macchinari, software, FV | 24 |
| Guida con calcolatore | 21 |
| Scaglioni e IRAP spiegati | 25 |
| Si somma con la Sabatini? | 25 |
| Esempi con i numeri veri | 24 |
| Aggiornato con DL 38/2026 | 25 |
| Verificato da commercialista | 28 |
| Prova gratis bandinQiaro | 24 |

| Descrizioni (max 90) | car. |
|---|---|
| Quanto si risparmia davvero su macchinari, software e fotovoltaico, con il calcolatore. | 87 |
| Scaglioni per anno, cumulo con ZES e Sabatini, errori da evitare. Guida aggiornata 2026. | 88 |
| Poi ricevi solo i bandi adatti alla tua impresa: prova gratuita, senza carta di credito. | 88 |

### Nuova Sabatini

- **Cosa**: misura nuova_sabatini (bando 2516) — sempre aperta
- **Pagina di arrivo**: /blog/ articolo n. 11 (pubblicato, con calcolatore)
- **Budget**: Google 250 €
- **Parole chiave a corrispondenza esatta**: [nuova sabatini], [nuova sabatini 2026], [sabatini 4.0], [contributo sabatini], [calcolo contributo sabatini]
- **Parole chiave a frase**: "nuova sabatini macchinari", "nuova sabatini green", "sabatini capitalizzazione", "finanziamento macchinari pmi contributo"
- **Parole chiave negative**: sabatini sindaco, sabatini ristorante, legge sabatini storia, tesi

| Titoli (max 30) | car. |
|---|---|
| Nuova Sabatini 2026 | 19 |
| Calcola il contributo | 21 |
| Fino al 14,26% di interessi | 27 |
| Linea 4.0 e green | 17 |
| Macchinari e software | 21 |
| Guida con calcolatore | 21 |
| Requisiti spiegati bene | 23 |
| Si somma all'iper? | 18 |
| Prova gratis bandinQiaro | 24 |
| Verificato da commercialista | 28 |

| Descrizioni (max 90) | car. |
|---|---|
| Quanto vale il contributo su macchinari e software: calcolatore con la formula MIMIT. | 85 |
| Linea ordinaria, 4.0, green e Capitalizzazione: chi può chiederle e come si ottiene. | 84 |
| Ricevi solo i bandi adatti alla tua impresa. Prova gratuita, nessuna carta richiesta. | 85 |

### Conto Termico 3.0 imprese

- **Cosa**: misura conto_termico (bando 1909) — sempre aperto (budget 450 mln imprese)
- **Pagina di arrivo**: /blog/ articolo n. 7 (pubblicato, con calcolatore)
- **Budget**: Google 200 €
- **Parole chiave a corrispondenza esatta**: [conto termico 3.0], [conto termico imprese], [conto termico pompa di calore azienda], [incentivo gse pompe di calore]
- **Parole chiave a frase**: "conto termico capannone", "conto termico 2026", "calcolo conto termico", "fondo perduto efficienza energetica imprese"
- **Parole chiave negative**: privati, condominio, casa, detrazione 50%, bonus casa

| Titoli (max 30) | car. |
|---|---|
| Conto Termico 3.0 imprese | 25 |
| Dal 25% al 65% a fondo perduto | 30 |
| Calcola l'incentivo GSE | 23 |
| Pompe di calore e cappotto | 26 |
| Guida con calcolatore | 21 |
| Esempi ricalcolati GSE | 22 |
| Prova gratis bandinQiaro | 24 |
| Bandi scelti per te | 19 |

| Descrizioni (max 90) | car. |
|---|---|
| Quanto paga il GSE alle imprese su pompe di calore, isolamento, infissi e fotovoltaico. | 87 |
| Calcolatore semplice e avanzato con le formule GSE. Guida verificata da un commercialista. | 90 |
| Ricevi solo i bandi adatti alla tua impresa. Prova gratuita, nessuna carta richiesta. | 85 |

### Brevetti+ 2026

- **Cosa**: bando 4628 — domande dal 25/11/2026 ore 12, a sportello (20 mln)
- **Pagina di arrivo**: pagina del bando (quando la landing è aperta) o articolo da scrivere; nel frattempo /bandi-aperti
- **Budget**: Google 150 € (dal 10/11)
- **Parole chiave a corrispondenza esatta**: [brevetti+], [brevetti+ 2026], [bando brevetti], [brevetti plus invitalia], [contributi brevetti pmi]
- **Parole chiave a frase**: "valorizzazione brevetti contributo", "fondo perduto brevetto", "incentivi brevetti imprese"
- **Parole chiave negative**: deposito brevetto costo privato, ufficio brevetti lavoro, concorso

| Titoli (max 30) | car. |
|---|---|
| Brevetti+ 2026 | 14 |
| Domande dal 25 novembre | 23 |
| Fino a 140.000 € per PMI | 24 |
| Valorizza il tuo brevetto | 25 |
| Requisiti e spese ammesse | 25 |
| Sportello: arriva pronto | 24 |
| Prova gratis bandinQiaro | 24 |

| Descrizioni (max 90) | car. |
|---|---|
| Chi può chiedere Brevetti+ 2026, cosa finanzia e come prepararsi prima del 25 novembre. | 87 |
| Scheda verificata sul decreto MIMIT. Ricevi solo i bandi adatti alla tua impresa, gratis. | 89 |

### Startup e digitale (Smart&Start, voucher digitalizzazione)

- **Cosa**: bando 3015 / misure regionali (Piemonte 4193, Lazio 563) — Smart&Start a sportello; voucher regionali con scadenze diverse
- **Pagina di arrivo**: /blog/ articolo startup e digitale (in preparazione, passo 8) e /bandi-aperti/<regione>
- **Budget**: Google 150 €
- **Parole chiave a corrispondenza esatta**: [smart&start], [smart and start italia], [finanziamenti startup innovative], [contributi startup 2026], [voucher digitalizzazione pmi]
- **Parole chiave a frase**: "fondo perduto startup", "bandi startup innovative", "voucher digitalizzazione 2026", "contributi digitalizzazione imprese"
- **Parole chiave negative**: lavoro startup, stage, corso, idee startup

| Titoli (max 30) | car. |
|---|---|
| Bandi per startup 2026 | 22 |
| Smart&Start: come funziona | 26 |
| Tasso zero fino a 1,5 mln | 25 |
| Voucher digitalizzazione | 24 |
| Bandi della tua regione | 23 |
| Prova gratis bandinQiaro | 24 |
| Solo bandi adatti a te | 22 |

| Descrizioni (max 90) | car. |
|---|---|
| Smart&Start, voucher regionali per il digitale e bandi per startup: requisiti e scadenze. | 89 |
| Ti segnaliamo solo i bandi adatti alla tua impresa. Prova gratis, nessuna carta richiesta. | 90 |

### Bandi aperti per regione (campagne locali)

- **Cosa**: pagine /bandi-aperti/<regione> (14 indicizzate) — sempre
- **Pagina di arrivo**: /bandi-aperti/<regione>
- **Budget**: Google 0-200 € (dopo i primi dati)
- **Parole chiave a corrispondenza esatta**: [bandi regione lombardia imprese], [bandi aperti veneto], [contributi imprese piemonte], [bandi lazio pmi], [bandi emilia romagna imprese]
- **Parole chiave a frase**: "bandi aperti [regione]", "contributi a fondo perduto [regione] 2026", "finanziamenti imprese [regione]"
- **Parole chiave negative**: concorsi, lavoro, bandi di gara, case popolari, borse di studio

| Titoli (max 30) | car. |
|---|---|
| Bandi aperti in Lombardia | 25 |
| Contributi per imprese 2026 | 27 |
| Aggiornati ogni giorno | 22 |
| Solo quelli per imprese | 23 |
| Scadenze e importi chiari | 25 |
| Prova gratis bandinQiaro | 24 |

| Descrizioni (max 90) | car. |
|---|---|
| I bandi aperti per le imprese della tua regione, con scadenza e importo, ogni giorno. | 85 |
| Ricevi solo quelli adatti alla tua impresa. Prova gratuita, nessuna carta richiesta. | 84 |

## Negative comuni a tutte le campagne

concorsi, concorso, lavoro, offerte di lavoro, assunzioni pubbliche, borse di studio, bandi di gara, appalti, case
popolari, bonus famiglie, reddito, isee, privati, condominio, superbonus, tesi, pdf, wikipedia.

## ChatGPT (circa 600 €)

Annunci brevi accanto alle risposte su agevolazioni per imprese. Stessi temi (Voucher Cloud, iperammortamento,
Sabatini, Conto Termico, startup), con un testo di una o due frasi e il link alla guida:

- "Voucher Cloud e Cybersecurity: domande dal 10 novembre. Scopri se la tua PMI può chiederlo e quanto vale." → guida
  Voucher Cloud.
- "Iperammortamento 2026: calcola quanto risparmi su macchinari, software e fotovoltaico." → articolo n. 8.
- "Nuova Sabatini: calcola il contributo sugli interessi del tuo finanziamento." → articolo n. 11.
- "Bandi per la tua impresa, scelti per te ogni settimana. Prova gratuita, senza carta." → landing.

Parametri di targeting e prezzi del canale da verificare all'apertura dell'account (il formato è nuovo).

## Come si aggiorna

Ogni settimana, dopo la ricerca dei bandi più discussi (PIANO_QUALITA azione 5): si toglie la campagna di un bando
chiuso o esaurito (es. Investimenti sostenibili 4.0 e Scoperta imprenditoriale II si sono chiusi in 1-2 giorni: per
gli sportelli che si esauriscono subito la campagna va accesa **prima** dell'apertura, con la guida su come
prepararsi), si aggiunge quella dei bandi nuovi in vetrina, si spostano i soldi verso le campagne che portano
registrazioni al costo più basso.
