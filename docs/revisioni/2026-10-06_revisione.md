# Revisione dell'architettura n. 1 — 06/10/2026

Lavoro di sola lettura: nessuna modifica a database, repository, /srv o container. Numeri presi dal database di
produzione il 06/10/2026 verso le 14:30 (query in `/tmp/claude-1000/cp/ra_q*.sql` e `ra_indicatori.sql`, indicatori
salvati in `/tmp/claude-1000/cp/indicatori_2026-10-06.csv`). È la prima revisione: non c'è un confronto con la
precedente, questi numeri fanno da **punto di partenza**.

Obiettivo di riferimento (`docs/VISIONE.md`): da 7-8/10 a **9/10** prima di vendere, senza perdere le misure
famose, con l'IA dentro **100 $ al mese**.

---

## 1. Il quadro in una pagina

| Fase | Numeri principali |
|---|---|
| Fonti | 303 nel registro: 267 attive, 15 difficili, 20 escluse, 1 da verificare. Ultimo controllo in errore: 4 attive (DNS del 04/10, transitorio). Errori nei controlli ultimi 14 giorni: 5,6% |
| Annunci | 10.831 (3.667 dalla scorta). Rilevanti 5.108 (5.085 collegati a un bando), non rilevanti 5.370, **da rivedere 353** (tutti di oggi, in attesa dell'IA) |
| Bandi | 4.336 non uniti + 51 uniti. Pagina ufficiale trovata 4.092 (94%), non trovata 240. Filtro: testo ufficiale 1.951, sintesi 2.087, nessuno 56, **da valutare 242** |
| Preliminare | Fatto su 1.946 dei 1.951 con testo. Dei 1.247 con testo e senza scheda: **886 fermati come chiusi**, 277 non per imprese, 59 edizione vecchia, 18 senza testo, 3 in attesa di scheda |
| Schede | **671 proponibili** (355 aperte, 28 in arrivo, 248 chiuse, 40 senza stato). Controllo senza IA: **33 con problemi gravi** (32 aperte o in arrivo, quindi nascoste ai clienti), 423 (63%) da migliorare |
| Qualità misurata | Verifica a campione 02-04/10: 87% → 90% dei campi giusti. Pilota IA 06/10: 2 gravi su 19 (≈10%) che il controllo senza IA non vede. Ricerca misure famose: 30/66 a posto, 25 con difetti, **11 assenti** |
| Feedback | **1** giudizio in tutto (voto 3). Nessun voto di qualità di Matteo sulle schede |
| Abbinamento ed email | 0 imprese iscritte, 3 profili di prova, 0 email alle imprese preparate; il riepilogo del lunedì a Matteo **non è partito** ("manca EMAIL_MATTEO nel .env"); Resend non configurato |
| IA | Ottobre: **11,86 $** in 6 giorni (6,92 $ il 01/10 e 4,31 $ il 02/10 per lo smaltimento iniziale; poi 0,04-0,23 $ al giorno). Tetto nel codice: 30 $ se `IA_TETTO_MESE_USD` non è impostato |
| Regista | 145 giri dal 01/10, nessun buco oltre 90 minuti, nessun errore registrato; 6 esecuzioni rimaste "in corso" (interrotte dai riavvii del deploy) |
| Server | Un solo server OVH; database 453 MB; backup notturno del database 14 giorni **sullo stesso disco**; allegati (12,2 GB) non nel backup del database |

### Dove si ferma il lavoro (l'imbuto)

```
annunci 10.831 ─► rilevanti 5.108 ─► bandi 4.336 ─► pagina trovata 4.092 ─► testo ufficiale 1.951
                    (353 da rivedere)                  (240 non trovata)       (2.087 solo sintesi, 242 da valutare)
  ─► preliminare passato ≈ 700 ─► schede proponibili 671 ─► senza problemi gravi 638 ─► aperte/in arrivo 351
                                                                                     (+ 32 aperte nascoste per gravi)
```

**L'arretrato "839 bandi con testo e senza scheda"**: non sono riuscito a riprodurre esattamente 839, ma
corrisponde al gruppo dei bandi con testo ufficiale **fermati dal controllo preliminare come chiusi** (886 dentro
il passo "senza scheda"; 996 contando anche quelli insieme "non per imprese"). Non è una coda di schede da
scrivere: la coda vera "preliminare passato, senza scheda" è di **3 bandi**. Il punto debole è un altro: quei
"chiusi" sono stati decisi
- **341 dai segnali gratuiti senza IA** (scadenza nei dati della fonte, frasi come "Conclusione Data
  aggiornamento stato" nella pagina, 73 casi solo per questa frase sul portale Calabria);
- **≈ 490 dai controlli preliminari delle sessioni del 26 e 28/09**, cioè prima dei fascicoli completi (03/10) e
  delle sottopagine (06/10);
- e **non vengono mai ricontrollati** (il ricontrollo settimanale dello stato riguarda solo i proponibili).
  50 di questi hanno una scadenza futura.

---

## 2. Voto per area

| Area | Voto | Perché (in breve) |
|---|---|---|
| Fonti | **7** | 267 attive e sane, ma 11 misure famose su 66 assenti (6 per fonte mancante, 5 per fonte letta solo in prima pagina); 15 fonti difficili tra cui la **Camera di Milano Monza Brianza Lodi** (protezione Imperva), Comune di Venezia, Catania, Rieti, Viterbo, Potenza; Lazio ha 7 fonti attive su 13 |
| Smistamento | **7,5** | Regole + IA funzionano (48,8% deciso dall'IA); 353 da rivedere in attesa; nessuna misura dell'errore: c'è 1 sola correzione di Matteo |
| Doppioni | **5,5** | Il difetto più frequente: 19 doppioni tra le 66 misure famose; 37 gruppi (95 bandi) con lo stesso indirizzo chiave non uniti; 92 bandi con annunci a più di 300 giorni di distanza (edizioni di anni diversi nello stesso bando, es. 1225: edizioni 2023, 2025 e graduatoria 2026 insieme) |
| Documenti | **7** | Pagina trovata nel 94%; ma 14,1% dei file in errore: 2.961 non scaricati per il limite di 30 file (97 bandi), 550 vietati da robots.txt, 108 certificati SSL rifiutati; 240 pagine non trovate (Città metropolitane, Bolzano, FVG, Marche, INPS, Turismo, VdA, Molise) |
| Schede | **7** | 90% dei campi giusti nel campione; ma il 63% delle proponibili ha almeno un "da migliorare" (fornitori non noti 193, ATECO vincolato senza codici 174) e 30 schede "bando ufficiale" senza il testo del bando |
| Controlli | **5,5** | Il controllo senza IA c'è e gira ogni ora, ma vede solo la forma: il pilota IA ha trovato 2 gravi su 19 che non vedeva; i "chiusi" e i "non per imprese" (≈1.160 bandi) non hanno nessun secondo controllo; 1 solo feedback |
| Abbinamento | **6** | Regole chiare e uniche, ma mai provato su imprese vere (0 iscritte, 3 profili di prova); i risultati non si salvano, quindi non si possono ricontrollare |
| Email | **3** | Resend non configurato, riepilogo del lunedì non partito, 0 email alle imprese; nessun avviso automatico a Matteo quando qualcosa si rompe |
| Costi | **8,5** | Spesa reale molto bassa (≈ 0,2 $/giorno a regime senza schede), Batch API e cache delle istruzioni già usate; da sistemare: tetto di base 30 $ nel codice e nella documentazione, 93 preliminari diretti pagati 3,8 volte quelli in lotto |
| Sicurezza e continuità | **5** | Server unico, backup solo sullo stesso disco, allegati fuori dal backup, nessuna prova di ripristino documentata, repository pubblico, chiavi solo nel `.env`, vecchia utenza "matteo" ancora attiva |

**Voto complessivo: 6,5 / 10** come sistema (la qualità delle singole schede è più alta, intorno a 7,5-8, ed è
quella che Matteo vede; il voto più basso viene da doppioni, secondo controllo, email e continuità).

---

## 3. Le 10 falle più importanti (in ordine di impatto sull'affidabilità)

1. **Doppioni e edizioni mescolate.** 19 doppioni tra le 66 misure più discusse (Nuova Sabatini: 1 misura + 5
   bandi); 37 gruppi / 95 bandi con lo stesso indirizzo chiave non uniti; 92 bandi (25 proponibili) contengono
   annunci a più di 300 giorni di distanza, segno di edizioni diverse nello stesso bando. Per il cliente è la
   cosa più visibile: la stessa misura due volte, o una scheda dell'edizione sbagliata.
2. **I "chiusi" non vengono mai riverificati.** 886 bandi con testo ufficiale fermati come chiusi: 341 dai
   segnali senza IA, ≈490 da preliminari del 26-28/09 fatti con fascicoli incompleti. Nessun passo li riguarda.
   50 bandi fermati (chiusi o non per imprese) hanno la scadenza nel futuro. È la via più probabile per
   **perdere una misura famosa senza accorgersene**.
3. **Fonti mancanti o lette solo in superficie.** 11 misure famose su 66 (17%) assenti; la Camera di Milano
   (la più grande d'Italia) è tra le fonti difficili; 6 fonti nazionali o UE senza annunci nuovi da 14 giorni
   (SIMEST ferme al 24-28/09, `mimit_incentivi` senza novità dal 28/09). Una fonte che espone solo le ultime 10
   notizie perde i bandi (caso Green Tour).
4. **Nessun secondo controllo del contenuto.** Il controllo senza IA vede solo date, numeri e campi vuoti. Il
   pilota IA ha trovato 2 errori gravi su 19 schede (≈10%: un bando non per imprese, una scadenza sbagliata). Per
   arrivare al 90% serve una revisione dopo ogni scheda, oggi assente.
5. **32 schede aperte o in arrivo nascoste ai clienti** per problemi gravi (30 "bando ufficiale" senza il testo
   del bando tra i documenti, 3 contributi oltre la dotazione). Oltre a queste, 40 proponibili senza stato e 36
   "bando ufficiale" con documentazione classificata come sintesi. Nessuno ha il compito di sistemarle.
6. **Continuità: server unico e backup sullo stesso disco.** Dump notturno 14 giorni in `/var/backups` dello
   stesso VPS; 12,2 GB di allegati non sono nel dump; nessuna prova di ripristino scritta; chiavi solo nel `.env`
   (prossimo passo 20 e 21 ancora da fare). Un guasto del disco o un errore umano ferma tutto.
7. **Nessun avviso automatico a Matteo.** Il riepilogo del lunedì non è partito (manca `EMAIL_MATTEO`), Resend non
   c'è. Se il regista si ferma, il tetto IA si raggiunge o una fonte importante tace, lo si scopre solo aprendo
   la plancia.
8. **Il deploy interrompe il lavoro in corso.** Ogni unione in `main` riavvia i servizi entro 5 minuti anche a
   metà giro: 6 esecuzioni sono rimaste "in corso" (regista, pagine, documenti, doppioni; due solo oggi alle 08:50
   e 12:31). Un passo interrotto a metà può lasciare dati parziali.
9. **Documenti persi per limiti e blocchi.** 2.961 file non scaricati per il limite di 30 per annuncio (97 bandi
   con testo toccati: il bando giusto può essere il 31°), 550 vietati da robots.txt (60 bandi con testo, 47 solo
   sintesi), 108 errori di certificato, 240 pagine non trovate che si riprovano solo dopo 14 giorni.
10. **Pagine cambiate non lette.** Il ricontrollo dello stato ha trovato 108 pagine cambiate in 4 giorni, ma
    cerca solo frasi di chiusura: proroghe, rettifiche, nuove date finiscono nella scheda solo con il ricontrollo
    dei documenti ogni 14 giorni. In tutto il sistema c'è stata **1 sola** "scheda da aggiornare".

Altre falle minori: abbinamento mai provato su imprese vere; tetto IA di base 30 $ nel codice e nella documentazione
(`COME_FUNZIONA.md`) mentre la decisione è 100 $; repository pubblico; vecchia utenza "matteo" attiva; 122
richieste di schede in lotto andate in errore il 02/10 (senza costo, ma segnale che il lotto delle schede va
provato bene prima di accenderlo davvero).

### Cosa lascia un risultato ispezionabile (richiesta di Matteo)

| Fase | Risultato leggibile da un agente | Manca |
|---|---|---|
| Raccolta | `controlli` (esito, novità per controllo), `annunci` | il motivo di un "silenzio" (pagina uguale? zero elementi letti?) non si distingue bene |
| Smistamento | `smistamenti` (esito, motivo, chi), `eventi_catena` | misura dell'errore (campione verificato) |
| Doppioni | `bandi_dubbi`, `eventi_catena`, `annunci.collegamento_motivo` | un rapporto periodico dei doppioni probabili non uniti |
| Pagina e documenti | colonne `pagina_stato/motivo`, `allegati` | nessuna riga in `eventi_catena`: non si ricostruisce *quando* e *perché* |
| Filtro | `bandi.documentazione_motivo` | storico (si sovrascrive) |
| Preliminare | `bandi.preliminare` (motivo, chi) | storico; nessun secondo parere sui "chiusi" |
| Scheda | `bandi_versioni`, `chiamate_ia` | le schede di sessione hanno 126 righe in `chiamate_ia` su 671: tracciabilità parziale |
| Controllo | `bandi.controllo` | la verifica IA in sessione non ha un'importazione: il suo esito non resta nel database |
| Abbinamento | **niente** (si calcola al volo) | salvare i risultati per profilo e data |
| Email | `email_imprese`, `notifiche_inviate` | — (oggi vuote) |
| Revisione architettura | questo rapporto | una tabella degli indicatori nel tempo (vedi istruzioni) |

---

## 4. Costi: il tetto di 100 $ regge?

Prezzi nel codice (`app/schede/ia.py`): Opus 5.5 4 $/20 $ per milione di token in/out, Batch a metà prezzo.
Costi misurati: smistamento 0,017 $ a lotto, doppione 0,0046 $, preliminare 0,0097 $ in lotto (0,037 $ diretto),
scheda diretta 0,87 $ (145.000 token in). Il testo medio di una scheda è di 154.000 caratteri (≈ 50.000 token) e
il 25% arriva al massimo di 300.000: una scheda in lotto costa quindi **0,30 $ in media, fino a 0,45 $**.

**Stima a regime (al mese)**, partendo dai bandi nuovi dei giorni 02-06/10 (≈ 28 al giorno) e dalla quota che
arriva alla scheda nei primi giorni (≈ 13,6%):

| Voce | Quantità al mese | Costo |
|---|---|---|
| Schede nuove | ≈ 115 | 35-50 $ |
| Schede da aggiornare (proroghe, rettifiche, ≈ 10% delle aperte) | ≈ 40 | 12-18 $ |
| Smistamento, doppioni, preliminari | ≈ 400 + 400 + 300 | ≈ 12 $ |
| **Totale senza revisioni** | | **≈ 60-80 $** |
| Margine per la verifica IA delle schede | | 20-40 $ |

Il tetto di 100 $ **regge per il flusso normale**, ma lascia poco spazio: la verifica con l'IA dopo ogni scheda
con Opus costerebbe altri 25-40 $ e farebbe sforare. Va fatta con un modello più economico o solo sulle aperte.

**L'arretrato.** Scrivere la scheda a tutti gli 839-886 "chiusi" costerebbe 250-400 $: con 20-40 $ di margine
al mese ci vorrebbero **7-19 mesi**, quindi **non va fatto così**. Rifare solo il **controllo preliminare** in
lotto sui 996 fermati costa **≈ 10 $ e un giorno**; ne usciranno presumibilmente 50-100 ancora aperti (50 hanno già
una scadenza futura), cioè 15-45 $ di schede, smaltibili in **2-4 settimane** dentro il tetto.

---

## 5. Cinque opportunità di risparmio

1. **Riverificare l'arretrato con il preliminare, non con la scheda**: ≈ 10 $ invece di 250-400 $ (vedi sopra).
2. **Modello più economico per i compiti di classificazione** (smistamento, doppioni dubbi, preliminare) e per la
   verifica delle schede: nel codice ci sono già i prezzi di Sonnet 5 (metà di Opus) e Haiku 4.5 (un quarto).
   Prova A/B su 100 casi già decisi prima di cambiare (la scelta di Opus del 28/09 si riapre solo con i numeri).
3. **Niente chiamate dirette**: i 93 preliminari diretti sono costati 3,43 $ contro 3,41 $ per 352 in lotto
   (3,8 volte di più a chiamata). Tenere `IA_PRELIMINARI_DIRETTI=0` salvo urgenze.
4. **Aggiornare le schede con il solo frammento cambiato**: per proroghe e rettifiche mandare all'IA la scheda
   attuale + il documento nuovo, non tutto il fascicolo (300.000 caratteri): da 0,30-0,45 $ a ≈ 0,05-0,10 $.
5. **Non schedare ciò che non serve**: saltare (o mettere in fondo alla coda) i bandi che scadono entro 3 giorni
   o già chiusi per le date, e tagliare dal fascicolo graduatorie ed esiti (2.051 file "graduatoria") che non
   servono alla scheda; dare priorità alle misure nazionali e regionali grandi.

## 6. Cinque opportunità di qualità

1. **Revisione dopo ogni scheda in automatico**: un lotto di verifica IA (modello economico) per ogni scheda nuova
   o cambiata delle aperte, con importazione dell'esito in `bandi.controllo`; i gravi fermano la proposta come oggi.
2. **Secondo parere sui fermati**: il preliminare rifatto sui "chiusi" dei segnali e delle sessioni di settembre;
   poi ogni mese sui fermati con scadenza futura o con annunci nuovi.
3. **Doppioni tra fonti e tra edizioni**: regola per i gestori (stesso incentivo su MIMIT, Invitalia,
   incentivi.gov.it, Camere → un bando), e regola opposta per le edizioni (annunci a più di 300 giorni o anni
   diversi nel titolo → bandi separati); rapporto settimanale dei gruppi con lo stesso indirizzo chiave.
4. **Ricerca settimanale delle misure famose** (prossimo passo 27) con il confronto automatico con il database: è
   l'indicatore più vicino a "non perdere le misure note".
5. **Giudizi veri**: 20 schede a settimana votate da Matteo e Luca (prossimo passo 3); l'indicatore "schede
   affidabili %" (voto ≥ 4 e nessun grave) diventa il numero da portare a 90%.

---

## 7. Piano in passi piccoli

Ogni passo è una pull request o un'operazione di sessione, con un numero da controllare alla revisione dopo.

| # | Passo | Costo | Indicatore che deve muoversi |
|---|---|---|---|
| 1 | Verificare che nel `.env` ci sia `IA_TETTO_MESE_USD=100` (oggi il codice usa 30 se manca) e correggere `COME_FUNZIONA.md` | 0 | I01 sotto 100 $ |
| 2 | Impostare `EMAIL_MATTEO` e la chiave Resend; aggiungere al riepilogo del lunedì: regista fermo da > 2 ore, tetto IA all'80%, fonti rosse, misure famose mancanti | 0 | M03, riepilogo ricevuto |
| 3 | Backup fuori dal server (spazio OVH o simile, copia cifrata notturna, prossimo passo 21) e una **prova di ripristino** scritta; gestore delle password (passo 20); togliere l'utenza "matteo" (passo 19) | pochi € al mese | backup esterno presente |
| 4 | Rifare in lotto il controllo preliminare dei 996 fermati (segnali e sessioni di settembre), poi schede per quelli che passano | ≈ 10 $ + 15-45 $ | B07, B08, B09 in calo |
| 5 | Sistemare le 32 aperte nascoste per gravi (documento del bando mancante o nome poco chiaro) con una sessione | 0 (sessione) | S04 = 0 |
| 6 | Deploy "gentile": prima di riavviare, aspettare la fine del giro del regista (o chiudere le esecuzioni rimaste aperte all'avvio) | 0 | R03 = 0 |
| 7 | Doppioni: rapporto settimanale dei gruppi con la stessa `url_chiave` e degli annunci a > 300 giorni; regole gestori/edizioni | 0 | D01, D02 in calo |
| 8 | Verifica IA automatica delle schede aperte con modello economico e importazione (passo 1 delle opportunità di qualità), dopo una prova A/B su 30 schede del pilota | 10-25 $/mese | gravi trovati per scheda, S03 |
| 9 | Fonti: Camera di Milano (uscita dall'Italia o fonte alternativa), misure famose assenti, paginazione delle fonti "solo ultime notizie"; ricerca settimanale (passo 27) | 0-5 € al mese | misure famose assenti 11 → 0 |
| 10 | Pagine cambiate: mandare all'IA il frammento cambiato (in lotto) per vedere proroghe e nuove date | ≈ 2-4 $/mese | schede da aggiornare > 0 quando servono |
| 11 | Documenti: alzare il limite di 30 file mettendo prima bando e decreti; riprova subito delle pagine non trovate quando cambia la regola della fonte | 0 | D04 in calo, B03 in calo |
| 12 | Salvare i risultati dell'abbinamento per profilo (anche di prova) per poterli confrontare nel tempo | 0 | — |

Ordine consigliato per la prossima settimana: 1, 2, 4, 5, 6. Poi 3 (decisione di spesa di Matteo), 7, 8.

---

## 8. Cosa non ho potuto verificare

- Il valore reale di `IA_TETTO_MESE_USD` e degli altri interruttori nel `.env` (non letto per non esporre segreti).
- Se il backup del disco di OVH è attivo e con quale frequenza.
- La provenienza esatta del numero 839 (vedi §1).
- L'esattezza dei segnali di chiusura del portale Calabria ("Conclusione Data aggiornamento stato"): sembrano
  plausibili sui casi guardati, ma il bando 1225 mostra edizioni di anni diversi unite insieme.
