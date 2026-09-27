export const meta = {
  name: 'valuta-efficacia',
  description: 'Valutazione efficacia Bandi Radar: per ogni fonte esploratore Opus, Haiku e Opus in parallelo, controllore, giudice schede, verifica di riserva',
  phases: [
    { title: 'Lavoro', detail: 'esploratore Opus, Haiku (leggero), Opus (riferimento), scheda Opus' },
    { title: 'Controllo', detail: 'controllore Opus e giudice delle schede' },
    { title: 'Riserva', detail: 'verifica avversaria Opus dei disaccordi e dei bandi persi' },
  ],
}

const OGGI = '2026-09-26'
const UA = 'BandiRadar/0.1 (+https://finanzagevolata.qiaro.it; raccolta bandi per imprese)'
const COMUNE = `Contesto: Bandi Radar raccoglie bandi di finanza agevolata per imprese italiane (contributi, finanziamenti agevolati, voucher, crediti d'imposta, garanzie, premi per imprese) e li trasforma in schede. Oggi e' ${OGGI}. Stai partecipando a una VALUTAZIONE DI EFFICACIA: lavora con cura, niente invenzioni, se non sai scrivilo.
Regole pratiche: i percorsi che iniziano con /out/ vanno letti come /tmp/claude-1000/sp/schede/ (esempio: /out/fascicoli/388/scheda.md -> /tmp/claude-1000/sp/schede/fascicoli/388/scheda.md). Leggi i file con Read (a pezzi con offset/limit se lunghi). Scrivi i risultati con Write, JSON valido (virgolette doppie, niente commenti). Non modificare altri file. Da Bash solo comandi singoli (niente pipe, &&, ;).`

const SMIST = { type: 'object', properties: { scritti: { type: 'integer' }, note: { type: 'string' } }, required: ['scritti', 'note'] }
const ESPLORA = { type: 'object', properties: { raggiungibile: { type: 'boolean' }, bandi_trovati: { type: 'integer' }, note: { type: 'string' } }, required: ['raggiungibile', 'bandi_trovati', 'note'] }
const CONTEGGI = {
  type: 'object',
  properties: {
    perimetro_bandi_sul_sito: { type: 'integer' }, perimetro_trovati_da_radar: { type: 'integer' },
    persi_non_raccolti: { type: 'integer' }, persi_smistamento: { type: 'integer' }, persi_deduplica_o_dubbio: { type: 'integer' },
    persi_pagina_ufficiale: { type: 'integer' }, persi_preliminare: { type: 'integer' },
    smistamento_valutati: { type: 'integer' }, errori_regole: { type: 'integer' }, errori_haiku: { type: 'integer' }, errori_opus: { type: 'integer' },
    preliminari_valutati: { type: 'integer' }, errori_preliminare_produzione: { type: 'integer' }, errori_preliminare_haiku_nuovo: { type: 'integer' }, errori_preliminare_opus: { type: 'integer' },
    note: { type: 'string' },
  },
  required: ['perimetro_bandi_sul_sito', 'perimetro_trovati_da_radar', 'persi_non_raccolti', 'persi_smistamento', 'persi_deduplica_o_dubbio', 'persi_pagina_ufficiale', 'persi_preliminare', 'smistamento_valutati', 'errori_regole', 'errori_haiku', 'errori_opus', 'preliminari_valutati', 'errori_preliminare_produzione', 'errori_preliminare_haiku_nuovo', 'errori_preliminare_opus', 'note'],
}
const VOTI = { type: 'object', properties: { voto_sonnet: { type: 'number' }, voto_opus: { type: 'number' }, errori_gravi_sonnet: { type: 'integer' }, errori_gravi_opus: { type: 'integer' }, note: { type: 'string' } }, required: ['voto_sonnet', 'voto_opus', 'errori_gravi_sonnet', 'errori_gravi_opus', 'note'] }

