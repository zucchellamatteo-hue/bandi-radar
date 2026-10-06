# Revisione periodica dell'architettura — istruzioni

Richiesta di Matteo (`docs/VISIONE.md`, richiesta 2): **ogni due settimane** (al più tardi ogni mese) un controllo
del sistema nel suo insieme che trovi falle, sprechi, costi da ridurre e qualità da migliorare, con un rapporto e
proposte concrete, **confrontato con la revisione precedente**. Prima revisione: 06/10/2026 (voto 6,5/10).

Obiettivo di riferimento: affidabilità da 7-8 a **9/10** prima di vendere, senza perdere le misure famose, con
l'IA dentro **100 $ al mese**.

## Regole

- **Sola lettura**: nessuna modifica a database, `/srv` o container. I file di lavoro vanno in `/tmp/claude-1000/cp/`.
- Database in lettura con `bash /tmp/claude-1000/sql.sh "SELECT ..."` o `bash /tmp/claude-1000/sql.sh -f file.sql`.
- Sequenze di comandi solo in script `.sh` in `/tmp/claude-1000/` (niente `&&` o `|` sulla riga di comando).
- Non leggere il `.env` (segreti): gli interruttori si deducono dai riepiloghi delle esecuzioni e dalla Supervisione.
- Negli `\echo` dei file SQL non usare apostrofi (psql li prende per l'inizio di una stringa).
- Alla fine (in una sessione che può fare commit): rapporto e indicatori in `docs/revisioni/` con una pull request,
  prossimo passo 33 aggiornato, eventuali nuovi prossimi passi per le azioni decise.

## Passi (circa un'ora di lavoro)

1. **Leggere il contesto**: `CLAUDE.md`, `docs/VISIONE.md`, `docs/COME_FUNZIONA.md`, `docs/ORCHESTRAZIONE.md`,
   `docs/CRONOLOGIA.md` (solo i giorni dopo la revisione precedente), la revisione precedente
   (`docs/revisioni/AAAA-MM-GG.md`) e i prossimi passi aperti
   (`SELECT id, tipo, stato, priorita, titolo FROM prossimi_passi WHERE stato <> 'fatto' ORDER BY priorita`).
2. **Ricalcolare gli indicatori**: copiare lo SQL qui sotto in `/tmp/claude-1000/cp/ra_indicatori.sql` e lo script
   `ra_csv.sh` (più sotto) in `/tmp/claude-1000/cp/`, poi `bash /tmp/claude-1000/cp/ra_csv.sh` → file
   `indicatori_AAAA-MM-GG.csv` (`data;indicatore;valore`).
3. **Confrontare con la volta precedente**: aggiungere le righe nuove a `docs/revisioni/indicatori.csv` (una riga per
   indicatore e per data: la tabella si allunga nel tempo) e preparare la colonna "prima → adesso → tendenza" per
   ogni indicatore. Segnalare in evidenza ogni indicatore peggiorato di oltre il 10% o passato da 0 a più di 0 dove
   0 è l'obiettivo (S04, S07, R03, R04, F03).
4. **Approfondire con le query di dettaglio** (sezione "Query di dettaglio") solo sulle aree che peggiorano o che
   erano tra le 10 falle della volta prima: per ogni falla dire se è **chiusa, migliorata, uguale, peggiorata**, con il
   numero.
5. **Controlli fuori dal database** (dal server):
   - backup: `ls -lh /var/backups/bandi-radar` (ci sono tutti i giorni? dimensione in crescita regolare?) e se esiste
     la copia fuori dal server;
   - disco: `df -h /` (allarme sopra l'80%);
   - deploy: `systemctl list-timers --all --no-pager` (il timer `bandi-radar-deploy` gira);
   - test automatici: ultimi esiti delle azioni GitHub (`gh run list --limit 10`);
   - pagina **Supervisione** e **Lavorazione** se c'è un browser.
6. **Misure famose**: se nelle due settimane è stata fatta la ricerca dei bandi più discussi (prossimo passo 27),
   riportare quante sono assenti o con difetti; altrimenti farla su un campione di 20 misure note.
7. **Costi**: spesa del mese, spesa degli ultimi 7 giorni × 4,3 come proiezione mensile, costo medio di una scheda;
   confronto con il tetto di 100 $; stima dei giorni per smaltire gli arretrati (formula sotto).
8. **Scrivere il rapporto** `docs/revisioni/AAAA-MM-GG.md` con la stessa struttura della prima revisione:
   1. quadro in una pagina (imbuto con i numeri); 2. voto per area (fonti, smistamento, doppioni, documenti, schede,
   controlli, abbinamento, email, costi, sicurezza) **con il voto della volta prima**; 3. le 10 falle in ordine di
   impatto con la prova numerica e lo stato rispetto alla volta prima; 4. tabella "cosa lascia un risultato
   ispezionabile"; 5. costi e tetto; 6. cinque risparmi; 7. cinque miglioramenti di qualità; 8. piano in passi
   piccoli; 9. cosa non si è potuto verificare.
9. **Rispondere a Matteo** in italiano semplice: voto complessivo (e di quanto è cambiato), 5 falle principali,
   3 risparmi, prime 5 azioni consigliate.

## Come dare i voti (scala comune, così i voti sono confrontabili)

| Voto | Significato |
|---|---|
| 9-10 | funziona, è misurato, ha un secondo controllo e un avviso se si rompe |
| 7-8 | funziona e si vede, ma senza secondo controllo o con un difetto noto misurabile |
| 5-6 | funziona in parte: difetti che il cliente può vedere, oppure nessuna misura dell'errore |
| 3-4 | spento o non provato su casi veri |
| 1-2 | rotto |

Voto complessivo: media dei voti per area, con peso doppio per fonti, doppioni, schede e controlli (sono quelli che
decidono "non perdere le misure famose" e "90% delle schede affidabili").

## Formule per i costi

- Costo medio di una scheda in lotto: dal campo `costo_usd` delle chiamate `scopo='scheda'` con `batch` ed
  `esito='ok'`; se non ci sono abbastanza casi, stimarlo: (caratteri del fascicolo / 3,2 + 15.000 di istruzioni) ×
  2 $/milione + 13.000 × 10 $/milione (prezzi Opus 5.5 in lotto, `PREZZI` in `app/schede/ia.py`). Il 06/10: 0,30 $ in
  media, 0,45 $ per i fascicoli pieni.
- Spesa a regime al mese = schede nuove al mese × costo scheda + schede da aggiornare × costo scheda + (smistamenti,
  doppioni, preliminari) al costo misurato.
- Giorni per smaltire un arretrato = costo dell'arretrato / (100 $ − spesa a regime) × 30.

## Indicatori (una riga per indicatore)

Codici stabili: se si aggiunge un indicatore, dargli un codice nuovo; non cambiare il significato di uno vecchio
(altrimenti la tendenza non vale più). Obiettivi indicativi per il 9/10 tra parentesi.

| Codice | Cosa misura | Obiettivo |
|---|---|---|
| F01-F07 | fonti attive, difficili, in errore, non controllate, silenziose (anche nazionali/UE), % errori | F03 = 0, F06 ≤ 2, F07 < 3% |
| A01-A04 | annunci nuovi, da rivedere, rilevanti senza bando, quota decisa dall'IA | A02 < 50, A03 = 0 |
| B01-B11 | imbuto dei bandi: pagina, filtro, preliminare, fermati come chiusi, scheda in attesa, da aggiornare | B06 = 0, B09 = 0, B10 < 30 |
| S01-S08 | schede proponibili, aperte, gravi, nascoste, da migliorare %, senza stato, incoerenti, non ricontrollate | S04 = 0, S05 < 20%, S06 = 0, S07 = 0 |
| D01-D05 | doppioni probabili (stessa url_chiave, edizioni mescolate), dubbi aperti, file persi per il limite, % file in errore | D01 e D02 in calo |
| Q01-Q03 | feedback ricevuti, da gestire, voto medio | Q01 in crescita, Q03 ≥ 4 |
| I01-I05 | spesa IA del mese, delle schede, ultimi 7 giorni, chiamate in errore, costo medio scheda | I01 < 100 $ |
| R01-R04 | giri del regista in 24 ore, durata massima, esecuzioni interrotte, esecuzioni in errore | R01 ≥ 20, R03 = 0, R04 = 0 |
| M01-M03 | imprese, profili, email preparate | in crescita dal pilota |
| P01, X01 | prossimi passi aperti, dimensione del database | — |

Valori del 06/10/2026 (punto di partenza): F01 267, F02 16, F03 4, F05 10, F06 6, F07 5,6%; A02 353, A03 23;
B03 240, B04 242, B07 996, B08 341, B09 50, B10 3; S01 671, S02 383, S03 33, S04 32, S05 63%, S06 40, S08 21;
D01 37, D02 92, D04 2.961, D05 14,1%; Q01 1; I01 11,86 $; R01 36, R03 4; M01 0. Elenco completo:
`docs/revisioni/indicatori.csv` (da creare alla prima pull request con le righe di
`/tmp/claude-1000/cp/indicatori_2026-10-06.csv`).

### SQL degli indicatori (`/tmp/claude-1000/cp/ra_indicatori.sql`)

```sql
-- Indicatori della revisione dell'architettura: una riga per indicatore (codice, valore).
-- Uso: bash /tmp/claude-1000/sql.sh -f /tmp/claude-1000/cp/ra_indicatori.sql
WITH
prop AS (SELECT * FROM bandi WHERE unito_a IS NULL AND completezza = 'bando_ufficiale'),
bv AS (SELECT * FROM bandi WHERE unito_a IS NULL),
ultc AS (SELECT DISTINCT ON (fonte_id) fonte_id, esito, iniziato_il FROM controlli ORDER BY fonte_id, iniziato_il DESC),
fatt AS (SELECT f.id, f.tipo FROM fonti f WHERE f.stato = 'attiva' AND NOT f.in_pausa),
nov AS (SELECT fa.id, count(a.id) FILTER (WHERE a.trovato_il > now() - interval '14 days' AND NOT coalesce(a.da_scorta, false)) n14
        FROM fatt fa LEFT JOIN annunci a ON a.fonte_id = fa.id GROUP BY 1),
ia AS (SELECT scopo, sum(costo_usd) usd, count(*) n FROM chiamate_ia WHERE fatta_il >= date_trunc('month', now()) GROUP BY 1)
SELECT * FROM (VALUES
 ('F01 fonti attive', (SELECT count(*) FROM fatt)::numeric),
 ('F02 fonti difficili o da verificare', (SELECT count(*) FROM fonti WHERE stato IN ('difficile','da_verificare'))),
 ('F03 fonti attive con ultimo controllo in errore', (SELECT count(*) FROM fatt JOIN ultc ON ultc.fonte_id = fatt.id WHERE ultc.esito <> 'ok')),
 ('F04 fonti attive senza controllo da 35 giorni', (SELECT count(*) FROM fatt LEFT JOIN ultc ON ultc.fonte_id = fatt.id WHERE ultc.iniziato_il IS NULL OR ultc.iniziato_il < now() - interval '35 days')),
 ('F05 fonti attive senza annunci nuovi in 14 giorni', (SELECT count(*) FROM nov WHERE n14 = 0)),
 ('F06 fonti nazionali/UE attive senza annunci nuovi in 14 giorni', (SELECT count(*) FROM nov JOIN fatt USING (id) WHERE n14 = 0 AND tipo IN ('nazionale','ue'))),
 ('F07 controlli in errore ultimi 14 giorni (%)', (SELECT round(100.0 * count(*) FILTER (WHERE esito <> 'ok') / greatest(count(*),1), 1) FROM controlli WHERE iniziato_il > now() - interval '14 days')),
 ('A01 annunci novita ultimi 14 giorni', (SELECT count(*) FROM annunci WHERE trovato_il > now() - interval '14 days' AND NOT coalesce(da_scorta,false))),
 ('A02 annunci da rivedere', (SELECT count(*) FROM smistamenti WHERE esito = 'da_rivedere')),
 ('A03 annunci rilevanti senza bando', (SELECT count(*) FROM annunci a JOIN smistamenti s ON s.annuncio_id = a.id WHERE s.esito = 'rilevante' AND a.bando_id IS NULL)),
 ('A04 smistamenti decisi dall IA (%)', (SELECT round(100.0 * count(*) FILTER (WHERE deciso_da = 'ia') / greatest(count(*),1), 1) FROM smistamenti)),
 ('B01 bandi (non uniti)', (SELECT count(*) FROM bv)),
 ('B02 bandi uniti a un altro', (SELECT count(*) FROM bandi WHERE unito_a IS NOT NULL)),
 ('B03 pagina ufficiale non trovata', (SELECT count(*) FROM bv WHERE pagina_stato = 'non_trovata')),
 ('B04 documenti da valutare (filtro non fatto)', (SELECT count(*) FROM bv WHERE documentazione IS NULL)),
 ('B05 con testo ufficiale', (SELECT count(*) FROM bv WHERE documentazione = 'bando')),
 ('B06 testo ufficiale senza preliminare', (SELECT count(*) FROM bv WHERE documentazione = 'bando' AND preliminare IS NULL)),
 ('B07 testo ufficiale fermati come chiusi (senza scheda)', (SELECT count(*) FROM bv WHERE documentazione = 'bando' AND completezza IS NULL AND preliminare->>'stato' = 'chiuso')),
 ('B08 di cui chiusi dai segnali senza IA', (SELECT count(*) FROM bv WHERE documentazione = 'bando' AND completezza IS NULL AND preliminare->>'stato' = 'chiuso' AND preliminare->>'deciso_da' = 'segnali')),
 ('B09 fermati come chiusi o non per imprese ma con scadenza futura', (SELECT count(*) FROM bv WHERE documentazione = 'bando' AND completezza IS NULL AND (preliminare->>'stato' = 'chiuso' OR preliminare->>'per_imprese' = 'no') AND scadenza >= current_date)),
 ('B10 scheda in attesa (preliminare passato, senza scheda)', (SELECT count(*) FROM bv WHERE documentazione = 'bando' AND completezza IS NULL AND preliminare IS NOT NULL AND coalesce(preliminare->>'per_imprese','') <> 'no' AND coalesce(preliminare->>'stato','') <> 'chiuso' AND coalesce(preliminare->>'edizione_in_corso','') <> 'no' AND coalesce(preliminare->>'testo_bando','') <> 'no')),
 ('B11 schede da aggiornare', (SELECT count(*) FROM bv WHERE da_aggiornare IS NOT NULL)),
 ('S01 schede proponibili (bando ufficiale)', (SELECT count(*) FROM prop)),
 ('S02 proponibili aperte o in arrivo', (SELECT count(*) FROM prop WHERE stato IN ('aperto','in_arrivo','prorogato'))),
 ('S03 proponibili con problemi gravi', (SELECT count(*) FROM prop WHERE jsonb_array_length(coalesce(controllo->'gravi','[]')) > 0)),
 ('S04 aperte o in arrivo con problemi gravi (nascoste ai clienti)', (SELECT count(*) FROM prop WHERE stato IN ('aperto','in_arrivo','prorogato') AND jsonb_array_length(coalesce(controllo->'gravi','[]')) > 0)),
 ('S05 proponibili da migliorare (%)', (SELECT round(100.0 * count(*) FILTER (WHERE jsonb_array_length(coalesce(controllo->'da_migliorare','[]')) > 0) / greatest(count(*),1), 1) FROM prop)),
 ('S06 proponibili senza stato', (SELECT count(*) FROM prop WHERE stato IS NULL)),
 ('S07 proponibili aperte scadute (stato incoerente)', (SELECT count(*) FROM prop WHERE stato IN ('aperto','prorogato') AND scadenza < current_date)),
 ('S08 proponibili non ricontrollate (stato) da 8 giorni', (SELECT count(*) FROM prop WHERE stato IS DISTINCT FROM 'chiuso' AND (stato_ricontrollato_il IS NULL OR stato_ricontrollato_il < now() - interval '8 days'))),
 ('D01 gruppi di bandi non uniti con la stessa url_chiave', (SELECT count(*) FROM (SELECT url_chiave FROM bv WHERE url_chiave IS NOT NULL GROUP BY 1 HAVING count(*) > 1) x)),
 ('D02 bandi con annunci a oltre 300 giorni di distanza (edizioni mescolate?)', (SELECT count(*) FROM (SELECT bando_id FROM annunci WHERE bando_id IS NOT NULL AND pubblicato_il IS NOT NULL GROUP BY 1 HAVING max(pubblicato_il) - min(pubblicato_il) > interval '300 days') x)),
 ('D03 doppioni dubbi senza decisione', (SELECT count(*) FROM bandi_dubbi WHERE decisione IS NULL)),
 ('D04 documenti non scaricati per il limite di 30 file', (SELECT count(*) FROM allegati WHERE errore LIKE 'non scaricato: gia%')),
 ('D05 documenti in errore (%)', (SELECT round(100.0 * count(*) FILTER (WHERE errore IS NOT NULL) / greatest(count(*),1), 1) FROM allegati)),
 ('Q01 feedback totali', (SELECT count(*) FROM feedback)),
 ('Q02 feedback da gestire', (SELECT count(*) FROM feedback WHERE stato NOT IN ('corretto','respinto','gestito'))),
 ('Q03 voto medio feedback', (SELECT round(avg(voto), 2) FROM feedback)),
 ('I01 spesa IA del mese (USD)', (SELECT round(coalesce(sum(usd),0), 2) FROM ia)),
 ('I02 spesa IA schede del mese (USD)', (SELECT round(coalesce(sum(usd),0), 2) FROM ia WHERE scopo = 'scheda')),
 ('I03 spesa IA ultimi 7 giorni (USD)', (SELECT round(coalesce(sum(costo_usd),0), 2) FROM chiamate_ia WHERE fatta_il > now() - interval '7 days')),
 ('I04 chiamate IA in errore ultimi 14 giorni', (SELECT count(*) FROM chiamate_ia WHERE esito = 'errore' AND fatta_il > now() - interval '14 days')),
 ('I05 costo medio scheda batch ultimi 30 giorni (USD)', (SELECT round(avg(costo_usd), 3) FROM chiamate_ia WHERE scopo = 'scheda' AND batch AND esito = 'ok' AND costo_usd > 0.05 AND fatta_il > now() - interval '30 days')),
 ('R01 giri del regista ultime 24 ore', (SELECT count(*) FROM esecuzioni WHERE sistema = 'regista' AND iniziato_il > now() - interval '24 hours')),
 ('R02 durata massima del regista ultimi 7 giorni (s)', (SELECT round(max(extract(epoch FROM finito_il - iniziato_il))) FROM esecuzioni WHERE sistema = 'regista' AND iniziato_il > now() - interval '7 days')),
 ('R03 esecuzioni rimaste in corso (interrotte) ultimi 14 giorni', (SELECT count(*) FROM esecuzioni WHERE finito_il IS NULL AND iniziato_il < now() - interval '2 hours' AND iniziato_il > now() - interval '14 days')),
 ('R04 esecuzioni in errore ultimi 14 giorni', (SELECT count(*) FROM esecuzioni WHERE esito = 'errore' AND iniziato_il > now() - interval '14 days')),
 ('M01 imprese iscritte', (SELECT count(*) FROM imprese)),
 ('M02 profili', (SELECT count(*) FROM profili)),
 ('M03 email alle imprese preparate ultimi 14 giorni', (SELECT count(*) FROM email_imprese WHERE creata_il > now() - interval '14 days')),
 ('P01 prossimi passi da fare o in corso', (SELECT count(*) FROM prossimi_passi WHERE stato IN ('da_fare','in_corso'))),
 ('X01 dimensione database (MB)', (SELECT round(pg_database_size(current_database()) / 1e6)))
) AS t(indicatore, valore);
```

### Script per salvare gli indicatori (`/tmp/claude-1000/cp/ra_csv.sh`)

```bash
#!/bin/bash
# Salva gli indicatori come CSV: data;indicatore;valore
D=${1:-$(date +%F)}
cd /srv/bandi-radar || exit 1
sudo -u deploy docker compose exec -T db psql -U postgres bandi_radar -A -t -F ';' < /tmp/claude-1000/cp/ra_indicatori.sql > /tmp/claude-1000/cp/ra_tmp.txt
sed "s/^/$D;/" /tmp/claude-1000/cp/ra_tmp.txt > /tmp/claude-1000/cp/indicatori_$D.csv
wc -l /tmp/claude-1000/cp/indicatori_$D.csv
```

Per il confronto: con `docs/revisioni/indicatori.csv` (tutte le date) basta un piccolo script Python che legga il
file e stampi, per ogni indicatore, il valore della data precedente e di oggi con la differenza.

## Query di dettaglio (da usare dove serve)

```sql
-- Fonti attive: ultimo controllo in errore, con il messaggio
WITH l AS (SELECT DISTINCT ON (fonte_id) fonte_id, esito, iniziato_il, left(messaggio,80) m FROM controlli ORDER BY fonte_id, iniziato_il DESC)
SELECT f.id, f.frequenza, l.esito, l.iniziato_il::date, l.m FROM fonti f LEFT JOIN l ON l.fonte_id = f.id
WHERE f.stato = 'attiva' AND NOT f.in_pausa AND (l.esito IS DISTINCT FROM 'ok' OR l.iniziato_il < now() - interval '35 days') ORDER BY 1;

-- Fonti nazionali e UE: ultimo annuncio pubblicato e trovato
SELECT f.id, f.modalita, f.frequenza, count(a.id) n, max(a.pubblicato_il)::date ult_pubbl, max(a.trovato_il)::date ult_trov
FROM fonti f LEFT JOIN annunci a ON a.fonte_id = f.id WHERE f.stato = 'attiva' AND f.tipo IN ('nazionale','ue') GROUP BY 1,2,3 ORDER BY 6 NULLS FIRST;

-- Fonti per territorio (territori scoperti: poche attive, molte difficili)
SELECT territorio, count(*) FILTER (WHERE stato = 'attiva') attive, count(*) FILTER (WHERE stato <> 'attiva') altre FROM fonti GROUP BY 1 ORDER BY 1;

-- Bandi con testo ufficiale e senza scheda: perche si sono fermati e chi lo ha deciso
SELECT CASE WHEN preliminare IS NULL THEN 'manca preliminare' WHEN preliminare->>'per_imprese' = 'no' THEN 'non per imprese'
 WHEN preliminare->>'stato' = 'chiuso' THEN 'chiuso' WHEN preliminare->>'edizione_in_corso' = 'no' THEN 'edizione vecchia'
 WHEN preliminare->>'testo_bando' = 'no' THEN 'senza testo' ELSE 'scheda in attesa' END fase,
 coalesce(preliminare->>'deciso_da', preliminare->>'compilato_da', '-') chi, count(*)
FROM bandi WHERE unito_a IS NULL AND documentazione = 'bando' AND completezza IS NULL GROUP BY 1,2 ORDER BY 3 DESC;

-- Segnali di chiusura senza IA: quali frasi pesano di piu (controllare a campione le piu frequenti)
SELECT regexp_replace(preliminare->>'motivo','[0-9/]+','N','g') m, count(*) FROM bandi WHERE preliminare->>'deciso_da' = 'segnali' GROUP BY 1 ORDER BY 2 DESC LIMIT 15;

-- Problemi gravi e da migliorare per tipo (schede proponibili)
SELECT regexp_replace(g,'[0-9.,]+','N','g') tipo, count(*) FROM bandi, jsonb_array_elements_text(controllo->'gravi') g
WHERE unito_a IS NULL AND completezza = 'bando_ufficiale' GROUP BY 1 ORDER BY 2 DESC;
SELECT left(regexp_replace(g,'[0-9.,]+','N','g'),90) tipo, count(*) FROM bandi, jsonb_array_elements_text(controllo->'da_migliorare') g
WHERE unito_a IS NULL AND completezza = 'bando_ufficiale' GROUP BY 1 ORDER BY 2 DESC LIMIT 12;

-- Doppioni probabili: gruppi con lo stesso indirizzo chiave (da far guardare a un agente)
SELECT url_chiave, count(*), string_agg(id::text, ',') FROM bandi WHERE unito_a IS NULL AND url_chiave IS NOT NULL GROUP BY 1 HAVING count(*) > 1 ORDER BY 2 DESC;

-- Edizioni mescolate: bandi con annunci molto lontani nel tempo
SELECT bando_id, min(pubblicato_il)::date, max(pubblicato_il)::date, count(*) FROM annunci WHERE bando_id IS NOT NULL AND pubblicato_il IS NOT NULL
GROUP BY 1 HAVING max(pubblicato_il) - min(pubblicato_il) > interval '300 days' ORDER BY 2 LIMIT 30;

-- Documenti: errori per causa
SELECT left(errore,60), count(*) FROM allegati WHERE errore IS NOT NULL GROUP BY 1 ORDER BY 2 DESC LIMIT 10;

-- Pagine ufficiali non trovate per sito
SELECT left(pagina_motivo,60), count(*) FROM bandi WHERE pagina_stato = 'non_trovata' AND unito_a IS NULL GROUP BY 1 ORDER BY 2 DESC LIMIT 10;

-- Costi IA per scopo, modo e mese
SELECT to_char(fatta_il,'YYYY-MM') mese, scopo, batch, modello, count(*), sum(token_in) tin, sum(token_out) tout,
 round(sum(costo_usd)::numeric,2) usd, round(avg(costo_usd)::numeric,4) medio FROM chiamate_ia GROUP BY 1,2,3,4 ORDER BY 1,2;

-- Spesa per giorno (ultimi 30)
SELECT fatta_il::date, round(sum(costo_usd)::numeric,2), count(*) FROM chiamate_ia WHERE fatta_il > now() - interval '30 days' GROUP BY 1 ORDER BY 1;

-- Flusso: bandi creati al giorno e quanti arrivano al testo e alla scheda (per la stima a regime)
SELECT creato_il::date g, count(*) bandi, count(*) FILTER (WHERE documentazione = 'bando') testo, count(*) FILTER (WHERE completezza = 'bando_ufficiale') scheda
FROM bandi WHERE creato_il > now() - interval '14 days' GROUP BY 1 ORDER BY 1;

-- Lunghezza del fascicolo delle schede (per il costo di una scheda)
SELECT width_bucket(n, ARRAY[25000,50000,100000,200000,299999]) fascia, count(*) bandi, round(avg(n)) media_caratteri
FROM (SELECT b.id, least(sum(length(a.testo_estratto)), 300000) n FROM bandi b JOIN allegati a ON a.bando_id = b.id AND a.errore IS NULL
 AND a.categoria IS DISTINCT FROM 'modulistica' WHERE b.documentazione = 'bando' AND b.completezza = 'bando_ufficiale' AND b.unito_a IS NULL GROUP BY 1) x
GROUP BY ROLLUP(1) ORDER BY 1;

-- Regista e sistemi: durate, esecuzioni interrotte, ultimo riepilogo
SELECT sistema, count(*), count(*) FILTER (WHERE esito <> 'ok') ko, round(avg(extract(epoch FROM finito_il - iniziato_il))) media_s,
 round(max(extract(epoch FROM finito_il - iniziato_il))) max_s, count(*) FILTER (WHERE finito_il IS NULL) non_finiti
FROM esecuzioni WHERE iniziato_il > now() - interval '14 days' GROUP BY 1 ORDER BY 1;
SELECT sistema, left(riepilogo,160) FROM (SELECT DISTINCT ON (sistema) sistema, riepilogo FROM esecuzioni ORDER BY sistema, id DESC) x;

-- Eventi del regista per passo (quali fasi lasciano traccia)
SELECT passo, esito, count(*) FROM eventi_catena WHERE quando > now() - interval '14 days' GROUP BY 1,2 ORDER BY 1,3 DESC;
```

## Le 10 falle della prima revisione (06/10/2026): da ricontrollare ogni volta

| # | Falla | Indicatori | Valore 06/10 |
|---|---|---|---|
| 1 | Doppioni tra fonti ed edizioni mescolate | D01, D02 (+ doppioni tra le misure famose) | 37 gruppi, 92 bandi, 19/66 famose |
| 2 | Bandi fermati come chiusi mai riverificati | B07, B08, B09 | 996, 341, 50 |
| 3 | Fonti mancanti o lette solo in superficie | F02, F06, misure famose assenti | 16, 6, 11/66 |
| 4 | Nessun secondo controllo del contenuto delle schede | gravi trovati dalla verifica IA / schede verificate | pilota 2/19 |
| 5 | Schede aperte nascoste per problemi gravi | S04, S06 | 32, 40 |
| 6 | Server unico, backup sullo stesso disco | backup esterno sì/no, prova di ripristino sì/no | no, no |
| 7 | Nessun avviso automatico a Matteo | riepilogo del lunedì ricevuto, M03 | non partito, 0 |
| 8 | Il deploy interrompe il lavoro in corso | R03 | 4 (6 in tutto) |
| 9 | Documenti persi per limiti e blocchi | D04, D05, B03 | 2.961, 14,1%, 240 |
| 10 | Pagine cambiate non lette (proroghe, nuove date) | B11, eventi "pagina cambiata" vs "scheda da aggiornare" | 0; 108 contro 1 |

## Cosa deve lasciare ogni fase (richiesta di Matteo)

Ad ogni revisione, aggiornare questa tabella: ogni fase deve lasciare un risultato che un agente orchestratore
possa leggere e analizzare (tabella, colonna o file con data e motivo). Situazione del 06/10:

| Fase | Risultato leggibile | Mancava il 06/10 |
|---|---|---|
| Raccolta | `controlli`, `annunci` | motivo del silenzio di una fonte |
| Smistamento | `smistamenti`, `eventi_catena` | misura dell'errore su un campione |
| Doppioni | `bandi_dubbi`, `eventi_catena`, `annunci.collegamento_motivo` | rapporto dei doppioni probabili non uniti |
| Pagina e documenti | `bandi.pagina_stato/pagina_motivo`, `allegati` | righe in `eventi_catena` (quando e perché) |
| Filtro | `bandi.documentazione_motivo` | storico |
| Preliminare | `bandi.preliminare` | storico e secondo parere |
| Scheda | `bandi_versioni`, `chiamate_ia` | traccia uniforme delle schede di sessione |
| Controllo | `bandi.controllo` | esito della verifica IA salvato nel database |
| Abbinamento | — | risultati salvati per profilo e data |
| Email | `email_imprese`, `notifiche_inviate` | — |
| Revisione | `docs/revisioni/` | — |
