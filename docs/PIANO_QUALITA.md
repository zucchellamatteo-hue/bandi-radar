# Piano qualità: da 7 a 9 su 10

Deciso con Matteo il 07/10/2026 (obiettivo in `docs/VISIONE.md`: almeno 9/10 prima di vendere). Le azioni si eseguono
**in sequenza**, una alla volta; ogni sessione aggiorna lo stato qui e una riga in `docs/CRONOLOGIA.md`.
Misura di riferimento: errori gravi nelle schede proponibili sotto il 3% (oggi circa 10%: 4 su 39 il 06/10).

| # | Azione | Cosa risolve | Stato | Note |
|---|---|---|---|---|
| 1 | Secondo controllo su ogni scheda proponibile (verifica IA in sessione, `strumenti/sessione/ar/ISTRUZIONI_VERIFICA_IA.md`), correzione subito degli errori gravi | Errori gravi dal ~10% sotto il 3% | **in corso** | Controllate 85 (06-08/10): 11 con errori gravi (~13%), tutti corretti; negli ultimi giri dell'08/10 2 su 31 (~6,5%) (`applica_verifica.py`). Errore più frequente: bando non per imprese segnato per imprese (5 casi), poi importi/percentuali (Nuova Sabatini, 4526), requisiti, documenti di altri bandi, scadenza. Ordine: scadenza più vicina, poi misure nazionali presenti come bando (es. Nuova Sabatini 2516 mostrata come "fondo perduto"). Automatico se la prova Gemini va bene |
| 2 | Testo ufficiale per i bandi "in disparte" (scheda su sola sintesi), prima gli aperti e i famosi | Casi Green Tour, Voucher Cloud | da fare | 1.332 in disparte il 07/10 (vista `bandi_situazione`) |
| 3 | Abbinamento più preciso | Bandi non per imprese proposti; "da verificare" senza motivo | **fatto** (PR 99) | Etichetta "Nuovo" da legare alla prima volta che l'impresa vede il bando |
| 4 | Doppioni ed edizioni mescolate: stessa pagina ufficiale in due schede = problema grave (salvo pagine elenco riconosciute); separare le edizioni vecchie | Bandi doppi, date di anni diversi | da fare | Esempi: 1598/3626, Calabria 1225 |
| 5 | Ricerca settimanale dei bandi più discussi, con controllo che la scheda sia sul testo ufficiale | Non perdere le misure famose | da fare | Primo giro 06/10: 66 misure, 11 assenti |
| 6 | Fonti bloccate: certificati incompleti (MIT, ENEA, ISMEA), anti-robot (MUR, MAECI, Camera di Milano) | Copertura nazionale | da fare | |
| 7 | Misura dell'affidabilità ogni due settimane: 30 schede a caso controllate dall'IA e da Luca, voto nella revisione (`docs/revisioni/`) | Sapere se siamo a 9 | da fare | Prossima revisione 20/10 |
| 8 | Mappare i bandi non profit con priorità bassa (decisione di Matteo del 07/10) | Bandi per associazioni ed enti (ETS, ASD, fondazioni, cooperative sociali) scartati come "non per imprese": Matteo potrebbe vendere servizi anche a loro | **in corso** | Fatto: destinatari nel controllo preliminare, situazioni "per il non profit" e "fuori target" (migrazione 031), filtro Destinatari nel catalogo, schede non profit solo in sessione finché `SCHEDE_NON_PROFIT=0`. Da fare dopo il rilascio: `deriva_destinatari.py` sui bandi già decisi (stima 145 per il non profit, 371 fuori target), poi le 23 schede non profit in coda, dopo quelle per imprese |

Quando il voto misurato al punto 7 è ≥ 9 per due revisioni di fila, il prodotto è pronto per la vendita.
