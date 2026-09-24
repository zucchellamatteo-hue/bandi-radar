# La scheda del bando

*Formato deciso il 24/09/2026 (Fase 3). La tabella è `bandi` in `app/db/migrazioni/004_schede.sql`; il testo che chiederà all'IA di compilarla è in `app/schede/prompt_scheda.md`.*

Una **scheda** è un bando vero, ricavato da un annuncio che lo smistamento ha giudicato rilevante. La compila l'IA (Sonnet) leggendo la pagina dell'ente e gli allegati scaricati (bando, decreti, modulistica, FAQ); Matteo la controlla e le dà un voto. Gli stessi campi servono al catalogo della plancia (filtri) e, dalla Fase 4, all'abbinamento con i profili dei clienti.

Ogni scheda mostrata a un cliente porta la frase: **"Informazione indicativa, verificare il bando ufficiale"**, con il link alla pagina dell'ente e la data dell'ultimo controllo.

## I campi

| Campo | Cosa contiene | Formato | Chi lo compila |
|---|---|---|---|
| `titolo` | Nome del bando come lo scrive l'ente, senza abbreviazioni inventate | testo | IA (dall'annuncio) |
| `ente` | Chi finanzia (Regione, Camera di Commercio, Comune, Ministero...). Se c'è un gestore diverso (Unioncamere, Invitalia) va nella sintesi | testo | IA |
| `territorio` | Dove deve trovarsi l'impresa (sede operativa o legale): regione, provincia, comune, "Italia" | testo | IA |
| `url` | Pagina ufficiale del bando. Sempre presente: è il link che il cliente deve poter aprire | indirizzo web | raccolta |
| `stato` | `aperto`, `chiuso`, `prorogato`, `in_arrivo` (annunciato ma domande non ancora aperte) | uno dei quattro valori | IA, poi aggiornato dalla raccolta |
| `data_apertura` | Primo giorno in cui si presenta la domanda | data AAAA-MM-GG | IA |
| `scadenza` | Ultimo giorno per la domanda. **Vuoto** se il bando è "a sportello fino a esaurimento risorse" senza data (va detto nella sintesi) | data AAAA-MM-GG | IA |
| `sintesi` | 3-5 righe in italiano semplice: cosa finanzia, a chi, quanto, come si partecipa | testo | IA |
| `a_chi_si_rivolge` | Beneficiari: tipo di impresa, dimensione, settori, sede, anzianità | testo | IA |
| `cosa_finanzia` | Progetti o investimenti ammessi | testo | IA |
| `tipo_agevolazione` | `fondo_perduto`, `credito_imposta`, `finanziamento_agevolato`, `garanzia`, `voucher`, `misto`, `altro` | uno dei valori | IA |
| `contributo_massimo` | Importo massimo per singola impresa, in euro. Se ci sono più massimali, il più alto (gli altri nella sintesi) | numero | IA |
| `percentuale` | Percentuale massima delle spese coperta, comprese le maggiorazioni | numero 0-100 | IA |
| `spese_ammesse` | Elenco delle spese ammissibili, con eventuali forfait e minimi di progetto | testo | IA |
| `codici_ateco` | Codici o sezioni ATECO **ammessi**, come li scrive il bando (`"62"`, `"25.62"`, `"C"`). **Vuoto** se il bando non limita i settori | elenco di testi | IA |
| `codici_ateco_esclusi` | Codici o sezioni ATECO **esclusi** ("tutti i settori tranne..."). Il motore di abbinamento li confronta con l'ATECO del cliente | elenco di testi | IA |
| `dimensioni_ammesse` | `micro`, `piccola`, `media`, `grande`. **Vuoto** se il bando non lo dice | elenco di valori | IA |
| `requisiti` | Gli altri requisiti di ammissione (iscrizione al Registro, DURC, de minimis, sede, anzianità, rating, polizze...) | testo | IA |
| `tema` | `digitale`, `green`, `internazionalizzazione`, `investimenti`, `formazione`, `ricerca`, `assunzioni`, `avvio_impresa`, `turismo`, `commercio`, `agricoltura`, `altro` | uno dei valori | IA |
| `qualita` | Voto di Matteo sulla scheda, da 1 (da rifare) a 5 (perfetta) | numero 1-5 | Matteo |
| `dati` | La risposta completa dell'IA: da quale documento viene ogni campo, avvertenze, costo | JSON | sistema |
| `annuncio_id`, `creato_il`, `aggiornato_il` | Collegamento all'annuncio di origine e date | | sistema |

Regole generali:

