# Revisione della struttura di Bandi Radar prima di collegare l'IA

*25/09/2026. Basata sul piano (`docs/PIANO_PROGETTO.md`), sul formato della scheda (`docs/SCHEDA_BANDO.md`, `004_schede.sql`), sui due prompt e sui risultati della prova in `/home/ubuntu/prova-ia/` (10 schede di Sonnet, 2 lotti di smistamento di Haiku, riferimento incentivi.gov.it). Non ho potuto interrogare il database (niente accesso a Docker da questa sessione): i numeri sull'arretrato vengono dai file della prova e dalle cifre che mi sono state date.*

## Sintesi

1. **L'impianto regge.** La catena resta giusta: raccolta senza IA, smistamento a regole e poi Haiku, Sonnet per le schede e abbinamento con regole fisse. I costi sono molto sotto il piano: circa **20-50 $ una tantum** per l'arretrato e **10-20 $ al mese** a regime.
2. **Ci sono però tre lacune di struttura.** Vanno chiuse **prima** della prima grande passata di Sonnet, perché dopo toccherebbe rifare tutte le schede.
3. **Prima lacuna: annuncio e bando sono ancora la stessa cosa.** Oggi un annuncio produce una scheda (`bandi.annuncio_id` è UNIQUE). Nella realtà più annunci portano allo stesso bando: il catalogo nazionale, la Regione, la Camera, una notizia, poi la proroga, le FAQ, la graduatoria. Serve un legame "molti annunci → un bando" con una chiave che riconosca i doppioni.
4. **Seconda lacuna: manca un passo "trova la pagina ufficiale".** Nella prova 5 schede su 10 non hanno avuto il bando vero: pagina con login, catalogo o notizia che rimandano altrove, bando troncato perché messo in fondo agli allegati. In più una scheda è stata spesa su un bando del 2020 per enti pubblici.
5. **Terza lacuna: i campi che servono al confronto sono testo libero o mancano.** Il territorio è scritto a parole ("Provincia di Modena (Emilia-Romagna)"). Mancano forma giuridica, soggetti ammessi (imprese, professionisti), età dell'impresa, requisiti come impresa femminile o giovanile, soglie di dipendenti e fatturato, spesa minima, regime d'aiuto.
6. **Una trappola da evitare.** Oggi un campo vuoto vuol dire due cose diverse: "il bando non pone limiti" oppure "non abbiamo letto il bando". Per l'abbinamento la differenza è decisiva. La scheda 2587 (pagina con login) ha l'ATECO vuoto: un motore ingenuo la proporrebbe a tutti.
7. **Bandi con più linee.** La scheda "a un valore per campo" va bene per il catalogo ma non basta quando le linee hanno regole diverse (6 casi su 8 schede utili). Basta aggiungere nella risposta dell'IA un elenco facoltativo di "linee", senza rifare le tabelle.
8. **Modelli: Haiku e Sonnet vanno bene.** L'omissione di Haiku (2 annunci su 45) si risolve con un controllo automatico e lotti più piccoli, non cambiando modello. Il costo vero non è l'IA ma il tempo di Matteo per rivedere le schede. Togliere doppioni e bandi chiusi lo riduce di più della metà.

---

## 1. I campi della scheda bastano per l'abbinamento?

**Risposta breve: no, bastano per il catalogo ma non per un confronto automatico affidabile.**

Il profilo che si chiederà alle anagrafiche (`RICHIESTA_SCHEMA_ANAGRAFICHE.md`) ha, per ogni caratteristica, un "gemello" da confrontare nella scheda. Ecco la situazione, campo per campo:

