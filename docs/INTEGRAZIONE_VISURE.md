# Integrazione con visure-parser (lettura della visura camerale)

*07/10/2026. Risposte di visure-parser alla ricognizione (preparata da Bandi Radar, vedi `~/INFRA_VPS.md` §8 e §8bis sul server) e posizione di Bandi Radar sui punti aperti. Uso previsto: onboarding dell'area impresa (tappa 3 di `docs/sessioni/2026-10-05_prodotto_indipendente.md`). L'impresa carica la visura su Bandi Radar, Bandi Radar la passa a visure-parser sulla rete Docker interna e il profilo si precompila in attesa della conferma dell'impresa.*

## Cosa garantisce visure-parser (risposte del 07/10)

| Tema | Risposta |
|---|---|
| IA | La lettura è deterministica (pdfplumber + regole), senza IA. Un modulo facoltativo riassume oggetto sociale e poteri: acceso solo con la **pseudonimizzazione** (nomi, codici fiscali, partite IVA, denominazione, indirizzi, PEC sostituiti da segnaposto, con test), con API a pagamento e accordo sul trattamento dei dati (nessun addestramento), possibilmente in UE. Finché la pseudonimizzazione non è pronta resta spento. La regola di Bandi Radar "all'IA non arriva nulla che identifichi un cliente" è rispettata. |
| PDF | Non conservato: letto in memoria e scartato; resta un'impronta SHA-256 per i doppioni. |
| Dati estratti | Conservati (registri pubblici, storico): dati delle persone cifrati nel database, backup cifrati anche fuori dal server, ogni scheda legata al servizio che l'ha caricata (Bandi Radar vede solo le sue), registro degli accessi, niente dati personali nei log, cancellazione o rettifica con un endpoint. **Bandi Radar deve citare questo trattamento nella sua informativa.** |
| Rete | Rete Docker `servizi_interni`, alias `visure-api`. **Dentro i container l'API ascolta sulla 8000**; la 8010 è solo la porta pubblicata su 127.0.0.1. |
| Autenticazione | `X-API-Key: <VISURE_API_KEY>`, una chiave per servizio chiamante, revocabile. |
| Endpoint | `POST /api/v1/schede` (PDF multipart, campo `file`; 202 con `id` e `in_elaborazione`, oppure con `?attendi=30` 200 con la scheda se finisce in tempo) · `GET /api/v1/schede/{id}` (stato e scheda) · `DELETE /api/v1/schede/{id}` (scheda e dati delle persone) · `GET /health`. |
| Errori e tempi | 401 chiave · 413 oltre 20 MB · 415 non PDF · 422 PDF senza testo o non una visura. Una visura tipica 5-20 s, le lunghissime fino a 2 minuti. |
| Scheda | Ogni campo è `{valore, affidabilita: alta|media|bassa, nota}`: anagrafica, sede legale, unità locali, ATECO principale e secondari con versione, addetti con data, soci, amministratori, requisiti femminile/giovanile con i valori aggregati, controlli di quadratura. Già provata su 34 visure reali per l'anagrafica; da aggiungere chiavi API, endpoint con stato, data inizio attività, ATECO secondari con versione, addetti con data, affidabilità per campo, femminile/giovanile, cifratura, separazione per servizio, pseudonimizzazione, rete condivisa. |

## La posizione di Bandi Radar

