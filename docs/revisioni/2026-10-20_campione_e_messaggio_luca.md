# Revisione dell'affidabilità del 20/10/2026 — campione e messaggio per Luca

Preparato il 10/10 (PIANO_QUALITA azione 7). Campione: 30 bandi proponibili scelti a caso
(`esporta_verifica.py 30 revisione-20-10`, ordine casuale fisso con il seme "revisione-20-10"), estratto il 10/10 per
dare tempo a Luca. Il 20/10 gli agenti fanno il secondo controllo sugli stessi 30 (la cartella si riesporta con lo
stesso comando e gli stessi id) e il voto è **10 meno la percentuale di schede con errori gravi, divisa per 10**
(es. 2 gravi su 30 = 6,7% → 9,3). Il prodotto è vendibile con due revisioni di fila ≥ 9.

## Il campione

| id | Bando | Ente | Scheda |
|---|---|---|---|
| 338 | Intervento a sostegno della transizione sostenibile delle micro, piccole e medie impr | Camera di Commercio di Firenze | https://bandinqiaro.it/bandi/338 |
| 416 | Bando per la concessione di voucher alle MPMI del settore Turismo per la sicurezza pu | Camera di Commercio del Sud Est Sicilia (Catania, Ragusa, Si | https://bandinqiaro.it/bandi/416 |
| 539 | Bando Voucher Internazionalizzazione - Anno 2026 | Camera di Commercio di Bari | https://bandinqiaro.it/bandi/539 |
| 566 | Tax Credit Librerie 2026 - Credito di imposta per gli esercenti di attività commercia | Ministero della Cultura | https://bandinqiaro.it/bandi/566 |
| 597 | Bando per contributi a fondo perduto a sostegno dei giovani imprenditori operanti sul | Comune di Arona | https://bandinqiaro.it/bandi/597 |
| 774 | Bando Sviluppo Impresa 2026 | Camera di Commercio di Roma | https://bandinqiaro.it/bandi/774 |
| 1227 | Erogazione di finanziamenti agevolati da parte dei confidi | Ministero delle Imprese e del Made in Italy | https://bandinqiaro.it/bandi/1227 |
| 1276 | Avviso Microcredito - PR FESR 2021-2027 (Regione Lombardia) | Regione Lombardia - DG Sviluppo economico | https://bandinqiaro.it/bandi/1276 |
| 1324 | Fondo rotativo regionale per il recupero di aziende in crisi o a rischio di delocaliz | Regione Lazio | https://bandinqiaro.it/bandi/1324 |
| 1452 | Regione Veneto - Fondo di rotazione per la concessione di finanziamenti agevolati Liq | Regione del Veneto | https://bandinqiaro.it/bandi/1452 |
| 1518 | Contratto di insediamento - Attrazione di investimenti in Piemonte - Grandi imprese ( | Regione Piemonte | https://bandinqiaro.it/bandi/1518 |
| 1559 | Investimenti - Linea Impresa efficiente | Regione Lombardia | https://bandinqiaro.it/bandi/1559 |
| 1704 | Aiuti Spazi di Collaborazione - Incentivi per lo sviluppo di servizi innovativi (PR S | Regione Autonoma della Sardegna (PR Sardegna FESR 2021-2027) | https://bandinqiaro.it/bandi/1704 |
| 1726 | Cultura Cresce - PN Cultura 2021-2027, Azione 1.3.1 | Ministero della Cultura - Direzione Generale Creatività Cont | https://bandinqiaro.it/bandi/1726 |
| 1933 | Aiuti alle PMI per gli oneri di gestione delle strutture di proprietà regionale o di | Regione Autonoma Valle d'Aosta | https://bandinqiaro.it/bandi/1933 |
| 2000 | Le Marche per i giovani imprenditori: Start&Innova Giovani – Sostegno alla creazione | Regione Marche | https://bandinqiaro.it/bandi/2000 |
| 2088 | PR FESR Umbria 2021-2027 - Azione 1.1.2 - Avviso Poli di Innovazione 2026 | Regione Umbria - Direzione Sviluppo economico, Agricoltura,  | https://bandinqiaro.it/bandi/2088 |
| 2408 | Bando per le agevolazioni finanziarie alle imprese agricole per il credito di funzion | Regione Lombardia - Direzione Generale Agricoltura, Sovranit | https://bandinqiaro.it/bandi/2408 |
| 2768 | Bando per voucher destinati alle imprese bresciane per la fornitura di servizi relati | Camera di Commercio di Brescia | https://bandinqiaro.it/bandi/2768 |
| 2922 | Bando per contributi alle micro e piccole imprese bresciane per la riduzione dei cons | Camera di Commercio di Brescia | https://bandinqiaro.it/bandi/2922 |
| 2923 | Fiere Italia 2026 - Contributi alle micro PMI per la partecipazione a manifestazioni | Camera di Commercio di Brescia | https://bandinqiaro.it/bandi/2923 |
| 2925 | Bando per contributi a PMI operanti in tutti i settori economici per la formazione e | Camera di Commercio di Brescia | https://bandinqiaro.it/bandi/2925 |
| 2926 | Bando per contributi alle micro, piccole e medie imprese per l'attivazione di percors | Camera di Commercio di Brescia | https://bandinqiaro.it/bandi/2926 |
| 3548 | Avviso di concessione di benefici economici a nuove attività che si insediano nel Cen | Comune di Siena - Direzione Commercio e Statistica | https://bandinqiaro.it/bandi/3548 |
| 4018 | Ri.Circo.Lo. Filiere prioritarie - Risorse Circolari in Lombardia per il sostegno all | Regione Lombardia - Direzione Generale Ambiente e Clima | https://bandinqiaro.it/bandi/4018 |
| 4150 | Dote Impresa Collocamento Mirato - Asse I Incentivi - Provincia di Lodi | Regione Lombardia (Fondo Regionale Disabili, l.r. 13/2003) | https://bandinqiaro.it/bandi/4150 |
| 4156 | Dote Impresa Collocamento Mirato Asse I - Provincia di Sondrio (incentivi all'assunzi | Provincia di Sondrio (risorse del Fondo regionale disabili d | https://bandinqiaro.it/bandi/4156 |
| 4163 | Dote Impresa Collocamento Mirato Asse I - Provincia di Mantova | Regione Lombardia (Fondo Regionale Disabili) | https://bandinqiaro.it/bandi/4163 |
| 4290 | Bando certificazione competenze anno 2026 | Camera di Commercio di Bari | https://bandinqiaro.it/bandi/4290 |
| 4649 | PR FESR Veneto 2021-2027 Azione 2.8.4 - TPL, Sistemi di trasporto intelligenti: bigli | Regione del Veneto | https://bandinqiaro.it/bandi/4649 |

## Messaggio per Luca (da mandare: Matteo)

> Ciao Luca, ti chiedo un aiuto per misurare quanto sono affidabili le schede di bandinQiaro prima di venderlo.
> Ti ho preparato 30 bandi scelti a caso tra quelli che proporremmo ai clienti (elenco qui sotto, ognuno con il suo
> link). Per ciascuno:
>
> 1. entra con il tuo utente e apri il link (oppure cerca il numero nel Catalogo);
> 2. leggi la scheda e, se hai un dubbio, apri il documento del bando dal riquadro "Documenti del bando";
> 3. in fondo alla scheda, nel riquadro **Il tuo giudizio sulla scheda**, rispondi con le stelle a "Mi fiderei a
>    proporlo a un cliente?" (1 no, 2 poco, 3 con controlli, 4 quasi, 5 sì);
> 4. se trovi un errore premi **+ Segnala un problema**, scegli la categoria (stato, non per imprese, importo,
>    beneficiari, territorio, ATECO, date, documento mancante...) e scrivi dove lo dice il bando;
> 5. premi **Salva il giudizio**.
>
> Contano soprattutto gli errori gravi: bando chiuso dato per aperto, non rivolto alle imprese, importi o
> percentuali sbagliati, requisito decisivo mancante. Bastano 3-5 minuti a scheda; se non riesci a farli tutti,
> anche 15-20 vanno bene. Mi servirebbero entro il 19/10. Grazie!
>
> (elenco dei 30 bandi con i link)

## Il 20/10

1. `ar.sh esporta_verifica.py 30 revisione-20-10` (stessi id se i bandi sono ancora proponibili; quelli usciti nel
   frattempo si annotano e si sostituiscono con i successivi dello stesso ordine).
2. 4-5 agenti con `ISTRUZIONI_VERIFICA_IA.md`; poi `applica_verifica.py`, `importa_verifica.py --corrette`.
3. Confronto con i giudizi di Luca (pagina Feedback) e voto in `docs/revisioni/2026-10-20_revisione.md`.
