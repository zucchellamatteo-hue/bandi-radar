# Deduplica senza IA: dagli annunci ai bandi (Parte 1)

**Data:** 25/09/2026, sessione sul VPS.
**Domanda:** quanti bandi veri ci sono dietro i ~1.250 annunci rilevanti, se si riconoscono i doppioni (stesso bando da più fonti) e gli aggiornamenti (proroghe, graduatorie, rettifiche) senza IA?
**Metodo:** `python -m app.schede.bandi` su una **copia** del database di produzione (`pg_dump` verso un Postgres temporaneo in Docker, poi rimosso). Chiavi, in ordine: codice ufficiale (Lombardia `RL...`), indirizzo della pagina ripulito (anche il `link_ente` di incentivi.gov.it), titolo con stesso ente e stessa edizione. Regole in `app/schede/bandi.py`, spiegate in cima al file.

## Numeri

| Voce | Valore |
|---|---|
| Annunci rilevanti | 1.257 |
| Bandi creati | **1.057** |
| Annunci collegati a un bando già esistente | 79 (76 doppioni, 2 graduatorie, 1 rettifica) |
| Collegati per chiave | 48 per titolo, 25 per indirizzo, 6 per codice |
| Bandi con due o più annunci | 59 |
| Dubbi da decidere (restano senza bando) | **116** |
| Aggiornamenti di bandi vecchi senza bando (lasciati stare) | 5 |
| Bandi con solo anni ≤ 2024 nel titolo (archivio) | 153 |
| Bandi con scadenza già passata (dai dati grezzi) | 95 |

Un secondo giro subito dopo non cambia nulla: il comando si può rilanciare a ogni raccolta.

**Rispetto alla stima di Opus (circa 500 schede).** La deduplica da sola toglie poco: meno del 10%. Il grosso della riduzione stimata da Opus non viene dai doppioni ma dai bandi **chiusi o d'archivio** (almeno 153 + 95, probabilmente di più: molti titoli non hanno anno né scadenza nei dati grezzi) e dalle pagine che non sono un bando. Quelli li fermeranno il passo "pagina ufficiale" (Parte 2) e il controllo preliminare con Haiku (Parte 4). Stima aggiornata: circa 800 bandi attuali, e dopo il controllo preliminare 500-600 schede da far scrivere a Sonnet.

Ci sono anche falsi rilevanti che diventano "bandi": pagine elenco con titoli come "Bandi e contributi camerali", "Opportunità di finanziamento", "Portale Agevolazioni". Sono errori dello smistamento. Li fermerà la Parte 2 ("pagina che non contiene un bando").

## 20 doppioni trovati

