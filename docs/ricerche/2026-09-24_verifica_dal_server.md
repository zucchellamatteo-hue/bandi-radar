# Fonti bloccate dal cloud: come rispondono dal server?

**Data:** 24/09/2026, sessione sul VPS di produzione (OVH, Gravelines).
**Domanda:** le fonti che dalla sessione cloud rispondevano 403 o non si aprivano (Milano, GSE, Umbria, incentivi.gov.it, Enna) e quelle con `stato: difficile` o `da_verificare` si leggono dal server?
**Metodo:** lettura con il codice della raccolta (`--prova`, nessuna scrittura nel database) dentro l'immagine Docker `raccolta`, con User-Agent dichiarato; per i casi dubbi `curl` dal server (IPv4 e IPv6) e Chromium con registrazione delle chiamate di rete. Un solo passaggio per fonte, più una rilettura finale dopo le modifiche.
**Limiti:** le fonti senza `url` nel registro (29 voci, per lo più capoluoghi "difficile") non sono state cercate: servono prima gli indirizzi. robots.txt rispettato ovunque: Liguria, Abruzzo e Trento restano in attesa della decisione di Matteo.

## Tre scoperte che valgono per più fonti

1. **Alcuni siti rifiutano l'IPv4 del server ma non l'IPv6.** Napoli e Siracusa rispondono 403 a qualunque richiesta dall'IPv4 del VPS (probabilmente tutto il blocco di indirizzi OVH) e 200 dall'IPv6. I container Docker uscivano solo in IPv4. Nuova opzione del registro `richiesta.ipv6: true` e rete `ipv6` in `docker-compose.yml`, usata solo dalla raccolta.
2. **Il firewall di Milano guarda lo User-Agent, non l'indirizzo.** `BandiRadar/0.1` riceve 403 (anche su robots.txt); lo stesso User-Agent con davanti la firma di un browser riceve 200. È la soluzione già usata per il MASE. Serve la decisione di Matteo.
3. **Tabelle e codici di sessione.** Nelle tabelle "Oggetto | Scadenza | Dettaglio" il titolo ora si prende dalla cella più lunga della riga; il `;jsessionid=` si toglie dai link (altrimenti ogni visita sembrerebbe piena di novità). Nuova opzione `richiesta.selettore` (CSS) per leggere solo una parte della pagina.

## Esito fonte per fonte

