# Misure nazionali automatiche o a sportello, da affiancare ai bandi

**Data:** 5 ottobre 2026

**Domanda:** quali misure nazionali "automatiche" o a sportello permanente danno benefici sugli investimenti delle imprese, sono in vigore a ottobre 2026 e si possono sommare ai bandi a fondo perduto? In primo luogo Conto Termico 3.0 e iperammortamento 2026; poi, se verificate, poche altre misure generali dello stesso tipo. Esito strutturato in `app/misure/misure.yaml`.

**Metodo:** ricerca web limitata il più possibile a siti ufficiali (gse.it, mimit.gov.it, agenziaentrate.gov.it, gazzettaufficiale.it, normattiva.it) e lettura diretta delle pagine. Due testi letti per intero: le **Regole Applicative del Conto Termico 3.0** (PDF GSE, 2,7 MB) e il **DM MIMIT-MEF 7 maggio 2026** sull'iperammortamento (PDF MIMIT), estratti a testo con `pypdf` dentro il container `app` perché lo strumento web non legge i PDF compressi. Le fonti secondarie (commercialisti, associazioni) le ho usate solo dove il testo ufficiale non era raggiungibile, e sono indicate come tali.

**Limiti:**
- **Il testo della Legge 199/2025 (commi 427-436 e 438-443) non l'ho letto direttamente**: Normattiva e Gazzetta Ufficiale mostrano solo l'inizio dell'articolo 1 (che ha centinaia di commi). Numero di legge, commi, scaglioni e periodo sono confermati dal MIMIT e dal DM attuativo; le esclusioni soggettive, il testo del comma 431 sul cumulo e la modifica del DL 38/2026 (via il vincolo "prodotto in UE") vengono da fonti secondarie concordi (Confindustria Toscana, ANCE, iperammortamenti.it e altre).
- Le FAQ GSE (assistenza.clienti.gse.it) si caricano con JavaScript e non si leggono senza browser: la posizione del GSE sul cumulo Conto Termico + iperammortamento è riportata da fonti secondarie che la citano, ed è coerente con l'art. 17 del DM che ho letto.
- Percentuale di riparto del credito ZES per il 2026, elenco preciso dei settori esclusi ZES e vincoli di mantenimento: non verificati, scritti come "da verificare".
- Le stime di beneficio sono mie, prudenti, e valgono per un'impresa in utile tassata IRES al 24%.

## URL visti davvero

