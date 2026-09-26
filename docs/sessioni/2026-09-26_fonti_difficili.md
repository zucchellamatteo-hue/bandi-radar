# Sessione sul server: mappare le fonti che la raccolta non riesce ancora a leggere

*Prompt preparato il 25/09/2026 sera. Da incollare in una nuova sessione di Claude Code sul server (cartella `~/bandi-radar` dell'utente `ubuntu`).*

---

Leggi prima `CLAUDE.md`, `fonti/README.md`, `deploy/MANUALE.md` e le mappature già fatte: `docs/ricerche/2026-09-24_api_nascoste.md` e `docs/ricerche/2026-09-24_verifica_dal_server.md`. Parla con Matteo in italiano semplice, proponi una strada sola e dì perché. Lavori nella copia `~/bandi-radar` su un branch nuovo da `main` (`git pull origin main` prima di partire), mai in `/srv`. Apri una pull request alla fine.

**Autorizzazioni.** In `.claude/settings.local.json` sono già consentiti senza chiedere: `sudo docker`, `sudo -u deploy docker compose`, `git`, `gh`, `python3`, `curl`, i comandi di lettura dei file e gli script in `/tmp/claude-1000/`. Sono vietati la lettura del `.env`, `docker compose down`, la cancellazione di volumi e le modifiche in `/srv`. Usa comandi di queste famiglie, e **raccogli i comandi ripetitivi in script** dentro `/tmp/claude-1000/`, così Matteo non deve approvare ogni comando.

## Dove siamo

Il 25/09 sera la plancia mostrava 70 fonti gialle. Ne sono già state recuperate 27, rilanciandole a mano:
- 18 lette con il browser senza interfaccia;
- 9 bloccate da robots.txt, per le quali Matteo aveva già deciso `ignora_robots`.

Restano circa **40 fonti** senza lettura. Per vederle aggiornate:

```
cd /srv/bandi-radar && sudo -u deploy docker compose exec -T app python -c "
from app.plancia.api import elenco_fonti
for x in elenco_fonti():
    if x['colore'] != 'verde': print(x['id'], '|', x['stato'], '|', x['modalita'], '|', x['motivo'])"
```

Sono di questi tipi (dalle note del registro):

| Problema | Fonti |
|---|---|
| Rispondono ai server con 403, un captcha o un bot manager (Imperva, Radware, Cloudflare/SiteGround) | `cciaa_milano_monza_brianza_lodi_bandi`, `ministero_turismo_strumenti`, `unioncamere_lazio`, `comune_venezia_sito`, `comune_grosseto_sito`, `comune_campobasso_sito`, `campania_regione_bandi_avvisi`, `basilicata_sviluppo_basilicata_incentivi`, `finlombarda_prodotti_imprese`, `comune_lodi_imprese` |
| Chiudono la connessione (reset o timeout) | `comune_chieti_sito`, `comune_isernia_sito`, `comune_macerata_sito`, `comune_rieti_sito`, `comune_viterbo_sito`, `comune_benevento_sito`, `comune_crotone_sito`, `comune_catania_sito`, `comune_lecce`, `comune_potenza`, `basilicata_sito_regione`, `comune_latina_avvisi`, `comune_pesaro_nuove_imprese`, `rna_open_data` |
| Siti Angular o myPortal, con la pagina vuota senza JavaScript | `comune_treviso_sito`, `comune_belluno_sito`, `comune_rovigo_sito`, `provincia_belluno_sito`, `comune_avellino_sito`, `comune_barletta`, `puglia_sistema_puglia` |
| Camere lombarde provate solo dal cloud | `cciaa_cremona_bandi`, `cciaa_mantova_bandi`, `cciaa_pavia_bandi` |
| Altri problemi | `comune_parma_sito` (TLS), `cciaa_salerno_notizie` (Drupal che mostra altro ai server), `comune_ferrara_avvisi` (HTTP 500) |
| Rispondono, ma senza nessuna novità finora (controllare che il selettore sia giusto) | `cciaa_nordsardegna_contributi`, `cciaa_torino_finanziamenti`, `comune_biella_avvisi_rss`, `comune_sondrio_avvisi_rss`, `marche_rss_tematici`, `trento_fesr_calendario_avvisi`, `umbria_bandi_imprese` |

## Il lavoro

Per ogni fonte, in quest'ordine, fermandoti alla prima strada che funziona:

1. **Riprova dal server**:
   - con la raccolta: `cd /srv/bandi-radar && sudo -u deploy docker compose run --rm -T raccolta python -m app.raccolta.esegui --prova ID_FONTE`, che non scrive nulla;
   - con `curl`, in IPv4 e in IPv6 (`richiesta: {ipv6: true}` nel registro), con e senza `www`, in `http` e `https`.
2. **Browser senza interfaccia** (Chromium nel container `raccolta`): apri la pagina, aspetta, guarda le chiamate di rete. Se la pagina si riempie da un'API interna, registra quella (`modalita: api`, blocco `richiesta`), come in `2026-09-24_api_nascoste.md`. Per i siti myPortal della Regione Veneto cerca l'API comune a tutti: una sola soluzione vale per 4 fonti.
3. **Un'altra porta dello stesso ente**: feed RSS, sitemap, sezione "Amministrazione trasparente" o albo pretorio su piattaforme esterne (Halley, Maggioli, JCity...), open data. Per le Camere anche la pagina della Unioncamere regionale o il catalogo incentivi.gov.it, che spesso ripubblica i loro bandi.
4. **Se niente funziona**: lascia la fonte `difficile`, scrivi nelle note cosa hai provato e con che esito, e proponi a Matteo una sola alternativa, per esempio "si prova dal PC di Matteo" o "si esclude: i bandi di questo ente arrivano già da incentivi.gov.it". **Mai aggirare un captcha o un bot manager** e mai insistere con richieste ripetute: due o tre tentativi per indirizzo, con pause.

Per le fonti "senza novità" controlla che la voce del registro legga davvero l'elenco dei bandi (selettore, feed giusto) e correggila.

Regole ferme:
- indirizzi nel registro **solo se aperti davvero**;
- si rispetta robots.txt, salvo le fonti in cui Matteo ha già deciso `ignora_robots`: per quelle nuove chiedi a lui;
- User-Agent del progetto;
- un controllo per fonte;
- mai stampare il `.env`;
- mai modificare `/srv/bandi-radar`.

Puoi lanciare agenti in parallelo per gruppi di fonti (per esempio: bot manager, connessioni chiuse, Angular/myPortal, Camere, senza novità), al massimo 5. Ogni agente riporta, per ogni fonte, la strada trovata e la prova.

## Alla fine

- Aggiorna il registro (`fonti/*.yaml`): indirizzo, modalità, `richiesta`, `stato` e `note` con la data. Controllo: `python -m app.fonti.verifica` (in un container con le dipendenze) e `pytest` senza rete.
- Scrivi la mappatura in `docs/ricerche/AAAA-MM-GG_fonti_difficili.md` secondo `docs/ricerche/README.md`: una riga per fonte con esito `sì` / `no` / `non chiaro` e cosa si è provato. Aggiorna l'indice.
- Dopo l'unione della pull request, rilancia le fonti sistemate con `--fonte ID` e riporta a Matteo quante sono diventate verdi.
- Riepilogo per Matteo in 10 righe: quante fonti recuperate, quante restano e perché, cosa serve da lui (decisioni su robots.txt, prove dal suo PC, esclusioni).
