# Misure nazionali automatiche o a sportello, da affiancare ai bandi

**Data:** 5 ottobre 2026

**Domanda:** quali misure nazionali "automatiche" o a sportello permanente danno benefici sugli investimenti delle imprese, sono in vigore a ottobre 2026 e si possono sommare ai bandi a fondo perduto? In primo luogo Conto Termico 3.0 e iperammortamento 2026; poi, se verificate, poche altre misure generali dello stesso tipo. Esito strutturato in `app/misure/misure.yaml`.

**Metodo:** ricerca web limitata il più possibile a siti ufficiali (gse.it, mimit.gov.it, agenziaentrate.gov.it, gazzettaufficiale.it, normattiva.it) e lettura diretta delle pagine. Due testi letti per intero: le **Regole Applicative del Conto Termico 3.0** (PDF GSE, 2,7 MB) e il **DM MIMIT-MEF 7 maggio 2026** sull'iperammortamento (PDF MIMIT), estratti a testo con `pypdf` dentro il container `app` perché lo strumento web non legge i PDF compressi. Le fonti secondarie (commercialisti, associazioni) le ho usate solo dove il testo ufficiale non era raggiungibile, e sono indicate come tali.

**Limiti:**
- **Il testo della Legge 199/2025 (commi 427-436 e 438-443) non l'ho letto direttamente**: Normattiva e Gazzetta Ufficiale mostrano solo l'inizio dell'articolo 1 (che ha centinaia di commi). Numero di legge, commi, scaglioni e periodo sono confermati dal MIMIT e dal DM attuativo; le esclusioni soggettive, il testo del comma 431 sul cumulo e la modifica del DL 38/2026 (via il vincolo "prodotto in UE") vengono da fonti secondarie concordi (Confindustria Toscana, ANCE, iperammortamenti.it e altre).
- Le FAQ GSE (assistenza.clienti.gse.it) si caricano con JavaScript e non si leggono senza browser: la posizione del GSE sul cumulo Conto Termico + iperammortamento è riportata da fonti secondarie che la citano, ed è coerente con l'art. 17 del DM che ho letto.
- Percentuale di riparto del credito ZES per il 2026, maggiorazioni R&S Mezzogiorno 2026, elenco preciso dei settori esclusi ZES e vincoli di mantenimento: non verificati, scritti come "da verificare".
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

## Esito per misura

| Misura | Vigente a ottobre 2026 | Nel file YAML | Note |
|---|---|---|---|
| Conto Termico 3.0 | sì | sì, `aperto` | portale sospeso 3/3 - 13/4/2026; risorse annuali da tenere d'occhio |
| Iperammortamento 2026 | sì | sì, `aperto` | investimenti 1/1/2026 - 30/9/2028 |
| Credito R&S 10% | sì (fino al 2031) | sì, `aperto` | spese di ricerca, non macchinari |
| Credito ZES unica 2026-2028 | sì | sì, `aperto` | finestra 2026 chiusa il 30/5/2026; prossima nel 2027 |
| Nuova Sabatini | sì | sì, `aperto` | sportello fino a esaurimento |
| Credito beni strumentali 4.0 / Transizione 5.0 | no per investimenti 2026 | no | sostituiti dall'iperammortamento |
| Credito innovazione tecnologica e transizione 4.0 | no (5% fino al 2025) | no | |
| Credito design 2026 | non chiaro | no | MIMIT indica prenotazione dal 7/7/2026 con plafond 60 mln: da verificare |
| Credito formazione 4.0 | non chiaro (non risulta rinnovato) | no | da verificare |
| Maggiorazioni R&S Mezzogiorno | non chiaro per il 2026 | no | da verificare |

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
- **Nuova Sabatini:** contributo pari agli interessi di un finanziamento a 5 anni (2,75% / 3,575% / 5%), circa il 7,7% / 10,1% / 14,3% del finanziamento. Aiuto in esenzione GBER: col bando sugli stessi beni si somma solo se l'intensità totale resta entro il massimo applicabile.

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
- Restano da verificare: testo letterale dei commi 427-436 su Normattiva, percentuale di riparto ZES 2026, credito design 2026, credito formazione, maggiorazioni R&S al Sud.

## Conseguenze per Bandi Radar

- Le misure stanno in `app/misure/misure.yaml`, separate dal registro delle fonti: non sono bandi, cambiano raramente e vanno ricontrollate a mano almeno ogni trimestre e a ogni Legge di bilancio (campo `fonte_verificata_il`).
- Il calcolo del cumulo nella scheda di un bando deve usare la base netta (formula sopra) e mostrare sempre l'avvertenza sui casi di non cumulabilità; mai sommare semplicemente le percentuali.
- Da osservare con il sistema di raccolta (senza IA): le pagine news del GSE sul Conto Termico (sospensioni, contatori) e la pagina MIMIT dell'iperammortamento, per accorgersi di cambi di regole o chiusure.
