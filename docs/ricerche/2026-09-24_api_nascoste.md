# API nascoste dei siti a pagina singola

**Data:** 24/09/2026
**Domanda:** le fonti con `modalita: browser` (elenco caricato via JavaScript) hanno un'API interna leggibile con una semplice richiesta HTTP, senza browser?
**Metodo:** un agente con Chromium (Playwright) ha aperto ogni pagina registrando le chiamate di rete, poi ha verificato che l'endpoint risponda anche a curl/httpx senza cookie o token. Esito confluito nel registro `fonti/` (campo `richiesta` per POST, intestazioni e modelli di link).
**Limiti:** dal cloud non rispondono GSE, Milano, Umbria, incentivi.gov.it, Enna: da riprovare dal server.

## Sintesi

- **API trovate e messe nel registro** (tutte provate con la raccolta il 24/09): Veneto (portale bandi, 40 pubblicati), Sardegna (motore di ricerca, 7222 bandi), Bolzano (myCIVIS OData e CMS Kontent.ai), Finlombarda, FILSE, calendario avvisi Calabria (78 inviti), Padova, Bologna e Città metropolitana di Bologna (myportal), L'Aquila (Strapi con token pubblico), Gorizia.
- **Non serviva il browser**: Ferrara, Lodi, Varese (con l'indirizzo giusto), MASE (con User-Agent da browser), Cagliari (ha un RSS "Bandi").
- **Restano bloccati dal cloud**: GSE (Akamai anche con browser), Milano (403), Umbria, incentivi.gov.it, Enna (endpoint noto: api.comune.enna.it).
- Quattro API interne sono vietate ai robot dal `robots.txt` del sito (Kontent.ai, myportal di Bologna, Varese): lette lo stesso per decisione di Matteo del 24/09 (`ignora_robots: true`).

---

# Fonti in modalità browser: esiste un'API "aperta"?

Verifica del 24/09/2026 dalla sessione cloud (Playwright/Chromium con intercettazione di rete, poi conferma con `curl`).
User-Agent usato nelle prove curl: `BandiRadar/0.1 (+https://finanzagevolata.qiaro.it)`.
Nota tecnica: in questa sessione Chromium non riusciva a scaricare i file JS di alcuni siti attraverso il proxy (ERR_TOO_MANY_RETRIES); ho aggirato il problema facendo passare tutte le richieste del browser da `page.route(... route.fetch ...)`. In produzione, sul VPS, non serve.

Legenda esito: **API trovata** = endpoint che risponde con una semplice richiesta HTTP senza browser; **HTML sufficiente** = l'elenco è già nell'HTML; **solo browser**; **bloccato dal cloud** = non verificabile da qui, da riprovare dal VPS.

---

## 1. veneto_portale_bandi — API TROVATA

- **Endpoint**: `GET https://bandi.regione.veneto.it/Public/GetListaAttiJson`
- **Parametri** (tutti obbligatori, anche se vuoti): `cig=&parolaChiave=&tipoAttoTmp=1&destinatariTmp=&struttureTmp=0&categorieTmp=0&statoTmp=0&materieTmp=&paginaIniziale=Elenco&sEcho=1&iDisplayStart=0&iDisplayLength=100`
  - `tipoAttoTmp=1` = Bandi (la pagina `Elenco?Tipo=1`).
  - `statoTmp`: `0` tutti (809 record), `4` PUBBLICATO (40 record), `5` SCADUTO, `6` ARCHIVIATO (da `GET /Public/GetStatiJsonResult?tipoAtto=1`).
  - `categorieTmp`: da `GET /Public/GetCategorieJsonResult?tipoAtto=1` → 30 Contributo, 3 Finanziamento, 6 Fondo di rotazione, 2 Bando di gara, ecc.
  - `iDisplayStart`/`iDisplayLength`: paginazione DataTables (testato 100 per pagina).
- **Header**: nessuno necessario. Funziona senza cookie e senza `X-Requested-With`. Perché prima rispondeva vuoto: mancavano i parametri DataTables (`sEcho`, `iDisplayStart`, `iDisplayLength`) e/o `paginaIniziale=Elenco`.
- **Risposta**: JSON `{"recordsTotal":809,"recordsFiltered":809,"aaData":[[ "<frammento HTML>" ], ...]}`. Ogni elemento è una stringa HTML da cui estrarre: id atto (primo `<span style="display:none">`), stato (`PUBBLICATO`), `Data scadenza: gg/mm/aaaa hh:mm`, titolo, `Struttura:`, link `Dettaglio?idAtto=13199&fromPage=Elenco` → `https://bandi.regione.veneto.it/Public/Dettaglio?idAtto=13199`.
- **Elementi visti**: 809 totali, 40 pubblicati.
- **YAML aggiornato**:
```yaml
- id: veneto_portale_bandi
  nome: Regione del Veneto - Portale Bandi, Avvisi e Concorsi (elenco bandi)
  ente: Regione del Veneto
  tipo: regione
  territorio: VEN
  url: https://bandi.regione.veneto.it/Public/Elenco?Tipo=1
  modalita: api
  feed_url: https://bandi.regione.veneto.it/Public/GetListaAttiJson?cig=&parolaChiave=&tipoAttoTmp=1&destinatariTmp=&struttureTmp=0&categorieTmp=0&statoTmp=4&materieTmp=&paginaIniziale=Elenco&sEcho=1&iDisplayStart=0&iDisplayLength=100
  piattaforma: datatables_json
  frequenza: giornaliera
  stato: attiva
  verificato_il: '2026-09-24'
  note: 'API DataTables: GET senza cookie ne'' header particolari. Risposta JSON con aaData = elenco di frammenti HTML
    (id atto, stato, data scadenza, titolo, struttura, link Dettaglio?idAtto=N). statoTmp=4 solo PUBBLICATO (40),
    statoTmp=0 tutti (809). Categorie utili: 30 Contributo, 3 Finanziamento, 6 Fondo di rotazione (GetCategorieJsonResult).
    Paginazione con iDisplayStart/iDisplayLength.'
```

## 2. sardegna_regione_bandi — API TROVATA

- **Endpoint**: `POST https://www.regione.sardegna.it/api/search?index=contentrepository` (è il proxy del sito verso il motore di ricerca; GraphQL `https://graphql-prod.regione.sardegna.it/graphql/` serve solo per menu e layout).
- **Header**: `Content-Type: application/json`. Nessun cookie né token (testato con curl).
- **Body** (minimo funzionante):
```json
{"state":{"current":1,"resultsPerPage":50,"searchTerm":"","sortList":[{"field":"dataPubblicazione","direction":"desc"}],
  "filters":[{"field":"stato.keyword","type":"any","values":["PUBBLICATO"]},{"field":"esterno","type":"any","values":["false"]},{"field":"tipoContenuto.keyword","type":"any","values":["BANDO"]}]},
 "config":{"result_fields":{},"facets":{},
  "filters":[{"field":"stato.keyword","type":"any","values":["PUBBLICATO"]},{"field":"esterno","type":"any","values":["false"]},{"field":"tipoContenuto.keyword","type":"any","values":["BANDO"]}]}}
```
  `state.current` = numero pagina. Il sito filtra anche i bandi "aperti" con un range su `dataScadenza >= adesso` (facet `stato`).
- **Risposta**: `{"totalResults":7222,"totalPages":145,"results":[...]}`. Chiavi di un elemento: `titolo`, `oggetto`, `dataPubblicazione` (ISO), `dataScadenza` (ISO), `dataCreazione`, `dataModifica`, `slug`/`idWeb` (numerico), `stato` (PUBBLICATO), `tipoContenuto` (BANDO), `destinazione` (es. `["impresa"]`), `documentiList` (PDF allegati), `linkList`, `strutturaOrganizzativaList`, `customClassification.argomenti`. Link scheda: `https://www.regione.sardegna.it/atti-bandi-archivi/atti-amministrativi/bandi/<slug>`.
- **Elementi visti**: 7222 totali (12 nella pagina, 50 con curl).
- **YAML aggiornato**:
```yaml
- id: sardegna_regione_bandi
  nome: Regione Sardegna - Bandi
  ente: Regione Autonoma della Sardegna
  tipo: regione
  territorio: SAR
  url: https://www.regione.sardegna.it/atti-bandi-archivi/atti-amministrativi/bandi
  modalita: api
  feed_url: https://www.regione.sardegna.it/api/search?index=contentrepository
  piattaforma: sardegna_search_api
  frequenza: tre_a_settimana
  stato: attiva
  verificato_il: '2026-09-24'
  note: 'POST JSON senza cookie (Content-Type: application/json). Body con state.current (pagina), resultsPerPage,
    sortList dataPubblicazione desc e filters stato.keyword=PUBBLICATO, esterno=false, tipoContenuto.keyword=BANDO
    (stesso blocco filters anche in config). Risposta: totalResults, results[] con titolo, dataPubblicazione,
    dataScadenza, slug, destinazione (es. impresa), documentiList. Scheda: .../bandi/<slug>. 7222 bandi totali.'
```

## 3a. bolzano_civis_servizi — API TROVATA (parziale: solo elenco titoli)

- **Endpoint**: `GET https://mycivis.civis.bz.it/_api/products/?$filter=statecode eq 0 and ntt_visibleonmycivis eq true and producttypecode eq 3&$select=ntt_name_italian,productnumber,modifiedon` (OData di Dynamics 365 Portal, URL-encodare gli spazi con `%20`).
- **Header**: nessuno; funziona senza cookie e senza `__RequestVerificationToken` (il browser lo manda, ma non serve). Attenzione: `$select` accetta solo alcuni campi (`ntt_name_italian`, `productnumber`, `modifiedon` ok; `$top` senza `$select` → 403; `createdon`/`ntt_name_german` → 400).
- **Risposta**: `{"value":[{"ntt_name_italian":"Contributi alle piccole imprese per investimenti aziendali (2024)","productnumber":"1223","modifiedon":"2026-09-24T15:54:43Z","productid":"..."}]}`. 961 servizi, di cui ~260 con "contributi/finanziamenti/agevolazioni" nel titolo. Link scheda: `https://mycivis.civis.bz.it/it/Services/ServiceDetail/?id=<slug-del-titolo>_<productnumber>` (lo slug lo genera il JS dal titolo; in alternativa si scarica la scheda HTML per verifica).
- **Limite**: l'API dà titolo, numero e data di modifica, non date di apertura/chiusura: buona per accorgersi di servizi nuovi o modificati, la scheda va poi letta a parte.
- **YAML aggiornato**:
```yaml
- id: bolzano_civis_servizi
  nome: Provincia autonoma di Bolzano - myCIVIS, catalogo servizi (contributi)
  ente: Provincia autonoma di Bolzano
  tipo: provincia
  territorio: BZ
  url: https://mycivis.civis.bz.it/it/Services/
  modalita: api
  feed_url: https://mycivis.civis.bz.it/_api/products/?$filter=statecode%20eq%200%20and%20ntt_visibleonmycivis%20eq%20true%20and%20producttypecode%20eq%203&$select=ntt_name_italian,productnumber,modifiedon
  piattaforma: dynamics365_portal_odata
  frequenza: tre_a_settimana
  stato: attiva
  verificato_il: '2026-09-24'
  note: 'OData pubblica, GET senza cookie/token. value[] con ntt_name_italian, productnumber, modifiedon (961 servizi,
    ~260 contributi). $select accetta solo pochi campi. Scheda: /it/Services/ServiceDetail/?id=<slug>_<productnumber>.
    Usare modifiedon per individuare novita'', poi leggere la scheda HTML.'
```

## 3b. bolzano_economia — API TROVATA (CMS headless Kontent.ai)

- **Endpoint**: `GET https://deliver.kontent.ai/34709482-d191-0125-83d4-7f2a83348147/items?system.type=page&elements=title,url&order=system.last_modified[desc]&limit=50&language=it&system.language=it` (Delivery API pubblica di Kontent.ai; con `curl` usare `-g` per le parentesi quadre). Nessun header/token.
- Le pagine dei contributi sono di tipo `page`: es. "Agevolazioni all'economia" (`url: agevolazioni-all-economia`), "Contributi per gli anni 2024 - 2028". Il contenuto della pagina si legge con `...items?system.type=page&elements.url=agevolazioni-all-economia&depth=2&language=it&system.language=it` (arriva anche `modular_content` con le sottopagine). Link sito: `https://economia.provincia.bz.it/it/<url>`.
- Le **news** economia stanno in un altro progetto Kontent: `https://deliver.kontent.ai/c1c45d5a-c794-01a3-3c24-89f77bf8cab4/items?system.type=news&elements.news_categories[contains]=economy&order=elements.date[desc]&limit=20&language=it&system.language=it&elements=title,url,date` → titolo, `date`, `url` (5 viste, es. "Camera di commercio: 1,2 milioni per formazione…").
- **Risposta**: `{"items":[{"system":{"codename","last_modified","type"},"elements":{"title":{"value"},"url":{"value"}}}],"pagination":{...}}`. `/types` elenca i 41 tipi (page, news, publication_item, ...): nessun tipo "bando".
- **YAML aggiornato**:
```yaml
- id: bolzano_economia
  nome: Provincia autonoma di Bolzano - Ripartizione Economia
  ente: Provincia autonoma di Bolzano
  tipo: provincia
  territorio: BZ
  url: https://economia.provincia.bz.it/it/home
  modalita: api
  feed_url: https://deliver.kontent.ai/34709482-d191-0125-83d4-7f2a83348147/items?system.type=page&elements=title,url&order=system.last_modified[desc]&limit=50&language=it&system.language=it
  piattaforma: kontent_ai
  frequenza: tre_a_settimana
  stato: attiva
  verificato_il: '2026-09-24'
  note: 'Sito su CMS headless Kontent.ai: Delivery API pubblica senza token. items[] con system.last_modified,
    elements.title/url; pagina sito = https://economia.provincia.bz.it/it/<url>. Pagine chiave: agevolazioni-all-economia,
    contributi-per-gli-anni-2024-2028 (leggere con elements.url=<url>&depth=2). News economia in altro progetto:
    deliver.kontent.ai/c1c45d5a-c794-01a3-3c24-89f77bf8cab4/items?system.type=news&elements.news_categories[contains]=economy.'
```

## 4. comune_milano_impresa — SITO BLOCCATO (parziale)

- `www.comune.milano.it`: risponde **403** al nostro User-Agent; con User-Agent Chrome e header da browser completi (`Accept`, `Accept-Language`, `Sec-Fetch-*`) risponde 200 anche con curl (il blocco è sulla firma del client, non sull'IP; comportamento non stabile: una volta 200, la volta dopo 403). Nel browser la pagina "Impresa" si carica ma non contiene un elenco di bandi (solo link a pagine argomento, es. "patrimonio immobiliare a bando"); nessuna chiamata JSON di contenuto (solo Adobe/OneTrust). Nessun RSS.
- `economiaelavoro.comune.milano.it`: **403 sempre** (Azure Application Gateway), anche nel browser headless e con header completi: da qui non è verificabile alcun feed o API.
- **Esito**: nessuna API. Da riprovare dal VPS (l'IP del cloud potrebbe essere in lista nera). YAML: **resta browser**, aggiornare solo la nota:
```yaml
  note: >
    Da server risponde 403 (firewall applicativo) sia comune.milano.it sia economiaelavoro.comune.milano.it.
    Verifica cloud 24/09: comune.milano.it risponde 200 solo con User-Agent Chrome e header completi (instabile);
    economiaelavoro.comune.milano.it 403 fisso (Azure App Gateway) anche con browser headless. Nessuna API o feed
    di contenuto trovati; la pagina Impresa non ha un elenco bandi. Riprovare dal VPS.
```

## 5. finlombarda_prodotti_imprese — API TROVATA

- **Endpoint**: `GET https://www.finlombarda.it/prodotti-e-servizi/prodotti-servizi/ajax-filter-prodotti?ProdottiServiziSearch%5Bscope%5D=1&page=1` (scope 1 = imprese; `page` 1..18).
- **Header**: `X-Requested-With: XMLHttpRequest` (consigliato; il browser lo manda). Nessun cookie/CSRF necessario in GET (testato).
- **Risposta**: JSON = una stringa HTML (frammento con le card). Da estrarre: link `/it/prodotti-e-servizi/prodotti-servizi/<id>/<slug>`, titolo, stato ("Aperto"), tipo ("Contributi", "Garanzie"), destinatari ("Micro imprese", "PMI"), finalità. Non ci sono date nel frammento: vanno lette nella scheda.
- **Elementi visti**: 25 link su pagina 1; paginazione fino a `page=18`.
- **YAML aggiornato**:
```yaml
- id: finlombarda_prodotti_imprese
  nome: Finlombarda - Prodotti e servizi per le imprese
  ente: Finlombarda S.p.A.
  tipo: regione
  territorio: LOM
  url: https://www.finlombarda.it/it/prodotti-e-servizi/prodotti-servizi/index?ProdottiServiziSearch%5Bscope%5D=1
  modalita: api
  feed_url: https://www.finlombarda.it/prodotti-e-servizi/prodotti-servizi/ajax-filter-prodotti?ProdottiServiziSearch%5Bscope%5D=1&page=1
  piattaforma: yii_ajax_html
  frequenza: settimanale
  stato: attiva
  verificato_il: '2026-09-24'
  note: 'Endpoint AJAX (GET, header X-Requested-With: XMLHttpRequest, senza cookie): risponde JSON contenente un frammento
    HTML con le card (link /it/prodotti-e-servizi/prodotti-servizi/<id>/<slug>, titolo, stato Aperto, tipo, destinatari).
    Paginazione page=1..18. Le date sono solo nella scheda. Le misure compaiono anche su Bandi Online.'
```

## 6. filse_bandi_attivi — API TROVATA

- **Endpoint**: `POST https://www.filse.it/index.php` (multipart/form-data) con campi: `option=com_publiccompetitions`, `task=display.ajaxLoadBandi`, `format=json`, `id=2` (categoria "bandi attivi"), `showBandi=0`, `pcQuickSearch=1`, `pcPagination=1`, `pcPaginationResults=50`, `limit=50`, `limitstart=0`, `page=1`, `startPage=0`, `quicksearch=`, `quicksearch_action=1`, `quicksearch_OrderField[]=6`, `quicksearch_OrderDir[]=1`, `pcOrderField=6`, `pcOrderDir=1`, `ActionSearch=1`.
- **Header**: `X-Requested-With: XMLHttpRequest`. Nessun cookie/token Joomla necessario (testato).
- **Risposta**: `{"html": "...", "items": [...], "count": 259}`. `items[]` è già strutturato: `id`, `title`, `alias`, `publish_up` (apertura), `publish_down` (scadenza), `data_apertura`, `proroghe`, `in_corso`, `state`, `url` (sito esterno di domanda), `Beneficiari`, `Fondo`, `txt_descr` (HTML), `created`, `modified`. Link scheda: `https://www.filse.it/it/bandi-avvisi-gare/bandi-attivi/publiccompetition/<id>:<alias>.html` (nell'HTML appare anche `/it/bandi-attivi-nascosto/publiccompetition/...`).
- **Elementi visti**: 259 (`count`), 50 per pagina.
- **YAML aggiornato**:
```yaml
- id: filse_bandi_attivi
  nome: FILSE - Bandi attivi
  ente: FILSE S.p.A.
  tipo: regione
  territorio: LIG
  url: https://www.filse.it/it/bandi-avvisi-gare/bandi-attivi/publiccompetitions/
  modalita: api
  feed_url: https://www.filse.it/index.php
  piattaforma: joomla_publiccompetitions
  frequenza: tre_a_settimana
  stato: attiva
  verificato_il: '2026-09-24'
  note: 'POST multipart a index.php (X-Requested-With: XMLHttpRequest, senza cookie) con option=com_publiccompetitions,
    task=display.ajaxLoadBandi, format=json, id=2, limit=50, limitstart=0, page=1, pcPaginationResults=50, pcQuickSearch=1,
    pcPagination=1, quicksearch_action=1, ActionSearch=1. Risposta JSON con count (259) e items[] gia'' strutturati:
    id, title, alias, publish_up, publish_down (scadenza), Beneficiari, Fondo, txt_descr. Scheda:
    /it/bandi-avvisi-gare/bandi-attivi/publiccompetition/<id>:<alias>.html.'
```

## 7. gse_bandi_avvisi — SITO BLOCCATO

- `https://www.gse.it/` e `/bandi-e-avvisi`: **403 "Access Denied"** (Akamai) con User-Agent BandiRadar, con User-Agent Chrome e anche nel browser headless (titolo pagina "Access Denied"). Nessun endpoint visto. Da riprovare dal VPS; se blocca anche lì, seguire GSE tramite incentivi.gov.it / fonti secondarie. YAML: **resta browser** (stato `difficile`), nota da integrare con "verificato anche con Chromium headless dal cloud: 403".

## 8. umbria_avvisi_attivita_produttive — BLOCCATO DAL CLOUD

- `www.regione.umbria.it` chiude la connessione (ECONNRESET) sia con curl sia con il browser da questa sessione: non verificabile da qui. YAML invariato (browser); da riprovare dal VPS. Suggerimento per il VPS: cercare nel sorgente le URL `render_portlet` (Liferay) e provarle in GET.

## 9. calabria_europa_calendario_inviti — API TROVATA

- **Endpoint**: `POST https://calabriaeuropa.regione.calabria.it/be-inviti/api/invitiPubblicati` con body `{}` e `Content-Type: application/json`. Nessun cookie/token (testato con curl). (Nel bundle Angular c'è anche `https://gestioneavvisi.regione.calabria.it/backend/api/...`, ma da qui non risponde: usare il percorso `/be-inviti/`.) Utile anche `GET /be-inviti/api/dataUltimoAggiornamento`.
- **Risposta**: `Content-Type: text/html` ma il corpo è JSON: `{"status":..., "elements":[...]}`. Chiavi elemento: `codice` (es. ASAI-2026-0008), `titolo`, `data_apertura`, `data_chiusura`, `data_pubblicazione_calendario`, `dotazione_finanziaria`, `descrizione_stato_invito` (PUBBLICATO), `stato_bando`, `link` (scheda su calabriaeuropa, es. `https://calabriaeuropa.regione.calabria.it/bando/<slug>`), `tipologia_beneficiari`, `tipologia_destinatari`, `ambito_tematico`, `obiettivo_specifico`, `servizio_responsabile`, `azione`.
- **Elementi visti**: 78.
- **YAML aggiornato**:
```yaml
- id: calabria_europa_calendario_inviti
  nome: Calabria Europa - Calendario avvisi 21-27 (art. 49)
  ente: Regione Calabria
  tipo: regione
  territorio: CAL
  url: https://calabriaeuropa.regione.calabria.it/programmazione-2021-2027/attuazione-del-programma/calendario-inviti/
  modalita: api
  feed_url: https://calabriaeuropa.regione.calabria.it/be-inviti/api/invitiPubblicati
  piattaforma: calabria_be_inviti
  frequenza: mensile
  stato: attiva
  verificato_il: '2026-09-24'
  note: 'API dell''app Angular del calendario: POST con body {} e Content-Type: application/json, senza cookie.
    Risposta JSON (dichiarata text/html) con elements[]: codice, titolo, data_apertura, data_chiusura,
    dotazione_finanziaria, descrizione_stato_invito, link alla scheda, tipologia_beneficiari, ambito_tematico. 78 inviti.
    GET /be-inviti/api/dataUltimoAggiornamento per la data dell''ultimo aggiornamento.'
```

## 10. Fonti minori

### comune_padova_sitemap — API TROVATA (Drupal JSON:API)
- `GET https://www.comune.padova.it/api/news?filter[status][value]=1&filter[news_type.meta.drupal_internal__target_id]=3&jsonapi_include=1&sort=-changed&page[offset]=0&page[limit]=50` → avvisi (tipo 3 = "Avviso"; 1 = comunicati, 2 = notizie; tassonomia in `/api/taxonomy_term/news?jsonapi_include=1`). Nessun header/cookie.
- Risposta: `{"meta":{"count":142},"data":[{"title","changed","created","news_publication_date","news_end_date","path":{"alias":"/novita/avvisi/<slug>"},"news_description","news_body"}]}`. 142 avvisi. Anche `GET /api/entity?path=/novita/avvisi` risponde.
```yaml
  modalita: api
  feed_url: https://www.comune.padova.it/api/news?filter[status][value]=1&filter[news_type.meta.drupal_internal__target_id]=3&jsonapi_include=1&sort=-changed&page[offset]=0&page[limit]=50
  piattaforma: drupal_jsonapi
  note: 'Backend Drupal JSON:API aperto (GET senza header). news_type 3 = Avviso (142), 2 = Notizia, 1 = Comunicati.
    Campi: title, changed, news_publication_date, news_end_date, path.alias (/novita/avvisi/<slug>), news_description.'
```

### comune_bologna_sitemap — API TROVATA (myportal Lepida)
- `POST https://www.comune.bologna.it/myportal/C_A944/api/search-advanced?page=0&pageSize=50&sortBy=firstPublishedAt&desc=true`, `Content-Type: application/json`, body `{"preconditions":{"type":"rer_bando_avviso_pubblico"},"attributes":{}}`. Nessun cookie.
- Risposta: `{"page":{"index":1,"entitiesCount":1429,"entities":[{"name","slug","type","firstPublishedAt","modifiedAt","parent":"/Bandi/Avvisi pubblici/...","attributes":{"sys_title","sys_canonical_url":"/amministrazione/concorsi-avvisi-bandi/avvisi-pubblici/<slug>","def_date_last_modified"}}]}}`. 1429 elementi. Altri tipi disponibili: `rer_news`, `rer_documento_pubblico`, `rer_schedaservizio`.
```yaml
  modalita: api
  feed_url: https://www.comune.bologna.it/myportal/C_A944/api/search-advanced?page=0&pageSize=50&sortBy=firstPublishedAt&desc=true
  piattaforma: myportal_lepida
  note: 'POST JSON {"preconditions":{"type":"rer_bando_avviso_pubblico"},"attributes":{}} senza cookie. page.entities[] con
    name, slug, firstPublishedAt, modifiedAt, parent (cartella), attributes.sys_canonical_url (link). 1429 bandi/avvisi.'
```

### citta_metropolitana_bologna_sitemap — API TROVATA (stessa piattaforma)
- `POST https://portale.cittametropolitana.bo.it/myportal/CMBO/api/search-advanced?page=0&pageSize=50&sortBy=firstPublishedAt&desc=true`, stesso body. 568 elementi; `sys_canonical_url` es. `/amministrazione/documenti-e-dati/bandi-e-avvisi/<slug>`. Nella pagina avvisi il browser resta sullo spinner: l'API è la strada giusta.
```yaml
  modalita: api
  feed_url: https://portale.cittametropolitana.bo.it/myportal/CMBO/api/search-advanced?page=0&pageSize=50&sortBy=firstPublishedAt&desc=true
  piattaforma: myportal_lepida
  note: 'Come Bologna: POST JSON {"preconditions":{"type":"rer_bando_avviso_pubblico"},"attributes":{}}. 568 elementi
    con name, firstPublishedAt, modifiedAt, attributes.sys_canonical_url.'
```

### comune_ferrara_avvisi — HTML SUFFICIENTE
- Non serve il browser: l'HTML scaricato con curl contiene già le card ("Tutti gli avvisi"), stesse 5 del browser. Link del tipo `https://www.comune.ferrara.it/it/b/<id>/<slug>` (non `/avvisi/...`: per questo prima non si trovavano), con data (giorno/mese/anno) e sommario. Solo 5 avvisi in pagina, nessuna paginazione, nessuna chiamata XHR.
```yaml
  modalita: html
  feed_url: null
  piattaforma: nextjs
  note: 'L''elenco e'' gia'' nell''HTML (rendering lato server): card con link /it/b/<id>/<slug>, data e sommario.
    Mostra solo gli ultimi 5 avvisi, senza paginazione.'
```

### comune_laquila_sito — API TROVATA (Strapi, token pubblico nel bundle)
- `GET https://www.comune.laquila.it/api/pagine?sort=data:desc&pagination[pageSize]=50&filters[categoria][url][$eq]=avvisi&fields[0]=titolo&fields[1]=data&fields[2]=url&populate[categoria][fields][0]=url` con header `Authorization: Bearer <apiToken>`; il token (256 caratteri esadecimali) è scritto in chiaro in `main.<hash>.js` (`apiToken:"..."`): va letto dal bundle a ogni esecuzione perché può cambiare. Senza token: 403.
- Risposta: `{"data":[{"titolo","data","url","sommario","publishedAt","categoria":{"url":"avvisi","nome"}}],"meta":{"pagination":{"total":42}}}`. Link: `https://www.comune.laquila.it/novita/avvisi/<url>`. 42 avvisi (7229 pagine totali; categoria `notizie` per le notizie).
```yaml
  modalita: api
  feed_url: https://www.comune.laquila.it/api/pagine?sort=data:desc&pagination[pageSize]=50&filters[categoria][url][$eq]=avvisi&fields[0]=titolo&fields[1]=data&fields[2]=url&fields[3]=sommario&populate[categoria][fields][0]=url
  piattaforma: angular_strapi
  note: 'Strapi con collezione "pagine". Serve Authorization: Bearer <apiToken> letto dal bundle main.*.js (chiave apiToken,
    pubblica). Risposta data[] con titolo, data, url, sommario; link /novita/avvisi/<url>. 42 avvisi.'
```

### comune_enna_avvisi — BLOCCATO DAL CLOUD (endpoint chiaro)
- La pagina HTML (200) contiene le chiamate: `GET https://api.comune.enna.it/api/Content<base64>` dove il base64 è il filtro JSON, es. `{"itemPerPagina":6,"pagina":1,"avvisi":true,"ordinamento":1}` (con gli altri campi `gruppi:[]`, `serviziTipo:[]`, `notizie:false`, ecc.). Il proxy del cloud rifiuta `api.comune.enna.it`: da verificare dal VPS. YAML: resta `browser` finché non provato; feed candidato come sopra.

### comune_gorizia_sitemap — API TROVATA
- `GET https://www.comune.gorizia.it/core/page/031007/265181/it/` (031007 = codice ente, 265181 = pagina "Avvisi"). Nessun header.
- Risposta: `{"name":"Avvisi","modified":..., "modules":[{"articles":[{"id","title","intro","published_date":"2026-09-17 13:17:00","full_url":"/novita-265178/avvisi-265181/<slug>-<id>","categories"}]}]}`. 48 avvisi. Link sito: `https://www.comune.gorizia.it/it<full_url>`. Anche home `/core/page/031007/it/`.
```yaml
  url: https://www.comune.gorizia.it/it/novita-265178/avvisi-265181
  modalita: api
  feed_url: https://www.comune.gorizia.it/core/page/031007/265181/it/
  piattaforma: piattaforma_regionale_fvg
  note: 'API JSON del portale FVG (GET senza header): modules[].articles[] con title, intro, published_date, full_url
    (/novita-265178/avvisi-265181/<slug>-<id>). 48 avvisi. Link sito = https://www.comune.gorizia.it/it + full_url.'
```

### comune_lodi_imprese — HTML SUFFICIENTE
- La pagina risponde 200 con curl (128 KB) e contiene già i titoli ("Bando Città che Legge", "Bando Regionale AL VIA", ...). Non serve il browser: `modalita: html`. Nessun RSS trovato.

### comune_varese_home — HTML SUFFICIENTE (con URL diverso)
- La home ha un `location.href` JavaScript ma l'HTML (117 KB) contiene già i link `novita/avvisi/novita_NNN.html`. L'elenco completo è `https://www.comune.varese.it/EG0/EGSCHTST6.HBL?en=eg403&MESSA=PUBBLICA` ("Tutte le novità", 200, 44 KB, link a `/novita/avvisi/novita_642.html`, `/novita/notizie/...`, `/novita/comunicati_stampa/...`). Attenzione: `/novita/avvisi/` risponde con una pagina di 99 byte che fa solo `window.open(homepage)`.
```yaml
  url: https://www.comune.varese.it/EG0/EGSCHTST6.HBL?en=eg403&MESSA=PUBBLICA
  modalita: html
  piattaforma: halley
  note: 'Elenco "Tutte le novita''" servito in HTML statico (link novita/avvisi/novita_NNN.html). Non serve il browser.'
```

### comune_cagliari_bandi_contributi — RSS TROVATO
- `GET https://www.comune.cagliari.it/portale/do/jprss/Rss/Feed/show.action?id=15128&lang=it` = canale **"Bandi"**, 20 item, titoli tipo "Contributi turismo - Carnevale ed eventi collaterali - Anno 2027", link `https://www.comune.cagliari.it/portale/it/documento.page?contentId=DOC263911`. (Altri: id 12299 notizie, 12312 protezione civile.)
```yaml
  modalita: rss
  feed_url: https://www.comune.cagliari.it/portale/do/jprss/Rss/Feed/show.action?id=15128&lang=it
  piattaforma: entando
  note: 'Feed RSS "Bandi" (20 item, link documento.page?contentId=DOC...). La pagina /rss e'' HTML ma elenca i feed.'
```

### incentivi_gov_ricerca — BLOCCATO DAL CLOUD
- Connessione chiusa (ECONNRESET) sia con curl sia con il browser. Non verificabile da qui; da riprovare dal VPS. YAML invariato.

### mase_bandi_avvisi — HTML SUFFICIENTE (con User-Agent da browser)
- Con User-Agent `BandiRadar/0.1` → 403 Akamai. Con User-Agent Chrome + `Accept` + `Accept-Language` → **200** (188 KB) e la pagina `/portale/bandi-e-avvisi` (Liferay) contiene già l'elenco: 15 link `https://www.mase.gov.it/portale/-/<slug>` (es. "avviso-c.s.e.-2025-comuni-per-la-sostenibilita-e-l-efficienza-energetica"). Nessun RSS. Nota: serve una decisione sull'identificazione (il nostro UA dichiarato viene bloccato): proporrei UA Chrome con il nostro contatto in coda, es. `Mozilla/5.0 ... Chrome/128 BandiRadar/0.1 (+https://finanzagevolata.qiaro.it)`, da verificare dal VPS.
```yaml
  url: https://www.mase.gov.it/portale/bandi-e-avvisi
  modalita: html
  piattaforma: liferay
  note: 'Risponde 200 solo con User-Agent da browser (Akamai blocca gli UA non standard). L''elenco (15 link /portale/-/<slug>)
    e'' gia'' nell''HTML. Da confermare dal VPS.'
```

---

## Riepilogo

| Fonte | Esito | Da fare nel registro |
|---|---|---|
| veneto_portale_bandi | API (GET JSON/DataTables) | `modalita: api` |
| sardegna_regione_bandi | API (POST JSON) | `modalita: api` |
| bolzano_civis_servizi | API OData (solo titoli+date modifica) | `modalita: api` |
| bolzano_economia | API Kontent.ai | `modalita: api` |
| comune_milano_impresa | bloccato (403 UA/Azure) | resta browser, riprovare dal VPS |
| finlombarda_prodotti_imprese | API (GET, HTML in JSON) | `modalita: api` |
| filse_bandi_attivi | API (POST multipart, JSON strutturato) | `modalita: api` |
| gse_bandi_avvisi | bloccato (Akamai anche headless) | resta browser |
| umbria_avvisi_attivita_produttive | non raggiungibile dal cloud | resta browser, riprovare dal VPS |
| calabria_europa_calendario_inviti | API (POST JSON) | `modalita: api` |
| comune_padova_sitemap | API Drupal JSON:API | `modalita: api` |
| comune_bologna_sitemap | API myportal search-advanced | `modalita: api` |
| citta_metropolitana_bologna_sitemap | API myportal search-advanced | `modalita: api` |
| comune_ferrara_avvisi | HTML già completo | `modalita: html` |
| comune_laquila_sito | API Strapi con token dal bundle | `modalita: api` |
| comune_enna_avvisi | endpoint noto, host bloccato dal cloud | riprovare dal VPS |
| comune_gorizia_sitemap | API JSON portale FVG | `modalita: api` |
| comune_lodi_imprese | HTML già completo | `modalita: html` |
| comune_varese_home | HTML (URL elenco Halley) | `modalita: html` |
| comune_cagliari_bandi_contributi | RSS "Bandi" | `modalita: rss` |
| incentivi_gov_ricerca | non raggiungibile dal cloud | riprovare dal VPS |
| mase_bandi_avvisi | HTML con UA browser | `modalita: html` |