function esploratore(f) {
  return `${COMUNE}

Sei l'ESPLORATORE del perimetro per la fonte "${f.id}" (tipo ${f.tipo}), indirizzo osservato: ${f.url}
Compito: elencare in modo ESAUSTIVO, guardando direttamente il sito dell'ente, i bandi/avvisi PER IMPRESE (anche se solo alcune: artigiani, commercianti, agricoltori, start-up, professionisti, cooperative sociali) che questa fonte o la sezione bandi/contributi dello stesso ente pubblica e che oggi sono aperti o in arrivo, piu' quelli pubblicati o chiusi negli ultimi 6 mesi. Escludi gare d'appalto, concorsi di personale, contributi solo a privati/famiglie/enti pubblici/associazioni (ma elencali a parte in "esclusi" se sono ambigui).
Lavoro INDIPENDENTE: non leggere nulla sotto /tmp/claude-1000 (non devi sapere cosa ha trovato Bandi Radar).
Strumenti: WebFetch; se non basta, curl con UN solo comando per volta: curl -sL -m 30 -A "${UA}" "<indirizzo>". Rispetta robots.txt, al massimo 30 richieste. Se il catalogo ha piu' di 40 bandi aperti, elencane 40 scelti in modo vario (non solo i primi) e scrivi il totale stimato.
Scrivi ${f.dir}/esploratore.json cosi':
{"fonte": "${f.id}", "raggiungibile": true|false, "pagine_visitate": ["..."], "totale_stimato": numero o null, "note": "...",
 "bandi": [{"titolo": "...", "url": "...", "stato": "aperto|in_arrivo|chiuso_recente|non_noto", "scadenza": "AAAA-MM-GG o null", "per_imprese": "si|incerto", "perche": "una frase"}],
 "esclusi": [{"titolo": "...", "url": "...", "perche": "..."}]}`
}

function leggero(f) {
  return `${COMUNE}

Fai il lavoro che in produzione fara' un modello leggero chiamato via API. Segui ALLA LETTERA le istruzioni di sistema dei file, senza aggiungere conoscenze esterne e senza usare Bash o la rete.
1. Leggi ${f.dir}/smistamento.md (istruzioni di sistema + messaggio con gli annunci). Rispondi come chiesto e scrivi la risposta JSON in ${f.dir}/haiku_smistamento.json (formato: {"risposte": [{"id": numero, "esito": "rilevante|non_rilevante|da_rivedere", "motivo": "..."}]}).${f.smistamento ? '' : ' (Se il file non esiste, salta questo punto.)'}
2. Leggi ${f.dir}/bandi.json. Per ogni bando con "fascicolo_preliminare" non nullo: leggi una volta /tmp/claude-1000/sp/schede/istruzioni_preliminare.md (istruzioni di sistema), poi il fascicolo_preliminare, e rispondi come chiesto. Scrivi TUTTE le risposte in ${f.dir}/haiku_preliminari.json: {"preliminari": [{"bando": id, "per_imprese": "si|no|incerto", "edizione_in_corso": "si|no|incerto", "stato": "aperto|in_arrivo|chiuso|non_noto", "testo_bando": "si|solo_sintesi|no", "motivo": "..."}]}. Ogni fascicolo va letto davvero.
Rispondi con il numero di file scritti.`
}

function riferimento(f) {
  return `${COMUNE}

Sei il RIFERIMENTO: fai lo stesso lavoro del modello leggero, ma come lo farebbe il miglior analista di finanza agevolata, per stabilire la risposta giusta. Niente rete, niente Bash: solo i file.
1. Leggi ${f.dir}/smistamento.md e decidi per ogni annuncio rilevante/non_rilevante/da_rivedere seguendo le istruzioni (rilevante = aiuto a imprese; ricorda che enti pubblici dispongono contributi anche sotto "bandi di gara"). Scrivi ${f.dir}/opus_smistamento.json: {"risposte": [{"id": numero, "esito": "...", "motivo": "...", "certezza": "alta|media|bassa"}]}.${f.smistamento ? '' : ' (Se il file non esiste, salta.)'}
2. Leggi ${f.dir}/bandi.json. Per ogni bando con "fascicolo_scheda" non nullo leggi il fascicolo_scheda PER INTERO (contiene tutti i documenti, non solo l'inizio) e rispondi alle quattro domande del controllo preliminare (istruzioni in /tmp/claude-1000/sp/schede/istruzioni_preliminare.md), piu' "serve_scheda": "si|no" (un commercialista vorrebbe questa scheda per i suoi clienti oggi?) e le date di apertura/scadenza se le trovi. Scrivi ${f.dir}/opus_preliminari.json: {"preliminari": [{"bando": id, "per_imprese": "...", "edizione_in_corso": "...", "stato": "...", "testo_bando": "...", "serve_scheda": "si|no", "apertura": "AAAA-MM-GG o null", "scadenza": "AAAA-MM-GG o null", "motivo": "...", "certezza": "alta|media|bassa"}]}.
Rispondi con il numero di file scritti.`
}

function schedaOpus(f) {
  return `${COMUNE}

Compila la scheda del bando ${f.bando_scheda} come RIFERIMENTO di qualita'. Leggi /tmp/claude-1000/sp/schede/istruzioni_scheda.md (26 regole e formato JSON) e il fascicolo /tmp/claude-1000/sp/schede/fascicoli/${f.bando_scheda}/scheda.md PER INTERO. NON leggere scheda.json ne' altri file della cartella fascicoli/${f.bando_scheda} (lavoro indipendente). Niente rete, niente Bash.
Scrivi ${f.dir}/opus_scheda_${f.bando_scheda}.json con solo l'oggetto JSON della scheda, tutte le chiavi del formato.
Rispondi con il numero di file scritti.`
}

