# Perché manca il testo ufficiale — 797 bandi aperti "in disparte" (08/10/2026)

Analisi in sola lettura (PIANO_QUALITA, azione 2). Insieme studiato: vista `bandi_situazione`
- 715 bandi `scheda_solo_sintesi` con stato `aperto` (703) o `in_arrivo` (12)
- 82 bandi `senza_scheda_sintesi` con stato `aperto`

Come: raggruppamento per dominio di `bandi.url` e per fonte; rilettura **senza rete** delle copie delle pagine già
salvate in `/srv/allegati` con le funzioni di produzione (`trova_allegati`, `sottopagine`, `testo_html`,
`valuta_pagina`); lettura degli allegati già scaricati; poche pagine campione per sito scaricate con il client di
produzione (User-Agent BandiRadar, robots.txt rispettato); per il Portale UE, una lettura dell'API SEDIA (la stessa
della fonte, 9 richieste) per i 382 topic.

## 1. Dove stanno i 797

| Gruppo | Bandi | Nota |
|---|---:|---|
| Portale UE Funding & Tenders (`ec.europa.eu`, fonte `ue_funding_tenders_api`) | 385 | **mai scaricato un documento**: 0 allegati su 482 bandi UE |
| Catalogo `incentivi.gov.it` rimasto come pagina ufficiale | 181 | il link all'ente (`link_ente`) è stato scartato o non funzionava |
| Siti degli enti (mycivis 30, MIMIT 20, Provincia di Trento 17, Toscana 9, lexview FVG 9, Finlombarda 8, Invitalia 8, ...) | 231 | cause varie, una per sito |

Altri fatti generali:
- 748 dei 797 hanno la pagina ufficiale cercata **prima del 02/10**: le regole aggiunte dopo (homepage dell'ente
  scartata, ecc.) non sono mai state applicate a loro.
- 367 dei 410 non UE hanno i documenti cercati più di 7 giorni fa e **nessuno viene ricercato di nuovo**:
  se l'ente pubblica il bando dopo la notizia, non lo vediamo.
- 5 bandi hanno già il decreto/avviso tra i documenti ma `documentazione` è rimasta `sintesi` (calcolata prima
  dell'arrivo dei documenti e mai ricalcolata): Italia Economia Sociale (2522), Autoimpiego Centro-Nord (2645),
  Resto al Sud 2.0 (2646), Trentino Sviluppo (1776), Filiera del libro (3644).
- 43 bandi hanno `documentazione = 'bando'` ma la scheda dice `solo_sintesi`: il testo c'è già (spesso però è
  un documento generico: regolamento UE 651, circolari vecchie MIMIT). Non è un problema di raccolta.

## 2. Tabella riassuntiva: causa → bandi recuperabili → correzione

In ordine di bandi recuperati. "Bandi" = quanti dei 797 ricadono nella causa; "recuperabili" = stima prudente
di quanti avrebbero il testo ufficiale dopo la correzione.

