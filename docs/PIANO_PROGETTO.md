# Bandi Radar — Piano di progetto v1

*Bozza del 23/09/2026, rivista lo stesso giorno con le prime decisioni di Matteo (vedi §10).*

---

## 1. Obiettivo

Trovare in automatico **tutti i bandi aperti** (UE, nazionali, regionali, camerali, altri enti), trasformarli in **schede ordinate** (chi può partecipare, cosa si finanzia, quanto, entro quando) e **abbinarli ai clienti di Contract to Cash**. Ai clienti arriva una proposta via email e possono consultare tutto da un cruscotto.

Requisiti di Matteo:
- **Non si scartano** regioni ed enti locali. Per i Comuni si coprono i **capoluoghi di provincia** (vedi §3).
- **Plancia di controllo** per vedere lo stato di ogni fonte, rilanciare le automazioni e accorgersi delle fonti "mute" da troppo tempo (possibile guasto).
- **Cruscotto** consultabile anche dai clienti.
- **Match automatici** con notifica ed email.
- Deve reggere la crescita da 0 a molti clienti senza che i costi esplodano (obiettivo: 100 clienti entro 6 mesi).
- Deve **funzionare da solo ed essere facilmente trasferibile**: il codice di Contract to Cash e l'hosting sono in mano a Sergio, quindi Bandi Radar nasce come sistema autonomo (Docker Compose, un file di configurazione, un comando per avviarlo) e il collegamento a C2C si fa più avanti.

---

## 2. Come è fatto il sistema (6 moduli)

```
 FONTI (~95)                       BANDI RADAR (nuovo, in Docker)                        CONTRACT TO CASH
 ─────────────                     ────────────────────────────────────────              ─────────────────
 incentivi.gov.it (dati aperti) ─┐
 Portale UE (API)               ─┤  1. RACCOLTA ──► 2. SCHEDE ──► 3. ABBINAMENTO ◄──── profili ANONIMI
 Lombardia (dati aperti)        ─┤     (script,       (IA legge      (regole, niente      dei clienti
 21 Regioni/Prov. autonome      ─┤      niente IA)     PDF, estrae    IA)
 ~60 Camere di Commercio        ─┤          │          requisiti)         │
 MIMIT/Invitalia/GSE/SIMEST     ─┘          ▼                             ▼
                                    4. PLANCIA DI CONTROLLO        5. API ───────────►  6. CRUSCOTTO CLIENTI
                                       (solo Matteo)                                    + EMAIL DI PROPOSTA
```

| # | Modulo | Cosa fa | Tecnologia proposta |
|---|---|---|---|
| 1 | **Raccolta** | Visita le fonti con la frequenza giusta, scarica le novità e salva tutto in archivio | Python (le librerie migliori per siti e PDF) |
| 2 | **Schede** | Legge bando e allegati e compila una scheda standard; riconosce i doppioni (lo stesso bando su incentivi.gov.it e sul sito regionale) e gli aggiornamenti (proroghe, chiusure anticipate) | Claude via API (Haiku per smistare, Sonnet per le schede) |
| 3 | **Abbinamento** | Confronta ogni scheda con ogni profilo cliente e assegna un punteggio con la motivazione | Regole automatiche; IA solo per scrivere la spiegazione |
| 4 | **Plancia di controllo** | Salute delle fonti, allarmi, rilanci, costi | Piccola app web React (stessa tecnologia di C2C) |
| 5 | **API** | Il "rubinetto" da cui Contract to Cash prende bandi e match | REST, chiamata dal backend Java di C2C |
| 6 | **Cruscotto clienti + email** | Pagine per i clienti e invio delle proposte. Nascono dentro Bandi Radar, da incorporare in C2C più avanti | React + servizio email transazionale (Resend, vedi §7) |

**Scelta chiave: Bandi Radar non conosce i clienti per nome.** Riceve solo profili anonimi (codice interno, ATECO, provincia, comune, dimensione, fatturato a fasce, export sì/no…). Nomi, email e invii restano nel sistema che gestisce i clienti. È più sicuro per la privacy e più semplice da difendere con i clienti.

