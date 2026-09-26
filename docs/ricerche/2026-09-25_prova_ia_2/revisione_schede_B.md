# Revisione schede Sonnet – seconda prova, gruppo B2 (478, 933, 1052, 519, 779)

*Revisione del 25/09/2026, con lo stesso metodo della prima prova: l'unico riferimento è il testo che Sonnet aveva davanti (`scheda_N.txt`). Nessuna pagina aperta su internet: tutti i dubbi si sono risolti con i documenti. Per il controllo preliminare ho letto anche `preliminare_N.txt`, cioè quello che Haiku vedeva davvero (solo l'inizio dei documenti, circa 20.000 caratteri).*

## Tabella riassuntiva

| Bando | Preliminare giusto? | Voto | INVENTATO | SBAGLIATO | MANCANTE | IMPRECISO | Nota |
|---|---|---|---|---|---|---|---|
| 478 Emilia-Romagna, Digital Export | sì | **4** | 0 | 0 | 2 | 2 | Solo la pagina di riepilogo. Scheda onesta. "Imprese manifatturiere" non è diventato sezione C: l'abbinamento lascerebbe passare ogni settore |
| 933 Sviluppumbria, STEP linea A | sì | **3** | 0 | 0 | 5 | 4 | Date, importi ed esclusioni ATECO giusti. Però la scheda fa sembrare il bando aperto a tutte le PMI, che invece entrano solo in cordata con una grande impresa. Manca anche il limite delle aree 107.3.c |
| 1052 Camera di Genova, pacchetto entroterra | sì per le regole, no nel merito | **2** | 0 | 2 | 2 | 2 | È una notizia su più misure, non un bando. La data "31/12/2026" presa dal titolo terrebbe la scheda "aperta" per tre mesi senza motivo |
| 519 Lombardia, housing sociale | **no** | **4** | 0 | 0 | 2 | 4 | Non è un bando da scartare: ammette le imprese sociali e le cooperative sociali. Sonnet ha fatto bene a compilarlo, Haiku ha sbagliato a fermarlo |
| 779 Camera di Roma, femminile 2025 | sì | **4** | 0 | 0 | 2 | 2 | Scheda quasi perfetta, ma di un bando chiuso a dicembre 2025: Haiku ha fatto bene a fermarlo |

Legenda come nella prima prova: **INVENTATO** = non c'è nei documenti · **SBAGLIATO** = i documenti dicono un'altra cosa · **MANCANTE** = c'è nei documenti ma la scheda non lo riporta · **IMPRECISO** = giusto ma incompleto o fuorviante. Pericolo = quanto l'errore può portare l'abbinamento a proporre un bando sbagliato a un cliente (o a non proporgli quello giusto).

## Sintesi

- **Anche stavolta nessuna invenzione.** In 5 schede non c'è un solo valore assente dai documenti. Date, ore, importi, percentuali, dotazioni e codici ATECO corrispondono al testo.
- **Le regole nuove funzionano.** L'ente è sempre chi finanzia e il gestore sta a parte (5 su 5, contro 2 errori della prima prova). Le esclusioni di settore sono nell'elenco (933). I tempi delle spese sono sempre scritti, e quando mancano c'è l'avvertenza. "NON PER IMPRESE" non è usato a sproposito (519). La prima avvertenza dice sempre se manca il bando ufficiale.
- **Il nuovo errore tipico riguarda l'abbinamento.** Tre schede scrivono "c'è un vincolo" ma lasciano vuoto il campo che lo descrive: ATECO nel 478 e nel 1052, età dell'impresa nel 933. Con le regole di oggi l'abbinamento legge l'elenco vuoto come "nessun limite". È l'errore più pericoloso di questo gruppo.
- **Restano fuori i limiti che non stanno in un elenco:** piccoli comuni (1052), aree 107.3.c (933), PMI ammesse solo in cordata con una grande impresa (933). Sono proprio questi limiti a escludere la maggior parte dei clienti.
- **Molti problemi vengono dal materiale in ingresso**, non da Sonnet. Nel 933 circa 21.000 caratteri (il 14% del testo) sono codici illeggibili del PDF ("/g36/g79..."), mentre la pagina ufficiale e l'elenco delle aree 107.3.c sono stati esclusi "per lunghezza". Nel 519 il bando vero è dentro un file .zip che non è stato aperto. Nel 779 il modulo di domanda è stato preso per il bando e messo per primo, e i due file hanno lo stesso nome ("scarica il file").
- **Controllo preliminare:** 3 decisioni giuste su 5 e una sbagliata. Il 519 è stato scartato anche se Haiku aveva letto "imprese sociali e cooperative sociali" e le sue istruzioni dicono "anche solo alcune imprese". Il 1052 invece è passato per un buco nelle regole: una notizia su un pacchetto di misure non è un bando.

