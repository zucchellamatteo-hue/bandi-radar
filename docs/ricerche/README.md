# Ricerche e mappature

Qui si raccolgono le **mappature manuali** fatte nelle sessioni di Claude Code prima di automatizzare: servono a capire cosa pubblicano davvero le fonti e cosa aspettarsi dal sistema automatico.

## Convenzioni

- Un file per mappatura, nome `AAAA-MM-GG_argomento.md` (es. `2026-09-23_province_capoluoghi.md`).
- In testa: data, domanda a cui si risponde, **metodo** (ricerca web, lettura diretta del sito, dati aperti) e **limiti** (cosa non si è potuto verificare).
- Tabelle con una riga per ente/fonte, con URL riportati **solo se visti davvero** (mai ricostruiti a memoria).
- Ogni riga ha un giudizio esplicito: `sì` / `no` / `non chiaro`, così le mappature si possono confrontare nel tempo.
- Chiusura con una **Sintesi** (5–10 righe) e con le **Conseguenze per il registro delle fonti** (cosa aggiungere, cosa escludere, con quale frequenza).

## Come lanciare una mappatura

In una sessione di Claude Code su questo repository, descrivere la domanda e chiedere di lanciare agenti in parallelo per gruppi di enti (es. per area geografica). Prima di partire, verificare che la rete della sessione raggiunga i siti degli enti: senza accesso diretto gli agenti possono usare solo la ricerca web, che è meno affidabile.

## Indice

| Data | File | Domanda |
|---|---|---|
| 2026-09-23 | `2026-09-23_province_capoluoghi.md` | Province e Comuni capoluogo pubblicano bandi di finanza agevolata per imprese? Parte 1, solo ricerca web |
| 2026-09-23 | `2026-09-23_province_capoluoghi_parte2.md` | Parte 2: aree mancanti e verifica diretta dei capoluoghi di FVG e Lombardia, con lettura dei siti |
| 2026-09-23 | `2026-09-23_open_data_comuni.md` | I Comuni e le Regioni pubblicano i bandi come open data? (catalogo nazionale, ~100 portali comunali, portali regionali) |
| 2026-09-24 | `2026-09-24_regioni_nazionali.md` | Per Regioni, enti nazionali, Portale UE e fondazioni: quale pagina, feed o API osservare? Esiste il calendario art. 49? Lettura diretta dei siti, esito nel registro `fonti/` |
| 2026-09-24 | `2026-09-24_camere_capoluoghi.md` | Per Camere di Commercio, Unioni regionali e Comuni capoluogo: quale pagina, feed o API osservare? Bandi per imprese recenti? Lettura diretta dei siti, esito nel registro `fonti/` |
| 2026-09-24 | `2026-09-24_api_nascoste.md` | I siti a pagina singola (Veneto, Sardegna, Bolzano, Bologna...) hanno un'API interna leggibile senza browser? Osservazione delle chiamate di rete con Chromium |
| 2026-09-24 | `2026-09-24_verifica_dal_server.md` | Le fonti bloccate dal cloud e quelle difficili si leggono dal server? Prove con la raccolta, curl IPv4/IPv6 e Chromium |
| 2026-09-25 | `2026-09-25_fonti_difficili.md` | Le ~44 fonti non verdi (bot manager, connessioni chiuse, myPortal, Camere, "senza novità") si leggono dal server? Raccolta, curl IPv4/IPv6, Chromium, altre porte |
| 2026-09-25 | `2026-09-25_prova_ia.md` | Prima di collegare l'IA: Haiku (smistamento) e Sonnet (schede) su dati reali, rivisti da Opus. La struttura regge? |
| 2026-09-26 | `2026-09-26_schede_in_produzione.md` | Catena senza IA accesa in produzione (deduplica, pagina ufficiale, allegati) e schede dell'arretrato compilate senza API: quanti bandi, quante schede, cosa non va |
| 2026-09-27 | `2026-09-27_valutazione_efficacia.md` | Il sistema e' efficace? 44 fonti stratificate per tipo e tecnologia: esploratore Opus sul sito, Haiku/Sonnet contro Opus, controllore e verifica di riserva. Perimetro, smistamento, preliminare, schede, costi |
| 2026-09-28 | `2026-09-28_perimetro_scorta.md` | Leggendo per intero le fonti (scorta) e aggiungendo le sezioni mancanti, quanti bandi in più entrano? Primo giro in produzione e incrocio con i 193 bandi aperti persi il 27/09 |
| 2026-10-02 | `2026-10-02_verifica_schede.md` | Le schede proponibili dicono il vero? 20 schede aperte a caso confrontate campo per campo con i documenti ufficiali, piu' i controlli automatici su tutte le 683 |
| 2026-10-05 | `2026-10-05_success_fee_concorrenti.md` | Come fanno pagare i consulenti di finanza agevolata la presentazione delle domande (percentuali, concesso o erogato, quando) e quanto costano gli abbonamenti ai bandi? Ricerca web, ~20 operatori |
| 2026-10-05 | `2026-10-05_fatturazione_elettronica.md` | Fattura elettronica per gli abbonamenti Stripe: costruirla o comprarla, quale servizio, quanto costa? Siti ufficiali dei fornitori |
| 2026-10-05 | `2026-10-05_marketing_prospect_regole.md` | Si possono mandare email promozionali alle imprese della mappatura di Matteo? Regole, sanzioni del Garante, canali leciti |