**Da dove arrivano i profili, oggi e domani.** Il codice di Contract to Cash non è accessibile (lo gestisce Sergio), quindi il collegamento a C2C si rinvia. Nella prima versione i profili anonimi si generano dalle **anagrafiche che Matteo ha nel suo Postgres in Docker**: un piccolo script legge quelle tabelle e produce i profili nel formato standard di Bandi Radar. Quando C2C sarà collegato, farà la stessa cosa attraverso l'API (modulo 5): il formato del profilo è lo stesso, cambia solo chi lo manda. Per lo stesso motivo il **cruscotto clienti e l'invio delle email (modulo 6) nascono dentro Bandi Radar**, con un accesso per cliente, e verranno incorporati in C2C quando sarà possibile.

**Come teniamo tutte le regioni e le Camere senza 80 programmi diversi:** non si scrive uno script per ogni sito. C'è **un solo "osservatore di pagine" generico**: per ogni fonte basta una riga di configurazione (indirizzo della pagina elenco, eventuale feed RSS). L'osservatore confronta la pagina con quella della volta prima e **manda all'IA solo la parte cambiata**. Aggiungere una fonte significa aggiungere una riga, non scrivere codice. Quando un sito cambia aspetto, di solito si aggiorna quella riga.

---

## 3. Fonti e frequenza di controllo

> Le frequenze di pubblicazione qui sotto sono **stime iniziali**. Non ho potuto misurarle perché i siti delle fonti sono bloccati dalla rete di questa sessione. La **Fase 1 le misura davvero** per 4 settimane (il sistema registra ogni nuovo bando con la sua data) e a fine Fase 2 si tarano le frequenze sui dati reali.
> Ogni controllo di una pagina costa praticamente zero, perché l'IA interviene solo se qualcosa è cambiato. La frequenza serve quindi a **essere tempestivi** senza **disturbare** i siti pubblici, non a risparmiare.

