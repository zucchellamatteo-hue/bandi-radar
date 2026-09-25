# Fonti che la raccolta non leggeva ancora

**Data:** 25/09/2026 sera, sessione sul VPS di produzione (prompt `docs/sessioni/2026-09-26_fonti_difficili.md`).
**Domanda:** le ~44 fonti non verdi in plancia (bot manager, connessioni chiuse, siti Angular/myPortal, Camere mai provate dal server, fonti "senza novità") si possono leggere dal server? Con quale strada?
**Metodo:** cinque agenti in parallelo, uno per gruppo, ciascuno su una copia del registro. Per ogni fonte, fermandosi alla prima strada buona: lettura con il codice della raccolta (`--prova`, nessuna scrittura nel database) nell'immagine Docker `raccolta`; `curl` in IPv4 e IPv6 con lo User-Agent del progetto; Chromium con registrazione delle chiamate di rete per trovare API interne; altre porte dello stesso ente (RSS, sitemap, open data, incentivi.gov.it). Due o tre tentativi per indirizzo, con pause. Alla fine, una rilettura di tutte le fonti sistemate con il registro unito.
**Limiti:** captcha e bot manager (Imperva, Radware, CloudFront, Akamai) non sono stati aggirati, e nemmeno cambiato lo User-Agent. robots.txt rispettato: Avellino e Barletta restano ferme in attesa di una decisione. Non si è provato da una connessione italiana (il VPS è in Francia): alcuni blocchi potrebbero essere geografici.

## Quattro scoperte che valgono per più fonti

1. **myPortal della Regione Veneto ha un'API comune.** Le pagine Novità > Avvisi di Treviso, Belluno, Rovigo si riempiono da `/myportal/<codice catastale>/api/content?type=pnrr_news&pnrrTaxonomyLevel1=avviso...`, che risponde senza cookie; la Provincia di Belluno (modello vecchio) da `type=rve_avviso`. Nessun robots.txt vero (il sito risponde con la pagina Angular), quindi niente `ignora_robots`. Nuova opzione del registro `richiesta.elenco` per dire al lettore dove sta l'elenco (con meno di 31 avvisi sceglieva la lista sbagliata).
2. **I Comuni su WordPress "design comuni" hanno un feed per tipo di notizia**: `/tipi_notizia/avvisi/feed/`. Così si leggono Chieti, Isernia, Macerata, Benevento, Crotone, che chiudevano la connessione alla pagina. A Biella e Sondrio lo stesso feed esiste ma è vuoto: lì si legge la pagina con un selettore.
3. **Due difetti del lettore corretti.** Il lettore CSV ora applica `richiesta.url_modello` (Trento FESR: il link sta nella colonna INFORMAZIONI). Il lettore HTML non butta più un `<nav>` che contiene il contenuto (Camera di Torino: un `</nav>` fuori posto metteva tutta la pagina dentro il menu).
4. **Molti blocchi sono sull'indirizzo del server, non sullo User-Agent**: rifiutano anche robots.txt e non hanno IPv6 (Lodi, Finlombarda www, Campobasso, Sviluppo Basilicata, Latina, Rieti, Viterbo, Catania, Potenza, Sistema Puglia).

## Esito fonte per fonte

Rilettura finale del 25/09 sera con il registro unito: elementi letti da `--prova`.

