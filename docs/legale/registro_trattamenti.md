# Registro delle attività di trattamento — Bandi Radar

**Bozza del 05/10/2026, da far rivedere a un professionista.** Documento interno, non pubblicato. Registro tenuto dal titolare ai sensi dell'art. 30, paragrafo 1, del Regolamento (UE) 2016/679 (GDPR). Va aggiornato ogni volta che cambia un trattamento, un fornitore o una misura di sicurezza; in fondo c'è lo storico delle versioni.

## Dati generali

| Voce | Valore |
|---|---|
| Titolare del trattamento | [RAGIONE SOCIALE DEL TITOLARE], [SEDE], P.IVA [PARTITA IVA] |
| Contatti | [EMAIL DI CONTATTO] — PEC [PEC] |
| Rappresentante legale | [NOME E RUOLO DEL RAPPRESENTANTE LEGALE] |
| Responsabile della protezione dei dati (DPO) | Non nominato: non obbligatorio (nessun trattamento su larga scala di dati particolari né monitoraggio sistematico su larga scala). [CONFERMARE] |
| Servizio | Bandi Radar, `finanzagevolata.qiaro.it`: raccolta di bandi pubblici di finanza agevolata, schede, abbinamento al profilo dell'impresa, email settimanale; supporto alla domanda a success fee |
| Persone autorizzate | Matteo (amministratore); collaboratori dello studio e revisori con ruolo "revisore" (vedono catalogo e schede, non i dati dei clienti salvo permesso "imprese"). [ELENCO NOMINATIVO E DATA DELLE AUTORIZZAZIONI SCRITTE, TENUTO A PARTE] |

## Misure di sicurezza comuni a tutti i trattamenti

Sono le misure realmente in funzione al 05/10/2026 (art. 32 GDPR).

