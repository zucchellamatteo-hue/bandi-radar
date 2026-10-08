# Documentazione legale per vendere bandinQiaro

**Bozza del 05/10/2026, da far rivedere a un professionista** (avvocato, consulente privacy e, per la parte fiscale e ordinistica, un collega commercialista o l'Ordine). Questa cartella è interna: **non viene pubblicata sul sito**. I testi pubblici (termini, privacy, cookie, supporto, note legali) stanno in `app/pubblico/testi/`.

Qui c'è l'elenco di tutto quello che serve prima di far pagare il servizio a clienti che non sono già clienti dello studio, con lo stato di ogni voce.

Legenda dello stato:

- **Bozza fatta**: c'è un testo da completare e far rivedere.
- **Da fare (Matteo)**: decisione o adempimento che spetta a Matteo, di solito veloce.
- **Professionista**: serve il parere o l'intervento di un professionista esterno.
- **Tecnico**: lavoro sul sistema, lo fa una sessione di Claude.

## 1. Chi vende: soggetto, attività, compatibilità

| Voce | Cosa serve | Stato |
|---|---|---|
| Chi è il fornitore | Decidere se bandinQiaro lo vende lo studio di Matteo (attività professionale) o una società separata (per esempio una Srl). Da questa scelta dipendono tutti i segnaposto `[RAGIONE SOCIALE DEL TITOLARE]`, la fatturazione, l'assicurazione e la compatibilità con l'Ordine. | Da fare (Matteo) + Professionista |
| Compatibilità con l'Ordine dei commercialisti | Il d.lgs. 139/2005 (art. 4) rende incompatibile con l'iscrizione l'esercizio di attività d'impresa, salvo eccezioni. Vendere un abbonamento a un servizio informativo è un'attività commerciale: va verificato (note interpretative del CNDCEC sulle incompatibilità, eventualmente quesito all'Ordine locale) se Matteo può farlo dallo studio, o se serve una società in cui abbia un ruolo compatibile (per esempio socio senza poteri di amministrazione). Il **supporto alla domanda a success fee** invece è un'attività tipicamente professionale e può restare allo studio. | Professionista |
| Codice ATECO | Scegliere il codice dell'attività di vendita degli abbonamenti (classificazione ATECO 2025). Candidati da valutare: servizi di informazione (gruppo 63.9), elaborazione dati e servizi correlati (63.1), consulenza imprenditoriale (70.2) per la parte di supporto. Da decidere insieme alla forma del fornitore; se l'attività va nello studio, valutare se aggiungere un codice secondario. | Da fare (Matteo) |
| Iscrizioni | Se società: atto costitutivo, iscrizione al Registro delle imprese, PEC, comunicazione di inizio attività con il codice ATECO. Se studio: eventuale variazione della dichiarazione IVA di inizio/variazione attività (modello AA9/AA7) con il nuovo codice. | Da fare (Matteo) |
| Note legali sul sito | Dati obbligatori del fornitore (art. 7 d.lgs. 70/2003, art. 2250 c.c.). | Bozza fatta: `app/pubblico/testi/note_legali.html` (manca il collegamento alla pagina `/note-legali`, Tecnico) |
| Marchio e dominio | Verificare che il nome "bandinQiaro" non sia già un marchio registrato per servizi simili; valutare la registrazione. Dominio `bandinqiaro.it` (dal 07/10; il vecchio `finanzagevolata.qiaro.it` rinvia lì): controllare a chi sono intestati. | Da fare (Matteo) |

## 2. Fisco e fatturazione

