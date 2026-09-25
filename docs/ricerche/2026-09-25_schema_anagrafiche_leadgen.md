# Schema del database `leadgen` — per Bandi Radar

Documento di sola **struttura**. Nessuna riga di dati reali e' stata letta, copiata o
riportata qui: tutti gli esempi sono **inventati**.

- Estratto il: **25/09/2026** (fotografia dello schema del 2026-09-25 11:26)
- Prodotto da: `estrai_schema.py` → `schema_grezzo.json` (vedi §6)

> **Avvertenza importante.** Questo database non contiene "clienti": contiene **imprese
> prospect** (lead) raccolte da Google Maps e arricchite da Cerved Power BIz. Non esiste
> nessuna tabella di clienti acquisiti, referenti o documenti. Se Bandi Radar deve
> profilare i *clienti dello studio*, questa non e' la fonte giusta.

---

## 1. Come si raggiunge il database

| Cosa | Valore |
|---|---|
| Container Docker | `lead-postgres` |
| Motore | PostgreSQL **16.14** (immagine Debian) |
| Database | `leadgen` |
| Schema Postgres | `public` (unico schema presente) |
| Host / porta | `localhost` : `5432` |

**Utenti del database.** Ne esiste **uno solo**: `postgres`, che e' **superuser**.
Un utente di sola lettura **non esiste**.

**Dove stanno le credenziali.** Nel file `.env` nella cartella del progetto
(`C:\Users\matte\lead-generation\.env`), nelle variabili
`DB_HOST`, `DB_PORT`, `DB_NAME`, `DB_USER`, `DB_PASSWORD`.
Il file e' escluso da Git. La password non e' riportata in questo documento.

> **Raccomandazione.** Far collegare Bandi Radar come `postgres` significa dargli il
> potere di cancellare tutto. Conviene creare un utente dedicato di sola lettura, per
> esempio `bandi_radar_ro`, con permesso `SELECT` limitato alle sole colonne non
> identificative. E' una decina di righe di SQL: se vuoi te le preparo.

---

## 2. Le tabelle

Tutte nello schema `public`. Le prime otto sono quelle che descrivono le imprese;
le ultime cinque servono al funzionamento interno e a Bandi Radar non servono.

| Tabella | A cosa serve | Chiave primaria | Righe |
|---|---|---|---|
| `leads_raw` | Anagrafica grezza da Google Maps + crawling del sito | `id` (unica anche `place_id`) | 43.368 |
| `leads_enriched` | Anagrafica Cerved della stessa impresa | `id` (unica anche `partita_iva`) | 8.198 |
| `leads_bilancio` | Bilanci per anno, importi in **milioni di euro** | `id` (unica `partita_iva`+`anno`) | 14.679 |
| `leads_persone` | Amministratori e altre figure | `id` | 13.276 |
| `leads_soci` | Compagine sociale | `id` | 13.104 |
| `leads_sedi` | Sedi legali e operative | `id` | 13.923 |
| `leads_scoring` | Indicatori di rischio Cerved | `id` (unica `partita_iva`) | 7.838 |
| `leads_master` | Vista consolidata con punteggio ICP e tier A/B/C/D | *nessuna* | 1.294 |
| `ricerche_fatte` | Registro delle ricerche gia' eseguite | `id` | 2.307 |
| `comuni_completati` | Avanzamento dello scraping per comune | `id` | 78 |
| `aree_da_raffinare` | Aree da riscandagliare | `id` | 64 |
| `email_templates` | Modelli di cold email | `id` | 9 |
| `emails_ready_to_send` | Email generate e pronte | `id` | 75 |

⚠️ `leads_master` **non ha chiave primaria**: e' una tabella ricalcolata da
`consolidator.py`, quindi va trattata come risultato, non come sorgente.

---

## 3. Colonne, tabella per tabella

Legenda: ⭐ = **dato identificativo**, che Bandi Radar non deve mai leggere.
Tutti gli esempi sono **inventati**.

### `leads_raw` — 43.368 righe