- **Server**: VPS OVH a Gravelines (Francia, UE), sistema aggiornato automaticamente, firewall, fail2ban contro i tentativi di intrusione.
- **Accesso ai server**: solo con chiave SSH, accesso con password disattivato; i segreti (chiavi API, password del database) stanno solo nel file `.env` del server, mai nel codice.
- **Connessione cifrata**: HTTPS con certificato gestito da Caddy.
- **Password degli utenti**: salvate solo come impronta con **scrypt** (algoritmo lento apposta), lunghezza minima 10 caratteri; nessuno può leggerle.
- **Sessioni**: al browser va un codice casuale in un cookie `HttpOnly`, `Secure` e `SameSite=Lax`; nel database c'è solo l'**impronta** (sha256) del codice, quindi chi leggesse il database non potrebbe entrare. Durata 30 giorni o fino all'uscita. Stesso meccanismo per i link via email (invito 7 giorni, recupero password 2 ore, conferma email 3 giorni, monouso).
- **Limite dei tentativi**: dopo 5 password sbagliate per lo stesso indirizzo, o 20 dallo stesso indirizzo IP, pausa di 15 minuti.
- **Ruoli e permessi**: admin, revisore (sola lettura sul catalogo), impresa (vede solo la propria area); permessi aggiuntivi assegnati uno per uno.
- **Separazione dei dati**: i dati che identificano il cliente (utente, email, nome dell'impresa) stanno in tabelle separate dal **profilo** usato per l'abbinamento, che ha solo un codice casuale e dati a fasce.
- **Intelligenza artificiale**: ai servizi di IA (Anthropic) arrivano **solo testi pubblici dei bandi**; mai dati dei clienti, dei profili o messaggi.
- **Backup**: copia giornaliera del disco fatta da OVH; in più ogni notte (3:30) copia del database in `/var/backups/bandi-radar` sullo stesso server, conservata 14 giorni. [VALUTARE UNA COPIA CIFRATA FUORI DAL SERVER]
- **Pagamenti**: i dati della carta li tratta solo Stripe; il sistema riceve gli aggiornamenti tramite webhook firmati.
- **Modifiche al sistema**: ogni modifica passa da una pull request su GitHub prima di andare in produzione (tracciabilità).

## Valutazione d'impatto (DPIA)

Valutazione del 05/10/2026: **non necessaria**. Motivi: non si trattano dati particolari né giudiziari; il profilo descrive l'impresa (sedi, ATECO, fasce) e non la persona, salvo indicazioni sì/no come "impresa femminile/giovanile"; l'abbinamento è un suggerimento senza effetti giuridici (art. 22 GDPR non applicabile); volumi piccoli; nessun incrocio con altre banche dati; nessuna sorveglianza. **Da rifare** se: arrivano le pratiche con i documenti dei clienti, l'IA riceve dati dei clienti, si usano archivi di prospect su larga scala. [CONFERMA DEL PROFESSIONISTA]

---

## T1. Account degli utenti

| Voce | Contenuto |
|---|---|
| Finalità | Creare e gestire l'accesso al servizio: registrazione o invito, conferma dell'email, accesso, recupero password, ruoli e permessi |
| Base giuridica | Esecuzione del contratto o di misure precontrattuali (art. 6.1.b) |
| Interessati | Clienti (titolari, dipendenti o collaboratori delle imprese e degli studi clienti); revisori e collaboratori |
| Categorie di dati | Email, nome (facoltativo), impronta della password, ruolo, data di creazione e ultimo accesso, data di conferma dell'email |
| Destinatari / responsabili | OVH (hosting); Resend (invio delle email di invito, conferma, recupero) |
| Trasferimenti extra UE | Resend (Stati Uniti): DPF o clausole contrattuali tipo [VERIFICARE] |
| Conservazione | Per la durata dell'account; cancellazione entro [GIORNI PER LA CANCELLAZIONE] giorni dalla chiusura; link via email scaduti cancellabili subito |
| Misure specifiche | scrypt, sessioni con impronta, limite tentativi, link monouso a scadenza |

## T2. Profili d'impresa e abbinamento ai bandi

| Voce | Contenuto |
|---|---|
| Finalità | Abbinare i bandi all'impresa e mostrarli nell'area "I miei bandi" |
| Base giuridica | Esecuzione del contratto (art. 6.1.b) |
| Interessati | Clienti; indirettamente le persone che guidano l'impresa (requisiti sì/no tipo "impresa femminile/giovanile"); ditte individuali e professionisti, per i quali i dati d'impresa sono dati personali |
| Categorie di dati | Nome o ragione sociale (tabella `imprese`); profilo anonimo con codice casuale (tabella `profili`): sedi (comune, provincia, regione), codici ATECO, forma giuridica, dimensione, fasce di dipendenti e fatturato, requisiti particolari sì/no |
| Destinatari / responsabili | OVH (hosting). **Nessun invio all'IA** |
| Trasferimenti extra UE | Nessuno |
| Conservazione | Per la durata dell'account; cancellazione entro [GIORNI PER LA CANCELLAZIONE] giorni dalla chiusura |
| Misure specifiche | Profilo separato dai dati identificativi; dati a fasce (minimizzazione); abbinamento con regole senza IA |

## T3. Abbonamenti e pagamenti

| Voce | Contenuto |
|---|---|
| Finalità | Gestire prova gratuita, abbonamento, addebiti ricorrenti, imprese e sedi in più, disdetta, solleciti |
| Base giuridica | Esecuzione del contratto (art. 6.1.b) |
| Interessati | Clienti paganti e in prova |
| Categorie di dati | Stato e formula dell'abbonamento, date di prova, fine periodo e fine impegno, identificativi cliente e abbonamento di Stripe, eventi ricevuti da Stripe; i dati della carta restano a Stripe (il sistema non li vede) |
| Destinatari / responsabili | Stripe (responsabile per l'elaborazione dei pagamenti per nostro conto; **titolare autonomo** per antifrode, antiriciclaggio e obblighi finanziari); OVH |
| Trasferimenti extra UE | Stripe (Stati Uniti): DPF e clausole contrattuali tipo [VERIFICARE] |
| Conservazione | Per la durata del rapporto e poi 10 anni per i dati con rilevanza contabile |
| Misure specifiche | Webhook firmati; chiavi di Stripe solo nel `.env`; pagamenti veri bloccati finché `STRIPE_PAGAMENTI_VERI` non è 1 |

## T4. Fatturazione

| Voce | Contenuto |
|---|---|
| Finalità | Emettere e conservare le fatture elettroniche, adempimenti fiscali e contabili |
| Base giuridica | Obbligo di legge (art. 6.1.c) ed esecuzione del contratto (art. 6.1.b) |
| Interessati | Clienti paganti (referenti, ditte individuali, professionisti) |
| Categorie di dati | Ragione sociale, partita IVA, codice fiscale, sede, codice destinatario o PEC, importi, date |
| Destinatari / responsabili | [SERVIZIO DI FATTURAZIONE ELETTRONICA] (responsabile); Agenzia delle Entrate tramite SdI (titolare autonomo); commercialista o consulente fiscale del titolare, se diverso; Stripe |
| Trasferimenti extra UE | [DIPENDE DAL SERVIZIO SCELTO] |
| Conservazione | 10 anni (art. 2220 c.c.), conservazione a norma |
| Misure specifiche | [DA DEFINIRE CON IL SERVIZIO SCELTO] |

## T5. Email settimanale con i bandi e comunicazioni di servizio

| Voce | Contenuto |
|---|---|
| Finalità | Inviare ogni settimana i bandi nuovi o in scadenza adatti all'impresa; avvisi di servizio (scadenza prova, pagamenti, modifiche ai termini) |
| Base giuridica | Esecuzione del contratto (art. 6.1.b): è una funzione del servizio, non pubblicità |
| Interessati | Clienti |
| Categorie di dati | Email, nome, nome dell'impresa, bandi segnalati (per non mandarli due volte), stato dell'invio, codice per la disiscrizione |
| Destinatari / responsabili | Resend (invio); OVH |
| Trasferimenti extra UE | Resend (Stati Uniti) [VERIFICARE GARANZIE] |
| Conservazione | Storico delle email inviate per la durata dell'account [O DURATA PIÙ BREVE DA DECIDERE] |
| Misure specifiche | Ogni email preparata viene approvata da Matteo prima dell'invio (fase di prova); link di disiscrizione senza accesso |

## T6. Richieste di supporto e pratiche

| Voce | Contenuto |
|---|---|
| Finalità | Ricevere le richieste "Richiedi supporto per la domanda", ricontattare l'impresa, valutare e svolgere l'incarico a success fee |
| Base giuridica | Misure precontrattuali su richiesta e contratto (art. 6.1.b); obblighi di legge per l'antiriciclaggio e la parte fiscale (art. 6.1.c) |
| Interessati | Clienti; legali rappresentanti e titolari effettivi delle imprese (per l'antiriciclaggio) |
| Categorie di dati | In Bandi Radar: impresa, bando, messaggio libero, stato, appunti di Matteo. Fuori da Bandi Radar (gestionale dello studio): documenti per la domanda, documenti d'identità, dati per l'adeguata verifica |
| Destinatari / responsabili | OVH; Resend (avviso a Matteo); enti che gestiscono i bandi (titolari autonomi) quando si invia la domanda; collaboratori autorizzati |
| Trasferimenti extra UE | Resend per l'avviso [VERIFICARE] |
| Conservazione | Richieste non diventate incarico: [DURATA DI CONSERVAZIONE RICHIESTE]. Incarichi: 10 anni dalla fine (prescrizione e antiriciclaggio) |
| Misure specifiche | Visibili solo ad admin e a chi ha il permesso "imprese"; nessun invio all'IA. I documenti delle pratiche oggi non passano da Bandi Radar: se cambierà (vedi `docs/PIANO_PRATICHE.md`), aggiornare questa scheda e rifare la valutazione d'impatto |

## T7. Giudizi e segnalazioni sulle schede (feedback)

| Voce | Contenuto |
|---|---|
| Finalità | Correggere e migliorare le schede in base a voti e segnalazioni |
| Base giuridica | Legittimo interesse a migliorare la qualità del servizio (art. 6.1.f) |
| Interessati | Clienti, revisori |
| Categorie di dati | Utente, voto 1-5, categoria del problema, testo libero, risposta dell'admin |
| Destinatari / responsabili | OVH. Agli agenti di IA che correggono le schede vanno il bando e il contenuto della segnalazione **senza** nome, email o identificativo di chi l'ha scritta (`strumenti/sessione/ar/esporta_feedback.py` li esclude); resta il rischio che qualcuno scriva dati personali nel testo libero |
| Trasferimenti extra UE | Anthropic (Stati Uniti) solo per il contenuto della segnalazione senza identificativi |
| Conservazione | Durata dell'account; dopo la chiusura in forma anonima |
| Misure specifiche | Un giudizio per persona e versione della scheda |

## T8. Sicurezza e registri di accesso

| Voce | Contenuto |
|---|---|
| Finalità | Proteggere il servizio da accessi abusivi e attacchi, ricostruire incidenti |
| Base giuridica | Legittimo interesse alla sicurezza (art. 6.1.f) |
| Interessati | Chiunque visiti o tenti di accedere al servizio |
| Categorie di dati | Indirizzo IP, data e ora, email usata nel tentativo di accesso, esito; registri tecnici del server web e di fail2ban |
| Destinatari / responsabili | OVH |
| Trasferimenti extra UE | Nessuno |
| Conservazione | Tentativi di accesso: 30 giorni. Altri registri tecnici: [DURATA DI CONSERVAZIONE LOG] |
| Misure specifiche | Accesso ai registri solo con chiave SSH |

## T9. Cookie di misurazione (Google Ads)

| Voce | Contenuto |
|---|---|
| Finalità | Misurare se le campagne pubblicitarie portano registrazioni (conversioni) |
| Base giuridica | Consenso (art. 6.1.a e art. 122 Codice privacy), raccolto con il banner; revocabile |
| Interessati | Visitatori della pagina pubblica che accettano |
| Categorie di dati | Identificativi dei cookie, dati di navigazione e di conversione |
| Destinatari / responsabili | Google Ireland Ltd. e Google LLC (in parte titolare autonomo, in parte responsabile secondo i termini di Google Ads) |
| Trasferimenti extra UE | Google LLC (Stati Uniti): DPF [VERIFICARE] |
| Conservazione | Consenso: [DURATA DEL CONSENSO]. Cookie di Google: [DURATA COOKIE GOOGLE ADS] |
| Misure specifiche | Tag caricato solo dopo "Accetta" (Consent Mode parte negato); se non c'è `GOOGLE_ADS_ID` il tag non esiste |

## T10. Campagne commerciali verso prospect (eventuale, non attivo)

| Voce | Contenuto |
|---|---|
| Finalità | Far conoscere Bandi Radar a imprese che non sono clienti |
| Base giuridica | **Consenso** (art. 6.1.a e art. 130 Codice privacy) per email, SMS, telefonate automatiche e PEC promozionali, anche verso indirizzi aziendali. Per i clienti già acquisiti: email su servizi analoghi senza consenso preventivo ma con diritto di opposizione in ogni messaggio (art. 130, comma 4, "soft spam") |
| Interessati | Prospect (imprese e loro referenti); clienti |
| Categorie di dati | Email e nome di chi si è iscritto con consenso; per l'archivio anagrafiche (`docs/ricerche/2026-09-25_schema_anagrafiche_leadgen.md`): dati d'impresa da registri pubblici |
| Destinatari / responsabili | Resend o altro servizio di invio [DA DEFINIRE] |
| Trasferimenti extra UE | [DA DEFINIRE] |
| Conservazione | Fino alla revoca del consenso; prova del consenso conservata per il tempo necessario a dimostrarlo |
| Misure specifiche | Nessuna email promozionale a indirizzi presi da elenchi o registri senza consenso; casella dedicata non preselezionata (vedi `consenso_email.md`). L'uso dell'archivio anagrafiche per statistiche o per scegliere dove fare pubblicità non richiede contatti diretti; ogni uso per contattare le imprese va valutato prima con il professionista |

---

## Storico delle versioni

| Data | Cosa cambia |
|---|---|
| 05/10/2026 | Prima bozza |
