# Revisione delle schede, gruppo A (seconda prova, 25/09/2026)

*Cinque revisioni Opus, una per bando, riunite qui. Riferimento: i documenti che Sonnet aveva davanti (`scheda_N.txt`, non inclusi nel repository perché lunghi; si rigenerano dalla copia del database).*

| Bando | Preliminare di Haiku giusto? | Voto | Inventato | Sbagliato | Mancante | Impreciso | Nota |
|---|---|---|---|---|---|---|---|
| 568 Camera di Bari, voucher doppia transizione | sì | 4 | 0 | 0 | 4 | 6 | accurata; la notizia di chiusura anticipata del 14/09 non è stata letta dalla raccolta |
| 254 Camera di Caserta, fiere Italia/estero (5 linee) | sì (chiuso) | 4 | 0 | 0 | 3 | 6 | fedele; il filtro "solo imprese di produzione" resta a parole |
| 610 Liguria FESR 1.3.4 (da incentivi.gov.it) | sì | 3 | 0 | 2 | 4 | 4 | territorio letto come sede invece che luogo delle riprese; "PMI" senza le micro |
| 416 Camera Sud Est Sicilia, voucher turismo (notizia) | sì | 3 | 0 | 2 | 3 | 5 | date copiate da un refuso (2025 invece di 2026): il bando risulterebbe chiuso |
| 346 Lombardia, voucher di accelerazione | sì (chiuso) | 4 | 0 | 2 | 4 | 4 | vincolo "moda e design" rimasto a parole; esclusioni del de minimis non nell'elenco |


---

## 568 — Voucher Doppia Transizione 2026 (Camera di Commercio di Bari)

*Revisione del 25/09/2026. Ogni campo è confrontato con il testo del prompt `scheda_568.txt`, cioè con l'unica fonte che Sonnet aveva. I numeri di riga si riferiscono a quel file, salvo quando è scritto `preliminare_568.txt`. Non è stato consultato nessun sito.*

**Materiale in ingresso:** buono, con un buco importante.
- In quest'ordine: (1) **testo integrale del bando**, dall'art. 1 all'art. 17 e firma "Bari, 28/07/2026" (righe 122-712); (2) **pagina ufficiale** (righe 714-877), con circa 70 righe di menu del sito in testa (righe 715-784) che non servono; (3) **FAQ** complete (righe 879-1072). Nessun taglio: "Note del sistema: nessuna" (riga 118). L'ordine è quello giusto (prima il bando).
- **Cosa manca:** la pagina mostra una notizia del **14.09.2026, "Bando Doppia Transizione 2026 - Chiusura anticipata termini presentazione domande"** (righe 859-861), ma il testo della notizia (l'avviso del Segretario Generale previsto dall'art. 3 comma 10, righe 195-197) **non è stato scaricato**. È l'informazione più importante per un cliente oggi: con ogni probabilità lo sportello si è chiuso il giorno stesso dell'apertura per esaurimento fondi. La modulistica (moduli di domanda, procura, F24) non è arrivata: va bene così.

| Campo | Valore di Sonnet | Esito | Nota |
|---|---|---|---|
| titolo | "Bando Voucher Doppia Transizione ... Anno 2026" | ok | Riga 111. |
| ente | CCIAA di Bari | ok | Art. 1 e art. 3 comma 1: stanzia la Camera (righe 138, 162). |
| gestore | null | ok | InfoCamere fornisce solo la piattaforma ReStart (riga 413); istruttoria e concessione sono della Camera (righe 483-485). |
| url | pagina ba.camcom.it | ok | Riga 114. |
| territorio | "Circoscrizione ... CCIAA di Bari (provincia di Bari e provincia di Barletta-Andria-Trani)" | ok | Bando: "circoscrizione territoriale della Camera di Commercio di Bari" (righe 207-208); la precisazione Bari-BAT viene dalla FAQ (righe 907-908). Giusto averla aggiunta tra parentesi. |
| territorio_regioni | ["PUG"] | ok | |
| territorio_province | ["BA","BT"] | ok | FAQ: "sede legale e/o unità locale a Bari-BAT e provincia" (righe 907-908). Fonte citata correttamente. |
| territorio_comuni | [] | ok | |
| sede_richiesta | legale_o_operativa | ok | "sede legale o unità locale" (riga 207); la FAQ conferma che basta l'unità locale con sede legale altrove (righe 905-908). |
| data_apertura / ora_apertura | 2026-09-14 / 10:00 | ok | Art. 10 comma 2 (riga 416). |
| scadenza / ora_scadenza | 2026-10-15 / 13:00 | ok | Riga 416. |
| chiuso_il | null | ok per le regole, **pericoloso nei fatti** | Giusto non inventare una data: il testo dell'avviso non c'è. Ma il sistema calcolerà lo stato "aperto" fino al 15/10 e proporrà ai clienti un bando che il titolo della notizia (riga 861) dice chiuso in anticipo. Guasto della raccolta, non del modello; vedi avvertenze. |
| modalita_selezione | sportello_valutativo | ok (con nota) | Art. 11 comma 1: "procedura valutativa a sportello ... secondo l'ordine cronologico" (righe 476-477). Non c'è un punteggio minimo, solo la verifica di attinenza del progetto (righe 479-482): la definizione del prompt ("con punteggio minimo", riga 25) non calza del tutto, ma la scelta è difendibile. |
| sintesi | 5 frasi | ok (lieve) | Numeri tutti giusti: 8.000 €, 70%, minimo 4.000 €, premi 150/300/500 € e 250 € (righe 165-190), date e ore. Un po' lunga. Non accenna alla notizia di chiusura anticipata: chi legge solo la sintesi crede che si possa ancora presentare domanda fino al 15/10. |
| a_chi_si_rivolge | MPMI anche startup innovative, sede o unità locale in Bari-BAT; no liberi professionisti non in forma d'impresa | ok | Art. 4 (righe 202-209); FAQ righe 891-897. |
| soggetti_ammessi | ["impresa"] | ok | FAQ riga 895: il libero professionista solo se iscritto come impresa. |
| forme_giuridiche_ammesse / _escluse | [] / [] | ok | Il bando non ne nomina. |
| dimensioni_ammesse | micro, piccola, media | ok | Art. 4 comma 1 lett. a (riga 205). |
| eta_impresa_min/max_mesi | null / null | ok | Nessun limite di età; le startup innovative sono ammesse (FAQ riga 892). |
| requisiti_speciali_obbligatori | [] | ok | La FAQ lo dice espressamente per il rating di legalità (righe 925-926). |
| requisiti_speciali_premiali | rating_legalita, certificazione_parita_genere | MANCANTE (basso) | Giusti i due valori (righe 170, 176). Manca `altro` per la **partecipazione al Bando PID-Next 2025 o 2026** (riga 182), che dà lo stesso premio di 250 € della parità di genere (riga 188). È scritta nella sintesi, ma non nell'elenco. |
| dipendenti_min/max, fatturato_min/max | null | ok | Solo la definizione europea di PMI (riga 205). |
| codici_ateco / codici_ateco_esclusi | [] / [] | ok | Il bando non elenca settori né esclusioni. Nota: il regolamento de minimis 2023/2831 (riga 394) esclude di suo alcuni settori (pesca, produzione agricola primaria), ma il bando non li scrive: giusto non inventarli. |
| ateco_versione | null | ok | Nessun codice nel bando. |
| regime_aiuto | ["de_minimis"] | ok | Art. 8 comma 1, Reg. UE 2023/2831 (righe 393-394). |
| requisiti | elenco art. 4-6 | ok (lieve MANCANTE) | Completo su DURC, polizza catastrofale, diritto annuale, antimafia, liquidazione, sanzioni interdittive, forniture con la Camera, esclusione di chi ha avuto il voucher 2024 o 2025, una sola domanda, vincoli sui fornitori (righe 202-298). Mancano: regolarità su **salute e sicurezza sul lavoro** (D.lgs. 81/2008, righe 225-226) e i documenti richiesti **a pena di esclusione** che un commercialista deve preparare prima: **preventivi non anteriori alla pubblicazione del bando** (righe 439-440) e **autovalutazione SELFI4.0 fatta negli ultimi 3 mesi** (righe 451-454). |
| cosa_finanzia | tecnologie abilitanti + consulenza e formazione | IMPRECISO (basso) | L'elenco tra parentesi sembra completo ma non lo è: mancano **stampa 3D/manifattura additiva, calcolo ad alte prestazioni, fintech (EDI), geolocalizzazione, sistemi per l'esperienza del cliente in negozio** (righe 302-319) e le spese per le **Comunità Energetiche Rinnovabili** (righe 344-347). Un cliente con un progetto di stampa 3D potrebbe pensare di non rientrare. |
| tipo_agevolazione / tipi_agevolazione | voucher / ["voucher"] | ok | Art. 3 comma 2 (riga 164). |
| tema / temi | digitale / digitale, green | ok | Art. 1 comma 2 (righe 143-148). |
| categorie_spesa | macchinari, software, consulenze, formazione, energia_efficienza | ok | Art. 7 (righe 301-358). |
| contributo_massimo | 8000 | ok | Art. 3 comma 3, premi esclusi (righe 165-166), come chiede la regola 19. |
| percentuale | 70 | ok | Art. 3 comma 5 (riga 168). I premi sono importi fissi, non punti percentuali: giusto lasciare 70. |
| fondo_perduto_massimo / percentuale_fondo_perduto / finanziamento_massimo | null / null / null | ok (rispetto al prompt) | Non è un aiuto misto, quindi la regola 18 non si applica. Però l'esempio a mano in `SCHEDA_BANDO.md` compila questi campi anche per un fondo perduto puro (15000, 60): le due indicazioni non coincidono (vedi problemi generali). |
| spesa_minima | 4000 | ok | Art. 3 comma 4 (riga 167). |
| spesa_massima | null | ok | Il bando non la fissa. |
| dotazione | 580000 | ok | Art. 3 comma 1 (riga 163). |
| spese_ammesse | tempi + esclusioni | ok (lieve MANCANTE) | Tempi perfetti: solo dopo la pubblicazione della concessione, fino al 120° giorno, rendiconto entro 30 giorni (righe 381-384, 576-577; FAQ righe 1043-1048). Tra le esclusioni manca **"siti web"** (riga 368: "sistemi e-commerce, **siti web** e loro componenti accessorie"): è proprio la spesa che molti clienti chiedono. Mancano anche IVA esclusa salvo non recuperabile (righe 385-387) e divieto di pagare in contanti o con assegni (righe 556-558). |
| linee | [] | ok | Una sola linea. |
| vincoli.territorio | vincolo | ok | Riga 207. |
| vincoli.soggetti | vincolo | ok | Solo imprese iscritte (riga 209, FAQ riga 895). |
| vincoli.forme_giuridiche | non_noto | IMPRECISO (medio) | L'art. 4 è un elenco chiuso di requisiti "pena l'inammissibilità" (righe 202-204) e ammette qualunque impresa iscritta. La stessa avvertenza 4 di Sonnet dice "si applica solo il requisito generale di impresa attiva e iscritta": cioè nessun limite. `nessun_vincolo` era più fedele (l'esempio in SCHEDA_BANDO.md fa così). Con `non_noto` il bando non risulterà mai "compatibile", solo "da verificare", per nessun cliente. |
| vincoli.dimensioni | vincolo | ok | |
| vincoli.ateco | non_noto | ok | Difendibile: il bando non ne parla, ma il de minimis ha esclusioni di settore proprie che il bando non riporta. Prudente. |
| vincoli.eta_impresa | non_noto | IMPRECISO (medio) | Stesso ragionamento delle forme giuridiche: elenco chiuso di requisiti senza età, startup ammesse (FAQ riga 892). Andava `nessun_vincolo`. |
| vincoli.requisiti_speciali | nessun_vincolo | ok | La FAQ dice espressamente che il rating non è obbligatorio (righe 925-926). Però è incoerente con le scelte `non_noto` sulle altre voci, che hanno lo stesso tipo di prova. |
| vincoli.dipendenti | non_noto | IMPRECISO (basso) | Nessuna soglia oltre la definizione di PMI (già coperta da `dimensioni`). `nessun_vincolo` più fedele. |
| vincoli.fatturato | non_noto | IMPRECISO (basso) | Come sopra. |
| vincoli.spesa | vincolo | ok | Minimo 4.000 € (riga 167). |
| vincoli.regime_aiuto | vincolo | ok | De minimis (riga 393). |
| completezza | bando_ufficiale | ok | Bando integrale letto. |
| fonti | per articolo | ok | Precise e verificabili (es. `territorio_province` dalla FAQ, `spese_ammesse` da art. 7 comma 5 + FAQ). Mancano solo le fonti di elenchi vuoti e `chiuso_il`, che il prompt non chiede in modo chiaro. |
| avvertenza 1 (chiusura anticipata) | "non è possibile sapere se e quando il bando si sia effettivamente chiuso" | IMPRECISO (medio) | Giusta e al primo posto, ma troppo prudente sul "se": il titolo della notizia dice proprio "Chiusura anticipata termini presentazione domande" (riga 861). Doveva dire chiaramente "la pagina annuncia la chiusura anticipata dal 14/09/2026; il testo dell'avviso non è stato letto: verificare prima di proporre il bando". |
| avvertenza 2 (spesa massima) | "il bando non indica un importo massimo di spesa" | IMPRECISO (basso) | Vera ma inutile: il limite pratico è il contributo di 8.000 €. È quasi una ripetizione della sintesi (regola 21). |
| avvertenza 3 (ATECO) | "il bando non elenca codici ATECO" | ok | Vera, utile per spiegare il `non_noto`. |
| avvertenza 4 (forme giuridiche) | "si applica solo il requisito generale" | ok nel contenuto | Contraddice però `vincoli.forme_giuridiche = non_noto` (vedi sopra). |
| avvertenze mancanti | — | MANCANTE (basso) | Regola 21: l'orario di chiusura **alle 13:00** (non a fine giornata) non è in avvertenze; è comunque in `ora_scadenza` e nella sintesi. Utile anche l'art. 11 comma 4 (righe 504-507): le domande non finanziate possono essere recuperate con lo scorrimento **fino al 31/08/2027**, informazione preziosa proprio perché lo sportello si è chiuso subito. |