| # | Causa | Bandi | Recuperabili | Correzione proposta (file, funzione, regola) |
|---|---|---:|---:|---|
| 1 | **UE**: il lettore SEDIA toglie i link dalle "condizioni" del topic, dove sta il documento del bando (Work Programme Horizon, call document) | 350 | ~345 | `app/raccolta/lettori/api.py` `sedia_annuncio`: salvare in `dati.documenti` i link di `topicConditions` (tipo 8: di `furtherInformation`/`description`); `app/schede/allegati.py` `esegui`: per le fonti `testo_dai_dati` aggiungerli ai candidati e **non** filtrarli con `documenti_del_sito`; per i Work Programme Horizon tagliare la sezione del topic; aggiungere i segni inglesi in `app/schede/documentazione.py` (vedi §3.1) |
| 2 | **mycivis (Alto Adige)**: i PDF arrivano come `application/octet-stream` e finiscono tipo `altro`, mai letti | 30 | 27 | `allegati.py` `elabora_pagina`: se il Content-Type non è in `TIPI_MIME`, decidere dal contenuto (`%PDF-` → pdf, `PK` + `word/document.xml` → docx, `D0 CF 11 E0` → doc) o dal `filename=` di Content-Disposition. Rileggere i 1.114 PDF già scaricati (tutto il sito, non solo i 797) con un `rileggi_illeggibili` esteso al tipo `altro` |
| 3 | **Pagine ASP.NET**: `testo_html` toglie `<form>`, ma questi siti mettono tutta la pagina dentro `<form id="form1">` → "pagina vuota" e l'ente viene scartato | 23 | ~14 | `allegati.py` `testo_html`: togliere `form` solo se non contiene il contenuto (come `_e_cornice`: senza `main`/`article`, o se ha poco testo). Regione Valle d'Aosta (10), GSE Conto Termico 3.0, BUR Veneto (3-4), lexview FVG (9, testi di legge: resta "pagina", vedi nota) |
| 4 | **Pagine "atto" non seguite**: MIMIT mette i decreti su `/it/normativa/...`, Lazio Europa su `regione.lazio.it/documenti/N`, la Camera di Chieti su `trasparenza...archivio19_regolamenti` | 17 (+12 MIMIT già "bando" ma con documenti vecchi) | ~20 | `allegati.py` `sottopagine`: oltre ai figli dell'indirizzo, una piccola tabella `PAGINE_ATTO` per dominio (`mimit.gov.it: /it/normativa/`, `regione.lazio.it: ^/documenti/\d+$`, ...), solo link del contenuto, al massimo 4, prima quelli con la data più recente nel testo |
| 5 | **Toscana**: documenti su `www301.regione.toscana.it/bancadati/atti/Contenuto.xml?id=…` (PDF senza estensione); in più la pagina ufficiale `.xml` viene scartata come "indirizzo di dati o API" | 14 (6 + 8 dal catalogo) | 14 | `allegati.py`: aggiungere `Contenuto\.xml\?id=` alle regole "file" (`_SCARICA`/nuova `_FILE_SENZA_ESTENSIONE`); `app/schede/bandi.py` `_e_pagina_di_servizio`: eccezione per `bancadati/(atti|BURT)/` |
| 6 | **Catalogo incentivi.gov.it**: pagina dell'ente ora raggiungibile (rifare la ricerca) | 7 | 7 | lanciare `pagina_ufficiale --bando` sui 181 (o una regola: per i bandi con url sul catalogo riprovare ogni 14 giorni, come i "non trovati") |
| 7 | **Ricerca dei documenti mai ripetuta / filtro non ricalcolato** | 8 (+ quanti l'ente aggiorna) | 8 | regista: per i bandi aperti in disparte rifare `allegati` ogni 14 giorni (`bandi_da_elaborare` con `allegati_cercati_il < now()-14 giorni`), e in `salva_bando` rimettere `documentazione = NULL` se arrivano documenti nuovi. Marche (1484, 1767, 2000: la pagina oggi ha 12 documenti) + i 5 sopra |
| 8 | **Finlombarda**: documenti su `/it/attachments/file/view?hash=…` (PDF senza estensione) | 8 | 8 | `allegati.py`: aggiungere `attachments/file/view\?hash=` alle regole "file" (92 pagine Finlombarda nel database lo usano) |
| 9 | **"Vai alla pagina" / "Vai al bando"**: la scheda bando rimanda alla pagina con i documenti | 9 | ~7 | registro (`fonti/*.yaml`): `pagina_ufficiale.segui_link` con `stesso_sito: true` e testi `["vai alla pagina"]` per `fvg_bandi_avvisi` (FOGLIA con i documenti, verificato), `["vai al bando"]` per `cciaa_treviso_belluno_bandi` |
| 10 | **Pagina ufficiale generica** (homepage o elenco: `bs.camcom.it/`, `comolecco.camcom.it/`, `lg.camcom.it/bandi`, `chpe…_bandi.html`) presa dal catalogo prima dell'annuncio specifico della Camera | 21 | 4 | `app/schede/pagina_ufficiale.py` `esegui_regole`: il `link_ente` del catalogo è "forte" solo se non è un elenco; se un altro annuncio dello stesso sito ha un indirizzo più specifico, provarlo prima. Gli altri 17 non hanno alternativa (vedi §4) |
| 11 | **Catalogo → ente: falso "login"** (Finmolise: casella di accesso nel sito ma 13 documenti) | 4 | 3 | `pagina_ufficiale.py` `valuta_pagina`: la regola login non vale se la pagina ha documenti (`documenti >= 3`) |
| 12 | **Plone/Volto decisa per fonte, non per sito** (`fesr.regione.emilia-romagna.it` arrivato dal catalogo) | 3 | 3 | `allegati.py` `esegui` e `pagina_ufficiale.py`: attivare `plone_api` anche quando il **dominio** della pagina è di una fonte con `documenti_plone` |
| 13 | **Limite 30 file**: le graduatorie riempiono i 30 posti e l'avviso resta fuori (Calabria 1611 e 3349, Invitalia FNEE 4195) | 3 | 3 | `allegati.py` `elabora_pagina`: ordinare i candidati con `categoria_allegato` + `ORDINE_CATEGORIE` (bando, decreto prima; graduatoria, modulistica dopo) **prima** del taglio a `MASSIMO_FILE_ANNUNCIO` |
| 14 | **Camere ISWEB**: `output_allegato.php?id=…` | 2 | 2 | `allegati.py`: aggiungere `output_allegato\.php\?id=` alle regole "file" |
| 15 | **Trento (17 Servizi della Provincia)**: Servizio → pagina "Documenti" → archivio delibere ASP con `javascript:DownloadDoc` (POST a `VediAllegato.asp`) | 16 | ~14 (da verificare) | lettore dedicato in `allegati.py`: dai link `delibere.provincia.tn.it/CercaSpecifica.asp?...anno=A&numero=N` fare il POST del modulo `VediAllegati` (campi `CDEL_N`, `ANDE_N`, `TYPE=DELI`). Non provato: richiede una richiesta POST al sito |
| | **Totale recuperabile con il codice** | | **~475** | di cui ~345 UE |

Correzioni piccole e generali (1-3 righe ciascuna): 2, 3, 5, 8, 11, 12, 13, 14. Quella che vale di più è la 1 (UE).

## 3. Dettaglio delle cause principali

### 3.1 Portale UE (385 bandi)
- **Perché manca**: le pagine del portale sono un'app JavaScript; il testo si prende dai dati dell'API
  (`descriptionByte` + `topicConditions`), ma `pulisci_html` butta via i link. Proprio nei link di
  `topicConditions` c'è il documento del bando. Nessun allegato è mai stato scaricato per un topic UE.
- **Cosa c'è nei link** (lettura dell'API per i 382 topic):

  | Tipo di documento del bando | Topic | Esempio |
  |---|---:|---|
  | Parte del Work Programme Horizon (`/wp-call/2026-2027/wp-9-…pdf`, 14 file in tutto) | 298 | wp-12-missions: 2 MB, 728.000 caratteri |
  | Call document / call fiche PDF diretto | 38 | `call-fiche_i3-2026-inv1_en.pdf` (116.000 caratteri) |
  | Link senza estensione (`cybersecurity-centre.europa.eu/document/<uuid>_en`, `chips-ju…/viewfile/?id=`, siti di progetto) | 14 | ECCC: pagina Drupal con il link `/document/download/<uuid>_en` |
  | Sovvenzioni a cascata (tipo 8): solo link al sito del progetto | 27 | non risolvibile con una regola generale |
  | Topic non più nell'API, pagine CINEA, "call document available shortly" | 8 | — |