| Annuncio | Stesso bando di | Chiave |
|---|---|---|
| 2586 Lombardia Bandi Online: PR FESR Azione 1.3.1 fiere (pagina di dettaglio) | 2623 Anagrafica bandi Lombardia | codice RLO12026055023 |
| 2587 Lombardia Bandi Online: stesso bando (pagina di domanda con login) | 2623 | codice RLO12026055023 |
| 2588 e 2589 Lombardia: Misura qualificazione imprese per le filiere | 2625 Anagrafica | codice RLO12026054663 |
| 4196 incentivi.gov.it: CCIAA Marche, Bando Internazionalizzazione 2026 | 644 Camera delle Marche | indirizzo (link all'ente) |
| 4334 incentivi.gov.it: CCIAA Cosenza, nuove imprese IV edizione | 880 Camera di Cosenza | indirizzo |
| 4311 incentivi.gov.it: CCIAA Ferrara Ravenna, accesso al credito | 544 Camera di Ferrara Ravenna | indirizzo |
| 851 Camera di Foggia: Doppia Transizione 2026 | 4345 incentivi.gov.it | indirizzo |
| 258 Unioncamere Lombardia: Export su Misura 2026 | 2585 Regione Lombardia | indirizzo |
| 492 Camera di Bologna: Voucher Doppia Transizione 2026 | 4303 incentivi.gov.it | indirizzo |
| 753 Camera di Caserta (pagina bandi): Voucher Doppia Transizione 2026 | 820 Camera di Caserta (feed) | indirizzo |
| 3259 Valle d'Aosta: Bando Ricerca 2026 | 4207 incentivi.gov.it | titolo |
| 4371 incentivi.gov.it: CCIAA Como-Lecco, Fiere internazionali all'estero 2026 | 97 Camera di Como-Lecco | titolo |
| 497 Camera di Bologna: Ristori per disagi da grandi cantieri | 4302 incentivi.gov.it | titolo |
| 93, 95, 103, 104 Camera di Como-Lecco (lo stesso bando in 4 sezioni del sito) | 97 | titolo |
| 2856 Emilia-Romagna: produzione opere cinematografiche 2020 (pagina "-1") | 2857 | titolo |
| 331 Camera di Treviso-Belluno: **esiti** del bando doppia transizione | 321 | titolo, ruolo graduatoria |
| 1200 Roma Capitale: Casa delle Tecnologie Emergenti, **graduatoria** | 1207 | titolo, ruolo graduatoria |
| 2327 Comune di Palermo: **rettifica** avviso Made in Sicily Fest | 2341 | titolo, ruolo rettifica |

## 10 dubbi (restano da decidere nella pagina Doppioni)

| Annuncio | Bando candidato | Perché è dubbio |
|---|---|---|
| 522 Camera di Modena: Bando UCER Digital Export 2026-2027 | 2807 Emilia-Romagna: Digital Export 2026-2027 | enti diversi, titolo simile (0,67): probabilmente sì |
| 217 e 241 Camera di Varese: Voucher formazione continua IV edizione | 2642 Anagrafica Lombardia: Formazione Continua quarta edizione | enti diversi, titolo quasi uguale (0,90): probabilmente sì |
| 845 Camera di Brindisi-Taranto: Bando Start-up 2025 | 857 Camera di Foggia: Bando Start-up 2025 | due Camere, stesso nome: quasi certamente no |
| 3425 Lazio Innova: Voucher Digitalizzazione PMI 2026 | 3396 Regione Lazio | gestore e Regione: probabilmente sì |
| 456 Camera di Bologna: "Portale Agevolazioni" | 538 Camera dell'Emilia: "Portale Agevolazioni" | pagine generiche, non bandi |
| 2890 Emilia-Romagna: sostegno alla produzione di opere cinematografiche, bando rivolto a... | 2861 Emilia-Romagna, stesso programma | stessa fonte, titolo simile (0,80): destinatari diversi, quindi no |
| 3015 Finpiemonte: Fondo unico Competitività, plafond Artigianato | 3005 Finpiemonte, stesso titolo | due linee dello stesso fondo |
| 2596 Anagrafica Lombardia: RI.CIRCO.LO. filiere prioritarie | 146 Camera di Sondrio: economia circolare 2022 | no (edizioni diverse) |
| 1203 Roma Capitale: avviso contributi a sportello | nessuno | proroga di cui non si trova il bando |
| 1514 Comune di Genova: Fiera di Cornigliano 2026, graduatoria | nessuno | graduatoria di cui non si trova il bando (e comunque posteggi, non un bando per imprese) |

## Cosa ne esce

- Le chiavi sicure (codice e indirizzo) non sbagliano nei casi visti. Il titolo sbaglia se due bandi diversi hanno lo stesso nome: per questo con enti diversi si chiede sempre, e due Camere diverse sono doppioni solo se il titolo è identico.
- I dubbi (116) sono tanti per Matteo, ma sono il lavoro giusto per Haiku ("stesso bando? sì/no", pochi centesimi in tutto). Fino ad allora restano nella pagina Doppioni.
- La Parte 2 aggiungerà l'indirizzo della **pagina ufficiale** come chiave: molti doppioni per titolo diventeranno doppioni per indirizzo, più sicuri.

Nota: un dubbio visto nel primo giro (Comune di Rimini contro un bando di Regione Lombardia dal catalogo nazionale) è sparito correggendo la regola: se nel catalogo il gestore è una Regione, il territorio è quella Regione, anche quando il catalogo elenca tutte le regioni.