| Caratteristica del cliente | Campo nella scheda oggi | Problema | Cosa serve |
|---|---|---|---|
| ATECO (principale e secondari) | `codici_ateco`, `codici_ateco_esclusi` (elenchi) | Buono il formato a elenco. Però la versione (2007 o 2025) sta solo nelle avvertenze, in testo libero. E spesso il bando esclude settori in modo implicito ("tutti i settori ammessi al de minimis", scheda 4136) | campo `ateco_versione` (2007/2025); campo `regime_aiuto` (de minimis / esenzione GBER / altro), che porta con sé le esclusioni standard (pesca, produzione agricola primaria...); più avanti una tabella di conversione ATECO 2007→2025 |
| Sede (comune, provincia, regione; legale o operativa) | `territorio`, **testo libero** | Nelle schede ci sono "Lombardia", "Provincia di Padova", "Toscana - province di Pistoia e Prato", "Provincia di Modena (Emilia-Romagna)" e anche vuoto. Non si confronta in automatico. In 4199 valgono solo alcuni comuni della provincia | elenco di codici (regione, provincia, comune; "IT" per l'Italia, "UE"), più il tipo di sede richiesto (legale / operativa / "da attivare entro l'erogazione", come in 2587b) |
| Dimensione | `dimensioni_ammesse` (valori fissi) | Va bene | — |
| Forma giuridica | **manca** | Molti bandi escludono o riservano (ditte individuali, cooperative, società di capitali) | `forme_giuridiche_ammesse`/`escluse`, con valori fissi |
| Tipo di soggetto | **manca** | La 3055 era per enti pubblici: l'ha capito solo Sonnet, a pagamento. I liberi professionisti (clienti tipici di uno studio) a volte sono ammessi e a volte no. incentivi.gov.it ha il campo `soggetti` | `soggetti_ammessi`: impresa, libero professionista, ente pubblico, ente del terzo settore, persona fisica |
| Età dell'impresa | **manca** (è dentro `requisiti`) | "Startup attiva da non più di 24 mesi" (2587b) e "nuova impresa" non si leggono in automatico | `eta_impresa_min_mesi`, `eta_impresa_max_mesi` |
| Femminile, giovanile, startup o PMI innovativa, artigiana, cooperativa, agricola | **manca** | La 358 è riservata di fatto alle "mamme imprenditrici" ma nella scheda non c'è un segnale leggibile dalla macchina | `requisiti_speciali`: elenco a valori fissi (femminile, giovanile, startup_innovativa, pmi_innovativa, artigiana, cooperativa, agricola, rating_legalita...), separando "obbligatorio" da "dà punti in più" |
| Dipendenti, fatturato | **manca** | Soglie minime o massime (e condizioni come "assumere under 35" in 4199) | `dipendenti_min/max`, `fatturato_min/max` quando il bando li indica |
| Investimenti previsti | `tema` (**un solo valore**), `cosa_finanzia` e `spese_ammesse` (testo) | Due delle 8 schede utili sono finite in "altro" (358, 4136). Un bando spesso tocca più temi. Le spese sono solo testo | `temi` a valori multipli; `categorie_spesa` a valori fissi (macchinari, opere edili, software, consulenze, formazione, personale, fiere, marketing...), le stesse che si chiederanno nel profilo |
| Taglia del progetto | **manca** | Spesa minima: 2.000 € in 358, 3.000 € in 4383, 6.000 € in 2587b. Oggi è sepolta nel testo | `spesa_minima`, `spesa_massima` |
| Export | — | Raramente è un requisito | nessun campo nuovo; basta il tema "internazionalizzazione" |
| Aiuti già ricevuti (de minimis) | — | Serve il regime d'aiuto del bando | `regime_aiuto` (vedi riga ATECO) |

Altri campi utili al cliente e a Matteo, oggi solo nella sintesi: `modalita` (sportello / graduatoria / click day), `dotazione` (fondi totali: 60.000 € in 358 vuol dire poche domande accolte), `gestore` (Unioncamere, Invitalia, Finpiemonte...).

**Il confronto con incentivi.gov.it.** Il catalogo nazionale fa quasi tutto con **elenchi a valori fissi**: `regioni`, `dimensioni`, `soggetti`, `forma` (più di una, non "misto"), `ambito` (più di uno), `spese` (categorie), `settori` (macro-settori a parole) più `costo_min`/`costo_max`, `dotazione`, `gestore`, `link_ente`. Su due punti la nostra scheda fa già meglio: l'ATECO (loro lo scrivono in testo libero, per esempio "Tutti i settori economici ammissibili...") e il territorio sotto la regione (loro si fermano alla regione, ma per i bandi delle Camere conta la provincia). Anche loro hanno errori: in 4231 `costo_max` vale 99.999.998.000, e Sonnet l'ha giustamente scartato. **La lezione da copiare:** tutto quello che serve a un filtro va scritto con valori presi da un elenco fisso, e il testo libero resta per spiegare.

**La regola dei tre stati (la più importante).** Ogni campo di confronto deve distinguere tre casi:

- **il bando pone un vincolo** (per esempio solo micro e piccole);
- **il bando dice espressamente che non ci sono vincoli** ("tutti i settori");
- **non lo sappiamo**, perché il documento non l'abbiamo letto.

Oggi `[]` vuol dire sia "nessun limite" sia "niente dati". La scheda 2587, ricavata da una pagina di login, ha `codici_ateco: []` e `dimensioni_ammesse: []`: per un motore di abbinamento sarebbe un bando valido per tutti. Serve anche un indicatore generale di completezza della scheda: "bando ufficiale letto", "solo pagina di sintesi" oppure "nessun documento". L'abbinamento, allora, darà per un bando letto a metà "da verificare", mai "compatibile".

**Cosa resta a parole.** I requisiti particolari (danni del Ciclone Harry in 4136, "esercizio polifunzionale riconosciuto" in 2814, DURC, polizza catastrofale) non si possono confrontare con un profilo. Vanno mostrati a Matteo e al cliente come **lista di controllo "da verificare"**. Sono la parte che fa lo studio, ed è giusto così.

---

## 2. Bandi con più misure o linee: la scheda "piatta" regge?

**Regge per il catalogo, non per l'abbinamento nei casi con linee diverse.** Nelle 8 schede utili della prova:

- **2587b Fiere Lombardia**: 15.000 € per i nuovi espositori, 8.000 € per chi espone abitualmente o ha già ricevuto il contributo nel primo sportello. La percentuale è 50%, più 5% per le micro e 5% per le startup. La scheda dice "15.000 / 60%", cioè il caso migliore, che non vale per tutti.
- **4136 Ciclone Harry**: 60% finanziamento a tasso zero e 40% fondo perduto. La scheda dice "misto, 400.000 €, 100%". Chi legge "100%" pensa a un fondo perduto totale: è fuorviante.
- **4199 Modena**: da 1.500 a 2.000 € per giovane, secondo il contratto, fino a 2 giovani, più 250 € con il rating di legalità.
- **4383 Bari**: 7.000 € più premi per rating e parità di genere; due linee (digitale/promozione e sostenibilità/accessibilità).
- **2585 Export**: il valore vale "per percorso-Paese", uno solo per impresa.
- **3055** (non per imprese): Linea A veicoli, B biciclette, C smartworking, ognuna con regole sue.

Sonnet ha fatto bene quello che poteva: ha messo il massimo nel campo e spiegato le differenze nella sintesi e nelle avvertenze. Il problema è che **l'abbinamento non legge le avvertenze**. Nei casi comuni le linee differiscono per importi e percentuali, e questo non cambia chi può partecipare. Nei casi peggiori cambia proprio il beneficiario: una linea solo per le startup, una solo per le micro, una per le imprese agricole. Lì la scheda piatta produce abbinamenti sbagliati.

**Cosa propongo (una sola strada):** restano i campi "piatti" per il catalogo e i filtri, e nella risposta di Sonnet si aggiunge un elenco facoltativo **`linee`**, compilato solo quando il bando ne ha. Per ogni linea: nome, beneficiari o requisiti speciali, dimensioni, tipo di agevolazione, massimale, percentuale, spesa minima. Si conserva nel campo `dati` che già esiste, quindi niente tabelle nuove. L'abbinamento controlla prima il bando e poi, se ci sono linee, dice quale linea è adatta al cliente. Va messo nel prompt **adesso**: aggiungerlo dopo l'arretrato vorrebbe dire rifare tutte le schede.

---

## 3. Doppioni e versioni

**Oggi la struttura non li gestisce.** Com'è fatta adesso:

- `annunci` sono unici per coppia fonte + indirizzo: due fonti diverse che parlano dello stesso bando fanno due annunci (va bene).
- `bandi.annuncio_id` è **UNIQUE**: ogni annuncio rilevante diventa una scheda sua. Quindi due fonti portano a **due schede, due chiamate a Sonnet, due revisioni di Matteo e due email al cliente**.
- `allegati` sono legati all'annuncio: lo stesso PDF scaricato da due annunci si scarica e si legge due volte.
- Proroghe, rettifiche, graduatorie e FAQ sono annunci a sé. Lo smistamento li segna giustamente "rilevanti" (il prompt lo chiede), ma poi diventerebbero schede nuove invece di aggiornare quella esistente.

**Quanto è diffuso, dai dati della prova:**

- 4199 (Modena) e 4231 (Pistoia-Prato) arrivano da incentivi.gov.it, ma le due Camere sono anche fonti del registro (`mo.camcom.it` con feed RSS, `ptpo.camcom.it`).
- 2585 "Export su Misura" è arrivato dalla fonte Regione Lombardia, ma la pagina sta sul sito di Unioncamere Lombardia, che è a sua volta una fonte. Lo stesso per il bando Fiere 2587, che gestisce Unioncamere Lombardia.
- 358 è una notizia di Unioncamere Veneto su un bando della Camera di Padova.
- Nel campione di smistamento, 4 dei 29 "rilevanti" sono ripubblicazioni del catalogo nazionale di bandi regionali o camerali (Investment Africa, Tuttofood, Artigiano in Fiera, bostrico FVG). Altri 5 sono graduatorie, esiti o FAQ (352, 904, 2430, 1144, 3956).

**Cosa serve:**

1. **Legame molti-a-uno.** Una colonna `bando_id` in `annunci` (al posto di `annuncio_id` UNIQUE in `bandi`), più il **ruolo** dell'annuncio: `origine`, `doppione`, `proroga/rettifica`, `graduatoria/esito`, `faq`, `chiusura`. Gli allegati vanno legati al bando, non all'annuncio. L'impronta (sha256) evita di scaricare e leggere due volte lo stesso file.
2. **Chiave di deduplica**, in ordine di affidabilità:
   - **codice ufficiale** quando c'è: il codice di Bandi Online Lombardia (RLO12026055023), l'identificativo di incentivi.gov.it, l'identificativo del bando sul portale UE, i codici delle Camere come "26BUA";
   - **indirizzo della pagina dell'ente ripulito**: senza parametri e senza "www", e per il catalogo nazionale il `link_ente`;
   - **somiglianza**: stesso ente (normalizzato: "CCIAA di Modena" = "Camera di Commercio di Modena"), stesso anno o edizione, titolo simile. I casi dubbi li conferma Haiku con una domanda secca ("stesso bando? sì/no") e poi Matteo dalla plancia.
   - **Attenzione alle edizioni:** "Voucher Turismo 2026" non è un doppione del 2025, e "secondo sportello" non è il primo. Anno, edizione e sportello devono far parte della chiave.
3. **Storico minimo.** Quando un annuncio "proroga/rettifica" aggiorna un bando, si salva la versione precedente dei campi (data, annuncio che ha causato il cambiamento, campi cambiati). Serve alla plancia ("storico" di §5b) e alle email ("la scadenza è stata spostata al..."). Lo stesso quando cambia l'impronta di un allegato già letto.
4. **Lo `stato` lo calcola il sistema, non l'IA.** Oggi Sonnet scrive "aperto" o "chiuso" confrontando le date con il giorno della scheda, e la mattina dopo il valore può essere già vecchio. Meglio che l'IA estragga solo le date e i fatti ("a sportello", "sospeso per esaurimento fondi"), e che lo stato si ricalcoli ogni giorno dalle date. "Prorogato" è un evento dello storico, non uno stato.

---

## 4. La catena raccolta → allegati → scheda: dove si rompe

**Cosa è successo alle 10 schede della prova:**

| Scheda | Cosa ha ricevuto Sonnet | Esito |
|---|---|---|
| 2587 | pagina di login (Shibboleth) di Bandi Online, 77 caratteri | scheda vuota; peggio, ATECO e dimensioni "vuoti" che sembrano "nessun limite" |
| 2587b | pagina giusta (rifatta a mano), 5 allegati | buona, ma il **bando ufficiale era il 4° allegato**, dopo due delibere da 50-60.000 caratteri, ed è stato **troncato**: articoli dopo C.1 persi |
| 4199, 4231 | solo la pagina di sintesi di incentivi.gov.it | discrete, senza bando ufficiale; il `link_ente` era nei dati del catalogo ma non è stato seguito |
| 2814 | solo la pagina della Regione Emilia-Romagna | discreta, niente bando e niente ATECO |
| 358 | solo la notizia di Unioncamere Veneto | incompleta **e** su un bando **chiuso** il 24/07 |
| 3055 | bando Finpiemonte **del 2020, per enti pubblici**, 44.000 token | corretto "NON PER IMPRESE", ma a prezzo Sonnet |
| 4136 | bando e scheda prodotto, più 7 moduli (perizie, business plan, fatture) | buona; i moduli sono rumore (circa 40.000 caratteri), uno era vuoto (scansione) |
| 4383 | bando completo più 6 moduli | ottima |
| 2585 | bando completo più 3 moduli | ottima |

**Conclusione:** quando Sonnet riceve il bando vero, la scheda è buona (2585, 2587b, 4136, 4383). Gli errori non sono di Sonnet: nascono **prima**, perché non si è trovato o non si è messo in testa il documento giusto.

**Cosa cambiare nell'ordine dei passi:**

```
oggi:     raccolta → smistamento → allegati (dalla pagina dell'annuncio) → Sonnet
proposta: raccolta → smistamento → 1 RISOLUZIONE → 2 allegati ordinati → 3 CONTROLLO PRELIMINARE → 4 Sonnet → 5 verifica automatica → Matteo
```

1. **Risoluzione: trova la pagina ufficiale e riconosci il bando.** Prima con regole scritte nel registro delle fonti, come per le modalità di lettura, quindi senza codice nuovo per ogni sito:
   - catalogo incentivi.gov.it → segui `link_ente`;
   - Lombardia: un indirizzo `faiDomanda?strumentoCod=RLO...` diventa la pagina di dettaglio con lo stesso codice (la correzione fatta a mano in `lombardia_corretta.json` lo dimostra);
   - notizie di Unioncamere, dei Comuni o del MIMIT che parlano di un bando altrui → il primo link verso il sito di un ente che contiene "bando", "avviso" o un PDF.

   Se una regola non basta, lo dice la plancia ("pagina ufficiale non trovata"). Qui si calcola anche la **chiave di deduplica** (punto 3): se il bando esiste già, l'annuncio si aggancia e si controlla solo se qualcosa è cambiato, **senza chiamare Sonnet**.
2. **Allegati ordinati e scelti.** Si classificano con regole sul nome del file: bando/avviso/"Allegato A" per primi, poi FAQ, poi il decreto più recente, poi il resto. **Modulistica, dichiarazioni, F24, procure e whistleblowing restano fuori** dal testo per Sonnet (si conservano comunque per la plancia). Il troncamento si fa sugli ultimi documenti, non sul bando. Un allegato con testo vuoto si segna come "scansione non letta" e lo si dice nella scheda.
3. **Controllo preliminare con Haiku, economico.** Haiku legge le prime pagine del testo, circa 3.000 parole, e risponde: è per imprese? È l'edizione in corso o un archivio (2020, 2022, 2024)? È ancora aperto o in arrivo? C'è il testo del bando o solo un riassunto? Solo se passa si chiama Sonnet. Nell'arretrato i **bandi chiusi** non si schedano con Sonnet: bastano titolo, ente, date e link per il catalogo. Casi 3055 e 358.
4. **Sonnet**, come oggi, con i campi nuovi dei punti 1 e 2.
5. **Verifica automatica della risposta:** valori negli elenchi ammessi, date sensate (apertura prima della scadenza), importi plausibili (niente 99.999.998.000), fonte citata per ogni campo pieno. Chi non passa va in coda a Matteo.

**Due casi da trattare a parte:**

- **I bandi UE (portale Funding & Tenders).** Nel campione, 6 dei 29 "rilevanti" sono singoli topic Horizon o EIC. Il portale ne pubblica centinaia: sono già dati strutturati dall'API e quasi tutti riguardano ricerca, non le PMI clienti di uno studio. Proposta: nessuna scheda Sonnet per i topic UE, salvo un elenco di programmi adatti (EIC Accelerator, SMP/COSME, LIFE, Digital Europe, i bandi a cascata per PMI).
- **Le pagine elenco con l'archivio.** Alcune fonti (Sondrio, Fincalabra, Marche) mostrano bandi del 2021-2024 insieme ai nuovi. Il controllo preliminare li ferma, ma conviene anche una regola nello smistamento: un anno ≤ 2024 nel titolo, senza 2026, rende l'annuncio "non rilevante per arretrato".

---

## 5. Costi e scelta dei modelli

**Dimensioni misurate** (caratteri divisi per 3,5):

- **Smistamento**: istruzioni circa 750 token; ogni annuncio circa **100 token** in ingresso e **27 token** in uscita (lotti da 45: 5.200-6.000 token in ingresso, circa 1.200 in uscita).
- **Schede**: istruzioni circa 1.200 token. Ingresso per scheda: 1,4k, 2,4k, 2,5k, 3,5k, 3,6k, 20k, 25k, 29k, 44k, 52k token → **media 18.400, mediana circa 12.000**. Uscita media circa **1.150 token**.
- Dopo le correzioni del punto 4, più schede avranno il bando completo, la modulistica sarà tolta e ci saranno i campi nuovi. Per prudenza stimo **25.000 token in ingresso e 2.500 in uscita** per scheda.

**Prezzi unitari** (Haiku 4.5: 1 $ / 5 $ per milione di token in ingresso / uscita; Sonnet 5: 2 $ / 10 $; Batch = metà prezzo):

| Operazione | Costo normale | Con Batch |
|---|---|---|
| smistamento di 1 annuncio (Haiku), con margine del 30% | 0,00035 $ | 0,00017 $ |
| controllo preliminare di 1 annuncio (Haiku, 4.000 token in ingresso, 200 in uscita) | 0,005 $ | 0,0025 $ |
| scheda media della prova (Sonnet: 18.400 in ingresso, 1.150 in uscita) | 0,048 $ | 0,024 $ |
| scheda a regime (Sonnet: 25.000 in ingresso, 2.500 in uscita) | 0,075 $ | 0,038 $ |
| scheda enorme (Sonnet: 52.000 in ingresso, 3.000 in uscita) | 0,13 $ | 0,07 $ |

**Arretrato:**

| Voce | Quanti | Normale | Batch |
|---|---|---|---|
| Smistamento dei "da rivedere" | 2.500 | 0,9 $ (2 $ se si manda a Haiku anche un pezzo del testo della pagina) | 0,5-1 $ |
| Controllo preliminare dei rilevanti | 1.250 | 6 $ | 3 $ |
| Schede Sonnet **senza** deduplica e filtri | 1.250 | 94 $ | 47 $ |
| Schede Sonnet **con** deduplica e senza bandi chiusi | **circa 500** (tra 400 e 700) | 38 $ | **19 $** |

Da dove viene "circa 500": nel campione di smistamento, dei 29 annunci segnati rilevanti solo una decina sono bandi nuovi e attuali. Gli altri sono doppioni del catalogo nazionale (4), graduatorie, esiti e FAQ da agganciare a un bando (5), bandi vecchi o archivi (4) e topic UE di ricerca (6). È circa un terzo. Applicato a 1.250 annunci dà 400-500 schede; con un margine, 500-700. **È una stima su un campione piccolo:** il numero vero lo dirà la deduplica.

**Flusso a regime** (stima). I 4.400 annunci dei primi 1-2 giri comprendono tutto quello che era già sulle pagine elenco, quindi non sono il ritmo normale. Per le fonti che pubblicano spesso stimo **30-60 annunci nuovi al giorno** (il piano diceva 150-300 a settimana; la misura vera arriva dopo 3-4 settimane di raccolta). Con la stessa proporzione di adesso: circa il 55% va a Haiku, circa il 28% risulta rilevante, e di questi circa il 40% sono bandi nuovi. Si aggiungono aggiornamenti e allegati cambiati.

| Voce | Al mese | Normale | Batch |
|---|---|---|---|
| Smistamento Haiku | 500-1.000 annunci | 0,3 $ | 0,15 $ |
| Controllo preliminare | 250-500 | 2 $ | 1 $ |
| Schede Sonnet (nuove più riletture) | 150-250 | 11-19 $ | **6-10 $** |
| **Totale IA** | | **circa 15-20 $** | **circa 8-12 $** |

È meno della metà dei 35-50 € del piano (§4). Il tetto di spesa di 30 € al mese basta, anche per assorbire l'arretrato in due mesi.

**La memoria temporanea (cache)** conviene poco: le istruzioni sono circa 1.200 token su 25.000, e la parte variabile (i documenti) cambia a ogni scheda. Risparmio sotto il 5%: non vale la complicazione. Tutto quello che non è urgente passa dal **Batch**: le risposte arrivano entro 24 ore, di solito molto prima, e un bando resta aperto settimane.

**Haiku e Sonnet sono le scelte giuste?**

- **Haiku per lo smistamento e il controllo preliminare: sì.** L'omissione di 2 annunci su 45 non è un difetto del modello ma del modo di usarlo. Rimedi: controllare che tornino tutti gli identificativi e rimandare i mancanti; lotti da 20-25 invece di 45; chiedere la risposta in formato vincolato (l'API può imporre lo schema JSON). Con Sonnet 5 a 2 $/10 $, passare anche lo smistamento a Sonnet costerebbe circa 1 $ in più sull'arretrato. Se le correzioni di Matteo mostrassero che Haiku sbaglia molto sui casi dubbi, il cambio non è un problema di soldi.
- **Sonnet per le schede: sì.** Le 4 schede con bando completo sono di buona qualità: fonti citate con l'articolo, differenze tra ATECO 2007 e 2025 riconosciute, valore anomalo del catalogo scartato. Un modello più grande non serve: gli errori della prova vengono dai documenti mancanti, non dalla lettura.
- **Il costo che conta davvero è il tempo di Matteo.** Rivedere 1.250 schede o 500 fa molta più differenza dei 30-50 $ di IA risparmiati.