---

## 478 – Regione Emilia-Romagna, Digital Export 2026-2027

**Materiale in ingresso.** Solo la pagina della Regione, letta dall'API del sito: circa 110 righe utili, nessun allegato. La pagina rimanda a "Bando e modulistica dal sito Unioncamere", ma il link non è stato seguito. Circa 20 righe sono il modulo di gradimento del sito.

| Campo | Problema | Tipo | Pericolo |
|---|---|---|---|
| `codici_ateco` `[]` con `vincoli.ateco = vincolo` | La pagina dice "imprese **manifatturiere**", cioè la sezione C, che ha la stessa lettera in ATECO 2007 e 2025. Sonnet l'ha scritto solo nelle avvertenze. Con l'elenco vuoto l'abbinamento non esclude nessun settore: un commercio o un'agenzia risulterebbero "da verificare" come una fabbrica | MANCANTE | **alto** (in parte attenuato: una scheda `solo_sintesi` non dà mai "compatibile") |
| `spesa_minima` `null` | Il contributo minimo è 10.000 € al 50%, quindi il progetto deve valere almeno 20.000 €. È un calcolo, non una deduzione, ma il prompt (regola 1) lo vieta. La sintesi riporta il minimo di 10.000 € | MANCANTE | medio |
| `fondo_perduto_massimo` 20000, `percentuale_fondo_perduto` `null` | Campi incoerenti tra loro. Il bando non è misto: secondo SCHEDA_BANDO.md andavano lasciati vuoti tutti e due, oppure compilati tutti e due (50) | IMPRECISO | basso |
| avvertenze | "Contributo minimo non riportato in un campo dedicato" è un commento sulla scheda, non un'informazione per il cliente | IMPRECISO | basso |

Il resto è corretto: ente Regione e gestore Unioncamere ER; sede legale o operativa in regione; micro, piccole e medie; 50%, massimo 20.000 € su 40.000 € di spesa; dal 28/09 ore 12 al 05/10 ore 12. La modalità di selezione resta vuota perché la pagina non la dice: giusto così.

**Regole nuove:** tutte rispettate. `completezza = solo_sintesi` con la prima avvertenza che lo dice; avvertenza sui tempi delle spese; ora di chiusura segnalata.

**Preliminare di Haiku: giusto** (per imprese, edizione in corso, `solo_sintesi`, quindi si procede). Un dettaglio: lo stato è "in arrivo" (apre il 28/09), non "aperto", ma la decisione non cambia.

**Voto: 4/5.** Con una sola pagina di riepilogo non si poteva fare molto di più. Manca soltanto la sezione C nell'elenco ATECO. Il bando apre tra tre giorni e resta aperto una settimana: conviene recuperare il bando da Unioncamere subito.

---

## 933 – Sviluppumbria, Avviso STEP 2026, linea A (sovvenzione)

