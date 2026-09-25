# Revisione schede Sonnet – gruppo B (4231, 358, 3055, 4136, 4383)

*Revisione del 25/09/2026. Unica fonte di confronto: il testo in `scheda_X.txt`, cioè quello che Sonnet aveva davanti. Nessun controllo su internet.*

## Sintesi

- **Sonnet non ha inventato nulla.** Nelle 5 schede non ho trovato un solo valore assente dai documenti: date, importi, percentuali e codici ATECO corrispondono al testo. Anche lo stato (aperto, chiuso, in arrivo) rispetto al 25/09/2026 è sempre giusto, e la regola "NON PER IMPRESE" è applicata bene (3055).
- **Il 4.250 € non è un campo del catalogo frainteso.** Nel 4231 la pagina di incentivi.gov.it riporta proprio "Agevolazione concedibile (min-max): Fino a 4.250 €". Nel 4199 la stessa cifra si ottiene dal testo del bando (2 giovani × 2.000 € + 250 € di premio): il portale però la mette sotto "Spesa ammessa". Nel file di riferimento `costo_max` è la **spesa ammessa** massima (99.999.998.000 = "nessun limite"), non il contributo. Che la cifra sia uguale in due bandi è una coincidenza plausibile, ma nel 4231 non si può verificare: manca il bando della Camera.
- **Gli errori veri sono omissioni e valori ambigui, non invenzioni.** 4136 (IRFIS): `contributo_massimo` 400.000 e `percentuale` 100 contano insieme prestito e fondo perduto, mentre il fondo perduto è solo il 40%. Mancano anche la fideiussione personale dei soci e la durata del prestito. 4383 (Bari): manca la regola che le spese valgono solo se fatte **dopo** la concessione. Per un cliente sono entrambi errori pericolosi.
- **Il limite principale è il materiale in ingresso.** Su 2 bandi su 5 (4231, 358) Sonnet aveva solo una pagina di riepilogo, senza il bando ufficiale. Sugli altri 3, dal 50% al 90% del testo era inutile: moduli vuoti, un F24 di prova, whistleblowing, menù del sito, un bando del 2020.
- **Il prompt va chiarito in 5 punti**: `ente` (chi paga oppure chi gestisce), `territorio`, come trattare le agevolazioni miste, premi aggiuntivi nel massimale, da quando valgono le spese.
- **Voti: 4231 = 3, 358 = 4, 3055 = 5, 4136 = 3, 4383 = 4.** Una scheda è pronta così com'è (3055, che però va solo scartata), le altre vanno ritoccate. Il sistema è vicino: le correzioni riguardano soprattutto raccolta e prompt, non il modello.

Legenda: **ERRATO** = contraddetto dai documenti · **INVENTATO** = non presente nei documenti · **MANCANTE** = presente ma lasciato fuori · **IMPRECISO** = giusto ma incompleto o fuorviante · **FONTE SBAGLIATA** = la citazione non corrisponde. ⚠ = pericoloso per un cliente.

---

## 4231 – CCIAA Pistoia-Prato, Formazione Scuola-Lavoro 2026 (da incentivi.gov.it)

**Materiale in ingresso.** Solo la pagina del catalogo incentivi.gov.it: circa 2/3 sono menù ed etichette del glossario, cioè un centinaio di voci come "Brevetto", "ZES" o "Credito d'imposta" che non descrivono il bando. Nessun allegato. Il bando della Camera, indicato nel campo "Sito di riferimento" (`link_ente` nel catalogo: `ptpo.camcom.it/.../formazione-scuola-lavoro-contributi-2026`), non è stato scaricato. Nell'annuncio anche la "Data di pubblicazione: 2026-10-19" è sbagliata: è la data di apertura (campo `data` del catalogo), che la raccolta ha preso per data di pubblicazione.

