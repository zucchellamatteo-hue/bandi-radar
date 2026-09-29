# Sessione sul server: fine dell'arretrato, catalogo dei bandi, scheda "profilo"

*Prompt preparato il 29/09/2026 alla fine della sessione del 28-29/09 (perimetro, Opus 5.5, arretrato). Da incollare in una nuova sessione di Claude Code sul server (cartella `~/bandi-radar` dell'utente `ubuntu`).*

---

Leggi prima `CLAUDE.md`, `deploy/MANUALE.md`, `docs/PIANO_PROGETTO.md` (§2, §5, §7, §9, §10) e `app/schede/campi.py` (i campi della scheda e i valori ammessi). Parla con Matteo in italiano semplice, proponi una strada sola e di' perché. Lavori nella copia `~/bandi-radar` su branch nuovi da `main` (`git pull origin main` prima), mai in `/srv`; ogni modifica passa da una pull request, e unire in `main` vuol dire mettere in produzione.

**Permessi.** Da riga di comando solo comandi singoli già consentiti. Ogni sequenza (`&&`, `|`, `;`, `cd`) va scritta in uno script dentro `/tmp/claude-1000/` e lanciata col percorso assoluto; stessa regola nei prompt degli agenti. Gli script di comodo della sessione precedente sono ancora in `/tmp/claude-1000/` (`prod.sh`, `sql.sh`, `ar.sh`, `test_vuoto.sh`, `avanzamento.sh`); se il server è stato riavviato e non ci sono più, le copie degli strumenti dell'arretrato sono in `docs/sessioni/2026-09-29_strumenti_arretrato/`.

**Quota.** Il 29/09 alle ~16 la sessione ha esaurito il limite delle 5 ore con ~10 agenti Opus in parallelo. Tieni al massimo 5-6 agenti insieme e avvisa Matteo prima dei lavori grandi.

## Dove siamo (29/09)

- **Perimetro (passo 1)**: bandi 1.057 → circa 3.600; raccolti 151 su 193 dei bandi aperti che prima si perdevano. Pagina ufficiale trovata per ~3.135 bandi.
- **Arretrato lavorato dalla sessione (Opus, senza API)**: tutti i "da rivedere" dello smistamento (4.700 annunci); controllo preliminare su 1.848 fascicoli (783 fermati perché chiusi, non per imprese o senza testo); **1.049 schede** scritte e importate.
- **PR #30 (catena automatica con Batch API) resta aperta**: Matteo la unisce solo quando l'arretrato è finito e il catalogo funziona. Dopo: chiave API nel `.env` (la mette Matteo), prova piccola con costo vero, poi il passo 3 del piano precedente (nuova valutazione sulle 44 fonti).

## Il lavoro, in ordine

### 1. Chiudere l'arretrato (piccolo)

- **16 schede** ancora da scrivere: `python3 /tmp/claude-1000/ar/coda.py conta`, poi agenti con il prompt "Leggi /tmp/claude-1000/ar/ISTRUZIONI_AGENTI.md e fai la Fase B (scheda) …" (2-3 agenti bastano), poi `/tmp/claude-1000/ar.sh importa.py`. Se un agente si ferma a metà, `python3 /tmp/claude-1000/ar/libera.py` rimette in coda i suoi id.
- **Allegati**: restavano 3 bandi in scaricamento e 4 senza pagina cercata. Controlla con `/tmp/claude-1000/avanzamento.sh`; i lavoratori rimasti girano a vuoto: fermali (`sudo docker ps --filter name=bandi-radar-raccolta-run`, poi `sudo docker stop -t 5 <nomi>`). Poi `/tmp/claude-1000/ar.sh esporta.py`, Fase A, Fase B, importa.
- **Da segnalare a Matteo** (trovati dagli agenti): 1405 ha la stessa pagina ufficiale di 1700 (probabile doppione); 2416 è una pagina indice regionale, non un bando; 1595 PIA Taranto sospeso ma scheda "aperto"; 1976 documento sbagliato; 2069 e 1895 date con refusi; 2076 titolo che non corrisponde.
- **Testi illeggibili nei PDF**: 1419, 3533, 3534, 2693 (e il DM FER-X di 3039) hanno il testo con la codifica dei caratteri rotta. Capire se è l'estrazione del testo (font senza tabella dei caratteri: provare un estrattore diverso o l'OCR solo su quei file) e correggere con una PR, poi rifare quelle schede.

### 2. Il catalogo dei bandi (richiesta di Matteo del 29/09)