| Voce | Cosa serve | Stato |
|---|---|---|
| Posizione IVA | Prezzi IVA esclusa (decisione del 05/10); IVA ordinaria sui servizi a imprese italiane. Se arrivano clienti con partita IVA di altri Paesi UE: fattura senza IVA con inversione contabile e comunicazione negli elenchi Intrastat servizi. Clienti senza partita IVA (consumatori): il servizio non è pensato per loro, ma i termini prevedono il caso. | Da fare (Matteo), con il proprio commercialista se il fornitore è una società |
| Fatturazione elettronica | Stripe non invia le fatture allo SdI. Serve un servizio di fatturazione elettronica collegato a Stripe che, a ogni pagamento, emetta la fattura con i dati del cliente (ragione sociale, P.IVA, codice destinatario o PEC). Da scegliere. Il checkout deve raccogliere partita IVA e codice destinatario/PEC. | Da fare (Matteo): scelta del servizio · Tecnico: collegamento e campi nel checkout |
| Conservazione a norma delle fatture | Le fatture elettroniche vanno conservate per 10 anni con conservazione a norma (servizio gratuito dell'Agenzia delle Entrate o quello del fornitore di fatturazione). | Da fare (Matteo) |
| Pagamenti e incassi | Riconciliare gli accrediti di Stripe (al netto delle commissioni) con le fatture; le commissioni di Stripe sono un costo documentato dalle sue fatture (Stripe è irlandese: inversione contabile). | Da fare (Matteo) |

## 3. Contratti con i clienti

| Voce | Cosa serve | Stato |
|---|---|---|
| Termini e condizioni | Prezzi IVA esclusa, impegno annuale, disdetta, limiti di responsabilità, foro. | Bozza fatta: `app/pubblico/testi/termini.html` |
| Approvazione specifica delle clausole (artt. 1341-1342 c.c.) | Elenco nei termini (punto 16) e **seconda casella** separata nel checkout; il sistema deve salvare data, ora e versione dei termini accettati. | Bozza fatta (testo) · Tecnico (casella e registrazione) · Professionista (validità della doppia spunta online) |
| Condizioni del supporto a success fee | Pagina pubblica che riassume il servizio. | Bozza fatta: `app/pubblico/testi/supporto.html` (mancano percentuali e minimo) |
| Modello di incarico per il supporto | Lettera di incarico da firmare per ogni domanda seguita. Per i commercialisti il compenso va pattuito per iscritto con preventivo (art. 9 d.l. 1/2012). Verificare la legge sull'equo compenso (l. 49/2023) per i clienti grandi (oltre 50 dipendenti o 10 milioni di fatturato), per i quali un compenso solo a successo potrebbe non essere ammesso. | Bozza fatta: `incarico_supporto.md` · Professionista |
| Assicurazione professionale | Obbligatoria per il professionista (d.p.r. 137/2012, art. 5): verificare che la polizza dello studio copra anche il supporto alle domande di agevolazione e indicarne gli estremi nell'incarico. Se il servizio in abbonamento lo vende una società, valutare una polizza di responsabilità civile per la società (errori nelle schede). | Da fare (Matteo) |
| Antiriciclaggio | Il supporto alla domanda è una prestazione professionale del commercialista: si applicano gli obblighi del d.lgs. 231/2007 (adeguata verifica del cliente e del titolare effettivo, conservazione dei dati per 10 anni, segnalazioni) secondo le regole tecniche del CNDCEC. Per l'abbonamento al servizio informativo, se venduto da una società non professionale, di norma no: da confermare. | Professionista (conferma) · Da fare (Matteo): applicare la procedura dello studio a ogni incarico |

## 4. Pagamenti

| Voce | Cosa serve | Stato |
|---|---|---|
| Contratto con Stripe | Apertura dell'account Stripe intestato al fornitore, verifica dell'identità e del conto, accettazione del Stripe Services Agreement (contiene anche l'accordo sul trattamento dei dati). Attivare le chiavi vere solo dopo termini, privacy e fatturazione pronti (`STRIPE_PAGAMENTI_VERI=1`). | Da fare (Matteo) |
| Descrizione sull'estratto conto e email di Stripe | Nome riconoscibile ("BANDI RADAR"), email di ricevuta, link a termini e privacy nel checkout. | Tecnico |

## 5. Privacy (GDPR)

| Voce | Cosa serve | Stato |
|---|---|---|
| Informativa privacy | Artt. 13-14 GDPR. | Bozza fatta: `app/pubblico/testi/privacy.html` |
| Registro dei trattamenti | Art. 30 GDPR: con dati di clienti e trattamenti continuativi va tenuto. | Bozza fatta: `registro_trattamenti.md` |
| Accordi con i fornitori (DPA) | Art. 28 GDPR: OVH, Resend, Stripe, Anthropic, Google Ads, futuro servizio di fatturazione. | Bozza fatta (elenco e controlli): `responsabili_dpa.md` · Da fare (Matteo): accettarli e archiviarne copia |
| Valutazione d'impatto (DPIA) | Probabilmente **non obbligatoria**: non ci sono dati particolari, il profilo descrive l'impresa e non la persona, l'abbinamento è un suggerimento senza effetti giuridici, i volumi sono piccoli. Conviene comunque scrivere due righe con questa valutazione (va bene una nota nel registro). Da rifare se arrivano le pratiche con i documenti dei clienti (vedi `docs/PIANO_PRATICHE.md`) o se l'IA dovesse ricevere dati dei clienti. | Bozza fatta (nota nel registro) · Professionista (conferma) |
| Responsabile della protezione dei dati (DPO) | Non obbligatorio per un'attività di queste dimensioni senza trattamenti su larga scala di dati particolari. Togliere il paragrafo nell'informativa se non nominato. | Da fare (Matteo): conferma |
| Consenso per le email commerciali | Casella separata e non preselezionata, informativa breve, disiscrizione. L'email settimanale con i bandi è parte del servizio e non richiede consenso. | Bozza fatta: `consenso_email.md` · Tecnico (casella nella registrazione) |
| Campagne verso prospect | Niente email promozionali a indirizzi presi da elenchi o registri senza consenso (art. 130 Codice privacy, vale anche per le email aziendali e le PEC). Per i prospect: pubblicità (Google Ads), pagina pubblica, contatto su richiesta. | Bozza fatta (nota in `consenso_email.md` e nel registro) |
| Cookie banner | Banner con "Accetta" e "Rifiuta" ugualmente visibili, tag di Google Ads solo dopo il consenso, link per cambiare scelta. Già costruito nella pagina pubblica (`app/pubblico/__init__.py`). Due cose da sistemare: oggi "Rifiuta" ha uno stile più chiaro di "Accetta" (meglio due pulsanti con lo stesso peso, come chiedono le linee guida del Garante del 2021), e la scelta è salvata nel browser (`localStorage`, chiave `br_consenso`) senza scadenza: va data una durata (di norma 6 mesi) e indicata nella cookie policy al posto di `[NOME COOKIE SCELTA COOKIE]`. | Bozza fatta: `app/pubblico/testi/cookie.html` · Tecnico (verifica del banner) |
| Gestione delle violazioni dei dati (data breach) | Procedura breve: chi si accorge, come si valuta, notifica al Garante entro 72 ore se serve, registro delle violazioni anche quando non si notifica. | Da fare (bozza da scrivere) |
| Richieste degli interessati | Come si risponde entro un mese a richieste di accesso, cancellazione, portabilità (oggi: a mano dalla pagina Utenti/Imprese, export del profilo). | Da fare (procedura breve) · Tecnico (esportazione dei dati dell'utente) |
| Autorizzazione dei collaboratori | Chi lavora con i dati (revisori, collaboratori dello studio) va autorizzato per iscritto e istruito alla riservatezza (art. 29 GDPR, art. 2-quaterdecies Codice privacy). | Da fare (Matteo): modulo di autorizzazione |

## 6. Conservazione dei documenti

| Voce | Cosa serve | Stato |
|---|---|---|
| Fatture e scritture contabili | 10 anni (art. 2220 c.c.), conservazione a norma per le fatture elettroniche. | Da fare (Matteo) |
| Accettazione dei termini | Conservare per ogni cliente quale versione dei termini ha accettato, quando, e le due caselle (termini e clausole). Archiviare ogni versione pubblicata dei testi (il repository Git fa già da archivio storico). | Tecnico |
| Incarichi firmati e documenti delle pratiche | Per tutta la durata dell'incarico e poi per i termini di prescrizione (10 anni) e dell'antiriciclaggio (10 anni). | Da fare (Matteo) |
| Consensi alle email commerciali | Data, ora, testo mostrato e revoche, finché il consenso è valido e poi per il tempo utile a dimostrarlo. | Tecnico |

## 7. Ordine consigliato

1. Decidere chi vende (studio o società) e verificare la compatibilità con l'Ordine: blocca tutto il resto.
2. Riempire i dati del fornitore in tutti i testi e far rivedere termini, privacy, cookie, note legali e incarico (una revisione di poche ore).
3. Scegliere il servizio di fatturazione elettronica e aprire l'account Stripe vero.
4. Accettare e archiviare i DPA dei fornitori; completare il registro dei trattamenti.
5. Lavori tecnici: pagina `/note-legali`, seconda casella nel checkout con registrazione della versione, casella del consenso commerciale, campi di fatturazione, verifica del banner.
6. Solo allora `STRIPE_PAGAMENTI_VERI=1` e `ABBONAMENTI_ATTIVI=1`.

## File di questa cartella

- `README.md` — questo elenco.
- `registro_trattamenti.md` — registro delle attività di trattamento (art. 30 GDPR).
- `responsabili_dpa.md` — fornitori, accordi sul trattamento dei dati e cosa controllare.
- `incarico_supporto.md` — modello di lettera di incarico per il supporto a success fee.
- `consenso_email.md` — testi per il consenso alle comunicazioni commerciali e la disiscrizione.
