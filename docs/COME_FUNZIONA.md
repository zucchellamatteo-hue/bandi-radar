# Come funziona Bandi Radar

*Mappa del sistema per Matteo, scritta il 06/10/2026 leggendo il codice. Va aggiornata quando cambia un pezzo (regola in `CLAUDE.md`). Le modifiche giorno per giorno stanno in `docs/CRONOLOGIA.md`; le decisioni in `docs/PIANO_PROGETTO.md` §10.*

---

## Il percorso di un bando in una pagina

```
 FONTI (≈300 voci in fonti/*.yaml)
   │  ogni ora: raccolta (feed, API, pagine web, browser, sitemap) + "scorta" dei bandi ancora aperti
   ▼
 ANNUNCI  ── "qualcosa di nuovo su una fonte" (anche notizie, gare, concorsi)
   │  smistamento: rilevante / non rilevante / da rivedere
   │  doppioni: più annunci dello stesso bando diventano un solo bando
   ▼
 BANDI
   │  pagina ufficiale dell'ente → documenti (bando, decreti, FAQ, modulistica) → filtro "c'è il bando?"
   │  controllo preliminare (IA): aperto? per chi (imprese, non profit, enti pubblici, persone)? edizione in corso?
   │  scheda (oggi scritta nelle sessioni di Claude Code)
   │  controllo della scheda (senza IA) → se ci sono problemi gravi la scheda non si propone
   ▼
 SCHEDE PROPONIBILI ── catalogo, profili, area impresa, email del lunedì, campagne
   + misure nazionali che si possono sommare (Conto Termico, Iperammortamento, Nuova Sabatini...)
```

Tutto quello che succede dopo la raccolta lo guida il **regista**, una volta all'ora. Le pagine della plancia dove guardare sono: **Fonti** (la raccolta), **Lavorazione** (a che punto sono annunci e bandi, e le schede "Da rivedere"), **Supervisione** (tutti i sistemi automatici e com'è andato l'ultimo giro).

**Chi lavora senza IA e chi con l'IA.** Raccolta, smistamento a regole, doppioni chiari, pagina ufficiale, documenti, filtro, ricontrolli dello stato, controllo delle schede, abbinamento ed email: **senza IA**, quindi senza costo. L'IA (Claude Opus 5.5 con la chiave API e il tetto di spesa) fa solo: smistamento degli annunci incerti, doppioni dubbi, controllo preliminare. Dal 06/10 anche le **schede** si scrivono con l'API (`IA_SCHEDE_API=1`, decisione di Matteo con il tetto a 100 $ al mese); gli agenti nelle sessioni di Claude Code restano per i casi difficili, le verifiche e i rifacimenti.

**Dove gira.** Tutto in Docker sul server OVH (`/srv/bandi-radar`): `db` (Postgres), `app` (sito e plancia), `raccolta` (il servizio che ogni ora raccoglie e fa girare il regista), `caddy` (HTTPS). Il server scarica `main` da GitHub ogni 5 minuti: unire una pull request vuol dire metterla in produzione.

---

## I pezzi, uno per uno

Per ogni pezzo: **cosa fa**, **quando gira**, **dove si vede**, **file principale**, **limiti noti**.

### 1. Raccolta e registro delle fonti

- **Cosa fa.** Legge le fonti del registro (Regioni, Camere di Commercio, Ministeri, Portale UE, Comuni capoluogo, catalogo incentivi.gov.it), ognuna nel modo che il suo sito permette: feed RSS, API, pagine web confrontate con la volta prima, browser senza interfaccia per i siti in JavaScript, sitemap. Salva ogni elemento nuovo come **annuncio**. Rispetta robots.txt e si presenta con lo User-Agent di Bandi Radar. Le fonti con il blocco `scorta` vengono lette anche per intero (tutti i bandi ancora aperti, non solo le novità): gli annunci della scorta non contano come novità. Il lunedì dalle 7 manda a Matteo il riepilogo della settimana.
- **Quando gira.** Ogni ora controlla le fonti "in scadenza" secondo la loro frequenza (giornaliera, tre volte a settimana, settimanale, quindicinale, mensile); la scorta di solito una volta al mese.
- **Dove si vede.** Pagina **Fonti**: semaforo per fonte (verde, giallo per errore o silenzio sospetto, rosso per tre errori o pagina cambiata, grigio in pausa), giorni di silenzio, pulsanti ▶ e ⏸. Pagina **Annunci** per tutto quello che arriva. Pagina **Novità** (una voce per settimana).
- **File principale.** `app/raccolta/esegui.py` (registro: `fonti/*.yaml`, formato in `fonti/README.md`).
- **Limiti noti.** Una dozzina di siti rifiuta gli indirizzi esteri del server (dal PC di Matteo si aprono): un'uscita dall'Italia è ancora da valutare. Il 01/10 40 fonti non avevano mai dato un annuncio: vanno verificate, una fonte silenziosa non è per forza sana. Una fonte che espone solo le ultime 10 notizie può perdere un bando (caso Green Tour del Ministero del Turismo). Il 06/10 è in lavorazione l'aggiunta del Ministero del Lavoro, che mancava.

### 2. Smistamento