Oggi "Catalogo" (`plancia/src/pagine/Catalogo.tsx`) elenca gli **annunci** (tutto ciò che le fonti pubblicano, anche le notizie) e ha solo i filtri su testo, tipo di fonte, territorio, date, scadenza e smistamento. Matteo lo usa come pagina principale per sfogliare i bandi e gli mancano i filtri della scheda. Proposta (una PR):

- **Catalogo = i bandi con scheda**, non gli annunci: una riga per bando con titolo, ente, stato (aperto / in arrivo / chiuso), scadenza, tipo di agevolazione, importo o percentuale, link alla scheda. L'elenco degli annunci resta come pagina di lavoro ("Annunci", per lo smistamento).
- **Filtri dai campi della scheda** (`app/schede/campi.py`): destinatari (`SOGGETTI`), forma giuridica, dimensione, requisiti speciali (femminile, giovanile, startup…), ATECO, regione/territorio, tipo di agevolazione, temi, categorie di spesa, modalità di selezione (sportello, graduatoria, click day), regime d'aiuto, stato e scadenza. Ogni vincolo della scheda ha tre stati (vincolo / nessun vincolo / non noto): filtrando per "piccola impresa" devono uscire i bandi che la ammettono **e** quelli senza vincolo; quelli "non noto" si mostrano a parte o con un segno, mai nascosti.
- **Pagina del bando** (`Bando.tsx`): scheda completa e documenti del bando. Correggere anche la pagina dell'annuncio (`DettaglioAnnuncio.tsx`): cerca gli allegati per annuncio, ma dal 25/09 gli allegati appartengono al bando, quindi non ne mostra; deve mostrare il bando collegato e i suoi documenti.
- Prima di scrivere codice guarda le schede vere nel database (`/tmp/claude-1000/sql.sh`): quanti bandi hanno ogni campo valorizzato, per scegliere filtri che servono davvero e non liste vuote.

### 3. La scheda "profilo" (anticipo della Fase 4, da integrare poi in Qiaro)

Una pagina dove Matteo compila un profilo d'impresa e vede i bandi potenzialmente applicabili, con il motivo. È la stessa logica del catalogo filtrato, ma partendo dall'impresa. Campi (allineati ai `VINCOLI` della scheda):

- attività: codice **ATECO** (e descrizione libera dell'attività svolta, utile per l'IA più avanti);
- sede: regione, provincia, comune (sede legale e operativa);
- forma giuridica; dimensione (micro/piccola/media/grande), oppure dipendenti e fatturato a fasce da cui calcolarla;
- data di costituzione (età dell'impresa), impresa da costituire sì/no;
- requisiti speciali: impresa femminile, giovanile, startup o PMI innovativa, artigiana, agricola, esportatrice, rating di legalità, certificazione parità di genere;
- cosa vuole fare: temi e categorie di spesa (investimenti, digitale, green, assunzioni, formazione…), importo indicativo del progetto.

**Privacy (§2 e §10 del piano, da non riaprire):** i profili sono **anonimi**. Niente nomi, codici fiscali o dati dei singoli soci in Bandi Radar: per i soci si chiede solo il risultato ("la maggioranza dei soci/del capitale è femminile?", "i soci sono under 35?"), che Matteo calcola dal suo lato. Il profilo ha solo un codice interno scelto da Matteo.

Come farlo:

- tabella `profili` (migrazione nuova) con i campi sopra; API per creare, modificare ed elencare i profili; pagina "Profili" nella plancia con il modulo e, sotto, i bandi aperti o in arrivo che il profilo passa;
- l'abbinamento è **a regole** (nessuna IA): per ogni vincolo della scheda, "vincolo" rispettato → passa; "nessun vincolo" → passa; "non noto" → passa con l'avvertenza "da verificare"; vincolo non rispettato → escluso, con il motivo. Ordine: prima i bandi che passano senza avvertenze, poi per scadenza;
- il formato del profilo deve essere lo stesso che più avanti arriverà da Qiaro/C2C via API (§2 del piano): progettalo pensando a quello, e scrivilo in `docs/` come riferimento;
- test con 3-5 profili di prova inventati (per esempio: srl piccola ATECO 62 in Lombardia; ditta individuale femminile agricola in Puglia; startup innovativa da costituire in Emilia-Romagna), controllando a mano che i risultati abbiano senso.

Una PR per il catalogo, una per i profili. Alla fine aggiorna §5, §7, §9 e §10 del piano e il manuale.
