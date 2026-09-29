# Il profilo d'impresa anonimo

*Deciso il 29/09/2026 (anticipo della Fase 4). Controlli in `app/abbinamento/profilo.py`, regole di confronto in `app/abbinamento/regole.py`, tabella `profili` (migrazione `010`). È il riferimento per chi manda profili a Bandi Radar: oggi Matteo dalla plancia (pagina Profili), poi lo script delle anagrafiche e Qiaro / Contract to Cash via API. Il formato è lo stesso: cambia solo chi lo manda.*

## Privacy (piano §2 e §8, da non riaprire)

- **Nessun dato identificativo.** Il profilo ha solo un **codice interno** scelto da chi lo manda (per esempio `C001`); la corrispondenza codice ↔ impresa resta sul suo lato. Niente ragione sociale, nomi, codici fiscali, partite IVA, email, telefoni, indirizzi.
- Il sistema **rifiuta** un codice che sembra un codice fiscale o una partita IVA, e note o descrizioni che contengono un codice fiscale, una partita IVA, un'email o un numero di cellulare. Rifiuta anche i campi non previsti (per esempio `nome`).
- **Soci**: si manda solo il risultato ("impresa femminile: sì/no", "giovanile: sì/no"), calcolato dal lato di chi manda (regole di legge su quote e amministratori, vedi `docs/RICHIESTA_SCHEMA_ANAGRAFICHE.md`), mai i dati delle persone.
- `attivita` (cosa fa l'impresa, a parole) servirà all'IA più avanti: vale la stessa regola, niente nomi.

## Il formato (JSON)

```json
{
  "codice": "C001",
  "soggetto": "impresa",
  "da_costituire": false,
  "forma_giuridica": "srl",
  "sedi": [
    {"tipo": "legale_e_operativa", "regione": "LOM", "provincia": "MI", "comune": "Milano"},
    {"tipo": "operativa", "provincia": "BG", "comune": "Dalmine"}
  ],
  "ateco": ["62.01.00", "63.11.19"],
  "ateco_versione": "2025",
  "attivita": "sviluppo di software gestionale per studi professionali",
  "dimensione": null,
  "dipendenti": 18,
  "fatturato": 2400000,
  "totale_bilancio": null,
  "data_costituzione": "2016-04-01",
  "requisiti": {"femminile": false, "giovanile": false, "startup_innovativa": false},
  "temi": ["digitale", "ricerca"],
  "categorie_spesa": ["software_digitale", "consulenze"],
  "importo_progetto": 80000,
  "note": "cliente dal 2020"
}
```

| Campo | Valori | Note |
|---|---|---|
| `codice` | lettere, numeri, `.` `_` `-`, fino a 40 | obbligatorio, unico |
| `soggetto` | `impresa`, `libero_professionista`, `ente_terzo_settore` | di base `impresa` |
| `da_costituire` | sì/no | se sì, per l'abbinamento il soggetto è `aspirante_imprenditore` e l'età è 0 mesi; niente data di costituzione |
| `forma_giuridica` | valori di `FORME_GIURIDICHE` in `app/schede/campi.py` | una `srls` vale anche come `srl` |
| `sedi` | `tipo` (`legale`, `operativa`, `legale_e_operativa`), `regione` (sigle del registro: `LOM`, `EMR`, `BZ`…), `provincia` (sigla), `comune` | la regione si ricava dalla provincia; provincia e regione devono essere coerenti |
| `ateco` | codici con o senza punti (`6201` → `62.01`); il primo è il principale | `ateco_versione` `2025` di base |
| `dimensione` | `micro`, `piccola`, `media`, `grande` | se manca si stima da `dipendenti`, `fatturato` e `totale_bilancio` (soglie UE 2003/361) |
| `data_costituzione` | data | età dell'impresa |
| `requisiti` | chiavi di `REQUISITI_SPECIALI` (tranne `altro`), valore vero/falso | **una chiave assente vuol dire "non lo so"**: i bandi che la chiedono restano "da verificare" |
| `temi`, `categorie_spesa` | valori di `TEMI` e `CATEGORIE_SPESA` | servono a ordinare e alla motivazione, non escludono |
| `importo_progetto` | euro | sotto la spesa minima del bando → "da verificare" |
| `note` | testo breve | promemoria di Matteo |

## Le regole di abbinamento

Quelle di `docs/SCHEDA_BANDO.md` ("Campo della scheda ↔ dato del profilo ↔ regola di confronto"), senza IA. Tre esiti:

- **compatibile**: ogni vincolo è rispettato o il bando dice che non c'è;
- **da verificare**: almeno un vincolo "non noto", un dato che manca al profilo, un vincolo scritto solo a parole, oppure la scheda fatta solo su una sintesi. L'elenco dice cosa manca;
- **escluso**: un vincolo non rispettato, con il motivo (e i bandi chiusi).

Si propongono solo i bandi aperti o in arrivo (e quelli senza date, come "da verificare"). Ordine: compatibili, poi da verificare (quelli di un'altra regione in fondo), poi esclusi; in ogni gruppo per scadenza. Per ogni bando c'è anche la lista **da controllare con il cliente**: de minimis, esclusioni dei soggetti (imprese in difficoltà, procedure concorsuali…), domanda a sportello o click day, più linee.

Tre scelte prese il 29/09 guardando i dati veri (aggiunte alla tabella di `docs/SCHEDA_BANDO.md`):

1. **Sede "da attivare"** (bandi che ammettono chi si impegna ad aprire una sede nel territorio): se l'impresa non ha già una sede lì, il bando è "da verificare", non "compatibile": aprire una sede in un'altra regione è una scelta da fare con il cliente.
2. **Bandi UE e nazionali con territorio "non noto"** ma descritto come "Paesi ammissibili", "Stati membri", "territorio nazionale": valgono per l'Italia.
3. **Nessun vincolo sulla sede, ma bando pubblicato solo da enti di un'altra regione** (un film da girare in Liguria, boschi in Sardegna): "da verificare", perché di solito è il progetto a doversi fare lì.

## API (plancia; più avanti per Qiaro)

Tutte sotto `/api`, con l'autenticazione della plancia.

| Metodo e indirizzo | Cosa fa |
|---|---|
| `GET /profili` | elenco dei profili |
| `GET /profili/{codice}` | un profilo |
| `PUT /profili/{codice}` | crea o aggiorna (il corpo è il profilo; il codice è quello dell'indirizzo). Errore 422 con il motivo se un controllo non passa |
| `DELETE /profili/{codice}` | cancella |
| `GET /profili/{codice}/bandi` | i bandi aperti o in arrivo con esito e motivi |
| `POST /abbina` | abbinamento di un profilo senza salvarlo |

Risposta dell'abbinamento: `conteggi` (compatibile, da_verificare, escluso) e `bandi`, ciascuno con i campi principali e `esito` = `livello`, `esclusioni`, `da_verificare`, `punti_a_favore`, `da_controllare`.

## Cosa manca (Fase 4 vera e propria)

- conversione ATECO 2007 ↔ 2025 (oggi: versioni diverse → "da verificare");
- scelta della linea adatta al cliente quando il bando ha più linee (oggi: nota "scegliere la linea");
- stima della percentuale ottenibile (maggiorazioni per dimensione, zone assistite);
- margine de minimis dal Registro nazionale aiuti (Fase 7);
- lo script che produce i profili dalle anagrafiche di Matteo e l'API per Qiaro con una chiave propria (non la password della plancia).