| Fonte | URL | Cosa conferma | Giudizio |
|---|---|---|---|
| GSE, pagina Conto Termico 3.0 | https://www.gse.it/servizi-per-te/efficienza-energetica/conto-termico-3-0 | budget 900 mln/anno, ripartizione, soggetti | sì |
| GSE, percentuali ed erogazione | https://www.gse.it/servizi-per-te/efficienza-energetica/conto-termico-3-0/percentuali-ed-erogazione-degli-incentivi | percentuali imprese, rate, soglia 15.000 € | sì |
| GSE, news regole applicative (19/12/2025) | https://www.gse.it/servizi-per-te/news/conto-termico-3-0-pubblicate-le-regole-applicative | DM 7/8/2025 in GU 26/9/2025, regole approvate | sì |
| GSE, Regole Applicative CT 3.0 (PDF letto per intero) | https://www.gse.it/documenti_site/Documenti%20GSE/Servizi%20per%20te/BIOMETANO/Regole%20e%20procedure/Regole_Applicative_CT_3_0.pdf | interventi, imprese (Titolo V), intensità, richiesta preliminare, 90 giorni, cumulo (par. 4.5) | sì |
| GSE, news riapertura portale (10/4/2026) | https://www.gse.it/servizi-per-te/news/conto-termico-3-0-riapre-il-portale | riapertura 13/4/2026 solo accesso diretto | sì |
| MIMIT, pagina iperammortamento | https://www.mimit.gov.it/it/incentivi/nuovo-piano-transizione-5-0-iperammortamento | norma, beneficiari, allegati IV e V, scaglioni, periodo, piattaforma GSE 12/6 e 21/7/2026 | sì |
| MIMIT, DM 7 maggio 2026 (PDF letto per intero) | https://www.mimit.gov.it/images/stories/normativa/allegati/Decreto_-_Iperammortamento_2026_-nf.pdf | procedura, 60 giorni, acconto 20%, 15/11/2028, perizia, certificazione, FER 105%, decadenza | sì |
| MIMIT, DD 10 giugno 2026 | https://www.mimit.gov.it/it/normativa/decreti-direttoriali/decreto-direttoriale-10-giugno-2026-iperammortamento-termini-e-modelli-di-comunicazione | esistenza del decreto su termini e modelli (visto solo nei risultati di ricerca) | non chiaro |
| MIMIT, credito R&S, innovazione, design | https://www.mimit.gov.it/it/incentivi/credito-d-imposta-r-s | aliquote per periodo, R&S 10% fino al 2031, design 2026 con plafond | sì |
| Agenzia Entrate, ZES unica 2026 | https://www.agenziaentrate.gov.it/portale/credito-d-imposta-per-investimenti-nella-zes-unica-zes-2026-/che-cos- | regioni (incluse Marche, Umbria, Abruzzo), 200.000 € minimo, 100 mln massimo, 2,3 mld nel 2026, cumulo | sì |
| MIMIT, Nuova Sabatini | https://www.mimit.gov.it/it/incentivi/agevolazioni-per-gli-investimenti-delle-pmi-in-beni-strumentali-nuova-sabatini | beneficiari, tassi, importi, erogazione, risorse al 14/9/2026 | sì |
| MIMIT, FAQ Nuova Sabatini | https://www.mimit.gov.it/it/assistenza/domande-frequenti/beni-strumentali-nuova-sabatini-domande-frequenti-faq | cumulo (FAQ 9.x), regime GBER, 120 giorni | sì |
| Confindustria Toscana Centro e Costa (secondaria) | https://confindustriatoscanacentroecosta.it/iperammortamento-nuova-agevolazione-per-le-imprese-della-legge-di-bilancio-2026/ | DL 38/2026 art. 7, esclusioni soggettive | sì (secondaria) |
| iperammortamenti.it (secondaria) | https://www.iperammortamenti.it/risorse/iperammortamento-cumulabilita | testo del comma 431, dubbio Sabatini | sì (secondaria) |
| naturalnzeb, FAQ CT (secondaria) | https://faqcontotermico.naturalnzeb.it/faq/cumulabilita-conto-termico-iper-ammortamento | posizione GSE: CT 3.0 non cumulabile con iperammortamento | sì (secondaria) |
| MIMIT, credito formazione 4.0 | https://www.mimit.gov.it/it/incentivi/credito-d-imposta-formazione-4-0 | "La misura non è più attiva" | sì |
| FiscoOggi (Agenzia Entrate), credito design 2026 | https://www.fiscooggi.it/portale/-/credito-design-e-ideazione-estetica-al-via-le-domande-al-mimit | L. 199/2025 commi 925-926, 10%, 2 mln per impresa, 60 mln totali, prenotazione dal 7/7/2026, completamento entro 30 giorni dalla chiusura del periodo | sì |
| Consulenti del Lavoro (30/7/2026) | https://www.consulentidellavoro.it/home/storico-articoli/19787-credito-d-imposta-design-esauriti-i-60-milioni-disponibili | 60 mln esauriti l'8/7/2026 (comunicazione MIMIT), coda per scorrimento | sì (secondaria) |
| EC News (17/2/2026) | https://www.ecnews.it/fiscale/fisco-e-patrimonio/agevolazioni/il-credito-design-prorogato-e-potenziato-nel-2026/ | design dal 5% al 10%, quota annuale unica; innovazione tecnologica non prorogata | sì (secondaria) |
| Normattiva, art. 244 DL 34/2020 | https://www.normattiva.it/uri-res/N2Ls?urn:nir:stato:decreto.legge:2020-05-19;34~art244 | aliquote maggiorate Sud (25/35/45%); scadenza non leggibile dalla pagina | non chiaro |
| incentivimpresa.it (secondaria) | https://www.incentivimpresa.it/credito-imposta-ricerca-sviluppo-sud-italia-bandi-regionali | maggiorazioni Sud fino al 2025, non prorogate nel 2026 | sì (secondaria) |
| **Aggiunta del 6/10/2026** (Art Bonus, Ecobonus, Sismabonus) | | | |
| Art Bonus, Benefici fiscali | https://artbonus.gov.it/beneficio-fiscale.html | 65%; 5 per mille dei ricavi per le imprese, 15% del reddito per persone fisiche; tre quote annuali; F24 codice 6842; riporto senza limiti; fuori dall'IRAP | sì |
| Art Bonus, Che cos'è | https://artbonus.gov.it/che-cosa-e-art-bonus.html | DL 83/2014 art. 1, reso permanente dalla L. 208/2015; beneficiari; obblighi di pubblicazione | sì |
| Art Bonus, FAQ | https://artbonus.gov.it/faq/ | esistono FAQ su enti ecclesiastici, codice tributo, cumulo: contenuto delle risposte non letto | non chiaro |
| Normattiva, art. 1 DL 83/2014 | https://www.normattiva.it/uri-res/N2Ls?urn:nir:stato:decreto.legge:2014-05-31;83~art1 | testo vigente: beneficiari, 65%, limiti, tre quote, comunicazione mensile dei beneficiari | sì |
| IPSOA (secondaria, solo risultato di ricerca) | https://www.ipsoa.it/documents/quotidiano/2026/02/21/beneficiari-art-bonus-proposta-legge-erogazioni-liberali | proposta di legge per estendere l'Art Bonus (musei privati, ETS, enti ecclesiastici), non ancora legge | sì (secondaria) |
| Agenzia Entrate, scheda Riqualificazione energetica | https://www.agenziaentrate.gov.it/portale/schede/agevolazioni/detrazione-riqualificazione-energetica-55-2016/cosa-riqualificazione-55-2016 | 2025-2026: 36% (50% abitazione principale); 2027: 30% (36%); esclusione caldaie a combustibili fossili; cessione/sconto vietati dal 17/2/2023; pagina aggiornata il 26/1/2026 | sì |
| Agenzia Entrate, area Risparmio energetico | https://www.agenziaentrate.gov.it/portale/aree-tematiche/casa/agevolazioni/agevolazioni-risparmio-energetico | IRPEF o IRES; 10 rate; stesse aliquote | sì |
| Agenzia Entrate, Circolare 8/E del 19/6/2025 (PDF letto con pypdf) | https://www.agenziaentrate.gov.it/portale/documents/d/guest/circolare-bonus-edilizi-del-19-giugno-2025 | testo della L. 207/2024 comma 55 (art. 14 e art. 16 c. 1-septies.1 DL 63/2013); limiti per intervento invariati; 50% solo per abitazione principale del titolare di diritto reale | sì |
| Agenzia Entrate, area Ristrutturazioni | https://www.agenziaentrate.gov.it/portale/aree-tematiche/casa/agevolazioni/agevolazioni-per-le-ristrutturazioni-edilizie | 2026 36%/50%, 2027 30%/36%; sismabonus 2026 come 2025 | sì |
| Agenzia Entrate, area Sisma bonus | https://www.agenziaentrate.gov.it/portale/aree-tematiche/casa/agevolazioni/sisma-bonus | IRPEF e IRES; edifici abitativi e produttivi in zona 1, 2, 3; 96.000 € per unità; 10 rate dal 2024 (L. 67/2024) | sì (pagina con aliquote vecchie, nuove dalla circolare) |
| ENEA, Vademecum Coibentazione strutture opache (23/9/2026, PDF letto con pypdf) | https://www.efficienzaenergetica.enea.it/images/detrazioni/VADEMECUM_2026/345_COIBENTAZIONE%20OPACO.pdf | tabella aliquote IRPEF/IRES 2025-2026 50%/36%, 2027 36%/30%; 60.000 € di detrazione; edificio esistente con riscaldamento; scheda ENEA entro 90 giorni; documenti | sì |
| ENEA, pagina Ecobonus | https://www.efficienzaenergetica.enea.it/detrazioni-fiscali/ecobonus.html | elenco interventi, 90 giorni (tabella non leggibile con lo strumento) | non chiaro |
| ENEA, notizia portale 2026 (22/1/2026) | https://www.efficienzaenergetica.enea.it/vi-segnaliamo/fisco-detrazioni-efficienza-energetica-online-portale-enea-per-invio-dati-2026.html | portale bonusfiscali.enea.it 2026, SPID/CIE | sì |
| ENEA, avviso 25/6/2026 (PDF) | https://www.efficienzaenergetica.enea.it/images/detrazioni/Avvisi/2026_06_25_AVVISO_RIAPERTURA_DLGS_5_2026.pdf | portale aggiornato al D.Lgs. 5/2026 e DM 26/10/2025 per lavori iniziati dal 4/2/2026 | sì |
| DM MISE 6/8/2020 requisiti tecnici, GU 246/2020 (PDF da ENEA, letto con pypdf) | https://www.efficienzaenergetica.enea.it/media/attachments/2020/10/13/30-decreto_efficienza_energetica_2020_gu.pdf | allegato B: limiti di detrazione per intervento (100.000 / 60.000 / 30.000 / 15.000 €); costi massimi €/kW; il DM non contiene un articolo sul cumulo con i contributi | sì |
| ANCE AIES (secondaria) | https://www.anceaies.it/le-detrazioni-edilizie-fruibili-nel-2026/ | quadro 2026; bonus barriere 75% non più disponibile; cessione/sconto finiti | sì (secondaria) |
| QuiFinanza e altri (secondarie, risultati di ricerca) | https://quifinanza.it/fisco-tasse/bonus-fiscali/bonus-barriere-architettoniche-2026/953303/ | bonus barriere 75% scaduto il 31/12/2025, non prorogato dalla L. 199/2025 | sì (secondaria) |
| Ricerca web (secondarie: Ance, quotidianopiu, legislazionetecnica non accessibile) | — | L. 199/2025 art. 1 comma 22 proroga il 36%/50% al 2026 | sì (secondaria), numero del comma non letto sul testo |
| PMI.it e risultati di ricerca (secondarie) | https://www.pmi.it/impresa/contabilita-e-fisco/esperto/352293/ecobonus-compatibile-con-contributi-regionali.html | ecobonus cumulabile con contributi regionali/locali solo sulla spesa non coperta, totale entro il 100% | sì (secondaria) |

