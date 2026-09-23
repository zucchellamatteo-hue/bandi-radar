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
| 2026-09-23 | `2026-09-23_province_capoluoghi.md` | Province e Comuni capoluogo pubblicano bandi di finanza agevolata per imprese? (parziale, solo ricerca web) |
