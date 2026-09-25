# La scheda del bando

*Formato deciso il 24/09/2026 (Fase 3), rivisto il 25/09/2026 dopo la prova dell'IA: bando separato dagli annunci (Parte 1), pagina ufficiale (Parte 2), campi per l'abbinamento a valori controllati (Parte 3). La tabella è `bandi` (migrazioni `004`, `005`, `006`, `007` in `app/db/migrazioni/`); i valori ammessi stanno in `app/schede/campi.py`; il testo che chiede all'IA di compilarla è `app/schede/prompt_scheda.md`.*

Una **scheda** è un bando vero. Può avere più annunci: lo stesso bando pubblicato da più fonti, poi proroghe, rettifiche, graduatorie e FAQ. La compila l'IA (Sonnet) leggendo la **pagina ufficiale** del bando e i suoi allegati, messi in ordine: prima il bando, poi le FAQ e l'ultimo decreto, niente modulistica. Matteo la controlla e le dà un voto. Gli stessi campi servono al catalogo della plancia (filtri) e, dalla Fase 4, all'abbinamento con i profili anonimi dei clienti.

Ogni scheda mostrata a un cliente porta la frase: **"Informazione indicativa, verificare il bando ufficiale"**, con il link alla pagina dell'ente e la data dell'ultimo controllo.

## Regole generali

- **Niente invenzioni.** Se un'informazione non c'è nei documenti, il campo resta vuoto (`null`). Meglio una scheda incompleta che un numero sbagliato.
- **Il bando ufficiale vince sulla pagina web.** Se pagina e PDF non coincidono vale il PDF (o il decreto più recente), e la differenza va nelle avvertenze.
- **Ogni campo ha la sua fonte**, conservata in `dati`: "annuncio", "pagina" oppure il nome dell'allegato con l'articolo. Serve a Matteo per controllare in fretta.
- **Valori controllati** per tutto quello che serve a un filtro o all'abbinamento (elenchi fissi in `app/schede/campi.py`). Il testo libero resta per spiegare.
- **Tre stati per ogni vincolo** (campo `vincoli`): `vincolo` (il bando pone un limite), `nessun_vincolo` (il bando dice che non ci sono limiti, per esempio "tutti i settori"), `non_noto` (non si può sapere: abbiamo solo una sintesi, il testo è tagliato o ambiguo). Se il bando ufficiale è stato letto per intero ed elenca i requisiti senza porre quel vincolo, il vincolo non c'è: `nessun_vincolo`. Un elenco vuoto da solo non vuol dire niente: conta lo stato. **L'abbinamento non tratta mai `non_noto` come "va bene"**: al massimo "da verificare".
- **Completezza** della scheda: `bando_ufficiale` (letto il bando o il decreto), `solo_sintesi` (solo una pagina di riepilogo: catalogo, notizia), `nessun_documento`. Una scheda `solo_sintesi` non produce mai un abbinamento "compatibile", solo "da verificare".
- **Linee.** Quando il bando ha più linee o misure con regole diverse (massimali, percentuali, beneficiari), le linee vanno nell'elenco `linee`, ciascuna con i suoi valori. I campi del bando riportano il caso più ampio (il massimale più alto, l'unione dei beneficiari) e servono al catalogo; l'abbinamento controlla prima il bando e poi dice quale linea è adatta al cliente.
- **Lo stato lo calcola il sistema** ogni giorno dalle date (`app/schede/stato.py`), non lo scrive l'IA. "Prorogato" non è uno stato: è una nuova versione della scheda, che resta nello storico.
- **ATECO come nel bando**, con la versione in `ateco_versione`. Dal 1° aprile 2025 vale ATECO 2025: alcune sezioni hanno lettere diverse da ATECO 2007 (per esempio le attività finanziarie sono la K nel 2007 e la L nel 2025).

## I campi

### Chi è il bando