- **Cosa fa.** Decide se un annuncio parla di aiuti alle imprese: **rilevante**, **non rilevante** o **da rivedere**. Prima con le parole chiave (gratis), poi gli incerti vanno all'IA. Un segnale di contributo vince sempre su "gara" (alcuni enti mettono i contributi sotto "Bandi di gara"). Gli annunci incerti anche per l'IA vengono mandati avanti come possibili bandi: li fermano poi il filtro sui documenti e il controllo preliminare. Le correzioni di Matteo non vengono mai cambiate.
- **Quando gira.** Ogni ora, primo passo del regista.
- **Dove si vede.** Pagina **Annunci** (filtro per esito, pulsanti ✓ ? ✗ per correggere), **Supervisione** → Smistamento.
- **File principale.** `app/schede/smista.py` (parole in `app/schede/regole_smistamento.yaml`).
- **Limiti noti.** Le parole chiave sbagliano sui casi ambigui (aiuti a famiglie o enti con le stesse parole degli aiuti alle imprese); l'IA corregge, ma un annuncio scartato per errore non arriva mai alla scheda.

### 3. Doppioni

- **Cosa fa.** Lo stesso bando arriva da più fonti (Regione, Camera, catalogo nazionale) e poi con proroghe, rettifiche, graduatorie e FAQ. Il passo dei doppioni collega tutti questi annunci a **un solo bando**. Chiavi in ordine: codice ufficiale del bando, indirizzo della pagina, stesso ente + edizione + titolo. Nei casi dubbi: titoli quasi uguali dello stesso ente → stesso bando; titoli poco simili → bandi diversi; anni o edizioni diversi → non decidono le regole; gli altri all'IA (40 per giro). Un bando già schedato che resta senza annunci non si cancella: viene segnato **"unito a"** il bando principale ed esce da catalogo, profili, area impresa e campagne (06/10).
- **Quando gira.** Ogni ora, nel giro del regista.
- **Dove si vede.** Pagina **Doppioni** (Stesso bando / Bando diverso), pagina dell'annuncio (Unisci allo stesso bando / Separa), avviso "questo bando è un doppione" sulla pagina di un bando unito.
- **File principale.** `app/schede/bandi.py` (sblocco dei dubbi in `app/catena/regista.py`).
- **Limiti noti.** Le pagine elenco che contengono molti bandi (es. Camera di Cuneo) hanno creato doppioni con la stessa pagina: il 06/10 ne sono stati uniti 59 e il controllo delle schede ora segnala "stessa pagina e stesso titolo" come problema grave.

### 4. Pagina ufficiale e documenti

- **Cosa fa.** Per ogni bando cerca la **pagina ufficiale dell'ente** (non la notizia o la scheda di un catalogo), con regole per fonte scritte nel registro (`pagina_ufficiale`). Poi da quella pagina **scarica i documenti**: bando, decreti, FAQ, modulistica, graduatorie; ne legge il testo (con l'OCR per le scansioni) e li ordina per la scheda (prima il bando, la modulistica mai). Conserva anche una copia della pagina. Quando la pagina è una **pagina elenco** con molti bandi, tiene solo i documenti e il testo della sezione di quel bando (06/10, caso Cuneo bando 423). Riconosce anche i link dei siti Liferay senza estensione (06/10, Veneto Metalmeccanica bando 2969). Ogni 14 giorni ricontrolla i documenti dei bandi aperti con la scheda: se ne arrivano di nuovi la scheda va aggiornata.
- **Quando gira.** Ogni ora nel giro del regista: 50 pagine e 25 bandi di documenti per giro. Pagina non trovata: si riprova dopo 14 giorni; errore di rete: il giorno dopo.
- **Dove si vede.** Pagina del bando (Documenti, **pagina ufficiale ↗**), **Lavorazione** (fasi "pagina da cercare", "non trovata", "documenti da scaricare"), **Supervisione** → Pagina ufficiale, Documenti.
- **File principale.** `app/schede/allegati.py` (ricerca della pagina: `app/schede/pagina_ufficiale.py`).
- **Limiti noti.** Limiti di 25 MB per file, 100 MB e 30 file per bando; OCR al massimo su 60 pagine; testo fino a 600.000 caratteri per documento. Quando cambia la regola di una fonte, le pagine non trovate aspettano comunque i 14 giorni. Se un bando non compare sulla pagina elenco condivisa, non riceve documenti.

### 5. Stato dei bandi (aperto, in arrivo, chiuso)

- **Cosa fa.** Lo stato lo calcola il sistema dalle date della scheda, non l'IA. In più, una volta a settimana, per ogni bando proponibile non chiuso riscarica la pagina ufficiale e cerca **nelle righe nuove** frasi come "piattaforma chiusa", "dotazione esaurita", "bando chiuso": se le trova la scheda diventa "da aggiornare". Prima dell'IA, i **segnali di stato** gratuiti (scadenza nei dati della fonte, "Bando chiuso" in testa alla pagina) fermano i bandi chiusi senza spendere.
- **Quando gira.** Stato dalle date: una volta al giorno. Ricontrollo della pagina: nel giro del regista, 10 pagine per giro, ogni bando una volta a settimana.
- **Dove si vede.** Catalogo e pagina del bando (stato); **Supervisione** → Stato dei bandi, Ricontrollo dello stato.
- **File principale.** `app/schede/ricontrollo_stato.py` (stato dalle date: `app/schede/stato.py`; segnali: `app/schede/segnali.py`).
- **Limiti noti.** Una chiusura scritta solo in un documento nuovo (non sulla pagina) si vede con il ricontrollo dei documenti ogni 14 giorni, non subito.