**Regole nuove del prompt (15-22):**
- **15 Ente e gestore:** rispettata. Ente = Camera di Commercio; `gestore` null, giusto perché InfoCamere fornisce solo la piattaforma.
- **16 Esclusioni di settore:** rispettata. Il bando non ne scrive, gli elenchi sono vuoti, e non ha inventato le esclusioni del de minimis.
- **17 Requisiti separati dal punteggio:** rispettata. I premi (rating, parità di genere, PID-Next) stanno nella sintesi e in `requisiti_speciali_premiali`, non nei requisiti. DURC, polizza catastrofale, una sola domanda, vincoli sui fornitori: tutti presenti. Il regime di aiuto non è ripetuto nei `requisiti`, ma c'è nel campo apposito e nella sintesi.
- **18 Agevolazioni miste:** non si applica (solo voucher); nessun "100%" sbagliato.
- **19 Premi:** rispettata in modo esemplare: `contributo_massimo` 8000 senza premi, premi con importi nella sintesi.
- **20 Tempi delle spese:** rispettata in pieno (da quando, termine del progetto, termine del rendiconto).
- **21 Avvertenze senza supposizioni:** quasi rispettata. Nessuna supposizione inventata; semmai il contrario (troppa prudenza sulla chiusura anticipata). Un'avvertenza superflua (spesa massima) e manca quella sull'orario delle 13:00.
- **Fonti (regola 3):** rispettata, con articoli e commi.

**Controllo preliminare di Haiku:** la **decisione di chiamare Sonnet era giusta**. Haiku ha visto solo il bando tagliato a metà dell'art. 7 comma 5 (`preliminare_568.txt`, righe 19-281: niente art. 10 con le date, niente pagina, niente FAQ). Valori: `per_imprese` si, `edizione_in_corso` si ("Anno 2026", esclusi i beneficiari 2024 e 2025), `testo_bando` si: tutti giusti. `stato` non_noto con motivo "data di scadenza non indicata": **giusto rispetto a quello che vedeva**. Rispetto ai documenti completi lo stato vero era **dubbio tra aperto (date) e chiuso (notizia del 14/09)**: se Haiku avesse visto la pagina avrebbe potuto rispondere `chiuso` e bloccare Sonnet. Qui non sarebbe stato grave (la scheda serve comunque, anche per lo scorrimento fino al 31/08/2027), ma il caso mostra che Haiku legge solo il primo documento lungo e non vede mai la pagina, dove stanno date e notizie. Inoltre nel messaggio di sistema di Haiku è rimasto il segnaposto **`{{data_oggi}}` non sostituito** (`preliminare_568.txt`, riga 5); la data c'è comunque nel messaggio dell'utente.

**Pericolosità:** l'unico rischio serio per l'abbinamento è a monte: la scheda risulterà "aperta" fino al 15/10 anche se la pagina annuncia la chiusura anticipata. Il modello ha fatto la cosa giusta (avvertenza al primo posto), ma l'avvertenza è troppo debole e il sistema non ha un modo per trasformarla in stato. Secondo rischio: i `non_noto` su forme giuridiche ed età rendono il bando "da verificare" per tutti, mai "compatibile".

**Voto: 4/5.** Scheda accurata, nessun numero o data sbagliati, regole nuove rispettate. Si perde un punto per la mancata notizia di chiusura (raccolta) e per i `non_noto` troppo prudenti.

