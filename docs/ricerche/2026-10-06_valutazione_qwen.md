# Valutazione di Qwen (Alibaba) come alternativa economica a Opus 5.5 — 06/10/2026

Ricerca in sola lettura (siti ufficiali Alibaba Cloud Model Studio, OVHcloud, Scaleway, Artificial Analysis,
OpenRouter e articoli di settore). Nessun account creato, nessuna spesa, nessuna modifica. Unica lettura sul
database: una SELECT sui token medi di `chiamate_ia` (`/tmp/claude-1000/cp/qwen_token.sql`).
Prezzi in dollari per milione di token (MTok), ingresso/uscita, salvo dove indicato in euro.

**In breve**: Qwen conviene **solo con i modelli medi** (qwen3.8-flash, qwen3.7-plus o l'open-weight
Qwen3.8-27B), non con il grande Qwen3.8-Max, che costa in ingresso quanto Opus in lotto e "pensa" molto di più.
Va provato come **revisore e smistatore**, non per scrivere le schede. Server in UE possibili (Francoforte di
Alibaba, oppure OVH a Gravelines).

---

## 1. I nostri compiti oggi (misurati in `chiamate_ia`, Opus 5.5)

| Compito | Token in medi | Token out medi | Costo medio (lotto, 2/10 $) |
|---|---|---|---|
| Smistamento (lotto da 20 annunci) | 13.400 | 1.150 | 0,037 $ |
| Controllo preliminare | 9.100 | 280 | 0,020 $ |
| Doppione | 1.400 | 90 | 0,0046 $ (diretta) |
| Scheda | 28.000-145.000 (media ≈ 50.000) | 10.000-14.000 | 0,30 $ in media, fino a 0,45 $ |
| Verifica di una scheda (stima: documenti + scheda) | ≈ 55.000 | ≈ 2.000 | ≈ 0,13 $ |

Sono compiti "da lettore attento": molto testo in ingresso, poca risposta. Quindi conta soprattutto il **prezzo
d'ingresso**, e il fatto che il modello non aggiunga migliaia di token di ragionamento in uscita.

## 2. Quali modelli Qwen (ottobre 2026)

| Modello | Tipo | Contesto | Qualità (Artificial Analysis Intelligence Index) | Note |
|---|---|---|---|---|
| **qwen3.8-max** (uscito 03/08, versione 0902) | chiuso, API Alibaba; esiste anche la versione open-weight Qwen3.8-2.4T-A95B | ≈ 1M | **45** | lento (≈ 38 token/s), molto prolisso: ≈ 71.000 token di ragionamento per compito contro 7.000 di Opus 5 |
| **qwen3.8-flash** (open-weight come Qwen3.8-Flash-Next, 26/08) | API Alibaba o open-weight (licenza Qwen Community) | 1M (API), 256K (open) | **40** | lettura di testi lunghi (AA-LCR) 80%, come Qwen3.8-Max; prolisso |
| **qwen3.7-plus** | chiuso, API Alibaba | 1M | 25 | economico, ma più debole di Flash 3.8 |
| **Qwen3.8-27B** (13-14/08) | open-weight, Apache 2.0 | 262K | **34** | ospitato da OVH, Scaleway, DeepInfra e altri |
| Confronto: Claude Opus 5.5 | — | — | **58** (il primo in classifica) | |
| Confronto: Claude Sonnet 5 (quello che lasciava errori gravi in 9 schede su 21) | — | — | 38 | |

Lettura semplice: i Qwen medi stanno **all'altezza di Sonnet 5** (che a Matteo non è piaciuto per le schede), il
Max un po' sopra; tutti ben sotto Opus 5.5. Sulla **lettura di documenti lunghi** (AA-LCR) Qwen3.8-Max e Flash
fanno 80%, alla pari di Opus 5 "low" (81%); sulla **conoscenza senza inventare** (AA-Omniscience) Qwen3.8-Max fa 12
contro 29: inventa di più quando non sa. Attenzione: le versioni dell'indice cambiano nel tempo, i confronti sono
indicativi.

- **Italiano**: nessun benchmark indipendente recente sull'italiano per Qwen 3.8; il rapporto tecnico di Qwen3
  mostra buoni risultati multilingue, italiano compreso. Va misurato sui nostri testi (è lo scopo della prova).
- **JSON con schema**: sì. Model Studio ha `response_format` con `json_schema` rigoroso per le serie
  Qwen3.7-Plus/Flash/Max e Qwen3.8-Max/Flash. Avvertenza della documentazione: in modalità "ragionamento" alcuni
  modelli non garantiscono JSON valido → da verificare nella prova. OVH supporta `json_schema` sui suoi modelli.