| Campo | Cosa contiene | Formato | Chi lo compila |
|---|---|---|---|
| `titolo` | Nome del bando come lo scrive l'ente | testo | deduplica, poi IA |
| `ente` | **Chi finanzia**: Regione, Camera di Commercio, Comune, Ministero | testo | IA |
| `gestore` | Chi gestisce il bando, se diverso da chi finanzia (Unioncamere, Invitalia, Finpiemonte, IRFIS...) | testo | IA |
| `url` | Pagina ufficiale del bando, trovata dal passo "pagina ufficiale" | indirizzo web | sistema |
| `codice_ufficiale`, `url_chiave`, `chiave_titolo` | Chiavi per riconoscere i doppioni | testo | sistema |
| `pagina_stato`, `pagina_motivo` | `trovata` o `non_trovata`, e da dove viene la pagina. Niente scheda se `non_trovata` | valore | sistema |

### Dove

| Campo | Cosa contiene | Formato |
|---|---|---|
| `territorio` | Il territorio con le parole del bando ("circoscrizione della Camera di Commercio di Bari") | testo |
| `territorio_regioni` | Sigle delle regioni in cui deve stare **la sede dell'impresa** (non il luogo del progetto, che va in `cosa_finanzia`), come nel registro delle fonti: `LOM`, `FVG`, `EMR`, `BZ`, `TN`... | elenco |
| `territorio_province` | Sigle delle province ammesse (`MI`, `BA`, `BT`), quando il bando si limita ad alcune province | elenco |
| `territorio_comuni` | Nomi dei comuni ammessi, quando il bando si limita ad alcuni comuni (il codice ISTAT lo aggiunge il sistema) | elenco |
| `sede_richiesta` | `legale`, `operativa`, `legale_o_operativa`, `da_attivare` (basta aprirla entro l'erogazione) | valore |

Tutta Italia: elenchi vuoti e `vincoli.territorio = nessun_vincolo`.

### Chi può partecipare

| Campo | Cosa contiene | Formato |
|---|---|---|
| `a_chi_si_rivolge` | I beneficiari a parole, con tutte le categorie se sono più di una | testo |
| `soggetti_ammessi` | `impresa`, `libero_professionista`, `aspirante_imprenditore`, `ente_terzo_settore`, `ente_pubblico`, `persona_fisica`, `altro` | elenco |
| `forme_giuridiche_ammesse` / `_escluse` | `ditta_individuale`, `snc`, `sas`, `srl`, `srls`, `spa`, `sapa`, `societa_semplice`, `cooperativa`, `consorzio`, `rete_imprese`, `associazione_professionale`, `stp`, `altro` | elenchi |
| `dimensioni_ammesse` | `micro`, `piccola`, `media`, `grande` | elenco |
| `eta_impresa_min_mesi` / `_max_mesi` | Età dell'impresa in mesi ("attiva da almeno 12 mesi"; "startup da non più di 24 mesi") | numeri |
| `requisiti_speciali_obbligatori` | Senza questo non si partecipa: `femminile`, `giovanile`, `startup_innovativa`, `pmi_innovativa`, `artigiana`, `agricola`, `commerciale`, `turistica`, `impresa_sociale`, `rating_legalita`, `certificazione_parita_genere`, `esportatrice`, `nuova_impresa`, `altro` | elenco |
| `requisiti_speciali_premiali` | Stessi valori, ma danno solo punti o maggiorazioni | elenco |
| `dipendenti_min` / `_max` | Soglie di dipendenti scritte nel bando (oltre alla dimensione) | numeri |
| `fatturato_min` / `_max` | Soglie di fatturato in euro | numeri |
| `codici_ateco` / `codici_ateco_esclusi` | Codici o sezioni ATECO ammessi / esclusi, come li scrive il bando (`"62"`, `"25.62"`, `"C"`). Ogni esclusione di settore scritta nel bando va qui, anche se è ripetuta nei requisiti | elenchi |
| `ateco_versione` | `2007`, `2025`, `incoerente` (il bando dichiara una versione ma usa le lettere dell'altra) | valore |
| `regime_aiuto` | `de_minimis`, `de_minimis_agricolo`, `gber` (Reg. UE 651/2014), `aber` (Reg. UE 2022/2472), `temporary_framework`, `notificato`, `non_aiuto`, `altro` | elenco |
| `requisiti` | Solo le **condizioni di ammissione** che restano a parole (DURC, polizza catastrofale, sede, garanzie...). Criteri di punteggio e premi non sono requisiti: vanno nella sintesi | testo |

### Cosa e quanto

| Campo | Cosa contiene | Formato |
|---|---|---|
| `cosa_finanzia` | Progetti o investimenti ammessi | testo |
| `tipo_agevolazione` | Il tipo principale, per il catalogo (valori di `tipi_agevolazione` più `misto`) | valore |
| `tipi_agevolazione` | Tutti i tipi presenti: `fondo_perduto`, `credito_imposta`, `finanziamento_agevolato`, `garanzia`, `voucher`, `servizi` (percorsi o consulenze erogati direttamente), `premio`, `altro` | elenco |
| `temi` | `digitale`, `green`, `internazionalizzazione`, `investimenti`, `formazione`, `ricerca`, `assunzioni`, `avvio_impresa`, `turismo`, `commercio`, `agricoltura`, `cultura`, `credito`, `sicurezza`, `altro` (`tema` resta il principale) | elenco |
| `categorie_spesa` | `macchinari_attrezzature`, `opere_edili_impianti`, `software_digitale`, `consulenze`, `formazione`, `personale`, `fiere_eventi`, `marketing_promozione`, `brevetti_certificazioni`, `veicoli`, `energia_efficienza`, `scorte_circolante`, `immobili`, `affitto_gestione`, `ricerca_sviluppo`, `altro` | elenco |
| `contributo_massimo` | Massimo per singola impresa, in euro, contributo base più alto (i premi aggiuntivi vanno nella sintesi) | numero |
| `percentuale` | Percentuale massima delle spese coperta, comprese le maggiorazioni | 0-100 |
| `fondo_perduto_massimo`, `percentuale_fondo_perduto` | **Solo la quota a fondo perduto**, quando l'aiuto unisce prestito e fondo perduto | numero, 0-100 |
| `finanziamento_massimo` | La parte a prestito, se c'è | numero |
| `spesa_minima`, `spesa_massima` | Progetto minimo e massimo ammesso | numeri |
| `dotazione` | Fondi totali del bando | numero |
| `spese_ammesse` | Le spese a parole, con da quando sono ammissibili (per esempio "solo dopo la concessione") e i termini per realizzare e rendicontare | testo |

### Come e quando

| Campo | Cosa contiene | Formato |
|---|---|---|
| `modalita_selezione` | `sportello` (ordine di arrivo), `sportello_valutativo` (ordine di arrivo con punteggio minimo), `graduatoria` (finestra fissa, poi classifica), `click_day`, `automatica` (crediti d'imposta), `negoziale`, `altro` | valore |
| `data_apertura`, `ora_apertura` | Primo giorno e ora per la domanda | data, ora |
| `scadenza`, `ora_scadenza` | Ultimo giorno e ora (spesso le 12 o le 16). **Vuoto** se "a sportello fino a esaurimento risorse" senza data | data, ora |
| `chiuso_il` | Chiuso prima del tempo (fondi esauriti, sospensione), se i documenti lo dicono | data |
| `stato` | `in_arrivo`, `aperto`, `chiuso`: **calcolato dal sistema** ogni giorno | valore |
| `sintesi` | 3-5 righe in italiano semplice: cosa finanzia, a chi, quanto, come e fino a quando, chi gestisce, graduatoria o sportello | testo |

### Affidabilità e controllo

| Campo | Cosa contiene | Formato |
|---|---|---|
| `vincoli` | Uno stato per ogni vincolo: `territorio`, `soggetti`, `forme_giuridiche`, `dimensioni`, `ateco`, `eta_impresa`, `requisiti_speciali`, `dipendenti`, `fatturato`, `spesa`, `regime_aiuto` | JSON |
| `completezza` | `bando_ufficiale`, `solo_sintesi`, `nessun_documento` | valore |
| `linee` | Elenco facoltativo di linee (vedi sotto) | JSON |
| `qualita` | Voto di Matteo, da 1 (da rifare) a 5 (perfetta) | 1-5 |
| `dati` | La risposta completa dell'IA: fonti di ogni campo, avvertenze, costo | JSON |
| `versione` | Numero della versione; le precedenti stanno in `bandi_versioni` | numero |

**Una linea** (elemento di `linee`) ha: `nome`, `a_chi_si_rivolge` (testo breve), e solo i campi che per quella linea sono diversi dal bando: `soggetti_ammessi`, `dimensioni_ammesse`, `requisiti_speciali_obbligatori`, `eta_impresa_max_mesi`, `codici_ateco`, `codici_ateco_esclusi`, `tipi_agevolazione`, `contributo_massimo`, `percentuale`, `fondo_perduto_massimo`, `spesa_minima`, `spesa_massima`, `note`.

## Campo della scheda ↔ dato del profilo ↔ regola di confronto

Il profilo anonimo del cliente arriva dalle anagrafiche di Matteo (`docs/RICHIESTA_SCHEMA_ANAGRAFICHE.md`). Per ogni vincolo, l'abbinamento guarda **prima lo stato**: `nessun_vincolo` → va bene; `non_noto` → "da verificare"; `vincolo` → si applica la regola. Se al profilo manca il dato, il risultato è "da verificare", mai "compatibile". Anche un `vincolo` con i campi vuoti (settore scritto a parole, solo alcuni comuni, PMI solo in cordata con una grande impresa) dà "da verificare": la verifica automatica (`app/schede/ia.py`, `verifica_scheda`) lo segnala e la condizione si legge in `requisiti`.

| Campo della scheda | Dato del profilo | Regola di confronto |
|---|---|---|
| `territorio_regioni` / `_province` / `_comuni`, `sede_richiesta` | regione, provincia e comune della sede legale e delle sedi operative | almeno una sede del tipo richiesto sta nel territorio (il più preciso dei tre elenchi pieni). `da_attivare`: va bene anche senza sede, con la nota "aprire una sede operativa prima dell'erogazione" |
| `soggetti_ammessi` | tipo di soggetto: impresa iscritta al Registro, libero professionista (sì/no) | il tipo del cliente è nell'elenco |
| `forme_giuridiche_ammesse` / `_escluse` | forma giuridica (ricavata dalla ragione sociale sul lato di Matteo) | nell'elenco degli ammessi (se c'è) e non in quello degli esclusi |
| `dimensioni_ammesse` | classe dimensionale (micro, piccola, media, grande), da dipendenti o ULA, fatturato e totale di bilancio | la classe del cliente è nell'elenco. Senza totale di bilancio la classe è stimata: "da verificare" ai confini |
| `eta_impresa_min_mesi` / `_max_mesi` | data di costituzione o di inizio attività | mesi tra quella data e la data della domanda dentro l'intervallo |
| `requisiti_speciali_obbligatori` | impresa femminile, giovanile, startup innovativa, PMI innovativa, artigiana, agricola, rating di legalità... (sì/no) | il cliente li ha **tutti**. I premiali non escludono: danno solo un "più" nella motivazione |
| `dipendenti_min` / `_max` | numero di dipendenti o ULA | dentro l'intervallo |
| `fatturato_min` / `_max` | fatturato dell'ultimo bilancio | dentro l'intervallo |
| `codici_ateco`, `codici_ateco_esclusi`, `ateco_versione` | ATECO principale e secondari, con la versione | un codice del cliente comincia con un codice ammesso (se l'elenco è pieno) e nessuno comincia con un escluso. Versioni diverse: conversione ATECO 2007↔2025 (Fase 4); finché manca, "da verificare" |
| `regime_aiuto` | aiuti de minimis già ricevuti negli ultimi 3 anni (quando ci saranno, da RNA) | con `de_minimis`: il margine residuo del cliente copre il contributo. Senza il dato: nota "verificare il de minimis" |
| `spesa_minima` / `_massima`, `categorie_spesa` | investimenti previsti (categorie, importo indicativo) | categorie in comune e importo dentro l'intervallo. Serve a ordinare, non a escludere |
| `temi` | interessi del cliente (export sì/no, digitale, green...) | serve a ordinare |
| `linee` | tutti i dati sopra | se il bando ha linee, la motivazione dice quali linee sono adatte al cliente |
| `completezza` | — | `bando_ufficiale` permette "compatibile"; le altre al massimo "da verificare" |
| `stato`, `scadenza`, `ora_scadenza`, `modalita_selezione` | — | si propongono solo bandi `aperto` o `in_arrivo`; `sportello`, `sportello_valutativo` e `click_day` si segnalano come urgenti |

## Esempio compilato a mano

**Bando:** PR FESR 2021-2027, Azione 1.3.1, "Contributi per la partecipazione delle PMI alle fiere internazionali in Lombardia – secondo sportello" (Regione Lombardia, codice RLO12026055023).

**Fonti usate:** la pagina ufficiale su Bandi Online (https://www.bandi.regione.lombardia.it/servizi/servizio/bandi/dettaglio/attivita-produttive-imprese/fiere/pr-fesr-2021-2027-azione-1-3-1-contributi-partecipazione-pmi-fiere-internazionali-lombardia-secondo-sportello-RLO12026055023, trovata dal sistema con la ricerca per codice) e l'allegato "Bando fiere internazionali – Secondo sportello – 07/07/2026", scaricati il 24-25/09/2026 e letti a mano. **I valori sono stati copiati da quei documenti in quelle date e vanno ricontrollati sul bando ufficiale prima di usarli con un cliente:** lo sportello chiude quando finiscono le risorse, e l'ente può modificare il bando.

| Campo | Valore | Fonte |
|---|---|---|
| `titolo` | PR FESR 2021-2027 – Azione 1.3.1 "Contributi per la partecipazione delle PMI alle fiere internazionali in Lombardia – secondo sportello" | pagina |
| `ente` | Regione Lombardia | pagina |
| `gestore` | Unioncamere Lombardia (soggetto gestore e organismo intermedio) | bando, art. A.4 |
| `url` | la pagina di dettaglio qui sopra | sistema (ricerca per codice) |
| `territorio` | Lombardia: sede operativa attiva, o da attivare entro la richiesta di erogazione | bando, art. A.3.3.b |
| `territorio_regioni` | `["LOM"]` | bando, art. A.3.3.b |
| `territorio_province`, `territorio_comuni` | `[]` | |
| `sede_richiesta` | `da_attivare` | bando, art. A.3.3.b |
| `soggetti_ammessi` | `["impresa"]`: solo come espositore diretto, non co-espositore né in forma aggregata | bando, artt. A.3, B.1.b.4 |
| `forme_giuridiche_ammesse`, `_escluse` | `[]` (il bando non ne parla) | |
| `dimensioni_ammesse` | `["micro", "piccola", "media"]` | bando, art. A.3 |
| `eta_impresa_min_mesi`, `_max_mesi` | `null` (le startup fino a 24 mesi hanno solo una maggiorazione) | bando, art. B.1.b.5 |
| `requisiti_speciali_obbligatori` | `[]` | |
| `requisiti_speciali_premiali` | `["nuova_impresa"]` (+5% alle imprese attive da non più di 24 mesi); anche le micro hanno +5% | bando, art. B.1.b.5 |
| `dipendenti_min/max`, `fatturato_min/max` | `null` (oltre alla definizione di PMI) | |
| `codici_ateco` | `[]` (tutti i settori salvo le esclusioni) | bando, art. A.3 |
| `codici_ateco_esclusi` | `["A", "L"]`: agricoltura, silvicoltura e pesca (salvo le imprese agromeccaniche iscritte all'albo regionale); attività finanziarie e assicurative | bando, art. A.3 |
| `ateco_versione` | `2025` | bando, art. A.3 |
| `regime_aiuto` | `["de_minimis"]` (Reg. UE 2023/2831) | bando, art. B.1.c |
| `requisiti` | Iscritta e attiva al Registro delle Imprese; non in liquidazione o procedure concorsuali; DURC regolare; polizza contro i rischi catastrofali (L. 213/2023); esclusi i settori del tabacco e le imprese con sanzioni interdittive | bando, artt. A.3, C.1 |
| `cosa_finanzia` | Partecipazione come espositore a una o al massimo due fiere internazionali in Lombardia del calendario regionale, con inizio tra il 1/9/2026 e il 31/12/2027 | bando, art. B.2 |
| `tipo_agevolazione` / `tipi_agevolazione` | `fondo_perduto` / `["fondo_perduto"]` | pagina |
| `temi` | `["internazionalizzazione"]` | pagina |
| `categorie_spesa` | `["fiere_eventi", "personale"]` | bando, art. B.3 |
| `contributo_massimo` | 15000 (nuovi espositori; vedi `linee`) | bando, art. B.1.b.1 |
| `percentuale` | 60 (50% più 5% micro più 5% startup) | bando, art. B.1.b.5-6 |
| `fondo_perduto_massimo`, `percentuale_fondo_perduto` | 15000, 60 | bando, art. B.1.b |
| `finanziamento_massimo` | `null` | |
| `spesa_minima` | 6000 | bando, art. B.1.b.2 |
| `spesa_massima` | `null` | |
| `dotazione` | 4668350 | bando, art. A.5 |
| `spese_ammesse` | A forfait: 440 € al metro quadro di area espositiva; più 20% di questa voce per il personale; più 7% delle due voci per i costi indiretti. Basta l'attestato dell'organizzatore della fiera. Rendicontazione entro il 29/02/2028 | bando, artt. B.2.b, B.3 |
| `modalita_selezione` | `sportello_valutativo` (ordine di arrivo, almeno 50 punti su 100) | bando, art. C.2 |
| `data_apertura`, `ora_apertura` | 2026-07-30, 10:00 | bando, art. C.1 |
| `scadenza`, `ora_scadenza` | `null`: sportello fino a esaurimento della dotazione (domande accolte fino al 125% della dotazione, poi lista d'attesa) | bando, art. C.1-2 |
| `stato` | calcolato dal sistema: `aperto` dal 30/07/2026 | sistema |
| `vincoli` | territorio `vincolo`, soggetti `vincolo`, forme_giuridiche `nessun_vincolo`, dimensioni `vincolo`, ateco `vincolo`, eta_impresa `nessun_vincolo`, requisiti_speciali `nessun_vincolo`, dipendenti `nessun_vincolo`, fatturato `nessun_vincolo`, spesa `vincolo`, regime_aiuto `vincolo` | |
| `completezza` | `bando_ufficiale` | |
| `linee` | vedi sotto | bando, art. B.1.b.1-3 |

`linee`:

| `nome` | `a_chi_si_rivolge` | `contributo_massimo` | Note |
|---|---|---|---|
| Nuovi espositori | PMI che non hanno partecipato, per nessuna delle fiere del progetto, alle 3 edizioni precedenti (2 per le fiere biennali o più rare) | 15000 | |
| Espositori abituali | PMI che hanno già partecipato almeno una volta a una precedente edizione di una delle fiere del progetto | 8000 | |
| Imprese già beneficiarie | PMI che hanno già avuto la concessione del contributo nel primo sportello | 8000 | vale qualunque sia la partecipazione precedente alla fiera |

**Avvertenza da riportare in `dati`:** la pagina web elenca le esclusioni con ATECO 2007 ("sezione K, attività finanziarie"), il PDF del bando con ATECO 2025 ("sezione L"). Il settore escluso è lo stesso; nella scheda vale la versione del bando ufficiale.

Questo esempio mostra le difficoltà tipiche che la scheda deve gestire: massimali diversi per tipo di beneficiario (le linee), una percentuale che cresce con le maggiorazioni (e le maggiorazioni sono "premiali", non obbligatorie), una scadenza che non è una data, esclusioni di settore invece di un elenco di settori ammessi, pagina e bando che usano versioni diverse dell'ATECO, una sede che basta aprire entro l'erogazione.