### 6. Filtro "c'è il bando?"

- **Cosa fa.** Guarda i documenti scaricati e decide, senza IA, se c'è **il testo ufficiale del bando**: un documento (PDF, Word) lungo almeno 3.000 caratteri con almeno 5 segni di un regolamento (articoli, beneficiari, spese ammissibili, domanda...). Esiti: **bando**, **sintesi** (solo pagine o notizie), **nessuno**. Solo i "bando" vanno al controllo preliminare e alla scheda; gli altri restano **in disparte** e non si propongono ai clienti (decisione di Matteo del 01/10).
- **Quando gira.** Ogni ora nel giro del regista; si rifà quando arrivano documenti nuovi.
- **Dove si vede.** Pagina del bando (riga Documenti), **Lavorazione** (fasi "in disparte"), **Supervisione** → C'è il bando?, catalogo con il filtro "Anche quelli in disparte".
- **File principale.** `app/schede/documentazione.py`.
- **Limiti noti.** Tarato sulle decisioni già prese dall'IA: riconosce circa il 91% dei bandi veri; circa 250 sintesi passano lo stesso e le ferma il controllo preliminare.

### 7. Controllo preliminare e schede

- **Cosa fa.** Il **controllo preliminare** (IA, Batch API a metà prezzo) chiede: chi può presentare domanda (i **destinatari**: imprese, non profit, enti pubblici, persone fisiche, altri; dal 07/10)? è davvero un'agevolazione (non una gara o un elenco fornitori)? è l'edizione in corso? è aperto? c'è il testo del bando? Legge anche l'inizio del modulo di domanda. "Per imprese" si ricava dai destinatari. Solo se passa si scrive la **scheda**; i bandi **solo per il non profit** (associazioni, ETS, fondazioni, ASD/SSD, cooperative sociali, enti religiosi) passano anche loro ma con **priorità bassa**: in coda dopo quelli per imprese e, finché `SCHEDE_NON_PROFIT=0`, solo nelle sessioni di Claude Code (decisione di Matteo del 07/10, per il budget). La **scheda** ha: campi per l'abbinamento a valori controllati (territorio, soggetti, dimensioni, ATECO, requisiti, con tre stati "vincolo / nessun vincolo / non noto"), sintesi, forma dell'incentivo, linee del bando, i sei blocchi di dettagli per il commercialista (intensità, prestito, vincoli sulle spese, esclusioni, obblighi, domanda), le note sui vincoli e i requisiti dei fornitori (06/10). Ogni modifica conserva la versione precedente. Le schede si scrivono oggi **nelle sessioni di Claude Code** con gli stessi prompt e controlli del programma; i bandi lunghissimi (oltre il testo di un fascicolo) in due passaggi, con un indice dei documenti (06/10).
- **Quando gira.** Controllo preliminare: ogni ora nel giro del regista (lotto Batch, risposta entro 24 ore). Schede: quando Matteo apre una sessione ("fai le schede in attesa"); con `IA_SCHEDE_API=1` le farebbe l'API nel giro orario.
- **Dove si vede.** **Catalogo** e pagina del bando; **Lavorazione** (fasi "controllo preliminare in attesa", "scheda in attesa", "da aggiornare"); **Supervisione** → IA, Sessioni.
- **File principale.** `app/schede/ia.py` (istruzioni della scheda: `app/schede/prompt_scheda.md`; campi ammessi: `app/schede/campi.py`; formato: `docs/SCHEDA_BANDO.md`; strumenti di sessione: `strumenti/sessione/`).
- **Limiti noti.** Finché le schede si fanno in sessione, un bando nuovo aspetta la prossima sessione. Le schede di sessione vanno importate subito: `/tmp` si svuota ai riavvii. Tetto di spesa dell'IA 30 $ al mese (nel programma e sulla Console).

### 8. Controllo delle schede (dal 06/10)

- **Cosa fa.** Senza IA e senza rete, ricontrolla ogni scheda nuova o cambiata con i dati già nel database e salva l'esito in `bandi.controllo`:
  - **gravi** (la scheda potrebbe ingannare il cliente): segnata "bando ufficiale" ma senza il testo del bando tra i documenti; stessa pagina e stesso titolo di un altro bando (possibile doppione); apertura dopo la scadenza; contributo per impresa più alto della dotazione del bando; percentuale fuori scala. **Una scheda con problemi gravi non si propone alle imprese** (catalogo, profili, area impresa, email) finché non è sistemata;
  - **da migliorare**: vincolo segnato senza numeri né spiegazione (regola 21e), requisiti dei fornitori non noti (regola 21f), bando a fasi o con dotazione ripartita senza le linee (regola 21d), pagina condivisa con altri bandi, testo del bando presente ma con un nome poco chiaro.

  In più, il 06/10 è partito un **pilota di verifica con l'IA in sessione**: gli agenti confrontano la scheda con i documenti e citano il bando per ogni problema. Su 19 schede: 14 corrette, 3 con imprecisioni minori, 2 gravi (corrette a mano) che il controllo senza IA non poteva vedere.