**Errori: INVENTATO 0 · SBAGLIATO 0 · MANCANTE 4 · IMPRECISO 6.**
- MANCANTE: premiale PID-Next (`altro`); "siti web" tra le spese escluse; documenti a pena di esclusione (preventivi, SELFI4.0) e sicurezza sul lavoro nei requisiti; avvertenze su orario 13:00 e scorrimento fino al 31/08/2027.
- IMPRECISO: `cosa_finanzia` incompleto presentato come completo; `vincoli` forme_giuridiche, eta_impresa, dipendenti, fatturato `non_noto` invece di `nessun_vincolo` (4); avvertenza 1 troppo prudente sul "se" della chiusura. (L'avvertenza 2 superflua è un difetto di stile, non contato.)

**Problemi generali emersi da questa scheda:**
1. **Raccolta: le notizie sulla pagina del bando non vengono seguite.** Una notizia "chiusura anticipata", "proroga", "riapertura" o "graduatoria" nella pagina ufficiale deve essere scaricata e messa **prima** degli altri documenti (è la cosa più recente). Serve anche un controllo semplice senza IA: se la pagina contiene "chiusura anticipata" o "esaurimento delle risorse", la plancia segna il bando "probabilmente chiuso, da verificare".
2. **Manca uno stato "chiuso annunciato ma data non nota".** Oggi `chiuso_il` accetta solo una data certa. Proposta: permettere a Sonnet di scrivere in `chiuso_il` la data della notizia quando il titolo dice esplicitamente "chiusura anticipata", con un'avvertenza, oppure aggiungere un segnale `chiusura_segnalata: si`.
3. **Haiku non vede la pagina.** Il preliminare riceve solo l'inizio del primo documento (il bando lungo), quindi non vede mai date, stato e notizie della pagina. Meglio mandargli la pagina (senza menu) più l'inizio del bando, o un pezzo di ciascun documento. Correggere il segnaposto `{{data_oggi}}` non sostituito.
4. **Regola dei tre stati in conflitto con l'esempio.** Il prompt (regola 4) vuole `nessun_vincolo` solo se il bando lo dice espressamente; l'esempio in `SCHEDA_BANDO.md` usa `nessun_vincolo` quando il bando ha un elenco chiuso di requisiti che non nomina quel limite. Sonnet qui ha mescolato le due letture. Serve una frase: "se l'elenco dei requisiti di ammissione è completo e non nomina un limite, quel vincolo è `nessun_vincolo`; `non_noto` solo se mancano documenti o il testo è ambiguo".
5. **`sportello_valutativo` non è segnalato come urgente** nella regola di abbinamento (SCHEDA_BANDO.md: solo `sportello` e `click_day`), ma è un ordine di arrivo come lo sportello: questo bando si è esaurito, a quanto pare, il giorno dell'apertura. Anche la definizione "con punteggio minimo" va allargata a "con verifica di merito".
6. **Campi fondo perduto per aiuti non misti:** il prompt dice di usarli solo per aiuti misti, l'esempio a mano li compila anche per il fondo perduto puro. Decidere una sola regola.
7. **Pagina con molto menu:** circa 70 righe di voci di menu (righe 715-784) prima del contenuto; il filtro di menu e piè di pagina non funziona per ba.camcom.it.

---

## 254 — CCIAA Caserta, contributi per fiere in Italia e all'estero (1° gennaio - 30 aprile 2026)

*Revisione del 25/09/2026. Confronto fatto solo con il testo del prompt `scheda_254.txt` (numeri di riga tra parentesi) e con il prompt di Haiku `preliminare_254.txt`. Nessun sito consultato.*

**Materiale in ingresso:** buono. Nessun documento tagliato. Ordine: (1) **Bando** completo, artt. 1-13 (righe 122-629); (2) **Modello A di domanda** (righe 631-1069); (3) **pagina ufficiale** della Camera (righe 1071-1111); (4) **Modello B de minimis** (righe 1113-1306), con il nome monco "odello B de minimis" perché il testo del link sulla pagina è spezzato ("M / odello B", righe 1100-1101); (5) **Calendario fiere vuoto** (righe 1308-1310, "nessun testo leggibile", riga 118). Mancano: Modello C (autocertificazione INPS/INAIL) e Modello D (rendicontazione), elencati sulla pagina (righe 1102-1103) ma non arrivati; la delibera di Giunta del 27/02/2026 che approva il bando (citata a riga 155). Nessuno dei mancanti cambia i campi della scheda. Da notare che qui il **modulo di domanda è stato utile**: contiene l'unica indicazione sulla dimensione d'impresa (righe 904-911) e una frase sul cumulo che contraddice il bando (righe 747-752).

| Campo | Valore di Sonnet | Esito | Nota |
|---|---|---|---|
| titolo | "Contributi per favorire le produzioni del territorio ... (1° gennaio - 30 aprile 2026)" | ok | Righe 124-127 e 1085. |
| ente / gestore | CCIAA di Caserta / null | ok | Regola 15 rispettata: la Camera finanzia e gestisce direttamente (artt. 1, 9, righe 129, 385-393). La fonte "Art. 1" non nomina Caserta (riga 129): lo dice la pagina (riga 1089). Lieve. |
| url | pagina ufficiale ce.camcom.it | ok | Riga 114. |
| territorio (testo) | "sede legale e/o sede operativa in provincia di Caserta" | ok | Art. 5, riga 203. |
| territorio_regioni / province / comuni | ["CAM"] / ["CE"] / [] | ok | |
| sede_richiesta | legale_o_operativa | ok | Art. 5 righe 203 e 209-212. La condizione che l'unità locale debba **ospitare attività produttiva** (non ufficio, deposito, magazzino) sta nel testo di `a_chi_si_rivolge`/`linee`, non in un campo: vedi problemi generali. |
| data_apertura / ora_apertura | null / null | ok | Il bando dice "dalla data di pubblicazione sull'Albo camerale" (riga 362-363) senza data. Giusto non usare la data della notizia (13/03/2026, riga 1086); l'avvertenza 2 lo spiega bene. |
| scadenza / ora_scadenza | 2026-03-31 / 12:00 | ok | Art. 8, riga 363; pagina riga 1088. |
| chiuso_il | null | ok | Nessuna chiusura anticipata scritta. |
| modalita_selezione | sportello | ok | Art. 9, righe 385-386, nonostante il titolo dell'articolo parli di "graduatoria" (riga 383). Bene. |
| sintesi | 5 righe | IMPRECISO (basso) | Corretta nei numeri (50%, 2.000-10.000 €, minimo 2.000 €, 150.000 €, PEC, sportello, 31/03 ore 12). "Fiere svolte tra il 1° gennaio e il 30 aprile" semplifica: conta la data di **inizio** della fiera (riga 476-477). Non dice che si può chiedere il contributo anche per una fiera **già conclusa** (riga 292: spese "che preventivano di sostenere o dichiarano di aver sostenuto"), informazione utile al cliente. |
| a_chi_si_rivolge | imprese con sede in CE, iscritte e attive, con attività produttiva e non di mera intermediazione | ok | Art. 5, righe 203-208. |
| soggetti_ammessi | ["impresa"] | ok | |
| forme_giuridiche ammesse/escluse | [] / [] | ok | Il bando non ne parla (cita solo i consorzi come possibili richiedenti, riga 212-213). |
| dimensioni_ammesse | ["micro","piccola","media"] | IMPRECISO (basso-medio) | Il **bando** dice solo "le imprese" (art. 5, riga 203) e non limita la dimensione. L'elenco viene dalle caselle del Modello A (righe 909-911), dove "grande impresa" non c'è. È una deduzione ragionevole e la fonte è citata onestamente, ma bando e modulo non coincidono e **manca l'avvertenza** (regola 2). Una grande impresa casertana verrebbe scartata dall'abbinamento senza spiegazione. |
| requisiti_speciali_obbligatori / premiali | [] / [] | IMPRECISO (medio) | Il vero filtro del bando è "attività di produzione di beni/servizi ... non mera intermediazione commerciale e/o distribuzione" (art. 5, righe 205-208; art. 11, righe 489-493). Non è esprimibile con i valori dell'elenco né con codici ATECO, e resta solo nel testo. Nessun premio o punteggio: premiali [] corretto. |
| dipendenti / fatturato min-max | null | ok | Non citati. (Nel JSON queste quattro chiavi compaiono **due volte**: vedi problemi generali.) |
| eta_impresa_min/max_mesi | null | ok | Basta essere "attive" alla domanda (art. 6 d, riga 238). |
| codici_ateco / esclusi / ateco_versione | [] / [] / null | ok nel valore | Il bando non usa codici. Vedi sopra per l'esclusione del commercio puro. |
| regime_aiuto | ["de_minimis"] | MANCANTE (basso) | L'art. 3 (righe 158-160) cita tre regolamenti: 2831/2023 (generale), **1408/2013 (agricolo)** e **717/2014 (pesca)**. Andava ["de_minimis","de_minimis_agricolo","altro"] con nota sulla pesca: il tetto de minimis di un'impresa agricola è diverso. |
| requisiti | elenco lungo | ok, con MANCANTE (basso) | Molto buono: diritto annuale, DURC con rigetto immediato, sicurezza, procedure concorsuali, difficoltà, antimafia, antiriciclaggio, restituzione aiuti, **polizza catastrofale** con esenzione agricola, niente contratti con la Camera, **vincoli sui fornitori**, **una sola domanda nel 2026**, spesa minima (regola 17 rispettata). Mancano: se chiede un consorzio, le consorziate non possono chiedere per la stessa fiera (riga 212-213); esclusione delle fiere in cui la Camera organizza una collettiva (righe 142-144, 485-486); pagamenti solo con bonifico, niente contanti né assegni (righe 427-429). |
| cosa_finanzia | partecipazione diretta come espositore, fiere in Italia nel calendario della Conferenza delle Regioni, estero | ok | Righe 132-141. Manca l'esclusione delle collettive camerali (vedi sopra). |
| tipo / tipi_agevolazione | voucher / ["voucher"] | ok | Parola del bando (riga 148, 448). Nella sostanza è un rimborso a fondo perduto del 50%, ma seguire il bando è corretto. |
| fondo perduto separato dal prestito | fondo_perduto_massimo, percentuale_fondo_perduto, finanziamento_massimo = null | ok | Nessun prestito. Regola 18 non si applica. |
| tema / temi | internazionalizzazione | ok | Riga 130. |
| categorie_spesa | ["fiere_eventi"] | ok | Art. 7, righe 282-286. |
| contributo_massimo / percentuale | 10000 / 50 | ok | Tabella art. 7, righe 332-337 (estero, sede legale): è il caso più ampio, come chiede la regola 11. |
| spesa_minima / spesa_massima | 2000 / null | ok | Righe 289-290, 487-488, 520-521. Nota: il bando è ambiguo sul valore esatto di 2.000 € ("non superi i 2.000" rende inammissibile anche 2.000 esatti, riga 289; "inferiore a 2.000", riga 487). Non segnalato; conta poco. |
| dotazione | 150000 | ok | Riga 147 e 1096. |
| spese_ammesse | tre voci, esclusi viaggio/vitto/alloggio, rendiconto entro 30 giorni, CUP | ok | Regola 20 rispettata: dice che il testo non indica da quando le spese sono ammissibili e dà il termine di rendicontazione (righe 408-410). Manca la riduzione proporzionale se lo stand è condiviso (righe 344-348). |
| linee | 5 linee (Campania 4.000, Italia fuori Campania 8.000, Italia sede operativa 2.000, estero sede legale 10.000, estero sede operativa 2.000) | ok | Coincidono con la tabella (righe 295-342) e con il Modello A (righe 699-712). Interpretare "sede operativa" come "sede operativa ma non legale" è coerente col Modello A (righe 704-706). Limite del formato: la differenza tra le linee è il **tipo di sede**, che la linea non può esprimere con un campo. |
| vincoli.territorio | vincolo | ok | |
| vincoli.soggetti | vincolo | ok | |
| vincoli.forme_giuridiche | non_noto | ok | Il bando non ne parla. |
| vincoli.dimensioni | vincolo | IMPRECISO (basso-medio) | Il vincolo esiste solo nel modulo, non nel bando (vedi `dimensioni_ammesse`). Accettabile, ma senza avvertenza. |
| vincoli.ateco | non_noto | ok nell'effetto | Nessun codice; il filtro "no mera intermediazione" non è in codici. `non_noto` porta l'abbinamento a "da verificare", che qui è la risposta prudente giusta. |
| vincoli.eta_impresa | non_noto | ok | |
| vincoli.requisiti_speciali | non_noto | IMPRECISO (basso) | C'è un requisito obbligatorio reale (attività produttiva) che non sta nell'elenco. Più corretto: `vincolo` con ["altro"] e spiegazione. L'effetto sull'abbinamento ("da verificare") è lo stesso. |
| vincoli.dipendenti | non_noto | ok | |
| vincoli.fatturato | non_noto | ok | |
| vincoli.spesa | vincolo | ok | Minimo 2.000 €. |
| vincoli.regime_aiuto | vincolo | ok | De minimis. |
| completezza | bando_ufficiale | ok | |
| fonti | per articolo | IMPRECISO (basso) | Quasi tutte giuste e verificabili. Sintesi cita artt. 1, 2, 5, 7, 8 ma lo sportello è all'art. 9; ente cita art. 1 che non nomina Caserta. |
| avvertenze | 5 | ok, con MANCANTE (medio) | La 1 (dotazione riferita alle fiere dal **1° aprile** all'art. 2, riga 146-147, contro 1° gennaio - 30 aprile a righe 127, 476-477, 1089) è un dubbio vero e ben trovato. La 2 e la 4 sono utili. La 3 ripete `spese_ammesse` (richiesta dalla regola 20: accettabile). La 5 **ripete i requisiti** e parla di una proroga al 31/03/2026 ormai passata: regola 21 non rispettata. **Manca** la contraddizione più utile per il commercialista: il bando ammette il cumulo con altri aiuti fino al 100% della spesa (art. 4, righe 171-178), mentre il Modello A fa dichiarare di **non** aver ricevuto né attendere altri aiuti pubblici per la stessa fiera (righe 747-752). Manca anche l'avviso che la dimensione viene solo dal modulo. |

**Pericolosità:** nessun errore alto. Il rischio pratico più serio per l'abbinamento è che il vero filtro del bando (imprese produttive, non commercio puro o distribuzione) resti solo nel testo: il motore segnalerà "da verificare" per tutti, senza dire perché. Per la consulenza, la contraddizione sul cumulo tra bando e modulo avrebbe meritato un'avvertenza.

**Regole nuove (15-22):**
- 15 ente/gestore: **rispettata** (CCIAA ente, gestore null, corretto).
- 16 esclusioni di settore nell'elenco: **non applicabile** in senso stretto (nessun codice). Il bando esclude una categoria di attività ("mera intermediazione commerciale e/o distribuzione") che il formato non sa rappresentare; Sonnet giustamente non ha inventato codici (per esempio sezione G), ma non l'ha segnalata in avvertenze.
- 17 requisiti separati dal punteggio: **rispettata**; nessun punteggio mescolato; DURC, polizza, fornitori, una sola domanda tutti presenti.
- 18 agevolazioni miste: non applicabile, campi del prestito correttamente null.
- 19 premi: non applicabile.
- 20 tempi delle spese: **rispettata** (frase richiesta presente, termine di rendiconto presente). Mancava l'informazione che la fiera può essere già conclusa al momento della domanda.
- 21 avvertenze senza supposizioni: **quasi rispettata**. Niente deduzioni inventate; ma la quinta avvertenza ripete i requisiti.
- 22 pagine di catalogo: non applicabile.
- Fonti (regola 3): rispettata, con due imprecisioni lievi.

**Controllo preliminare di Haiku:** risposta `per_imprese=si`, `edizione_in_corso=si`, `stato=chiuso`, `testo_bando=si`. **Decisione giusta: Sonnet non andava chiamato.**
- Haiku vedeva il bando fino all'art. 8 compreso (fine documento a riga 280 di `preliminare_254.txt`), quindi la scadenza "ore 12.00 del 31 marzo 2026" (riga ~260 del preliminare, riga 363 della scheda) era sotto i suoi occhi.
- Esiste **una sola finestra** di domanda, valida per tutte e cinque le linee (art. 8, riga 363); la pagina la conferma (riga 1088). Le date 1° gennaio - 30 aprile riguardano le **fiere**, non le domande; il "1° aprile" dell'art. 2 è un periodo di fiere (probabile refuso), non una seconda finestra. La Camera si riserva di riaprire i termini (riga 153), ma nessun documento dice che l'abbia fatto. Oggi (25/09/2026) il bando è chiuso.
- `edizione_in_corso=si` è accettabile (è l'edizione "I quadrimestre 2026"), ma il titolo della pagina (riga 1085) fa capire che esistono edizioni per quadrimestre: il cliente di un commercialista vorrebbe sapere se c'è il II o III quadrimestre 2026, che sarà un bando separato.
- Tutti e quattro i valori sono giusti sia rispetto a quello che Haiku vedeva sia rispetto ai documenti completi.

**Voto: 4/5.** Scheda fedele, senza invenzioni, con linee complete e un'avvertenza acuta sulla dotazione. Le mancanze sono di dettaglio (regime agricolo e pesca, contraddizione sul cumulo, dimensione dedotta dal modulo senza avviso, filtro "solo imprese produttive" non strutturato). Ha poca importanza pratica perché il bando è chiuso.

**Conteggio errori:** INVENTATO 0 · SBAGLIATO 0 · MANCANTE 3 (regime agricolo/pesca; avvertenza sul cumulo bando vs modulo; requisiti minori: consorzi, collettive, pagamenti tracciabili) · IMPRECISO 6 (dimensioni dal solo modulo; requisito "attività produttiva" non strutturato; vincoli.requisiti_speciali; sintesi "svolte" invece di "iniziate" e fiere già concluse; avvertenza 5 ripetitiva; fonti).

**Problemi che sembrano generali:**
1. **Le linee non hanno un campo per il tipo di sede.** Qui (e in molti bandi camerali) il massimale cambia con sede legale o solo operativa: senza `sede_richiesta` nella linea, il motore non sa dire al cliente quale linea gli spetta. Aggiungere `sede_richiesta` ai campi ammessi nelle linee.
2. **Esclusioni di settore non espresse in ATECO** ("non mera intermediazione commerciale o distribuzione", "attività produttive"). Frequenti nei bandi camerali. Serve un modo per dirle: per esempio consentire `requisiti_speciali_obbligatori = ["altro"]` con una nota, oppure un campo testo "esclusioni di attività" letto dall'abbinamento come "da verificare, motivo: ...".
3. **Modulistica:** SCHEDA_BANDO.md dice "niente modulistica", ma qui il modulo di domanda aveva due informazioni che il bando non ha (dimensione, dichiarazione sul cumulo). Meglio tenerlo in coda, dopo bando e FAQ, e chiedere nel prompt di segnalare le differenze tra modulo e bando.
4. **`regime_aiuto` non ha un valore per il de minimis pesca** (Reg. 717/2014); aggiungere `de_minimis_pesca`.
5. **Bandi a edizioni ripetute** (per quadrimestre, per anno): la raccolta dovrebbe collegare le edizioni e cercare quella successiva quando la corrente è chiusa.
6. **Raccolta:** nome dell'allegato spezzato ("odello B") perché il testo del link va a capo; Modelli C e D non arrivati; calendario fiere vuoto come nella 2587b (il calendario vero è su regioni.it, fonte esterna).
7. **JSON con chiavi doppie:** `dipendenti_min/max` e `fatturato_min/max` compaiono due volte nella risposta. Qui i valori coincidono (null), ma se differissero il sistema terrebbe in silenzio l'ultimo. Il programma che legge la risposta dovrebbe accorgersi delle chiavi doppie e segnalarle.

---

## 610 — Liguria, attrazione di produzioni audiovisive 2026 (PR FESR azione 1.3.4, dal catalogo incentivi.gov.it)

*Numeri di riga = righe di `scheda_610.txt`. L'unica fonte controllata è il testo che Sonnet ha ricevuto.*

**Materiale in ingresso:** buono, e questa volta la raccolta ha fatto la cosa giusta. L'annuncio 4178 viene dal catalogo incentivi.gov.it, ma il sistema ha seguito il "link all'ente" e ha passato come pagina ufficiale **il decreto della Regione** (`decretidigitali.regione.liguria.it/.../Decreto-5716-2026.pdf`, riga 114), non la scheda di catalogo. Il testo del catalogo non è stato passato, quindi la regola 22 non entra in gioco. C'è **un solo documento**, un PDF di 189.263 caratteri tagliato a 150.000 (riga 118). Al suo interno, in quest'ordine:
- premesse e dispositivo del decreto (righe 122-493);
- **Allegato 1**: un **altro bando**, "Interventi a sostegno dello sviluppo e produzione di progetti audiovisivi" (750.000 €, solo imprese con sede in Liguria, righe 501-~1720);
- **Allegato 2**: il bando di questa scheda, "Interventi a sostegno dell'attrazione di produzioni audiovisive" (1.000.000 €, righe 1736-2603), **letto per intero** fino all'art. 17 (privacy);
- tagliati: l'informativa privacy (Allegato A) e lo schema di convenzione Regione-FILSE (Allegato 3), che non servono alla scheda.

Quindi il decreto approva **due bandi** della stessa azione 1.3.4 (righe 250-259 e 383-390). Sonnet ha scelto quello giusto (l'Allegato 2) e non ha mescolato i due, nonostante siano quasi identici. Il bando giusto però era il **secondo** nel PDF: con un Allegato 1 un po' più lungo sarebbe stato tagliato. Manca anche la pagina del gestore (filse.it: modulistica, FAQ).

| Campo | Valore di Sonnet | Esito | Nota (riga) |
|---|---|---|---|
| titolo | "PR FESR Liguria 2021-2027 Azione 1.3.4 - ... attrazione di produzioni audiovisive - Bando 2026" | ok | 1755-1757 |
| ente / gestore | Regione Liguria / FI.L.S.E. S.p.A. | ok | Ente = chi finanzia (390, 418-421); FILSE è l'organismo intermedio che gestisce il bando (1778-1780). |
| url | PDF del decreto | ok | È il documento ufficiale dell'ente, non il catalogo. Una pagina di presentazione su filse.it sarebbe più comoda per il cliente, ma la raccolta non ce l'ha. |
| territorio | "Liguria" | IMPRECISO (basso) | Il bando dice che le **iniziative** vanno realizzate in Liguria (1855), non dove deve stare l'impresa. Il testo doveva dirlo: "progetto girato o speso in Liguria; imprese italiane, europee o extraeuropee". |
| territorio_regioni + vincoli.territorio | ["LIG"], `vincolo` | **SBAGLIATO (alto)** | L'abbinamento confronta questo elenco con la **sede** del cliente (SCHEDA_BANDO.md, tabella abbinamento). Questo bando però serve ad **attirare produzioni da fuori**: possono partecipare imprese "italiane europee o extraeuropee" (1791-1792, 1767-1768, 1860). Non chiede nessuna sede in Liguria, a differenza dell'Allegato 1, che la chiede espressamente (568, 577, 640-642). Con LIG come vincolo, una casa di produzione di Roma o Milano, cioè il destinatario tipico, verrebbe **scartata**. Valori corretti: `[]` e `nessun_vincolo`, con un'avvertenza che il vincolo riguarda il luogo delle riprese o delle spese. |
| territorio_province / comuni | [] / [] | ok | |
| sede_richiesta | null | ok | Il bando non chiede una sede. Coerente con la correzione proposta sopra. |
| data_apertura / scadenza | 2026-09-22 / 2026-10-02 | ok | 2000-2001 |
| ora_apertura / ora_scadenza | null / null | **MANCANTE (medio)** | Domande "dal lunedì al venerdì dalle ore 08.30 alle ore 17.30" (2003). Il 2/10/2026 è un venerdì, quindi la chiusura effettiva è **alle 17:30**. Sonnet l'ha scritto nelle avvertenze ma ha lasciato vuoti i campi fatti apposta (regola 6): un promemoria automatico sulla scadenza direbbe "fino a fine giornata". |
| chiuso_il | null | ok | |
| modalita_selezione | graduatoria | ok | "procedura valutativa a graduatoria" (2042), con finestra fissa. L'"ordine cronologico" di 2051 riguarda solo il controllo formale. |
| sintesi | cosa finanzia, a chi, 300.000 €, 35/40/60 % secondo il punteggio, 22/9-2/10, FILSE, graduatoria | IMPRECISO (medio) | Numeri giusti (1967-1981), ma due frasi portano fuori strada: "percentuale **sul budget**" e "il progetto deve **costare** almeno 300.000 euro". Per il bando (1890, 1916-1917) sono le **spese ammissibili, cioè sostenute in Liguria**, a dover arrivare ad almeno 300.000 €, e la percentuale si calcola su quelle, non sul costo totale del film. Per un commercialista è la differenza tra un contributo possibile e uno impossibile. Mancano il punteggio minimo di 50 sui criteri 1 e 5, il fatto che basta uno zero su uno degli elementi del criterio 1 per essere esclusi (2163-2168) e l'anticipo del 40 % con fideiussione (2299-2303). |
| a_chi_si_rivolge | PMI di produzione audiovisiva italiane, UE o extra-UE, ATECO 59.11.00, indipendenti, con contratto di distribuzione ed esperienza | ok (lieve MANCANTE) | 1785-1805. Manca "in forma singola o associata" (1785). |
| soggetti_ammessi | ["impresa"] | ok | Le associazioni sono ammesse solo nell'Allegato 1 (561): Sonnet non le ha mescolate. |
| forme_giuridiche_ammesse / escluse | [] / [], `non_noto` | ok (vedi vincoli) | Il bando non ne parla. |
| dimensioni_ammesse | ["piccola","media"] | **SBAGLIATO (alto)** | "piccole e medie imprese", con rinvio alla Raccomandazione 2003/361/CE e all'allegato 1 del Reg. 651/2014 (1785-1789). In quella definizione le **micro imprese fanno parte delle PMI**. Mancando "micro", l'abbinamento escluderebbe proprio le micro imprese, che nel settore delle produzioni indipendenti sono la maggioranza. Valore corretto: ["micro","piccola","media"]. |
| eta_impresa_min/max_mesi | null / null | ok | L'"esperienza con credit ufficiali" (1805) non è un'età dell'impresa. |
| requisiti_speciali_obbligatori | [] | ok | |
| requisiti_speciali_premiali | ["giovanile","femminile","rating_legalita"] | ok | 2171-2228. Precisazione utile: contano **solo in caso di parità** di punteggio, e la sintesi non lo dice. |
| dipendenti / fatturato min-max | tutti null | ok | |
| codici_ateco | ["59.11.00"] | ok | 1794. Per le imprese UE vale il NACE 59.11 (1795), detto nei requisiti. |
| codici_ateco_esclusi | [] | ok | Il bando non esclude settori. Le opere escluse (pornografiche, pubblicitarie, talk show...) non sono codici ATECO e stanno giustamente in `cosa_finanzia` (1875-1880). |
| ateco_versione | "2025" | ok | "codice ATECO 2025 59.11.00" (1794). |
| regime_aiuto | ["de_minimis"] | ok | Reg. 2023/2831 (1961-1964). |
| requisiti | ammissione, esclusioni, DURC, polizza catastrofale, una domanda per tipologia, de minimis e cumulo | ok (lieve MANCANTE) | Buono, niente punteggi dentro (1791-1851, 1983-1984). Mancano: PEC attiva alla data della domanda (2008-2010), firma digitale e marca da bollo (1998, 2004), esclusione per delocalizzazione (1840-1844) e, come chiede la regola 17, la **fideiussione per l'anticipo** del 40 % (2299-2303). |
| cosa_finanzia | lungometraggi ≥52', serie TV ≥90', 30 % dei giorni di ripresa o 20 % della spesa in Liguria, esclusioni | ok | 1860-1880 |
| tipo / tipi_agevolazione | fondo_perduto / ["fondo_perduto"] | ok | 1961 |
| tema / temi | cultura / [cultura, turismo] | ok | "turismo" regge: filiere turistiche (1764) e criterio 2 sulla destagionalizzazione turistica (2111-2113). |
| categorie_spesa | personale, macchinari_attrezzature, altro | ok | 1918-1930 |
| contributo_massimo / percentuale | 300000 / 60 | ok | 1969-1981. 60 è il caso più ampio (punteggio > 90), come chiede la regola 11. |
| fondo_perduto_massimo / percentuale_fondo_perduto | null / null | MANCANTE (basso) | Nella scheda di esempio di SCHEDA_BANDO.md, per un bando tutto a fondo perduto, questi campi sono uguali a contributo_massimo e percentuale (15000 / 60). Qui dovevano essere 300000 / 60. La specifica è ambigua ("quando l'aiuto unisce prestito e fondo perduto"). |
| finanziamento_massimo | null | ok | |
| spesa_minima / spesa_massima | 300000 / null | ok | 1890. Si tratta della spesa ammissibile, non del costo del film (vedi sintesi). |
| dotazione | 1000000 | ok | 1773. Non ha confuso i 1.000.000 con i 750.000 dell'Allegato 1 né con i 2.012.612,09 € del decreto. |
| spese_ammesse | voci, limiti 15 % e 10 %, esclusioni, IVA, tempi | ok | 1896-1948 e 2332-2334. Contiene tutti e tre i tempi della regola 20: spese dal 1/6/2024 per iniziative non concluse alla domanda, fine entro 12 mesi dalla concessione, rendiconto entro 60 giorni. Mancano il CUP sulle fatture (1905-1914) e il divieto di pagamenti in contanti (1950-1951). |
| linee | [] | ok | Lungometraggi e serie TV hanno le stesse regole (1969-1972). |
| vincoli: soggetti, dimensioni, ateco, spesa, regime_aiuto | `vincolo` | ok | Su dimensioni lo stato è giusto, è l'elenco a essere sbagliato. |
| vincoli: territorio | `vincolo` | SBAGLIATO | Vedi territorio_regioni. |
| vincoli: forme_giuridiche, eta_impresa, dipendenti, fatturato | `non_noto` | IMPRECISO (basso) | Il bando è stato letto tutto e non pone questi limiti. Sonnet ha applicato alla lettera la regola 4 ("nessun_vincolo solo se il bando lo dice espressamente"). La scheda di esempio in SCHEDA_BANDO.md, per un bando letto per intero, usa invece `nessun_vincolo`. Risultato: per ogni cliente quattro "da verificare" inutili. Incoerente anche con requisiti_speciali (sotto). |
| vincoli: requisiti_speciali | `nessun_vincolo` | ok | Nella sostanza giusto, ma segue un criterio diverso dalle quattro voci sopra. |
| completezza | bando_ufficiale | ok | |
| fonti | 24 voci, con allegato e punto | IMPRECISO (basso) | Precise e verificabili. Mancano però le fonti di `temi`, `tipi_agevolazione`, `categorie_spesa`, `url` e `requisiti_speciali_obbligatori` (la regola 3 le chiede). Formato a elenco `{campo, fonte}` invece dell'oggetto del prompt: lo impone lo schema (righe 3532-3545), non è un errore. |
| avvertenze | 3 | ok, con una mancanza | (1) Il taglio è descritto con esattezza. Dire che le parti tagliate "non riguardano i requisiti" è una deduzione, ma il decreto la sostiene (447-454, 2598-2600). (2) Orario 8:30-17:30 nei giorni feriali: giusto e utile. (3) "Non c'è una spesa massima": vera ma poco utile. **MANCANTE (basso):** non avverte che lo stesso decreto approva **un secondo bando** (Allegato 1, 750.000 €, per imprese con sede in Liguria, con sviluppo e produzione e anche web serie e cortometraggi, 501-672). Per un cliente ligure potrebbe essere quello giusto. |

**Regole nuove del prompt (15-22):**
- **15 Ente e gestore**: rispettata (Regione Liguria / FILSE).
- **16 Esclusioni di settore**: rispettata. Non ci sono esclusioni ATECO, e le opere escluse non sono state trasformate in codici.
- **17 Requisiti separati dal punteggio**: rispettata. Nei `requisiti` non ci sono criteri di punteggio. Ci sono DURC, polizza catastrofale, regime di aiuto e una domanda per tipologia. Mancano la fideiussione per l'anticipo e, nella sintesi, il punteggio minimo di 50 e il fatto che i criteri premiali contano solo in caso di parità.
- **18 Agevolazioni miste / 19 Premi**: non si applicano. Nessun "100 %" sbagliato.
- **20 Tempi delle spese**: rispettata in pieno (dal 1/6/2024, 12 mesi, 60 giorni).
- **21 Avvertenze senza supposizioni**: rispettata. L'orario diverso da fine giornata è in avvertenza. Il vincolo "iniziative non concluse alla data della domanda" è in `spese_ammesse` ma non in avvertenze, dove la regola lo chiede.
- **22 Pagine di catalogo**: non si applica, perché la raccolta ha passato direttamente il documento dell'ente.
- **3 Fonti**: quasi sempre precise, con alcune voci mancanti (vedi tabella).

**Controllo preliminare di Haiku:** la **decisione era giusta** (chiamare Sonnet). Haiku ha visto solo le premesse del decreto, fino a circa la riga 339 del prompt completo, senza nessuna data di apertura.
- `per_imprese = si`: giusto.
- `edizione_in_corso = si`: giusto.
- `stato = non_noto`: giusto per quello che vedeva. In realtà il bando è **aperto** (22/9-2/10, oggi 25/9).
- `testo_bando = solo_sintesi` con motivo "i bandi completi sono negli allegati non forniti": **sbagliato**. Rispetto ai documenti completi, gli allegati sono nello stesso PDF e l'Allegato 2 è arrivato per intero a Sonnet (1736-2603). È sbagliato anche rispetto a quello che Haiku vedeva: il prompt definisce `si` anche per "il decreto che lo approva", e `solo_sintesi` per pagine di riepilogo, notizie o cataloghi, cosa che un decreto non è. Le premesse dicono chiaramente che i bandi sono "allegati al presente provvedimento" (250-251). "Non forniti" è una supposizione. Qui non ha fatto danni, perché `solo_sintesi` non blocca la chiamata. Se però il valore finisse in plancia o servisse a scegliere il modello, sarebbe un'etichetta falsa.

**Errori:** INVENTATO 0 · SBAGLIATO 2 · MANCANTE 4 · IMPRECISO 4.

**Voto: 3/5.** Da leggere è molto buona: niente di inventato, numeri, date, spese e tempi giusti, nessuna confusione tra i due bandi del decreto. Per l'abbinamento però ha **due errori gravi che colpiscono proprio il pubblico del bando**. Il vincolo "Liguria" sulla sede scarta le case di produzione di fuori regione, che il bando vuole attirare. La mancanza di "micro" scarta le micro imprese. Va corretta prima di usarla nel motore.

**Problemi generali emersi:**
1. **Luogo del progetto e sede dell'impresa sono due cose diverse**, ma la scheda ha un solo gruppo di campi `territorio_*`, che l'abbinamento legge come sede. Serve una regola nel prompt: "territorio_regioni riguarda dove deve stare la sede; se il bando chiede solo che il progetto si svolga in una regione, elenchi vuoti, `nessun_vincolo` e un'avvertenza". Meglio ancora un campo `luogo_progetto` separato.
2. **"PMI" va tradotto sempre in micro + piccola + media.** Aggiungere al prompt: "piccole e medie imprese / PMI secondo la Raccomandazione 2003/361 comprende le micro".
3. **Un decreto che approva più bandi**: la raccolta ne ricava una sola scheda. Il secondo bando (Allegato 1) resta senza scheda, a meno che non esista un altro annuncio. Inoltre il bando giusto può finire dopo il taglio dei 150.000 caratteri. Proposte: nella raccolta, spezzare il PDF per "Allegato numero N" e passare prima l'allegato il cui titolo corrisponde all'annuncio; in plancia, segnalare "il decreto contiene altri bandi".
4. **Contraddizione tra prompt e manuale su `nessun_vincolo`**: la regola 4 lo vuole solo se il bando lo dice espressamente, mentre la scheda di esempio lo usa quando il bando, letto per intero, non pone il limite. Va deciso quale delle due vale. Con la regola attuale ogni bando letto per intero produce molti "da verificare" inutili.
5. **Ore di apertura e chiusura**: Sonnet le trova ma le mette in avvertenza e lascia vuoti i campi. Il prompt dovrebbe dire: "se le domande si inviano solo in certe fasce orarie, `ora_scadenza` è l'ultima ora dell'ultimo giorno".
6. **`fondo_perduto_massimo` per bandi tutti a fondo perduto**: la specifica è ambigua. Stabilire che si compila sempre quando c'è fondo perduto.
7. **La base di calcolo del contributo** (spesa ammissibile o costo del progetto) andrebbe chiesta esplicitamente nella sintesi quando il bando ammette solo una parte delle spese (qui solo quelle sostenute in Liguria).
8. **Haiku e `testo_bando`**: istruire Haiku che un decreto di approvazione con "allegati" nel titolo non vuol dire allegati mancanti. Se non vede articoli e requisiti nel pezzo che legge, deve rispondere `si` (decreto) oppure avere a disposizione un valore `incerto`.

---

## 416 — Voucher Turismo per la sicurezza pubblica 2026 (Camera di Commercio del Sud Est Sicilia)

**Materiale in ingresso:** un solo documento, ma è quello giusto. La raccolta è partita dalla notizia sul sito camerale (`.../it/blog/bando-la-concessione-di-voucher-...`), il cui link porta direttamente al PDF "delibera commissario 54-2026 (giunta) All. bando turismo ... DEMINIMIS anno 2026.pdf" (scheda_416.txt righe 114, 122). È il **testo integrale del bando** (art. 1-17, letto per intero fino a riga 582, nessun taglio: riga 118). È l'edizione giusta: "Anno 2026" (r. 127), cita il decreto MIMIT del 17 marzo 2026 (r. 138) e il progetto Turismo 20% 2026-2028 (r. 153).

Cosa manca:
- **Il testo della notizia**: siccome il link portava al PDF, la pagina della notizia non è stata passata come documento. È un peccato proprio qui, perché le date nel bando sono sbagliate (vedi sotto) e la notizia probabilmente riporta quelle vere.
- La delibera del commissario n. 54/2026 che approva il bando (è arrivato solo l'allegato) e la modulistica (in "Amministrazione Trasparente", r. 416-418).
- L'indirizzo ha spazi non codificati (r. 114): il link mostrato al cliente potrebbe non aprirsi. È un problema della raccolta.

**Il problema principale è nel bando stesso.** L'art. 10 dice che le domande vanno presentate "dalle ore 11:00 del 22 luglio 2025 alle ore 21:00 del 30 novembre 2025" (r. 362-363). Per un bando "Anno 2026" è chiaramente un errore di copia dall'edizione 2025. La prova più forte: l'art. 11 cita il D.lgs. 27 novembre 2025, n. 184 (r. 421), una legge uscita **dopo** la presunta apertura del luglio 2025, e l'art. 1 cita un decreto del marzo 2026 (r. 138). Sonnet se n'è accorto (avvertenza 1), ma ha comunque scritto le date del 2025 nei campi.

| Campo | Valore di Sonnet | Esito | Nota |
|---|---|---|---|
| titolo | titolo completo 2026 | ok | r. 124-127. |
| ente / gestore | Camera di Commercio del Sud Est Sicilia / null | ok | È lei che stanzia i soldi (r. 172) e gestisce direttamente. ReStart (r. 361) è solo la piattaforma per le domande, non un gestore. |
| url | PDF del bando | ok (difetto della raccolta) | Contiene spazi non codificati; sarebbe meglio anche il link della notizia. |
| territorio | "Circoscrizione ... (Catania, Ragusa, Siracusa)" | ok | Il bando dice solo "circoscrizione territoriale della Camera di Commercio del Sud Est Sicilia" (r. 215-216). Le tre province vengono dall'annuncio (r. 112) e sono giuste: la Camera Sud Est copre Catania, Ragusa e Siracusa. |
| territorio_regioni / province / comuni | ["SIC"] / ["CT","RG","SR"] / [] | ok | Sigle corrette. La fonte citata ("art. 4") però non contiene i nomi delle province: andava scritto "annuncio". |
| sede_richiesta | legale_o_operativa | ok | "sede legale e/o unità locali, oggetto dell'intervento" (r. 215). La condizione che l'unità locale sia iscritta con attività dal 31/12/2024 (r. 216-217) è riportata in `a_chi_si_rivolge`. |
| data_apertura / ora_apertura | 2025-07-22 / 11:00 | **SBAGLIATO (pericolo alto)** | Copiato alla lettera da r. 362, ma è un refuso evidente (vedi sopra). Il sistema calcola lo stato dalle date: con queste date il bando risulta **chiuso** e non verrà mai proposto ai clienti, anche se con ogni probabilità è aperto o in arrivo. Andavano lasciate `null` con l'avvertenza. Il prompt non ha una regola per questo caso: errore in parte indotto. L'ora (11:00) è giusta. |
| scadenza / ora_scadenza | 2025-11-30 / 21:00 | **SBAGLIATO (pericolo alto)** (stesso errore) | r. 362-363. L'ora 21:00 è giusta ed è bene averla. |
| chiuso_il | null | ok | Nessuna chiusura anticipata nei documenti; la Camera si riserva solo di chiudere se finiscono i fondi (r. 196). |
| modalita_selezione | sportello_valutativo | IMPRECISO (basso) | Il bando dice "procedura valutativa a sportello ... secondo l'ordine cronologico" (r. 420-422), ma **non c'è nessun punteggio minimo**, che per noi è la differenza tra `sportello` e `sportello_valutativo` (r. 25). Per le nostre regole è `sportello`. Il bando poi parla anche di "graduatoria delle domande ammesse" (r. 328-329): contraddizione interna che andava in avvertenza. |
| sintesi | 5 righe | IMPRECISO (basso) | Numeri giusti (10.000 €, 70%, 500.000 €, 250 € di premio, una domanda). Ma usa "art. 86 TULPS" senza spiegarlo (regola 12): va detto che sono i **pubblici esercizi con licenza di pubblica sicurezza** (alberghi, bar, ristoranti, locali di intrattenimento). Per un commercialista "settore turismo" è fuorviante: anche un bar in città rientra. |
| a_chi_si_rivolge | MPMI del turismo, art. 86 TULPS, sede/unità locale nella circoscrizione | ok | r. 201-217. Stessa sigla non spiegata. |
| soggetti_ammessi | ["impresa"] | ok | r. 201. |
| forme_giuridiche ammesse / escluse | [] / [] | ok | La nota 2 (r. 253) che nomina "le imprese individuali" si riferisce alla regola sulle forniture alla Camera (lett. j), **non** esclude le ditte individuali dal bando. Sonnet non è caduto nella trappola. |
| dimensioni_ammesse | micro, piccola, media | ok | r. 211 e r. 264. |
| eta_impresa_min / max | null / null | ok | Non c'è un limite di età dell'impresa. Il vincolo "unità locale attiva dal 31/12/2024" (r. 216) vale solo per chi partecipa con un'unità locale. |
| requisiti_speciali_obbligatori | ["turistica"] | ok (con riserva) | r. 201-202. Il valore più vicino disponibile. Rischio: se nei profili "turistica" è segnato solo per alberghi e agenzie, un bar o un ristorante (art. 86 TULPS) verrebbe scartato. |
| requisiti_speciali_premiali | rating_legalita, certificazione_parita_genere | ok | r. 177-187. |
| dipendenti / fatturato | null | ok | Non se ne parla. |
| codici_ateco / esclusi | [] / [] | ok | Il bando non usa codici ATECO ma rinvia all'art. 86 TULPS (r. 202); non elenca i settori esclusi dal de minimis. Avvertenza 6 lo dice bene. |
| ateco_versione | null | ok | |
| regime_aiuto | ["de_minimis"] | ok | art. 8, r. 338-341. |
| requisiti | elenco lett. a-k, una domanda, fornitori, PEC | ok (MANCANTE lieve) | Completo su DURC, polizza catastrofale (r. 246-247), antimafia, diritto annuale, fornitori (r. 266-273), una sola domanda (r. 261). Manca l'obbligo di **realizzare almeno il 70% delle spese ammesse**, pena la decadenza (art. 12.1.c, r. 440-441), e che i requisiti vanno mantenuti fino alla liquidazione (r. 248-250). |
| cosa_finanzia | 4 famiglie di beni + consulenza + formazione | ok | art. 2 e art. 7, r. 275-319. |
| tipo / tipi_agevolazione | voucher / [voucher] | ok | "contributi a fondo perduto (voucher)" (r. 157), r. 174. |
| tema / temi | sicurezza / sicurezza, turismo, digitale | ok | |
| categorie_spesa | macchinari, software, consulenze, formazione | MANCANTE (basso) | Gli impianti antincendio e di evacuazione fumo e calore (r. 281-284) sono impianti: manca `opere_edili_impianti`. |
| spese_ammesse | dalla pubblicazione a 120 giorni dopo la determina; rendiconto entro 30 giorni; esclusioni | ok | r. 320-330, r. 483-484. Regola 20 rispettata. |
| contributo_massimo / percentuale | 10000 / 70 | ok | r. 175-176. |
| fondo_perduto_massimo / percentuale_fondo_perduto / finanziamento_massimo | null / null / null | ok | Non è un'agevolazione mista (regola 18). |
| spesa_minima / spesa_massima | null / null | ok | Il bando non le fissa. |
| dotazione | 500000 | ok | r. 172-173. |
| linee | [] | ok | Una sola linea. |
| vincoli.territorio | vincolo | ok | |
| vincoli.soggetti | vincolo | ok | |
| vincoli.forme_giuridiche | non_noto | ok | Il bando non ne parla. |
| vincoli.dimensioni | vincolo | ok | |
| vincoli.ateco | vincolo | IMPRECISO (medio) | Il bando limita il settore, ma **non con codici ATECO**. Con "vincolo" ed elenchi vuoti, il motore (SCHEDA_BANDO.md r. 119: controlla i codici solo se l'elenco è pieno) lascia passare **qualunque** settore: un'impresa manifatturiera risulterebbe compatibile per l'ATECO. L'unico freno resta "turistica". Più prudente `non_noto` (→ "da verificare"). Il prompt non dice cosa fare in questo caso. |
| vincoli.eta_impresa | non_noto | ok | Accettabile (vedi sopra). |
| vincoli.requisiti_speciali | vincolo | ok | |
| vincoli.dipendenti | non_noto | ok | |
| vincoli.fatturato | non_noto | ok | |
| vincoli.spesa | vincolo | **SBAGLIATO (medio)** | Il bando non ha né minimo né massimo di spesa; lo dice la stessa avvertenza 4 di Sonnet. Andava `non_noto`. Contraddizione dentro la scheda. |
| vincoli.regime_aiuto | vincolo | ok | |
| completezza | bando_ufficiale | ok | |
| fonti | 27 voci, per articolo | IMPRECISO (basso) | Precise e verificabili. Mancano però le fonti di `territorio_regioni`, `territorio_province`, `ora_apertura`, `ora_scadenza` (regola 3: "un campo senza fonte deve valere null"). Le province vengono dall'annuncio ma la scheda cita "art. 4". Sonnet ha usato il formato a elenco `{campo, fonte}` dello schema (r. 1512), non quello a dizionario delle istruzioni (r. 100): il prompt si contraddice. |
| avvertenze 1 (date) | date 2025 incoerenti con "Anno 2026" | ok, molto utile | Giusta e onesta; poteva citare la prova più forte (D.lgs. 184 del 27/11/2025 a r. 421). Ma non basta: i campi data restano sbagliati. |
| avvertenze 2 (orari) | 11:00 / 21:00 | ok | Regola 21 rispettata. |
| avvertenze 3 (spese dalla pubblicazione, preventivi) | | ok | r. 327, r. 395-396. |
| avvertenze 4 (spesa) | "il massimale fissa indirettamente un tetto di spesa" | IMPRECISO (basso) | Deduzione che il bando non scrive (regola 21). |
| avvertenze 5 (de minimis) | "non indica un massimale in euro specifico" | IMPRECISO (basso) | Non è un dubbio reale: il de minimis funziona sempre così. Da togliere. |
| avvertenze 6 (ATECO) | nessun codice, rinvio all'art. 86 TULPS | ok | Utile. |
| avvertenze mancanti | | MANCANTE (basso) | Ritenuta d'acconto del 4% sul voucher (r. 191-193); obbligo di spendere almeno il 70% (r. 440); contraddizione "sportello" / "graduatoria" (r. 328 e r. 420). |

**Pericolosità:** un errore grave. Le date del 2025 fanno risultare il bando **chiuso**, quindi non verrebbe mai proposto ai clienti. In più, "ateco = vincolo" con elenchi vuoti lascia passare qualunque settore, e "spesa = vincolo" senza importi è incoerente.

**Regole nuove del prompt (15-22):**
- 15 (ente e gestore): rispettata.
- 16 (esclusioni di settore): nessuna esclusione da riportare; rispettata. Il caso del settore definito per legge (art. 86 TULPS) non è previsto dalla regola.
- 17 (requisiti separati dal punteggio): rispettata. I premi sono in sintesi e tra i premiali; DURC, polizza catastrofale, una domanda per impresa e vincoli sui fornitori sono tutti riportati. Manca solo l'obbligo del 70% minimo di spesa realizzata.
- 18 (agevolazioni miste): non applicabile; campi del prestito giustamente vuoti.
- 19 (premi): rispettata (250 € in sintesi, `contributo_massimo` 10.000 base).
- 20 (tempi delle spese): rispettata in modo esemplare (da quando, fino a quando, rendiconto a 30 giorni).
- 21 (avvertenze senza supposizioni): quasi rispettata; le avvertenze 4 e 5 sono superflue o deduttive. Ha segnalato gli orari diversi da fine giornata e il vincolo dei preventivi.
- 22 (cataloghi): non applicabile.

**Controllo preliminare di Haiku:** risposta `per_imprese=si`, `edizione_in_corso=si`, `stato=non_noto`, `testo_bando=si`; motivo: "data di scadenza non indicata nei documenti forniti". **Decisione giusta** (chiamare Sonnet). I valori sono giusti rispetto a quello che Haiku vedeva: il suo estratto si ferma esattamente a "ARTICOLO 10 – PRESENTAZIONE DELLE DOMANDE / 1. A pena di esc" (preliminare_416.txt r. 256-257), cioè **una riga prima delle date**. Rispetto al documento completo `stato=non_noto` resta la risposta corretta, perché le date scritte sono un refuso. Ma è andata bene per caso: se Haiku avesse letto le date del 2025, avrebbe probabilmente risposto `chiuso` e il bando sarebbe stato scartato senza chiamare Sonnet.

**Voto: 3/5.** Il testo per il commercialista è da 4: completo, fedele, niente invenzioni, tempi delle spese esemplari, avvertenza sulle date onesta. Ma nell'uso automatico la scheda fa sparire il bando (risulta chiuso) e ha due stati dei vincoli incoerenti. La colpa è in buona parte del bando e del prompt, che non dice cosa fare con date palesemente sbagliate.

**Errori per tipo:** INVENTATO 0 · SBAGLIATO 2 (date di apertura e scadenza del 2025; vincoli.spesa) · MANCANTE 3 (obbligo di realizzare il 70% della spesa; categoria impianti; avvertenze su ritenuta 4% e "sportello/graduatoria") · IMPRECISO 5 (vincoli.ateco; modalità di selezione; sigla TULPS non spiegata; fonti incomplete; avvertenze 4-5 superflue).

**Problemi generali emersi:**
1. **Date palesemente sbagliate nel bando**: il prompt dovrebbe dire "se le date contraddicono l'anno del bando o le norme citate, lascia le date `null` e spiega in avvertenza". Anche il sistema dovrebbe mettere lo stato "da verificare" (non "chiuso") quando l'avvertenza segnala date incoerenti.
2. **Raccolta dalle notizie**: quando il link della notizia porta direttamente al PDF, il testo della notizia va comunque passato come documento (spesso contiene le date vere). Vanno cercati anche la delibera di approvazione e la modulistica.
3. **Settore definito per legge e non per ATECO** (art. 86 TULPS, "esercizi pubblici", "imprese artigiane"): la scheda non ha modo di esprimerlo. Con `vincoli.ateco = vincolo` ed elenchi vuoti il motore lascia passare tutti. Serve una regola: in questi casi `ateco = non_noto` (da verificare), più il requisito speciale.
4. **Significato di `vincoli.spesa`** da chiarire nel prompt: "vincolo" solo se c'è una spesa minima o massima di progetto, non per la percentuale del contributo.
5. **`sportello_valutativo`**: le Camere di Commercio scrivono "procedura valutativa a sportello" (D.lgs. 184/2025, art. 13) anche senza punteggio. Il prompt deve dire che conta il punteggio minimo, non le parole del bando.
6. **Prompt contraddittorio sulle `fonti`**: dizionario nelle istruzioni (r. 100), elenco nello schema (r. 1512). Va allineato.
7. **Estratto di Haiku a lunghezza fissa**: può tagliare subito prima delle date (qui per un soffio). Conviene aggiungere all'estratto le righe che contengono date e orari ("dalle ore", "entro il", nomi dei mesi).
8. Gli indirizzi con spazi vanno codificati prima di mostrarli al cliente.

---

## 346 — Bando Voucher di Accelerazione (Regione Lombardia, moda e design)

*Ogni campo è stato confrontato con il testo del prompt `scheda_346.txt` (l'unica fonte che Sonnet aveva). I numeri tra parentesi sono le righe di quel file. Nessun sito consultato.*

**In breve:** bando piccolo (270.000 €) per PMI lombarde della moda e del design, che paga l'80% (90% per le imprese giovanili) di un percorso presso un acceleratore dell'elenco regionale, su una spesa massima di 40.000 €. Lo sportello è stato **chiuso il 09/07/2026 per fondi esauriti**. La scheda è scritta bene e non inventa nulla. Il difetto serio è un altro: **il bando è riservato alla moda e al design, ma nessun campo usato per l'abbinamento lo dice**. Resta scritto solo nel testo. In più `vincoli.ateco` vale "nessun vincolo". Il preliminare di Haiku aveva giusto a fermarsi (bando chiuso), anche se uno dei suoi valori è sbagliato.

### Materiale in ingresso

Buono e completo, **nessun taglio** (righe 117-118: "nessuna" nota). Quattro documenti, in quest'ordine:

1. **Pagina del bando** (122-220): etichetta "Chiuso", "Scade il 09/07/2026 ore 13:00" (134-136). Dopo la chiusura la pagina ha sostituito la data prevista dal bando con quella di chiusura. C'è anche la scheda informativa.
2. **Decreto n. 9232 del 09/07/2026, chiusura dello sportello** (222-309): è il documento più recente ed è giusto che stia in cima.
3. **Decreto n. 5856 del 06/05/2026 con il bando completo (Allegato A)** (311-2020): articoli da A.1 a D.10 (492-1284), poi i moduli dall'Allegato A all'Allegato L (1287-2020). Ci sono l'Allegato B, con l'elenco dei settori esclusi dal de minimis (1484-1504), e l'Allegato H, la scheda progetto con la frase "Indipendentemente dal codice Ateco" (1775).
4. **D.G.R. 5943 del 30/03/2026** (2022-2302): la delibera senza il suo Allegato A dei criteri. Non manca nulla, perché il bando completo è già al punto 3.

**Cosa manca o è di troppo:**
- La pagina elenca gli allegati e poi scrive "Mostra altri" (214). Allegati nascosti dietro quel pulsante (rettifiche, FAQ, elenchi) non sarebbero stati scaricati: da verificare nella raccolta.
- Non è stato seguito il link all'"Elenco Regionale degli incubatori e degli acceleratori" (216). Per il cliente è l'informazione pratica più utile: da chi posso fare il percorso?
- Circa 460 righe di moduli vuoti (Allegati C-L, 1556-2020) e la D.G.R., che ripete il bando, occupano spazio senza aggiungere informazioni. Qui non ha fatto danni perché il testo non è stato tagliato.

### Campo per campo

| Campo | Valore di Sonnet | Esito | Nota (righe di scheda_346.txt) |
|---|---|---|---|
| titolo | Bando Voucher di Accelerazione | ok | 125, 440 |
| ente | Regione Lombardia | ok | Finanzia la Regione (A.4, 576) |
| gestore | null | ok | Lo gestisce direttamente la Regione, tramite la D.G. Turismo, Marketing territoriale e Moda (D.6, 1210). Non c'è un gestore esterno |
| url | pagina di dettaglio RLP12026053343 | ok | 114 |
| territorio | Lombardia | ok | A.3, 548-549 |
| territorio_regioni | ["LOM"] | ok | |
| territorio_province / comuni | [] / [] | ok | Nessun limite sotto la regione |
| sede_richiesta | operativa | ok | "Sede operativa, presso cui svolgere le attività del progetto, in Lombardia" (548). La decadenza scatta se manca la sede operativa al momento dell'erogazione (D.2, 1142) |
| data_apertura / ora_apertura | 2026-06-15 / 10:00 | ok | C.1, 761 |
| scadenza / ora_scadenza | 2027-02-28 / 12:00 | ok | C.1, 761; confermato dal decreto di chiusura (261-262). La pagina dice "09/07/2026 ore 13:00" (135): è la data di chiusura, non la scadenza del bando. Scelta giusta (regola 2) |
| chiuso_il | 2026-07-09 | ok | Decreto 9232, punto 1 (223, 298) |
| modalita_selezione | sportello_valutativo | ok | "valutativo a sportello" (C.2, 891). La valutazione è un SÌ/NO su due criteri, senza punti (952-953), ma il valore resta il più vicino |
| sintesi | 80% / 90%, 40.000 €, 270.000 €, sportello, chiuso il 9/7 | ok | Corretta e chiara. Non indica il contributo massimo per le imprese giovanili (36.000 €) |
| a_chi_si_rivolge | PMI con sede operativa in Lombardia, iscritte e attive, dei settori moda e/o design | ok | A.3 (544-549), Allegato H (1775-1776) |
| soggetti_ammessi | ["impresa"] | ok | |
| forme_giuridiche ammesse / escluse | [] / [] | ok | Il bando non ne parla |
| dimensioni_ammesse | micro, piccola, media | ok | A.3 (544), modulo di domanda (1296-1299) |
| eta_impresa min/max | null / null | ok | Basta essere "regolarmente costituite, iscritte e attive" (546) |
| requisiti_speciali_obbligatori | [] | **MANCANTE, pericolo alto** | Il bando è solo per chi opera nella moda e nel design. Lo dicono la finalità (A.1, 497-499), i progetti ammessi (B.2, 674-676) e la scheda progetto, che è obbligatoria (C.1 punto 3, 797-803): "Indipendentemente dal codice Ateco, descrivere e motivare la riconducibilità dell'attività del soggetto ai settori della moda e del design" (1775-1776). Nessun campo strutturato lo riporta. Andava `["altro"]` con `vincoli.requisiti_speciali = "vincolo"`, oppure un'avvertenza dedicata. Con la scheda così, il motore proporrebbe il bando a qualunque PMI lombarda (un ristorante, una software house) |
| requisiti_speciali_premiali | ["giovanile"] | ok | +10% alle imprese giovanili (B.1, 588-594) |
| dipendenti / fatturato | null | ok | Il bando richiede solo di essere PMI |
| codici_ateco | [] | ok | Il bando non elenca codici ammessi ("indipendentemente dal codice Ateco", 1775) |
| codici_ateco_esclusi | [] | **MANCANTE, pericolo medio** | Il bando esclude "i settori esclusi di cui all'art. 1 par. 1 e 2 del Reg. UE 2831/2023" (567, 602, 1337) e l'Allegato B, che fa parte del decreto, li elenca (1484-1504): pesca e acquacoltura (produzione primaria) e produzione agricola primaria. È esattamente il caso della regola 16 ("quando il bando li elenca"). Andavano almeno `"01"` e `"03"`, che hanno lo stesso codice in ATECO 2007 e 2025. Sonnet li descrive nei `requisiti` e in avvertenza ma non nell'elenco, che è l'unica cosa che legge il motore |
| ateco_versione | null | ok | Il bando non dichiara una versione |
| vincoli.ateco | nessun_vincolo | **SBAGLIATO, pericolo alto** | Il settore è limitato due volte: moda e design, più le esclusioni del de minimis. "Indipendentemente dal codice Ateco" vuol dire che il codice da solo non decide, non che tutti i settori sono ammessi. Con "nessun_vincolo" il motore dà "ATECO compatibile" a chiunque. Giusto: "vincolo" con gli esclusi `01`, `03` (e il vincolo moda-design nei requisiti speciali). In alternativa "non_noto", così il risultato diventa "da verificare" |
| regime_aiuto | ["de_minimis"] | ok | B.1 (595-600) |
| requisiti | PMI, registro, sede operativa, polizza catastrofale, DURC, sanzioni 231, condanne, procedure concorsuali, settori esclusi dal de minimis, più domande solo dopo la conclusione dell'istruttoria | ok, **MANCANTE lieve** | Tutto vero (A.3 553-572, B.2 687-690). Mancano: il divieto di spese fatturate da società collegate, con soci o amministratori in comune o da parenti (746-751), cioè un vincolo sui fornitori (regola 17), e la dichiarazione di regolarità su salute e sicurezza del lavoro (1358-1359). Pericolo basso |
| cosa_finanzia | percorso di accelerazione presso un incubatore o acceleratore dell'elenco regionale, in una sede lombarda | ok | B.2-B.3 (674-704) |
| tipo_agevolazione / tipi_agevolazione | fondo_perduto / ["fondo_perduto"] | ok (fonte parziale) | "sovvenzione a fondo perduto" (584). Manca la fonte di `tipi_agevolazione` (regola 3) |
| tema / temi | formazione / ["formazione"] | IMPRECISO, pericolo basso | Un percorso di accelerazione d'impresa non è formazione in senso stretto. I temi dichiarati dal bando sono competitività, filiera e sostenibilità (A.1, 498-504): `investimenti`, `altro` o anche `green` sarebbero più fedeli. Manca la fonte |
| categorie_spesa | consulenze, formazione | ok (senza fonte) | Accettabile per un percorso di servizi. Manca la fonte |
| contributo_massimo | 32000 | IMPRECISO, pericolo basso | Il bando non scrive un contributo massimo: 32.000 è il calcolo 80% × 40.000. È un calcolo corretto e non un'invenzione, ma l'avvertenza avrebbe dovuto dirlo e la sintesi dare anche i 36.000 € (90%) per le imprese giovanili |
| percentuale | 80 | **SBAGLIATO, pericolo medio** | SCHEDA_BANDO.md: "Percentuale massima delle spese coperta, **comprese le maggiorazioni**". Doveva essere 90 (B.1, 588-589; scheda informativa "fino al 90%", 1234-1235). Nel catalogo il bando sembra meno generoso del vero |
| fondo_perduto_massimo / percentuale_fondo_perduto | null / null | ok | Non è un'agevolazione mista (regola 18). L'esempio di SCHEDA_BANDO.md li compila anche per un fondo perduto puro: la specifica è incoerente |
| finanziamento_massimo | null | ok | |
| spesa_minima | null | ok | Il bando non fissa una spesa minima di progetto. Esiste solo il limite di 2.000 € per singola fattura (752-753), riportato in `spese_ammesse` |
| spesa_massima | 40000 | ok | B.3 (705-706) |
| dotazione | 270000 | ok | A.4 (576) |
| spese_ammesse | dal giorno dopo la domanda; percorso e rendiconto entro 14 mesi e non oltre il 31/12/2027; rendiconto dal 07/01/2027; niente fatture sotto 2.000 €, contanti o compensazioni | ok, **MANCANTE lieve** | Tempi corretti (712-716, 682-683, 1005-1006, 1083). Mancano le spese escluse (personale, consulenze continuative, notai e tasse, 734-745) e la **decadenza se si rendiconta meno del 60%** delle spese ammesse (D.2, 1149-1150), utile al commercialista. Pericolo basso |
| linee | [] | ok | Una sola linea |
| vincoli.territorio | vincolo | ok | |
| vincoli.soggetti | vincolo | ok | |
| vincoli.forme_giuridiche | non_noto | ok | Il bando non ne parla (regola 4) |
| vincoli.dimensioni | vincolo | ok | Solo PMI |
| vincoli.ateco | nessun_vincolo | **SBAGLIATO** | Vedi sopra |
| vincoli.eta_impresa | non_noto | ok | |
| vincoli.requisiti_speciali | nessun_vincolo | **SBAGLIATO** (stesso errore del settore moda-design) | Il requisito di settore moda e design c'è. E anche senza quello, la regola 4 vuole "nessun_vincolo" solo se il bando lo dice espressamente |
| vincoli.dipendenti | non_noto | ok | |
| vincoli.fatturato | non_noto | ok | |
| vincoli.spesa | vincolo | ok | Massimo 40.000 € |
| vincoli.regime_aiuto | vincolo | ok | |
| completezza | bando_ufficiale | ok | Il bando completo c'è. Citare come fonte "pagina" è improprio: vale il decreto 5856 |
| fonti | 26 voci, quasi tutte con articolo | IMPRECISO, pericolo basso | Le citazioni per articolo sono precise e verificabili. Mancano le fonti di `territorio_regioni`, `tipi_agevolazione`, `tema`/`temi`, `categorie_spesa` e `requisiti_speciali_premiali`→`vincoli`. La regola 3 dice che un campo senza fonte deve valere null |
| avvertenze | 5 | ok, IMPRECISO lieve | La n. 1 (chiusura, 9 domande per 284.400 €, 269-271) e la n. 2 (ATECO) sono utili e vere. La n. 3 (80% e 90%) e la n. 4 (fatture sotto 2.000 €) ripetono sintesi e spese: la regola 21 lo vieta. La n. 5 ("la Regione si riserva di integrare la dotazione", 578) è vera ma, a sportello chiuso, può far sperare in una riapertura che nessun documento annuncia |

### Regole nuove del prompt (15-22)

- **15, ente e gestore:** rispettata. Ente = Regione, gestore null: corretto, perché non c'è un soggetto gestore esterno.
- **16, esclusioni di settore nell'elenco:** **non rispettata**. I settori esclusi dal de minimis sono elencati nell'Allegato B (1484-1504) e Sonnet li ha scritti nei `requisiti` e in avvertenza, ma `codici_ateco_esclusi` è vuoto e `vincoli.ateco` vale "nessun_vincolo". È l'errore che la regola doveva evitare. A sua parziale difesa: il bando rimanda al regolamento e l'elenco sta in un modulo informativo, non negli articoli.
- **17, requisiti separati dal punteggio:** rispettata. I requisiti contengono solo condizioni di ammissione; la maggiorazione giovanile è tra i premiali. Riportati regime, DURC, polizza catastrofale e numero di domande. Il vincolo sui fornitori (società collegate) manca.
- **18, agevolazioni miste:** non si applica (solo fondo perduto). Campi del prestito lasciati vuoti: giusto.
- **19, premi:** applicata alla lettera: contributo base al 32.000, maggiorazione nella sintesi. Però `percentuale` è rimasta all'80 invece di 90, contro la specifica.
- **20, tempi delle spese:** **rispettata bene**. Ammissibili dal giorno dopo la domanda, termine di 14 mesi e 31/12/2027, rendiconto dal 07/01/2027.
- **21, avvertenze senza supposizioni:** in parte. Niente deduzioni inventate, ma due avvertenze ripetono la sintesi e una (integrazione della dotazione) rischia di illudere.
- **22, pagine di catalogo:** non si applica.
- **Regola 2 (il bando vince sulla pagina):** applicata. La scadenza è quella del bando (28/02/2027), non il "09/07/2026" della pagina. La differenza non è spiegata in un'avvertenza, ma la n. 1 la chiarisce nella sostanza.

### Controllo preliminare di Haiku

Risposta: `per_imprese = si`, `edizione_in_corso = no`, `stato = chiuso`, `testo_bando = si`, motivo "Sportello chiuso il 09/07/2026; scadenza della precedente edizione: 09/07/2026".

- **Decisione (non chiamare Sonnet): giusta.** Lo sportello è stato chiuso per intero con il decreto 9232 ("Di chiudere lo sportello di adesione al bando", 298-299) perché "non residuano risorse" (280-282). Il bando ha una sola linea e un solo sportello, quindi la chiusura riguarda tutto. Nei documenti non c'è una nuova edizione né una nuova finestra. La coda del 10% oltre la dotazione (C.1, 766-770) non riapre le domande: il decreto chiude lo sportello anche per quelle. La frase "si riserva di integrare la dotazione" (578, 2234) è solo una possibilità: se la Regione riaprisse, la pagina cambierebbe e l'osservatore la vedrebbe.
- `per_imprese = si`: giusto (PMI, riga 164 del preliminare e della scheda).
- `testo_bando = si`: giusto. Haiku vedeva l'inizio del decreto 5856, che approva il bando: bastava.
- `stato = chiuso`: giusto, sia rispetto a quello che vedeva (pagina "Chiuso", decreto di chiusura) sia rispetto ai documenti completi.
- `edizione_in_corso = no`: **sbagliato**. È l'edizione 2026, l'unica pubblicata del "Voucher di accelerazione". Il programma precedente, del 2023, aveva un altro nome (2098-2099) e Haiku non poteva nemmeno vederlo. Non è una pagina d'archivio: è l'edizione attuale, chiusa. Il motivo parla di una "precedente edizione" che non esiste nel testo, quindi è un'invenzione lieve di Haiku. Qui non ha conseguenze perché `stato = chiuso` bastava da solo a fermare Sonnet. Il rischio è generale: Haiku confonde "chiuso" con "edizione passata". Se in futuro questi due valori verranno trattati in modo diverso (per esempio tenendo d'occhio i bandi chiusi dell'edizione in corso per possibili riaperture), l'errore conterà.

### Voto e conteggio

**Voto: 4/5.** Testo accurato, nessuna invenzione, date, importi e tempi delle spese esatti, chiusura anticipata registrata bene. Non vale 5 perché, per l'abbinamento, il bando risulta aperto a tutti i settori: il vincolo moda e design e le esclusioni del de minimis restano solo nel testo, e la percentuale non comprende la maggiorazione. Essendo chiuso, oggi il bando non verrebbe comunque proposto a nessun cliente. Correttamente, in produzione Sonnet non sarebbe stato chiamato.

**Errori: INVENTATO 0 · SBAGLIATO 2 · MANCANTE 4 · IMPRECISO 4.**
- SBAGLIATO: `vincoli.ateco` = nessun_vincolo (alto); `percentuale` 80 invece di 90 (medio).
- MANCANTE: vincolo di settore moda e design nei campi strutturati, `requisiti_speciali_obbligatori` e `vincoli.requisiti_speciali` (alto); `codici_ateco_esclusi` senza 01 e 03 del de minimis (medio); vincolo sui fornitori collegati nei requisiti (basso); spese escluse e decadenza sotto il 60% (basso).
- IMPRECISO: `contributo_massimo` calcolato senza dirlo e senza i 36.000 € giovanili (basso); `tema` formazione (basso); fonti mancanti per alcuni campi (basso); avvertenze che ripetono la sintesi (basso).

### Problemi che sembrano generali

1. **Settori definiti a parole e non con codici ATECO** ("imprese della moda e del design", "indipendentemente dal codice Ateco"): la scheda non ha un campo per dirlo. Oggi finisce in `a_chi_si_rivolge`, che il motore non legge. Servono una regola nel prompt ("se il bando è riservato a un settore descritto a parole, `vincoli.ateco` = `non_noto` e il settore va in `requisiti_speciali_obbligatori: [\"altro\"]` con avvertenza") oppure un campo `settore_descritto`.
2. **"nessun_vincolo" usato per "non c'è un elenco"**: la regola 4 chiede che il bando lo dica espressamente, ma Sonnet lo usa quando l'elenco manca. In più l'esempio di SCHEDA_BANDO.md mette `nessun_vincolo` su forme giuridiche, età, dipendenti e fatturato "perché il bando non ne parla", contro la regola 4. Va reso coerente, altrimenti il modello riceve due istruzioni opposte.
3. **`percentuale` con o senza maggiorazioni**: la specifica dice "comprese", la regola 19 del prompt parla di "contributo base". Il prompt va allineato: "`percentuale` = la più alta, comprese le maggiorazioni; `contributo_massimo` = base, e se il bando non lo scrive calcolalo e dillo".
4. **Esclusioni del de minimis**: quando il bando rimanda all'art. 1 del Reg. 2831/2023, il prompt potrebbe indicare direttamente i codici minimi (`01`, `03`), così non tocca al modello decidere.
5. **Raccolta**: il pulsante "Mostra altri" sulle pagine di Regione Lombardia può nascondere allegati; il link all'elenco dei fornitori ammessi (qui gli acceleratori) non viene seguito; i moduli vuoti dentro il PDF del decreto occupano spazio.
6. **Prompt contro schema**: il prompt descrive `fonti` come un oggetto `{campo: fonte}`, lo schema JSON finale (3229-3249) come un elenco di coppie. Sonnet ha seguito lo schema. Va corretto il testo del prompt.
7. **Haiku, `edizione_in_corso`**: confonde "chiuso" con "edizione passata" e inventa una "precedente edizione". La domanda andrebbe chiarita: "`no` solo se esiste o è citata un'edizione più recente dello stesso bando".