function controllore(f) {
  return `${COMUNE}

Sei il CONTROLLORE della fonte "${f.id}". Confronta cosa fa Bandi Radar (e il modello leggero) con il riferimento e con la realta' del sito. File nella cartella ${f.dir}:
- radar.json: tutto cio' che Bandi Radar ha della fonte: annunci (esito dello smistamento a regole: rilevante/non_rilevante/da_rivedere/null), bandi collegati (pagina_stato, preliminare di produzione, stato calcolato, ha_scheda);
- esploratore.json: bandi per imprese trovati da Opus sul sito (la "verita'" sul perimetro, da verificare se dubbia);
- smistamento.md (gli annunci del campione), haiku_smistamento.json (leggero), opus_smistamento.json (riferimento);
- bandi.json, haiku_preliminari.json (Haiku a piccoli lotti), opus_preliminari.json (riferimento); il preliminare DI PRODUZIONE (Haiku a lotti da 20) di ogni bando e' in /tmp/claude-1000/sp/schede/fascicoli/<bando>/preliminare.json.
Se un file manca, dillo nelle note e vai avanti.

Compiti:
A. PERIMETRO. Per ogni bando per imprese dell'esploratore (per_imprese si o incerto; stato aperto, in_arrivo o chiuso_recente) cerca il corrispondente in radar.json (stesso indirizzo o titolo equivalente). Se c'e', segui la catena: annuncio smistato rilevante? collegato a un bando (bando_id)? pagina trovata? preliminare di produzione lo fa passare (non: per_imprese=no, edizione_in_corso=no, stato=chiuso, testo_bando=no)? ha scheda? Classifica: "trovato_con_scheda", "perso_non_raccolto", "perso_smistamento", "perso_deduplica_o_dubbio", "perso_pagina_ufficiale", "perso_preliminare", "fermato_giustamente" (chiuso davvero). Per i "non raccolti" chiediti PERCHE' (la fonte osservata non lo elenca? e' su un'altra sezione del sito? e' vecchio?). Puoi usare WebFetch o curl (un comando per volta, User-Agent ${UA}) per verificare, al massimo 10 richieste.
B. SMISTAMENTO. Per ogni annuncio del campione confronta: regole (esito in radar.json), Haiku, Opus. Dove non concordano decidi tu chi ha ragione (puoi aprire l'annuncio in rete). Conta gli errori: "errore" = scartare un aiuto per imprese (grave) o tenere cio' che non lo e' (medio); "da_rivedere" su un caso chiaro = lieve.
C. PRELIMINARE. Per ogni bando valutato confronta produzione, Haiku nuovo, Opus. Decidi la risposta giusta sulle due cose che contano: il bando va fermato o va schedato? Errore grave = fermare un bando aperto per imprese; errore medio = far passare un bando chiuso/non per imprese.
Scrivi ${f.dir}/verdetto.json: {"fonte": "${f.id}", "perimetro": [{"titolo": "...", "url": "...", "esito": "...", "annuncio": id o null, "bando": id o null, "spiegazione": "..."}], "smistamento": [{"annuncio": id, "regole": "...", "haiku": "...", "opus": "...", "giusto": "...", "errore_regole": "nessuno|lieve|medio|grave", "errore_haiku": "...", "errore_opus": "...", "spiegazione": "..."}], "preliminare": [{"bando": id, "produzione": "passa|ferma", "haiku_nuovo": "passa|ferma", "opus": "passa|ferma", "giusto": "passa|ferma", "errore_produzione": "nessuno|medio|grave", "errore_haiku_nuovo": "...", "errore_opus": "...", "spiegazione": "..."}], "osservazioni": ["difetti di struttura che vedi: fonte che non espone i bandi, pagina ufficiale sbagliata, prompt ambiguo..."]}
Nei conteggi della risposta conta come errori solo medi e gravi.`
}