| Colonna | Tipo | Vuota? | Cosa contiene | Esempio (inventato) |
|---|---|---|---|---|
| `id` | integer | no | Numero progressivo automatico | `40277` |
| `place_id` | text | si | Codice Google Maps del luogo | `ChIJxxYYzz00AaBb` |
| `fonte` | text | si | Da dove arriva la riga (default `google_maps`) | `google_maps` |
| ⭐ `nome` | text | si | Insegna commerciale | `Alfa Impianti` |
| `categoria` | text | si | Parola chiave usata nella ricerca | `impianti elettrici` |
| `area` | text | si | **Comune** di ricerca | `Codroipo` |
| ⭐ `indirizzo` | text | si | Indirizzo completo in una stringa | `Via Esempio 1, 33033 Codroipo UD` |
| ⭐ `telefono` | text | si | Telefono | `+39 0432 000000` |
| `sito_web` | text | si | Sito | `https://esempio-non-reale.it` |
| ⭐ `email` | text | si | Email ordinaria trovata sul sito | `info@esempio-non-reale.it` |
| `rating` | numeric | si | Voto medio Google | `4.6` |
| `num_recensioni` | integer | si | Numero recensioni Google | `27` |
| `latitudine` | numeric | si | Coordinata | `45.96000` |
| `longitudine` | numeric | si | Coordinata | `12.98000` |
| `creato_il` | timestamp | si | Quando e' entrata la riga (default `now()`) | `2026-03-01 10:00:00` |
| `tipi_google` | text | si | Categorie Google separate da virgola | `electrician,general_contractor` |
| ⭐ `partita_iva` | text | si | P.IVA, **chiave di collegamento** con le altre tabelle | `01234567890` |
| `granularita` | text | si | Livello della ricerca | `comune` |
| `cap_origine` | text | si | CAP da cui e' partita la ricerca | `33033` |
| ⭐ `social` | text | si | Link social trovati | `https://facebook.com/esempio` |
| `parole_chiave` | text | si | Parole trovate sul sito | `fotovoltaico, domotica` |
| `certificazioni` | text | si | Certificazioni dichiarate sul sito | `ISO 9001` |
| `crawled_il` | timestamp | si | Quando e' stata visitata la home | `2026-04-02 09:12:00` |
| `crawl2_il` | timestamp | si | Quando sono state visitate le sottopagine | `2026-04-20 18:40:00` |
| `crawl_esito` | text | si | Esito del crawling (categorico) | `js_probabile` |

### `leads_enriched` — 8.198 righe (una riga per P.IVA)

| Colonna | Tipo | Vuota? | Cosa contiene | Esempio (inventato) |
|---|---|---|---|---|
| `id` | integer | no | Progressivo automatico | `5120` |
| ⭐ `partita_iva` | text | si | P.IVA (**unica**) | `01234567890` |
| ⭐ `denominazione` | text | si | Ragione sociale Cerved | `ALFA IMPIANTI S.R.L.` |
| ⭐ `codice_fiscale` | text | si | CF della societa' | `01234567890` |
| `ateco` | text | si | Codice ATECO — **formato da verificare (§4)** | `43.21.01` |
| ⭐ `telefono` | text | si | Telefono da Cerved | `+39 0432 000000` |
| ⭐ `pec` | text | si | PEC — **mai usare per contattare** | `alfa@pec-esempio.it` |
| `sito_web` | text | si | Sito da Cerved | `https://esempio-non-reale.it` |
| `dipendenti` | **text** | si | Numero dipendenti, salvato come **testo** | `12` |
| `stato` | text | si | Stato dell'impresa (categorico) | `Attiva` |
| ⭐ `sede` | text | si | Sede in una stringa unica, non scomposta | `Codroipo (UD)` |
| `fatturato` | **text** | si | Fatturato, salvato come **testo** | `2.4` |
| `fonte` | text | si | Default `powerbiz` | `powerbiz` |
| `arricchito_il` | timestamp | si | Data dell'arricchimento | `2026-05-11 14:30:00` |
| `esito` | text | si | `ok` oppure `non_trovata` | `ok` |
| ⭐ `indirizzo` | text | si | Indirizzo da Cerved | `Via Esempio 1, 33033 Codroipo UD` |

### `leads_bilancio` — 14.679 righe (una per P.IVA e anno)

Chiave unica composta: **(`partita_iva`, `anno`)**.
**Tutti gli importi sono in MILIONI di euro** (normalizzati dalla funzione `a_milioni`).