**Materiale in ingresso.** C'è l'avviso completo pubblicato sul Bollettino regionale (46 pagine, fino all'art. 15). Il taglio a 150.000 caratteri è caduto dentro i fac-simile finali, quindi con ogni probabilità ha tolto solo moduli. Però:
- in coda all'avviso ci sono circa **21.000 caratteri di codici illeggibili** ("/g36/g79/g79..."): sono i fac-simile della domanda, estratti male dal PDF;
- la **pagina ufficiale** è stata esclusa "per lunghezza", e così tutte le appendici. Tra queste c'è l'**Appendice D "Aree 107.3.c"**, che serve a capire dove una grande impresa può investire;
- il titolo e l'intestazione dell'avviso sono ripetuti tre volte.

| Campo | Problema | Tipo | Pericolo |
|---|---|---|---|
| `dimensioni_ammesse` = micro, piccola, media, grande; `linee` `[]` | L'elenco unisce tutte le dimensioni, ma **le PMI possono partecipare solo in un raggruppamento (RTI) con una grande impresa capofila** (art. 2.1): massimo 6 imprese, ognuna con almeno il 10% dei costi, progetto di almeno 1.700.000 €. Andavano fatte due linee: "grande impresa da sola" (spesa minima 1.200.000 €) e "RTI grande impresa + PMI" (1.700.000 €). Oggi ogni PMI umbra a forma di società di capitali risulterebbe adatta | MANCANTE (linee) | **alto** |
| territorio / requisiti | Nella tabella dell'art. 3.1 la grande impresa può fare solo "nuova unità produttiva" o "diversificazione", e **solo nelle aree 107.3.c**. Fuori da quelle aree l'aiuto sugli investimenti per la grande impresa è **0%** (art. 4.2). Poiché gli investimenti sono obbligatori, in pratica il capofila deve investire in un'area 107.3.c. La sintesi dice solo che la percentuale "varia secondo la zona" | MANCANTE | **alto** |
| `percentuale` 80 | L'80% vale solo per la parte di ricerca e sviluppo (al massimo il 35% del progetto), per una piccola impresa con tutte le maggiorazioni. Sugli investimenti, che sono la parte principale, il massimo è 40% (piccola impresa in area 107.3.c). L'avvertenza lo spiega, ma il numero nel catalogo fa pensare a un aiuto molto più alto | IMPRECISO | medio |
| `vincoli.eta_impresa = vincolo`, mesi `null` | Il requisito vero è "almeno due bilanci approvati e depositati" (una sola PMI neocostituita per RTI). "Vincolo" senza un numero non serve all'abbinamento. Meglio `non_noto` e il requisito a parole, oppure 24 mesi con un'avvertenza | IMPRECISO | medio |
| `requisiti` | Mancano condizioni che escludono: l'**indice di autocopertura** (patrimonio netto / quota a carico dell'impresa ≥ 0,20: sotto questa soglia l'intero progetto è escluso, criterio C.3 e art. 6.2); il livello tecnologico (TRL) già a 5 e obiettivo 7 per la ricerca (art. 3.1); le **fatture sotto 1.000 € di imponibile non ammesse**; i pagamenti solo con bonifico o RiBa; CUP o dicitura "Avviso STEP 2026 - Linea a sovvenzione" sulle fatture (artt. 3.2 e 3.4) | MANCANTE | medio |
| requisiti (polizza e DURC) | La scheda dice "al momento dell'erogazione". Il bando li chiede per la **concessione**, da presentare entro 30 giorni dalla comunicazione (art. 6.5) | IMPRECISO | basso |
| `requisiti_speciali_premiali` `rating_legalita` | Il rating di legalità serve solo a decidere tra due domande con lo stesso punteggio (art. 6.4), non dà punti. Le startup e le PMI innovative danno punti (criterio G), ma solo se partecipano al raggruppamento o fanno da fornitori | IMPRECISO | basso |
| avvertenze | Non dicono che mancano l'elenco delle aree 107.3.c e la pagina ufficiale. Non citano l'anticipo del 40% con fideiussione bancaria (art. 9.1). Ripetono la soglia di 55 punti, che è già nella sintesi | MANCANTE | basso |

Tutto il resto è corretto: ente Regione Umbria e gestore Sviluppumbria; sede da attivare entro la prima erogazione; società di capitali; esclusi sezione A, divisione 12 e i codici del tabacco in G, ATECO 2025; regime GBER (artt. 14, 17, 25); dotazione 15.421.586 €; dal 01/10 ore 10 al 30/11 ore 12; graduatoria con minimo 55 punti; spese solo dopo la domanda, da concludere e pagare entro 24 mesi dalla concessione, saldo entro 60 giorni.

**Regole nuove:** ente e gestore ✓; esclusioni ATECO nell'elenco ✓; requisiti separati dal punteggio ✓ (con l'eccezione del C.3, che è un requisito nascosto nella griglia dei punti); tempi delle spese ✓; fonti ✓ con l'articolo. Le avvertenze non contengono supposizioni.

**Preliminare di Haiku: giusto** (si procede). Haiku ha scritto "stato non noto, date non specificate" perché vedeva solo l'inizio del testo e le date sono a pagina 18. L'errore è innocuo, ma conferma che lo stato va calcolato dopo la scheda e non dal controllo preliminare.

