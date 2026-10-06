# Confronto modelli per verifica schede, controllo preliminare e smistamento — 06/10/2026

Ricerca in sola lettura (Artificial Analysis, Arena/LMArena, Vectara, pagine prezzi ufficiali e articoli di settore).
Nessun account, nessuna spesa. Calcolo dei costi: `/tmp/claude-1000/cp/costi.py`.
Prezzi in $ per milione di token (MTok), ingresso/uscita. "n.d." = non trovato; **[NV]** = dato non verificato su
fonte ufficiale (solo fonte secondaria o non leggibile).

## Cosa conta per noi (e quali numeri lo misurano meglio)

I nostri compiti sono "leggere bene e non inventare" su testi lunghi in italiano, con risposta JSON. Nessuna classifica
misura esattamente questo. Le più vicine:

- **AA-LCR** (Artificial Analysis, ragionamento su documenti lunghi ~100k token): misura il compito (b) e in parte (a).
- **AA-Omniscience** (da -100 a +100): premia le risposte giuste, **penalizza le invenzioni**, non penalizza "non lo so".
  Un valore negativo = il modello inventa più di quanto azzecchi quando non sa. È a "libro chiuso" (conoscenza, non
  lettura di un documento), quindi è un indizio indiretto della tendenza a inventare, non una prova.
- **Arena "Hard prompts" e "Instruction following"** (voti di persone, 02/10/2026): qualità percepita su richieste
  difficili e rispetto delle istruzioni.
- **Indice di intelligenza AA**: media generale (agenti, codice, scienza); utile solo come ordine di grandezza.
- **Italiano**: nessuna classifica aggiornata trovata con questi modelli (Arena non espone una pagina italiano
  raggiungibile; Evalita-LLM e ITA-Bench non includono i modelli recenti). **Va misurato nella prova.**
- **Vectara (fedeltà dei riassunti a un documento, 22/09/2026)**: sarebbe il più vicino al compito (a), ma non contiene
  nessuno dei modelli candidati attuali (solo vecchi: Gemini 2.5, Qwen3, DeepSeek V4-Pro 8,6%, GPT-5 mini 12,9%).

## Tabella

Fonti dei punteggi: AA = artificialanalysis.ai (pagine modello e confronti, lette il 06/10/2026, indice v4.3.x);
Arena = arena.ai/leaderboard/text (aggiornamento 02/10/2026; HP = Hard prompts, IF = Instruction following, rango e
punteggio).