## Esito per misura

| Misura | Vigente a ottobre 2026 | Nel file YAML | Note |
|---|---|---|---|
| Conto Termico 3.0 | sì | sì, `aperto` | portale sospeso 3/3 - 13/4/2026; risorse annuali da tenere d'occhio |
| Iperammortamento 2026 | sì | sì, `aperto` | investimenti 1/1/2026 - 30/9/2028 |
| Credito R&S 10% | sì (fino al 2031) | sì, `aperto` | spese di ricerca, non macchinari |
| Credito ZES unica 2026-2028 | sì | sì, `aperto` | finestra 2026 chiusa il 30/5/2026; prossima nel 2027 |
| Nuova Sabatini | sì | sì, `aperto` | sportello fino a esaurimento |
| Credito beni strumentali 4.0 / Transizione 5.0 | no per investimenti 2026 | no | sostituiti dall'iperammortamento |
| Credito innovazione tecnologica e transizione 4.0 | no (5% fino al 2025, non prorogato) | no | |
| Credito design 2026 | sì per legge, ma fondi esauriti | no | 10%, plafond 60 mln finito l'8/7/2026; prenotazioni solo in coda per scorrimento. Citato nell'avvertenza di `credito_rs_2026` |
| Credito formazione 4.0 | no | no | MIMIT: "La misura non è più attiva"; l'iperammortamento non copre la formazione |
| Maggiorazioni R&S Mezzogiorno | no per il 2026 | no (corretta la voce R&S) | valevano fino al 2025; nel 2026 10% ovunque |
| Art Bonus (6/10) | sì, permanente | sì, `art_bonus`, `aperto`, `categorie_spesa: []` | 65% della donazione, max 5 per mille dei ricavi, 3 quote in F24; non si abbina ai bandi |
| Ecobonus imprese (6/10) | sì, 36% per le spese 2026 (30% nel 2027) | sì, `ecobonus_imprese_2026`, `aperto` | tipo nuovo `detrazione_fiscale`; alternativo al Conto Termico |
| Sismabonus immobili produttivi (6/10) | sì, 36% per le spese 2026, zone sismiche 1-3 | sì, `sismabonus_imprese_2026`, `aperto` | 96.000 € per unità e per anno, 10 rate |
| Bonus barriere architettoniche 75% (6/10) | no (spese fino al 31/12/2025) | no (solo nel commento del YAML) | non prorogato dalla L. 199/2025 secondo fonti secondarie concordi; da confermare su fonte ufficiale |

## Punti principali e dubbi