- **Quattro ritocchi necessari insieme**:
  1. `sedia_annuncio`: `dati["documenti"] = [{"url", "nome"}]` dai `<a href>` di `topicConditions`, tenendo quelli
     col testo "call document / work programme / guide for applicants" o con `/wp-call/` nel percorso (escludere
     `/common/`, `/agr-contr/`, `/temp-form/`, eur-lex, Online Manual). Per Horizon tenere anche
     `wp-15-general-annexes` (condizioni di ammissibilità, valutazione, finanziamento). Serve una nuova lettura
     della scorta UE (come `testo_ue.py` del 28/09) per riempire i dati già raccolti.
  2. `allegati.esegui`: per le fonti con `testo_dai_dati` aggiungere `dati.documenti` ai candidati e saltare il
     filtro `documenti_del_sito` (lo stesso Work Programme serve a 50 topic: oggi dal terzo in poi verrebbe
     scartato). Meglio ancora: se lo stesso URL è già stato scaricato, riusare il file invece di riscaricarlo
     (14 PDF invece di 298 scaricamenti).
  3. **Sezione del topic** nei Work Programme: il testo va tagliato **prima** del limite `MASSIMO_TESTO`
     (600.000 caratteri: il wp-12 ne ha 728.000). Regola provata sul wp-12: l'identificativo compare 3 volte
     (indice, tabella della call, scheda); si prende l'occorrenza seguita entro 3.000 caratteri da
     "Expected Outcome / Specific conditions / Expected EU contribution" e si taglia fino al prossimo
     `\n(HORIZON|ERC|EURATOM)-…:`. Risultato: 6.900 e 10.200 caratteri per i due topic provati, con importo,
     condizioni, criteri. Salvarla come documento "Work Programme – sezione del topic X".
  4. `documentazione.py`: i segni del filtro sono solo in italiano. Sulla call fiche I3 trova 1 segno su 10
     (servono 5), sul Work Programme 2. Con gli equivalenti inglesi (article/section, eligib/applicant,
     eligible costs, submission, deadline/cut-off, funding rate/EU contribution, regulation (EU)/state aid,
     evaluation/award criteria, pre-financing/payment) ne trova 10 su 10 e 5-6 nella sola sezione del topic.
