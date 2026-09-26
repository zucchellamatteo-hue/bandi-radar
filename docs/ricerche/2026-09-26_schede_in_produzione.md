# Catena delle schede accesa in produzione e arretrato schedato senza API

**Data:** 26/09/2026, sessione sul VPS (prompt `docs/sessioni/2026-09-26_schede_in_produzione.md`).
**Domanda:** la catena senza IA (deduplica, pagina ufficiale, allegati) funziona sul database vero? E, su richiesta di Matteo, si possono compilare subito le schede dei bandi già raccolti, lasciando l'API ai bandi che arriveranno da qui in avanti?
**Metodo:**
1. In produzione, con i comandi del manuale: `app.schede.bandi` (prima `--prova`), poi `app.schede.pagina_ufficiale` e `app.schede.allegati`. Per non metterci 15 ore, pagina ufficiale e allegati sono stati lanciati con **6 lavoratori in parallelo divisi per sito** (un sito sempre in mano a un solo lavoratore: una richiesta alla volta, 2 secondi di pausa, robots.txt rispettato come sempre). Lo script dei lavoratori era temporaneo (fuori dal repository) e chiamava le funzioni di produzione un bando alla volta.
2. Per ogni bando pronto, un "fascicolo" costruito con **le stesse funzioni di `app/schede/ia.py`**: stesse istruzioni, stesso messaggio, stessi documenti in ordine (prima il bando, niente modulistica), stessi tagli (18.000 caratteri per il controllo preliminare, 150.000 per la scheda).
3. Agenti di Claude Code al posto dell'API: **Haiku** per il controllo preliminare (gruppi da 20), **Sonnet** per la scheda (gruppi da 5-10), con la stessa regola del programma: niente scheda se il bando non è per imprese, è di un'edizione passata, è chiuso o non ha testo.
4. Import nel database con i controlli del programma (`verifica_scheda`, valori ammessi, date e ore valide), come fa `salva_scheda`. Le schede portano `dati.modello` = "claude-code (sessione del 26/09/2026, senza API)" e costo 0; lo stato lo ricalcola il sistema dalle date.

**Limiti:** gli agenti non sono l'API: qualità indicativa, non misurata con un revisore come il 25/09. Il controllo preliminare di Haiku ha sbagliato in modo evidente in un gruppo (11 risposte "file non letto", cancellate e rifatte) e in alcuni casi ha fermato bandi aperti: un incrocio con le date grezze della raccolta ne ha fatti ricontrollare 9 da Sonnet. Il server dei modelli ha limitato le richieste per un'ora circa (errori 429): i lavori interrotti sono stati rimessi in coda e completati.

## Numeri