### Conto Termico 3.0
- DM MASE 7 agosto 2025, in GU il 26/9/2025, in vigore dal 25/12/2025; Regole Applicative GSE approvate il 19/12/2025; nuovo Portaltermico attivo dal 2/2/2026.
- Per le imprese valgono le regole speciali del Titolo V: **richiesta preliminare prima dell'avvio dei lavori** (anche un ordine firmato fa partire i lavori), poi domanda entro **90 giorni dalla fine lavori**. Niente prenotazione per le imprese.
- Intensità per le imprese: efficienza (Titolo II) dal 25% al 65% (60% per le grandi); rinnovabili termiche (Titolo III) dal 45% al 65% (piccole), 55% (medie), 45% (grandi). Restano sempre i costi massimi unitari del decreto.
- **Cumulo, regola chiave:** niente Conto Termico se lo stesso intervento riceve altri "incentivi statali", cioè contributi erogati direttamente da un'Amministrazione centrale (art. 17); fanno eccezione fondi di garanzia, fondi di rotazione e contributi in conto interessi (quindi Sabatini e Fondo di garanzia sì). Per le imprese l'art. 27 permette di cumulare con altri aiuti di Stato sugli stessi costi (in pratica bandi regionali o camerali) entro le intensità massime. Il GSE considera "incentivi statali" anche detrazioni, crediti d'imposta e iperammortamento: **niente cumulo Conto Termico + iperammortamento sulle stesse spese**. Il dubbio "ma la legge sull'iperammortamento ammette il cumulo" c'è, ma il divieto del DM blocca l'ingresso al Conto Termico: va scelta una delle due strade.
- Dubbio: un bando a fondo perduto di un ministero (amministrazione centrale) sugli stessi costi sembra escludere il Conto Termico; un bando regionale finanziato con fondi nazionali è un caso grigio. Prudenza: verificare caso per caso con il GSE.

### Iperammortamento 2026
- Legge 199/2025, art. 1, commi 427-436, allegati IV e V (aggiornano i vecchi allegati A e B). Il DL 38/2026 ha tolto il vincolo dei beni prodotti in UE/SEE (resta per i moduli fotovoltaici, che devono essere del registro ENEA lettere b o c).
- Scaglioni per anno: 180% fino a 2,5 mln; 100% da 2,5 a 10 mln; 50% da 10 a 20 mln. Deduzione extracontabile, non credito d'imposta.
- Nessun requisito di risparmio energetico per i beni 4.0 (la vecchia Transizione 5.0 lo richiedeva). Gli impianti a fonti rinnovabili sono ammessi se per autoconsumo e dimensionati fino al 105% del fabbisogno.
- Procedura (DM 7/5/2026): comunicazione preventiva al GSE, conferma entro 60 giorni dall'esito con acconti di almeno il 20%, completamento entro il 15/11/2028 dopo l'interconnessione, poi comunicazioni annuali (20 gennaio e 30 giugno). Perizia asseverata e certificazione contabile per ogni bene, senza soglie.
- Il beneficio si usa dall'anno della comunicazione di completamento, se il bene è entrato in funzione nello stesso anno, e si distribuisce lungo l'ammortamento.
- Dubbi: esclusioni soggettive (autonomi, forfettari, agricoltori a reddito catastale) lette solo su fonti secondarie; non è chiaro se ci sia un tetto complessivo di spesa con chiusura anticipata; non verificato l'effetto IRAP (di solito nessuno); non chiarito ufficialmente se il contributo Sabatini vada sottratto dalla base (prudenza: sì).

### Altre misure
- **Credito R&S:** 10% delle spese di ricerca e sviluppo, massimo 5 mln l'anno, fino al 2031; comunicazioni preventive e consuntive al MIMIT obbligatorie dal 2024. Riguarda spese di ricerca, non l'acquisto di macchinari di produzione: si affianca ai bandi di ricerca (base al netto dei contributi).
- **Credito ZES unica:** Legge 199/2025 commi 438-443, anni 2026-2028, regioni del Sud più Abruzzo, Marche e Umbria; progetti da almeno 200.000 €. È un aiuto di Stato regionale: col bando a fondo perduto si somma solo entro l'intensità massima della Carta degli aiuti per quella zona. Il credito effettivo dipende dal riparto (nel 2025: 75% del richiesto).
- **Credito design e ideazione estetica 2026** (verifica del 5/10/2026): la L. 199/2025, art. 1, commi 925-926, lo porta dal 5% al **10%** per le spese 2026, massimo 2 milioni per impresa, utilizzabile in F24 in **una sola quota annuale**, con un tetto complessivo di **60 milioni** e prenotazione sulla piattaforma MIMIT (DD 3/7/2026, apertura 7/7/2026; poi comunicazione di completamento entro 30 giorni dalla chiusura del periodo d'imposta, con spese almeno pari al 70% di quelle prenotate). Il MIMIT ha comunicato l'**esaurimento dei fondi l'8/7/2026**, dopo 24 ore; le nuove domande restano in coda per un eventuale scorrimento. Quindi non è una misura su cui contare per un cliente oggi: non l'ho inserita come voce separata, l'ho citata nella voce R&S. Se arrivano nuovi fondi, va aggiunta (non esiste una categoria di spesa "design": `ricerca_sviluppo` lo abbinerebbe ai bandi di ricerca, che non c'entrano; da decidere se usare `altro` o aggiungere una categoria).
- **Credito innovazione tecnologica (anche 4.0 e green):** 5% nel 2024-2025, **non prorogato** per il 2026 (pagina MIMIT riporta aliquote solo fino al 2025; EC News concorde).
- **Credito formazione 4.0:** la pagina MIMIT dice "La misura non è più attiva" (ultimo aggiornamento della pagina: dicembre 2022). La formazione era poi entrata come spesa accessoria nella Transizione 5.0, che per i nuovi investimenti dal 2026 è chiusa; l'iperammortamento riguarda solo beni (allegati IV e V e impianti FER), per quanto risulta dalle fonti lette non la formazione. Nessuna misura nazionale automatica per la formazione da inserire.
- **Maggiorazioni R&S Mezzogiorno** (art. 244 DL 34/2020, 25% grandi / 35% medie / 45% piccole): valevano fino al periodo d'imposta 2025 e **non risultano prorogate** per il 2026; la pagina MIMIT non le riporta per il 2026 e le fonti secondarie concordano. Non ho potuto leggere su Normattiva la nota con la scadenza: certezza buona ma non piena. Corretta di conseguenza la voce `credito_rs_2026` (10% ovunque).
- **Nuova Sabatini:** contributo pari agli interessi di un finanziamento a 5 anni (2,75% / 3,575% / 5%), circa il 7,7% / 10,1% / 14,3% del finanziamento. Aiuto in esenzione GBER: col bando sugli stessi beni si somma solo se l'intensità totale resta entro il massimo applicabile.