- Nota: sono quasi tutti progetti di ricerca in consorzio (Horizon), poco adatti ai clienti di Matteo. Vale la pena
  farlo perché è un solo intervento, ma la priorità "per clienti" è più alta per le cause 2-15.

### 3.2 Catalogo incentivi.gov.it (181 bandi)
Tutti hanno il `link_ente`; è stato provato e scartato (il motivo si perde: `pagina_motivo` registra solo il
candidato vincente). Provato di nuovo un link per sito (91 bandi, 1 richiesta per sito) ed esteso agli altri bandi
dello stesso sito:

| Esito del link all'ente | Bandi | Risolvibile col codice? |
|---|---:|---|
| Sito JavaScript (Provincia di Bolzano nuovo portale `*.provinz.bz.it`/`provincia.bz.it` 17, SUS Sardegna `#/` 11, Umbria, CDP, Giustizia, Puglia smart) | 34 | solo con browser senza interfaccia |
| Link morto (404/410/500: Provincia di Trento 7, FVG 6, VdA imprese 4, Veneto Sviluppo 3, ...) | 34 | no: cercare la pagina nuova |
| Sito che non risponde al nostro server (Protezione civile FVG 20, MIT 3, Provincia MB 3, ocdpc Veneto, ...) | 32 | no (blocco di rete; niente IPv6) |
| Link generico (homepage, archivio delibere, elenco) | 18 | no: cercare la pagina del bando |
| robots.txt vieta (Liguria 4, Sacco 2, urbi, halley, bollettino TAA) | 11 | no |
| Pagina che non parla del bando (o pagina sostituita) | 9 | no |
| Pagina vuota per il bug `<form>` (VdA 10, GSE, BUR Veneto) | 12 | **sì** (causa 3) |
| Indirizzo `.xml` della Toscana scartato | 8 | **sì** (causa 5) |
| Ora la pagina si trova (rifare la ricerca) | 7 | **sì** (causa 6) |
| Regione Lombardia `wps/portal` | 6 | da verificare |
| Falso login (Finmolise 3, Sarentino) | 4 | **sì** (causa 11) |
| Plone ER | 3 | **sì** (causa 12) |
| Anti-bot Incapsula (Camera Milano) | 3 | no |

Per la Valle d'Aosta serve anche la regola file `allegato\.aspx\?pk=\d+` (i documenti sono
`/allegato.aspx?pk=68108`): aggiungerla con le altre della causa 5/8/14.

### 3.3 Altre evidenze
- **Google Drive** (Camera di Ferrara 6, ART-ER 1): `drive.google.com/uc` è vietato da robots.txt; la pagina
  `/file/d/…/view` è permessa ma non contiene il testo. Non risolvibile rispettando robots.
- **Molise** (5): notizie della Regione senza link all'avviso. **La Spezia** (5): pagine del Comune che rimandano a
  call UE o FILSE.
- **lexview FVG** (9): sono articoli di legge regionale; con la correzione del `<form>` il testo arriva, ma resta
  una "pagina" e il filtro non la conta come bando. Decidere se un articolo di legge che istituisce un contributo
  vale come testo ufficiale.
