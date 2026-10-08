# Fornitori e accordi sul trattamento dei dati (DPA)

**Bozza del 05/10/2026, da far rivedere a un professionista.** Documento interno, non pubblicato.

Ogni fornitore che tratta dati personali per conto nostro è un **responsabile del trattamento** (art. 28 GDPR) e serve un accordo scritto (DPA, *Data Processing Agreement*). I grandi fornitori non firmano accordi su misura: il DPA è un documento standard che si accetta con il contratto o dal pannello dell'account. Il nostro compito è: accettarlo, **scaricarne una copia datata** e archiviarla, controllare le garanzie per i trasferimenti fuori UE, e tenere aggiornato l'elenco qui sotto e nell'informativa privacy.

Dove archiviare le copie: [CARTELLA DELLO STUDIO PER I DOCUMENTI PRIVACY] (non nel repository).

## Cosa controllare per ogni fornitore

1. **DPA accettato**: data e versione; copia in PDF archiviata.
2. **Ruolo**: responsabile (tratta per noi) o titolare autonomo (decide lui per alcune finalità, come Stripe per l'antifrode).
3. **Sub-responsabili**: elenco pubblicato dal fornitore e modo in cui avvisa dei cambiamenti (iscriversi agli avvisi, se possibile).
4. **Trasferimenti fuori UE**: se i dati vanno negli Stati Uniti, verificare sul sito ufficiale `dataprivacyframework.gov` che il fornitore sia **certificato EU-US Data Privacy Framework (DPF)** e che la certificazione sia attiva; in alternativa o in aggiunta, che il DPA contenga le **clausole contrattuali tipo (SCC)** della Commissione europea (decisione 2021/914, modulo 2: titolare-responsabile).
5. **Sicurezza**: certificazioni dichiarate (per esempio ISO 27001, SOC 2) e regione in cui sono i dati.
6. **Cancellazione a fine rapporto**: cosa succede ai dati se chiudiamo l'account.

## Elenco

| Fornitore | Cosa fa per bandinQiaro | Dati personali | Ruolo | Dove si accetta il DPA | Trasferimenti extra UE | Stato |
|---|---|---|---|---|---|---|
| **OVH SAS** (Roubaix, Francia) | Server VPS a Gravelines: applicazione, database, backup | Tutti i dati del servizio | Responsabile | Il DPA è un allegato delle condizioni contrattuali di OVHcloud, accettato con l'ordine; si scarica dallo spazio clienti (sezione contratti) | No: dati in Francia. Verificare nel DPA i sub-responsabili ed eventuali accessi da fuori UE per assistenza | Da archiviare la copia |
| **Resend** (Stati Uniti) | Invio delle email: inviti, conferme, recupero password, email settimanale, avvisi di supporto | Email, nome, nome dell'impresa, contenuto delle email | Responsabile | DPA pubblicato sul sito di Resend (pagina legale), da accettare/firmare secondo le loro istruzioni; verificare se è possibile scegliere una regione UE per l'invio | Sì: verificare DPF e SCC nel DPA | Da fare (prima di attivare l'invio ai clienti) |
| **Stripe Payments Europe Ltd.** (Irlanda) e Stripe, Inc. (Stati Uniti) | Pagamenti con carta, abbonamenti, portale clienti | Email, nome, dati di fatturazione, dati della carta (solo Stripe) | In parte **responsabile** (elaborazione dei pagamenti per nostro conto), in parte **titolare autonomo** (antifrode, antiriciclaggio, obblighi finanziari) | Il DPA di Stripe è incorporato nello Stripe Services Agreement, accettato all'apertura dell'account | Sì: verificare DPF di Stripe, Inc. e SCC nel DPA | Da fare (all'apertura dell'account vero) |
| **Anthropic** (Stati Uniti; per l'UE Anthropic Ireland) | Intelligenza artificiale per smistamento, controlli preliminari e schede, lavorando **solo sui testi pubblici dei bandi** | Di norma **nessun dato dei clienti**. Possibili eccezioni: nomi di referenti che compaiono nei bandi pubblici; testo libero delle segnalazioni sulle schede (senza identificativi di chi le scrive) | Responsabile per le eventuali informazioni personali contenute nei testi inviati | Le condizioni commerciali dell'API (Commercial Terms) incorporano il DPA di Anthropic; verificare la versione in vigore e scaricarla dalla console | Sì: verificare DPF e SCC nel DPA. Verificare che i dati inviati via API non siano usati per addestrare i modelli (previsto dalle condizioni commerciali) | Da archiviare la copia. Nota: le sessioni di lavoro con l'abbonamento Claude non devono ricevere dati dei clienti |
| **Google Ireland Ltd.** / Google LLC (Google Ads) | Misurazione delle conversioni delle campagne, solo con il consenso ai cookie | Identificativi dei cookie, dati di navigazione e conversione | Per la misurazione delle conversioni Google opera in parte come titolare autonomo e in parte come responsabile, secondo i suoi termini | Nell'account Google Ads: accettare i *Google Ads Data Processing Terms* e, per le parti da titolare, i *Google Ads Controller-Controller Data Protection Terms*. Rispettare la *Norma relativa al consenso degli utenti dell'UE* di Google (Consent Mode attivo) | Sì: verificare DPF di Google LLC | Da fare (quando si crea l'account Ads) |
| **[SERVIZIO DI FATTURAZIONE ELETTRONICA]** (da scegliere) | Emissione delle fatture elettroniche collegate a Stripe, invio allo SdI, eventuale conservazione a norma | Ragione sociale, P.IVA, codice fiscale, sede, codice destinatario/PEC, importi | Responsabile | Da verificare al momento della scelta | Preferire un fornitore con dati in UE | Da scegliere |
| **GitHub** (Microsoft, Stati Uniti) | Repository del codice | Nessun dato dei clienti (regola: niente dati e segreti nel repository) | — | Non serve finché il repository non contiene dati personali | — | Da tenere così |

Altri destinatari che **non** sono responsabili: Agenzia delle Entrate (SdI) e gli enti che gestiscono i bandi sono titolari autonomi; il commercialista o consulente fiscale del titolare, se esterno, va nominato responsabile con la sua lettera di incarico.

## Quando aggiornare questo elenco

- Si aggiunge un fornitore che vede dati dei clienti (anche solo per assistenza).
- Un fornitore cambia DPA, sub-responsabili o perde la certificazione DPF.
- Si attivano le pratiche con documenti dei clienti (`docs/PIANO_PRATICHE.md`) o si decide di far leggere all'IA dati dei clienti: in quel caso Anthropic diventa un responsabile a pieno titolo e va rifatta la valutazione d'impatto.

Ogni modifica va riportata anche nella tabella "Chi riceve i dati" dell'informativa (`app/pubblico/testi/privacy.html`) e nel registro (`registro_trattamenti.md`).