- **Quando gira.** Ogni ora, ultimo passo del regista. A mano: `python -m app.schede.controlli [--tutti] [--bando ID]`. La verifica con l'IA: solo in sessione, su richiesta.
- **Dove si vede.** Pagina **Lavorazione**, sezione **Da rivedere** (prima i gravi; casella "solo i gravi"); **Supervisione** → Controllo delle schede.
- **File principale.** `app/schede/controlli.py` (verifica con l'IA: `strumenti/sessione/ar/ISTRUZIONI_VERIFICA_IA.md` ed `esporta_verifica.py`).
- **Limiti noti.** Vede solo errori "di forma" (date, numeri, documenti, campi vuoti): un contenuto sbagliato ma plausibile (bando non per imprese, scadenza letta male) lo trova solo la verifica con l'IA o un revisore. La verifica con l'IA non è ancora automatica e non ha uno strumento di importazione.

### 9. Il regista e la Supervisione

- **Cosa fa.** Ogni ora, dopo la raccolta, porta avanti di un passo ogni annuncio e ogni bando, riprova quelli fermi e sblocca i blocchi. Ordine del giro: smistamento → doppioni → pagina ufficiale → documenti (con ricontrollo ogni 14 giorni e schede da aggiornare per proroghe, rettifiche, chiusure, FAQ) → ricontrollo dello stato → filtro "c'è il bando?" → IA (Batch API) → controllo delle schede. Un passo che fallisce non ferma gli altri; lo stesso passo non gira mai due volte insieme (blocchi nel database). Ogni azione resta in `eventi_catena`.
- **Quando gira.** Ogni ora, nel servizio `raccolta` (`CATENA_AUTOMATICA=0` lo spegne).
- **Situazione dei bandi** (dal 06/10). Ogni bando ha **una sola** situazione, calcolata in un posto solo (vista `bandi_situazione`, migrazioni 028 e 031; nomi in `app/catena/situazione.py`), con il perché accanto (motivo, chi ha deciso: regole, segnali gratuiti, IA, sessione o Matteo; quando). Le voci, in ordine: **unito** (doppione), **per il non profit** (dal 07/10: non per imprese ma per associazioni ed enti; fasi: scheda in coda, scheda fatta, su sintesi, senza testo, chiuso), **fuori target** (solo enti pubblici o persone fisiche, o non è un'agevolazione, anche con scheda; i bandi decisi prima del 07/10 senza destinatari restano qui come "destinatari da determinare" finché non passa `deriva_destinatari.py`), **chiuso con scheda**, **nascosto per errori** (problemi gravi), **proponibile**, **in disparte** (manca il testo ufficiale), **scartato: chiuso** (o edizione passata), **scartato: altro** (nessun testo del bando), **in lavorazione** (con la fase: pagina, documenti, preliminare in coda, scheda in coda). Plancia, revisioni, sessioni e agenti contano i bandi solo da qui: `python -m app.catena.situazione` (conteggi), `--situazione X [--fase Y]` (elenco con i motivi), `--bando N`. Il 06/10 sera: 370 proponibili, 31 nascosti per errori, 1.245 in disparte, 1.034 in lavorazione (791 in coda per il controllo preliminare), 336 chiusi con scheda, 947 scartati chiusi, 271 non per imprese, 102 scartati per altro, 51 uniti.
- **Dove si vede.** **Lavorazione**: in cima il riquadro **Situazione dei bandi** (cliccabile: elenco con il perché, chi ha deciso e quando; collegamento agli scartati); la situazione è anche nella pagina del bando. Sotto, due imbuti (annunci e bandi) con quanti sono fermi in ogni fase e perché, ultime azioni del regista, spesa IA del mese, schede da rivedere. **Supervisione**: tutti i sistemi automatici, cosa fanno, quando girano, ultimo esito, dati; si aggiorna ogni 30 secondi.
- **File principale.** `app/catena/regista.py` (fasi: `app/catena/stato.py`; situazione dei bandi: `app/catena/situazione.py` e vista `bandi_situazione`; elenco dei sistemi: `app/sistemi.py`; dettagli: `docs/ORCHESTRAZIONE.md`).
- **Limiti noti.** Nella plancia non c'è ancora un pulsante per riprovare subito un passo o escludere un bando a mano.

### 10. Misure nazionali e cumulabili

- **Cosa fa.** Elenca le agevolazioni previste dalla legge, sempre aperte finché sono in vigore (non bandi con scadenza): Conto Termico 3.0, Iperammortamento 2026, credito ricerca e sviluppo, credito ZES unica, Nuova Sabatini, e dal 06/10 Art bonus, Ecobonus e Sismabonus per le imprese. Ogni scheda dice a chi si rivolge, cosa si può comprare, quanto vale, come si ottiene, i tempi e se si somma ai bandi. Nelle schede dei bandi il riquadro **"Per gli stessi investimenti si può sommare anche"** indica le misure cumulabili con il beneficio stimato sulla spesa che il bando non copre. Le misure chiuse (credito design 2026, formazione 4.0, innovazione tecnologica, maggiorazioni R&S per il Sud) restano in fondo alla pagina, in grigio, e non si propongono mai.
- **Quando gira.** Non gira: è un file scritto e verificato a mano.
- **Dove si vede.** Pagina **Misure** (per le imprese **Agevolazioni fiscali**), riquadro nella pagina del bando, campagne.
- **File principale.** `app/misure/misure.yaml` (fonti in `docs/ricerche/2026-10-05_misure_nazionali.md`).
- **Limiti noti.** Va aggiornato a mano quando cambia una legge o si esauriscono i fondi. Il beneficio è una stima: le regole sul cumulo vanno controllate caso per caso.

### 11. Abbinamento con le imprese

- **Cosa fa.** Confronta ogni scheda con un profilo d'impresa **anonimo** (codice, sedi, ATECO, forma giuridica, dimensione, requisiti) con regole fisse, senza IA. Per ogni vincolo: rispettato → va bene; non noto o dato mancante → **da verificare**; non rispettato → **escluso**, con il motivo. Una scheda non fatta sul bando ufficiale non è mai "compatibile". Le stesse regole servono ai filtri del catalogo, alla pagina Profili, all'area impresa, all'email settimanale e alle campagne: rispondono sempre allo stesso modo. A parità di livello vengono prima i bandi a fondo perduto. Dal 07/10 un'impresa (o professionista o aspirante) non riceve i bandi che non sono per imprese anche se lo schema lo lascia in dubbio: beneficiari "altro" con un testo "a chi si rivolge" che non parla di imprese, controllo preliminare "incerto" senza imprese tra i beneficiari, titoli "senza scopo di lucro"/"terzo settore", bandi per enti che ammettono le imprese "solo per iniziative senza scopo di lucro"; quelli che tra le imprese ammettono solo le imprese sociali chiedono il requisito "impresa sociale". I bandi **solo per il non profit** (07/10) sono nel catalogo ma li vede solo chi sceglie il filtro **Destinatari: non profit** (o "tutti", o cerca per "ente del Terzo settore"); nell'abbinamento li ricevono solo i profili con soggetto "ente del Terzo settore", mai le imprese.
- **Quando gira.** Al momento, ogni volta che si apre una pagina o si prepara un'email.
- **Dove si vede.** **Catalogo** (filtri "Chi partecipa"), **Profili** (profili di prova), area impresa **I miei bandi**.
- **File principale.** `app/abbinamento/regole.py` (elenco e proponibilità: `app/abbinamento/catalogo.py`; formato del profilo: `docs/PROFILO_IMPRESA.md`).
- **Limiti noti.** Mancano ancora: filtro per comune ed età dell'impresa nel catalogo, conversione ATECO 2007↔2025, stima della percentuale ottenibile. Un bando di un Comune di un'altra regione senza vincolo di sede scritto poteva risultare compatibile: corretto il 05/10 per i bandi ripresi dal catalogo incentivi.gov.it, da tenere d'occhio.

### 12. Area impresa ed email

- **Cosa fa.** Un utente "impresa" descrive la sua attività con un modulo guidato (anche più imprese e più sedi) e vede **I miei bandi**: solo compatibili e da verificare, solo proponibili. Apre una scheda ridotta con l'avvertenza, le misure cumulabili e i documenti; può premere **Richiedi supporto per la domanda** (arriva a Matteo per email e nella pagina Imprese). Ogni lunedì il sistema prepara un'**email per impresa** (dal 07/10, `app/notifiche/email_imprese.py`): poche righe di introduzione, bandi nuovi adatti (mai due volte lo stesso, al massimo 15: compatibili, poi fondo perduto più alto, poi scadenza; gli altri con la riga "Altri N bandi adatti ti aspettano nel tuo portale"), novità sui bandi già segnalati (in scadenza entro 14 giorni, prorogati o con la scadenza cambiata, riaperti, nuovi documenti ufficiali: confronto con `bandi_versioni` e con la data di comparsa dei documenti `allegati.creato_il`), in fondo i bandi segnalati chiusi nell'ultima settimana (un bando chiuso da prima della segnalazione va in Segnalazioni come errore, non nell'email), fino a 3 misure nazionali aggiunte da poco e adatte al profilo (`aggiunta_il` in `app/misure/misure.yaml`), le **news** pubblicate (tabella `news`, pagina **News**, `app/news`), il numero dei bandi adatti con il link all'area impresa e l'invito a chiedere supporto. Ogni novità, misura e news arriva una volta sola (colonna `email_imprese.contenuti`); senza bandi nuovi né novità sui bandi segnalati l'email non parte. La prima email di un'impresa è di **benvenuto** (10 bandi più interessanti tra quelli aperti oggi, niente sezioni sui già segnalati); quando un'email parte, i bandi rimasti fuori per il tetto si segnano "visti nel portale" (`bandi_segnalati.modo = 'portale'`) e non tornano come nuovi. Carattere Outfit dove il programma di posta lo carica. Parte solo dopo l'approvazione di Matteo. Il nome dell'impresa è separato dal profilo e non va mai all'IA. Ogni utente può scaricare i propri dati o cancellare l'account (pagina **Il mio account**). Tutte le email partono da "non-rispondere@" con l'avviso in fondo.
- **Cosa fa.** Un utente "impresa" descrive la sua attività con un modulo guidato (anche più imprese e più sedi) e vede **I miei bandi**: solo compatibili e da verificare, solo proponibili. Dal 07/10 la pagina ha un riepilogo (adatti, da valutare, in scadenza entro 15 giorni, nuovi da 7 giorni), filtri per tipo di agevolazione e scadenza, card per bando in tre gruppi (**adatti**, **potenzialmente applicabili** con il motivo in parole semplici, **di altre regioni**), in ogni gruppo prima il fondo perduto e poi la scadenza, e in fondo le **misure nazionali** adatte al profilo con l'esempio del tipo di impresa più simile (`app/impresa/vista.py`, `misure.per_profilo`). Matteo vede la stessa pagina per qualunque profilo da **Profili** → "Come la vede l'impresa" (`/profili/<codice>/impresa`). Apre una scheda ridotta con l'avvertenza, le misure cumulabili e i documenti; può premere **Richiedi supporto per la domanda** (arriva a Matteo per email e nella pagina Imprese). Ogni lunedì il sistema prepara un'**email per impresa** con i bandi nuovi o in scadenza (mai due volte lo stesso), che parte solo dopo l'approvazione di Matteo. Il nome dell'impresa è separato dal profilo e non va mai all'IA. Ogni utente può scaricare i propri dati o cancellare l'account (pagina **Il mio account**). Tutte le email partono da "non-rispondere@" con l'avviso in fondo.
- **Quando gira.** Area impresa: quando l'impresa entra. Email: preparate il lunedì dalle 7, inviate quando Matteo approva.
- **Dove si vede.** Per l'impresa: **I miei bandi**, **Agevolazioni fiscali**, **Le mie imprese**, **Richieste di supporto**, **Abbonamento**. Per Matteo: pagina **Imprese** (richieste, email da approvare, imprese iscritte).
- **File principale.** `app/impresa/api.py` (email: `app/notifiche/email_imprese.py`; invio: `app/notifiche/email.py`).
- **Limiti noti.** Le email partono solo quando nel `.env` c'è la chiave di Resend; finché manca, inviti e link si copiano a mano. La registrazione libera è spenta (`REGISTRAZIONE_APERTA`): le imprese entrano solo su invito.

### 13. Feedback e revisori

- **Cosa fa.** In fondo a ogni scheda revisori e imprese danno un voto da 1 a 5 ("mi fiderei a proporlo?") e segnalano problemi per categoria (stato, beneficiari, importi, territorio, ATECO, date, documento mancante...). Un giudizio per persona e per versione della scheda. Gli agenti in sessione rileggono i documenti, correggono la scheda (causa "feedback N" nello storico) o respingono, e scrivono una risposta; propongono anche regole nuove per prompt e controlli, che decide Matteo. "Stato sbagliato" fa ricontrollare la pagina ufficiale entro un'ora. I revisori pesano il doppio delle imprese.
- **Quando gira.** Il giudizio quando lo si scrive; la rianalisi quando si apre una sessione.
- **Dove si vede.** Riquadro **Il tuo giudizio** nella pagina del bando; pagina **Feedback** (o **I miei giudizi** per il revisore).
- **File principale.** `app/feedback/api.py` (strumenti: `strumenti/sessione/ar/esporta_feedback.py`, `ISTRUZIONI_FEEDBACK.md`, `importa_feedback.py`).
- **Limiti noti.** La rianalisi non è automatica: le segnalazioni aspettano una sessione.

### 14. Utenti e permessi

- **Cosa fa.** Si entra con email e password. Tre ruoli: **amministratore** (tutto, pagina Utenti e Prossimi passi), **revisore** (solo i permessi spuntati), **impresa** (solo la sua area). Permessi del revisore: `catalogo`, `giudizi`, `lavoro` (tutte le pagine di lavoro in sola lettura), `modifiche` (le azioni), `imprese` (pagine Imprese e Campagne). Inviti con link valido 7 giorni, recupero password valido 2 ore, pausa di 15 minuti dopo 5 password sbagliate. Utente e password del `.env` servono solo a creare il primo amministratore.
- **Quando gira.** A ogni accesso.
- **Dove si vede.** Pagina **Utenti** (solo amministratore); dal server `python -m app.utenti crea/elenco/link/disattiva/attiva`.
- **File principale.** `app/utenti/api.py`.
- **Limiti noti.** Senza Resend l'email d'invito non parte: il link si copia dalla pagina Utenti. Gli utenti non si cancellano dalla pagina Utenti, si toglie l'accesso (l'utente può cancellarsi da solo da Il mio account).