- **Regione Marche**: oltre alla copia vecchia, i file sotto `www.regione.marche.it/portals/` falliscono con
  `CERTIFICATE_VERIFY_FAILED` (102 file, quasi tutti del bando 1274 che però ha come pagina un elenco).
- **Formati mai letti in tutto il database**: `altro` 1.660 file (1.114 sono PDF di mycivis), `doc` 982, `zip` 326
  (221 contengono PDF; 8 bandi dei 797 hanno PDF dentro uno zip), `odt` 185, `xls/xlsx` 557. Leggere PDF e DOCX
  dentro gli zip e i `.doc` (antiword o LibreOffice nel container) è una correzione generale utile, ma tra i 797
  sposta pochi bandi (circa 8).

## 4. Casi che il codice non risolve (stima)

| Caso | Bandi | Cosa serve |
|---|---:|---|
| Catalogo incentivi.gov.it: link morto, generico, pagina senza bando | 61 | cercare a mano la pagina dell'ente (o lasciare in disparte) |
| Catalogo: sito che blocca il nostro server | 32 | provare da un'altra rete / chiedere all'ente; Protezione civile FVG da sola fa 20 |
| Siti JavaScript (catalogo 34) | 34 | browser senza interfaccia (modalità già prevista dal registro): unica strada |
| robots.txt (catalogo 11 + bollettino TAA 4, lexbrowser 2, Credito sportivo 1, Liguria 1) | 19 | rispettare: pagina dell'ente a mano |
| UE: sovvenzioni a cascata su siti di progetto, altro | 35 | a mano, se interessano |
| Pagine ufficiali generiche senza alternativa (homepage camerali, MUR, CNR, Ministero turismo, comuni) | 17 | cercare la pagina del bando |
| Google Drive, notizie senza link, rimandi ad altri enti | 17 | a mano |
| Anti-bot (Camera di Milano) | 3 | a mano |
| **Totale stimato** | **~218** | |

Restano ~46 bandi sparsi (1-2 per sito: comuni, Camere, Gepafin, Fondo di garanzia, Invitalia) e i 43 con il
testo già tra i documenti: non li ho analizzati uno per uno.

Conti: ~475 recuperabili col codice + ~218 non risolvibili + ~46 sparsi + 43 già col testo ≈ 782. Le categorie si
sovrappongono un poco (MIMIT, limite 30 file), quindi il totale non torna esatto a 797.

## 5. Ordine consigliato
1. Correzioni piccole e sicure in `allegati.py` (2, 5, 8, 13, 14, `allegato.aspx`, ordine prima del taglio a 30)
   + `testo_html` senza togliere i `<form>` che contengono la pagina (3) + falso login e Plone per dominio
   (11, 12). Poi rifare pagina ufficiale e allegati sui 797 e ricalcolare `documentazione`.
   Circa 90 bandi non UE, quasi tutti regionali/nazionali, compresi Conto Termico 3.0 e i prodotti Finlombarda.
2. Pagine "atto" per MIMIT/Lazio (4): Contratti di sviluppo, Semiconduttori, Transizione 5.0, IPCEI, Green
   New Deal: pochi bandi ma i più grossi per dotazione.
3. Ricerca ripetuta dei documenti e reset del filtro (7): copre anche i bandi dove l'ente pubblica il bando dopo.
4. UE (1): un intervento più ampio (lettore, allegati, sezione del topic, filtro in inglese), ~345 bandi.
5. Lettore delle delibere di Trento (15), dopo aver verificato il POST.

## 6. Cosa non ho fatto / limiti
- Niente modifiche a database, repository o `/srv`. File di lavoro in `/tmp/claude-1000/cp/tm/` e
  `/tmp/claude-1000/ar/cp_*`.
- Le stime per il catalogo estendono a tutto il sito l'esito di un link provato (91 bandi provati su 181).
- Non ho provato il POST alle delibere di Trento né il lettore browser.
- Per verificare il tipo di file ho fatto **una** richiesta a `drive.google.com/uc` prima di accorgermi che
  robots.txt la vieta (lo script la segnalava ma non si fermava). Nessuna altra richiesta vietata.
- Non ho rifatto il controllo degli ~46 casi sparsi né dei 43 "testo già presente".