| Passo | Risultato |
|---|---|
| Deduplica | 1.257 annunci rilevanti → **1.057 bandi**, 79 annunci collegati a un bando esistente, **116 dubbi** per la pagina Doppioni (uguale alla prova sulla copia del 25/09) |
| Pagina ufficiale | **1.003 trovate**, 54 non trovate (nessuna fonte con più di 6: FVG notizie 6, Comune di Siena 6, Valle d'Aosta 5, dati.gov.it 4, Camera di Verona 3). Nessuna regola nuova nel registro: nessun caso abbastanza ripetuto da verificarla |
| Allegati | 1.001 bandi su 1.003; **6.016 file, 2,8 GB** (disco: 55 GB liberi). Categorie: 1.765 modulistica, 864 copie di pagina, 861 decreti, 831 bandi, 394 graduatorie, 186 FAQ, 1.073 altro. Non scaricati: 713 oltre il limite di 30 file per bando, 106 vietati da robots.txt, 47 errori 404, 21 server che chiudono la connessione |
| Controllo preliminare | 1.001 bandi; **613 fermati**: 285 edizioni passate, 179 non per imprese, 97 chiusi, 52 senza testo di bando |
| Schede | **388**: 253 dal bando ufficiale, 109 solo da una sintesi, 26 senza documenti utili; 16 dichiarate "NON PER IMPRESE" |
| Stato calcolato | **183 aperti, 22 in arrivo**, 93 chiusi (edizioni in corso ma già scadute), 90 senza date (sportelli senza scadenza o date non scritte) |
| Aperti o in arrivo, per imprese | **205**: 137 dal bando ufficiale, 68 solo da sintesi |
| Verifica automatica | 100 schede senza segnalazioni, 288 con almeno una. Le più frequenti: campi senza fonte (247), "vincolo ATECO a parole" (112: il settore è scritto nel testo, l'abbinamento dirà "da verificare"), soglie di spesa, età o fatturato a parole |

Tempi misurati: deduplica meno di un minuto; pagina ufficiale circa 6 bandi al minuto per lavoratore; allegati circa 1 bando al minuto per lavoratore (molti file per bando, 2 secondi tra le richieste). Con 6 lavoratori l'intero arretrato ha richiesto circa 25 minuti per le pagine e 1 ora e 45 per gli allegati.

## Cosa è stato corretto strada facendo

- **Allegati**: un link con un nome di sito troppo lungo faceva cadere l'intero bando (Campania, bando 966) e un PDF con caratteri "surrogati" veniva rifiutato dal database (Calabria Europa, bando 548). Ora il link si segna come "indirizzo non valido" e i caratteri si tolgono, come i caratteri nulli. I due bandi prenderanno gli allegati dopo l'unione della PR.
- **Test dei bandi**: cancellavano tutti gli smistamenti, i bandi e gli allegati del database di prova. Ora toccano solo le righe di prova e si saltano se il database contiene annunci veri.
- **Plancia**: una fonte che risponde ma da cui non si è mai letto nulla ha un motivo suo ("controllare la voce del registro").

## Casi da guardare

- **7 schede "aperte" con apertura prima del 2024 e nessuna scadenza** (sportelli): 1 Foncooper, 17 ON Nuove imprese a tasso zero (davvero permanenti), ma 890 (Piemonte efficienza energetica 2016, sportello sospeso nel 2019), 971, 973, 974 (Puglia) e 854 sono probabilmente chiusi. Il sistema non può saperlo dalle date.
- **Documenti di un altro bando nel fascicolo**: 140 (titolo "Gerace Porta del Sole", documenti di "Calabria Scouting") e 331: pagina ufficiale sbagliata, da correggere a mano.
- **PDF illeggibili**: 976 (PIA Piccole Imprese Puglia, testo non estraibile), 975, 331; servirebbe la lettura delle scansioni (non prevista).
- **Pagina ufficiale = home page dell'ente**: 986 (Comune di Perugia), 585 (Camera di Foggia), 494 (Comune di Norbello).
- **Bandi fermati come chiusi dal preliminare che erano aperti**: trovati incrociando le date grezze (per esempio 561 "intelligenza artificiale nelle PMI", scadenza 2027) e rifatti. Chi non ha date grezze non è stato incrociato: qualche bando aperto può essere rimasto senza scheda.

## Sintesi

La catena senza IA regge sul database vero: 1.057 bandi, pagina ufficiale per il 95%, allegati per tutti tranne due (corretti). Le schede dell'arretrato sono state compilate senza API, con gli stessi testi e gli stessi controlli del programma: **205 bandi aperti o in arrivo per imprese hanno ora una scheda**, 137 dal bando ufficiale. Il controllo preliminare con Haiku è il punto debole (qualche risposta non letta, qualche bando aperto fermato): quando l'API sarà accesa conviene che il programma incroci il preliminare con le date già note, come fatto qui a mano. Le segnalazioni della verifica automatica sono le stesse della prova del 25/09 e non bloccano: l'abbinamento tratta i vincoli a parole come "da verificare".

## Conseguenze

- **Nel giro orario della raccolta** (proposta): dopo lo smistamento, deduplica, pagina ufficiale (al massimo 20 bandi per giro) e allegati (al massimo 10), così un'ora di raccolta non si allunga di più di 10-15 minuti. Con 20-40 bandi nuovi al giorno bastano.
- **Controllo preliminare**: aggiungere al programma l'incrocio con le date grezze (un bando con scadenza futura nei dati della fonte non si ferma come "chiuso" senza una seconda lettura).
- **Registro**: nessuna regola `pagina_ufficiale` nuova; da guardare a mano FVG notizie (6 non trovate) e il Comune di Siena (6).