### 15. Abbonamenti, fatture, pagina pubblica e campagne

- **Cosa fa.**
  - **Abbonamenti** con Stripe: prova gratuita, mensile 30 €, annuale 20 €/mese con impegno di 12 mesi, impresa in più 10 €, sede in più 5 € (IVA esclusa). L'admin può rendere gratuito un abbonamento o allungare la prova.
  - **Fattura elettronica**: XML FatturaPA generato da Bandi Radar e inviato allo SdI con Invoicetronic a ogni pagamento.
  - **Pagina pubblica** (landing, 07/10) per chi arriva da Google, dagli annunci e dalle IA: promessa, numeri veri dal database (in memoria 15 minuti), bandi aperti per regione, prezzo di lancio, domande frequenti, bozze dei testi legali. SEO tecnica e GEO: URL canonico dal dominio di `SITO_URL`, `robots.txt` (solo pagine pubbliche), `sitemap.xml`, dati strutturati JSON-LD, `/llms.txt`. Strumenti di Google solo con `GOOGLE_ADS_ID`/`GOOGLE_ANALYTICS_ID` e dopo il consenso (Consent Mode v2 base).
  - **Verifica della proprietà** per Google Search Console e Bing Webmaster Tools: `GOOGLE_SITE_VERIFICATION` e `BING_SITE_VERIFICATION` aggiungono i meta tag nelle pagine pubbliche e nella pagina "/" (anche quando è ancora la pagina d'accesso). Per Google è consigliata la proprietà "Dominio" con un record TXT nel DNS.
  - **Statistiche senza cookie** (07/10, `app/visite`, tabella `visite`, migrazione 033): per le sole pagine pubbliche (/, /blog, /blog/<slug>, /llms.txt, /sitemap.xml, /robots.txt) si conta ogni visita riuscita in una riga per giorno con percorso, dominio di provenienza (solo il dominio del Referer: google.it, chatgpt.com, "diretto"), parametri utm, tipo di visitatore (persona, motore di ricerca, programma IA, altro programma, riconosciuto dallo User-Agent che poi si butta) e conteggio. Niente IP, User-Agent completi, cookie o identificativi; non si contano le visite di chi ha fatto l'accesso. Pagina **Visite** della plancia (permesso "lavoro"): visite per giorno, pagine più viste, provenienze con i motori IA in evidenza, letture dei programmi IA e dei motori pagina per pagina, campagne utm. **Rapporto SEO/GEO** via email a `EMAIL_MATTEO` (`app/notifiche/rapporto_seo.py`, servizio raccolta dalle 7, una volta sola grazie a `notifiche_inviate`, sistema "Rapporto SEO/GEO" in Supervisione): ieri contro il giorno prima e totale 7 giorni (in modalità settimanale: 7 giorni contro i 7 prima), visite di persone e al blog, persone da Google, Bing e motori IA, letture dei programmi IA e dei motori per pagina, nuove imprese registrate, riga di Google Search Console (punto pronto `dati_search_console`, oggi "non ancora collegato"). `RAPPORTO_SEO` = giornaliero (di base), settimanale o spento.
  - **Blog** (07/10) su `/blog` e `/blog/<slug>`: articoli brevi sui bandi e sulle misure più cercati, scritti in bozza dalla pagina **Blog** della plancia (permesso "modifiche") o dalle sessioni (`python -m app.articoli carica FILE.json`), pubblicati solo dall'admin. Tabella `articoli` (migrazione 030), corpo in Markdown semplice convertito in HTML sicuro, FAQ della sezione "Domande frequenti" anche in JSON-LD (Article, FAQPage, BreadcrumbList). Solo i pubblicati vanno in `sitemap.xml` e `/llms.txt`; indicizzabili con `PAGINA_PUBBLICA=1` oppure, landing ancora chiusa, con `BLOG_PUBBLICO=1` (dal 07/10: robots.txt apre solo /blog, /llms.txt, la sitemap e i file delle pagine; la sitemap ha solo il blog; /llms.txt descrive solo blog e articoli, senza prezzi; niente link all'anteprima della landing). Riquadro "Bando chiuso" automatico se il bando collegato (vista `bandi_situazione`) è chiuso o scaduto o la misura non è più aperta; gli archiviati rispondono 410.
  - **Campagne di lancio**: Matteo esporta dal suo database i profili **anonimi** delle imprese (`strumenti/anagrafiche/esporta_profili.py`, la corrispondenza codice → impresa resta sul suo computer), li carica, Bandi Radar li abbina ai bandi aperti e prepara un CSV con la bozza di lettera e i messaggi LinkedIn da mandare a mano.