| Fonte | Esito | Strada | Prova / cosa si è provato |
|---|---|---|---|
| **Bot manager** | | | |
| finlombarda_prodotti_imprese | sì (serve il sì di Matteo) | api, stessa API interna sul dominio senza www `finlombarda.it` | 13 prodotti. `www.finlombarda.it` dà 403 dal VPS a tutto (firewall Amazon); la soluzione del 24/09 era stata trovata dal cloud. Il dominio senza www risponde, robots.txt `Allow: /` |
| ministero_turismo_strumenti | sì | rss, `https://www.ministeroturismo.gov.it/feed/` | 10 voci (rassegna e avvisi, da smistare). Pagina, API e feed di categoria: controllo Radware, non aggirato |
| comune_grosseto_sito | sì | html `/novita/tipologia/avvisi/`, selettore `#load-more` | 12 avvisi datati; dal VPS nessun blocco |
| campania_regione_bandi_avvisi | sì | html notizie della Regione, selettore `div.view--res-news h5.card-title` | 10 notizie (da smistare). Il sito è stato rifatto, la vecchia sezione bandi dà 404 |
| unioncamere_lazio | no → `esclusa` | – | il dominio ora è un sito di casinò (registrato da un privato il 19/07/2025) |
| cciaa_milano_monza_brianza_lodi_bandi | no | – | Imperva ovunque. **Coperta da incentivi.gov.it**: 32 misure della Camera, 6 aperte nel 2026 |
| comune_venezia_sito | no | – | Imperva su tutti i sottodomini; open data senza bandi; incentivi.gov.it ne ha solo 2 vecchie |
| comune_lodi_imprese | no (era attiva) | – | 403 CloudFront anche su robots.txt, niente IPv6; il 24/09 passava dal cloud |
| comune_campobasso_sito | no | – | 403 "Accesso negato", stesso filtro di Sviluppo Basilicata |
| basilicata_sviluppo_basilicata_incentivi | no | – | come Campobasso; il Fondo Microfinanza è già nel Portale Bandi regionale |
| **Connessioni chiuse** | | | |
| comune_chieti_sito | sì | rss `/tipi_notizia/avvisi/feed/` | 23 voci, ultima del 15/06/2026 (feed poco aggiornato) |
| comune_isernia_sito | sì | rss, stesso schema | 10 voci di settembre 2026 |
| comune_macerata_sito | sì | rss, stesso schema | 10 voci fino al 24/09/2026 |
| comune_benevento_sito | sì | rss, stesso schema | 21 voci, ultima del 17/07/2026 |
| comune_crotone_sito | sì | rss, stesso schema | 10 voci fino al 25/09/2026 |
| comune_pesaro_nuove_imprese | sì | html archivio della sezione, selettore `h2.news-list__title` | 7 contributi alle imprese, senza data; il feed resta muto |
| comune_latina_avvisi | no (era attiva) | – | nessuna risposta alla connessione (feed, home, robots.txt) |
| comune_rieti_sito, comune_viterbo_sito | no | – | stesso server, non accetta connessioni; albi Urbi raggiungibili ma solo atti, a clic |
| comune_catania_sito, comune_potenza | no | – | anti-bot Radware (Potenza 403 `server: rdwr`), non aggirato |
| comune_lecce | no | – | il certificato HTTPS è installato male (manca l'intermedio): la raccolta lo rifiuta |
| basilicata_sito_regione | no → `esclusa` | – | nessuna connessione; doppione di `basilicata_portale_bandi_api`, che risponde |
| rna_open_data | non chiaro → `esclusa` fino alla Fase 7 | – | i file mensili ci sono (POST `/opendata/misure-agevolative/download` → zip senza cookie), ma serve un lettore dedicato |
| **Angular / myPortal** | | | |
| comune_treviso_sito | sì | api myPortal `C_L407`, filtro avvisi, `elenco: page.entities` | 39 avvisi |
| comune_belluno_sito | sì | api myPortal `C_A757` | 40 avvisi |
| comune_rovigo_sito | sì | api myPortal `C_H620`, filtro avvisi | 18 avvisi (senza `elenco` erano 0) |
| provincia_belluno_sito | sì, rende poco | api myPortal `P_BL`, `type=rve_avviso` | 50 avvisi, quasi tutti aste, espropri, conferenze di servizi |
| comune_avellino_sito, comune_barletta | no (robots.txt) | API `/kapi/api/sito/avvisi` trovata, risponde senza cookie | robots.txt vieta `/kapi`; servirebbe anche insegnare al lettore i campi `cntTitle`, `cntDataPubblicazione`. Avvisi quasi tutti sociali |
| puglia_sistema_puglia | no | – | timeout su https e http, anche col browser; avvisi in parte già dalle altre fonti pugliesi |
| **Camere e casi vari** | | | |
| cciaa_cremona_bandi | sì | html `https://www.cmp.camcom.it/incentivi-alle-imprese/bandi-e-contributi` | 9 bandi 2026. **Cremona, Mantova e Pavia sono ora un'unica Camera** con un solo sito |
| cciaa_mantova_bandi, cciaa_pavia_bandi | → `esclusa` | – | confluite nella voce di Cremona-Mantova-Pavia; i vecchi siti chiudono la connessione |
| comune_parma_sito | sì | api Plone `++api++/@search?portal_type=Bando` | 30 bandi e avvisi con data (anche gare: niente filtro sulla parola "gara"); il problema TLS era intermittente |
| cciaa_salerno_notizie | sì | html notizie con filtro `field_notizia_categoria_target_id=195` | 11 voci; dal server la pagina è completa |
| comune_ferrara_avvisi | sì (sito tornato su) | html, invariata | alle 19:08 tutto il sito dava 500 anche al browser; alla rilettura finale 200, 4 elementi |
| **Senza novità** | | | |
| umbria_bandi_imprese, marche_rss_tematici | sì, invariate | – | 20 bandi e 30 voci: il controllo del 24/09 era stato fatto con il lettore e il registro di prima delle correzioni |
| comune_biella_avvisi_rss, comune_sondrio_avvisi_rss | sì | html `/tipi_notizia/avvisi/`, selettore `.card-body h4` | 27 e ~30 avvisi; il feed degli avvisi è vuoto |
| cciaa_nordsardegna_contributi | sì | rss `https://www.ss.camcom.it/rss.xml` | 10 notizie; le pagine contributi hanno i bandi solo nel menu laterale |
| cciaa_torino_finanziamenti | sì | html (con il lettore corretto) | 23 link; titoli spesso deboli ("Portale Agevolazioni") |
| trento_fesr_calendario_avvisi | sì | api CSV con `url_modello: '{informazioni}'` (lettore corretto) | 9 avvisi FESR |

## Sintesi

- Su 44 fonti: **25 ora si leggono** (22 sistemate nel registro o nel lettore, 3 già a posto o tornate su), **5 escluse** (Unioncamere Lazio, Mantova e Pavia confluite, Basilicata sito regione doppione, RNA fino alla Fase 7), **14 restano `difficile`**.
- Delle 14: 10 bloccano l'indirizzo del server o hanno un anti-bot, 2 aspettano una decisione su robots.txt (Avellino, Barletta), 1 ha il certificato rotto (Lecce), 1 non risponde affatto (Sistema Puglia). La Camera di Milano è coperta da incentivi.gov.it.
- La "fonte senza novità" che risponde con 0 elementi dal primo controllo oggi appare come fonte tranquilla (`app/raccolta/esegui.py`, `app/plancia/semaforo.py`): sarebbe utile un messaggio a parte "risponde ma non si legge nulla".

## Conseguenze per il registro delle fonti

- Nuova opzione `richiesta.elenco` (documentata in `fonti/README.md`); `url_modello` vale anche per i CSV.
- **Decisioni per Matteo:** Finlombarda dal dominio senza www; `ignora_robots` per Avellino e Barletta (guadagno basso); prova dal suo PC di Lodi, Campobasso, Sviluppo Basilicata, Latina, Rieti, Viterbo, Sistema Puglia per capire se il blocco è geografico; Lecce (accettare un certificato incompleto è una modifica al codice); Provincia di Belluno da tenere o escludere.
- Venezia e Campobasso restano senza copertura: per Venezia la strada è chiedere al Comune di far passare il nostro User-Agent.
