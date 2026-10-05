# Fattura elettronica per gli abbonamenti (Stripe → SdI)

**Data:** 05/10/2026

**Domanda.** Bandi Radar incassa con Stripe (abbonamento mensile 30 €, annuale 20 €/mese addebitato ogni mese, impresa in più 10 €, sede in più 5 €, più le success fee del supporto alle domande). Stripe non invia nulla al Sistema di Interscambio (SdI). Come si emette la fattura elettronica per ogni addebito? Conviene costruirlo in casa o comprare un servizio? Quale, a che costo, con quale flusso? E quali sono i nodi fiscali (chi emette, quando)?

**Metodo.** Ricerca web e lettura diretta delle pagine ufficiali di prezzi e documentazione dei fornitori, del portale fatturapa.gov.it, delle FAQ dell'Agenzia delle Entrate e della documentazione Stripe. Lettura del codice attuale degli abbonamenti (`app/abbonamenti/`) per adattare il flusso a quello che c'è già.

**Limiti.**
- Prezzi letti il 05/10/2026 sulle pagine pubbliche: possono cambiare, e alcuni fornitori (A-Cube oltre 200 documenti/mese, Aruba Premium) non pubblicano il listino per le API: indicato come "su preventivo" o "non verificato".
- Per Openapi due pagine ufficiali danno prezzi diversi per lo stesso invio (0,049 € e 0,070 € base): riportati entrambi.
- Nessun account di prova è stato aperto: funzioni come "gestisce il codice destinatario raccolto in un campo personalizzato di Stripe" non sono state provate.
- Le parti fiscali (momento di effettuazione, incompatibilità del commercialista, IVA sui servizi digitali a consumatori UE) sono riportate come quadro generale, non come parere: Matteo è il professionista e decide lui. Dove la fonte non è stata vista sul web lo dico.

---

## 1. Costruirlo in casa: fattibile?

Sì, tecnicamente è fattibile, ma conviene solo a metà: **generare l'XML in casa sì, parlare direttamente con lo SdI no.**

### Cosa serve davvero

