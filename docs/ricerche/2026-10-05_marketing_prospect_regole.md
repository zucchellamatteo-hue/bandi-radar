# Marketing verso le imprese prospect: cosa si può fare e cosa no

- **Data:** 05/10/2026
- **Domanda:** Matteo può lanciare Bandi Radar mandando una prima email personalizzata ("esiste il bando X, fino a Y €; abbonati; possiamo presentare la domanda a success fee") alle ~43.000 imprese del database `leadgen` (Google Maps + crawling dei siti, email generiche tipo `info@`; 8.200 arricchite con Cerved)? Se no, quali canali sono leciti e con quali regole?
- **Metodo:** ricerca web e lettura diretta dei provvedimenti sul sito del Garante (garanteprivacy.it, docweb), del testo dell'art. 130 del Codice privacy (riportato da Brocardi), di una sentenza della Corte di giustizia UE (EUR-Lex) e di commenti di studi legali dove il provvedimento originale non era raggiungibile. Contesto del database da `docs/ricerche/2026-09-25_schema_anagrafiche_leadgen.md`.
- **Limiti:**
  - **Non è un parere legale.** È una ricognizione fatta da un assistente IA; prima di qualunque invio va fatta verificare da un avvocato esperto di protezione dati (vedi §8).
  - Alcuni provvedimenti sono stati letti tramite un riassunto automatico della pagina: date, importi e nomi sono stati controllati sul sito del Garante, ma le citazioni sono brevi e vanno rilette sull'originale.
  - Non ho trovato un provvedimento del Garante che parli **espressamente** delle caselle generiche `info@` di società: la conclusione su quel punto (§2.3) è un ragionamento sulle norme, non un precedente.
  - Non ho letto il contratto di licenza Cerved di Matteo né i termini d'uso di Google Maps: entrambi possono porre limiti ulteriori (contrattuali, non solo privacy).

---

## 1. Risposta breve

**No: la prima email non richiesta alle 43.000 imprese non è lecita in Italia**, nemmeno se le imprese sono società e l'indirizzo è un `info@` pubblicato sul loro sito. L'email promozionale richiede il **consenso preventivo** del destinatario (art. 130, commi 1-2, Codice privacy), il consenso vale anche per le **persone giuridiche** (sono "contraenti"), e il Garante ripete dal 2003 che i dati presi da siti web, elenchi o registri pubblici **non** si possono usare per promozione senza consenso. Il "legittimo interesse" del GDPR **non** sostituisce il consenso per l'email. Chiedere il consenso con la prima email è a sua volta considerato una comunicazione promozionale.

Restano però canali leciti (posta cartacea alle società, Google Ads, contenuti, webinar, partner, clienti dello studio con le dovute cautele) e la mappatura delle imprese resta utilissima **come strumento interno** per scegliere dove e a chi rivolgersi (§7).

---

## 2. Domanda 1 — email promozionali non richieste alle imprese

### 2.1 La regola