| Colonna | Tipo | Vuota? | Cosa contiene | Esempio (inventato) |
|---|---|---|---|---|
| `id` | integer | no | Progressivo | `9001` |
| ⭐ `partita_iva` | text | si | Collegamento all'impresa | `01234567890` |
| `anno` | integer | si | Anno del bilancio | `2024` |
| `ricavi` | numeric | si | Ricavi, in Mln € | `2.4` |
| `valore_produzione` | numeric | si | Valore della produzione, Mln € | `2.6` |
| `acquisti` | numeric | si | Acquisti, Mln € | `1.3` |
| `mol` | numeric | si | Margine operativo lordo, Mln € | `0.31` |
| `oneri_finanziari` | numeric | si | Oneri finanziari, Mln € | `0.02` |
| `utile_perdita` | numeric | si | Utile o perdita, Mln € | `0.12` |
| `cash_flow` | numeric | si | Cash flow, Mln € | `0.22` |
| `ebitda` | numeric | si | EBITDA, Mln € | `0.30` |
| `ebitda_margin` | numeric | si | EBITDA margin (percentuale) | `12.5` |
| `attivo_breve` | numeric | si | Attivo circolante, Mln € | `1.8` |
| `patrimonio_netto` | numeric | si | Patrimonio netto, Mln € | `0.9` |
| `passivo_breve` | numeric | si | Passivo corrente, Mln € | `1.1` |
| `debiti_banche_breve` | numeric | si | Debiti bancari a breve, Mln € | `0.35` |
| `aggiornato_il` | timestamp | si | Ultimo aggiornamento della riga | `2026-05-11 14:31:00` |

⚠️ **Non esiste la colonna "totale attivo"**: ci sono solo `attivo_breve` e
`patrimonio_netto`. Per la soglia PMI europea il totale di bilancio va ricostruito
altrove o aggiunto.

### `leads_persone` — 13.276 righe

| Colonna | Tipo | Vuota? | Cosa contiene | Esempio (inventato) |
|---|---|---|---|---|
| `id` | integer | no | Progressivo | `7700` |
| ⭐ `partita_iva` | text | si | Impresa di riferimento | `01234567890` |
| `tipo` | text | si | Gruppo della figura (categorico) | `esponente` |
| ⭐ `nome` | text | si | Nome e cognome della persona | `Mario Bianchi` |
| ⭐ `cf` | text | si | Codice fiscale della persona | `BNCMRA80A01H501X` |
| `carica` | text | si | Carica ricoperta | `Amministratore unico` |
| `in_carica_dal` | **text** | si | Data di nomina, salvata come **testo** | `01/02/2019` |
| `fonte` | text | si | Default `powerbiz` | `powerbiz` |
| `aggiornato_il` | timestamp | si | Ultimo aggiornamento | `2026-05-11 14:31:00` |
| `aggiunto_il` | timestamp | si | Primo inserimento | `2026-05-11 14:31:00` |

### `leads_soci` — 13.104 righe

