# Revisione schede Sonnet — gruppo A (2587, 2587b, 2585, 2814, 4199)

*Revisione del 25/09/2026. Ogni campo è stato confrontato con il testo del prompt `scheda_X.txt`, cioè con l'unica fonte che Sonnet aveva. Non è stato consultato nessun sito.*

## Sintesi

- **Il modello non ha inventato nulla** in nessuna delle 5 schede: tutti gli importi, le date e le percentuali si ritrovano nei testi. Formato delle date, importi numerici e valori ammessi sono rispettati ovunque. Anche le avvertenze sono oneste: segnala sempre testi troncati, allegati mancanti e differenze tra pagina e bando.
- **Quando i documenti ci sono, la scheda è quasi da usare così com'è**: la 2587b è praticamente uguale alla scheda compilata a mano (stessi importi, stessa percentuale, stessi ATECO esclusi con lo stesso ragionamento ATECO 2007→2025) e aggiunge dettagli utili che la scheda a mano non ha.
- **I problemi veri stanno quasi tutti a monte, nella raccolta**: 2587 ha il link alla pagina di login (scheda vuota); 2814 e 4199 non hanno nessun allegato (la scheda si basa sulla sola pagina di sintesi); nella 2587b il bando ufficiale viene tagliato perché delibera e decreto, messi prima, consumano lo spazio disponibile, e il calendario delle fiere ammesse arriva vuoto.
- **L'errore più pericoloso per l'abbinamento è nella 2585**: le esclusioni di settore per sezione (agricoltura, immobiliare, finanza) sono scritte nei requisiti ma **non** in `codici_ateco_esclusi`, quindi il motore proporrebbe il bando a clienti esclusi. Il bando stesso ha un errore di lettere ATECO che Sonnet non ha notato.
- Errori ricorrenti minori: `ente` a volte è il gestore invece di chi finanzia (il prompt non lo spiega); i requisiti mescolano condizioni di ammissione e criteri di punteggio; nelle `fonti` non esiste la voce "annuncio" e la citazione "pagina" viene usata anche quando la pagina non contiene l'informazione.
- **Voti: 2587 = 1 · 2587b = 4 · 2585 = 4 (da correggere prima dell'abbinamento) · 2814 = 3 · 4199 = 3.** Il modello è pronto; la raccolta di pagine e allegati non ancora.

---

## 2587 — Fiere internazionali Lombardia (versione scaricata oggi dal sistema)

**Materiale in ingresso:** inutilizzabile. L'indirizzo della raccolta è `.../bpm/web/la-mia-area/domande/faiDomanda?strumentoCod=RLO12026055023`, cioè la pagina per **presentare la domanda**, che chiede il login: il testo è solo "Shibboleth Authentication Request". Nessun allegato. Il titolo dell'annuncio è troncato ("...PARTECIPAZIONE DE...").

| Campo | Valore di Sonnet | Esito | Nota |
|---|---|---|---|
| titolo | titolo troncato dell'annuncio | IMPRECISO | Corretto non inventare, ma il titolo mostrato al cliente è monco. È un difetto della raccolta. |
| ente / territorio | Regione Lombardia / Lombardia | ok | Presi dai dati dell'annuncio ("LOM" → Lombardia). |
| url | link della pagina di domanda | IMPRECISO (pericoloso) | Il cliente che apre il link finisce su un login, non sul bando. Non è colpa del modello. |
| fonti di titolo, ente, territorio, url | "pagina" | FONTE SBAGLIATA | La pagina non contiene nessuna di queste informazioni: vengono dai dati dell'annuncio. Il prompt non prevede la voce "annuncio". |
| tutti gli altri campi | null / [] | corretto | Comportamento giusto: non c'era nulla da cui ricavarli. |
| avvertenze | 4 avvertenze chiare | ok | Spiega bene che la pagina chiede il login e che mancano gli allegati. |

**Regole del prompt:** rispettate tutte (niente invenzioni, avvertenze presenti), a parte la citazione "pagina" per dati che vengono dall'annuncio.

**Voto: 1/5.** La scheda è inutilizzabile, ma il modello si è comportato **correttamente**: il guasto è della raccolta. Serve una regola nella raccolta che, per Regione Lombardia, trasformi il link `faiDomanda?strumentoCod=XXX` nella pagina di dettaglio `.../bandi/dettaglio/...-XXX` (o la cerchi per codice), e un controllo che scarti le pagine con meno di ~300 caratteri o con parole come "Authentication", "login", "SPID" prima di chiamare l'IA (così non si spende una chiamata a vuoto).

---

## 2587b — Fiere internazionali Lombardia (pagina di dettaglio e allegati giusti)

**Materiale in ingresso:** buono ma tagliato male. Pagina di dettaglio completa, più 5 allegati in quest'ordine: D.G.R. revisione criteri (lunga, letta tutta), Decreto di approvazione (tagliato), Modello di domanda, **Bando (Allegato A) tagliato a metà dell'articolo C.1**, Calendario fiere **vuoto** ("testo troncato: limite complessivo"). Quindi Sonnet non ha visto gli articoli del bando su valutazione, graduatoria, rendicontazione dopo C.1 e non ha visto l'elenco delle fiere ammesse, che è l'informazione pratica più utile per il cliente ("la mia fiera c'è?").

**Confronto con la scheda compilata a mano (docs/SCHEDA_BANDO.md):** coincidono titolo, ente, territorio, url, stato, data di apertura (2026-07-30), scadenza vuota, tipo, `contributo_massimo` 15000, `percentuale` 60, spese a forfait (440 €/m², +20%, +7%, minimo 6.000 €), `codici_ateco_esclusi` ["A","L"] con la stessa avvertenza ATECO 2007/2025, dimensioni, tema. Sonnet in più riporta: la possibilità di attivare la sede in Lombardia entro l'erogazione, il blocco dello sportello al 125% della dotazione, una sola domanda per impresa, il divieto di cumulo anche con il PNRR, il tetto de minimis di 300.000 € in tre anni, la ripartizione della dotazione. La scheda a mano in più ha: la soglia di 50 punti su 100, l'esclusione del tabacco e la rendicontazione entro il 29/02/2028.

| Campo | Esito | Nota |
|---|---|---|
| titolo, ente, territorio, url, stato, data_apertura | ok | Tutti dalla pagina; "Aperto" e "Domande dal 30/07/2026 ore 10:00". |
| scadenza | ok (fonte da precisare) | `null` giusto. La fonte citata è "art. C.1", che dà solo l'apertura; lo "fino ad esaurimento risorse" è sulla pagina ("Come partecipare") e il blocco al 125% è in C.1.3. |
| sintesi | IMPRECISO (lieve) | Corretta nei numeri. "Imprese che partecipano per la prima volta" semplifica troppo: "nuovo espositore" vuol dire non aver partecipato alle ultime 3 edizioni (2 se la fiera è biennale) di **tutte** le fiere indicate. Non dice che è uno sportello **valutativo** con punteggio minimo (lo dice la pagina: "soglia minima nella valutazione di merito"; i 50 punti sono nella D.G.R.). Un po' lunga (6 righe). |
| a_chi_si_rivolge | ok | Include correttamente l'impegno ad attivare la sede operativa (art. A.3.3.b). |
| cosa_finanzia | MANCANTE (utile) | Manca che **non si finanziano fiere già terminate** al momento della domanda (art. B.2.a): per un commercialista è il primo avviso da dare al cliente. |
| tipo_agevolazione, contributo_massimo, percentuale | ok | 15000 e 60 corretti (art. B.1.b, punti 1, 5, 6). |
| spese_ammesse | ok | Completo, anche il calcolo automatico senza fatture (B.3.2). |
| codici_ateco / esclusi | ok | [] e ["A","L"], con avvertenza chiara sulla differenza tra pagina/D.G.R. (ATECO 2007, sezione K) e bando (ATECO 2025, sezione L). |
| dimensioni_ammesse, tema | ok | |
| requisiti | MANCANTE (lieve) | Mancano: esclusione dei settori del tabacco e dei settori esclusi dal de minimis (A.3.2), requisito antimafia (A.3.3.f), rendicontazione entro il 29/02/2028 senza proroghe (B.2.b.3, letto da Sonnet). |
| fonti | IMPRECISO (lieve) | Manca la fonte di `sintesi`; per il resto le citazioni con articolo sono giuste e verificabili. |
| avvertenze | ok, ottime | Tutte vere, inclusa quella onesta sul bando troncato dopo C.1. |

**Pericolosità:** nessun errore pericoloso. L'unico rischio pratico è la mancanza dell'avviso "fiere già finite escluse" e dell'elenco fiere.

**Regole del prompt:** rispettate. Regola 2 (bando vince sulla pagina) applicata in modo esemplare sugli ATECO.

**Voto: 4/5.** Usabile da un commercialista con due aggiunte (fiere già concluse, punteggio minimo). Con il bando completo e il calendario delle fiere sarebbe da 5.

---

## 2585 — Export su Misura 2026 (Unioncamere Lombardia)

**Materiale in ingresso:** ottimo. Pagina completa, Determinazione di approvazione, **testo integrale del bando** (letto per intero fino all'art. 10 e oltre), tre moduli .docx (vuoti o quasi, non servono).

| Campo | Valore di Sonnet | Esito | Nota |
|---|---|---|---|
| titolo | "Export su Misura 2026 - Servizi a supporto..." | ok | |
| ente | Unioncamere Lombardia | ERRATO (rispetto alla specifica) | Secondo SCHEDA_BANDO.md `ente` è **chi finanzia**: la dotazione è "a carico di Regione Lombardia" (art. 5); Unioncamere è il soggetto attuatore/gestore (art. 4) e andava nella sintesi (dove c'è). La fonte citata è proprio "punto 4 Soggetto gestore". Il prompt però non spiega questa distinzione: errore indotto dal prompt. |
| territorio | Lombardia | ok | |
| stato, data_apertura, scadenza | aperto, 2026-09-02, 2026-10-09 | ok | Mancano gli orari (dalle 11:00 / **fino alle 16:00** del 9/10): la chiusura alle 16 e non a mezzanotte è un dettaglio che può far perdere il bando. Il formato non ha un campo per l'ora. |
| sintesi | | ok | Chiara e completa: 8 Paesi, 75 imprese, 11.500 €, de minimis, Restart, graduatoria. |
| a_chi_si_rivolge, cosa_finanzia | | ok | Giusto dire che viaggio, soggiorno e campionature restano a carico dell'impresa. |
| tipo_agevolazione | voucher | IMPRECISO | Non è un voucher da spendere: sono servizi erogati direttamente da Promos Italia, con valore in de minimis. `altro` (con spiegazione) sarebbe più fedele. Manca un valore "servizi". |
| contributo_massimo | 11500 | ok | Art. 6. |
| percentuale | null | ok | Giusto, ben spiegato in avvertenze. |
| spese_ammesse | | ok | |
| codici_ateco_esclusi | ["12","46.35","46.39.20","46.21.21","47.26"] | **MANCANTE (pericoloso per l'abbinamento)** | Ci sono solo i codici del tabacco. Il bando (art. 3) esclude anche, per codice primario, le **sezioni A** (salvo agromeccaniche), **L** e **K**. Sono scritte nel testo dei requisiti ma non nell'elenco, che è quello che userà il motore: un'impresa agricola, immobiliare o finanziaria verrebbe abbinata. |
| avvertenza ATECO | "codici in ATECO 2025, come specificato nel bando" | IMPRECISO | Il bando scrive "sezioni L (Attività immobiliari) e K (Attività finanziarie) ... ATECO 2025", ma queste sono le lettere di **ATECO 2007**: in ATECO 2025 la finanza è la L (come ricorda la stessa SCHEDA_BANDO.md) e l'immobiliare è un'altra sezione. Il bando è incoerente e Sonnet non lo ha segnalato. Il commercialista deve saperlo, perché con le lettere prese alla lettera si escluderebbe il settore sbagliato. |
| dimensioni_ammesse | micro, piccola, media | ok | |
| requisiti | | ok (lieve MANCANTE) | Completo. Manca la regola sulle imprese collegate o con stessi amministratori/soci (vale solo la prima domanda, art. 7) e l'allegato obbligatorio del certificato di polizza catastrofale (art. 7.b), utile per preparare la domanda. |
| tema | internazionalizzazione | ok | |
| fonti | | ok | Precise, per articolo. |
| avvertenze | | ok | Vere; la soglia 50/100 e 20 punti sulla prefattibilità è corretta (art. 8). "Un solo percorso" è corretto (art. 8: "assegnataria di un unico percorso"). |

**Regole del prompt:** rispettate, salvo la regola 6 applicata a metà (esclusioni per sezione non riportate nell'elenco) e la mancata segnalazione dell'incoerenza ATECO.

**Voto: 4/5** per la lettura da parte del commercialista (testo molto buono), ma **da correggere prima di usarla nell'abbinamento** (`codici_ateco_esclusi` incompleto).

---

## 2814 — Esercizi commerciali polifunzionali, spese di gestione 2026 (Regione Emilia-Romagna)

**Materiale in ingresso:** insufficiente. Solo la pagina di sintesi. La pagina ha una sezione "Bando e modulistica" ma **nessun allegato è stato scaricato**: il bando integrale (con l'art. 2 delle definizioni b, g, h, che decide chi può partecipare) non è arrivato a Sonnet. La pagina stessa è incoerente sulla legge (in testa "L.R. n. 12/2003", nel testo "legge regionale 3 ottobre 2023, n. 12"); non incide sui campi.

| Campo | Valore di Sonnet | Esito | Nota |
|---|---|---|---|
| titolo, ente, territorio, url | | ok | |
| stato | aperto | ok | Oggi 25/09, chiusura 30/09 alle 23:59: mancano 5 giorni. Il formato non prevede un segnale di urgenza. |
| data_apertura | 2026-09-01 | ok / FONTE SBAGLIATA | La data è giusta ma la fonte "pagina - Tempi e scadenze" è sbagliata: lì ci sono solo pubblicazione (08/07) e scadenza; l'apertura è in "Presentazione domanda". |
| scadenza | 2026-09-30 | ok | |
| sintesi | | ok | Corretta: 80%, 15.000 €, plafond 400.000 € con riduzione proporzionale, PEC. |
| a_chi_si_rivolge | "esercizi ... già riconosciuti ..." | IMPRECISO (pericoloso: esclude chi ha diritto) | La pagina indica **due** gruppi: (1) esercizi polifunzionali già riconosciuti (lett. h) **e anche** (2) imprese in aree di rarefazione commerciale che hanno le caratteristiche di esercizio polifunzionale (lett. b e g). Sonnet ha fuso i due casi in "già riconosciuti", restringendo la platea: un cliente non ancora riconosciuto formalmente potrebbe essere scartato a torto. |
| cosa_finanzia, spese_ammesse | | ok | Voci e riferimento alle spese 2025 corretti. |
| tipo_agevolazione, contributo_massimo, percentuale | fondo_perduto, 15000, 80 | ok | |
| codici_ateco / esclusi | [] / [] | ok | La pagina non ne parla; l'avvertenza lo dice. |
| dimensioni_ammesse | micro, piccola, media | ok | Dalla voce "Chi può fare domanda". |
| requisiti | | IMPRECISO | Stesso problema di `a_chi_si_rivolge` (i due gruppi fusi). Il regime de minimis c'è solo nella sintesi. |
| tema | commercio | ok | |
| avvertenze | | ok | Onesta sulla mancanza del bando integrale. |

**Regole del prompt:** rispettate (niente invenzioni, formati corretti).

**Voto: 3/5.** Utile come segnalazione rapida (scade tra 5 giorni), ma chi può partecipare è descritto in modo più stretto del vero e manca il bando integrale.

---

## 4199 — CCIAA Modena, occupazione giovanile 2026 (dal catalogo incentivi.gov.it)

**Materiale in ingresso:** insufficiente. Solo la scheda del catalogo nazionale, con molto rumore (un glossario di ~70 voci tipo "Credito d'imposta", "ZES", "De minimis" che **non** descrivono questo bando). Il bando vero è sul sito della Camera di Commercio (`link_ente` = mo.camcom.it, presente come "Vai al sito"), che non è stato seguito. Inoltre la raccolta ha registrato come "data di pubblicazione" la data di apertura (2026-11-02): errore della raccolta.

**Confronto con il catalogo strutturato (`riferimento_incentivi_gov.json`):** dimensioni (micro/piccola/media), forma (fondo perduto), scadenza 30/11/2026, apertura 02/11/2026, ATECO "tutti i settori" coincidono. `costo_max` = 4250 corrisponde al **massimo contributo** (2 × 2.000 € + 250 € di premio legalità = 4.250 €), non a una spesa: il catalogo lo espone come "Spesa ammessa fino a 4.250 €". `dotazione` = 200000 è lo stanziamento complessivo, `costo_min` = 0 non significa nulla. L'ambito "Formazione" del catalogo è una classificazione generica: il tema giusto è `assunzioni`, come ha scelto Sonnet.

| Campo | Valore di Sonnet | Esito | Nota |
|---|---|---|---|
| titolo, ente | | ok | |
| territorio | Provincia di Modena | ok | I 47 comuni elencati sono tutti quelli della provincia. |
| url | pagina del catalogo | IMPRECISO | Il cliente dovrebbe ricevere il link della Camera di Commercio (bando ufficiale), non quello del catalogo. |
| stato | in_arrivo | ok | La pagina elenca "Attivo Chiuso In Arrivo" tutte insieme (è il menu dei filtri); Sonnet ha dedotto giustamente dalle date. |
| data_apertura, scadenza | 2026-11-02, 2026-11-30 | ok | La precompilazione dal 26/10 è in avvertenze: bene. |
| sintesi | | ok | Corretta. |
| a_chi_si_rivolge, cosa_finanzia | | ok | Età 18-35 non compiuti, tre tipi di contratto. |
| contributo_massimo | 4250 | ok nel valore, IMPRECISO nella fonte | Il numero è giusto (coincide con 2×2.000+250), ma viene dalla voce "Spesa ammessa (min-max)", mentre "Agevolazione concedibile" è vuota. Andava detto in avvertenza. Resta un dubbio non risolvibile con la sola pagina: "fino a due" giovani per ciascun tipo di contratto, o due in tutto? Il catalogo suggerisce due in tutto. |
| spese_ammesse | "Oneri diversi di gestione, fino a 4.250 €" | IMPRECISO (fuorviante) | È l'etichetta generica del catalogo. Per un bonus assunzioni non ci sono "spese": il contributo è a importo fisso per giovane assunto. Meglio `null` o "contributo fisso per assunzione, senza rendicontazione di spese" se il bando lo dicesse. |
| codici_ateco | [] | ok | "Tutti i settori ammissibili a ricevere aiuti". |
| requisiti | | IMPRECISO | Contiene criteri di punteggio (questionari di Assessment, premio legalità, parità per ordine cronologico) che **non sono requisiti** di ammissione. I veri requisiti (periodo in cui devono avvenire le assunzioni, iscrizione al Registro, diritto annuale, regime di aiuto) non sono nella pagina: non è colpa del modello, ma andava detto. |
| tema | assunzioni | ok | |
| fonti | tutte "pagina" | IMPRECISO | Nessun dettaglio sulla sezione; "codici_ateco: pagina" per un elenco vuoto va bene. |
| avvertenze | | IMPRECISO (una) | "Le risorse potrebbero esaurirsi prima della scadenza" è fuorviante: il bando è **a graduatoria** con finestra fissa, non a sportello; le domande presentate entro il 30/11 vengono tutte valutate. Le altre avvertenze sono giuste, compresa quella sulla mancanza del bando originale. |

**Informazione mancante e importante (non presente nella pagina):** il periodo in cui devono essere fatte le assunzioni ("abbiano assunto o intendano assumere": da quando?). Per un commercialista è il primo dato da verificare, e la scheda non avverte che manca.

**Regole del prompt:** rispettate nella sostanza; nessuna invenzione.

**Voto: 3/5.** Corretta nei numeri e nelle date, ma costruita su una pagina di catalogo: requisiti e spese sono deboli, e il link non porta al bando ufficiale.

---

## Problemi ricorrenti

1. **Materiale in ingresso (la causa principale).** 3 schede su 5 sono limitate dalla raccolta, non dal modello: link di login (2587), nessun allegato scaricato (2814, 4199), bando ufficiale troncato dietro delibere e decreti (2587b), allegato importante vuoto (calendario fiere).
2. **Liste strutturate meno complete del testo.** Nella 2585 le esclusioni ATECO per sezione sono nel testo dei requisiti ma non nell'elenco: il motore di abbinamento leggerà solo l'elenco.
3. **`ente` = gestore invece di chi finanzia** (2585). Il prompt non spiega la differenza.
4. **`requisiti` mescola ammissione e punteggio** (4199) e **fonde gruppi diversi di beneficiari** (2814).
5. **Fonti**: manca la voce "annuncio" (2587); "pagina - sezione X" a volte indica la sezione sbagliata (2814); `sintesi` spesso senza fonte (2587b).
6. **Coerenza ATECO non controllata**: Sonnet ha gestito bene il caso "pagina 2007 / bando 2025" (2587b), ma non ha visto un bando che dichiara ATECO 2025 usando lettere del 2007 (2585).
7. **Informazioni pratiche perse**: orario di chiusura (2585: ore 16:00), fiere già concluse escluse (2587b), periodo delle assunzioni (4199).

## Proposte

### Al prompt (`app/schede/prompt_scheda.md`)

1. **Definire `ente`**: "chi finanzia (Regione, Camera di Commercio, Ministero...). Se il bando è gestito da un altro soggetto (Unioncamere, Invitalia, Promos...), l'ente resta chi mette i soldi e il gestore va nella sintesi."
2. **Regola ATECO più forte**: "Ogni esclusione di settore scritta nel bando (sezioni, divisioni, codici) deve comparire in `codici_ateco_esclusi`, anche se la ripeti nei requisiti. Controlla che le lettere delle sezioni corrispondano alla versione ATECO dichiarata (in ATECO 2025 le attività finanziarie sono la sezione L, in ATECO 2007 la K): se non tornano, scrivilo in `avvertenze`."
3. **Separare i requisiti dal punteggio**: "`requisiti` contiene solo le condizioni per essere ammessi. Criteri di valutazione, premi e punteggi minimi vanno nella `sintesi` o in `avvertenze`."
4. **Più gruppi di beneficiari**: "Se il bando ammette più categorie di beneficiari (per esempio 'già riconosciuti' oppure 'con le caratteristiche di'), elencale tutte, separate."
5. **Fonte "annuncio"**: aggiungere `"annuncio"` tra le fonti ammesse per i dati che vengono dalla raccolta, e chiedere la fonte anche per `sintesi`.
6. **Avvisi pratici obbligatori in `avvertenze`**, se presenti nei documenti: orario di chiusura se diverso da fine giornata; spese o eventi che non devono essere già conclusi/sostenuti al momento della domanda; periodo in cui devono cadere assunzioni o investimenti. E se **non** sono presenti: "Il testo non indica il periodo di ammissibilità delle spese/assunzioni".
7. **Tipo di bando**: aggiungere una frase: "a graduatoria (finestra fissa) oppure a sportello (ordine di arrivo)", e non scrivere "le risorse potrebbero esaurirsi" per i bandi a graduatoria.
8. **Pagine di catalogo** (incentivi.gov.it): "Se la pagina è una scheda di catalogo, ignora il glossario e le etichette generiche (es. 'Oneri diversi di gestione'); se c'è un link al sito dell'ente, dillo in avvertenze e indica che il bando ufficiale non è stato letto."

### Ai campi della scheda (`docs/SCHEDA_BANDO.md`)

1. Aggiungere **`ora_scadenza`** (o permettere `AAAA-MM-GGTHH:MM` in `scadenza`): la chiusura alle 16:00 o alle 12:00 è frequente.
2. Aggiungere **`modalita_selezione`**: `sportello`, `sportello_valutativo`, `graduatoria`, `automatica`. Serve al commercialista per capire l'urgenza.
3. Aggiungere **`gestore`** come campo separato, così `ente` resta chi finanzia senza ambiguità.
4. In `tipo_agevolazione` aggiungere **`servizi`** (percorsi e consulenze erogati direttamente, come Export su Misura), oggi forzati in `voucher`.
5. Aggiungere **`url_bando_ufficiale`** distinto da `url` quando la pagina raccolta è un catalogo o un aggregatore (4199).
6. Aggiungere **`versione_ateco`** (`2007`, `2025`, `incoerente`) come campo, non solo come avvertenza, così il motore sa come confrontare i codici.

### Alla raccolta degli allegati e delle pagine

1. **Regione Lombardia**: trasformare i link `.../faiDomanda?strumentoCod=CODICE` nella pagina di dettaglio del bando (ricerca per codice). Senza questo, tutte le schede lombarde di Bandi Online nascono vuote come la 2587.
2. **Scartare le pagine vuote o di login prima dell'IA**: se il testo è sotto ~300 caratteri o contiene "Authentication", "Accedi con SPID", "login", non chiamare Sonnet e segnalare in plancia "pagina non leggibile".
3. **Ordine e priorità degli allegati nel limite di testo**: mettere per primo il documento che si chiama "Bando", "Avviso", "Allegato A", "Regolamento"; poi FAQ e calendari/elenchi; per ultimi delibere e decreti di approvazione (sono lunghi e ripetono il bando con parole più vecchie). Nella 2587b la D.G.R. e il decreto hanno consumato lo spazio e il bando è stato tagliato a metà.
4. **Limite per singolo allegato**, così un documento lungo non azzera gli altri (il calendario fiere della 2587b è arrivato vuoto).
5. **Seguire il link all'ente** per le pagine di aggregatori (incentivi.gov.it "Vai al sito", `link_ente` nei dati del catalogo): scaricare lì la pagina e gli allegati del bando vero.
6. **Verificare perché 2814 non ha allegati**: la pagina ha la sezione "Bando e modulistica" ma nessun file è arrivato; probabilmente i link sono in una parte della pagina tolta dal filtro di menu e piè di pagina, o puntano a un altro dominio.
7. **Data di pubblicazione dal catalogo**: nella 4199 la raccolta ha usato la data di apertura come data di pubblicazione; va corretto nella lettura di incentivi.gov.it.
8. Saltare gli allegati .docx di modulistica vuoti (2585): occupano spazio senza informazioni.