### Aggiunta del 6/10/2026: Art Bonus, Ecobonus, Sismabonus

**Art Bonus.** Vigente e permanente (DL 83/2014 art. 1, reso stabile dalla L. 208/2015). Credito del 65% delle donazioni in denaro a beni e istituti culturali pubblici e agli enti dello spettacolo ammessi; per le imprese massimo 5 per mille dei ricavi annui; tre quote annuali uguali, in F24 con codice tributo 6842; la parte non usata si riporta senza limiti; non conta per l'IRAP. Il beneficiario deve essere sul portale e comunicare ogni mese le donazioni ricevute.
- **Perché `categorie_spesa: []`:** non è un investimento dell'impresa ma una donazione. Il codice (`cumulabili()` in `app/misure/__init__.py`) propone una misura accanto a un bando solo se hanno categorie di spesa in comune: con l'elenco vuoto l'Art Bonus compare nella pagina "Misure nazionali" ma **non viene mai abbinato ai bandi** (provato con uno script: su un bando con tutte le categorie energia/edilizia/macchinari non esce). `con_fondo_perduto: si` solo perché il campo è obbligatorio: non tocca le spese dei bandi.
- Da verificare: decorrenza della prima quota (anno della donazione o successivo), cumulo con la deduzione della stessa donazione (FAQ del portale non lette), casi di enti ecclesiastici. Una proposta di legge del 2026 vuole estenderlo a musei privati, ETS ed enti ecclesiastici: non è ancora legge.

**Ecobonus per le imprese.** Vigente. Le aliquote 2025-2027 le ha riscritte la L. 207/2024 (comma 55): aliquota unica per tutti gli interventi, sparito il 65%. La L. 199/2025 (comma 22, numero da fonti secondarie) ha tenuto per il 2026 le aliquote del 2025: **36%, 50% solo per l'abitazione principale** di chi ne è proprietario o titolare di un diritto reale. Un'impresa quindi ha sempre il **36%** (30% per le spese 2027). Per i titolari di reddito d'impresa vale su qualunque immobile posseduto o detenuto (strumentale, bene merce, patrimonio), secondo l'Agenzia. 10 quote annuali; nessuna domanda preventiva; scheda ENEA entro 90 giorni dalla fine lavori; limiti di detrazione per intervento invariati (100.000 € riqualificazione globale, 60.000 € involucro/infissi/schermature/solare termico, 30.000 € impianti di riscaldamento, 15.000 € building automation). Escluse le caldaie solo a combustibili fossili. Cessione del credito e sconto in fattura: vietati dal 17/2/2023, salvo casi transitori residuali. Per i lavori iniziati dal 4/2/2026 valgono i nuovi requisiti tecnici del D.Lgs. 5/2026 (pompe di calore, ibridi, biomassa).
- **Cumulo:** con un bando a fondo perduto regionale o camerale la detrazione si calcola sulla parte di spesa non coperta dal contributo, totale entro il 100% (fonti secondarie concordi; il DM 6/8/2020 non ha un articolo sul cumulo: riferimento puntuale da verificare). **Con il Conto Termico 3.0 è alternativo**: il DM 7/8/2025 art. 17 esclude il Conto Termico se ci sono altri incentivi statali, e il GSE ci include le detrazioni. Per un'impresa il Conto Termico (25-65% in pochi anni) di solito rende di più del 36% in 10 anni; l'ecobonus resta utile quando il Conto Termico non c'è (fondi finiti, edificio non terziario per il Titolo II, intervento non ammesso).
- Nella frase della campagna (`frase_cumulo`) esce una sola misura, la più vantaggiosa: con energia/edilizia resta il Conto Termico, quindi l'ecobonus non viene presentato come sommabile al Conto Termico.
- Da verificare: se per l'IRES la quota annua non capiente si perde o si riporta; obbligo di bonifico "parlante" per le imprese.

**Sismabonus.** Vigente: art. 16 commi 1-bis e seguenti DL 63/2013, nuovo comma 1-septies.1 (L. 207/2024) con aliquote fisse; per il 2026 **36%** (50% abitazione principale), 30% nel 2027. Vale per IRPEF e IRES, su edifici abitativi e **adibiti ad attività produttive** nelle zone sismiche 1, 2 e 3; massimo 96.000 € di spesa per unità immobiliare e per anno; 10 quote annuali (DL 39/2024 art. 4-bis). Inserito come `sismabonus_imprese_2026` con `categorie_spesa: [opere_edili_impianti]`. Da verificare: tempi dell'asseverazione del rischio sismico per gli interventi 2026.