| Punto | Fonte vista | Giudizio |
|---|---|---|
| Email, SMS, fax, chiamate automatiche a fini promozionali solo con **consenso preventivo** (opt-in) | Art. 130 c. 1-2 Codice privacy, testo su [Brocardi](https://www.brocardi.it/codice-della-privacy/parte-ii/titolo-x/capo-i/art130.html); [Linee guida Garante 4/7/2013, docweb 2542348](https://www.garanteprivacy.it/home/docweb/-/docweb-display/docweb/2542348) | sì, vale |
| La regola protegge il **"contraente"**, che può essere anche una **persona giuridica** (società, ente, associazione): la riforma del 2011 che ha tolto le società dalla nozione di "dato personale" non le ha tolte dall'art. 130 | [Garante, provv. 20/9/2012, docweb 2094932](https://www.garanteprivacy.it/home/docweb/-/docweb-display/docweb/2094932); [comunicato 13/11/2012 "imprese ancora tutelate dal telemarketing", docweb 2094796](https://www.garanteprivacy.it/home/docweb/-/docweb-display/docweb/2094796) | sì, vale anche per le società |
| Dati presi da **siti web, elenchi, registri pubblici** non utilizzabili per promozione senza consenso: "senza il preventivo consenso ... non è possibile inviare comunicazioni promozionali ... anche se i dati personali sono tratti da registri pubblici, elenchi, siti web" | Linee guida 2013 (docweb 2542348); ribadito in [Isinc S.r.l.s., 21/4/2021, docweb 9680996](https://www.garanteprivacy.it/web/guest/home/docweb/-/docweb-display/docweb/9680996) | sì, vale |
| Il **legittimo interesse** (art. 6.1.f GDPR, considerando 47) **non** basta per l'email: l'art. 130 è norma speciale (direttiva ePrivacy 2002/58) e prevale | [Iliad Italia, 17/7/2024, docweb 10084158](https://www.garanteprivacy.it/home/docweb/-/docweb-display/print/10084158) (il soft spam è "deroga all'obbligo di consenso", non base giuridica); [Geturhotels, 23/10/2025, docweb 10199166](https://www.garanteprivacy.it/home/docweb/-/docweb-display/docweb/10199166) (legittimo interesse respinto per SMS); Cassazione ord. 15881/2025 (commento su [leggeinchiaro.it](https://leggeinchiaro.it/newsletter-email-marketing-consenso-art-130-codice-privacy-cassazione-15881-2025/)) | sì, vale |
| La Corte di giustizia UE ha detto che anche un interesse **commerciale** può essere "legittimo interesse" | [CGUE C-621/22 KNLTB, 4/10/2024](https://eur-lex.europa.eu/legal-content/EN/TXT/?uri=celex%3A62022CJ0621) | non cambia nulla per l'email: riguarda l'art. 6 GDPR, non l'art. 130/ePrivacy. Utile invece per la posta cartacea (§4) |
| Telefonate: il fatto che un numero sia **su internet** non lo rende utilizzabile per qualsiasi scopo | Garante provv. n. 4 del 12/1/2017, letto solo nel commento di [FiscoeTasse](https://www.fiscoetasse.com/approfondimenti/12769-privacy-no-al-telemarketing-con-i-numeri-di-telefono-prelevati-in-internet.html) | sì, vale (provvedimento originale non letto) |

### 2.2 Informativa (art. 14 GDPR)

Quando i dati **personali** non sono raccolti presso l'interessato (è il caso di Google Maps, siti, Cerved), il titolare deve dare l'informativa dell'art. 14 GDPR entro un mese e comunque **al primo contatto**, indicando anche la **fonte** dei dati. Questo obbligo riguarda le persone fisiche: titolari di ditte individuali, professionisti, amministratori e soci presenti nelle tabelle Cerved, persone il cui nome compare nell'email (es. `mario.rossi@...`). L'informativa **non rende lecito** l'invio: serve in aggiunta alla base giuridica, non al posto. Giudizio: **sì, obbligo da rispettare** per qualunque uso dei dati delle persone fisiche.

### 2.3 Caselle `info@` e PEC

| Caso | Ragionamento / fonte | Giudizio |
|---|---|---|
| `info@impresa.it` di una **società** | L'indirizzo non è "dato personale" (GDPR non si applica alla società), ma l'art. 130 tutela il **contraente**, persona giuridica compresa (docweb 2094932). Nessun provvedimento trovato che faccia un'eccezione per le caselle generiche | **no**, serve comunque il consenso (ragionamento, non precedente: da far confermare all'avvocato) |
| `info@` di una **ditta individuale** o di un professionista | È di fatto il recapito di una persona fisica: si applicano insieme art. 130 e GDPR | **no** |
| **PEC** prese da INI-PEC, Registro imprese, albi | Uso per pubblicità vietato senza consenso; l'estrazione di elenchi PEC è riservata alle pubbliche amministrazioni per comunicazioni istituzionali. Isinc: 20.000 € (docweb 9680996) | **no**, ed è il caso più sanzionato |

### 2.4 Chi può lamentarsi

Dal 2011 le persone giuridiche non possono presentare **reclamo** al Garante come interessati (Linee guida 2013), ma: (a) il Garante può agire d'ufficio o su segnalazione; (b) la società destinataria può agire davanti al giudice civile; (c) chi riceve materialmente l'email (dipendente, titolare di ditta individuale, professionista) è una persona fisica e **può** fare reclamo; (d) su 43.000 invii, i reclami sono statisticamente certi. Non contare su "tanto sono società".

---

## 3. Domanda 2 — "soft spam" (art. 130 c. 4) per i clienti dello studio

Testo: il titolare può usare, **per la vendita diretta di propri prodotti o servizi**, l'email **fornita dall'interessato nel contesto della vendita** di un prodotto o servizio, purché si tratti di **servizi analoghi**, con informativa iniziale e possibilità di opporsi in ogni messaggio.

| Requisito | Situazione di Matteo | Giudizio |
|---|---|---|
| Stesso titolare | L'email l'ha data il cliente **allo studio**. Se Bandi Radar è venduto da un soggetto diverso (es. la società di `qiaro.it`), il titolare **non è lo stesso** e la deroga cade | **non chiaro** — dipende da chi vende l'abbonamento |
| Contesto di una vendita (rapporto a pagamento) | I clienti dello studio pagano le prestazioni: sì. La Cassazione (ord. 15881/2025) interpreta la deroga in modo **restrittivo**: solo rapporti onerosi, non prove gratuite | sì per i clienti paganti |
| **Servizi analoghi** | Consulenza fiscale/contabile vs abbonamento a una banca dati di bandi: non è analogo in senso stretto. È più sostenibile per la **consulenza sulla finanza agevolata** (domanda a success fee) se lo studio la offre già, meno per l'abbonamento a 30 € | **non chiaro**, tendente al **no** per l'abbonamento |
| Informativa data al momento della raccolta | Va verificato se il mandato/informativa dello studio lo prevedeva | **non chiaro** |
| Solo email | Il soft spam vale **solo per l'email**, non per SMS/WhatsApp (Geturhotels, docweb 10199166) | sì, solo email |

**Conclusione pratica:** per i clienti dello studio la strada più sicura **non** è il soft spam ma la **richiesta di consenso fatta di persona** (colloquio, firma di un modulo, rinnovo del mandato, area clienti) oppure una comunicazione che rientri nel rapporto professionale in corso (il commercialista che segnala a un cliente un bando specifico per **quel** cliente è consulenza, non marketing di massa — da far confermare all'avvocato e da tenere distinta dalla promozione dell'abbonamento).

---

## 4. Domanda 3 — canali alternativi e loro regole

| Canale | Regola principale | Fonte vista | Giudizio |
|---|---|---|---|
| **Email fredda** (anche "solo per chiedere il consenso") | Il primo messaggio che chiede il consenso o offre l'opt-out è già promozionale e quindi illecito | Linee guida 2013 (docweb 2542348) | **no** |
| **PEC** | Come sopra, con aggravante | docweb 9680996 | **no** |
| **SMS / WhatsApp / chiamate automatiche** | Consenso obbligatorio, niente soft spam | art. 130 c. 1-2; docweb 10199166 | **no** |
| **Telefonata con operatore** | Opt-out (Registro pubblico delle opposizioni, esteso ai cellulari dal 27/7/2022, DPR 26/2022) **solo per numeri presi dagli elenchi telefonici pubblici**; numeri presi da Google Maps/siti richiedono il consenso; obbligo di consultare il Registro prima di ogni campagna e almeno ogni 30 giorni; le imprese sono tutelate | [MIMIT, consultazione RPO](https://www.mimit.gov.it/it/normativa/notifiche-e-avvisi/consultazione-pubblica-per-l-estensione-del-registro-pubblico-delle-opposizioni-ai-numeri-non-presenti-negli-elenchi-telefonici-pubblici-come-previsto-dal-d-p-r-n-26-2022); docweb 2094796; provv. 12/1/2017 | **non chiaro / sconsigliato**: con i numeri del database (presi dal web) è di fatto **no**; settore molto sanzionato |
| **Posta cartacea** a società | L'art. 130 c. 3 rinvia agli artt. 6-7 GDPR per i mezzi diversi da quelli dei commi 1-2; per le **società** il GDPR non si applica e non c'è un obbligo di consenso; con indirizzi tratti dagli elenchi telefonici vale l'opt-out via Registro opposizioni (obbligo di consultarlo e di indicare la fonte e come iscriversi) | art. 130 c. 3 su Brocardi; [Garante, posta cartacea e Registro, docweb 9058898](https://garanteprivacy.it/web/guest/home/docweb/-/docweb-display/docweb/9058898) | **sì** per le società (sede legale da registro imprese), con opt-out chiaro in ogni lettera |
| **Posta cartacea** a ditte individuali/professionisti | Persone fisiche: GDPR, base giuridica = legittimo interesse (considerando 47, CGUE C-621/22) con bilanciamento documentato, informativa art. 14 nella lettera, opposizione sempre possibile e rispettata; consultare il Registro se l'indirizzo viene dagli elenchi | considerando 47; C-621/22 | **non chiaro**, sostenibile con cautele: decisione da far validare all'avvocato |
| **LinkedIn / messaggi privati sui social** | Il Garante ha sanzionato un messaggio promozionale privato su LinkedIn (5.000 €): il profilo non è "fonte pubblica" e l'iscrizione non è consenso. **Però** il Tribunale di Milano ha annullato quel provvedimento nel 2024 (notizia da commenti, sentenza non letta) | [La Prima S.r.l., 16/9/2021, docweb 9705632](https://www.garanteprivacy.it/home/docweb/-/docweb-display/docweb/9705632); Linee guida 2013 (social) | **non chiaro**: messaggi uno a uno, pertinenti al ruolo, senza automazione, sono il rischio minore; campagne automatiche **no** |
| **Google Ads / LinkedIn Ads** | Pubblicità a pagamento mostrata a chi cerca: nessun problema di consenso per l'annuncio in sé; il **remarketing** e i pixel sul sito richiedono il consenso cookie. Caricare la lista email/telefoni del database per creare pubblico ("Customer Match") **no**: è un trattamento dei dati per marketing senza base | ragionamento | **sì** (ricerca e parole chiave); **no** per Customer Match con il database |
| **Contenuti / SEO** (schede pubbliche dei bandi, guide per settore e regione) | Nessun vincolo privacy; chi si iscrive alla newsletter dà il consenso (doppia conferma consigliata: Digilab ammonita anche per l'assenza di double opt-in) | [Digilab, 25/9/2025, docweb 10191282](https://www.garanteprivacy.it/home/docweb/-/docweb-display/docweb/10191282) | **sì** |
| **Webinar** ("i bandi aperti per il tuo settore") | Iscrizione con consenso separato e facoltativo al marketing | Linee guida 2013 (consenso specifico) | **sì** |
| **Associazioni di categoria, Confidi, ordini, consorzi, banche locali** | L'associazione scrive **ai propri iscritti** con la propria base giuridica (consenso o rapporto associativo); Matteo **non** riceve la lista. Contenuto co-firmato o convenzione (sconto per gli iscritti) | ragionamento | **sì**, la verifica della base giuridica tocca all'associazione |
| **Clienti dello studio** | Vedi §3: consenso raccolto di persona; soft spam incerto | §3 | **sì** con consenso; soft spam **non chiaro** |
| **Passaparola / segnalazioni** dai clienti | Programma "porta un'impresa"; il cliente presenta, l'impresa si registra da sola | ragionamento | **sì** |

---

## 5. Domanda 4 — dati Cerved e profilazione delle imprese

| Punto | Fonte / ragionamento | Giudizio |
|---|---|---|
| Dati **societari** puri (ATECO, fatturato, dipendenti, bilanci di una società) | Non sono dati personali: il GDPR non si applica. Limiti solo **contrattuali** (licenza Cerved: uso interno? divieto di ricedere? durata?) | **sì** per analisi interne, salvo contratto |
| **Soci e amministratori** persone fisiche (tabelle `leads_persone`, `leads_soci`) | Sono dati personali. Il Codice di condotta delle informazioni commerciali consente agli operatori come Cerved di trattarli per verifiche di solidità e affidabilità, anche per "l'individuazione di soggetti per l'avvio di nuovi rapporti commerciali", ma **non** cita il marketing né le comunicazioni promozionali | [Codice di condotta, provv. 29/4/2021, docweb 9586215](https://www.garanteprivacy.it/home/docweb/-/docweb-display/docweb/9586215) | **no** per contattarli o profilarli a fini promozionali; da non portare in Bandi Radar (già la regola del progetto) |
| **Ditte individuali** (impresa = persona fisica) | Tutti i loro dati sono dati personali: profilazione commerciale = trattamento GDPR con base giuridica, informativa art. 14, diritto di opposizione | GDPR artt. 6, 14, 21 | **non chiaro**: meglio escluderle da qualsiasi contatto diretto e usarle solo in forma aggregata |
| **Abbinamento anonimo bandi ↔ categorie** (es. "nel Friuli ci sono 1.200 imprese manifatturiere con 10-49 dipendenti; 7 bandi aperti le riguardano") | Dati aggregati, nessun contatto: serve per decidere dove investire in pubblicità e contenuti | ragionamento | **sì** |
| **Scraping** di siti per raccogliere email | Il Garante considera il web scraping un trattamento da giustificare; per l'uso promozionale la risposta è già no (§2) | [Garante, web scraping, 20/5/2024, docweb 10020316](https://www.garanteprivacy.it/home/docweb/-/docweb-display/docweb/10020316) | **no** per marketing; ok fermare la raccolta di email |

---

## 6. Domanda 5 — rischi concreti e sanzioni recenti

| Provvedimento | Fatti | Esito |
|---|---|---|
| [Lex Iuris S.r.l., 12/2/2026, docweb 10225019](https://www.garanteprivacy.it/web/guest/home/docweb/-/docweb-display/docweb/10225019) (commento [Aliprandi](https://aliprandi.org/2026/05/13/sanzione-15mila-euro-garante-privacy-per-email-marketing-e-mancato-riscontro-interessato/)) | Piccola società di formazione: email promozionali a due avvocati con indirizzi da fonti pubbliche, senza consenso; non ha risposto alla richiesta di accesso | **15.000 €** nonostante "episodio isolato" e piccola impresa |
| [Geturhotels S.r.l., 23/10/2025, docweb 10199166](https://www.garanteprivacy.it/home/docweb/-/docweb-display/docweb/10199166) | SMS promozionali per anni dopo una prenotazione; legittimo interesse invocato e respinto | **6.000 €** |
| [Digilab S.r.l., 25/9/2025, docweb 10191282](https://www.garanteprivacy.it/home/docweb/-/docweb-display/docweb/10191282) | Liste acquistate, niente double opt-in | ammonimento e ordine di cessare |
| [Iliad Italia, 17/7/2024, docweb 10084158](https://www.garanteprivacy.it/home/docweb/-/docweb-display/print/10084158) | Soft spam a un cliente che aveva negato il consenso al marketing | **50.000 €** |
| [La Prima S.r.l., 16/9/2021, docweb 9705632](https://www.garanteprivacy.it/home/docweb/-/docweb-display/docweb/9705632) | Un solo messaggio LinkedIn promozionale | 5.000 € (poi annullato dal Tribunale, da verificare) |
| [Isinc S.r.l.s., 21/4/2021, docweb 9680996](https://www.garanteprivacy.it/web/guest/home/docweb/-/docweb-display/docweb/9680996) | Email promozionali a PEC estratte da INI-PEC | **20.000 €**, divieto e cancellazione dei dati |

Rischi oltre la multa:
- **Massimo teorico:** fino a 20 milioni o 4% del fatturato (art. 83 GDPR, richiamato dall'art. 166 Codice per l'art. 130). Le multe reali per piccoli titolari sono nell'ordine di 5.000–50.000 €, più la **pubblicazione** del provvedimento con il nome.
- **Ordine di cancellare** il database: è il danno più grave per Matteo, perché la mappatura perderebbe valore.
- **Danno reputazionale** per un commercialista (deontologia dell'Ordine) e per il dominio: 43.000 email fredde portano il dominio `finanzagevolata.qiaro.it` nelle liste nere antispam, e Resend può sospendere l'account (le sue regole vietano liste non raccolte con consenso — da verificare sui termini di Resend).
- **Rilevanza penale:** l'art. 167 Codice punisce chi viola l'art. 130 per trarne profitto o causare danno, se ne deriva nocumento. Improbabile in un caso come questo, ma da far valutare all'avvocato.
- Volume del settore: secondo commenti alla Relazione annuale 2024 del Garante, il marketing è il primo settore per reclami (oltre 4.000) e sanzioni (dato non letto sulla Relazione originale).

---

## 7. Proposta di go-to-market lecita (in passi ordinati)

Idea di fondo: **la mappatura delle imprese non serve per scrivere alle imprese, serve per sapere a chi parlare e cosa dire**, e poi farle arrivare da sole a Bandi Radar.

1. **Fermare** l'invio delle email già pronte (`emails_ready_to_send`, 75 righe) e la raccolta di nuove email dal crawling. Tenere i modelli di cold email solo come base per testi di pagine, lettere e annunci.
2. **Separare i dati**: in Bandi Radar portare solo dati societari aggregabili (ATECO, provincia, classe di dipendenti e di fatturato) delle **società**; niente nomi, email, telefoni, soci, amministratori, ditte individuali (coerente con la regola dei profili anonimi).
3. **Abbinamento anonimo per categoria**: far girare il motore di match di Bandi Radar sui "profili tipo" ricavati dal database (es. "manifattura, UD, 10-49 dipendenti") e ottenere una classifica: quali settori e territori hanno più bandi aperti e più valore in euro. È il listino di cosa promuovere e dove.
4. **Pagine pubbliche per categoria** su `finanzagevolata.qiaro.it` ("Bandi aperti per le imprese edili in Friuli: 7, fino a 200.000 €"), alimentate dalle schede: SEO, e destinazione degli annunci. Iscrizione alla newsletter gratuita con **doppia conferma** e consenso al marketing separato.
5. **Google Ads sulle categorie più ricche** del passo 3 (parole come "bando [settore] [regione]", "contributi a fondo perduto [attività]"), budget piccolo e misurato. Nessun caricamento di liste del database.
6. **Clienti dello studio**: chiedere il consenso **di persona** (modulo al prossimo incontro o con il rinnovo del mandato, area clienti); intanto il commercialista segnala ai singoli clienti i bandi che li riguardano come parte della consulenza, senza promuovere l'abbonamento finché non c'è il consenso.
7. **Partner**: proporre a 2-3 associazioni di categoria, Confidi o ordini locali, scelti con la classifica del passo 3, un webinar co-firmato o una convenzione per i loro iscritti; sono loro a scrivere ai propri iscritti.
8. **Posta cartacea mirata (facoltativa, dopo il via libera dell'avvocato)**: lettera alle **sole società** delle categorie migliori, all'indirizzo della sede, con il bando concreto ("nel vostro settore è aperto il bando X, fino a Y €"), un codice o QR per registrarsi, l'indicazione della fonte dell'indirizzo e un modo semplice per non ricevere altro (lista interna di esclusione, rispettata per sempre). Partire con un lotto piccolo (es. 200 lettere) e misurare.
9. **Webinar mensile** "bandi aperti del mese" per settore, con iscrizione e consenso: diventa il canale principale verso l'abbonamento a 30 € e verso la domanda a success fee.
10. **Registro dei consensi**: in Bandi Radar salvare per ogni iscritto quando, come e per cosa ha dato il consenso (serve a dimostrarlo al Garante).

---

## 8. Cosa far verificare a un avvocato (privacy/ePrivacy)

1. Conferma che l'art. 130 c. 1-2 vale anche per le caselle generiche `info@` delle società (nessun precedente specifico trovato).
2. Soft spam: chi è il titolare che vende Bandi Radar (lo studio o un'altra società) e se abbonamento e domanda a success fee sono "servizi analoghi" a quelli dello studio.
3. Posta cartacea: liceità verso società con indirizzo da registro imprese/Cerved; verso ditte individuali, testo del bilanciamento del legittimo interesse e dell'informativa art. 14.
4. Contratto Cerved: se consente l'uso dei dati per selezionare destinatari di comunicazioni commerciali (anche solo cartacee) e per quanto tempo.
5. Termini d'uso di Google Maps per i dati già estratti; sorte del database (conservare, ridurre, cancellare le email).
6. Esito definitivo del caso LinkedIn (Tribunale di Milano 2024) prima di usare messaggi uno a uno.
7. Aspetti deontologici per un commercialista che promuove servizi a success fee.
8. Testi: informativa del sito, modulo di consenso, informativa nelle lettere, registro dei trattamenti.

---

## Sintesi

- L'email fredda alle 43.000 imprese **non è lecita**: serve il consenso preventivo anche per le società (art. 130 Codice privacy, "contraenti"), anche per gli `info@` trovati sul web, anche per chiedere il consenso stesso. Il legittimo interesse non basta per l'email.
- PEC e LinkedIn automatico sono i casi più rischiosi; le sanzioni recenti per piccole imprese vanno da 5.000 a 50.000 €, con pubblicazione e ordine di cancellare i dati.
- Il soft spam per i clienti dello studio è **incerto** (titolare diverso? servizio analogo?): meglio raccogliere il consenso di persona.
- Leciti: contenuti/SEO, Google Ads sulle parole chiave, webinar, partner che scrivono ai propri iscritti, passaparola; posta cartacea alle società quasi certamente sì (opt-out), da validare.
- I dati Cerved su soci e amministratori non vanno usati per il marketing; quelli societari sì per analisi interne, nei limiti del contratto.
- La mappatura resta preziosa come **bussola anonima**: dice quali settori e territori hanno più bandi e dove investire.

## Conseguenze per il progetto

- Nessuna importazione in Bandi Radar di email, telefoni, nomi, soci, amministratori e ditte individuali dal database `leadgen`; solo profili tipo aggregati.
- Da prevedere: pagine pubbliche per categoria, iscrizione con doppia conferma e registro dei consensi, lista di esclusione per la posta cartacea.
- Resend da usare solo verso iscritti con consenso.