| Colonna | Tipo | Vuota? | Cosa contiene | Esempio (inventato) |
|---|---|---|---|---|
| `id` | integer | no | Progressivo | `6100` |
| ⭐ `partita_iva` | text | si | Impresa di riferimento | `01234567890` |
| ⭐ `nome` | text | si | Nome del socio (persona o societa') | `Mario Bianchi` |
| `quota` | **text** | si | Quota percentuale, come **testo** | `50%` |
| `ammontare` | **text** | si | Valore della quota, come **testo** | `10.000` |
| `tipologia` | text | si | Tipo di socio (categorico) | `persona fisica` |
| `aggiunto_il` | timestamp | si | Inserimento | `2026-05-11 14:31:00` |

### `leads_sedi` — 13.923 righe

| Colonna | Tipo | Vuota? | Cosa contiene | Esempio (inventato) |
|---|---|---|---|---|
| `id` | integer | no | Progressivo | `8300` |
| ⭐ `partita_iva` | text | si | Impresa di riferimento | `01234567890` |
| ⭐ `indirizzo` | text | si | Indirizzo della sede, **stringa unica non scomposta** | `Via Esempio 1, 33033 Codroipo UD` |
| `tipo` | text | si | Legale / operativa / unita' locale (categorico) | `sede operativa` |
| `aggiunto_il` | timestamp | si | Inserimento | `2026-05-11 14:31:00` |

### `leads_scoring` — 7.838 righe (una per P.IVA)

Tutte le colonne di valore sono **text**, non numeri: sono etichette Cerved.

| Colonna | Tipo | Vuota? | Cosa contiene | Esempio (inventato) |
|---|---|---|---|---|
| `id` | integer | no | Progressivo | `4400` |
| ⭐ `partita_iva` | text | si | Impresa (**unica**) | `01234567890` |
| `affidabilita_media` | text | si | Giudizio sintetico di affidabilita' | `Medio-alta` |
| `eventi_negativi` | text | si | Presenza di eventi pregiudizievoli | `Assenti` |
| `tempi_pagamento` | text | si | Comportamento nei pagamenti | `Regolare` |
| `richieste_impresa` | text | si | Richieste di informazioni ricevute | `Basse` |
| `fido_certificato` | text | si | Fido suggerito | `50.000` |
| `liquidita` | text | si | Indicatore di liquidita' | `Buona` |
| `solvibilita` | text | si | Indicatore di solvibilita' | `Buona` |
| `crescita` | text | si | Indicatore di crescita | `Stabile` |
| `marginalita` | text | si | Indicatore di marginalita' | `Media` |
| `aggiornato_il` | timestamp | si | Ultimo aggiornamento | `2026-05-11 14:31:00` |

### `leads_master` — 1.294 righe (vista consolidata, ricalcolata)

Contiene **solo le imprese gia' scorate**, non tutte le 43.368 di `leads_raw`.

| Colonna | Tipo | Vuota? | Cosa contiene | Esempio (inventato) |
|---|---|---|---|---|
| `place_id` | text | si | Codice Google | `ChIJxxYYzz00AaBb` |
| ⭐ `denominazione` | text | si | Ragione sociale Cerved | `ALFA IMPIANTI S.R.L.` |
| ⭐ `nome` | text | si | Insegna Google | `Alfa Impianti` |
| ⭐ `partita_iva` | text | si | P.IVA | `01234567890` |
| `ateco` | text | si | Codice ATECO | `43.21.01` |
| `stato` | text | si | Stato impresa | `Attiva` |
| `area` | text | si | **Comune** | `Codroipo` |
| `provincia` | text | si | **Provincia** (unico posto dove e' un campo a se') | `UD` |
| `ricavi` | double precision | si | Ricavi in Mln € | `2.4` |
| ⭐ `telefono` | text | si | Telefono | `+39 0432 000000` |
| ⭐ `email` | text | si | Email ordinaria | `info@esempio-non-reale.it` |
| ⭐ `pec` | text | si | PEC — mai per contatto | `alfa@pec-esempio.it` |
| `sito_web` | text | si | Sito | `https://esempio-non-reale.it` |
| `score` | double precision | si | Punteggio ICP complessivo | `72.5` |
| `tier` | text | si | Fascia A / B / C / D | `B` |
| `s_ateco` | bigint | si | Sottopunteggio ATECO | `20` |
| `s_geo` | bigint | si | Sottopunteggio geografico | `15` |
| `s_keyword` | bigint | si | Sottopunteggio parole chiave | `10` |
| `s_completezza` | double precision | si | Sottopunteggio completezza dati | `12.5` |
| `s_freschezza` | bigint | si | Sottopunteggio freschezza | `5` |
| `s_fatturato` | double precision | si | Sottopunteggio fatturato | `10.0` |

---

## 4. Le informazioni che hai chiesto: dove sono (e dove NON ci sono)

Legenda: ✅ c'e' · ⚠️ c'e' ma in forma difficile · ❌ **non esiste**

| Informazione richiesta | Stato | Dove / commento |
|---|---|---|
| **ATECO principale** | ⚠️ | `leads_enriched.ateco`, `leads_master.ateco`. **Formato non verificato**: non so se ha i punti ne' se e' ATECO 2007 o 2025. Serve un controllo (§7). |
| **ATECO secondari** | ❌ | Una sola colonna, un solo codice. |
| **Forma giuridica** (srl, snc, ditta individuale) | ❌ | Nessuna colonna. Deducibile *a occhio* dal suffisso della ragione sociale, ma e' un dato identificativo che Bandi Radar non dovrebbe leggere. |
| **Comune sede legale** | ⚠️ | `leads_raw.area` e' il comune **di ricerca**, non necessariamente della sede. `leads_enriched.sede` e' una stringa unica (`"Codroipo (UD)"`), non scomposta. |
| **Provincia** | ⚠️ | Campo a se' **solo** in `leads_master.provincia` (1.294 righe su 43.368). Altrove va estratta dal testo. |
| **Regione** | ❌ | Mai memorizzata. Ricavabile dalla provincia con una tabella di conversione. |
| **Sedi operative** | ⚠️ | `leads_sedi` esiste, ma `indirizzo` e' una stringa unica e `tipo` distingue le sedi. Comune/provincia non scomposti. |
| **Data di costituzione / inizio attivita'** | ❌ | Nessuna colonna. `leads_persone.in_carica_dal` e' un'altra cosa. |
| **Numero dipendenti** | ⚠️ | `leads_enriched.dipendenti`, ma di tipo **text**: va convertito e potrebbe contenere fasce invece di numeri. |
| **ULA** | ❌ | Mai calcolate. |
| **Fatturato** | ✅ | Due fonti: `leads_bilancio.ricavi` (numerico, in **Mln €**, per anno) — la piu' affidabile — e `leads_enriched.fatturato` (text). |
| **Totale attivo** | ❌ | Ci sono solo `attivo_breve` e `patrimonio_netto`. Il totale di bilancio manca. |
| **Classe dimensionale** (micro/piccola/media) | ❌ | Mai calcolata. Ricostruibile parzialmente da ricavi + dipendenti, ma senza totale attivo la soglia PMI UE non e' verificabile in pieno. |
| **Impresa femminile** | ❌ | Nessuna colonna. Stimabile da `leads_soci` / `leads_persone`, ma richiede i **nomi delle persone** (dati identificativi ⭐). |
| **Impresa giovanile** | ❌ | Nessuna colonna, e manca la data di nascita dei soci. |
| **Start-up innovativa / PMI innovativa** | ❌ | Nessuna colonna. |
| **Iscrizione albo artigiani** | ❌ | Nessuna colonna. |
| **Cooperativa** | ❌ | Nessuna colonna (rientra nella forma giuridica mancante). |
| **Impresa agricola** | ❌ | Nessuna colonna; deducibile solo dall'ATECO. |
| **Export (si/no o %)** | ❌ | Nessuna colonna. |
| **Regime contabile** | ❌ | Nessuna colonna. |
| **Settore** (commercio/manifattura/servizi/turismo/agricoltura) | ⚠️ | Non esiste come campo. Derivabile dall'ATECO, una volta chiarito il formato. |
| **Aiuti de minimis gia' ricevuti** | ❌ | Mai registrati. |
| **Stato del cliente** (attivo/cessato/in prova) | ⚠️ | `leads_enriched.stato` e `leads_master.stato` dicono lo stato **camerale** dell'impresa (Attiva / Cessata / …), non il rapporto con lo studio. Il concetto di "cliente" qui non esiste. |
| **Data ultimo aggiornamento riga** | ✅ | `arricchito_il`, `aggiornato_il`, `aggiunto_il`, `crawled_il`, `crawl2_il`, `creato_il` a seconda della tabella. |

**In sintesi:** su 13 informazioni-chiave per valutare l'ammissibilita' a un bando,
questo database ne copre bene **due** (fatturato e ATECO) e parzialmente altre tre
(dipendenti, comune, stato). Tutti i requisiti soggettivi tipici dei bandi —
forma giuridica, dimensione d'impresa certificata, femminile/giovanile, innovativa,
artigiana, de minimis — **vanno aggiunti o chiesti a mano.**

---

## 5. Relazioni fra le tabelle

⚠️ **Nel database non esiste nessuna chiave esterna (FOREIGN KEY).** Le tabelle sono
collegate solo *per convenzione*, attraverso la colonna `partita_iva`. Postgres non
impedisce righe orfane, e infatti ce ne sono: 43.368 righe in `leads_raw` contro
8.198 in `leads_enriched`.

```
leads_raw
  | id (PK), place_id (unico)
  | partita_iva ........... collegamento logico, NON imposto dal database
  |
  +--> leads_enriched     (partita_iva, unica)      1 : 1
  +--> leads_bilancio     (partita_iva + anno)      1 : N   (un bilancio per anno)
  +--> leads_persone      (partita_iva)             1 : N
  +--> leads_soci         (partita_iva)             1 : N
  +--> leads_sedi         (partita_iva)             1 : N
  +--> leads_scoring      (partita_iva, unica)      1 : 1

leads_master  <-- ricalcolata da consolidator.py unendo le tabelle qui sopra
                  (collegata a leads_raw da place_id; nessuna chiave primaria)
```

---

## 6. Come rifare questa estrazione

Lo schema e' stato estratto con uno script del progetto, non con `pg_dump`, perche'
serviva anche il conteggio delle righe:

```bat
REM Dalla cartella C:\Users\matte\lead-generation, doppio clic su:
Estrai_schema.bat
```

che equivale a:

```bat
docker start lead-postgres
call venv\Scripts\activate.bat
python estrai_schema.py
```

Produce `schema_grezzo.json` (solo metadati + conteggi, nessun dato).

In alternativa, per il DDL puro delle tabelle:

```bat
docker exec -t lead-postgres pg_dump -U postgres -d leadgen --schema-only -n public > schema.sql
```

---

## 7. Cosa manca ancora a questo documento

Per rispondere con certezza su **formato ATECO** e sui **valori ammessi** delle colonne
categoriche (`stato`, `tipo`, `tipologia`, `tier`, `crawl_esito`, `esito`, `granularita`)
servirebbe guardare i valori distinti di quelle colonne. Non e' stato fatto: la consegna
era "nessuna riga di dati". Quei valori non sono identificativi — sono etichette come
`Attiva` o `sede operativa` — quindi si puo' decidere di estrarli in un secondo giro,
con conteggi aggregati e senza toccare nomi, P.IVA, email o indirizzi.
