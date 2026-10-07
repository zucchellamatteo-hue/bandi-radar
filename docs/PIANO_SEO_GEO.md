# Piano SEO e GEO (visibilità su Google e sui motori di risposta IA)

Deciso con Matteo il 07/10/2026. Ricerca di base: `docs/ricerche/2026-10-07_landing_seo_geo.md`. Si procede in
sequenza; ogni sessione aggiorna lo stato.

| # | Mossa | Stato | Note |
|---|---|---|---|
| 1 | Landing page, SEO tecnica (title, canonical, sitemap, robots, JSON-LD), llms.txt, banner cookie pronto (Consent Mode v2) | **fatto** (PR 97) | Spenta finché `PAGINA_PUBBLICA=0` |
| 2 | Blog: articoli sui bandi più popolari e di nicchia; **articoli esaustivi per tutte le misure nazionali** (richiesta di Matteo) | **in corso** | Pubblica Matteo. Dal 07/10 il blog si apre da solo ai motori con `BLOG_PUBBLICO=1` (robots, sitemap e llms.txt solo del blog), la landing resta chiusa |
| 3 | Decisioni di Matteo prima di accendere: prezzo (landing 20 € vs Stripe/Termini), "Chi c'è dietro", dati del titolare (società) | in attesa di Matteo | Vedi prossimi passi |
| 4 | Dominio definitivo (bandinqiaro.it) con rinvio 301 dal vecchio; poi `SITO_URL` | in attesa del DNS | La SEO va fatta sul dominio definitivo |
| 5 | Account: Google Search Console, Bing Webmaster Tools (ChatGPT cerca su Bing), Google Business Profile; invio sitemap; IndexNow | in attesa di Matteo | Pronti i meta tag (`GOOGLE_SITE_VERIFICATION`, `BING_SITE_VERIFICATION`); consigliata la proprietà "Dominio" con record TXT. Bing può importare il sito da Search Console |
| 6 | Pagine delle misure nazionali (`/agevolazioni-nazionali/<misura>`) | da fare | Base: articoli del punto 2 |
| 7 | Pagine "bandi aperti in <regione>" aggiornate ogni giorno (sotto 8 bandi non indicizzate) | da fare | Anche destinazione degli annunci regionali |
| 8 | Rapporto mensile con i numeri (bandi aperti per regione, tipi) da far riprendere a stampa di settore, Ordini, associazioni; LinkedIn | da fare | Menzioni esterne = autorevolezza per Google e IA |
| 9 | Google Ads con conversioni (registrazione) e Consent Mode v2 | dopo la società | |
| 10 | Strumenti gratuiti (es. "quanto contributo puoi ottenere") per link spontanei | più avanti | |
| — | **Misura** (ogni due settimane, con la revisione dell'architettura; all'avvio anche ogni giorno con l'email "rapporto SEO/GEO", `RAPPORTO_SEO`) | **attiva** dal 07/10 | Pagina **Visite** della plancia (statistiche senza cookie, `app/visite`) e indicatori W01-W06 di `strumenti/sessione/ar/ISTRUZIONI_REVISIONE_ARCHITETTURA.md`: persone sulle pagine pubbliche, persone arrivate da Google/Bing e dai motori IA (chatgpt.com, perplexity.ai, gemini, copilot, claude.ai), letture di GPTBot/OAI-SearchBot/ClaudeBot/PerplexityBot per articolo, articoli mai letti dai motori, campagne utm. Insieme: Search Console (impressioni, clic, query, pagine indicizzate) e Bing Webmaster Tools. Si guarda la tendenza rispetto alle due settimane prima e si decide quali articoli scrivere o aggiornare |
