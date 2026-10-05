# Scheda di un bando lunghissimo, in due passaggi (06/10/2026)

Il bando ha documenti troppo lunghi per un fascicolo (anche oltre un milione di caratteri). Non leggere tutto: lavora
in due passaggi. La cartella è `/tmp/claude-1000/ar/lunghi/<ID>/`.

## Passaggio 1: orientarsi
1. Leggi `istruzioni.md`: sono le istruzioni complete della scheda (formato JSON, campi, valori ammessi, regole) e i dati
   del bando. Valgono tutte, tranne la parte sui documenti, che qui sono nei file.
2. Leggi `indice.md`: un documento per voce, con categoria, dimensione e i titoli e gli articoli con il numero di riga.
3. Decidi quali documenti e quali parti servono. In ordine di importanza:
   - il **bando o avviso in vigore** (l'ultima versione, con le rettifiche: guarda date e "rettifica", "modifica", "D.D.");
   - gli atti che cambiano dotazione, scadenze o regole (decreti, determine, delibere recenti);
   - le **FAQ** più recenti;
   - la pagina web solo per stato e date.
   La modulistica non serve, salvo il modulo di domanda per capire chi può fare domanda.

## Passaggio 2: leggere solo il necessario e scrivere
4. Apri i file `documenti/NN.txt` a pezzi con lo strumento Read (offset e limit sulle righe dell'indice): per ogni campo
   della scheda leggi l'articolo che ne parla (beneficiari, territorio, spese ammissibili, intensità e massimali, durata,
   presentazione delle domande, criteri, erogazione). Puoi usare Grep sul file per trovare parole chiave.
5. Se un bando ha più linee o assi, la scheda deve coprirli tutti (campo `linee`), non solo il primo.
6. Scrivi la scheda in `scheda.json` nella stessa cartella, nel formato chiesto da `istruzioni.md`, con le citazioni
   (`fonti`) copiate dai documenti. Nelle `avvertenze` dì solo ciò che resta davvero incerto: non scrivere più che "il
   testo è tagliato", perché qui il testo è completo.

Regole: usa solo Read, Grep e Write; nessun comando sul database; non modificare altri file. Alla fine rispondi con una
riga: ID, scritta o no, e i dubbi principali.