| Modello | Prezzo in/out $/MTok | Indice AA | AA-LCR | AA-Omniscience | Arena HP / IF | Contesto | JSON con schema | Dati in UE? addestramento | Rischi |
|---|---|---|---|---|---|---|---|---|---|
| **Riferimento: Claude Opus 5.5** | 4/20 (lotto 2/10) | 58 | 85% | **46** (il migliore) | #2 1534 / #2 1517 | 1M | sì | — | prezzo |
| **qwen3.8-flash** (Alibaba; valutato da AA come Qwen3.8-Flash-Next) | **0,15/0,47** (Singapore; prezzo Francoforte **[NV]**) | 40 | 80% | **−10** | **assente** in Arena | 1M API / 256K open | sì (avviso: in ragionamento non garantito) | Francoforte ambito EU possibile; dichiarano niente addestramento | inventa più di quanto sa; molto prolisso (108k token out per compito AA); lento (55 t/s); nessun voto Arena; fornitore che cambia spesso |
| qwen3.8-max | 2/6 | 45 | 80% (rapporto Qwen) | 12 (rapporto Qwen) | #27 1503 / #31 1474 | ~1M | sì | come sopra | costa quanto Opus in lotto; lentissimo |
| Qwen3.8-27B (open, OVH Gravelines) | 0,40 €/2,70 € | 34 | n.d. | n.d. | #89 1463 / #101 1426 | 262K | sì (OVH) | **sì, Gravelines**, nessuna conservazione | più debole di tutti i candidati |
| **Gemini 3.8 Flash** (Google, 02/09/2026) | **0,75/3,75 fino al 31/12/2026, poi 1,50/7,50**; lotto −50%; endpoint regionale UE +10% | 41 | 81% | **30** | **#11 1516 / #15 1486** | 1M | sì (responseSchema) | **sì**: Vertex AI, multi-regione EU (dati e calcolo in UE) **[NV su pagina Google, fonte: rivenditori]**; a pagamento niente addestramento (pagina prezzi Google) | prezzo raddoppia a gennaio 2027; prolisso (71k token out per compito AA): va limitato il ragionamento |
| Gemini 3.5 Flash-Lite | 0,30/2,50 | 22 | n.d. | n.d. | #76 1474 / n.d. | 1M | sì | come sopra | troppo debole per la verifica; ok forse solo smistamento |
| **DeepSeek V4.1 Flash** (09/2026) | 0,15/0,60 fuori punta, 0,30/1,20 in punta (orari UTC 01-04 e 06-10 lun-ven) | 39 | **84%** | −5 | #34 1500 / #21 1479 | 1M | modalità JSON; schema rigido **[NV]** | **no: server in Cina**; uso per addestramento sulle API a pagamento poco chiaro (fonti contraddittorie) | dati fuori UE senza garanzie: da escludere per GDPR (nei bandi ci sono nomi ed email dei responsabili) |
| **GPT-5.6 Luna** (OpenAI, "mini" attuale, 07/2026) | 0,20/1,20 (+10% residenza UE) | 37 | **84%** | **−10** | #74 1476 / #74 1445 | 1M | sì (strict) | sì con progetto "Europe", ma serve approvazione di OpenAI (controllo abusi) | inventa come Qwen flash; voti Arena bassi |
| GPT-5.6 Terra (OpenAI, fascia media) | 2/12 | 42 | 83% | 0 | #48 1489 / #47 1461 | 1M | sì | come Luna | costo vicino a Opus; nessun vantaggio |
| GPT-5 nano | 0,05/0,40 | n.d. | n.d. | n.d. | n.d. | — | sì | come Luna | modello vecchio, solo smistamento |
| **Mistral Large 4** (europeo, **uscito oggi 06/10, anteprima**) | 0,68/2,09 in anteprima (listino 1,36/4,18) | 38 | 81,3% **[NV, benchlm]** | n.d. (benchlm: tasso di allucinazione 41,9% **[NV]**) | non ancora in classifica | 524K (AA) / 1M (Mistral) | sì | **sì, Francia/UE di base**; API a pagamento senza addestramento | anteprima di un giorno, prezzi e qualità instabili; molto prolisso (200M token per l'indice AA) |
| Mistral Medium 3.5 | n.d. | 14 | n.d. | n.d. | n.d. | 256K | sì | UE | troppo debole |
| Kimi K3 (Moonshot) | 3/15 | 44 | 88,7% (il primo) | n.d. | #9 1517 / #14 1488 | 1M | n.d. | Cina | costa più di Opus in lotto: escluso |
| GLM-5.3 (Z.ai) | 1,40/4,40 | 45 | n.d. | n.d. | #25 1503 / #25 1476 | 1M | n.d. | Cina | prezzo medio, dati fuori UE: escluso |

Nota: Claude Sonnet 5 (indice 38), quello che lasciava errori gravi in 9 schede su 21, è al livello di qwen3.8-flash,
DeepSeek V4.1 Flash, GPT-5.6 Luna e Mistral Large 4. Gemini 3.8 Flash è appena sopra per indice, ma nettamente sopra
su "non inventare" (Omniscience 30 contro −10/−5) e nei voti Arena (Hard prompts #11, davanti a qwen3.8-max #27).

## Costo mensile stimato (solo i compiti medi, non le schede)

Volumi del rapporto Qwen: 20 lotti di smistamento, 300 preliminari, 400 doppioni, 155 verifiche di schede; +3.000
token di ragionamento a chiamata (tranne i doppioni). Due ipotesi per il preliminare: 9.100 token in ingresso (media
misurata) e 50.000 (documenti lunghi, come nella richiesta).

| Modello | Preliminare 9k | Preliminare 50k |
|---|---|---|
| qwen3.8-flash (Singapore) | 3 $ | 5 $ |
| DeepSeek V4.1 Flash (fuori punta / punta) | 3 / 6 $ | 5 / 10 $ |
| GPT-5.6 Luna (UE) | 5 $ | 8 $ |
| Gemini 3.8 Flash in lotto, fino al 31/12 | 8 $ | 13 $ |
| Gemini 3.8 Flash Vertex UE regionale, fino al 31/12 | 18 $ | 28 $ |
| Gemini 3.8 Flash dal 2027 (lotto / standard) | 16 / 32 $ | 25 / 51 $ |
| Mistral Large 4 (anteprima / listino) | 12 / 24 $ | 21 / 41 $ |
| Qwen3.8-27B su OVH | 12 $ | 17 $ |
| GPT-5.6 Terra | 47 $ | 71 $ |
| Opus 5.5 in lotto (stesso calcolo) | 43 $ | 68 $ |

Con le schede a Opus (~46 $/mese) il totale resta sotto i 100 $ con tutti i candidati tranne Terra/Kimi. Gemini
3.8 Flash dal 2027 a prezzo pieno e preliminari lunghi (~51 $) porterebbe il totale a ~97 $: va usato in lotto o con
la cache (−90% sull'ingresso ripetuto), e col ragionamento limitato. **[NV]**: che il lotto (batch) sia disponibile
anche sull'endpoint UE di Vertex allo stesso sconto.

## Conclusioni

1. **qwen3.8-flash non convince per la verifica delle schede**: stesso livello generale di Sonnet 5, Omniscience −10
   (tende a rispondere invece di dire "non so": rischio di errori inventati), nessun voto Arena, molto prolisso.
   Va bene, probabilmente, per lo **smistamento** (compito facile e a basso rischio).
2. **Consigliato per la prova: Gemini 3.8 Flash su Vertex AI, regione UE**: è il miglior "economico" sulle misure che
   ci interessano (Omniscience 30, la più alta dopo i grandi modelli; LCR 81%; Arena hard prompts #11 su 413), dati e
   calcolo in UE, niente addestramento sui dati a pagamento, JSON con schema. Costa 5-6 volte Qwen ma sempre 3-5 volte
   meno di Opus.
3. **Alternativa: qwen3.8-flash nella stessa prova** (stessi casi, +1-3 $): se sulla nostra verità nota pareggia con
   Gemini, si prende il più economico. Seconda alternativa europea da tenere d'occhio: Mistral Large 4, da riprovare
   quando esce dall'anteprima (oggi troppo nuovo per fidarsi).
4. Esclusi: DeepSeek (dati in Cina), Kimi/GLM (cari e fuori UE), GPT-5.6 Luna (inventa quanto Qwen, voti bassi),
   Terra (costo da Opus), Flash-Lite e Mistral Medium (troppo deboli).

## Dati non verificati / limiti

- Prezzo UE (Francoforte) di qwen3.8-flash; che l'API "qwen3.8-flash" sia lo stesso modello valutato da AA.
- Gemini 3.8 Flash: residenza UE e prezzo regionale letti da rivenditori (requesty.ai), non dalla pagina Vertex; il lotto
  sull'endpoint UE.
- Mistral Large 4: punteggi da benchlm.ai, AA non pubblica ancora LCR/Omniscience; prezzi in anteprima.
- DeepSeek: schema JSON rigido e politica di addestramento sulle API a pagamento (fonti contraddittorie).
- Nessun benchmark sull'italiano amministrativo per nessun candidato.
- AA-Omniscience misura conoscenza "a libro chiuso", non la fedeltà a un documento: è un indizio, la prova sui nostri
  casi resta l'unico giudice.
- Le stime di costo assumono 3.000 token di ragionamento a chiamata: Gemini e Qwen sono prolissi, senza un tetto
  (thinking budget/level) il costo reale può essere 2-3 volte più alto.

## Fonti

- Artificial Analysis: https://artificialanalysis.ai/leaderboards/models ; https://artificialanalysis.ai/models/gemini-3-8-flash ;
  https://artificialanalysis.ai/models/qwen3-8-flash-next ; https://artificialanalysis.ai/models/comparisons/gemini-3-8-flash-vs-qwen3-8-flash-next ;
  https://artificialanalysis.ai/models/comparisons/deepseek-v4-1-flash-vs-gpt-5-6-luna ; https://artificialanalysis.ai/models/comparisons/gpt-5-6-terra-vs-gemini-3-8-flash ;
  https://artificialanalysis.ai/models/comparisons/gemini-3-8-flash-vs-claude-opus-5-5 ; https://artificialanalysis.ai/models/comparisons/qwen3-8-flash-next-vs-deepseek-v4-1-flash ;
  https://artificialanalysis.ai/models/gemini-3-5-flash-lite ; https://artificialanalysis.ai/models/gpt-5-6-terra ; https://artificialanalysis.ai/models/mistral-large-4 ;
  https://artificialanalysis.ai/evaluations/artificial-analysis-long-context-reasoning ; https://artificialanalysis.ai/evaluations/omniscience
- Arena: https://arena.ai/leaderboard/text ; https://arena.ai/leaderboard/text/hard-prompts ; https://arena.ai/leaderboard/text/instruction-following ; https://arena.ai/leaderboard/text/longer-query
- Vectara: https://github.com/vectara/hallucination-leaderboard
- Prezzi Gemini: https://ai.google.dev/gemini-api/docs/pricing ; Vertex UE: https://www.requesty.ai/eu/gemini , https://www.requesty.ai/models/vertex/gemini-3.8-flash-eu
- DeepSeek prezzi: https://www.yottalabs.ai/post/deepseek-v4-1-flash-pricing-specs-v4-pro-routing-2026 ; privacy: https://meetily.ai/llm-privacy/deepseek
- OpenAI prezzi: https://www.cloudzero.com/blog/openai-pricing/ ; residenza UE: https://openai.com/index/introducing-data-residency-in-europe/
- Mistral Large 4: https://docs.mistral.ai/models/mistral-large-4-0 ; https://benchlm.ai/models/mistral-large-4 ; dati: https://meetily.ai/llm-privacy/mistral
- Kimi/GLM prezzi: https://benchlm.ai/moonshot/api-pricing ; https://valueaddvc.com/pulse/glm-5-3-api-pricing-per-million-tokens-2026
- Italiano: https://huggingface.co/spaces/evalitahf/evalita_llm_leaderboard (nessun modello recente)
- Qwen: /tmp/claude-1000/cp/valutazione_qwen.md