- **Quando gira.** Abbonamenti e fatture: quando sono accesi, a ogni pagamento (avvisi di Stripe). Campagne: quando Matteo carica un file (analisi in sottofondo, circa 75 secondi per 5.000 imprese).
- **Dove si vede.** Per l'impresa **Abbonamento**; per Matteo pagina **Imprese** (abbonamenti, fatture) e pagina **Campagne**; la presentazione su `/presentazione`; il blog su `/blog` e nella pagina **Blog** della plancia; le visite delle pagine pubbliche nella pagina **Visite**.
- **File principale.** `app/abbonamenti/api.py` (fatture: `app/fatture/api.py`; presentazione: `app/pubblico/landing.py`, SEO: `app/pubblico/seo.py`; blog: `app/articoli/`, `app/pubblico/blog.py`; statistiche: `app/visite/`; campagne: `app/campagne/api.py`).
- **Limiti noti.** Abbonamenti, fatture e pagina pubblica sono **spenti** (`ABBONAMENTI_ATTIVI`, `FATTURE_ATTIVE`, `PAGINA_PUBBLICA` a 0) e Stripe accetta solo chiavi di prova: si accendono dopo le decisioni di Matteo su prezzi, prova gratuita, testi legali (da far rivedere a un professionista) e pagamenti. Le email promozionali non richieste sono vietate anche verso le società: le campagne servono per lettere o per chi ha dato il consenso.

