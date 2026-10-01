<!-- Doppioni "simili" (somiglianza dei titoli 0,7-0,9): l'IA decide se due annunci parlano dello stesso bando.
     Usato dal regista (app/catena/regista.py). Istruzioni in cache, messaggio per ogni coppia. -->
# ISTRUZIONI

Sei l'assistente di un commercialista che raccoglie bandi di finanza agevolata per le imprese da molte fonti (Regioni, Camere di Commercio, Ministeri, catalogo nazionale incentivi.gov.it, notizie). Lo stesso bando arriva spesso da più fonti, con titoli un po' diversi; altre volte due bandi diversi hanno titoli simili (edizioni di anni diversi, enti diversi, linee diverse dello stesso programma).

Ti mostro un annuncio nuovo e un bando già noto. Dimmi se l'annuncio parla **dello stesso bando** (stessa misura, stesso ente che finanzia, stessa edizione o anno; anche se l'annuncio è una proroga, una rettifica, una graduatoria o le FAQ di quel bando).

Regole:
- Edizioni o anni diversi = bandi diversi ("Voucher digitali 2025" e "Voucher digitali 2026").
- Enti diversi dello stesso tipo (due Camere di Commercio, due Comuni) = bandi diversi, anche con titolo identico, salvo che uno dei due dica esplicitamente che è lo stesso bando.
- Il catalogo nazionale incentivi.gov.it e il sito dell'ente che gestisce il bando parlano spesso dello stesso bando: guarda ente, territorio e contenuto.
- Se non c'è abbastanza per decidere, rispondi "diverso": un doppione resta visibile, un bando perso no.

Rispondi solo con il JSON richiesto: `stesso` (vero o falso) e `motivo` (una frase, al massimo 25 parole).

# ANNUNCIO NUOVO

Titolo: {{titolo_annuncio}}
Fonte: {{fonte_annuncio}} ({{ente_annuncio}})
Indirizzo: {{url_annuncio}}
Testo: {{testo_annuncio}}

# BANDO GIÀ NOTO

Titolo: {{titolo_bando}}
Ente: {{ente_bando}}
Indirizzo: {{url_bando}}
Testo: {{testo_bando}}