- **Ragionamento**: acceso di base; si spegne (`enable_thinking=false`) o si limita (`thinking_budget`). I token
  di ragionamento si pagano come uscita: senza un tetto, il risparmio si riduce.

## 3. Prezzi

### Alibaba Cloud Model Studio, endpoint internazionale (Singapore)

| Modello | Ingresso | Uscita | Note |
|---|---|---|---|
| qwen3.8-max | 2,00 $ | 6,00 $ | stesso ingresso di **Opus in lotto (2 $)** |
| qwen3.7-plus | 0,40 $ (fino a 256K) | 1,60 $ | |
| **qwen3.8-flash** | **0,15 $** | **0,47 $** | |
| qwen3.7-flash | 0,03-0,10 $ | 0,13-0,40 $ | a fasce di lunghezza |

- **Cache**: lettura al 10% del prezzo d'ingresso, scrittura al 125%.
- **Lotti (Batch, -50%)**: a Singapore la documentazione li elenca solo per i nomi generici `qwen-max`,
  `qwen-plus`, `qwen-flash`, `qwen-turbo`; per Francoforte non risultano. Quindi sui modelli 3.8 si paga il prezzo
  pieno (comunque molto basso). Su Francoforte e Singapore ci sono sconti notturni (fino al 60%, ore cinesi
  22-08): da verificare nella console.
- **Quota gratuita**: 1 milione di token per modello per 90 giorni sull'endpoint di Singapore.
- **Francoforte (UE)**: qwen3.8-max ≈ 1,65/4,95 $ (fonte secondaria); i prezzi UE di Flash e Plus non li ho
  trovati scritti: **da leggere nella console prima della prova**.

### Qwen open-weight su fornitori europei

| Fornitore (sede dei server) | Modello | Ingresso | Uscita |
|---|---|---|---|
| **OVHcloud AI Endpoints** (Gravelines, Francia) | Qwen3.8-27B (fp8, 262K) | 0,40 € | 2,70 € |
| OVHcloud | Qwen3.5-397B-A17B | 0,60 € | 3,60 € |
| Scaleway Generative APIs (Parigi) | Qwen3.8-27B | 0,60 € | 3,30 € (lotti -50%) |
| Scaleway | Qwen3.5-397B-A17B | 0,60 € | 3,60 € |
| DeepInfra / Together (USA) | Qwen3.8-2.4T-A95B (il "Max" aperto) | 2,00 $ | 6,00 $ |
| DeepInfra (USA) | Qwen3.8-27B | 0,40 $ | 3,00 $ |

Il "Max" aperto costa ovunque 2/6 $: nessun risparmio rispetto ad Alibaba. OVH non dichiara Qwen3.8-Flash.

## 4. Dove stanno i dati, GDPR, uso per l'addestramento