---

## 6. Giudizio finale

**La struttura regge nelle scelte di fondo.** Raccolta senza IA, annunci separati dalle schede, smistamento a regole con l'IA solo sui dubbi, scheda con le fonti citate e abbinamento con regole: sono le scelte giuste, e i costi sono più bassi del previsto. Non regge ancora in **tre punti** del modello dei dati e della catena: l'identità del bando, la ricerca della pagina ufficiale e il formato dei campi da confrontare. Sono tutti da sistemare **prima** della passata sull'arretrato, perché ogni modifica fatta dopo costa una seconda passata di Sonnet e una seconda revisione di Matteo.

### Modifiche NECESSARIE prima di collegare l'IA (in ordine di priorità)

1. **Separare annuncio e bando (molti-a-uno) con una chiave di deduplica.** `bando_id` e `ruolo` sull'annuncio; allegati legati al bando; chiave = codice ufficiale → indirizzo della pagina dell'ente ripulito → ente + edizione + titolo simile (Haiku solo per i dubbi). Senza questo l'arretrato si paga e si rivede due volte e i clienti ricevono doppioni.
2. **Passo "risoluzione della pagina ufficiale" prima degli allegati.** Regole nel registro delle fonti: incentivi.gov.it → `link_ente`; Lombardia `faiDomanda` → pagina di dettaglio con lo stesso codice; notizie → link all'ente. La plancia segnala quando non si trova.
3. **Campi di confronto a valori fissi nella scheda e nel prompt:**
   - territorio in codici, con il tipo di sede;
   - soggetti ammessi, forme giuridiche, età dell'impresa, requisiti speciali (femminile, giovanile, startup...);
   - soglie di dipendenti e fatturato, spesa minima e massima, regime d'aiuto, versione ATECO;
   - temi e tipi di agevolazione a più valori, categorie di spesa, modalità, dotazione, gestore;
   - più l'elenco facoltativo delle `linee`.