function giudice(f) {
  return `${COMUNE}

Sei il GIUDICE di due schede dello stesso bando (${f.bando_scheda}), compilate da modelli diversi seguendo le stesse istruzioni (/tmp/claude-1000/sp/schede/istruzioni_scheda.md):
- A = produzione (Sonnet): /tmp/claude-1000/sp/schede/fascicoli/${f.bando_scheda}/scheda.json
- B = riferimento (Opus): ${f.dir}/opus_scheda_${f.bando_scheda}.json
I documenti letti da entrambi: /tmp/claude-1000/sp/schede/fascicoli/${f.bando_scheda}/scheda.md (leggilo, almeno le parti che servono a verificare i campi).
Per ogni campo che conta per un commercialista e per l'abbinamento (ente, gestore, territorio_regioni/province/comuni, sede_richiesta, soggetti_ammessi, dimensioni_ammesse, forme giuridiche, eta impresa, requisiti_speciali_obbligatori, codici_ateco e esclusi, regime_aiuto, tipi_agevolazione, contributo_massimo, percentuale, fondo_perduto/finanziamento, spesa_minima/massima, dotazione, data_apertura, scadenza, chiuso_il, modalita_selezione, vincoli, completezza, sintesi, e i sei blocchi di dettagli) verifica sui documenti se A e B sono giusti, sbagliati o incompleti. Errore grave = un dato che farebbe sbagliare un abbinamento o dare un'informazione falsa a un cliente (importo, percentuale, data, territorio, beneficiari, settori sbagliati o inventati; bando dichiarato per imprese quando non lo e').
Scrivi ${f.dir}/giudizio_scheda_${f.bando_scheda}.json: {"bando": ${f.bando_scheda}, "voto_sonnet": 1-5, "voto_opus": 1-5, "campi": [{"campo": "...", "sonnet": "giusto|sbagliato|mancante|non_applicabile", "opus": "...", "gravita": "nessuna|lieve|grave", "nota": "..."}], "sintesi": "tre righe: cosa sbaglia Sonnet, cosa sbaglia Opus, se la differenza giustifica il modello piu' costoso"}`
}

function riserva(f) {
  return `${COMUNE}

Sei la VERIFICA DI RISERVA per la fonte "${f.id}". Il controllore ha scritto ${f.dir}/verdetto.json. Il tuo compito e' SMENTIRLO dove puoi: ricontrolla con le fonti (i file della cartella ${f.dir}, i fascicoli in /tmp/claude-1000/sp/schede/fascicoli/, e il sito con WebFetch o curl, un comando per volta, User-Agent ${UA}, al massimo 15 richieste) ogni caso in cui:
- un bando e' dichiarato perso (qualunque "perso_*") o "fermato_giustamente";
- regole, Haiku e Opus non concordano nello smistamento o nel preliminare;
- il controllore ha attribuito un errore a qualcuno.
Per ciascuno conferma o correggi il verdetto. Controlla anche che l'esploratore non abbia dimenticato sezioni evidenti del sito (una sola occhiata alla pagina ${f.url}).
Scrivi ${f.dir}/verdetto_finale.json con la STESSA struttura di verdetto.json, corretto, piu' "correzioni": [{"caso": "...", "prima": "...", "dopo": "...", "perche": "..."}] e "fiducia": "alta|media|bassa". Poi rispondi con i conteggi FINALI (solo errori medi e gravi).`
}

const fonti = args
log(`Fonti in questo gruppo: ${fonti.length}`)

const risultati = await pipeline(
  fonti,
  async (f) => {
    const lavori = [
      () => agent(esploratore(f), { label: `esploratore:${f.id}`, phase: 'Lavoro', model: 'opus', schema: ESPLORA }),
      () => agent(leggero(f), { label: `haiku:${f.id}`, phase: 'Lavoro', model: 'haiku', schema: SMIST }),
      () => agent(riferimento(f), { label: `opus:${f.id}`, phase: 'Lavoro', model: 'opus', schema: SMIST }),
    ]
    if (f.bando_scheda) lavori.push(() => agent(schedaOpus(f), { label: `scheda-opus:${f.bando_scheda}`, phase: 'Lavoro', model: 'opus', schema: SMIST }))
    const [esplora] = await parallel(lavori)
    return { esplora }
  },
  async (prima, f) => {
    const lavori = [() => agent(controllore(f), { label: `controllore:${f.id}`, phase: 'Controllo', model: 'opus', schema: CONTEGGI })]
    if (f.bando_scheda) lavori.push(() => agent(giudice(f), { label: `giudice:${f.bando_scheda}`, phase: 'Controllo', model: 'opus', schema: VOTI }))
    const [conti, voti] = await parallel(lavori)
    return { ...prima, conti, voti }
  },
  async (prima, f) => {
    const finale = await agent(riserva(f), { label: `riserva:${f.id}`, phase: 'Riserva', model: 'opus', schema: CONTEGGI })
    return { fonte: f.id, esplora: prima.esplora, controllore: prima.conti, finale, voti: prima.voti }
  },
)
return risultati.filter(Boolean)