- **Niente invenzioni.** Se un'informazione non c'è nella pagina o negli allegati, il campo resta vuoto (`null`). Meglio una scheda incompleta che un numero sbagliato.
- **Il bando ufficiale vince sulla pagina web.** Se la pagina e il PDF del bando non coincidono (succede, vedi l'esempio sotto), vale il PDF e la differenza si segnala nelle avvertenze.
- **Ogni campo ha la sua fonte**, conservata in `dati`: "pagina" oppure il nome dell'allegato e, se possibile, l'articolo. Serve a Matteo per controllare in fretta.
- I codici ATECO si scrivono come nel bando. Dal 1° aprile 2025 vale la classificazione **ATECO 2025**: alcuni bandi citano ancora ATECO 2007 e le sezioni hanno lettere diverse (per esempio le attività finanziarie sono la sezione K in ATECO 2007 e la L in ATECO 2025). La versione va nelle avvertenze.

## Esempio compilato a mano

**Bando:** PR FESR 2021-2027, Azione 1.3.1, "Contributi per la partecipazione delle PMI alle fiere internazionali in Lombardia – secondo sportello" (Regione Lombardia, codice RLO12026055023).

**Fonti usate:** la pagina su Bandi Online (https://www.bandi.regione.lombardia.it/servizi/servizio/bandi/dettaglio/attivita-produttive-imprese/fiere/pr-fesr-2021-2027-azione-1-3-1-contributi-partecipazione-pmi-fiere-internazionali-lombardia-secondo-sportello-RLO12026055023) e il suo allegato "Allegato A bando Fiere internazionali – 2° sportello" (PDF), scaricati il 24/09/2026 con `app/schede/allegati.py` e letti a mano. **I valori sono stati copiati da quei documenti in quella data, ma vanno ricontrollati sul bando ufficiale prima di usarli con un cliente:** lo sportello chiude quando finiscono le risorse, e l'ente può modificare il bando.

| Campo | Valore | Fonte |
|---|---|---|
| `titolo` | PR FESR 2021-2027 – Azione 1.3.1 "Contributi per la partecipazione delle PMI alle fiere internazionali in Lombardia – secondo sportello" | pagina |
| `ente` | Regione Lombardia | pagina |
| `territorio` | Lombardia | pagina (sede operativa attiva in Lombardia al momento dell'erogazione) |
| `url` | l'indirizzo della pagina qui sopra | raccolta |
| `stato` | `aperto` (domande dal 30/07/2026, sportello fino a esaurimento risorse: al 24/09/2026 non risultava chiuso) | pagina |
| `data_apertura` | 2026-07-30 | pagina; Allegato A, art. C.1 (dalle ore 10) |
| `scadenza` | *vuoto*: sportello fino a esaurimento della dotazione | Allegato A, art. C.2 |
| `sintesi` | Contributo a fondo perduto alle PMI che espongono a una o due fiere internazionali in Lombardia del calendario regionale, con inizio tra il 1/9/2026 e il 31/12/2027. Fino a 15.000 € per i nuovi espositori e 8.000 € per gli espositori abituali o già beneficiari del primo sportello; 50% dei costi, fino al 60% per micro imprese e startup. Costi calcolati a forfait sui metri quadri di stand. Domanda online su Bandi e Servizi dal 30/07/2026, a sportello con valutazione (almeno 50 punti su 100) fino a esaurimento dei 4,67 milioni disponibili. Gestisce Unioncamere Lombardia. | pagina; Allegato A, artt. A.5, B.1.b, B.2, C.2 |
| `a_chi_si_rivolge` | Micro, piccole e medie imprese iscritte e attive al Registro delle Imprese, di tutti i settori salvo le esclusioni, con sede operativa in Lombardia al momento dell'erogazione | pagina; Allegato A, art. A.3 |
| `cosa_finanzia` | Partecipazione come espositore a una o al massimo due fiere internazionali in Lombardia inserite nel calendario fieristico regionale, con inizio tra il 1/9/2026 e il 31/12/2027 | pagina; Allegato A, art. B.2 |
| `tipo_agevolazione` | `fondo_perduto` | pagina |
| `contributo_massimo` | 15000 | pagina; Allegato A, art. B.1.b (15.000 € per i nuovi espositori; 8.000 € per gli abituali e i già beneficiari) |
| `percentuale` | 60 | Allegato A, art. B.1.b (50% più 5% micro impresa più 5% startup) |
| `spese_ammesse` | A forfait: 440 € per metro quadro di superficie espositiva affittata; più 20% di quella voce per il personale; più 7% delle due voci per costi indiretti. Progetto minimo 6.000 €. Non serve rendicontare le fatture: basta l'attestato dell'organizzatore della fiera | Allegato A, art. B.3 |
| `codici_ateco` | *vuoto* (tutti i settori, salvo le esclusioni) | Allegato A, art. A.3 |
| `codici_ateco_esclusi` | `["A", "L"]`: sezione A agricoltura, silvicoltura e pesca (salvo le imprese agromeccaniche iscritte all'albo regionale) e sezione L attività finanziarie e assicurative, in **ATECO 2025** | Allegato A, art. A.3 |
| `dimensioni_ammesse` | `["micro", "piccola", "media"]` | pagina; Allegato A, art. A.3 |
| `requisiti` | PMI secondo il Reg. UE 651/2014; iscritta e attiva al Registro delle Imprese; non in liquidazione o procedure concorsuali; in regola con il DURC; aiuti "de minimis" (Reg. UE 2831/2023); polizza contro i rischi catastrofali (L. 213/2023); esclusi i settori del tabacco e le sanzioni interdittive; sede operativa in Lombardia al momento dell'erogazione; rendicontazione entro il 29/02/2028 | pagina; Allegato A, artt. A.3, B.1.c, B.2.b |
| `tema` | `internazionalizzazione` | pagina |
| `qualita` | *vuoto* (lo decide Matteo) | |

**Avvertenza da riportare in `dati`:** la pagina web elenca le esclusioni con ATECO 2007 ("sezione K, attività finanziarie"), il PDF del bando con ATECO 2025 ("sezione L"). Il settore escluso è lo stesso; nella scheda vale la versione del bando ufficiale.

Questo esempio mostra le difficoltà tipiche che la scheda deve gestire: più massimali per tipo di beneficiario, una percentuale che cresce con le maggiorazioni, una scadenza che non è una data, esclusioni di settore invece di un elenco di settori ammessi, pagina e bando che usano versioni diverse dell'ATECO.