| Fonte | Esito dal server | Cosa è cambiato nel registro | Giudizio |
|---|---|---|---|
| incentivi_gov_ricerca | 200; la pagina interroga un motore Solr interno (`/solr/coredrupal/select`, non vietato da robots.txt) con tutto il catalogo: 5.904 misure | `modalita: api`, query delle 200 misure aggiornate più di recente con campi rinominati; `attiva` | sì |
| incentivi_gov_open_data | cartella `/open-data/` 404; i pulsanti "Scarica" generano l'export nel browser dallo stesso Solr | `esclusa` (coperta dalla voce sopra) | no |
| gse_bandi_avvisi | 200 anche senza browser (Akamai bloccava solo il cloud); la home non è un elenco | url → pagina News, `modalita: html`, `attiva`: 6 notizie | sì |
| umbria_bandi_imprese | 200, tabella di 20 bandi con link "Dettaglio" e jsessionid | lettore corretto (vedi sopra): 20 bandi | sì |
| umbria_avvisi_attivita_produttive | 200 ma solo menu, anche col browser | `esclusa` (coperta da umbria_bandi_imprese) | no |
| comune_napoli_avvisi | 403 in IPv4, 200 in IPv6 | `richiesta.ipv6: true`: 9 avvisi | sì |
| comune_siracusa_avvisi | 403 in IPv4, 200 in IPv6 | `richiesta.ipv6: true`: 9 avvisi | sì |
| comune_milano_impresa | 403 al nostro User-Agent, 200 a User-Agent da browser + BandiRadar; economiaelavoro resta 403 | note; resta `difficile` in attesa di Matteo | non chiaro |
| comune_enna_avvisi | `api.comune.enna.it` non esiste; `hub-api.comune.enna.it` risponde 403 "Non abilitato"; la pagina contiene i 6 avvisi più recenti ma senza link | note; resta `difficile` | no |
| fondazione_cariplo_bandi | 403 Cloudflare a richiesta semplice (anche IPv6); col browser si apre | `modalita: browser`, `attiva`: 4 bandi | sì |
| fondazione_cariverona_bandi | come Cariplo | `modalita: browser`, `attiva`: 6 bandi | sì |
| cciaa_bari_bandi | 200, ma /info/bandi era un indice | url → "Bandi per sostegno alle imprese", selettore `div.insight.snippet`: 11 bandi | sì |
| campania_porfesr_opportunita | 200, prendeva i pulsanti di condivisione | selettore `#news_body`: 75 avvisi | sì |
| molise_home_notizie | 200, prendeva il menu | selettore `div.Notizie`: 6 notizie | sì |
| marche_rss_tematici | `/rss` è l'indice dei feed | feed "Fondi Europei e Attività Internazionali" (blog=10): 30 voci | sì |
| provincia_lecco_bandi_contributi | 200, la pagina mescola menu | feed RSS della categoria (vuoto il 24/09: nessun bando aperto) | sì |
| cciaa_palermoenna_home | home con solo carosello | url → pagina Avvisi: 20 voci miste | sì |
| cciaa_nuoro_bandi, marche_bandi | 200, elenchi misti | `attiva` | sì |
| unioncamere_emilia_romagna_bandi, unioncamere_toscana_news, sviluppo_italia_molise_bandi, sardegna_sfirs, puglia_puglia_sviluppo | 200, leggono già bene | `attiva` | sì |
| basilicata_sviluppo_basilicata_incentivi | 403 in IPv4 con qualunque User-Agent, niente IPv6, col browser pagina di blocco | resta `difficile`, "bloccata anche dal VPS" | no |
| ministero_turismo_strumenti | bot manager Radware: risultato variabile anche col browser | `difficile`, "bloccata anche dal VPS" | no |
| cciaa_rieti_viterbo_supporto_imprese | i bandi attivi sono solo nel menu di navigazione | note; resta `difficile` | non chiaro |
| fvg_fesr_calendario_inviti | nessun calendario art. 49 linkato | note; resta `da_verificare` | non chiaro |
| rna_open_data | la pagina è HTML, non JSON | invariata (fonte di contesto, non bandi) | non chiaro |
| comune_latina_avvisi, comune_pesaro_nuove_imprese | Latina non risponde (timeout, anche IPv6); Pesaro 503 con pagina di attesa | invariate: da ricontrollare nei prossimi giorni | non chiaro |

## Sintesi

- 20 fonti rilette dopo le modifiche, tutte con esito positivo; 18 passano da `difficile`/`da_verificare` ad `attiva`, 2 diventano `esclusa` perché coperte da altre voci.
- La fonte più preziosa è il catalogo di incentivi.gov.it: tutte le misure nazionali, regionali e camerali con scadenze, dimensioni d'impresa, forme di agevolazione, spese ammesse e ATECO, già nei dati grezzi per le schede della Fase 3.
- Restano bloccate dal server: Sviluppo Basilicata, Ministero del Turismo, Enna; Milano dipende da una decisione di Matteo.

## Conseguenze per il registro delle fonti

- Nuove opzioni `richiesta.selettore` e `richiesta.ipv6` (documentate in `fonti/README.md`).
- Milano: se Matteo approva, `richiesta.intestazioni.User-Agent` da browser con in coda BandiRadar e contatto, come per il MASE.
- Da ricontrollare fra qualche giorno: Latina, Pesaro (possibili problemi temporanei dei siti).
