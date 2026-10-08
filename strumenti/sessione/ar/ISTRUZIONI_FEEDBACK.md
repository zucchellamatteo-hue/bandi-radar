# Istruzioni per gli agenti: chi ha segnalato un errore nella scheda ha ragione? (dal 05/10/2026)

Revisori e imprese leggono le schede dei bandi in bandinQiaro, le votano e segnalano errori. Tu rileggi i documenti
ufficiali del bando e decidi, per ogni problema segnalato, se chi scrive ha ragione; se ha ragione proponi la
correzione. Per ogni segnalazione c'è una cartella `/tmp/claude-1000/ar/feedback/<id>/` con:

- `segnalazione.json`: cosa dice chi scrive: `ruolo` e `peso` (revisore/admin 2, impresa 1), `voto` da 1 a 5,
  `problemi` (`categoria`, `nome` leggibile, `campo` della scheda se indicato, `testo`), `commento`;
  `versione_giudicata` e `versione_attuale` della scheda (se sono diverse, la scheda è cambiata dopo il giudizio:
  il problema potrebbe essere già risolto);
- `scheda.json`: la scheda attuale (`risposta`) più titolo, ente, url, stato, scadenza, chiuso_il del bando;
- `documenti.md`: i documenti del bando (bando ufficiale, decreti, FAQ, modulistica), con nome, url e categoria.

**Strumenti: solo Read e Write.** Niente Bash, niente WebFetch, niente ricerche in rete, nessun comando sul
database: decidi solo dai file della cartella. Non modificare nessun altro file: scrivi soltanto `esito.json`.

## Prima di cominciare

Leggi una volta, per conoscere campi e valori ammessi della scheda:
- `/home/ubuntu/bandi-radar/app/schede/prompt_scheda.md` (regole della scheda e formato JSON di ogni campo);
- `/home/ubuntu/bandi-radar/app/schede/campi.py` (gli elenchi dei valori ammessi: regioni, soggetti, dimensioni,
  tipi di agevolazione, regimi di aiuto, ecc.).

## Per ogni cartella che ti è assegnata

1. Leggi `segnalazione.json` e `scheda.json`.
2. Leggi **per intero** `documenti.md`. Se è lungo, leggilo a pezzi con offset/limit (per esempio 800 righe alla
   volta) fino in fondo: decreti di proroga, chiusure anticipate e FAQ in coda possono cambiare date e importi.
3. Per ogni problema segnalato (e per il commento, se dice qualcosa di preciso) decidi:
   - `si`: i documenti danno ragione a chi segnala;
   - `no`: i documenti dicono quello che c'è già nella scheda, o non dicono nulla che dia ragione a chi segnala;
   - `in_parte`: c'è qualcosa di vero, ma non tutto (spiega cosa).
   Ogni decisione ha la sua **citazione copiata parola per parola da `documenti.md`** (massimo 300 caratteri): la
   frase su cui ti basi. Mai citazioni a memoria o riassunte. Se i documenti non dicono nulla, `citazione` è `null`
   e lo scrivi nella spiegazione.
4. **Conta solo cosa dicono i documenti.** Le segnalazioni dei revisori (peso 2) meritano più attenzione di quelle
   delle imprese (peso 1): rileggi con più cura i passaggi che indicano. Ma un revisore senza riscontro nei documenti
   ha torto, e un'impresa con riscontro ha ragione.
5. Se ha ragione (`si` o `in_parte`), proponi la correzione in `correzioni`: `campo` è il nome di un campo della
   scheda (le chiavi di `risposta` in `scheda.json`, come nel formato di `prompt_scheda.md`), `valore` è il valore
   nuovo **nel formato della scheda**:
   - valori degli elenchi scritti esattamente come in `campi.py` (per esempio `"LOM"`, `"micro"`, `"fondo_perduto"`);
   - date `AAAA-MM-GG`, ore `HH:MM`, importi e percentuali come numeri senza separatori né simboli;
   - il valore **sostituisce tutto il campo**: per un elenco (es. `territorio_regioni`, `codici_ateco`) scrivi
     l'elenco completo corretto, non solo la voce da aggiungere; per un oggetto (es. `intensita`, `vincoli`,
     `forma_incentivo`, `linee`) copia l'oggetto intero da `scheda.json` e cambia solo quello che va cambiato;
   - non si correggono `fonti` e `url`; ogni correzione ha la sua `citazione` dai documenti.
