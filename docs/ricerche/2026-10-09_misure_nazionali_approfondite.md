# Schede delle misure nazionali approfondite sul modello della Nuova Sabatini (09/10/2026)

Richiesta di Matteo (PIANO_AZIONE punto 8, dopo l'ok alla scheda Sabatini). Ogni scheda di `app/misure/misure.yaml` ha ora le tabelle (`tabella_intensita`) sul beneficio e sulle distinzioni per dimensione e categoria, la formula del beneficio e gli esempi ricalcolati. Lavoro di 5 agenti in sessione, verificato sulle fonti ufficiali; sotto, per ogni misura, cosa è cambiato, le fonti e cosa resta da verificare.

---

## conto_termico_3

### conto_termico_3: note della revisione (09/10/2026)

## Aggiunto
- `tabella_intensita` con 3 tabelle: (1) tetto del Titolo V per dimensione, zona e tipo di intervento, con importi su 100.000 euro; (2) algoritmo, costi massimi unitari, incentivo massimo e rate per ogni intervento II.A-II.H e III.A-III.G; (3) distinzioni per dimensione, zona (a/c, zone climatiche), agricole, professionisti, edifici residenziali, locali in affitto.
- Formula per le imprese in `intensita`: il GSE paga il minimo tra algoritmo dell'Allegato 2 (con Cmax e Imax) e la percentuale del Titolo V; algoritmi di pompe di calore, biomassa, solare termico con coefficienti; esempio di calcolo completo.
- Definizione di multi-intervento (solo 2+ interventi del Titolo II, o II.D/G/H); professionisti = impresa (art. 2 lett. s); niente ibridi a gas; nuova installazione solo per la biomassa delle aziende agricole; grandi imprese senza rimborso di diagnosi/APE; maggiorazione +10% componenti UE; elenco delle zone 107.3.a.

## Corretto (prima / dopo)
- **Calcolo per le imprese.** Prima: incentivo = percentuale del Titolo V x spesa (es. "pompa di calore al 65%", "LED al 50%"). Dopo: minimo tra algoritmo e percentuale (webinar GSE 3/2/2026: "Per imprese e ETS economici l'algoritmo è cappato in funzione dell'intensità massima del Titolo V", esempio impresa con min tra algoritmo e 45%). Conseguenza: LED, building automation, schermature al massimo 40% per chiunque; pompe di calore secondo l'energia prodotta (circa 520 euro/kW in zona E con SCOP 4).
- **Sintesi/beneficio:** prima "copre dal 25% al 65%"; dopo spiega che 25-65% è il tetto e nei casi tipici si incassa il 30-55%.
- **Esempi rifatti con l'algoritmo:** hotel 117.000 -> circa 74.000 euro; artigiano 39.500 -> 37.500 (il cappotto con pompa di calore non è multi-intervento: 45%, non 50%); agricola "fino a 78.000" -> 42.500-63.750 (formula biomassa); negozio 10.800 -> circa 8.350 (LED oltre il costo massimo di 35 euro/m2, intervento singolo con requisito del 10%, non 20%); ufficio 15.200 -> circa 13.200; manifattura con risparmio del 40%: LED restano al 40% (prima 55%); logistica invariata (35%) con nota della rata unica per pratica.
- Rate: aggiunti biomassa fino a 35 kW, solare fino a 50 m2 e scaldacqua tra i casi a 2 anni.
- Cumulo: aggiunto che un bando può coprire la differenza quando l'algoritmo resta sotto il tetto.

## Fonti
- Regole Applicative CT 3.0 (PDF letto per intero, par. 3.4, 4.2, 4.2.1, 4.3, 8, cap. 9 tabelle 15-39): https://www.gse.it/documenti_site/Documenti%20GSE/Servizi%20per%20te/BIOMETANO/Regole%20e%20procedure/Regole_Applicative_CT_3_0.pdf
- Webinar GSE 3/2/2026 "Focus Titolo III" (slide 48-59, regola del minimo e caso studio impresa): https://www.gse.it/media_site/media-gallery_site/Documents/CT%203%20-%203%20febbraio%202026%20webinar%20Focus%20Titolo%20III%20R%20Visone%20M%20Rosati.pdf
- GSE, percentuali ed erogazione: https://www.gse.it/servizi-per-te/efficienza-energetica/conto-termico-3-0/percentuali-ed-erogazione-degli-incentivi
- Carta aiuti a finalità regionale 2022-2027 (zone a): https://politichecoesione.governo.it/it/politica-di-coesione/la-programmazione-2021-2027/risorse-2021-2027/aiuti-a-finalita-regionale-2022-2027/

## Da verificare
- Per II.D, II.G, II.H (nota 6 delle Regole: "non deve superare il 30%") se si sommino le maggiorazioni per dimensione/zona.
- Elenco dei comuni in zona 107.3.c (Abruzzo e aree del Centro-Nord): non riportato, va controllato comune per comune.
- Gli esempi sulle pompe di calore usano ipotesi (SCOP 4, efficienza 150% contro minimo 110%, kp 1,36): il valore vero dipende dalla scheda prodotto; ηs minimo 110% ricavato dal caso studio GSE (125% per le applicazioni a bassa temperatura).
- Resa del solare termico (450 kWh/m2) ipotetica: va letta sul certificato Solar Keymark del modello.
- Stato dei contatori GSE per le imprese a ottobre 2026: non trovata una notizia ufficiale recente.

---

## iperammortamento_2026

### iperammortamento_2026 — note (09/10/2026)

## Aggiunto
- `tabella_intensita` con 4 tabelle: scaglioni (180/100/50%) con risparmio IRES 24% e IRPEF 33%/43%; esempi su 100.000, 1 milione, 2,5, 5, 10 e 20 milioni (5 milioni = 7.000.000 di maggiorazione, 1.680.000 euro di IRES, 33,6%; diviso su due anni 2.160.000); distinzioni per tipo di bene (4 gruppi dell'allegato IV, allegato V software, fotovoltaico con i costi massimi per kWp, altre rinnovabili, accumuli con il coefficiente alfa, calore di processo, esclusi); distinzioni per forma e dimensione (srl, ditte/snc IRPEF, forfettari, professionisti, agricole, concordato preventivo biennale, perdite, Sud/ZES).
- Formula e calcolo dei tempi in `intensita` (coefficienti di ammortamento, software in 2 anni, fotovoltaico al 9%, leasing).
- Gli scaglioni valgono per gli investimenti completati **in ciascun anno** (art. 4 c. 2 DM 7/5/2026, testo letto dal PDF MIMIT): ripartono ogni anno.
- Definizione di struttura produttiva, regole dell'art. 8 DM (dove puo' stare l'impianto, 105% calcolato sui consumi dell'anno precedente, solo calore di processo).
- Concordato preventivo biennale: la maggiorazione riduce anche il reddito concordato (art. 7 DL 38/2026, conv. L. 88/2026; nota Agenzia Entrate sulle istruzioni CPB del 23/06/2026).
- DD 20/07/2026 (comunicazioni di conferma) nella norma; perizia senza soglie (art. 6 DM); comma 434 per gli acconti; esclusione dei beni gia' agevolati con art. 1 c. 446 L. 207/2024.

## Corretto (prima / dopo)
- `beneficio_stimato.percentuale_max`: 43.2 -> 77.4 (180% x IRPEF 43% per ditte e soci di snc; 43,2% resta il valore per le societa'). Coerente con la maxi-deduzione, che gia' usa il massimo IRPEF.
- Sintesi: "per una societa' vale circa il 43% della spesa" -> precisato che e' il 43,2% solo fino a 2,5 milioni l'anno e che con IRPEF 43% arriva a 77,4%.
- Esempio manifattura: fotovoltaico 400 kW a 500.000 euro superava il costo massimo ammesso (lettera b, 200-600 kW: 1.020 euro/kWp = 408.000) -> portato a 400.000; totale 1.600.000, IRES 691.200 (prima 734.400).
- Esempio ristorazione: 50 kW a 60.000 superava il massimo (1.120 euro/kWp = 56.000) -> 56.000, IRES circa 24.200 (prima 25.900); aggiunto che la pompa di calore conta solo per il calore di processo.
- Esempio artigiano e negozio: aggiunte le cifre IRPEF.
- `fonte_verificata_il`: 2026-10-07 -> 2026-10-09.

## Fonti
- MIMIT, pagina misura: https://www.mimit.gov.it/it/incentivi/nuovo-piano-transizione-5-0-iperammortamento
- DM 7/5/2026 (testo integrale con allegato 1): https://www.mimit.gov.it/images/stories/normativa/allegati/Decreto_-_Iperammortamento_2026_-nf.pdf
- DD 20/07/2026: https://www.mimit.gov.it/it/normativa/decreti-direttoriali/decreto-direttoriale-20-luglio-2026-iperammortamento-termini-e-modelli-di-comunicazione
- Agenzia Entrate, aggiornamento istruzioni CPB (art. 7 DL 38/2026): https://www.agenziaentrate.gov.it/portale/documents/d/guest/motivi-aggiornamento-istruzioni-cpb-isa-2026
- Agenzia Entrate, aliquote IRPEF 2026: https://www.agenziaentrate.gov.it/portale/imposta-sul-reddito-delle-persone-fisiche-irpef-/aliquote-e-calcolo-dell-irpef
- Nuovo TUIR D.Lgs. 117/2026 (art. 364, allegati E/F): GU n. 152 del 3/7/2026 (riscontro tramite fonti secondarie: edotto.com, ance.it)
- Fonti secondarie usate solo come riscontro: iperammortamenti.it (allegato IV, comma 431), ecnews.it (nettizzazione), reteagevolazioni.it (comma 434).

## Da verificare
- Testo ufficiale degli allegati IV e V (gruppi e voci riportati da fonte secondaria, coerenti con la scheda precedente).
- Comma 434 sugli acconti e testo esatto del comma 431 sulla nettizzazione: letti solo in fonti secondarie (Normattiva non leggibile).
- Software SaaS: nessun chiarimento ufficiale.
- Sabatini da sottrarre o no dalla base (prudenza: sottrarre).
- Natura di misura generale (non aiuto di Stato): solo commentatori.
- Polizza catastrofale non richiesta: solo commentatori.
- Coefficienti di ammortamento indicati come tipici (10-15,5% macchinari, 9% fotovoltaico): dipendono dal settore.

---

## credito_rs_2026

### credito_rs_2026 - note (09/10/2026)

## Aggiunto
- `tabella_intensita` con 3 tabelle: aliquote per attivita' nel 2026 (R&S 10%, R&S al 150%, maggiorazione Sud finita, innovazione e 4.0/green finite, design esaurito); voci di spesa con come contano, limiti ed esempio; distinzioni per dimensione e categoria (micro/piccola, media, grande, Sud, startup, agricole e forfettari, professionisti, imprese in procedura).
- Formula del beneficio in `intensita` (base = personale con giovani x1,5 + beni max 30% + extra muros x1,5 + privative + consulenze max 20% + materiali max 30% - contributi; credito 10% + certificazione fino a 5.000) con un esempio completo (piccola srl: 27.000 euro, 9.000 l'anno 2027-2029) e percentuali effettive (10% / 15%).
- Giovani ricercatori al 150%: requisiti completi (under 35, primo impiego, dottorato o laurea magistrale tecnico-scientifica ISCED, tempo indeterminato, impiego **esclusivo** in R&S).
- Amministratori e soci: max 50% del compenso fisso, variabili esclusi, compenso fisso pagato per intero (DM 26/5/2020 art. 6 c. 6).
- Contratti extra muros: 150% con universita', enti di ricerca, startup innovative italiane; 100% con altri.
- Professionisti non in forma d'impresa: esclusi (comma 199 parla di imprese), da verificare per STP.
- Attenzione: blocco compensazioni con ruoli scaduti oltre soglia (100.000 euro, 50.000 dal 2026).
- Esempi per profilo aggiornati con la maggiorazione al 150% (startup 29.500 con due giovani; manifattura 21.000 con contratto universitario; artigiano 6.000; logistica 12.000; agricola 7.500).

## Corretto (prima / dopo)
- `beneficio_stimato.percentuale_max`: 10 -> 15 (le spese al 150% danno il 15% del costo). Se il campo deve restare "stima prudente" anche nel massimo, rimettere 10.
- Esempi artigiano/logistica/agricola: prima contratti con universita' calcolati al 10% (4.000 / 8.000 / 5.000), dopo al 150% (6.000 / 12.000 / 7.500): la scheda stessa diceva che i contratti con universita' contano al 150%.
- `norma`: aggiunti comma 203 e 205 e la natura di misura generale (non aiuto di Stato).
- `fonte_verificata_il`: 2026-10-07 -> 2026-10-09.
- Nessun errore sostanziale trovato nel resto (aliquota 10%, tetto 5 milioni, fine 2031, maggiorazioni Sud finite nel 2025, innovazione non prorogata: confermati).

## Fonti
- MIMIT, pagina del credito R&S, innovazione e design (aliquote e tetti per anno): https://www.mimit.gov.it/it/incentivi/credito-d-imposta-r-s
- Art. 244 DL 34/2020 (maggiorazioni Sud e sisma 25/35/45%): https://www.normattiva.it/uri-res/N2Ls?urn:nir:stato:decreto.legge:2020-05-19;34~art244 ; durata fino al 2025 confermata da fonti secondarie e codici tributo 6939/6940 (https://www.brocardi.it/decreto-rilancio/titolo-viii/capo-xi/art244.html)
- L. 160/2019 comma 200 (150% giovani ed extra muros), testo riportato da: https://www.assolombarda.it/servizi/fisco/informazioni/legge-di-bilancio-2020-art-1-commi-198-209 e https://www.to.camcom.it/sites/default/files/pid/materiale-webinar/Slide_Credito_imposta_RSI.pdf
- DM 26/5/2020 art. 6 c. 6 (amministratori 50%): https://www.assolombarda.it/servizi/fisco/documenti/decreto-mise-26-5-2020-credito-dimposta-r-s-innovazione-e-design
- Circ. AdE 16/E/2024 e soglia 50.000 dal 2026: https://www.fiscoetasse.com/approfondimenti/16883-la-compensazione-vietata-per-ruoli-superiori-a-100000-euro.html , https://www.grifofinance.com/compensazione-f24-soglia-50000-euro-2026/ (secondarie)

## Da verificare
- Testo vigente del comma 200 su Normattiva (non leggibile da qui: estratto da fonti secondarie e dalla scheda precedente). In particolare: limite 30% dei beni calcolato sul personale gia' maggiorato o no; regole dei contratti infragruppo; soggetti esteri ammessi per l'extra muros.
- Legge che ha prorogato l'art. 244 fino al 2025 (non individuata con certezza; la fine nel 2025 e' confermata).
- Soglia 50.000 euro per il blocco compensazioni (L. 199/2025 comma 116): letta su fonti secondarie.
- Professionisti / societa' tra professionisti: esclusione dedotta dal comma 199.
- Patent box nel nuovo TUIR (D.Lgs. 117/2026): riferimento gia' "da verificare" nella scheda precedente.

---

## credito_zes_unica_2026

### credito_zes_unica_2026 - note (09/10/2026)

## Aggiunto
- `tabella_intensita` con 3 tabelle: intensita' per zona e dimensione (anche grandi progetti oltre 50 milioni e STEP); esempi su 200.000 euro, 1 milione e 10 milioni per piccola/media/grande in 4 gruppi di zone (teorico e con riparto 75%); distinzioni per dimensione e categoria (micro, piccola, media, grande, trasformazione agricola, produzione primaria/pesca, trasporti, energia, professionisti).
- Formula in `intensita`: credito = (costo ammesso x intensita' - altri aiuti) x riparto; grandi progetti con "importo corretto" R x (A + 0,5 x B), A = primi 55 milioni, B = 55-100 milioni (esempio 80 milioni in Campania = 27 milioni teorici).
- Grandi imprese nelle zone c (Abruzzo, Marche, Umbria): solo nuova attivita' economica; cambiamento di processo nelle zone a: costi oltre gli ammortamenti dei 3 anni prima; diversificazione: costi oltre il 200% dei beni riutilizzati; divieto di delocalizzazione 2 anni prima/dopo.
- Marche e Umbria nella ZES dal 2026 con L. 171/2025; elenco di esempio dei comuni ammessi nelle zone c.
- Requisiti formali: partita IVA attiva, ATECO e comune uguali all'Anagrafe tributaria (pena scarto), iscrizione al Registro imprese, DURC.
- Leasing: conta la consegna; costo del locatore senza manutenzione; leasing in costruendo ammesso per l'immobile (risposta AdE 32/2026). IVA solo se indetraibile.
- Risorse: 2026 2,3 miliardi; 2027 1 miliardo e 2028 750 milioni (fonte secondaria); avviso che il riparto 2027 potrebbe essere piu' basso.
- Sensibilita' al riparto: esempi anche con il 60,38% (riparto iniziale 2025).
- Noleggio unita' da diporto ammesso (codice casi particolari 1); divieto di doppio finanziamento PNRR; cumulo con la Sabatini (FAQ MIMIT 9.6).
- Blocco compensazioni con ruoli scaduti oltre soglia (circ. 16/E/2024).
- Esempi per profilo: aggiunti confronto Taranto (manifattura), Marche (artigiano), cifre per negozio e logistica.

## Corretto (prima / dopo)
- Effetto di incentivazione: prima "il progetto non deve essere partito prima del 1/1/2026"; dopo "non prima dell'entrata in vigore della misura, prorogata senza interruzioni (risposta 169/2026); i progetti pluriennali avviati dal 2024 possono comprendere acquisti 2026 (provvedimento 30/1/2026 punto 1.5)". La versione precedente era troppo restrittiva.
- Sintesi: prima "fino al 60% ... 70% a Taranto" senza le altre zone; ora tutte le intensita' per zona e dimensione con un esempio numerico.
- Grandi progetti: prima "sopra 50 milioni percentuali piu' basse"; ora regola precisa (niente maggiorazione PMI + importo corretto).
- Percentuale 2026: "non ancora pubblicata" aggiornato al 09/10/2026.
- `fonte_verificata_il`: 2026-10-07 -> 2026-10-09.
- Le intensita' gia' presenti (60/50/40, 50/40/30, Taranto 70/60/50, Sulcis 60/50/40, zone c 35/25/15) sono confermate dalla tabella delle istruzioni AdE.

## Fonti
- Pagina AdE ZES 2026: https://www.agenziaentrate.gov.it/portale/credito-d-imposta-per-investimenti-nella-zes-unica-zes-2026-/che-cos-
- Modelli e istruzioni (tabella intensita', allegato 1 comuni, formula importo corretto): https://www.agenziaentrate.gov.it/portale/credito-d-imposta-per-investimenti-nella-zes-unica-zes-2026-/modello-e-istruzioni (allegati https://www.agenziaentrate.gov.it/portale/documents/d/guest/agedc001_38382_2026_3103_all1 ... all4)
- Provvedimento 30/1/2026 n. 3882: https://www.agenziaentrate.gov.it/portale/-/provvedimento-del-30-gennaio-2026-2
- Risposta AdE 169/2026 (incentivazione, leasing febbraio 2026): https://www.agenziaentrate.gov.it/portale/documents/20143/10289089/Risposta+n.+169_2026.pdf/ad60b5ea-d951-6548-b68a-e38655baf4a5
- Risposta AdE 32/2026 (leasing in costruendo): https://www.agenziaentrate.gov.it/portale/documents/20143/9680917/Risposta+n.+32_2026/a4dd84b9-690e-20d7-7d2f-bb581a241766
- Contributo aggiuntivo 14,6189% (riparto 2025 al 75%): https://www.agenziaentrate.gov.it/portale/documents/20143/9730656/ZES+Unica+credito+aggiuntivo+istr+9.2.2026.pdf/4d40ec02-6f80-5ec2-7716-8e280626b535
- Risorse 2027-2028 (secondaria): https://www.finanzaefisco.com/credito-dimposta-zes-unica-2026-2028-nuove-comunicazioni-scadenze-e-utilizzo-del-beneficio/
- Soglia ruoli 50.000 dal 2026 (secondaria): https://www.grifofinance.com/compensazione-f24-soglia-50000-euro-2026/

## Da verificare
- Risorse 2027 (1 miliardo) e 2028 (750 milioni) sul testo del comma 438 (Normattiva non leggibile da qui).
- Percentuale di riparto 2026: uscira' a fine gennaio 2027.
- Tassazione IRES/IRAP del credito ZES: nessun chiarimento AdE specifico (resta il precedente della circ. 34/E/2016).
- Intensita' maggiorata STEP sui grandi progetti.
- Professionisti non iscritti al Registro delle imprese (il modello chiede l'iscrizione).
- Software di controllo fatturato separatamente dalla macchina.
- Soglia 50.000 euro per il blocco compensazioni (L. 199/2025 comma 116).

---

## ecobonus_imprese_2026

### ecobonus_imprese_2026 — note (09/10/2026)

## Aggiunto
- `tabella_intensita` con due tabelle: (1) tetti per tipo di intervento con spesa massima utile al 36% (2026) e al 30% (2027) ed esempi di detrazione e di rata annua; (2) distinzioni per tipo di impresa (srl in utile o in perdita, società di persone, ditta individuale/professionista, forfettario, agricola, grande impresa) e di immobile (strumentale, merce, patrimonio abitativo, in affitto/leasing, abitazione principale).
- In `intensita`: formula (aliquota x spesa netta, fino al tetto di detrazione; rata = /10; limite dell'imposta lorda), esempio completo 2026 contro 2027, spesa massima utile = tetto / aliquota, regola di competenza (fine lavori o SAL definitivi) contro cassa, valore attuale delle 10 rate (calcolo nostro al 3%, dichiarato come tale), aliquote fino al 2024 per confronto, ipotesi 65% per il 2027 (stampa, nessun testo approvato).
- In `a_chi_si_rivolge`: nessun limite di dimensione; come si usa la detrazione per società di capitali, società di persone (passa ai soci), ditte/professionisti (tetto art. 16-ter TUIR sopra 75.000 euro), forfettari.
- Chiarito che i limiti del DM 6/8/2020 sono di DETRAZIONE, non di spesa; nota sul tetto per unità catastale nei capannoni.

## Corretto (prima / dopo)
- Prima: "Per le imprese conta la data di fine lavori" (per tutte). Dopo: vale per le imprese in contabilità ordinaria; semplificata/professionisti cassa (per l'ecobonus in semplificata: da verificare).
- `fonte_verificata_il` 2026-10-07 -> 2026-10-09. Nessun numero della scheda precedente risultato sbagliato.

## Fonti
- https://www.agenziaentrate.gov.it/portale/schede/agevolazioni/detrazione-riqualificazione-energetica-55-2016/cosa-riqualificazione-55-2016 (aliquote 2025-2026 36/50, 2027 30/36, 10 rate, immobili strumentali/merce/patrimonio)
- Risoluzione AdE 34/E/2020: https://www.agenziaentrate.gov.it/portale/documents/20143/2522862/Risoluzione+n.+34+del+25+giugno+2020.pdf (sintesi ANIT: https://www.anit.it/risoluzione-34e-ecobonus-e-sismabonus-anche-per-imprese-e-societa-di-costruzione-e-locazione/)
- AdE, limiti art. 16-ter TUIR: https://www.agenziaentrate.gov.it/portale/la-misura-della-detrazione-limiti-detraibilita
- Risposta AdE 46/2018 (pagamenti imprese, competenza/cassa) tramite ANCE: https://ance.it/2018/10/eco-e-sismabonus-i-chiarimenti-dell-ade-sulla-modalit-di-pagamento-degli-interventi-agevolati/
- L. 199/2025 proroga 2026 (conferme secondarie): https://www.legislazionetecnica.it/12144677/news-edilizia-appalti-professioni-tecniche-sicurezza-ambiente/bonus-fiscali-edilizi-tutte-le-novit-2026
- Ipotesi 2027: https://www.edilportale.com/news/2026/09/normativa/ecobonus-65-dal-2027-ipotesi-del-governo_111828_15.html
- Tetti in detrazione e spesa massima al 36% (conferma secondaria): https://fiscomania.com/bonus-infissi/

## Da verificare
- Ecobonus per imprese in contabilità semplificata: cassa o competenza (la risposta 46/2018 riguarda il sismabonus).
- Applicazione del tetto art. 16-ter TUIR alle spese su immobili dell'impresa (ditte individuali, soci di società di persone).
- Passaggio delle rate residue in caso di vendita di immobile merce a un acquirente società.
- Manovra 2027: se cambia le aliquote 2027 (ipotesi 65%), aggiornare.
- Deducibilità piena del costo insieme alla detrazione (già segnalato: manca prassi AdE specifica).

---

## sismabonus_imprese_2026

### sismabonus_imprese_2026 — note (09/10/2026)

## Aggiunto
- `tabella_intensita` con due tabelle: (1) aliquota e detrazione massima per anno di spesa (2024 per confronto, 2025, 2026, 2027) con esempi su 50.000, 96.000 e 400.000 euro e rata annua; (2) distinzioni per tipo di impresa (ordinaria, semplificata, società di persone, ditta/professionista, in perdita/forfettario/agricola, grande impresa) e di immobile (strumentale, merce, patrimonio abitativo, acquisto di unità ricostruita, abitazione principale, zona 4).
- In `intensita`: formula con il tetto che conta le spese degli anni prima, esempio srl 250.000 euro (2026 contro 2027), competenza/cassa e bonifico (risposta AdE 46/2018), aliquote maggiorate fino al 2024 sparite, valore attuale (calcolo nostro al 3%).
- Sismabonus acquisti: ora spiegato per le imprese (acquirente IRPEF o IRES, unità residenziali e non, vendita entro 30 mesi dalla fine lavori) — prima era "regole per acquirenti imprese da verificare".
- Tetto per unità catastale: un capannone = un tetto; spezzare i lavori su più anni non raddoppia il tetto.
- Nella scheda: nessun limite di dimensione; uso della detrazione per società di persone, ditte, forfettari; tetto art. 16-ter TUIR.

## Corretto (prima / dopo)
- Prima: nessuna regola sui pagamenti. Dopo: imprese in ordinaria senza obbligo di bonifico; semplificata, professionisti e privati con bonifico parlante e cassa (risposta 46/2018).
- Prima: "anno della spesa: per le imprese in ordinaria di norma competenza". Dopo: ordinaria competenza, semplificata cassa (fonte citata).
- Aggiunto in `norma` il riferimento alla risoluzione 34/E/2020 (vale per il sismabonus oltre che per l'ecobonus) e alla risposta 46/2018.
- `fonte_verificata_il` 2026-10-07 -> 2026-10-09.

## Fonti
- https://www.agenziaentrate.gov.it/portale/aree-tematiche/casa/agevolazioni/sisma-bonus (zone 1-3, 96.000 per unità per anno, 10 quote, IRPEF/IRES; la pagina non è aggiornata alle aliquote 2025-2027)
- Risoluzione AdE 34/E/2020 (ecobonus e sismabonus su immobili strumentali, merce, patrimonio): https://www.anit.it/risoluzione-34e-ecobonus-e-sismabonus-anche-per-imprese-e-societa-di-costruzione-e-locazione/
- Risposta AdE 46/2018 (bonifico e competenza/cassa per le imprese): https://ance.it/2018/10/eco-e-sismabonus-i-chiarimenti-dell-ade-sulla-modalit-di-pagamento-degli-interventi-agevolati/
- Risposta AdE 556/2021 (sismabonus acquisti: unità residenziali e non residenziali): https://www.agenziaentrate.gov.it/portale/documents/20143/0/Risposta_556_25.08.2021.pdf/bf6b0932-8c3a-8e61-5305-24ab258f0d75
- Proroga 2026 al 36/50 (art. 1 c. 22 L. 199/2025): https://www.idealista.it/news/finanza/fisco/2026/01/15/311617-sismabonus-2026-le-detrazioni-prorogate-dalla-legge-di-bilancio
- Sismabonus acquisti 30 mesi: https://www.mansarda.it/leggi-e-regolamenti/sismabonus-2026-novita-percentuali-e-limitazioni/ (fonte secondaria)
- AdE, limiti art. 16-ter TUIR: https://www.agenziaentrate.gov.it/portale/la-misura-della-detrazione-limiti-detraibilita

## Da verificare
- Termine di 30 mesi per la vendita nel sismabonus acquisti: confermato solo da fonti secondarie (la risposta 556/2021 cita ancora 18 mesi); verificare il testo vigente del comma 1-septies.
- Riferimento puntuale di prassi sulla cumulabilità con contributi a fondo perduto (rimasto "da verificare").
- Tetto art. 16-ter TUIR sulle spese per immobili dell'impresa (ditte, soci).
- Monitoraggio strutturale continuo nel sismabonus ordinario.
- Aliquote dal 2027 nel nuovo TUIR (art. 371 D.Lgs. 117/2026): "secondo le prime analisi invariate", non verificato sul testo.

---

## art_bonus

### art_bonus — note (09/10/2026)

## Aggiunto
- Tabella "Quanto si recupera: credito per livello di ricavi" (200.000 euro - 50 milioni): credito massimo 5 per mille, donazione utile massima (credito/0,65), quota annua F24, esempio.
- Tabella "Cosa cambia secondo chi dona": societa' di capitali, societa' di persone/ditte individuali, forfettari d'impresa, professionisti, persone fisiche, enti non commerciali/ETS, agricole a reddito agrario. Detto esplicitamente che dimensione, settore e zona (Sud/ZES) non cambiano nulla.
- Formula in `intensita`: credito = 65% nel limite; donazione utile massima = ricavi x 0,005 / 0,65 (circa 0,77% dei ricavi); tre quote, riporto senza limiti; esempio srl 3 milioni.
- Donazioni a concessionari/affidatari di beni culturali pubblici (solo manutenzione, protezione, restauro).
- Regola degli enti non commerciali che donano nell'attivita' commerciale (limite delle imprese).
- Circ. AdE 34/E/2023 in `norma` (forfettari ammessi; nessun limite generale di compensazione).
- Esempi aggiornati con quote annue e donazione utile massima; professionista/socio che dona in proprio (limite 15% del reddito).

## Corretto
- Nulla di sbagliato nei numeri. Precisato: prima "Il limite per le imprese 5 per mille dei ricavi annui" -> ora "ricavi artt. 85 e 57 TUIR dell'anno della donazione" e limite riferito al credito (confermato dall'esempio del portale 20 mln -> 100.000 / 153.846).
- `fonte_verificata_il` 2026-10-07 -> 2026-10-09.

## Fonti
- https://artbonus.gov.it/beneficio-fiscale.html (65%, limiti, tre quote, F24 6842, persone fisiche primo terzo nell'anno, riporto, esclusione IRES/IRAP)
- https://artbonus.gov.it/qualifica-soggetto-che-effettua-erogazioni-liberali-limiti-massimi-spettanza-credito-imposta-modalita-fruizione-differente.html (limiti per tipo di donatore, enti non commerciali con attivita' commerciale)
- https://artbonus.gov.it/erogazione-liberale-soggetto-concessionario-affidatario-bene-culturale-pubblico-beneficio-fiscale-art-bonus.html (concessionari/affidatari)
- https://artbonus.gov.it/Circolare_n_34_del_28-12-2023_Chiarimenti.pdf (circ. AdE 34/E/2023, forfettari) e sintesi https://www.edotto.com/articolo/art-bonus-nuove-precisazioni
- Ricavi artt. 85 e 57 TUIR: https://www.fiscoetasse.com/approfondimenti/14041-lart-bonus-credito-di-imposta-per-larte.html (fonte secondaria)
- Nessuna modifica all'Art Bonus trovata nella Legge di bilancio 2026.

## Da verificare
- Forfettari: limite (5 per mille dei ricavi per i forfettari d'impresa, 15% del reddito per i professionisti) e quadro di dichiarazione: indicati solo da fonti secondarie, non letti nel testo della circ. 34/E.
- Imprese agricole a reddito agrario: limite applicabile.

---

## incentivi_assunzione_2026

### incentivi_assunzione_2026 — note (09/10/2026)

Letto il testo integrale delle circolari INPS 55, 56 e 57 del 14/05/2026 (PDF ufficiali estratti in
/tmp/claude-1000/mis_out/inc_circ55.txt, inc_circ56.txt, inc_circ57.txt).

## Aggiunto
- Tabella "Le tre misure a confronto": per Giovani (molto svantaggiati / svantaggiati), Donne (molto svantaggiate / svantaggiate), ZES: chi assumere, datori ammessi, tetto mensile, durata, massimo per lavoratore, fondi 2026.
- Tabella "Quanto si risparmia su una retribuzione tipica": 20.000, 24.000, 30.000, 36.000 euro lordi e part-time 50%, per ogni tetto (500, 650, 800, ZES), 12 e 24 mesi.
- Tabella "Cosa cambia per zona, dimensione e tipo di datore": Centro-Nord, ZES sopra/sotto 10 dipendenti, dimensioni, studi/ETS, agricoltura, edilizia, somministrazione, esclusi.
- Formula in `intensita`: esonero mensile = min(contributi del mese, tetto x % part-time); risparmio = esonero x mesi; tetti giornalieri 16,12 / 20,96 / 25,80; contributi NON esonerati (INAIL, Fondo Tesoreria TFR, 0,30% fondi interprofessionali, fondi di solidarieta', contributi di solidarieta').
- Elenco completo delle condizioni di svantaggio (DM 17/10/2017, Reg. 651/2014 art. 2 n. 4 e 99) per Giovani e Donne.
- Differenza chiave: maggiorazione Giovani legata al luogo di lavoro (trasferimento fuori ZES -> 500 dal mese dopo); maggiorazione Donne legata alla residenza della lavoratrice; Bonus ZES legato a luogo di lavoro + max 10 dipendenti contati nel mese di assunzione al netto degli assunti col bonus.
- Ripartizione dei fondi Bonus Donne per categoria di regione (141,5 mln totali: 50,83% / 7,04% / 42,13%).
- Somministrazione ammessa (beneficio all'utilizzatore), lavoro occasionale escluso, sospensione solo per maternita', INPS accoglie solo con copertura per tutti i mesi, importo autorizzato = massimo, registrazione nel Registro aiuti di Stato.
- Cumulabilita': anche con sgravi a carico del lavoratore (es. madri); limite GBER art. 32 (50% dei costi salariali di 12/24 mesi).

## Corretto (prima -> dopo)
- Studi professionali: prima "per gli studi professionali conviene una conferma con il consulente del lavoro" -> dopo: ammessi, le circolari INPS (par. 2) valgono per tutti i datori privati "a prescindere" dalla natura di imprenditore (anche negli esempi ufficio_servizi).
- Dirigenti: prima esclusi in generale -> dopo esclusi solo nel Bonus ZES (le circolari 55 e 57 non li escludono).
- Lavoro intermittente: prima "secondo le istruzioni INPS" in a_chi_si_rivolge -> ora anche in settori_esclusi e negli esempi (escluso in tutti e tre).
- Bonus Donne 12 mesi: aggiunto che basta anche "senza impiego regolare da 6 mesi" (lett. a) e l'elenco completo delle condizioni.
- SIISL: prima "tempi e modalita' da verificare" -> dopo: dovuta dal 1/4/2026 ma non obbligatoria fino al decreto attuativo (messaggio INPS 1153 del 31/03/2026, citato dalla circ. 56).
- `beneficio_stimato`: 13-23% -> 12-22% (con contributi al 30% e TFR il massimo teorico e' circa 21-22% del costo aziendale; con 36.000 euro lordi e tetto 500 circa 12%).
- Esempio manifattura: specificato lo stipendio (28.000 euro) che serve perche' il tetto 650 sia pieno.
- Termine domande: confermato che il 30/09/2026 (messaggio INPS 2451 del 23/07/2026) riguarda i bonus del DL 60/2024, non quelli 2026; data di controllo aggiornata al 09/10.

## Fonti
- Circolare INPS 55/2026 (Giovani): https://www.inps.it/content/dam/inps-site/it/scorporati/circolari-e-messaggi/2026/05/Circolare_15258/Allegati/16770_Circolare-numero-55-del-14-05-2026.pdf
- Circolare INPS 56/2026 (ZES): https://www.inps.it/content/dam/inps-site/it/scorporati/circolari-e-messaggi/2026/05/Circolare_15259/Allegati/16771_Circolare-numero-56-del-14-05-2026.pdf
- Circolare INPS 57/2026 (Donne): https://www.inps.it/content/dam/inps-site/it/scorporati/circolari-e-messaggi/2026/05/Circolare_15260/Allegati/16772_Circolare-numero-57-del-14-05-2026.pdf
- Termine 30/09 decreto Coesione: https://www.mysolution.it/lavoro/approfondimenti/prima-lettura/2026/07/decreto-coesione-termine-al-30-settembre-per-le-domande-di-esonero/ (fonte secondaria che cita il messaggio INPS 2451/2026)

## Da verificare
- Aliquota contributiva esonerabile reale (gli esempi usano un 30% indicativo): dipende da CCNL, settore, dimensione; va presa dal cedolino.
- Termine finale per le domande relative alle assunzioni 2026: non trovato al 09/10/2026.
- Stato dei fondi 2026 (in particolare ZES e Donne, circa 26 milioni ciascuno): nessuna comunicazione INPS di esaurimento trovata.
- Testo della legge di conversione 112/2026 non riletto in questa sessione (la scheda lo dava gia' per verificato su Normattiva il 07/10).

---

## fondo_garanzia_pmi

### fondo_garanzia_pmi: note della revisione (09/10/2026)

## Aggiunto
- `tabella_intensita` con 3 tabelle: (1) copertura per tipo di operazione e fasce di rating (investimenti, Sabatini, liquidità, importo ridotto, microcredito, startup/PMI innovative, ETS, capitale di rischio, mid-cap) con importo garantito su 100.000 euro; (2) commissioni per dimensione e categorie esenti, professionisti, agricoltura, agroalimentare, ETS; (3) valore dell'aiuto (ESL) stimato con la formula ufficiale.
- Formula in `intensita`: garantito = prestito x copertura; commissione = garantito x aliquota; formula dell'ESL (Disposizioni operative Parte VII: 0,95%/1,28% + 0,60% + 0,32%) con esempi.
- Riassicurazione tramite confidi (prodotto delle due percentuali, max 80% x 80%, entro la copertura della riga); sezioni speciali regionali.
- Rating: fasce 1-4 con la stessa copertura dal 2025 (nel 2024 liquidità 55% fasce 1-2, 60% fasce 3-4); per importo ridotto e microcredito il rating serve solo alla gestione del rischio.
- Nuove imprese senza due bilanci: solo investimenti, mezzi propri versati >= 25%, business plan triennale (DO Parte IX).
- Sezione speciale ETS (circ. MCC 6/2026, 21/9/2026): ETS solo RUNTS ed enti religiosi, 80% gratuita, 10 milioni.
- Esclusioni: operazioni per l'export, operazioni senza scadenza certa; erogazione di almeno il 25% entro 6 mesi dalla delibera; commissione entro 3 mesi.
- ESL negli esempi (artigiano, hotel, manifattura) e interazione con la Sabatini delle medie imprese.

## Corretto (prima / dopo)
- **Agricoltura.** Prima: "Le imprese agricole sono ammesse (con regole apposite...)" ed esempio agricolo con garanzia diretta 80%. Dopo: la sezione A ATECO (produzione primaria, pesca) è esclusa dalla garanzia diretta; solo riassicurazione tramite confidi del settore agricolo e solo in de minimis; ammessi con garanzia diretta solo servizi di supporto all'agricoltura, caccia, silvicoltura; la trasformazione (sezione C) è normale. Interesse del profilo agricola da "medio" a "basso" (DO Parte IV, tabelle 1 e 3).
- **Toscana.** Prima non citata. Dopo: garanzia diretta non ammessa per sedi in Toscana (DO Parte IV B.4), solo tramite confidi/Fidi Toscana con sezione speciale fino al 90%.
- **Nuova Sabatini senza commissione.** Prima: "nessuna commissione per Nuova Sabatini". Dopo: l'esenzione non risulta nelle Disposizioni operative (par. 3-4 Parte V esentano startup innovative, incubatori, PMI innovative, microcredito, anticipi PA, PMI dell'indotto ex Ilva; par. 4 Mezzogiorno, femminili, rete, sociali, autotrasporto): commissione secondo la dimensione.
- Esenzione Mezzogiorno e simili precisata: vale per le operazioni ordinarie, non per consolidamento sulla stessa banca, capitale di rischio, minibond.
- Settori esclusi aggiornati alle sezioni ATECO 2007 delle DO (K, O, T, U, A con eccezioni).
- Esempi: hotel commissione 3.200 confermata (+ femminile esente); logistica 80% = 960.000 garantiti; consulenza liquidità 50.000 garantiti e 250 euro di commissione se piccola.

## Fonti
- Circolare MCC 21/2023 (tabelle coperture per fascia, mid-cap, micro gratis): https://www.fondidigaranzia.it/wp-content/uploads/2023/12/Circolare-N.-21-2023_Applicazione-misure-DL-145_23.pdf
- Circolare MCC 20/2024 (liquidità 50%, importo ridotto 100.000 con confidi, mid-cap 499): https://www.fondidigaranzia.it/wp-content/uploads/2024/12/Circolare-N.20.2024-Applicazione-misure-LdB.pdf
- Circolare MCC 1/2026 (proroga al 31/12/2026, art. 14 c. 1 DL 200/2025): https://www.fondidigaranzia.it/wp-content/uploads/2026/04/Circ-1-2026-Proroga-misure-fondo-PMI.pdf
- Circolare MCC 2/2026 (premio aggiuntivo banche dal 20/2/2026): https://www.fondidigaranzia.it/wp-content/uploads/2026/04/Circolare-n.2-2026-Premio-aggiuntivo.pdf
- Circolare MCC 6/2026 (sezione speciale ETS): https://www.fondidigaranzia.it/wp-content/uploads/2026/09/20260921_circolare-n.-6-2026_sezione-ETS.pdf
- Disposizioni operative (PDF sul sito MIMIT; Parte IV soggetti e settori, Parte V commissioni tab. 5, Parte VII ESL, Parte IX nuove imprese): https://www.mimit.gov.it/images/stories/normativa/disposizioni_fondo_di_garanzia.pdf
- Fondo di garanzia, news proroga 2026 e riforma 2024/2025: https://www.fondidigaranzia.it/prorogate-per-il-2026-le-modalita-di-funzionamento-del-fondo-di-garanzia/ , https://www.fondidigaranzia.it/dal-1-gennaio-al-via-la-riforma-del-fondo-di-garanzia-per-le-pmi/ , https://fondidigaranzia.it/confermata-la-riforma-del-fondo-di-garanzia-per-il-2025-con-la-copertura-al-50-per-la-liquidita/
- MIMIT, pagina del Fondo (aggiornata il 21/09/2026): https://www.mimit.gov.it/it/incentivi/fondo-di-garanzia-per-le-pmi

## Da verificare
- Versione delle Disposizioni operative lette (PDF MIMIT senza data in copertina): parametri ESL, esclusione agricola, esclusione Toscana e tabella commissioni potrebbero essere stati aggiornati.
- Mid-cap: se l'autorizzazione UE è arrivata e l'operatività è attiva.
- Come i limiti di 2,5 e 1,5 milioni delle DO convivono con i 5 milioni per impresa del DL 145/2023.
- PMI innovative: 80% anche per la liquidità o solo per gli investimenti (nella tabella della circ. 21/2023 stanno nella colonna degli investimenti).
- Fascia 5: se è esclusa anche per importo ridotto, microcredito e startup (nella tabella 21/2023 la riga 5 riporta "n.a." solo per tre colonne).
- Esenzione dalla commissione per la Nuova Sabatini: non trovata nelle DO; chiedere conferma alla banca.
- Valori ESL: stime nostre (tasso 3,5%, rate annuali costanti); il dato vero è nella delibera.
- Tempi dell'istruttoria; regola "in de minimis programma avviato da non più di 6 mesi" (dalla scheda precedente, non riletta oggi).

---

## maxi_deduzione_assunzioni

### maxi_deduzione_assunzioni — note (09/10/2026)

## Aggiunto
- `tabella_intensita` con 2 tabelle: maggiorazione per categoria di lavoratore (120%/130%) con esempio su 35.000 euro e risparmio IRES 24%, IRPEF 33% e 43%; valore per forma giuridica e aliquota (srl, ditte/snc/professionisti al 23/33/43%, forfettari, agricoli, enti non commerciali, gruppi, imprese nuove).
- Formula completa in `intensita` con l'esempio 3 della circolare 1/E (285.000 euro di maggiorazione) e un esempio di assunzione a meta' anno; base "mobile" anno per anno.
- Elenco completo e testuale delle categorie al 130% (allegato 1), compresa la categoria "sede di lavoro in regioni con PIL 2018 sotto il 75% della media UE o 75-90% con occupazione sotto la media": e' quella che interessa piu' clienti (tutte le assunzioni nelle regioni del Sud).
- Regole della circolare 1/E: part-time in proporzione, soci di cooperativa, somministrati, trasformazioni (costo dalla data), cessioni d'azienda e passaggi infragruppo esclusi, pensionamenti che contano come uscite, enti non commerciali in proporzione ai ricavi, semplificati per cassa, inizio attivita' entro il 1/1/2025 per il 2026.

## Corretto (prima / dopo)
- Condizione di incremento: "aumento del numero medio dei dipendenti a tempo indeterminato rispetto al periodo precedente" -> numero dei dipendenti a tempo indeterminato **al 31/12** superiore alla **media** dell'anno precedente (e lo stesso per il totale), come dice la circolare 1/E par. 2.
- Categoria "regioni a basso PIL (elenco preciso da verificare)" -> criterio esatto della norma; elenco probabile indicato come da verificare.
- Categoria "donne con almeno due figli minori": precisato che la norma la lega alla residenza in regioni/aree indicate (prima sembrava valere ovunque).
- `beneficio_stimato.percentuale_min`: 4.8 -> 4.6 (IRPEF 23% x 20%).
- Esempio ufficio_servizi: usava il giovane "ammesso agli incentivi art. 27 DL 48/2023" per il 130%; quell'incentivo riguardava le assunzioni del 2023, quindi per il 2026 e' poco realistico -> sostituito con la sede di lavoro al Sud.
- Sintesi: tolto "giovani ammessi agli incentivi" come esempio principale, aggiunte le cifre IRPEF.
- `fonte_verificata_il`: 2026-10-07 -> 2026-10-09.

## Fonti
- Circolare Agenzia Entrate 1/E del 20/01/2025 (letta per intero): https://www.agenziaentrate.gov.it/portale/documents/d/guest/circolare_n_1_del_20_01_2025
- Comunicato Agenzia 20/01/2025: https://www.agenziaentrate.gov.it/portale/-/comunicato-stampa-del-20-gennaio-2025-nuove-assunzioni
- Aliquote IRPEF 2026: https://www.agenziaentrate.gov.it/portale/imposta-sul-reddito-delle-persone-fisiche-irpef-/aliquote-e-calcolo-dell-irpef
- Nuovo TUIR D.Lgs. 117/2026, art. 104 e allegato G: GU n. 152 del 3/7/2026 (riscontro tramite fonti secondarie: miolegale.it, edotto.com)

## Da verificare
- Elenco delle regioni con sede di lavoro al 130% (con lo stesso criterio la Decontribuzione Sud usava Abruzzo, Molise, Campania, Puglia, Basilicata, Calabria, Sicilia, Sardegna; l'Agenzia non lo ha pubblicato per questa misura).
- Categoria "giovani art. 27 DL 48/2023": probabilmente vuota per le assunzioni 2026.
- Effetto sul reddito del concordato preventivo biennale.
- Numero esatto dei commi dell'art. 104 nuovo TUIR (10-18) e codice del rigo nel modello Redditi.
- Cumulo espresso con i bonus del DL 62/2026: non riverificato in questa sessione (ripreso dalla scheda precedente).
