# Bandi Radar — Piano di progetto v1

*Bozza del 23/09/2026 — da approvare con Matteo.*

---

## 1. Obiettivo

Trovare in automatico **tutti i bandi aperti** (UE, nazionali, regionali, camerali, altri enti), trasformarli in **schede ordinate** (chi può partecipare, cosa si finanzia, quanto, entro quando) e **abbinarli ai clienti di Contract to Cash**. Ai clienti arriva una proposta via email e possono consultare tutto da un cruscotto.

Requisiti di Matteo:
- **Non si scartano** regioni ed enti locali.
- **Plancia di controllo** per vedere lo stato di ogni fonte, rilanciare le automazioni e accorgersi delle fonti "mute" da troppo tempo (possibile guasto).
- **Cruscotto** consultabile anche dai clienti.
- **Match automatici** con notifica ed email.
- Deve reggere la crescita da 0 a molti clienti senza che i costi esplodano.

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
| 6 | **Cruscotto clienti + email** | Pagine dentro Contract to Cash e invio delle proposte | React in C2C + servizio email europeo (es. Brevo) |

**Scelta chiave: Bandi Radar non conosce i clienti per nome.** Riceve solo profili anonimi (codice interno, ATECO, provincia, dimensione, fatturato a fasce, export sì/no…). Nomi, email e invii restano dentro Contract to Cash. È più sicuro per la privacy e più semplice da difendere con i clienti.

**Come teniamo tutte le regioni e le Camere senza 80 programmi diversi:** non si scrive uno script per ogni sito. C'è **un solo "osservatore di pagine" generico**: per ogni fonte basta una riga di configurazione (indirizzo della pagina elenco, eventuale feed RSS). L'osservatore confronta la pagina con quella della volta prima e **manda all'IA solo la parte cambiata**. Aggiungere una fonte significa aggiungere una riga, non scrivere codice. Quando un sito cambia aspetto, di solito si aggiorna quella riga.

---

## 3. Fonti e frequenza di controllo

> Le frequenze di pubblicazione qui sotto sono **stime iniziali**. Non ho potuto misurarle perché i siti delle fonti sono bloccati dalla rete di questa sessione. La **Fase 1 le misura davvero** per 4 settimane (il sistema registra ogni nuovo bando con la sua data) e a fine Fase 2 si tarano le frequenze sui dati reali.
> Ogni controllo di una pagina costa praticamente zero, perché l'IA interviene solo se qualcosa è cambiato. La frequenza serve quindi a **essere tempestivi** senza **disturbare** i siti pubblici, non a risparmiare.