**Voto: 3/5.** Dati precisi e ben citati. Il bando però è per grandi imprese, e la scheda lascerebbe passare per l'abbinamento molte PMI che da sole non possono partecipare.

---

## 1052 – Camera di Commercio di Genova, pacchetto di misure per l'entroterra

**Materiale in ingresso.** Una notizia della Camera, scritta come una sola lunga frase, e 30 righe di slide di presentazione della legge regionale 6/2025. Non c'è nessun bando: la notizia descrive quattro misure diverse, con gestori diversi (Camera di Genova, Filse, due fondi di garanzia) e senza date.

| Campo | Problema | Tipo | Pericolo |
|---|---|---|---|
| `scadenza` 2026-12-31 | La data compare solo nel titolo della notizia ("Entro il 31 Dicembre 2026"). Il testo non dice a quale misura si riferisca. Sonnet lo ammette nelle avvertenze ma compila lo stesso il campo: il sistema mostrerà il pacchetto come "aperto" fino al 31/12. Con le regole attuali il campo doveva restare vuoto | IMPRECISO | **alto** |
| territorio | Le misure valgono solo per i **comuni sotto 2.500 abitanti** (nuove attività) o **fino a 5.000** (imprese esistenti). La scheda ha solo `LIG`: un cliente di Genova città risulterebbe nel territorio. L'unico posto giusto per ora è il testo di `territorio`, ma serve un modo per dire all'abbinamento che il territorio è solo una parte della regione (vedi proposte) | MANCANTE | **alto** |
| territorio (aree interne) | Le 8 aree interne della Strategia Nazionale riguardano i 2,8 milioni per la sicurezza dei boschi, che Sonnet stesso esclude nelle avvertenze. Non c'entrano con le misure per le imprese. Inoltre la pagina dice "sei aree" ma ne elenca otto, e la differenza non è segnalata | SBAGLIATO | medio |
| linea "Garanzie", `percentuale` 100 | La notizia dice che i due strumenti "permettono di coprire fino al 100% delle spese di ammodernamento": è il finanziamento, non la copertura della garanzia come scrive la nota. Un 100% nella linea rischia di essere letto come contributo | SBAGLIATO | medio |
| `tipi_agevolazione` | Le slide dicono "fondo perduto e **finanziamenti agevolati e garantiti**": manca `finanziamento_agevolato` | MANCANTE | basso |
| `codici_ateco` `[]` con `vincoli.ateco = vincolo` | I settori sono artigianato, commercio e ristorazione, ma l'elenco è vuoto: per l'abbinamento vuol dire "tutti i settori". Meglio `non_noto`, oppure ristorazione (56) e commercio al dettaglio (47) con un'avvertenza | IMPRECISO | medio |

Il lavoro di Sonnet è onesto: le avvertenze dicono chiaramente che non c'è un bando, che le misure sono diverse e che la data è incerta. Ente (Regione Liguria) e gestori sono separati bene.

**Regole nuove:** ente e gestore ✓; avvertenze senza supposizioni ✓ (la frase sui 2,8 milioni "sembrano servizi" è una valutazione, ma è dichiarata come tale); avvertenza sui tempi delle spese ✓.

**Preliminare di Haiku: giusto secondo le regole, sbagliato nel merito.** Per le sue istruzioni una notizia è `solo_sintesi`, e `solo_sintesi` non ferma Sonnet. Questa però non è la sintesi di un bando: è un comunicato su una politica regionale. Andava trattato come segnalazione ("esistono queste misure, cercare i bandi Filse e Camera"), non come scheda.

**Voto: 2/5.** Non per colpa di Sonnet: dal materiale non si poteva fare una scheda utile. Così com'è, però, la scheda porterebbe in abbinamento clienti liguri di qualunque comune e settore, con una scadenza che non esiste.

---

## 519 – Regione Lombardia, housing sociale Linea 3 (il "bando trappola")