### 16. Prossimi passi

- **Cosa fa.** L'elenco dei promemoria, delle decisioni e dei lavori da sviluppare, con stato, priorità e chi se ne occupa. Le sessioni di Claude Code sul server lo leggono all'inizio e lavorano sui "da sviluppare" in ordine di priorità, poi li segnano "fatto".
- **Quando gira.** Non gira: si legge e si scrive.
- **Dove si vede.** Pagina **Prossimi passi** (la modifica l'amministratore, la legge chi ha "lavoro"); dal server `python -m app.passi`.
- **File principale.** `app/passi/api.py`.
- **Limiti noti.** Funziona solo se le sessioni lo aggiornano davvero a fine lavoro.

### 17. Segnalazioni (pulsante "Segnala")

- **Cosa fa.** In basso a destra di ogni pagina della plancia c'è il pulsante **Segnala**, per tutti quelli che hanno fatto l'accesso (anche le imprese). Si sceglie il tipo (manca un bando, errore in una scheda, stato o scadenza sbagliati, doppione, documenti sbagliati o mancanti, problema della plancia, idea o richiesta, altro), si compilano i due o tre campi del tipo (per "Manca un bando": nome o link) e si scrive un testo libero. La pagina da cui si scrive parte da sola; nella pagina di un bando il suo numero è già scritto. Diverse dai giudizi sulle schede (sezione 13): non serve una scheda, e coprono anche bandi che non ci sono e problemi della plancia.
- **Quando gira.** Non gira: si scrive e si legge. Le sessioni di Claude Code le leggono all'inizio (`python -m app.segnalazioni`) e le chiudono con una risposta (`python -m app.segnalazioni rispondi ID risolta "testo"`).
- **Dove si vede.** Pagina **Segnalazioni** (chi ha "lavoro" la legge, chi ha "modifiche" cambia stato e risposta); i riquadri in alto contano le aperte per tipo, così "Manca un bando" si filtra con un clic. Chi non ha "lavoro" vede le sue segnalazioni e le risposte dal pulsante stesso (**Le mie segnalazioni e le risposte**).
- **File principale.** `app/segnalazioni/api.py` (tipi e campi in `app/segnalazioni/__init__.py`; pulsante `plancia/src/Segnala.tsx`).
- **Limiti noti.** Nessun avviso via email quando arriva una segnalazione o una risposta: si guarda la pagina.

### 18. Guida

- **Cosa fa.** Le istruzioni d'uso della piattaforma, in una sola guida filtrata dal server: ogni sezione dice chi la vede (`tutti`, `admin`, `impresa` o un permesso). L'amministratore vede tutto, l'impresa solo le sezioni scritte per lei.
- **Quando gira.** Quando si apre la pagina.
- **Dove si vede.** Voce **Guida** nel menu, per tutti.
- **File principale.** `app/guida/guida.yaml`.
- **Limiti noti.** Va aggiornata a mano a ogni cambio di pagina o di comando (regola in `CLAUDE.md`).

---

## Gli interruttori nel file `.env` del server

| Interruttore | Cosa accende | Oggi |
|---|---|---|
| `CATENA_AUTOMATICA` | il regista nel giro orario | acceso |
| `ANTHROPIC_API_KEY`, `IA_TETTO_MESE_USD` | l'IA con la chiave API e il tetto mensile | attiva, 100 $ al mese (dal 06/10) |
| `IA_SCHEDE_API` | schede scritte dall'API invece che in sessione | spento |
| `IA_PRELIMINARI_DIRETTI` | controlli preliminari con chiamate dirette (prezzo pieno) | spento |
| `RESEND_API_KEY` | invio delle email | da configurare |
| `EMAIL_IMPRESE_APPROVAZIONE` | email alle imprese solo dopo l'approvazione | acceso |
| `REGISTRAZIONE_APERTA` | registrazione libera delle imprese | spento |
| `ABBONAMENTI_ATTIVI`, `STRIPE_PAGAMENTI_VERI` | abbonamenti e pagamenti veri | spenti |
| `FATTURE_ATTIVE`, `FATTURE_VERE` | fattura elettronica | spente |
| `PAGINA_PUBBLICA` | presentazione su "/" | spenta |
| `BLOG_PUBBLICO` | solo il blog aperto a motori e IA (landing chiusa) | spento finché Matteo non lo accende |
| `GOOGLE_SITE_VERIFICATION`, `BING_SITE_VERIFICATION` | meta tag di verifica di Search Console e Bing | vuoti |
| `RAPPORTO_SEO` | email SEO/GEO a Matteo: giornaliero, settimanale, spento | giornaliero |

Come cambiarli: sezione "Gli interruttori nel file .env" della Guida (solo amministratore). I valori non vanno mai in chat né su GitHub.

## Dove trovare il resto

| Documento | Cosa contiene |
|---|---|
| `docs/PIANO_PROGETTO.md` | obiettivi, fasi, costi e tutte le decisioni (§10) |
| `docs/CRONOLOGIA.md` | cosa è cambiato giorno per giorno |
| `docs/ORCHESTRAZIONE.md` | i passi del regista e le fasi di un bando |
| `docs/SCHEDA_BANDO.md`, `docs/PROFILO_IMPRESA.md` | i campi della scheda e del profilo d'impresa |
| `deploy/MANUALE.md`, `deploy/README.md` | il server: servizi, comandi, manutenzione |
| `fonti/README.md` | come si scrive una voce del registro delle fonti |
| `strumenti/sessione/README.md` | gli strumenti delle sessioni sul server (schede, feedback, verifiche) |
| `docs/ricerche/`, `docs/sessioni/` | mappature, prove, verifiche e piani delle singole sessioni |
| `docs/legale/` | bozze dei documenti legali per la vendita |