6. **Stato sbagliato (aperto/chiuso).** Il campo stato non esiste nella scheda: lo calcola il sistema dalle date.
   Se il bando è chiuso prima del tempo (fondi esauriti, sportello chiuso, decreto di chiusura) correggi `chiuso_il`
   con la data ISO della chiusura; se la scadenza nella scheda è sbagliata o manca, correggi anche `scadenza`. Se è
   aperto ma la scheda lo fa sembrare chiuso, correggi la data sbagliata (`scadenza`, `chiuso_il` a `null`,
   `data_apertura`). Le formule "fino a esaurimento delle risorse" o "salvo chiusura anticipata" descrivono un bando
   aperto, non chiuso.
7. **Non è per imprese.** Se i beneficiari sono solo enti pubblici, Comuni, scuole, persone fisiche senza impresa o
   enti non commerciali, chi segnala ha ragione: correggi `soggetti_ammessi` (e se serve `a_chi_si_rivolge`) secondo
   i documenti. Cooperative e imprese sociali **sono** imprese.
8. **Documento mancante.** Se il documento indicato non è in `documenti.md` non puoi leggerlo: se senza di esso la
   scheda non sta in piedi, esito `rifare` con il motivo (il sistema cercherà di nuovo i documenti); altrimenti
   `respinto`, spiegando che il documento non è tra quelli raccolti.
9. **Scheda da rifare.** Se gli errori sono tanti o tali che correggere campo per campo non basta (scheda costruita
   sul bando sbagliato, su un'edizione vecchia, sulla sola sintesi mentre ora c'è il bando), esito `rifare` con
   `rifare_motivo` in una frase, e niente correzioni.
10. **Regola.** Se lo stesso tipo di errore può ripetersi su altri bandi (per esempio "le proroghe nelle FAQ non
    vengono lette", "il regime de minimis scambiato per un tipo di agevolazione"), proponi in `regola`, in una
    frase, cosa cambiare nel prompt della scheda o nei controlli automatici. Altrimenti `null`.
11. Scrivi `/tmp/claude-1000/ar/feedback/<id>/esito.json` con **solo** questo oggetto JSON (nessun testo prima o
    dopo, niente blocchi ```, virgolette doppie, niente virgole finali):

```
{"esito": "corretto" | "respinto" | "rifare",
 "risposta": "spiegazione breve e cortese in italiano per chi ha segnalato, senza gergo",
 "problemi": [{"categoria": "...", "ha_ragione": "si|no|in_parte", "spiegazione": "...", "citazione": "..."}],
 "correzioni": [{"campo": "...", "valore": ..., "citazione": "..."}],
 "rifare_motivo": null | "...",
 "regola": null | "..."}
```

- `esito`: `corretto` se proponi almeno una correzione; `respinto` se chi segnala non ha ragione su nulla (o il
  problema è già risolto nella versione attuale: dillo nella risposta); `rifare` come al punto 9.
- `problemi`: uno per ogni problema di `segnalazione.json`, con la stessa `categoria` (valori ammessi:
  `stato_sbagliato`, `non_per_imprese`, `importo_percentuale`, `beneficiari`, `territorio`, `ateco`, `scadenza`,
  `documento_mancante`, `altro`). Per il solo commento usa `altro`.
- `correzioni`: `[]` se l'esito è `respinto` o `rifare`.
- `risposta`: la legge chi ha scritto (un commercialista o un'impresa): grazie, cosa hai controllato, cosa cambia o
  perché non cambia, in due-tre frasi. Niente nomi di campi tecnici, niente JSON.

## Regole

- Un esito per cartella. Se ti sono assegnate più cartelle dello stesso bando, leggi i documenti una volta e
  rispondi a ciascuna nella sua cartella; le correzioni di cartelle diverse non devono contraddirsi.
- Le citazioni devono essere copiate dai documenti, non inventate né riassunte.
- Non cambiare nient'altro: nessun file oltre agli `esito.json`, nessun comando.

Alla fine rispondi con **una sola riga**: `fatto: <N> esiti scritti (corretti X, respinti Y, da rifare Z)` e, se ci
sono stati, `; problemi: <id> <frase>`.