1. **Porta: nessun cambio a visure-parser.** Bandi Radar chiama `http://visure-api:8000`. L'indirizzo sta in una variabile (`VISURE_URL`) del `.env` dei bandi, così una porta diversa in futuro è una riga di configurazione. La chiave va in `VISURE_API_KEY`, sempre e solo nel `.env` (il repository dei bandi è pubblico).
2. **Chiamata.** `POST ?attendi=30`; se arriva il 202, Bandi Radar richiede lo stato ogni 5 secondi fino a 3 minuti, e intanto all'impresa mostra "stiamo leggendo la visura". Limite del caricamento anche lato bandi: 20 MB, solo PDF. Errori tradotti per l'impresa: 415/422 → "il file non sembra una visura camerale leggibile: scarica la visura in PDF dal Registro Imprese" (nessuna scansione); 413 → "file troppo grande"; 401 o servizio giù → l'impresa compila il profilo a mano, Matteo riceve un avviso.
3. **Minimizzazione: Bandi Radar non vuole i dati delle persone.** Per abbinare i bandi bastano gli aggregati. **Richiesta a visure-parser**: un parametro (per esempio `?senza_persone=1`) che restituisca la scheda senza nomi e codici fiscali di soci e amministratori, solo con quote e cariche aggregate e l'esito femminile/giovanile. Così Bandi Radar non riceve né conserva dati di persone. Finché il parametro non c'è, Bandi Radar scarta quei campi appena li riceve e non li scrive mai nel database né nei log.
4. **Cosa conserva Bandi Radar.** Nelle tabelle dei clienti (separate dal profilo di abbinamento): denominazione, codice fiscale e partita IVA, PEC e sede legale (servono per l'account e la fatturazione) e l'`id` della scheda di visure-parser. Nel profilo: forma giuridica, sedi (legale e unità locali **attive**, solo comune e provincia), ATECO, data di costituzione, addetti, femminile/giovanile (esito e percentuali aggregate). Nessun dato di persone.
5. **Cancellazione.** Quando un'impresa chiude l'account o chiede la cancellazione, Bandi Radar chiama `DELETE /api/v1/schede/{id}` e cancella i suoi dati. Va scritto nell'informativa e nei termini.
6. **Affidabilità per campo.** Nel modulo di conferma i campi `alta` arrivano già compilati; quelli `media` o `bassa` (per esempio ATECO secondari, data di inizio attività, addetti) sono evidenziati da confermare. Il profilo vale solo dopo la conferma dell'impresa.

## Dalla scheda della visura al profilo (`docs/PROFILO_IMPRESA.md`)

| Scheda di visure-parser | Profilo di Bandi Radar | Regola |
|---|---|---|
| `impresa.forma_giuridica` (testo) | `forma_giuridica` | Conversione in Bandi Radar verso `FORME_GIURIDICHE` (`app/schede/campi.py`): "societa' a responsabilita' limitata" → `srl`, "...semplificata" → `srls`, "societa' per azioni" → `spa`, "societa' in nome collettivo" → `snc`, "societa' in accomandita semplice" → `sas`, "impresa individuale" → `ditta_individuale`, "societa' cooperativa" → `cooperativa`, "consorzio" → `consorzio`; il resto `altro`, da confermare. |
| `sede_legale`, `unita_locali` (attive) | `sedi` | Sede legale come `legale` (o `legale_e_operativa` se l'impresa lo conferma); ogni unità locale attiva come `operativa`; regione dalla provincia. Le unità cessate non entrano. |
| `ateco.principale`, `ateco.secondari` | `ateco`, `ateco_versione` | Principale per primo; i secondari (affidabilità media) da confermare. |
| `data_costituzione` | `data_costituzione` | Età dell'impresa. |
| `addetti.numero` | `dipendenti` | Gli addetti della visura non sono le ULA: servono a stimare la dimensione, che l'impresa conferma con fatturato e totale di bilancio (la visura non li ha). |
| `requisiti.impresa_femminile`, `impresa_giovanile` | `requisiti.femminile`, `requisiti.giovanile` | `si` → vero, `no` → falso, `incerto` → chiave assente ("non lo so": i bandi che la chiedono restano "da verificare"). Le percentuali aggregate si conservano per riapplicare soglie diverse da bando a bando. |
| `stato_attivita` | — | Se non è `attiva`, avviso all'impresa prima di proseguire. |
| soci, amministratori, capitale, REA | — | Non servono all'abbinamento: non si conservano. |

## Regola standard femminile e giovanile (proposta, decide Matteo)

Proposta, sulle definizioni più usate dai bandi nazionali (per esempio il Fondo impresa femminile):
- **femminile**: ditta individuale di una donna; società di persone e cooperative con almeno il 60% dei soci donne; società di capitali con almeno 2/3 delle quote **e** 2/3 degli amministratori donne;
- **giovanile**: stesse soglie con persone **sotto i 36 anni** alla data della visura (alcuni bandi usano i 35: per questo si conservano le percentuali e Bandi Radar riapplica la soglia del singolo bando).

`incerto` quando tra i soci ci sono società o persone senza codice fiscale italiano, come proposto da visure-parser.

## Prossimi passi (Batch 1)

- **visure-parser**: chiavi API, endpoint con stato, parametro senza persone, regola standard dopo la decisione di Matteo, rete `servizi_interni` con alias `visure-api`.
- **Bandi Radar** (con la tappa 3, area impresa): rete `servizi_interni` come `external: true` per `app`; `VISURE_URL` e `VISURE_API_KEY` in `deploy/env.example` senza valori; caricamento della visura nell'onboarding con conversione e modulo di conferma; chiamata a `DELETE` alla chiusura dell'account; informativa privacy aggiornata.
- **Decisioni di Matteo**: la regola standard femminile/giovanile (sopra) e se l'impresa può saltare la visura e compilare tutto a mano (proposta: sì).