**Materiale in ingresso.** Il **bando vero (Allegato A) non è stato letto**. Secondo l'avviso del 22/09 il file "Bando e allegati parti integranti" è un **archivio** (zip), non una scansione. Sono stati letti invece la pagina, le FAQ del 22/09 (molto ricche), il decreto di approvazione, la Scheda tecnica dei criteri (d.g.r. 6522) e parte dello schema di convenzione. Esclusi per lunghezza: la d.g.r. 6209, il BURL e l'elenco dei "Comuni ATA" (i comuni con più bisogno di case). Le "Linee guida di rendicontazione" sono elencate nella pagina ma non sono state scaricate.

**È per imprese?** In parte sì. Tra i beneficiari ci sono le **imprese sociali** (d.lgs. 112/2017) e le **cooperative sociali**, che sono imprese a tutti gli effetti. Non lo sono le società commerciali normali. Sonnet ha fatto bene a **non** usare "NON PER IMPRESE" e a spiegarlo nelle avvertenze.

| Campo | Problema | Tipo | Pericolo |
|---|---|---|---|
| `soggetti_ammessi` = solo `ente_terzo_settore`; `requisiti_speciali` `non_noto` | Per le imprese sociali e le cooperative sociali serviva `impresa` con `requisiti_speciali_obbligatori = ["impresa_sociale"]` (e `vincoli.requisiti_speciali = vincolo`); per gli enti religiosi, `altro`. Così com'è, un cliente cooperativa sociale registrato come "impresa" viene escluso. Le società normali restano giustamente fuori | MANCANTE | medio |
| `requisiti` | Mancano condizioni che fanno perdere il contributo: **titolo edilizio entro 6 mesi dalla graduatoria, pena la revoca**; proposta **concordata con il Comune**; intervento minimo = un edificio (o una sua parte funzionale) oppure almeno 5 alloggi nello stesso comune; alloggi destinati a servizi abitativi sociali per **almeno 20 anni** (Scheda tecnica, "Interventi ammissibili" e "Criteri di ammissibilità") | MANCANTE | medio |
| `completezza = bando_ufficiale` | Formalmente giusto: il prompt lo permette anche con il solo decreto di approvazione. Però il testo del bando non è stato letto, e la scheda dovrebbe dirlo nel campo, non solo nelle avvertenze (vedi proposte) | IMPRECISO | medio |
| avvertenza 1 | "Non leggibile perché è una scansione": è una supposizione. L'avviso del 22/09 dice che è un archivio, e la nota del sistema dice "scansione **o formato non letto**" | IMPRECISO | basso |
| avvertenza sulla maggiorazione | "Si aggiunge a questo importo base" lascia intendere 2.000.000 € più 20%. La Scheda tecnica dice che la maggiorazione vale il 5% del costo convenzionale per elemento, fino al 20%. Non dice se il tetto di 2.000.000 € la comprende | IMPRECISO | basso |
| fonti | `requisiti` cita solo le FAQ, ma gran parte viene dalla Scheda tecnica | IMPRECISO | basso |

