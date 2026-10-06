# Cronologia di Bandi Radar

*Registro delle modifiche giorno per giorno, dall'inizio del progetto. Ricostruito il 06/10/2026 dai messaggi dei commit e delle pull request (#1–#82); da qui in avanti si aggiorna a fine di ogni lavoro (regola in `CLAUDE.md`). Il numero tra parentesi è la pull request. Per come funziona oggi ogni pezzo: `docs/COME_FUNZIONA.md`; per le decisioni con il loro perché: `docs/PIANO_PROGETTO.md` §10.*

---

## Mercoledì 23/09/2026 — Il piano

- Prima bozza del **piano di progetto**: obiettivo, sei moduli (raccolta, schede, abbinamento, plancia, API, cruscotto), fonti, costi, fasi (#1).
- **Decisioni di Matteo**: Bandi Radar nasce autonomo, senza aspettare Contract to Cash (il codice è di Sergio); profili dei clienti anonimi dal suo Postgres; niente IA nelle fasi 0-2, API a consumo dalla fase 3; email con Resend in regione europea; bozze privacy in fase 6.
- Ricerche sulle fonti: le **Province** non pubblicano bandi per imprese (salvo poche eccezioni), i **Comuni capoluogo** sì → si coprono i capoluoghi, non tutti i Comuni. Gli open data dei Comuni non contengono bandi aperti; utili invece l'Anagrafica bandi della Lombardia e i calendari degli avvisi delle Regioni.
- Deciso il **server OVH VPS-2** (acquistato subito, condiviso con altri progetti) e il dominio **qiaro.it** di Matteo. Script di preparazione del server (firewall, Docker, aggiornamento da GitHub ogni 5 minuti, backup notturno).

## Giovedì 24/09/2026 — Fondamenta, raccolta e plancia in un giorno

- Server attivo; un solo indirizzo per tutto: **finanzagevolata.qiaro.it** (#2–#4). Nasce `CLAUDE.md` con le regole di lavoro (#5).
- **Fase 0**: Docker con Postgres, applicazione e Caddy per l'HTTPS (#6); corretta la password del database con caratteri speciali (#7); manuale del server per Matteo (#8).
- **Registro delle fonti**: prima 95 voci (Regioni, enti nazionali, UE), poi completo con **287 voci** (Camere di Commercio, capoluoghi) (#9, #10). Su richiesta di Matteo i filtri del catalogo coincidono con i campi del profilo cliente e il calendario passa da settimane a giorni.
- **Fase 1, raccolta**: lettori di feed, API e pagine HTML, servizio che gira ogni ora (#11); poi browser senza interfaccia, API interne dei siti in JavaScript (Veneto, Sardegna, Bolzano...), sitemap ed **email del lunedì** (#12). Matteo decide di leggere comunque 9 fonti vietate da robots.txt (`ignora_robots`) e Milano con un User-Agent da browser.
- **Fase 2, plancia**: semafori delle fonti, catalogo con filtri, pagina **Novità** settimanale stile blog chiesta da Matteo (#13).
- Fonti verificate dal server: incentivi.gov.it si legge dal suo motore di ricerca interno (5.904 misure) (#14).
- **Fase 3 senza IA**: tabelle di bandi e allegati, smistamento a regole (la parola "gara" non può battere un contributo), scaricamento di documenti e FAQ, correzione a mano dello smistamento dalla plancia, primo formato della scheda (#15).

## Venerdì 25/09/2026 — Prova dell'IA e struttura delle schede

- **Prova dell'IA su dati reali**, senza chiave API: Haiku smista 90 annunci, Sonnet scrive 10 schede, Opus le controlla. L'impianto regge, ma servono tre cambi di struttura prima di collegare l'API (#16).
- **Decisioni di Matteo** (#17): annuncio e bando separati; cercare la pagina ufficiale prima dei documenti; campi di abbinamento a valori controllati.
- Matteo chiede **sei blocchi di dettagli** nella scheda, quelli che guarda un commercialista: intensità e maggiorazioni, prestito e garanzie, vincoli sulle spese, esclusioni, obblighi, domanda (#23).
- **Fonti difficili**: 25 su 44 tornano leggibili; escluse Avellino, Barletta, Provincia di Belluno; alcuni siti bloccano gli indirizzi esteri del server (#24).
- Lavoro sulle tre parti della struttura (unite il 26/09): seconda prova dell'IA con 0 errori gravi nello smistamento e schede senza invenzioni.

## Sabato 26/09/2026 — La catena delle schede in produzione

- **Parte 1**: annuncio e bando separati, deduplica senza IA, pagina **Doppioni** (#18).
- **Parte 2**: pagina ufficiale del bando e documenti per bando, in ordine (#19).
- **Parte 3**: campi della scheda per l'abbinamento con tre stati (vincolo / nessun vincolo / non noto) (#20).
- **Parte 4**: prompt corretti, IA pronta ma spenta senza chiave, tetto di spesa (#21).
- Catena accesa in produzione per la prima volta: 1.057 bandi, 1.003 pagine ufficiali, 6.016 documenti. **Decisione di Matteo**: l'arretrato delle schede lo scrive la sessione di Claude Code (388 schede) (#25, #26).

## Domenica 27/09/2026 — Quanto stiamo perdendo?

- **Valutazione dell'efficacia** su 44 fonti: solo il 22% dei bandi aperti per imprese aveva una scheda; il 45% non veniva raccolto perché si leggevano solo le novità. Opus scrive schede migliori di Sonnet (4,74 contro 3,45). Rapporto in `docs/ricerche/2026-09-27_valutazione_efficacia.md`.

## Lunedì 28/09/2026 — Perimetro completo e Opus 5.5

- **Scorta**: si leggono per intero anche i bandi pubblicati prima e ancora aperti; i bandi raddoppiano (2.487) e si recupera il 78% dei persi del campione. Sezioni nuove nel registro, segnali di stato gratuiti che fermano i bandi chiusi prima dell'IA (#27).
- **Decisione di Matteo**: **Claude Opus 5.5** per smistamento, controllo preliminare e schede, al posto di Haiku e Sonnet (#28).
- Portale UE: il testo del bando si prende dai dati della ricerca, perché la pagina è vuota (#29).
- Catena automatica nel giro orario, con la Batch API a metà prezzo (#30).

## Martedì 29/09/2026 — Catalogo e profili

- Piano della sessione: fine arretrato (1.049 schede), catalogo dei bandi e pagina profilo (#31).
- Lavoro unito il 30/09: OCR per i PDF illeggibili, catalogo con i filtri della scheda, profili anonimi (sotto).

## Mercoledì 30/09/2026 — Abbinamento a regole

- **PDF illeggibili** (font senza tabella dei caratteri, scansioni): si riconoscono e si leggono con l'OCR (#32).
- **Catalogo dei bandi** con i filtri della scheda (chi partecipa, cosa finanzia, quando); gli annunci in una pagina a parte (#33).
- **Profili d'impresa anonimi** e abbinamento a regole nella pagina **Profili**, anticipo della Fase 4 chiesto da Matteo (#34); i "da verificare" in ordine di vicinanza (#35). Una sede "da attivare" fuori regione è da verificare, non compatibile.
- Recuperati 479 bandi senza pagina ufficiale (Bolzano, Trento, Liguria, Veneto, MASE, Padova) (#36); la scheda del catalogo incentivi.gov.it entra tra i documenti come sintesi (#37).

## Giovedì 01/10/2026 — Il regista

- **Decisione di Matteo**: si analizzano e si propongono solo i bandi con il **testo ufficiale** tra i documenti. Nasce il filtro senza IA "c'è il bando?"; le schede fatte su una sintesi restano in disparte (#38).
- **Regista della fase 2** e pagina **Lavorazione**: ogni ora porta avanti annunci e bandi, riprova i fermi, decide i doppioni (regole + IA), segna le schede da aggiornare (#39, #40). Chiave API attiva, tetto 30 $ al mese.
- Pagina **Supervisione**: tutti i sistemi automatici, le loro esecuzioni e i loro dati (#41).

## Venerdì 02/10/2026 — Robustezza e qualità

- Dall'analisi della struttura: blocchi nel database (un passo non gira mai due volte insieme), test automatici su GitHub a ogni pull request, strumenti delle sessioni nel repository (#42).
- Testi lunghi: 600.000 caratteri per documento, 300.000 per la scheda (#43). Le schede con l'API venivano tutte rifiutate per lo schema troppo grande: tolto lo schema vincolato (#44).
- **Decisione di Matteo**: finché il servizio non è venduto **le schede si scrivono in sessione** (`IA_SCHEDE_API=0`); una scheda con l'API arriva a 0,43 $ (#45).
- Plancia in azzurro chiaro, regioni a scelta multipla, titoli e riquadri più evidenti, su richiesta di Matteo (#46–#48). Verifica a campione di 20 schede: 87% dei campi giusti, ma 4 bandi chiusi o non per imprese.
- Nuova sezione della scheda **"Forma dell'incentivo"** chiesta da Matteo (fondo perduto, prestito, servizi, con quota e massimale) (#49, #50).

## Sabato 03/10/2026 — Bandi chiusi e fascicoli completi

- **Ricontrollo settimanale dello stato** sulla pagina ufficiale dei bandi proponibili; i bandi "non per imprese" escono dal catalogo anche con la scheda; il controllo preliminare legge anche il modulo di domanda (#51).
- Fascicoli completi: gli "Allegato B" che sono atti non finiscono più tra la modulistica; ogni documento ha i primi 30.000 caratteri garantiti (#52).
- Istruzioni della scheda: percentuale = intensità base, bandi a più misure, fondi esauriti in evidenza, settori a parole tradotti in ATECO (#53).
- Proposta del **piano delle pratiche** (checklist dei documenti, caricamento, controlli, chat): servono decisioni di Matteo prima di costruirlo (#54).

## Domenica 04/10/2026 — Bandi Radar diventa un prodotto

- Fascicolo della scheda: versioni in vigore prima, testi doppi letti una volta (#55). Risultati della sessione qualità: campi giusti dall'87% al 90% (#56).
- **Decisione di Matteo**: Bandi Radar diventa un **prodotto indipendente**, con utenti veri (admin, revisori, imprese), abbonamenti con Stripe, richiesta di supporto a successo, acquisizione con Google Ads (#57).
- **Utenti e ruoli**: accesso con email e password, inviti, recupero password, revisore in sola lettura (#58).
- **Feedback sulle schede**: voto, segnalazioni, pagina Feedback, rianalisi degli agenti; le date tecniche non creano più versioni nuove della scheda (#59).
- **Area impresa**: profilo guidato, "I miei bandi", richiesta di supporto, email settimanale con approvazione (#60).
- IA a lotti: anche i controlli preliminari con la Batch API, a metà prezzo (#61).
- **Pagina pubblica** di presentazione (spenta) e bozze dei testi legali (#62). **Abbonamenti Stripe** (spenti, solo modalità di prova) (#63).

## Lunedì 05/10/2026 — Permessi, campagne, misure, guida

- **Permessi per utente** (catalogo, giudizi, lavoro, modifiche, imprese) nella pagina Utenti; il revisore amico vede tutto senza toccare (#64). **Decisione di Matteo**: prezzi IVA esclusa; impresa in più 10 €, sede in più 5 €.
- **Campagne di lancio** con i profili anonimi dal database delle anagrafiche; ricerche su success fee, fatturazione e regole del marketing (niente email non richieste, nemmeno alle società); bozze dei documenti legali (#65).
- **Fattura elettronica** (spenta) con Invoicetronic; **misure nazionali** (Conto Termico, Iperammortamento, credito R&S, ZES unica, Nuova Sabatini) con il riquadro "si può sommare con"; prima i bandi a fondo perduto; **success fee decisa** (12/10/8% sul fondo perduto, 2/1,5/1% sul finanziamento, minimo 500 €); messaggi LinkedIn nelle campagne (#66).
- Pagina **Prossimi passi** modificabile e **Guida** filtrata per ruolo (#67). Stripe e fattura elettronica rimandati da Matteo finché il servizio non è pronto per la vendita.
- Email automatiche dal mittente "non-rispondere" con l'avviso in fondo (#68).
- Abbinamento: il catalogo incentivi.gov.it non rende più "nazionale" un bando locale (caso del Comune di Rimini proposto a un'impresa di Milano) (#69).
- Pagina **Il mio account**: scaricare i propri dati e cancellare l'account (#70).

## Martedì 06/10/2026 — Controllo delle schede

- **Bandi uniti** (#71): un doppione già schedato non si cancella ma si segna "unito a" il bando principale ed esce da catalogo, profili, area impresa e campagne. In giornata **uniti 59 doppioni** che avevano la stessa pagina ufficiale; unito anche il doppione di **Green Tour** (bando 2117).
- **Bandi lunghissimi** (#72, #73): scheda in due passaggi, con un indice dei documenti; quattro schede importate (180, 1276, 4160, 4162).
- **Misure chiuse** in fondo alla pagina Misure, in grigio, su richiesta di Matteo: restano visibili per code, scorrimenti o riaperture (#74).
- Catalogo: **ricerca per numero del bando** ("4092", "n. 4092") (#75).
- **Pagine elenco** (segnalazione di Matteo sul bando 423, AI Match Cuneo): quando una pagina contiene molti bandi, si tengono solo i documenti e il testo della **sezione** di quel bando (#76, #77).
- **Regole della scheda** nuove, sempre dal bando 423: **21d** (dotazione ripartita o bando a fasi: spiegarlo nella sintesi e usare le linee), **21e** (ogni vincolo senza numeri spiegato in una nota), **21f** (requisiti dei fornitori mappati con cura e in evidenza nel riquadro "Requisiti dei fornitori") (#76, #78, #79).
- **Controllo delle schede senza IA** nel giro del regista (#80): ogni ora le schede nuove o cambiate vengono ricontrollate (colonna `bandi.controllo`); le schede con **problemi gravi non si propongono** alle imprese finché non sono sistemate; tutte compaiono nella nuova sezione **Da rivedere** della pagina Lavorazione. Riconosciuti i link dei siti **Liferay**: il bando Veneto **Metalmeccanica** (2969) restava senza testo ufficiale.
- **Misure nuove** su richiesta di Matteo: **Art bonus**, **Ecobonus** e **Sismabonus** per le imprese; il bonus barriere 75% no, perché scaduto. Il controllo non segnala più come grave un bando il cui testo c'è ma con un nome poco chiaro (falso allarme su circa 35 bandi) (#81).
- **Pilota del controllo con l'IA in sessione** (#82): gli agenti confrontano la scheda con i documenti e citano il bando. Su 19 schede: 14 corrette, 3 con imprecisioni minori, **2 gravi** corrette a mano, che il controllo senza IA non poteva vedere: il bando **2072 non è per imprese**; il bando **271 scade il 31/12/2026**.
- **In lavorazione**: scheda del **Fondo screening DAE** e aggiunta del **Ministero del Lavoro**, che mancava tra le fonti.
- Documentazione: nascono `docs/COME_FUNZIONA.md` (mappa del sistema) e questa cronologia.
- Green Tour: i doppioni (Camera di Genova, FIRA, Ministero, Invitalia) uniti nel bando 2819 con la pagina Invitalia; il sito del Ministero del Turismo blocca i programmi automatici (protezione anti-robot), quindi i documenti ufficiali sono stati scaricati a mano (nuovo strumento `carica_manuali.py`) e la scheda rifatta: proponibile, scade l'08/10 ore 17. "GreenTour" e "Green Tour" ora sono riconosciuti come lo stesso nome (PR #83).
- Fondo screening - DAE: nuova fonte `lavoro_notizie` (Ministero del Lavoro, PR #83); creato il bando 4407 con avviso e decreti.
- Misure nazionali: esempi pratici per otto tipi di impresa (ufficio, negozio, ristorazione/hotel, artigiano, manifattura, logistica, agricola, startup) nella pagina Misure.
- Supervisione: il sistema "Controllo delle schede" ha ora un nome suo (`controllo_schede`), separato dai controlli delle fonti.