4. **Regola dei tre stati e completezza della scheda.** "Vincolo", "nessun vincolo" e "non noto" devono essere distinguibili; la scheda dichiara se ha letto il bando ufficiale, solo una sintesi o niente. L'abbinamento non tratta mai "non noto" come "compatibile".
5. **Controllo preliminare con Haiku prima di Sonnet** (per imprese? edizione attuale? aperto? c'è il bando?). Nell'arretrato niente Sonnet per i bandi chiusi, gli archivi e i topic UE di ricerca.
6. **Allegati ordinati:** il bando per primo, poi FAQ e decreto più recente; modulistica esclusa dal testo per Sonnet; troncare dal fondo; scansioni segnalate.
7. **Chiamate robuste:**
   - controllo che tutti gli annunci abbiano risposta, con rinvio dei mancanti;
   - lotti da 20-25;
   - risposta in formato JSON vincolato;
   - verifica automatica di valori, date e importi;
   - uso del Batch;
   - tetto di spesa.
8. **Lo stato calcolato dal sistema** dalle date e dagli eventi, non scritto dall'IA.

### Modifiche RIMANDABILI

- Storico completo delle versioni del bando, con il confronto campo per campo. Per ora basta salvare la versione precedente a ogni aggiornamento; il resto serve prima delle email (Fase 5).
- Tabella di conversione ATECO 2007→2025 e macro-settori a parole ("filiera turistica") collegati alle sezioni ATECO (Fase 4).
- Lettura delle scansioni (OCR o invio del PDF come immagine a Claude): oggi riguarda pochi allegati, quasi tutti moduli.
- Usare i dati di incentivi.gov.it come scheda "precompilata" gratuita e come controllo incrociato dei campi di Sonnet.
- Taratura del flusso giornaliero e del tetto di spesa sui dati reali di 3-4 settimane.
- Memoria temporanea (cache) delle istruzioni: risparmio trascurabile.
- Richiesta delle anagrafiche: aggiungere al punto 4 "libero professionista sì/no", "ULA" e le categorie di investimento previste, allineate a quelle della scheda.