Corretti: ente Regione Lombardia (gestore "non previsto", come scritto nella Scheda tecnica); sede operativa in Lombardia; dal 01/09 ore 12 al 30/10 ore 12; graduatoria approvata entro 120 giorni; massimo 2.000.000 € calcolati sui metri quadri (700/800/900 €/mq a seconda della durata del vincolo); dotazione 13 milioni; regime SIEG (`altro`, giusto: non c'è un valore apposta); spese dal 30/05/2026, pagate e collaudate entro il 31/12/2029, rendicontazione entro il 30/06/2030; fideiussione o ipoteca; priorità al massimo per 2 proposte per proponente.

**Regole nuove:** tempi delle spese ✓ (completi); garanzie ✓; numero di domande ✓; "NON PER IMPRESE" non usato, ed è la scelta giusta.

**Preliminare di Haiku: sbagliato.** Haiku ha risposto `per_imprese = no` ("enti privati non lucrativi e terzo settore"). Eppure nel testo che vedeva c'era "imprese sociali e cooperative sociali", e le sue istruzioni dicono di rispondere `si` se il bando è per imprese "anche solo alcune". Con le regole attuali la scheda non sarebbe stata fatta. Per uno studio che ha clienti cooperative sociali, questo è un bando perso.

**Voto: 4/5.** La scheda è ricca e precisa, e Sonnet ha capito il caso meglio di Haiku. Vanno sistemati i soggetti (impresa sociale) e le condizioni che fanno scattare la revoca.

---

## 779 – Camera di Commercio di Roma, Idea innovativa femminile 2025 (XIII edizione)

**Materiale in ingresso.** C'è il bando completo (13 articoli) con la pagina. Il **modulo di domanda** però è stato classificato come "bando" e messo per primo, mentre il bando vero è classificato "altro" e sta in fondo. Tutti e due si chiamano "scarica il file": nelle fonti di Sonnet non si capisce quale dei due è citato.

| Campo | Problema | Tipo | Pericolo |
|---|---|---|---|
| `territorio_regioni` `[]` con `territorio_province` `RM` | Per l'abbinamento basta la provincia. Ma un filtro "Lazio" nella plancia non troverebbe il bando: meglio compilare anche `LAZ` | IMPRECISO | basso |
| spese_ammesse / avvertenze | Manca l'obbligo di scrivere il **CUP** e la dicitura "Spesa sostenuta a valere sul Bando Idea Innovativa 2025 CCIAA Roma" sulle fatture (artt. 8 e 10). Il CUP arriva con la concessione, quindi le fatture fatte prima (ammesse fino a 60 giorni prima del bando) rischiano di non essere in regola. Un cliente deve saperlo prima di comprare | MANCANTE | medio |
| `requisiti` | Manca la regolarità contributiva (DURC), che il modulo di domanda fa dichiarare | MANCANTE | basso |
| avvertenza 1 | Ripete quasi alla lettera `spese_ammesse` (regola 21: non ripetere) | IMPRECISO | basso |

Tutto il resto è esatto: ente Camera di Roma, niente gestore; sede legale o unità operativa a Roma e provincia; micro, piccole e medie; impresa femminile obbligatoria, con le soglie per ogni forma giuridica; de minimis; 50% fino a 5.000 € per cinque vincitrici, dotazione 25.000 €; domande dal 10/11/2025 ore 9 al 19/12/2025 ore 14 via PEC; graduatoria con minimo 18 punti su 30; spese dal 60° giorno prima dell'approvazione (3/11/2025); rendicontazione entro 12 mesi, senza proroga, solo con bonifico.

**Regole nuove:** tutte rispettate. Ente e gestore ✓, requisiti separati dal punteggio ✓ (i 18 punti sono nella sintesi), tempi delle spese ✓, fonti con l'articolo ✓. La menzione speciale senza premio è segnalata correttamente, senza supposizioni.

**Preliminare di Haiku: giusto.** Edizione 2025, chiusa il 19/12/2025: `edizione_in_corso = no` e `stato = chiuso`, quindi niente scheda. Sonnet l'ha compilata solo perché la prova lo forzava.

**Voto: 4/5.** Nel merito è la scheda migliore del gruppo, ma manca l'avviso sul CUP in fattura. Oggi serve solo come storico e per sapere cosa aspettarsi dall'edizione 2026.

---

## Problemi ricorrenti

1. **"Vincolo" con il campo vuoto** (478 ATECO, 1052 ATECO, 933 età). È il difetto più pericoloso: SCHEDA_BANDO.md dice che l'elenco ATECO si controlla "se è pieno", quindi un elenco vuoto lascia passare tutti, anche quando lo stato è `vincolo`. Né Sonnet né il sistema si accorgono dell'incoerenza.
2. **Limiti che non entrano nei campi**: una parte dei comuni (1052 piccoli comuni, 933 aree 107.3.c, 519 comuni ad alta tensione abitativa solo per il punteggio) e il ruolo del cliente ("solo dentro un raggruppamento con una grande impresa", 933). Quando mancano i campi, Sonnet mette l'informazione nella sintesi o la perde, e l'abbinamento la ignora.
3. **Linee non usate quando servono** (933: grande impresa da sola / raggruppamento; investimenti / ricerca con percentuali molto diverse). Il campo `percentuale` finisce così per riportare il caso più favorevole e più raro.
4. **Requisiti nascosti altrove**: soglie che escludono ma stanno nella griglia dei punti (933, autocopertura ≥ 0,20), obblighi dopo la concessione che fanno perdere il contributo (519 titolo edilizio entro 6 mesi; 779 e 933 CUP in fattura; 933 fatture sotto 1.000 €). La regola 17 del prompt non li copre.
5. **Materiale in ingresso**: codici illeggibili del PDF tenuti mentre si tagliano pagina e appendici (933); archivio .zip non aperto (519); modulo scambiato per il bando e documenti con lo stesso nome (779); link al bando vero non seguito (478, Unioncamere).
6. **Campi del fondo perduto usati in modo diverso**: `fondo_perduto_massimo` è compilato nel 478 e nel 519 (bandi non misti) e vuoto nel 779 e nel 933. Per il catalogo non cambia nulla, ma rende inaffidabili i confronti.
7. **Controllo preliminare**: Haiku non considera imprese quelle sociali e cooperative (519), e non ha un modo per dire "questa è una notizia su più misure, non un bando" (1052).

Cosa è migliorato rispetto alla prima prova: nessuna confusione tra ente e gestore, nessun 100% che somma prestito e fondo perduto, tempi delle spese sempre presenti, avvertenze molto più pulite (nessuna "le risorse potrebbero esaurirsi").

## Proposte

1. **Controllo automatico dopo Sonnet** (nel codice, senza IA): se un vincolo è `vincolo` ma il campo che lo descrive è vuoto (elenco ATECO, mesi di età, dipendenti, fatturato), lo stato diventa `non_noto` e si aggiunge l'avvertenza "vincolo scritto nel bando ma non tradotto in codici". Lo stesso controllo compila o svuota `fondo_perduto_massimo` e `percentuale_fondo_perduto` secondo `tipo_agevolazione`. Così l'abbinamento non tratta mai un limite dichiarato come "nessun limite".
2. **Nuovo valore per il territorio parziale**: un campo `territorio_parziale` (sì/no) o un valore `parziale` in `vincoli.territorio`. Nel prompt: "se il bando vale solo per una parte dei comuni che non puoi elencare (comuni sotto X abitanti, aree 107.3.c, aree interne, montani), scrivila in `territorio` e segna il territorio come parziale; se hai l'elenco, compila `territorio_comuni`". L'abbinamento risponde allora al massimo "da verificare: controllare il comune".
3. **Prompt, linee e partecipazione**: "Crea una linea per ogni modo di partecipare con regole diverse (da soli / in raggruppamento, capofila obbligatorio) e per ogni tipo di intervento con percentuali diverse (investimenti / ricerca). Se una categoria può partecipare solo insieme a un'altra, scrivilo in `a_chi_si_rivolge` della linea e nei `requisiti`". Aggiungere a `requisiti_speciali` il valore `solo_in_aggregazione`, così l'abbinamento non propone il bando a una PMI come se potesse partecipare da sola.
4. **Prompt, requisiti che escludono ovunque siano scritti**: "In `requisiti` metti anche le soglie della griglia di valutazione che portano all'esclusione (indici di bilancio minimi, 'non adeguato' = escluso) e gli obblighi dopo la concessione che fanno perdere il contributo (titoli edilizi entro X mesi, CUP o dicitura in fattura, importo minimo delle fatture, pagamenti tracciabili)". E una frase fissa: "Le imprese sociali e le cooperative sociali sono imprese: `soggetti_ammessi` contiene `impresa` e `requisiti_speciali_obbligatori` contiene `impresa_sociale`".
5. **Controllo preliminare di Haiku**: aggiungere che "imprese sociali e cooperative sociali contano come imprese" (519), e una quinta domanda `tipo_documento`: `bando`, `pacchetto_misure` o `notizia`. Un pacchetto o una notizia senza bando non diventa una scheda: diventa una segnalazione nella plancia ("cercare i bandi collegati"), e senza scadenza inventata dal titolo (1052).
6. **Raccolta dei documenti**: (a) togliere le sequenze di codici illeggibili dei PDF (`/g36/g79...`) **prima** del taglio per lunghezza; (b) non escludere mai la pagina ufficiale e gli allegati con elenchi di territori ("Aree", "Comuni", "Appendice D"), al massimo accorciarli; (c) aprire gli archivi .zip e leggere il bando che contengono; (d) riconoscere il modulo di domanda dal contenuto ("CHIEDE", "DICHIARA", "La sottoscritta") e metterlo in fondo; (e) dare ai documenti il nome del testo accanto al link ("Bando Idea Innovativa 2025"), non "scarica il file"; (f) aggiungere a `completezza` il valore `bando_parziale` per quando si leggono criteri, FAQ e decreto ma non il testo del bando (519).