- **Alibaba Model Studio** ha sei regioni. La regione decide **dove si salvano** le richieste, l'"ambito" decide
  **dove si calcola**: Singapore (internazionale), Virginia (USA/globale), **Francoforte con ambito "EU"** (calcolo
  limitato all'Unione europea), Hong Kong, Tokyo, Pechino.
- **Addestramento**: FAQ ufficiale: "Alibaba Cloud strictly protects data privacy and never uses your data for
  model training". La pagina sulla trasparenza dei dati di addestramento elenca fonti che non comprendono i dati
  dei clienti. Durata di conservazione non indicata nella FAQ (rimanda ai Product Terms).
- **Cosa implica per noi**: mandiamo solo testi pubblici dei bandi, mai dati dei clienti. Però nei bandi ci sono
  nomi ed email dei responsabili del procedimento (dati personali, anche se pubblici): con **Francoforte, ambito
  EU** il problema del trasferimento fuori UE non si pone; con Singapore servirebbero le clausole contrattuali
  standard. **Scelta: Francoforte, ambito EU.**
- **OVH AI Endpoints**: server a Gravelines (lo stesso posto del nostro VPS), "i dati non vengono conservati né
  condivisi". È già il nostro fornitore: nessun nuovo contratto.

## 5. API, limiti, affidabilità

- **Compatibile OpenAI** (`/compatible-mode/v1`, dominio dedicato `{WorkspaceId}.eu-central-1.maas.aliyuncs.com`
  per Francoforte). Anche OVH e Scaleway sono compatibili OpenAI. Nel nostro codice servirebbe un piccolo
  "adattatore" accanto a quello Anthropic (stesso prompt, schema convertito in `json_schema`).
- **Limiti**: Francoforte qwen3.8-flash / qwen3.8-max / qwen3.7-plus **30.000 richieste/minuto, 5M token/minuto**;
  Singapore "dinamici" per i 3.8. Ampiamente sopra il nostro bisogno (poche centinaia di chiamate al giorno).
- **Affidabilità**: nessun dato pubblico di uptime serio; l'ultimo guasto riconosciuto risulta del 20/03/2026
  (StatusGator, fonte debole). Segnali di **cambi frequenti**: il dominio condiviso DashScope è in manutenzione dal
  30/09/2026 (si passa ai domini per workspace) e il 10/10/2026 Alibaba spegne i modelli vecchi. Bisogna fissare
  il nome della versione e mettere in conto una migrazione ogni pochi mesi.
- **Lentezza e prolissità** (Artificial Analysis): 38-55 token/s, molto ragionamento. Per noi la velocità non
  conta (lavoriamo a lotti), la prolissità sì (costo): va messo `thinking_budget`.

## 6. Quanto si risparmierebbe (volumi della revisione del 06/10)

Volumi al mese: 155 schede (115 nuove + 40 aggiornamenti), 20 lotti di smistamento (400 annunci), 400 doppioni,
300 preliminari, 155 verifiche di schede. Per Qwen ho aggiunto ≈ 3.000 token di ragionamento a chiamata
(con `thinking_budget`); cambio 1 € = 1,17 $.

| Compito (al mese) | Opus 5.5 in lotto | qwen3.8-flash (Alibaba) | qwen3.7-plus (Alibaba) | Qwen3.8-27B (OVH) | qwen3.8-max |
|---|---|---|---|---|---|
| Smistamento (20 lotti) | 0,7 $ | 0,1 $ | 0,2 $ | 0,4 $ | ≈ 1 $ |
| Preliminari (300) | 6,3 $ | 0,9 $ | 2,7 $ | 4,4 $ | ≈ 11 $ (peggio di Opus) |
| Doppioni (400) | 1,8 $ | 0,5 $ | 1,5 $ | 2,8 $ | — |
| Verifica schede (155) | 20 $ | 1,7 $ | 4,7 $ | 6,5 $ | ≈ 20 $ |
| **Totale compiti medi** | **≈ 29 $** | **≈ 3 $** | **≈ 9 $** | **≈ 14 $** | nessun risparmio |
| Schede (155) — da NON spostare | ≈ 46 $ | (≈ 2 $) | (≈ 6 $) | (≈ 12 $) | |
| Secondo parere una tantum sui 996 "fermati" | ≈ 20 $ | ≈ 3 $ | ≈ 9 $ | ≈ 15 $ | |

**Cosa significa**: con qwen3.8-flash i compiti medi passano da circa 29 $ a circa 3 $ al mese. Le schede restano
a Opus (≈ 46 $) e il totale scende da ≈ 75 $ a ≈ 50 $, lasciando 50 $ di margine sotto il tetto di 100 $: abbastanza
per una **verifica di ogni scheda** e per i secondi pareri sui fermati, cioè proprio le revisioni chieste nella
visione. Qwen3.8-Max non serve: costa quanto Opus in lotto e rende meno.

## 7. Rischi

1. **Qualità sulle decisioni che "fermano" un bando** (preliminare "chiuso" / "non per imprese"): un falso
   "chiuso" fa perdere una misura, il danno peggiore per la visione. Per questo Qwen va prima usato come
   **revisore** (un errore produce al massimo un falso allarme) e solo dopo, se la prova lo giustifica, come
   preliminare.
2. **Italiano amministrativo e documenti lunghi**: benchmark generici buoni ma non specifici.
3. **JSON in modalità ragionamento**: da verificare (la documentazione avverte).
4. **Fornitore nuovo e mutevole**: account Alibaba Cloud con carta, nuovo contratto, modelli ritirati spesso.
   Alternativa senza nuovo fornitore: OVH (più cara di 4 volte ma sempre metà di Opus, e un po' meno capace).
5. Nota fuori tema: esiste ora Claude Sonnet 5.5 (indice 56, quasi Opus); Matteo ha escluso i modelli Anthropic
   più piccoli, lo segnalo solo perché l'esperienza negativa era su Sonnet 5 (indice 38).

## 8. Piano di prova (uno solo)

**Modello e fornitore**: `qwen3.8-flash` su **Alibaba Cloud Model Studio, Francoforte, ambito EU**, versione
fissata, `json_schema` rigoroso, ragionamento acceso con `thinking_budget` 4.000 (se il JSON non regge: ragionamento
spento, seconda prova). Stessi prompt di oggi (`prompt_preliminare.md`, `prompt_smistamento.md`, istruzioni della
verifica del pilota). Script di prova in `/tmp/claude-1000/`, **nessuna modifica alla produzione**.

**Casi già decisi** (verità nota, non decisioni di Opus non controllate):

| Compito | Casi | Da dove | Criterio di successo |
|---|---|---|---|
| Controllo preliminare | 100 | 50 bandi con scheda proponibile e aperta (passati e verificati), 30 chiusi con data di chiusura certa, 20 "non per imprese" controllati a mano | **errori gravi ≤ 2 su 100** (bando aperto per imprese fermato, o chiuso fatto passare) e non più di Opus sugli stessi casi; JSON valido 100% |
| Verifica delle schede | 30 | le 19 del pilota IA del 06/10 (2 gravi noti) + 11 della verifica a campione 02-04/10 con errori noti | trova **tutti i gravi noti**, e almeno l'80% degli errori noti in totale; falsi "gravi" ≤ 3 su 30 |
| Smistamento | 100 annunci (5 lotti) | annunci decisi da regole sicure o corretti da Matteo | rilevanti persi ≤ 2 su 100; nessun annuncio perso nel lotto |

Ogni caso si fa girare **2 volte** per vedere se le risposte sono stabili; un agente in sessione (o Matteo su
10 casi) controlla i disaccordi con la verità.

**Costo della prova**: ≈ 3 milioni di token a giro, 2 giri → **≈ 1-3 $** (anche con prezzi UE più alti, sotto
5 $), più una sessione di lavoro per preparare i casi e confrontare i risultati. Serve che Matteo crei l'account
Alibaba Cloud e la chiave (con tetto di spesa) e la metta nel `.env`: è l'unica azione sua.

**Decisione dopo la prova**:
- tutti i criteri rispettati → Qwen diventa il **revisore di ogni scheda** e fa il **secondo parere sui 996
  fermati**; il preliminare passa a Qwen solo dopo un mese di revisore senza sorprese;
- passa la verifica ma non il preliminare → Qwen solo come revisore, preliminare resta a Opus;
- non passa → si rifà la stessa prova con Qwen3.8-27B su OVH (stessi casi, ≈ 5 $); se fallisce anche quella,
  si resta con Opus e si fa la verifica solo sulle schede aperte.

---

## Fonti

- Alibaba Cloud Model Studio — prezzi: https://www.alibabacloud.com/help/en/model-studio/model-pricing
- Regioni e ambiti: https://www.alibabacloud.com/help/en/model-studio/regions/
- FAQ (dati e addestramento): https://www.alibabacloud.com/help/en/model-studio/faq-about-alibaba-cloud-model-studio
- Trasparenza dati di addestramento: https://www.alibabacloud.com/help/en/model-studio/qwen-and-wan-training-data-disclosure
- Limiti di richieste: https://www.alibabacloud.com/help/en/model-studio/rate-limit
- Output strutturato: https://www.alibabacloud.com/help/en/model-studio/qwen-structured-output
- Ragionamento (enable_thinking, thinking_budget): https://www.alibabacloud.com/help/en/model-studio/deep-thinking
- Batch compatibile OpenAI: https://www.alibabacloud.com/help/en/model-studio/batch-interfaces-compatible-with-openai
- Dominio DashScope in manutenzione: https://www.alibabacloud.com/en/notice/product_change_noticemodel_studio_dashscope_shared_domain_entering_maintenance_mode_88a
- Artificial Analysis: https://artificialanalysis.ai/models/qwen3-8-max , https://artificialanalysis.ai/models/comparisons/qwen3-8-max-vs-claude-opus-5-low , https://artificialanalysis.ai/models/qwen3-8-flash-next , https://artificialanalysis.ai/models/qwen3-8-27b
- Classifica Sonnet 5 / Sonnet 5.5: https://artificialanalysis.ai/models/releases/comparisons/claude-sonnet-5-vs-claude-4-5-haiku
- Qwen3.8 open-weight e licenze: https://sqmagazine.co.uk/qwen3-8-open-weights-two-licenses/
- Fornitori del Max aperto: https://infrabase.ai/models/qwen3-8-2-4t-a95b , https://openrouter.ai/qwen/qwen3.8-2.4t-a95b
- Qwen3.8-Flash (contesto API): https://codersera.com/blog/qwen-3-8-flash-complete-guide-2026/
- OVHcloud AI Endpoints catalogo: https://www.ovhcloud.com/en/public-cloud/ai-endpoints/catalog/
- OVH output strutturato: https://docs.ovhcloud.com/en/guides/public-cloud/ai-machine-learning/ai-endpoints-structured-output
- Scaleway Generative APIs: https://www.scaleway.com/en/generative-apis/ (prezzi da riepiloghi di terzi, pagina ufficiale troppo grande da leggere)
- Stato del servizio: https://statusgator.com/services/alibaba-cloud/alibaba-cloud-model-studio

Da verificare prima della prova: prezzi UE (Francoforte) di qwen3.8-flash; che il modello API "qwen3.8-flash"
coincida con Qwen3.8-Flash-Next valutato da Artificial Analysis; prezzi Scaleway sulla pagina ufficiale.