| Gruppo | N. fonti | Pubblicazione stimata | Controllo proposto | Metodo |
|---|---|---|---|---|
| incentivi.gov.it (dati aperti) | 1 | aggiornamento continuo | ogni giorno | download CSV/JSON |
| Portale UE Funding & Tenders | 1 | a ondate (programmi di lavoro), più volte al mese | ogni giorno | API ufficiale |
| Lombardia: Anagrafica dei bandi regionali (open data, tutti i bandi con apertura e chiusura) + schede su Bandi Online | 1 | più bandi a settimana; 122 aperti al 23/09/2026 | ogni giorno | API Socrata + osservatore |
| **FVG** | 1 | più avvisi a settimana (di cui molti non per imprese) | ogni giorno | osservatore (+ RSS se c'è) |
| Regioni grandi (Veneto, Emilia-R., Piemonte, Lazio, Campania, Puglia, Sicilia, Toscana) | 8 | più avvisi a settimana | ogni giorno | osservatore |
| Altre Regioni e Province autonome | 11 | 1–5 a settimana | 3 volte a settimana | osservatore |
| MIMIT, Invitalia, GSE, SIMEST | 4 | poche misure nuove al mese, ma aperture di sportello e modifiche frequenti | 3 volte a settimana | osservatore |
| **CCIAA Milano-MB-Lodi e Pordenone-Udine** | 2 | 1–4 bandi al mese, concentrati a inizio anno | ogni giorno | osservatore |
| Altre Camere di Commercio | ~58 | 1–4 bandi al mese, concentrati a inizio anno | 1 volta a settimana (2 volte tra gennaio e aprile) | osservatore |
| Comuni capoluogo di provincia | ~80 | 1–5 bandi all'anno ciascuno, per commercio e centro storico | 1 volta a settimana | osservatore |
| Province con bandi propri (eccezioni) | ~7 | poche misure all'anno | 1 volta a settimana | osservatore |
| Fondazioni bancarie (selezione) | ~5 | poche finestre all'anno | 1 volta a settimana | osservatore |
| **Totale** | **~180** | | | |

**Province e Comuni.** Una mappatura del 23/09/2026 (`docs/ricerche/2026-09-23_province_capoluoghi.md`, fatta con la sola ricerca web, quindi da verificare sui siti) dice questo:
- **Le Province non sono una fonte**: pubblicano appalti e concorsi, non finanza agevolata. Le eccezioni entrano nel registro una per una: Province autonome di Trento e Bolzano, Belluno, Treviso, Città metropolitane di Bologna, Milano e Torino. In FVG le Province non esistono più e gli EDR che le hanno sostituite non fanno bandi per imprese.
- **I Comuni capoluogo sì**: circa due terzi pubblicano bandi propri per imprese (commercio di vicinato, centro storico, locali sfitti, nuove aperture, start-up), con Nord più attivo del Sud. I 4 capoluoghi del FVG (Udine, Pordenone, Trieste, Gorizia) sono tra i più attivi d'Italia. Entrano tutti nel registro (~80 fonti, controllo settimanale), con priorità FVG e Lombardia.
- **I Comuni non capoluogo restano fuori**: chi eroga è quasi sempre Regione, Camera di Commercio o capoluogo. Resta possibile, su richiesta, aggiungere il Comune della sede di un cliente come fonte dedicata.
- Una seconda tornata con lettura diretta dei siti (`docs/ricerche/2026-09-23_province_capoluoghi_parte2.md`) ha completato le aree mancanti e confermato: Province fuori; tra i capoluoghi, quelli con bandi ricorrenti e pagina verificata sono una decina (Roma, Pesaro, La Spezia, Udine, Brescia, Bergamo, Pordenone, Sondrio, Ragusa, Messina, Taranto), gli altri hanno elenchi misti con bandi per imprese rari e vanno controllati con frequenza minore. Nessun Comune ha una pagina "solo imprese": l'osservatore deve leggere elenchi misti e filtrare.
- Lezione tecnica: molti siti pubblici rifiutano le connessioni da server o caricano gli elenchi con JavaScript. L'osservatore deve prevedere tre modalità (HTML, RSS, API JSON) e un browser senza interfaccia, e le famiglie di piattaforma ricorrenti (Municipium, WordPress Design Comuni, Drupal, Plone) permettono di scrivere un lettore per famiglia invece che per sito.

**Open data**: una verifica del 23/09 (`docs/ricerche/2026-09-23_open_data_comuni.md`, due passate, la seconda con 34 sinonimi) mostra che i portali open data dei Comuni non contengono i bandi aperti, ma solo gare e sovvenzioni già concesse. Le Regioni invece hanno alcune fonti strutturate preziose: **l'Anagrafica dei bandi regionali della Lombardia** (tutti i bandi dal 2015 con apertura e chiusura, API, aggiornata ogni mese), Regione Basilicata (elenco avvisi e bandi in JSON con scadenza e destinatari, da verificare dal server), i calendari FESR/FSE+/FEASR della Provincia di Trento e il calendario avvisi 2021-27 della Calabria. Quest'ultimo è un **obbligo europeo per tutte le Regioni** (art. 49 Reg. UE 2021/1060): i calendari vanno cercati per tutte e 21, in qualunque formato, perché anticipano di mesi le aperture. Il catalogo nazionale dati.gov.it si osserva una volta al mese, con l'intera lista di sinonimi. Per la Fase 7: gli open data mensili del Registro Nazionale Aiuti (de minimis) e i feed dei GAL (bandi rurali). I dati di contesto (perimetri dei Distretti del Commercio di Milano, aree ammissibili Emilia-Romagna, elenchi beneficiari) entrano in una categoria a parte del registro, per il matching e per il de minimis.

**Fonti escluse dalla raccolta**: TED (sono appalti), OpenCoesione (storico), aggregatori privati (i loro elenchi hanno diritti sulla banca dati; possono servire solo per un controllo manuale).
**RNA** non serve a trovare bandi: entra in Fase 7 per il controllo del *de minimis* dei clienti.

---

## 3b. Stato del registro delle fonti (al 23/09/2026)

Circa 180 voci, dopo le mappature in `docs/ricerche/`. Divise per modo di lettura:

| Tipo | Quante | Quali | Costo di ogni controllo |
|---|---|---|---|
| **API o dati strutturati** | 8 (3 verificate) | Lombardia Anagrafica bandi (verificata), Trento calendari FESR/FSE+/FEASR (verificata), Portale UE (API ufficiale), incentivi.gov.it dati aperti, Basilicata avvisi JSON, Calabria calendario avvisi, Registro Nazionale Aiuti (Fase 7), catalogo dati.gov.it (per scoprire fonti nuove) | zero token: sono dati già strutturati |
| **Feed RSS o API del CMS** | ~10 verificate | Sondrio, Pavia, Taranto, Ragusa, Messina (feed); Pordenone, La Spezia (API JSON Plone); tutti i Comuni su Municipium (`/it/feeds`) | zero token per il controllo; IA solo sui titoli nuovi da smistare |
| **Pagine HTML con osservatore** | ~160 | 20 Regioni, ~60 Camere di Commercio, ~70 capoluoghi, 7 Province eccezione, 4 enti nazionali, fondazioni | zero token per il controllo; IA solo sul frammento cambiato |
| **Difficili** | ~15 | 8 con elenchi caricati via JavaScript (Trieste, Gorizia, Cagliari, Sassari, Oristano, Varese, Barletta, Provincia di Potenza): browser senza interfaccia. 7 che rifiutano connessioni da server (Milano, incentivi.gov.it, Lecce, Potenza, Frosinone, Rieti, Viterbo): da riprovare dal PC di Matteo o dal VPS | come sopra, più tempo macchina |

**L'osservatore non consuma token.** Scaricare una pagina e confrontarla con la versione precedente è un lavoro da script. L'IA entra solo in due momenti: quando un frammento è cambiato (smistamento con Haiku, pochi centesimi) e quando un bando nuovo va trasformato in scheda (Sonnet, qualche decina di centesimi con i PDF). **La frequenza dei controlli quindi non incide sul costo IA**: i bandi nuovi da leggere sono gli stessi, che li si scopra il giorno dopo o due settimane dopo. Incide solo sulla tempestività, e molti bandi restano aperti poche settimane (in Lombardia, "Fondo giovani agricoltori 2026" apre il 13/10 e chiude il 27/10). Per questo le frequenze restano quelle di §3; controllare ogni 10–15 giorni farebbe risparmiare solo banda, che costa nulla.

**Quando rifare le mappature manuali** (sessioni di Claude Code con agenti, come quelle del 23/09):
1. **Appena il VPS è attivo**: un'ora per testare i 15 siti difficili e i 4 open data non raggiungibili dalla sessione cloud.
2. **A fine Fase 0**: verifica automatica di tutti i 180 indirizzi (la fa il sistema, non l'IA).
3. **Ogni sei mesi**, a gennaio (bandi annuali delle Camere) e a luglio: rimappatura con gli agenti per fonti nuove e siti rifatti.
4. **Quando la plancia lo chiede**: se in un mese più del 10% delle fonti segnala "struttura cambiata" o "silenzio sospetto".

---

## 4. Stima dei costi (mensile, a regime)

Ipotesi: 150–300 novità a settimana raccolte da tutte le fonti, di cui 60–120 rilevanti per le imprese e quindi da trasformare in scheda.

**Costi IA (API Claude, prezzi attuali):**

| Voce | Calcolo | €/mese |
|---|---|---|
| Lettura delle pagine cambiate (Haiku) | ~1 milione di parole-token a settimana | ~5 |
| Smistamento delle novità (Haiku) | ~250 a settimana | ~5 |
| Schede complete da PDF (Sonnet, elaborazione "in blocco" a metà prezzo) | ~90 a settimana, più aggiornamenti e proroghe | 20–30 |
| Controllo settimanale anomalie e fonti difficili | 1 esecuzione a settimana | 3–5 |
| Spiegazioni dei match | ~0,05 € per cliente al mese | cresce con i clienti |

**Scenari totali (IA + server + email):**

| Clienti | IA | Server, backup, email | **Totale al mese** |
|---|---|---|---|
| 0–10 (avvio) | 35–50 € | 10–25 € | **45–75 €** |
| 100 | 40–55 € | 15–30 € | **55–85 €** |
| 500 | 55–80 € | 35–50 € | **90–130 €** |
| 2.000 | 110–180 € | 50–80 € | **160–260 €** |

La parte grossa del costo è **fissa** (leggere i bandi). Ogni bando si legge una volta, qualunque sia il numero di clienti, e un cliente in più costa pochi centesimi. Più clienti ci sono, più il servizio si ripaga.

**Costo di sviluppo:** le sessioni di lavoro con me in Claude Code rientrano nel tuo abbonamento, non si pagano a token. Nelle settimane di sviluppo intenso potresti arrivare ai limiti del piano: in quel caso si valuta un piano superiore solo per quel periodo.

**Abbonamento e API sono due cose diverse.** L'abbonamento copre il lavoro interattivo (Claude Code, chat). Il sistema in produzione, che legge i bandi da solo di notte, deve chiamare l'API di Anthropic, che si paga a consumo e richiede un account separato (Console Anthropic) con carta e un tetto di spesa mensile. Le condizioni d'uso non permettono di usare le credenziali dell'abbonamento dentro un'applicazione propria. Per contenere la spesa iniziale:
- **Fasi 0, 1 e 2 non usano l'IA**: raccolta, archivio e plancia funzionano con soli script. L'account API serve dalla **Fase 3** (schede).
- Durante lo sviluppo, le prove sulle schede si fanno **nelle sessioni di Claude Code**, quindi dentro l'abbonamento. L'API entra solo quando il flusso è automatico.
- Si parte con un tetto basso (es. 30 € al mese) che si alza quando le schede sono a regime. Con i volumi stimati sopra, i primi mesi costano 20–50 € al mese.

**Server:** OVH VPS-2 con Ubuntu 24.04 in Francia, 8,80 €/mese IVA inclusa, condiviso con altri progetti di Matteo (stesso fornitore e stesso tipo di Sergio, così il trasferimento futuro è una copia dei container e del database). Il backup giornaliero è incluso; in più il sistema fa un proprio dump del database ogni notte.

---

## 5. Plancia di controllo (solo per Matteo)

Una schermata con **una riga per fonte** e un semaforo:

| Colonna | Significato |
|---|---|
| Stato | 🟢 regolare · 🟡 silenziosa più del solito · 🔴 errore o struttura cambiata · ⏸ in pausa |
| Ultimo controllo / esito | quando e com'è andato (errore del sito, pagina irraggiungibile…) |
| Ultima novità trovata | data e titolo |
| Silenzio | giorni senza novità **rispetto al ritmo normale di quella fonte** |
| Novità ultimi 30/90 giorni | con un mini-grafico dell'andamento |
| Costo IA del mese | per fonte |
| Azioni | ▶ rilancia ora · ⏸ pausa · ✎ modifica configurazione · 📄 vedi log |

**Allarmi automatici**, via email a Matteo e in cima alla plancia:
- **Silenzio sospetto**: nessuna novità da più di 3 volte l'intervallo normale della fonte (minimo 30 giorni).
- **Struttura cambiata**: la pagina risponde ma non si riesce più a leggere nessun elemento dall'elenco. È il segnale tipico di un sito rifatto.
- **Errori ripetuti**: sito irraggiungibile per 3 controlli di fila.
- **Budget**: la spesa IA del mese supera la soglia impostata (es. 80 €). Le schede non urgenti si fermano da sole.

Altre sezioni della plancia: **coda di approvazione dei match** (vedi §7), **bandi in scadenza**, **resoconto settimanale** (cosa è arrivato, cosa si è rotto, quanto si è speso).

---

## 6. Cruscotto clienti (dentro Contract to Cash)

- **I miei bandi**: i match del cliente con punteggio, motivo ("sei in FVG, ATECO 25.62, PMI: requisiti rispettati"), requisiti da verificare, scadenza.
- **Catalogo**: tutti i bandi aperti con filtri (territorio, settore, tipo di aiuto, scadenza, importo).
- **Scheda bando**: sintesi in italiano semplice, requisiti, spese ammesse, contributo, scadenze, link e documenti ufficiali.
- **Pulsante "Mi interessa, contattatemi"**: la richiesta arriva a Matteo come opportunità di consulenza.
- **Preferenze**: frequenza delle email (subito / riepilogo settimanale) e disiscrizione.

Ogni scheda riporta **"Informazione indicativa, verificare il bando ufficiale"** e la data dell'ultimo controllo.

---

## 7. Match e notifiche

1. Quando arriva un bando nuovo o cambia un profilo, il sistema ricalcola i match.
2. **Punteggio**: prima i requisiti obbligatori (territorio, ATECO, dimensione, forma giuridica: se ne manca uno il match si scarta), poi quelli di preferenza.
3. **Fase iniziale: approva Matteo.** I match vanno in una coda nella plancia e Matteo sceglie se inviare, modificare o scartare. Da commercialista, è una garanzia di qualità verso il cliente.
4. **Dopo la taratura**: i match con punteggio alto partono da soli, quelli incerti restano in coda.
5. **Email** inviata dal modulo 6 (nella prima versione dentro Bandi Radar, poi da C2C): oggetto chiaro, 3 righe di motivo, link al cruscotto. Mai due volte lo stesso bando allo stesso cliente. Promemoria 15 giorni prima della scadenza se il cliente ha cliccato "mi interessa".
6. **Servizio email: Resend.** Sergio lo usa già per altro, quindi quando il modulo passerà in C2C non si cambia fornitore. Va attivata la **regione europea** di Resend (i dati restano in UE) e firmato il loro accordo sul trattamento dati. Brevo sarebbe stato equivalente sul piano tecnico; il vantaggio di Resend è avere un solo fornitore tra i due sistemi. Il piano gratuito (3.000 email al mese) basta fino a qualche centinaio di clienti.

---

## 8. Privacy e aspetti legali

- **Profili anonimi** verso Bandi Radar e verso l'IA (vedi §2).
- **Contratti con i fornitori**: accordi sul trattamento dati (DPA) con Anthropic, il servizio email e l'hosting.
- **Informativa ai clienti e registro dei trattamenti**: non c'è un consulente privacy. In Fase 6 preparo io le bozze (informativa, registro, DPA da firmare, testo per il consenso alle email). Sono bozze tecniche: prima dei clienti reali conviene farle leggere a un professionista, anche solo per una revisione di poche ore.
- **Siti pubblici**: si leggono solo informazioni pubbliche, rispettando le regole dei siti (robots.txt) e a ritmo moderato. Si citano le fonti come richiedono le licenze dei dati aperti.

---

## 9. Piano d'azione e cronoprogramma

Partenza ipotizzata **lunedì 28/09/2026**, con 2–3 sessioni di lavoro a settimana. Ogni fase termina con **qualcosa che Matteo può provare**.

| Fase | Settimane | Contenuto | Cosa provi tu alla fine |
|---|---|---|---|
| **0 — Fondamenta** | 1 (28/09–04/10) | Repository e regole di lavoro (CLAUDE.md), VPS OVH preparato (Docker, firewall, backup notturno), Docker Compose avviabile con un comando, raccolta pianificata, database, **registro completo delle ~180 fonti con indirizzi verificati** | Il sistema che parte sul tuo PC e l'elenco delle fonti |
| **1 — Raccolta** | 2–4 (05/10–25/10) | Connettori per incentivi.gov.it, Portale UE e dati aperti Lombardia; osservatore di pagine per Regioni, Camere ed enti nazionali; archivio; **inizio misurazione delle frequenze** | Ogni lunedì un'email "novità della settimana" |
| **2 — Plancia di controllo v1** | 4–5 (19/10–01/11) | Semafori, silenzi, rilanci, log, costi, allarmi email. **Taratura delle frequenze** con 4 settimane di dati reali | La plancia nel browser |
| **3 — Schede bando** | 5–7 (26/10–15/11) | Lettura dei PDF, scheda standard, doppioni, proroghe e chiusure. **Controllo qualità: Matteo verifica 30 schede** a campione | Schede leggibili, con i tuoi voti sulla qualità |
| **4 — Profili e match** | 7–9 (09/11–29/11) | Formato del profilo anonimo, script che legge le anagrafiche dal Postgres di Matteo, API (pronta per C2C), motore di abbinamento, spiegazioni, Comuni dei clienti aggiunti alle fonti. Test con 5 imprese di prova | Per ogni impresa di prova, i suoi bandi con il motivo |
| **5 — Cruscotto clienti ed email** | 9–11 (23/11–13/12) | Pagine React dentro Bandi Radar con accesso per cliente, coda di approvazione, invio email con Resend, preferenze e disiscrizione | Il cruscotto e un'email di prova |
| **6 — Pilota** | 11–12 (07/12–20/12) | Primi clienti reali, correzioni, bozze dei documenti privacy, messa online stabile | Il servizio acceso per i primi clienti |
| **7 — Estensioni** | da gennaio 2027 | Collegamento a C2C (con Sergio), RNA/de minimis (open data mensili), bandi agricoli (PSR) e GAL, altri Comuni capoluogo, avvisi SIMEST, scadenzario | Uno alla volta, a tua scelta |

Alcune fasi si sovrappongono di una settimana, apposta. Nella **Fase 0** e nella **Fase 3** l'impegno di Matteo è maggiore: decisioni e verifica delle schede.

---

## 10. Decisioni prese e punti aperti

**Decise il 23/09/2026:**

| Tema | Decisione |
|---|---|
| Integrazione con Contract to Cash | Rinviata: il codice è di Sergio. Bandi Radar nasce autonomo; nella prima versione i profili arrivano dal Postgres di Matteo e cruscotto ed email vivono dentro Bandi Radar. |
| Server | **OVH VPS-2** (4 vCore, 8 GB, 75 GB NVMe, backup incluso, 8,80 €/mese IVA inclusa), Ubuntu 24.04 LTS, datacenter in Francia, come il server di Sergio. Matteo lo compra subito, anche per altri progetti: il VPS-2 regge Bandi Radar più uno o due progetti leggeri; se arriva un secondo progetto con database e browser propri, si passa al VPS-3 (12 GB) senza reinstallare (OVH permette di salire di taglia, non di scendere). Ogni progetto vive nel suo Docker Compose, isolato dagli altri. Le sessioni cloud di Claude Code non possono ospitare il sistema. Se qualche sito blocca l'IP del VPS (Milano, incentivi.gov.it), il ripiego è un browser senza interfaccia o un lancio dal PC di Matteo. |
| IA | Fasi 0–2 senza IA. Account API Anthropic a consumo dalla Fase 3, con tetto di spesa basso. Prima di automatizzare, Matteo lancia lui stesso nelle sessioni di Claude Code (abbonamento) le stesse richieste che farà il sistema, come **mappature** salvate in `docs/ricerche/`, per vedere cosa esce dai siti. |
| Dominio | Non serve fino alla Fase 4: la plancia (solo Matteo) si raggiunge con l'IP del VPS e un nome tecnico gratuito. Serve dalla **Fase 5**, per due motivi: il cruscotto dei clienti va su un indirizzo presentabile in HTTPS, e le email non si possono inviare da un IP (Resend richiede un dominio con record SPF e DKIM). Proposta: **sottodominio del dominio di Contract to Cash** (es. `bandi.<dominio-c2c>`), coerente con il prodotto; Sergio delega il sottodominio a una zona DNS gestita da Matteo (su OVH), così i record successivi non richiedono più il suo intervento. Da chiedere a Sergio in tempo per la Fase 5. |
| Approvazione manuale dei match | Per tutto il pilota e almeno i primi 2 mesi con clienti reali. |
| Catalogo visibile ai clienti | Solo i propri match nella prima versione; catalogo completo in Fase 7. |
| Province e Comuni | Corretto il 23/09: bastano Province e Comuni capoluogo. La mappatura in `docs/ricerche/` mostra che le Province non pubblicano bandi per imprese (salvo poche eccezioni, inserite singolarmente) e che i capoluoghi sì: entrano tutti i capoluoghi (~80) e le Province eccezione (~7). Comuni minori fuori, salvo richiesta per il Comune di un cliente. |
| Modello commerciale | Da decidere. È un'opportunità di cross-selling verso la consulenza sui bandi: il pulsante "Mi interessa, contattatemi" è quindi centrale e va curato per primo. |
| Clienti | Oggi 0, obiettivo 100 entro 6 mesi. Test con le anagrafiche del Postgres di Matteo. |
| Servizio email | Resend (già usato da Sergio), regione europea. |
| Consulente privacy | Nessuno. Bozze preparate in Fase 6, da far rivedere a un professionista prima dei clienti reali. |

**Ancora aperti:**

1. **Struttura delle anagrafiche in Postgres**: entro la Fase 4 serve lo schema delle tabelle (senza dati) e i campi disponibili per costruire il profilo anonimo (ATECO, comune, dimensione, fatturato, forma giuridica…).
2. **Server**: OVH VPS-2, acquisto immediato. In Fase 0 serve l'accesso SSH, da inserire come segreto dell'ambiente cloud (mai in chat).
4. **Dominio**: chiedere a Sergio, entro la Fase 5, la delega di un sottodominio del dominio C2C (o un record A e i record di Resend, se preferisce tenere il DNS).
5. **Rete della sessione cloud**: da allargare nelle impostazioni dell'ambiente, altrimenti le mappature e la Fase 1 non raggiungono i siti delle fonti.
3. **Modello commerciale**: resta da decidere, non blocca lo sviluppo.