**Bonus barriere architettoniche 75%** (art. 119-ter DL 34/2020): valeva per le spese fino al 31/12/2025 e non è stato prorogato (ANCE e varie fonti secondarie concordi; nessuna pagina dell'Agenzia letta che lo dica espressamente). Non inserito. Dal 2026 l'eliminazione delle barriere rientra nelle detrazioni ordinarie per le ristrutturazioni (36%/50%), che però sono per i contribuenti IRPEF sulle abitazioni: per le società non c'è una misura equivalente (da verificare).

## Come stimare il beneficio cumulato con un bando a fondo perduto

Esempio: **macchinario 4.0 da 100.000 €** (IVA esclusa), comprato da una piccola società di capitali in utile (IRES 24%), con un **bando regionale che dà il 40% a fondo perduto** sullo stesso bene.

**Passo 1 - il bando:** 40% di 100.000 = **40.000 €** di contributo.

**Passo 2 - l'iperammortamento si calcola sulla parte non coperta dal bando** (comma 431: base al netto dei contributi ricevuti per gli stessi costi):
- base = 100.000 - 40.000 = 60.000 €
- maggiorazione = 60.000 × 180% = 108.000 € di costo in più deducibile
- risparmio d'imposta = 108.000 × 24% = **25.920 €**, distribuito sugli anni di ammortamento

**Passo 3 - controllo del tetto:** 40.000 + 25.920 = 65.920 €, meno del costo di 100.000 €: cumulo ammesso.

**Risultato:** circa **66% del costo** torna all'impresa (40% subito o quasi, col bando; 26% negli anni, con le tasse). Senza bando l'iperammortamento da solo darebbe 100.000 × 180% × 24% = 43.200 € (43%): il bando aggiunge quindi "solo" circa 22,7 punti netti, non 40, perché riduce la base dell'iperammortamento.

Nota onesta: il contributo a fondo perduto è un contributo in conto impianti e concorre al reddito (o riduce il costo ammortizzabile). In entrambi i casi l'impresa deduce 40.000 € di ammortamenti in meno, quindi paga circa 9.600 € di imposte in più negli anni. Il valore netto di tasse del bando è circa 30.400 €. Nella plancia conviene mostrare il calcolo lordo (66%) con questa avvertenza.

**Formula generale per la plancia (bene ammesso a iperammortamento, primo scaglione):**
`beneficio = B + (C - B) × M × t`, con C = costo, B = contributo del bando, M = maggiorazione dello scaglione (1,8 / 1,0 / 0,5), t = aliquota (0,24 per le società di capitali). Condizione: `B + (C - B) × M × t ≤ C`.

### Casi in cui il cumulo non c'è o è ridotto

| Caso | Cosa succede | Esempio su 100.000 € |
|---|---|---|
| Il bando vieta espressamente di cumulare con altre agevolazioni sugli stessi costi (succede in alcuni bandi de minimis o camerali) | vale la regola del bando: o il bando o l'iperammortamento | scegliere: 40.000 € (bando) oppure 43.200 € (iper) |
| Intervento energetico ammesso al Conto Termico (es. pompa di calore, isolamento) | Conto Termico e iperammortamento non si cumulano sulle stesse spese (art. 17 DM, posizione GSE) | scegliere: CT fino a 65.000 € per una piccola impresa, oppure iper (solo se il bene rientra negli allegati o tra gli impianti FER per autoconsumo) |
| Bando di un ministero + Conto Termico | escluso il Conto Termico (incentivo statale) | resta solo il bando (e l'eventuale iper) |
| Bando regionale + Conto Termico | ammesso entro l'intensità massima del Conto Termico (65% piccola impresa) | bando 40% + CT al massimo 25% = 65.000 € in tutto |
| Bando 40% + Nuova Sabatini sullo stesso bene | entrambi aiuti di Stato: il totale non può superare l'intensità massima applicabile (la più alta tra le misure cumulate) | se il massimo del bando è 40%, non c'è spazio per la Sabatini sugli stessi costi; la Sabatini si può usare sulla parte non finanziata dal bando, da verificare caso per caso |
| Bando 40% + credito ZES sullo stesso bene | stesso limite: intensità della Carta per la zona e la dimensione | piccola impresa in zona al 60%: ZES al massimo 20.000 € (prima del riparto) |
| Bene usato, non interconnesso o non presente negli allegati IV e V | niente iperammortamento | resta solo il bando |
| Impresa in perdita o forfettaria | l'iperammortamento non rende subito o non spetta | resta solo il bando (e i crediti d'imposta, utilizzabili anche in perdita) |
| Investimenti oltre 2,5 milioni l'anno | lo scaglione scende al 100% e poi al 50% | la parte oltre 2,5 mln vale il 24%, poi il 12% |

## Sintesi

- Tutte e cinque le misure inserite nel YAML risultano in vigore a ottobre 2026, verificate su pagine ufficiali: Conto Termico 3.0, iperammortamento 2026, credito R&S, credito ZES unica, Nuova Sabatini.
- Iperammortamento: Legge 199/2025, art. 1, commi 427-436; maggiorazione del 180% / 100% / 50% per scaglioni annuali fino a 20 mln; investimenti dal 1/1/2026 al 30/9/2028; procedura su piattaforma GSE con perizia e certificazione. Vale circa il 43% della spesa per una società in utile.
- Conto Termico 3.0: dal 25% al 65% a fondo perduto per le imprese, con richiesta preliminare prima dei lavori. Non si cumula con l'iperammortamento né con altri contributi statali; si cumula con bandi regionali entro il 65%.
- Il cumulo bando + iperammortamento è ammesso, ma l'iperammortamento si calcola sulla parte non coperta dal bando: bando al 40% + iper = circa 66% lordo su un macchinario da 100.000 €, non 83%.
- Le misure che sono aiuti di Stato (ZES, Sabatini, Conto Termico) si sommano al bando solo entro le intensità massime europee: spesso lo spazio è poco.
- Verificati il 5/10/2026: credito formazione 4.0 non più attivo; innovazione tecnologica non prorogata; maggiorazioni R&S al Sud finite nel 2025; credito design 2026 al 10% esistente ma con i 60 milioni già esauriti (in coda per scorrimento).
- Restano da verificare: testo letterale dei commi 427-436 e 925-926 su Normattiva, percentuale di riparto ZES 2026, eventuali nuovi fondi per il credito design (scorrimento), scadenza dell'art. 244 DL 34/2020 letta sul testo ufficiale.

## Conseguenze per Bandi Radar

- Le misure stanno in `app/misure/misure.yaml`, separate dal registro delle fonti: non sono bandi, cambiano raramente e vanno ricontrollate a mano almeno ogni trimestre e a ogni Legge di bilancio (campo `fonte_verificata_il`).
- Il calcolo del cumulo nella scheda di un bando deve usare la base netta (formula sopra) e mostrare sempre l'avvertenza sui casi di non cumulabilità; mai sommare semplicemente le percentuali.
- Da osservare con il sistema di raccolta (senza IA): le pagine news del GSE sul Conto Termico (sospensioni, contatori) e la pagina MIMIT dell'iperammortamento, per accorgersi di cambi di regole o chiusure.

## Aggiunta del 6/10/2026: incentivi all'assunzione, Fondo di Garanzia PMI, maxi-deduzione dei nuovi assunti

**Domanda:** il rapporto sui bandi più discussi di ottobre (`bandi_discussi_2026-10.md`, nazionali n. 21 e 25) segnala come mancanti tra le misure nazionali i bonus assunzioni Giovani, Donne e ZES e il Fondo di Garanzia PMI; in più va verificata la maxi-deduzione del costo dei nuovi assunti (120%/130%). Sono vigenti al 6/10/2026? Le domande INPS sono ancora aperte?

**Metodo:** ricerca web limitata a inps.it, agenziaentrate.gov.it, fiscooggi.it, fondidigaranzia.it, mimit.gov.it. Le pagine notizie dell'INPS si caricano con JavaScript: le ho scaricate con `curl` (User-Agent di Bandi Radar) e ho tolto i tag con Python. Le circolari INPS 55, 56, 57 del 14/05/2026 e la circolare 1/E 2025 dell'Agenzia delle Entrate le ho lette per intero, estratte a testo con `pypdf` dentro il container `raccolta`.

### URL visti davvero

| Fonte | URL | Cosa conferma | Giudizio |
|---|---|---|---|
| INPS, notizia "Bonus INPS 2026: al via le domande" (30/06/2026) | https://www.inps.it/it/it/inps-comunica/notizie/dettaglio-news-page.news.2026.06.bonus-inps-2026-al-via-le-domande-per-giovani-donne-e-zes.html | assunzioni a tempo indeterminato dal 1/1 al 31/12/2026; esonero 100%; messaggi 1966, 1968, 1970 dell'11/06/2026; Portale delle Agevolazioni; Bonus ZES: over 35 disoccupati da 24 mesi, max 10 dipendenti, 10 regioni | sì |
| INPS, notizia "domande entro il 30 settembre" (23/07/2026) | https://www.inps.it/it/it/inps-comunica/notizie/dettaglio-news-page.news.2026.07.bonus-giovani-donne-e-zes-domande-entro-il-30-settembre.html | messaggio 2451/2026: il termine del 30/09/2026 riguarda **solo** i bonus del decreto Coesione (DL 60/2024 artt. 22-24, assunzioni 1/9/2024 - 31/12/2025); dal 1/10 niente nuove domande | sì |
| INPS, comunicato stampa 14/05/2026 (PDF) | https://www.inps.it/content/dam/inps-site/it/scorporati/comunicati-stampa/2026/05/Allegati/4095_Cs_decreto_lavoro.pdf | DL 62/2026; circolari 55 (Giovani), 56 (ZES), 57 (Donne); tetti 500/650/800 euro; esclusi PA, domestico, apprendistato | sì |
| INPS, circolare 55 del 14/05/2026 (PDF letto per intero) | https://www.inps.it/content/dam/inps-site/it/scorporati/circolari-e-messaggi/2026/05/Circolare_15258/Allegati/16770_Circolare-numero-55-del-14-05-2026.pdf | Bonus Giovani: art. 2 DL 62/2026; under 35 svantaggiati (12 mesi) o molto svantaggiati (24 mesi); 500 euro, 650 nella ZES; incremento occupazionale netto; spesa 109,7 mln 2026; niente trasformazioni; non cumulabile con altri esoneri, cumulabile con la maxi-deduzione (L. 207/2024 c. 399-400); domanda anche prima dell'assunzione con 10 giorni per assumere | sì |
| INPS, circolare 56 del 14/05/2026 (PDF letto per intero) | https://www.inps.it/content/dam/inps-site/it/scorporati/circolari-e-messaggi/2026/05/Circolare_15259/Allegati/16771_Circolare-numero-56-del-14-05-2026.pdf | Bonus ZES: art. 3 DL 62/2026; 650 euro per 24 mesi; spesa 26 mln 2026, 60 nel 2027, 34 nel 2028; GBER; niente Decontribuzione Sud insieme; compatibile con la maxi-deduzione | sì |
| INPS, circolare 57 del 14/05/2026 (PDF letto per intero) | https://www.inps.it/content/dam/inps-site/it/scorporati/circolari-e-messaggi/2026/05/Circolare_15260/Allegati/16772_Circolare-numero-57-del-14-05-2026.pdf | Bonus Donne: art. 1 DL 62/2026; 650 euro, 800 per residenti ZES; 24 mesi (12 per alcune categorie); spesa 26,5 mln 2026 | sì |
| INPS, comunicato stampa 31/07/2026 (PDF) | https://www.inps.it/content/dam/inps-site/it/scorporati/comunicati-stampa/2026/07/Allegati/4156_CS_bonus-assunzioni-e-stabilizzazioni.pdf | misure collegate: madri di almeno 3 figli (L. 199/2025 c. 210-213, circ. 82/2026, 8.000 euro l'anno); trasformazioni di giovani dal 1/8 al 31/12/2026 (art. 4 DL 62/2026, circ. 72/2026, msg 2518/2026); decreto convertito il 25/06/2026 | sì |
| Agenzia Entrate, circolare 1/E del 20/01/2025 (PDF letto per intero) | https://www.agenziaentrate.gov.it/portale/documents/20143/8410815/Circolare_n_1_del_20_01_2025.pdf/7d236acf-dd08-2d3f-dd3a-58717c71b1aa | maxi-deduzione: art. 4 D.Lgs. 216/2023; proroga L. 207/2024 commi 399-400 per i periodi d'imposta **2025, 2026 e 2027**; 20% o 30% (allegato 1); minore tra costo dei nuovi assunti e aumento del costo del personale (voci B9); esclusi liquidazione e forfettari; 365 giorni di attività; acconti senza maggiorazione | sì |
| Agenzia Entrate, comunicato stampa 20/01/2025 | https://www.agenziaentrate.gov.it/portale/-/comunicato-stampa-del-20-gennaio-2025-nuove-assunzioni | proroga fino al 2027, categorie al 30% | sì |
| FiscoOggi (Agenzia Entrate), "Maxi-deduzione nuove assunzioni" | https://www.fiscooggi.it/portale/-/maxi-deduzione-nuove-assunzioni-l-agenzia-fornisce-indicazioni | stesso contenuto della circolare | sì |
| Fondo di garanzia, "Prorogate per il 2026 le modalità di funzionamento" (2/1/2026) | https://www.fondidigaranzia.it/prorogate-per-il-2026-le-modalita-di-funzionamento-del-fondo-di-garanzia/ | art. 14 c. 1 DL 200/2025: regole 2025 valide per tutto il 2026; 80% investimenti, startup, PMI innovative, Sabatini, importo ridotto, microcredito; 50% liquidità | sì |
| Fondo di garanzia, "Dal 1° gennaio al via la riforma" (2024) | https://www.fondidigaranzia.it/dal-1-gennaio-al-via-la-riforma-del-fondo-di-garanzia-per-le-pmi/ | 5 mln garantiti per impresa; commissioni: micro esenti, piccole 0,5%, medie 1%, small mid-cap 1,25%; fascia di rating 5 esclusa; percentuali mid-cap 40%/30% | sì, ma del 2024: commissioni e mid-cap da verificare per il 2026 |
| Fondo di garanzia, home e "Conosci il Fondo" | https://www.fondidigaranzia.it/conosci-il-fondo/ | beneficiari (PMI, professionisti), accesso solo tramite banca o confidi, Consiglio di gestione due volte a settimana; dati gen-giu 2026 | sì |
| MIMIT, pagina Fondo di garanzia per le PMI (aggiornata il 21/09/2026) | https://www.mimit.gov.it/it/incentivi/fondo-di-garanzia-per-le-pmi | L. 662/1996 art. 2 c. 100 lett. a); esclusi finanziari e assicurativi; niente garanzie aggiuntive sulla parte coperta | sì |
| Fonti secondarie viste solo nei risultati di ricerca (Investireoggi, Leggioggi, BibLus, IRDE, Studio Giaquinta) | — | coerenti con le fonti ufficiali; non usate per i dati | sì (secondarie) |

### Esito

- **Incentivi all'assunzione 2026 (Bonus Giovani, Donne, ZES)**: **aperti**. Valgono per le assunzioni a tempo indeterminato dal 1/1 al 31/12/2026 (DL 62/2026); domande sul Portale delle Agevolazioni INPS dall'11/06/2026, fino a esaurimento dei fondi annuali. Inseriti come una sola misura `incentivi_assunzione_2026`, tipo `decontribuzione`, spese `personale`.
- **Bonus Giovani, Donne e ZES del decreto Coesione** (assunzioni 1/9/2024 - 31/12/2025): **chiusi**. Il 30/09/2026 indicato nel rapporto è il termine delle domande per queste assunzioni passate, non per i bonus 2026. Inseriti tra le chiuse (`incentivi_assunzione_coesione`) con la nota.
- **Fondo di Garanzia PMI**: **aperto**, permanente; percentuali 2025 prorogate per tutto il 2026. Tipo `garanzia`. Beneficio non espresso in percentuale della spesa (è una garanzia, non un contributo).
- **Maxi-deduzione dei nuovi assunti 120%/130%**: **vigente nel 2026** (proroga per 2025-2027 della L. 207/2024). Inserita tra le aperte (`maxi_deduzione_assunzioni`), tipo `deduzione_maggiorata`. Le circolari INPS 2026 confermano che si somma ai bonus contributivi.

### Da verificare

- Estremi della legge di conversione del DL 62/2026 (convertito il 25/06/2026) ed eventuali modifiche agli artt. 1-3: le circolari 55-57 sono di maggio, prima della conversione.
- Termine finale delle domande INPS per le assunzioni 2026 (per i bonus 2024-2025 è stato fissato un anno dopo); stato dei fondi annuali (Bonus ZES e Donne circa 26 milioni ciascuno nel 2026).
- Ammissione dei datori non imprenditori (studi professionali) ai bonus 2026, scritta nelle circolari? Non l'ho trovata in modo esplicito.
- Fondo di garanzia: commissioni e percentuali small mid-cap nel 2026 (fonte del 2024); accesso delle imprese agricole.
- Maxi-deduzione: conteggio degli apprendisti; testo dei commi 399-400 su Normattiva (letto solo tramite la circolare 1/E).