| Gruppo | N. fonti | Pubblicazione stimata | Controllo proposto | Metodo |
|---|---|---|---|---|
| incentivi.gov.it (dati aperti) | 1 | aggiornamento continuo | ogni giorno | download CSV/JSON |
| Portale UE Funding & Tenders | 1 | a ondate (programmi di lavoro), più volte al mese | ogni giorno | API ufficiale |
| Lombardia (dati aperti + portale bandi) | 1 | più bandi a settimana | ogni giorno | dati aperti + osservatore |
| **FVG** | 1 | più avvisi a settimana (di cui molti non per imprese) | ogni giorno | osservatore (+ RSS se c'è) |
| Regioni grandi (Veneto, Emilia-R., Piemonte, Lazio, Campania, Puglia, Sicilia, Toscana) | 8 | più avvisi a settimana | ogni giorno | osservatore |
| Altre Regioni e Province autonome | 11 | 1–5 a settimana | 3 volte a settimana | osservatore |
| MIMIT, Invitalia, GSE, SIMEST | 4 | poche misure nuove al mese, ma aperture di sportello e modifiche frequenti | 3 volte a settimana | osservatore |
| **CCIAA Milano-MB-Lodi e Pordenone-Udine** | 2 | 1–4 bandi al mese, concentrati a inizio anno | ogni giorno | osservatore |
| Altre Camere di Commercio | ~58 | 1–4 bandi al mese, concentrati a inizio anno | 1 volta a settimana (2 volte tra gennaio e aprile) | osservatore |
| Fondazioni bancarie (selezione) | ~5 | poche finestre all'anno | 1 volta a settimana | osservatore |
| **Totale** | **~92** | | | |

**I Comuni** (quasi 7.900) non si possono controllare tutti. Proposta: in Fase 7 aggiungiamo i **capoluoghi di Lombardia e FVG**. Per gli altri ci affidiamo al campo "comuni" di incentivi.gov.it. Decide Matteo.

**Fonti escluse dalla raccolta**: TED (sono appalti), OpenCoesione (storico), aggregatori privati (i loro elenchi hanno diritti sulla banca dati; possono servire solo per un controllo manuale).
**RNA** non serve a trovare bandi: entra in Fase 7 per il controllo del *de minimis* dei clienti.

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

**Server:** un piccolo server in Europa (8–20 €/mese) oppure un container in più accanto a quelli di Contract to Cash, se il tuo hosting lo permette.

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
5. **Email** inviata da Contract to Cash (è C2C a conoscere gli indirizzi): oggetto chiaro, 3 righe di motivo, link al cruscotto. Mai due volte lo stesso bando allo stesso cliente. Promemoria 15 giorni prima della scadenza se il cliente ha cliccato "mi interessa".

---

## 8. Privacy e aspetti legali

- **Profili anonimi** verso Bandi Radar e verso l'IA (vedi §2).
- **Contratti con i fornitori**: accordi sul trattamento dati (DPA) con Anthropic, il servizio email e l'hosting.
- **Informativa ai clienti e registro dei trattamenti**: da aggiornare con il tuo consulente privacy.
- **Siti pubblici**: si leggono solo informazioni pubbliche, rispettando le regole dei siti (robots.txt) e a ritmo moderato. Si citano le fonti come richiedono le licenze dei dati aperti.

---

## 9. Piano d'azione e cronoprogramma

Partenza ipotizzata **lunedì 28/09/2026**, con 2–3 sessioni di lavoro a settimana. Ogni fase termina con **qualcosa che Matteo può provare**.

| Fase | Settimane | Contenuto | Cosa provi tu alla fine |
|---|---|---|---|
| **0 — Fondamenta** | 1 (28/09–04/10) | Repository e regole di lavoro (CLAUDE.md), ambiente cloud con accesso ai siti delle fonti, database, **registro completo delle ~92 fonti con indirizzi verificati** | L'elenco delle fonti, consultabile |
| **1 — Raccolta** | 2–4 (05/10–25/10) | Connettori per incentivi.gov.it, Portale UE e dati aperti Lombardia; osservatore di pagine per Regioni, Camere ed enti nazionali; archivio; **inizio misurazione delle frequenze** | Ogni lunedì un'email "novità della settimana" |
| **2 — Plancia di controllo v1** | 4–5 (19/10–01/11) | Semafori, silenzi, rilanci, log, costi, allarmi email. **Taratura delle frequenze** con 4 settimane di dati reali | La plancia nel browser |
| **3 — Schede bando** | 5–7 (26/10–15/11) | Lettura dei PDF, scheda standard, doppioni, proroghe e chiusure. **Controllo qualità: Matteo verifica 30 schede** a campione | Schede leggibili, con i tuoi voti sulla qualità |
| **4 — Profili e match** | 7–9 (09/11–29/11) | Formato del profilo anonimo, API per C2C, motore di abbinamento, spiegazioni. Test con 5 imprese di prova | Per ogni impresa di prova, i suoi bandi con il motivo |
| **5 — Cruscotto clienti ed email** | 9–11 (23/11–13/12) | Pagine React in C2C, coda di approvazione, invio email, preferenze e disiscrizione | Il cruscotto in C2C e un'email di prova |
| **6 — Pilota** | 11–12 (07/12–20/12) | Primi clienti reali, correzioni, documenti privacy, messa online stabile | Il servizio acceso per i primi clienti |
| **7 — Estensioni** | da gennaio 2027 | RNA/de minimis, bandi agricoli (PSR), Comuni capoluogo, avvisi SIMEST, scadenzario | Uno alla volta, a tua scelta |

Alcune fasi si sovrappongono di una settimana, apposta. Nella **Fase 0** e nella **Fase 3** l'impegno di Matteo è maggiore: decisioni e verifica delle schede.

---

## 10. Decisioni aperte per Matteo

1. **Comuni**: bastano i capoluoghi di Lombardia e FVG, o ne servono altri?
2. **Server**: stesso hosting di Contract to Cash (dove si trova oggi?) o server separato?
3. **Approvazione manuale** dei match: per quanto tempo prima di passare all'invio automatico?
4. **Cruscotto clienti**: il cliente vede solo i suoi match o anche tutto il catalogo?
5. **Il servizio è incluso** nell'abbonamento di C2C o a pagamento? Non cambia la tecnica, ma cambia le priorità.
6. **Integrazione con C2C**: chi lavora sul codice di Contract to Cash? È su GitHub, e posso accedervi?