| Pezzo | Cosa comporta | Difficoltà |
|---|---|---|
| XML FatturaPA (formato FPR12, privati) | Un file per fattura con cedente, cessionario, righe, riepilogo IVA, natura per le operazioni senza IVA, dati di pagamento. Le specifiche cambiano ogni tanto (l'Agenzia pubblica nuove versioni delle specifiche tecniche) | Media: 2-3 giorni con test, poi manutenzione |
| Canale verso lo SdI | Quattro canali (fatturapa.gov.it, pagina "Inviare la FatturaPA"): **PEC** (nessun accreditamento, file fino a 30 MB, primo invio a sdi01@pec.fatturapa.it, poi lo SdI assegna un suo indirizzo PEC); **procedura web** (manuale, con SPID/Entratel); **SDICoop** (servizio web SOAP con MTOM, TLS 1.2, accreditamento preventivo con due certificati client/server e prove di interoperabilità); **SDIFTP** (per grandi volumi, accreditamento e infrastruttura dedicata) | PEC: media, ma fragile. SDICoop: alta (settimane di accreditamento e prove) |
| Firma digitale | Per le fatture tra privati **non è obbligatoria**: "SdI accetta fattura elettronica anche non firmata digitalmente" (FAQ Agenzia). Serve solo verso la Pubblica Amministrazione | Nessuna per noi |
| Ricevute e notifiche | Ricevuta di consegna (RC), notifica di scarto (NS), mancata consegna (MC). Vanno lette, legate alla fattura, mostrate a Matteo. Lo scarto va corretto e ritrasmesso | Media: con la PEC significa leggere una casella di posta e interpretare allegati XML |
| Numerazione progressiva | Numero unico e crescente per anno (si può usare un sezionale, es. `BR/2026/0001`), senza buchi, sicuro anche se due pagamenti arrivano insieme | Bassa, ma critica |
| Note di credito | Documento TD04 collegato alla fattura originaria, per rimborsi e storni | Bassa |
| Bollo virtuale | 2 € sulle fatture **senza IVA** sopra 77,47 € (operazioni esenti, regime forfettario, alcune non imponibili), indicato nell'XML e versato con F24 trimestrale. Con IVA al 22% non si paga | Bassa (raramente ci riguarda) |
| Conservazione a norma 10 anni | **Gratis con l'Agenzia delle Entrate**: servizio facoltativo per i soggetti IVA, conserva le fatture passate dallo SdI per 15 anni, va attivato con un'adesione nel portale Fatture e Corrispettivi (anche tramite intermediario delegato) | Nessuna se si aderisce |

### Stima onesta

- **Via PEC** (senza accreditamento): 2-3 settimane di lavoro tra XML, invio PEC, lettura delle notifiche dalla casella, gestione scarti, pagina di controllo, test. Rischi: PEC che si blocca o cambia password, notifiche perse, nessun "ambiente di prova" dello SdI per la PEC (si prova in produzione con fatture vere).
- **Via SDICoop**: 4-8 settimane tra accreditamento, certificati, prove, SOAP. Va mantenuto (certificati in scadenza, cambi di specifiche).
- **Risparmio ottenuto**: 5-30 €/mese rispetto ai servizi più economici (vedi sotto). Un errore fiscale (fatture non emesse, numerazione sbagliata) costa più di anni di canone.

**Giudizio: costruire tutto in casa → no.** Costruire in casa solo l'XML e affidare l'invio a un intermediario con API → sì (è la raccomandazione, §6).

---

## 2. Servizi di terzi con API

Volumi di riferimento: **50 clienti ≈ 55-60 documenti/mese** (abbonamenti + qualche nota di credito e success fee); **500 clienti ≈ 520-550 documenti/mese, ~6.500/anno**.

| Servizio | Costo (IVA esclusa, letto il 05/10/2026) | API e documentazione | Conservazione | Invio automatico allo SdI | Note di credito | Giudizio |
|---|---|---|---|---|---|---|
| **Invoicetronic** | Pacchetti prepagati senza scadenza: 1.000 transazioni 100 € (0,10 €), 5.000 a 275 € (0,055), 20.000 a 800 € (0,04). Una transazione = invio, ricezione o validazione; stati, webhook e registro eventi gratis; sandbox gratis. Firma opzionale 0,02 € | REST, SDK ufficiali anche per **Python**, webhook sugli stati e sulle fatture in arrivo, validazione preventiva, dati trattati solo in UE | **Non inclusa**: la loro documentazione rimanda al servizio gratuito dell'Agenzia | Sì | Sì (si invia un XML TD04 come qualunque altro documento) | **sì** — il più adatto |
| **Openapi (SDI)** | Pagina prodotto: invio 0,049 €, con firma 0,09, con conservazione 0,105, firma+conservazione 0,125; abbonamenti annui fino a 0,0135 €. Console prezzi: creazione fattura 0,070 € base, 0,022 € con abbonamento; conservazione 0,105 € | REST, webhook, sandbox, consultazioni gratuite entro quote giornaliere | A pagamento per fattura (o Agenzia gratis) | Sì | Sì | **sì** — alternativa valida, listino meno limpido |
| **A-Cube — app Stripe** (nel marketplace Stripe) | Fino a 50 doc/mese 19,90 € + 0,45 €/doc oltre; fino a 100 → 29,90 € + 0,35; fino a 200 → 39,90 € + 0,25; oltre 200 su preventivo. Conservazione opzionale 5 €/mese. Firma e invio inclusi | App dentro la dashboard Stripe, trasforma i dati Stripe in XML; dietro c'è l'API A-Cube (REST, JSON o XML, webhook, sandbox gratis) | Opzionale 5 €/mese | Sì, in tempo reale | Non verificato | **non chiaro** — zero codice, ma da provare in sandbox se legge il codice destinatario; a 500 clienti prezzo ignoto |
| **A-Cube — API** | Non pubblicato (preventivo) | Come sopra, con integration manager e SLA | — | Sì | — | **non chiaro** (prezzo) |
| **Fatture in Cloud** (TeamSystem) | Annuo: Standard 144 € (100 documenti/anno), Premium 252 € (400), **Premium Plus 348 € (800)**, Complete 612 € (3.000). API pubbliche solo in Premium Plus e Complete. Firma e conservazione incluse | API v2 REST ben documentata (developers.fattureincloud.it), webhook | Inclusa | Sì | Sì | **no** — i limiti di documenti annui non reggono 500 clienti (6.500 doc > 3.000 del piano più alto) |
| **FatturaExpress** | 39 €/mese o 450 €/anno, fatture illimitate, **più** un abbonamento Fatture in Cloud | Nessun codice: ascolta `invoice.paid` di Stripe e crea/invia la fattura su Fatture in Cloud, gestisce reverse charge UE ed extra UE, 3 tentativi in caso di errore | Quella di Fatture in Cloud | Sì (tramite FiC) | Non indicato | **no** — eredita i limiti di FiC e somma due canoni |
| **Fattura24** | Business 144 € primo anno, 192 € rinnovo (6.000 documenti, API); Complete 288/384 € (10.000) | API HTTPS per creare documenti, nota di credito TD04 | **Non offerta** (rimandano all'Agenzia) | **No**: "L'uso delle API consente solo la creazione automatica di una fattura elettronica dentro l'account in Fattura24, ma NON consente l'invio automatico" | Sì | **no** — serve un clic a mano per ogni fattura |
| **Aruba Fatturazione Elettronica** | Base 29,90 €/anno (1 € i primi 3 mesi), conservazione 10 anni inclusa, **solo pannello web**. API solo con utenza **Premium**, prezzo non presente nel listino ufficiale (fonti terze: 300 € di attivazione + da 600 €/anno, non verificato) | REST JSON documentata (upload, invio, ricerca, notifiche), limiti di chiamate a scaglioni | Inclusa | Sì (con Premium) | Tramite tipo documento | **no** — costo d'ingresso alto per i nostri volumi |
| **Agenzia delle Entrate** (servizi gratuiti) | Gratis | **Nessuna API** per i programmi senza accreditamento: procedura web, app e PEC; l'accesso "da programma" è proprio SDICoop/SDIFTP (§1) | **Gratis, 15 anni** | Solo a mano o via PEC | Sì (a mano) | **sì per la conservazione**, no per l'invio automatico |

Osservazioni:
- **Integrazioni "native" Stripe → SdI**: nel marketplace Stripe ho trovato solo l'app di A-Cube. Stripe stessa non dichiara alcun invio allo SdI e dal luglio 2025 non emette più nemmeno fatture elettroniche italiane per le proprie commissioni (servono autofatture TD17: è un tema contabile a parte, che Matteo conosce).
- **Ricezione**: tutti i servizi "sì" ricevono anche le fatture passive con un loro codice destinatario (per Invoicetronic va registrato `7HD37X0` nel cassetto fiscale). A noi interessa poco: per le fatture d'acquisto può bastare il codice già usato dallo studio o dalla società.
- **Codice destinatario o PEC del cliente**: è solo un campo dell'XML (`CodiceDestinatario` di 7 caratteri, oppure `0000000` + `PECDestinatario`). Con i servizi API lo mettiamo noi; con l'app Stripe va verificato da dove lo prende.

---

## 3. Fatture dal gestionale dello studio

Se Matteo usa già un gestionale per le fatture dello studio, si può caricare lì ogni mese un file CSV con i pagamenti Stripe (o usarne l'API, se esiste) e far partire le fatture da lì.

**Pro**
- Nessun canone nuovo; contabilità e registri IVA già nello stesso posto; Matteo lo conosce.
- Controllo umano su ogni fattura prima dell'invio.

**Contro**
- Lavoro manuale ogni mese (esporta, carica, controlla, invia): sostenibile a 50 clienti, pesante a 500.
- Ritardi: con la fattura immediata ci sono 12 giorni per trasmettere; un mese di ferie o una dimenticanza diventano fatture tardive. Si può usare la fattura differita (§4), ma resta una scadenza fissa ogni 15 del mese.
- Lo stato della fattura (consegnata, scartata) non torna in Bandi Radar: il cliente non la vede nella sua pagina Abbonamento.
- **Mescola i ricavi del servizio con quelli dello studio**: va bene solo se l'emittente è davvero lo studio (vedi §4, è il punto delicato).

**Giudizio: non chiaro.** Ragionevole come soluzione di partenza se l'emittente è lo studio e i clienti sono poche decine; non come soluzione stabile.

---

## 4. Questioni fiscali (quadro, non parere)

**Chi emette.** Emette chi firma il contratto con l'impresa cliente e riceve i soldi su Stripe: deve coincidere con il titolare dell'account Stripe. Un abbonamento a un software è un'attività d'impresa; per i commercialisti l'ordinamento professionale (D.Lgs. 139/2005, art. 4, *non letto in questa ricerca*) prevede incompatibilità con l'esercizio di attività d'impresa in nome proprio. Questo fa pensare a una **società apposita** (con Matteo socio) per gli abbonamenti; le success fee per il supporto alle domande potrebbero invece restare prestazioni dello studio, se è lo studio a svolgerle. Da verificare da Matteo con le norme dell'Ordine: è la decisione che condiziona tutto il resto (account Stripe, numerazione, gestionale).

**Momento di emissione.** Per le prestazioni di servizi l'operazione si considera effettuata al **pagamento** (art. 6 DPR 633/72, *non riletto sul web in questa ricerca*). Con la carta su Stripe il pagamento è l'addebito riuscito (evento `invoice.paid`), non il giorno in cui Stripe versa i soldi in banca. Conseguenze utili:
- prova gratuita e addebiti falliti → **nessuna fattura** (niente da stornare per i morosi);
- piano annuale addebitato ogni mese → una fattura per ogni addebito mensile.

**Fattura entro 12 giorni.** La fattura immediata va trasmessa entro 12 giorni dall'effettuazione (art. 21, confermato dall'Agenzia anche per le elettroniche); la data del documento è quella del pagamento. Con l'invio automatico al momento di `invoice.paid` il problema non si pone.

**Fattura differita mensile.** Possibile per i servizi documentati (qui le ricevute Stripe): una fattura TD24 per cliente entro il 15 del mese successivo. Utile solo se si fattura a mano (§3); con l'automatico è più semplice la fattura immediata, una per addebito.

**Scarti.** Una fattura scartata dallo SdI si considera non emessa; si corregge e si ritrasmette (con la prassi dei 5 giorni con stesso numero e data, *da confermare da Matteo*). Una **mancata consegna** invece è una fattura emessa: resta nel cassetto fiscale del cliente, va solo avvisato.

**Clienti esteri e consumatori.**
- Imprese UE ed extra UE: operazione non soggetta (art. 7-ter), reverse charge, codice destinatario `XXXXXXX`; si trasmette comunque allo SdI. Per importi senza IVA sopra 77,47 € valutare il bollo.
- Consumatori italiani: fattura via SdI con `0000000` e codice fiscale, più copia al cliente.
- Consumatori UE: servizio digitale, IVA del paese del cliente oltre la soglia UE di 10.000 € (OSS).
- **Proposta semplice**: per ora vendere solo a imprese con P.IVA italiana (Bandi Radar si rivolge a loro) e bloccare il resto nel checkout. Così una sola casistica: IVA 22%, niente bollo.

---

## 5. Cosa c'è già nel codice

`app/abbonamenti/__init__.py` già crea la sessione Checkout con `billing_address_collection=required` e `tax_id_collection[enabled]=true` (raccoglie ragione sociale e P.IVA, formato `eu_vat` tipo `IT12345678901`), registra gli eventi in `eventi_stripe` una volta sola e il portale clienti permette di cambiare indirizzo, P.IVA e nome. Manca: codice destinatario/PEC, codice fiscale (diverso dalla P.IVA per le ditte individuali), tabella fatture, gestione di `invoice.paid` e dei rimborsi. Stripe Checkout ammette al massimo **3 campi personalizzati** (testo fino a 255 caratteri), non modificabili poi dal cliente nel portale.

---

## 6. Raccomandazione

**Comprare il canale, non il gestionale: Invoicetronic, con l'XML generato da Bandi Radar e la conservazione gratuita dell'Agenzia.**

Perché questa strada:
1. **Costa poco e scala**: pochi euro al mese a 50 clienti, circa 25-30 € a 500, a consumo prepagato senza canone.
2. **Python, sandbox gratis, webhook**: si integra nello stesso stile di Stripe (evento firmato → stato in tabella).
3. **Niente accreditamento, niente PEC da leggere, niente firma** (non serve tra privati).
4. **Non ci lega**: l'XML FatturaPA lo prepariamo noi ed è standard. Se Invoicetronic sparisse o alzasse i prezzi, si passa a Openapi (o A-Cube) cambiando solo la chiamata d'invio. È la ragione per non usare l'app Stripe di A-Cube, che è comoda ma chiusa e senza prezzo pubblico oltre 200 documenti/mese.
5. **Conservazione**: adesione una volta sola al servizio gratuito dell'Agenzia (15 anni). Pagare la conservazione al fornitore sarebbe un costo inutile.

Prima di tutto serve la decisione di Matteo su **chi emette** (§4): il flusso tecnico è lo stesso, cambiano solo i dati del cedente nell'XML e l'account Stripe.

### Flusso tecnico proposto

**Dati da chiedere al cliente** (pagina "Dati di fatturazione" di Bandi Radar, *prima* del checkout, modificabile dopo; tabella separata `dati_fatturazione`, mai nei profili anonimi e mai nelle chiamate all'IA):
- ragione sociale;
- partita IVA (controllo del formato e, se si vuole, verifica VIES);
- codice fiscale (precompilato uguale alla P.IVA, modificabile per le ditte individuali);
- **codice destinatario (7 caratteri) oppure PEC** (almeno uno; se nessuno dei due, `0000000` e la fattura resta nel cassetto fiscale);
- indirizzo della sede (via, CAP, comune, provincia).

Raccoglierli in una pagina nostra invece che con i campi personalizzati di Stripe: si validano meglio, il cliente li può correggere, e restano disponibili anche per le success fee. Nel checkout si lasciano attivi `tax_id_collection` e l'indirizzo come controllo incrociato.

**Eventi Stripe da usare**
| Evento | Cosa fa Bandi Radar |
|---|---|
| `invoice.paid` (con `amount_paid > 0`) | Crea la fattura: numero progressivo dell'anno (assegnato in transazione nel database), data = data del pagamento, righe dalle righe della fattura Stripe (abbonamento, imprese e sedi in più), IVA 22%, pagamento "carta, già incassato". Genera l'XML, lo invia, salva l'identificativo del fornitore |
| `charge.refunded` / `credit_note.created` | Nota di credito TD04 collegata alla fattura originaria |
| `invoice.payment_failed` | Nessuna fattura (già gestito per lo stato dell'abbonamento) |
| `checkout.session.completed` | Solo per collegare il cliente Stripe ai dati di fatturazione |

**Ritorno dal fornitore** (webhook Invoicetronic): consegnata → la fattura appare nella pagina Abbonamento dell'impresa; **scartata** → avviso a Matteo con il motivo, correzione dei dati e reinvio; mancata consegna → email al cliente ("la trova nel suo cassetto fiscale").

**Success fee**: dalla pagina Imprese l'admin crea un addebito Stripe (fattura Stripe da pagare); quando arriva `invoice.paid` segue lo stesso percorso.

**Controlli**: una volta al mese, confronto automatico tra pagamenti Stripe e fatture emesse (nessun pagamento senza fattura), visibile nella pagina Supervisione.

**Lavoro stimato**: 4-6 giorni (XML e test sugli esempi ufficiali, tabella e numerazione, eventi, webhook del fornitore, pagina dati di fatturazione, prove in sandbox).

### Costo mensile stimato (IVA esclusa)

| | 50 clienti (~60 doc/mese) | 500 clienti (~540 doc/mese) |
|---|---|---|
| **Invoicetronic** (raccomandato) | ~6 € (pacchetto 1.000 a 100 €, dura ~16 mesi) | ~25-30 € (pacchetti da 5.000 a 0,055 €; ~22 € con quello da 20.000) |
| Conservazione Agenzia | 0 € | 0 € |
| *Confronto* Openapi (solo invio) | ~3-4 € | ~26-38 € |
| *Confronto* A-Cube app Stripe | ~25-35 € | su preventivo |
| *Confronto* Fatture in Cloud + FatturaExpress | ~68 € (29 + 39) | non regge i volumi |

---

## Sintesi

- Stripe non manda nulla allo SdI: per ogni addebito pagato serve una fattura elettronica, che possiamo emettere in automatico al momento dell'evento `invoice.paid`.
- Costruire tutto in casa (canale SDICoop o PEC) è possibile ma costa settimane e rischi per risparmiare pochi euro al mese: **no**.
- La firma digitale non serve tra privati, e la conservazione a norma è **gratuita con l'Agenzia delle Entrate** (15 anni): non vanno pagate a un fornitore.
- Tra i servizi visti, Invoicetronic (da 0,04 a 0,10 € a fattura, SDK Python, sandbox gratis) e Openapi (circa 0,05 €) sono i più adatti; A-Cube offre l'unica app nel marketplace Stripe ma senza prezzo pubblico oltre 200 documenti/mese; Fatture in Cloud non regge 500 clienti; Fattura24 non invia allo SdI via API; Aruba chiede l'utenza Premium per le API.
- Raccomandazione: XML generato da Bandi Radar, invio con Invoicetronic, conservazione dell'Agenzia; circa 6 €/mese a 50 clienti e 25-30 € a 500; 4-6 giorni di lavoro.
- Il gestionale dello studio è una partenza possibile a poche decine di clienti, ma è manuale e mescola i ricavi.
- Prima di partire Matteo deve decidere chi emette (studio o società apposita, anche per le incompatibilità del commercialista) e se vendere solo a imprese italiane (consigliato all'inizio).

## Conseguenze per il progetto

- Decisione da chiedere a Matteo: emittente (studio o società) e limitazione iniziale a imprese con P.IVA italiana.
- Da aggiungere ad `app/abbonamenti/`: tabella `dati_fatturazione`, tabella `fatture` con numerazione, gestione di `invoice.paid` e dei rimborsi, invio a Invoicetronic, webhook di ritorno; variabili in `deploy/env.example` (senza valori).
- Azione una tantum dell'emittente: adesione alla conservazione gratuita nel portale Fatture e Corrispettivi.
- Tema separato per la contabilità: autofatture TD17 per le commissioni Stripe.

## Pagine viste

- https://invoicetronic.com/en/pricing/
- https://invoicetronic.com/en/features/
- https://invoicetronic.com/en/docs/prerequisites/
- https://openapi.com/products/italian-electronic-invoicing
- https://console.openapi.com/apis/sdi/pricing
- https://www.acubeapi.com/prodotti/connettori/app-e-invoicing-stripe
- https://www.acubeapi.com/prodotti/api-e-invoicing-italia
- https://www.fattureincloud.it/costo/
- https://developers.fattureincloud.it/docs/FAQs/
- https://fatturaexpress.com/
- https://www.fattura24.com/prezzi/
- https://www.fattura24.com/api/crea-fattura-elettronica/
- https://www.aruba.it/listino-fatturazione-elettronica.aspx
- https://fatturazioneelettronica.aruba.it/apidoc/docs.html
- https://www.fatturapa.gov.it/it/comefare/operatori-economici/inviare-la-fatturapa/index.html
- https://www.agenziaentrate.gov.it/portale/schede/comunicazioni/fatture-e-corrispettivi/faq-fe/risposte-alle-domande-piu-frequenti-categoria/registrazione-e-conservazione-delle-fatture
- https://www.agenziaentrate.gov.it/portale/schede/comunicazioni/fatture-e-corrispettivi/faq-fe/risposte-alle-domande-piu-frequenti-categoria/compilazione-della-fattura-elettronica-imprese
- https://docs.stripe.com/payments/checkout/custom-components.md?platform=web&payment-ui=stripe-hosted
- https://docs.stripe.com/tax/checkout/tax-ids
- https://stripe.com/resources/more/data-einvoices-italy