**Il caso 4.250 €.**
- Pagina 4231: "Spesa ammessa (min-max): Fino a 99.999.998.000 €" e "**Agevolazione concedibile (min-max): Fino a 4.250 €**". Il valore è scritto nel documento, quindi non è inventato, e Sonnet ha scelto il campo giusto (l'agevolazione, non la spesa). L'avvertenza lo spiega.
- Riferimento catalogo 4231: `costo_max` = "99999998000", cioè la spesa ammessa. Il catalogo strutturato non contiene l'agevolazione concedibile: non può quindi né confermare né smentire il 4.250.
- Pagina 4199: "Spesa ammessa: Fino a 4.250 €", "Agevolazione concedibile: --". Qui è il portale a mettere la cifra nel campo sbagliato. Il valore però coincide con il contributo massimo ricavabile dal testo della stessa pagina (2 × 2.000 + 250 di premio legalità), quindi il `contributo_massimo` 4250 del 4199 è corretto nel merito. L'unica imprecisione è la fonte e la frase in `spese_ammesse` ("Oneri diversi di gestione, fino a 4.250 euro").
- Conclusione: nessun equivoco su `costo_max`. Per il 4231 resta un rischio che non si può verificare: la cifra potrebbe essere stata ricopiata male sul portale, ed è identica a quella di un altro bando camerale dello stesso tipo. Per stabilirlo serve il bando della Camera, che la raccolta non ha scaricato.

| Campo | Problema | Tipo | Pericolo |
|---|---|---|---|
| url | È la pagina del catalogo, non quella ufficiale della Camera, anche se il link è presente ("Sito di riferimento", troncato) | IMPRECISO (limite della raccolta) | medio |
| contributo_massimo 4250 | Valore scritto nella pagina ("Agevolazione concedibile"), ma non verificabile sul bando | corretto, da verificare | medio |
| cosa_finanzia | Omette "l'inserimento in azienda di risorse umane e di nuove figure professionali" (sezione "Cos'è") | MANCANTE (lieve) | no |
| sintesi | "la pagina non chiarisce in modo coerente le spese ammesse" è un commento sulla fonte, non un contenuto per il cliente: il posto giusto sono le avvertenze | IMPRECISO (lieve) | no |
| requisiti | Solo la sede. Il resto non c'era: giusto lasciarlo fuori | ok | – |
| avvertenze | "le risorse potrebbero esaurirsi prima della scadenza": non si sa se il bando sia a sportello o a graduatoria, quindi è una supposizione. L'avvertenza sugli orari ripete la sintesi | IMPRECISO (lieve) | no |
| fonti | Manca la fonte di `codici_ateco_esclusi` (vuoto, accettabile) | – | – |

Regole del prompt: rispettate. Date, importi e valori ammessi sono corretti; `stato` = `in_arrivo` è giusto (apre il 19/10). La pagina elenca insieme "Attivo / Chiuso / In Arrivo" senza dire quale vale: Sonnet ha giustamente ricavato lo stato dalle date. Nessuna invenzione.

**Voto: 3/5.** Sonnet ha fatto il massimo con quello che aveva, ma la scheda non basta a un commercialista: mancano spese ammesse, percentuale, criteri di assegnazione e requisiti. È un segnale da approfondire, non una scheda.

---

## 358 – CCIAA Padova, mamme imprenditrici 2026 (notizia di Unioncamere Veneto)

**Materiale in ingresso.** È una notizia di Unioncamere, non la pagina della Camera di Padova. Il link "BANDO E MODULISTICA ONLINE" non è stato seguito: nessun allegato. Circa metà del testo è la barra laterale con altre notizie. Tuttavia la notizia contiene date, importi e beneficiari chiari.

| Campo | Problema | Tipo | Pericolo |
|---|---|---|---|
| url | Pagina di Unioncamere, non della Camera di Padova | IMPRECISO (limite della raccolta) | basso |
| titolo | Tiene il prefisso "Padova:" aggiunto da Unioncamere; il titolo del bando è senza | IMPRECISO (lieve) | no |
| spese_ammesse | Correttamente dichiarate "non specificate"; l'investimento minimo di 2.000 € è riportato | ok | – |
| sintesi / avvertenze | Manca la precompilazione dal 21/06/2026, irrilevante perché il bando è chiuso. "Soli 60.000 euro" è un giudizio non necessario | lieve | no |
| fonti | `tema` = "altro" senza fonte (regola 3: un campo senza fonte dovrebbe essere null) | FONTE mancante (lieve) | no |

Tutti i valori controllati corrispondono al testo: apertura 29/06, scadenza 24/07, 50%, 1.000–5.000 €, MPMI, sede in provincia di Padova, figli sotto i sei anni, piattaforma RESTART. `stato` = `chiuso` è corretto rispetto al 25/09/2026.

**Voto: 4/5.** Corretta e chiara. Resta il limite della fonte secondaria senza bando ufficiale. Essendo chiusa, oggi serve solo come storico.

---

## 3055 – Finpiemonte, contributi a soggetti pubblici (prova "NON PER IMPRESE")

**Materiale in ingresso.** Circa 150.000 caratteri (stima 40–45 mila token, il prompt più costoso del gruppo) per un bando **chiuso il 22/10/2020** e rivolto a enti pubblici. Lo diceva già la prima riga della pagina ("Chiuso", "In vigore dal 24/08/2020 al 22/10/2020"). Inoltre l'allegato "Modalità di rendicontazione" è stato scaricato due volte, "Allegato 5 FAC SIMILE DOMANDA" e l'xls sono vuoti, e "Allegato N° 8" è elencato nella pagina ma non è stato scaricato.

| Campo | Problema | Tipo | Pericolo |
|---|---|---|---|
| avvertenze | "NON PER IMPRESE:" all'inizio, con elenco dei beneficiari preso dalla pagina: corretto | ok | – |
| ente | "Finpiemonte S.p.A." è il gestore; chi finanzia è la Regione Piemonte (DGR 11-1667). Il prompt però non dà questa regola: sta solo in SCHEDA_BANDO.md | IMPRECISO (lieve) | no |
| stato | `null` come chiede la regola 9, ma "chiuso" sarebbe stato utile e certo | scelta del prompt | no |
| fonti | `{}`: coerente con la regola 9 | ok | – |

**Voto: 5/5** rispetto al compito: il bando è riconosciuto e scartato bene. Il problema è a monte: una pagina chiusa da sei anni non doveva arrivare alla fase delle schede, e tanto meno con 13 allegati.

---

## 4136 – IRFIS FinSicilia, Ciclone Harry e frana di Niscemi

**Materiale in ingresso.** L'avviso (725 righe) e la scheda prodotto (114) sono completi, non troncati: l'avviso arriva fino all'art. 14 e alla data "Palermo, 29/04/2026". Il resto, circa 1.100 righe su 2.000, sono moduli da compilare: business plan, due perizie, DSAN, elenco fatture. Utili al cliente dopo, inutili per la scheda. "WHISTLEBLOWING" è un documento vuoto preso dal menù in alto del sito. Il testo dei PDF ha intestazioni spezzate ("F / ONDO S / ICILIA") ma è leggibile.

| Campo | Problema | Tipo | Pericolo |
|---|---|---|---|
| contributo_massimo 400000 | 400.000 € è il massimo dell'**investimento finanziabile** a carico del Fondo (avviso art. 6), di cui il 60% è prestito da restituire e il 40% fondo perduto. Il fondo perduto massimo è 160.000 €. La sintesi spiega la ripartizione, ma il numero da solo, nei filtri del catalogo o nell'abbinamento, fa credere a 400.000 € di contributo | IMPRECISO | ⚠ alto |
| percentuale 100 | "Fino al 100% della spesa ammissibile" è scritto, ma comprende il prestito. La quota a fondo perduto è il 40% | IMPRECISO | ⚠ alto |
| requisiti | Mancano la **fideiussione personale dei soci** (art. 6 e scheda prodotto, "Garanzie"), la valutazione del **merito creditizio** prospettico (art. 6), la **polizza contro i rischi catastrofali** L. 213/2023 (dichiarazione 30), la regolarità contributiva (dich. 29), il fatto che si può presentare **una sola domanda** (art. 8) e la conclusione degli investimenti entro **36 mesi** (art. 6.1) | MANCANTE | ⚠ alto (la fideiussione dei soci cambia la decisione del cliente) |
| sintesi | Mancano le condizioni del prestito: **tasso zero, fino a 15 anni con al massimo 3 di preammortamento, rate trimestrali** (art. 6), e l'erogazione a stato avanzamento lavori (scheda prodotto) | MANCANTE | medio |
| ente | "IRFIS ... (soggetto gestore, per conto della Regione Siciliana)": per SCHEDA_BANDO.md l'ente è chi finanzia (Regione Siciliana) e il gestore va nella sintesi | IMPRECISO | basso |
| avvertenze (de minimis) | Giusto segnalare il limite di 300.000 €. Però "probabilmente solo la componente equivalente-sovvenzione" è un ragionamento di Sonnet, non un testo del bando. Inoltre la scheda prodotto cita un'alternativa ("ovvero art. 50 GBER", aiuti per calamità naturali) che l'avvertenza ignora | IMPRECISO | medio |
| avvertenze | "alcuni moduli di domanda/rendicontazione risultano vuoti": falso, l'unico vuoto è WHISTLEBLOWING | ERRATO (lieve) | no |
| tema | "altro": difendibile ("investimenti" sarebbe altrettanto giusto); manca un tema per calamità e ricostruzione | – | no |
| stato / scadenza | `aperto`, `null` corretti: sportello senza data di chiusura, spiegato nella sintesi. Sarebbe stato utile avvertire che lo sportello è aperto dal 12/05 e le risorse vanno verificate | lieve | medio |

Regole del prompt: formato, valori ammessi e fonti sono corretti; le citazioni degli articoli corrispondono (art. 5, 6, 6.1, 8.1). Nessuna invenzione, a parte la frase sul de minimis.

**Voto: 3/5.** I dati sono corretti, ma i due numeri principali sono ambigui per un'agevolazione mista, e mancano le condizioni del prestito e le garanzie, cioè proprio ciò che un commercialista guarda per primo.

---

## 4383 – CCIAA Bari, Voucher Turismo 2026

**Materiale in ingresso.** Bando completo (584 righe) e pagina ricca, che contiene anche una FAQ. Circa 90 righe della pagina sono il menù del sito camerale. Tra gli allegati, "Facsimile F24" (478 righe di caselle vuote), modulo di rendicontazione, DSAN e procura non servono alla scheda: circa il 60% del testo degli allegati. Nel PDF del bando le lettere accentate sono rovinate dall'estrazione ("attivit a+", "nonch e9"), ma Sonnet le ha lette correttamente.

| Campo | Problema | Tipo | Pericolo |
|---|---|---|---|
| spese_ammesse / requisiti | Manca la regola sui tempi (art. 7 c. 4, ripetuta nella pagina): valgono solo le spese **fatte e pagate dopo la pubblicazione della graduatoria di concessione**, entro 250 giorni dalla concessione. Mancano anche la rendicontazione entro 30 giorni dalla fine del progetto (art. 13) e i pagamenti solo tracciabili (bonifico, RiBa o carta) | MANCANTE | ⚠ alto (un cliente che compra prima perde il contributo) |
| requisiti | Manca il regime **de minimis** (Reg. UE 2023/2831, art. 8), citato solo di passaggio nelle avvertenze. Manca "una sola domanda per impresa" (art. 5). L'esclusione per forniture con la Camera non vale per le imprese individuali (nota 3), che la scheda non esenta | MANCANTE / IMPRECISO | medio |
| territorio | "Provincia di Bari": il bando dice "circoscrizione territoriale di competenza della Camera di Commercio di Bari" (art. 4 B). Tradurlo in "provincia" non è scritto nei documenti. Da verificare sul sito della Camera: per quanto ne so, la sua competenza comprende anche la provincia di Barletta-Andria-Trani, i cui clienti verrebbero esclusi per errore | IMPRECISO | ⚠ medio |
| contributo_massimo 7000 | Corretto come voucher base. Con i premi (fino a +500 € di rating di legalità e +250 € di parità di genere, art. 3) si arriva a 7.750 €. Spiegato nelle avvertenze; va deciso quale dei due valori deve andare nel campo | IMPRECISO (lieve) | basso |
| codici_ateco | I 16 codici corrispondono all'art. 4 (ATECO 2025, segnalato). La deroga per gli agriturismi (FAQ, 55.20.51 e 56.11.91 anche come attività secondaria) è riportata bene nelle avvertenze | ok | – |
| stato / date | `aperto`, 18/09 ore 10 – 27/11 ore 12, sportello fino a esaurimento dei 400.000 € (art. 11): corretti | ok | – |
| fonti | Articoli citati corretti (art. 2, 3, 4, 7, 10). `tema` senza fonte (lieve) | ok | – |

**Voto: 4/5.** La migliore del gruppo tra i bandi veri: completa, precisa, ben citata. Manca però la regola sui tempi delle spese, da aggiungere prima di mostrarla a un cliente.

---

## Problemi ricorrenti

1. **Nessuna invenzione, molte omissioni.** Sonnet rispetta molto bene la regola 1. Gli errori vengono da campi riassunti troppo (requisiti, condizioni del prestito, tempi delle spese) e da numeri ambigui.
2. **`ente` non uniforme**: gestore (3055, 4136) oppure chi finanzia. Il prompt non dice quale scegliere; SCHEDA_BANDO.md sì.
3. **Agevolazioni miste**: `contributo_massimo` e `percentuale` non distinguono prestito e fondo perduto (4136). È il caso più pericoloso per l'abbinamento automatico.
4. **Premi aggiuntivi**: non è chiaro se entrano in `contributo_massimo` (4383; nel 4199 sì, e lì producono il 4.250).
5. **Tempi delle spese e regime di aiuto** (de minimis, GBER) spesso assenti, anche se decisivi per un commercialista.
6. **Fonti secondarie** (incentivi.gov.it, Unioncamere): la raccolta si ferma al riepilogo e non segue il link al bando ufficiale. La scheda resta povera e `url` non punta all'ente.
7. **Avvertenze usate male**: supposizioni ("le risorse potrebbero esaurirsi"), ripetizioni della sintesi, affermazioni false sul materiale (4136).
8. **`tema` spesso senza fonte**: nessuna delle 4 schede di bandi veri cita la fonte del tema.
9. **Materiale gonfio**: nei 3 bandi con allegati, dal 50% al 90% del testo in ingresso non serviva. Tutto costo, e più rumore in cui perdere le regole importanti.

## Proposte

### Al prompt (`app/schede/prompt_scheda.md`)

1. **Ente e gestore**: "`ente` è chi finanzia (Regione, Camera, Ministero). Se il bando è gestito da un altro soggetto (Finpiemonte, IRFIS, Invitalia, Unioncamere), scrivilo nella sintesi, non in `ente`."
2. **Territorio**: "Riporta il territorio con le parole del bando (es. 'circoscrizione della Camera di Commercio di Bari'). Non tradurlo in provincia o regione se il bando non lo fa."
3. **Agevolazioni miste**: "Se l'agevolazione unisce prestito e fondo perduto (`misto`), `contributo_massimo` e `percentuale` si riferiscono **solo alla parte a fondo perduto**. Nella sintesi scrivi l'importo totale, la ripartizione e le condizioni del prestito (tasso, durata, preammortamento, garanzie)." In alternativa si aggiunge un campo (vedi sotto).
4. **Premi**: decidere una regola e scriverla. Proposta: "`contributo_massimo` è il voucher o contributo base più alto; i premi aggiuntivi (rating di legalità, parità di genere) vanno nella sintesi con il loro importo."
5. **Elenco minimo per `requisiti`**: "Controlla sempre e riporta se presenti: regime di aiuto (de minimis o altro regolamento), polizza catastrofale, DURC, garanzie richieste (fideiussioni), numero massimo di domande, vincoli sui fornitori."
6. **Tempi delle spese**: "In `spese_ammesse` indica sempre da quando le spese sono ammissibili (es. 'solo dopo la concessione') e il termine per realizzare il progetto e per rendicontare."
7. **Avvertenze**: "Solo differenze tra documenti, dubbi reali o informazioni mancanti importanti. Non ripetere la sintesi e non fare supposizioni. Se hai solo una pagina di riepilogo e non il bando, scrivilo come prima avvertenza." Aggiungere: "Non fare deduzioni normative che il documento non scrive (es. equivalente-sovvenzione)."
8. **Fonti**: "Anche `tema` e `tipo_agevolazione` devono avere una fonte" (oppure esentare `tema` in modo esplicito, dato che è una classificazione).
9. **incentivi.gov.it**: aggiungere una nota fissa: "'Spesa ammessa (min-max)' è la spesa, non il contributo; 'Agevolazione concedibile' è il contributo; 99.999.998.000 significa 'nessun limite indicato'."
10. **Regola 9**: permettere di compilare anche `stato` quando è certo (es. "chiuso" per bandi del 2020), utile alla plancia.

### Ai campi della scheda (`docs/SCHEDA_BANDO.md` e tabella `bandi`)

- **`modalita_assegnazione`**: `sportello`, `graduatoria`, `click_day`, `automatica`. Oggi l'informazione sta solo nella sintesi, ma decide quanto è urgente avvisare il cliente.
- **`quota_fondo_perduto`** (percentuale) oppure **`fondo_perduto_massimo`** (euro), da riempire solo per `misto`: evita il caso 4136 nell'abbinamento.
- **`gestore`** (testo): toglie l'ambiguità di `ente`.
- **`fonte_primaria`** (sì/no): dice se la scheda si basa sul bando ufficiale o su un riepilogo (incentivi.gov.it, notizia di Unioncamere). La plancia può mostrarle con un'etichetta "da verificare".
- **`spese_ammissibili_dal`** (testo breve, es. "dopo la concessione", "dal 01/01/2026"): una delle cause più frequenti di perdita del contributo.

### Alla raccolta degli allegati

1. **Seguire il link al bando ufficiale** quando la pagina è un riepilogo: per incentivi.gov.it usare `link_ente` del catalogo; per Unioncamere Veneto il link "BANDO E MODULISTICA ONLINE". La scheda va fatta sulla pagina dell'ente, e `url` deve puntare lì.
2. **Correggere `pubblicato_il` per incentivi.gov.it**: il campo `data` del catalogo è la data di apertura, non di pubblicazione.
3. **Scartare prima i bandi chiusi da tempo**: una verifica senza IA sulla pagina ("Chiuso", date di validità passate da più di 6 mesi) avrebbe evitato 40–45 mila token sul 3055. In alternativa, un primo passaggio con la sola pagina: se è "NON PER IMPRESE" o chiuso, niente allegati.
4. **Mettere gli allegati in ordine di importanza e togliere quelli inutili**: prima bando, avviso, decreto, scheda prodotto e FAQ; i moduli (business plan, perizie, DSAN, procure, rendicontazione) solo con nome e prime righe; esclusi del tutto F24 di prova, whistleblowing, privacy e documenti vuoti. Il filtro sui documenti di menù e piè di pagina (commit 77ff1df) non ha ancora preso "WHISTLEBLOWING" del 4136, che sta nel menù in alto.
5. **Togliere i doppioni** per indirizzo o contenuto (3055: "Modalità di rendicontazione" due volte) e **segnalare gli allegati elencati ma non scaricati** (3055: Allegato 8).
6. **Ripulire la pagina** da menù e barre laterali: menù della Camera di Bari, notizie laterali di Unioncamere, glossario di incentivi.gov.it.
7. **Estrazione dei PDF**: nel bando di Bari le lettere accentate escono rovinate ("a+", "e9"). Sonnet le ha lette, ma conviene provare un secondo estrattore quando un testo contiene molte sequenze di questo tipo, per non rischiare cifre illeggibili.
