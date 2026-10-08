# Testi legali della pagina pubblica

Frammenti HTML (solo contenuto, senza stili né script) che la pagina pubblica di bandinQiaro inserisce nel proprio modello:

- `termini.html` — Termini e condizioni del servizio in abbonamento (rivolto a imprese e professionisti), con la sezione 16 "Approvazione specifica delle clausole" (artt. 1341-1342 c.c.).
- `privacy.html` — Informativa privacy (artt. 13-14 GDPR).
- `cookie.html` — Cookie policy; contiene il link `id="rivedi-cookie"` che la pagina deve collegare al banner dei cookie.
- `supporto.html` — Condizioni del servizio di supporto per la domanda a success fee.
- `chi_siamo.html` — Sezione "Chi c'è dietro" della landing (07/10/2026): bozza con segnaposto (nome, Albo, città, anni), da confermare con Matteo prima di accendere la pagina.
- `note_legali.html` — Note legali: dati obbligatori del fornitore (art. 7 d.lgs. 70/2003, art. 2250 c.c.). **Non ancora collegata**: va aggiunta a `LEGALI` in `app/pubblico/__init__.py` con l'indirizzo `/note-legali` e un link nel piede della pagina (i termini la richiamano già).

**Sono bozze del 05/10/2026**: vanno fatte rivedere da un professionista (avvocato o consulente privacy) prima di usarle con clienti reali. Ogni file ha in cima il riquadro `<p class="bozza">`, da togliere solo dopo la revisione.

I documenti interni (registro dei trattamenti, fornitori e DPA, modello di incarico, testi del consenso alle email, elenco di tutto ciò che serve per vendere) sono in `docs/legale/`, non pubblicati.

## Decisioni già riportate nei testi (05/10/2026)

Prezzi **IVA esclusa** (IVA aggiunta in fattura): mensile 30 €/mese; annuale 20 €/mese pagato ogni mese con impegno di 12 mesi (rate residue dovute in caso di interruzione anticipata); impresa in più 10 €/mese; sede in più della stessa impresa 5 €/mese. Servizio per imprese e professionisti (B2B, partita IVA richiesta per abbonarsi). Fattura elettronica tramite un servizio collegato a Stripe. Prova gratuita senza carta e senza addebito automatico alla fine (è come funziona il sistema; da confermare).

Success fee del supporto alla domanda (decisione di Matteo del 05/10/2026, IVA esclusa, in `supporto.html` e nel modello di incarico; ricerca in `docs/ricerche/2026-10-05_success_fee_concorrenti.md`): calcolo sul contributo concesso con conguaglio sull'erogato; fondo perduto a scaglioni 12% fino a 50.000 €, 10% da 50.000 a 150.000 €, 8% oltre; finanziamento agevolato 2% / 1,5% / 1% (soglie da confermare); credito d'imposta 6% man mano che è usato in F24; minimo 500 € a pratica accolta; quota d'avvio 250 € scalata dalla success fee (unico compenso se la domanda è respinta); pagamento 50% (almeno il minimo) entro 30 giorni dalla concessione e il resto entro 15 giorni da ogni erogazione; rinuncia prima dell'invio = quota d'avvio, dopo la concessione = 50% della success fee; revoca per causa dell'impresa = resta il maturato, per errore dello studio = restituzione; rendicontazione e varianti a forfait 400-600 € (da confermare); la success fee non è spesa ammissibile.

## Segnaposto da riempire (tra parentesi quadre nei testi)

Dati del titolare (tutti i file): `[RAGIONE SOCIALE DEL TITOLARE]`, `[PARTITA IVA]`, `[SEDE]`, `[EMAIL DI CONTATTO]`, `[PEC]`, `[DATA DI ENTRATA IN VIGORE]`.

Note legali: `[FORMA GIURIDICA ...]`, `[CODICE FISCALE]`, ufficio del Registro delle imprese e `[NUMERO REA]`, `[CAPITALE SOCIALE]` (solo società di capitali), righe "unico socio" e "in liquidazione" da tenere o togliere, `[TELEFONO ...]`, iscrizione all'Ordine (solo se il fornitore è un professionista o una STP), eventuale codice di condotta.

Termini: `[SERVIZIO DI FATTURAZIONE ELETTRONICA]`, `[GIORNI DI PREAVVISO]` (modifiche di prezzi e termini, disdetta dell'annuale), `[DURATA PROVA GRATUITA]` e conferma del funzionamento della prova, cosa succede alla scadenza dei 12 mesi dell'annuale (`[SI RINNOVA PER ALTRI 12 MESI / PASSA ALLA FORMULA MENSILE / CONTINUA A 20 € AL MESE SENZA IMPEGNO ...]`: oggi il sistema fa la terza), `[FORO COMPETENTE]`. La nota tecnica tra parentesi quadre in fondo alla sezione 16 va tolta dalla versione pubblica: ricorda che nel checkout serve una **seconda casella**, separata e non preselezionata, per l'approvazione specifica delle clausole, con registrazione di data, ora e versione dei termini.

Privacy: eventuale DPO (`[DATI DI CONTATTO DEL DPO]`, altrimenti togliere il paragrafo), `[GIORNI PER LA CANCELLAZIONE]`, `[DURATA DI CONSERVAZIONE RICHIESTE]`, `[DURATA DI CONSERVAZIONE LOG]`, `[DURATA DEL CONSENSO]`, verifica dell'adesione dei fornitori al Data Privacy Framework. Quando sarà scelto, aggiungere il servizio di fatturazione elettronica alla tabella dei fornitori.

Cookie: `[NOME COOKIE SCELTA COOKIE]` (oggi la scelta è salvata nel `localStorage` del browser con chiave `br_consenso`, senza scadenza), `[DURATA DEL CONSENSO]`, `[DURATA COOKIE GOOGLE ADS]`.

Supporto: `[CONTRIBUTO PREVIDENZIALE INTEGRATIVO DEL 4%, SE DOVUTO]`, `[SOGLIE DA CONFERMARE]` degli scaglioni del finanziamento agevolato (200.000 € e 1.000.000 €, proposte da Claude), `[IMPORTO DA CONFERMARE]` del forfait di rendicontazione (400-600 €), limiti di responsabilità e assicurazione professionale. Nel modello di incarico `docs/legale/incarico_supporto.md` restano anche: compenso per garanzie e altre forme, eventuale tetto massimo, cadenza del compenso sul credito d'imposta, giorni per comunicare esito ed erogazioni, polizza, foro.

I link interni usano `/privacy`, `/cookie`, `/termini`, `/condizioni-supporto` e `/note-legali`: adeguarli se le pagine avranno indirizzi diversi.
