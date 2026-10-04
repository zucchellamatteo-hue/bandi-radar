# Testi legali della pagina pubblica

Frammenti HTML (solo contenuto, senza stili né script) che la pagina pubblica di Bandi Radar inserisce nel proprio modello:

- `termini.html` — Termini e condizioni del servizio in abbonamento (rivolto a imprese e professionisti).
- `privacy.html` — Informativa privacy (artt. 13-14 GDPR).
- `cookie.html` — Cookie policy; contiene il link `id="rivedi-cookie"` che la pagina deve collegare al banner dei cookie.
- `supporto.html` — Condizioni del servizio di supporto per la domanda a success fee.

**Sono bozze del 05/10/2026**: vanno fatte rivedere da un professionista (avvocato o consulente privacy) prima di usarle con clienti reali. Ogni file ha in cima il riquadro `<p class="bozza">`, da togliere solo dopo la revisione.

## Segnaposto da riempire (tra parentesi quadre nei testi)

Dati del titolare (tutti i file): `[RAGIONE SOCIALE DEL TITOLARE]`, `[PARTITA IVA]`, `[SEDE]`, `[EMAIL DI CONTATTO]`, `[PEC]`, `[DATA DI ENTRATA IN VIGORE]`.

Termini: `[PREZZO MENSILE]`, `[PREZZO ANNUALE MENSILE]`, `[PREZZI AGGIUNTIVI]`, `[IVA INCLUSA / IVA ESCLUSA]`, `[MODALITÀ DI FATTURAZIONE]`, `[GIORNI DI PREAVVISO]`, `[DURATA PROVA GRATUITA]`, cosa succede alla fine della prova (con `[GIORNI DI AVVISO FINE PROVA]`), regola per l'uscita anticipata dall'impegno annuale, rinnovo dell'annuale (`[SI RINNOVA PER ALTRI 12 MESI / PASSA ALLA FORMULA MENSILE]`), `[FORO COMPETENTE]`.

Privacy: eventuale DPO (`[DATI DI CONTATTO DEL DPO]`, altrimenti togliere il paragrafo), `[GIORNI PER LA CANCELLAZIONE]`, `[DURATA DI CONSERVAZIONE RICHIESTE]`, `[DURATA DI CONSERVAZIONE LOG]`, `[DURATA DEL CONSENSO]`, verifica dell'adesione dei fornitori al Data Privacy Framework.

Cookie: `[NOME COOKIE SCELTA COOKIE]`, `[DURATA DEL CONSENSO]`, `[DURATA COOKIE GOOGLE ADS]`.

Supporto (cioè le percentuali e il minimo della success fee): `[CONCESSO / EROGATO]`, `[PERCENTUALE FONDO PERDUTO]` (proposta 10-15%), `[PERCENTUALE FINANZIAMENTO AGEVOLATO]` (proposta 1-2%), `[COMPENSO MINIMO]` (proposta 400-500 €), `[IVA ESCLUSA / IVA INCLUSA]`, `[MOMENTO DEL PAGAMENTO, ...]`, cosa succede se l'impresa rinuncia dopo l'avvio, limiti di responsabilità e assicurazione professionale.

I link interni usano `/privacy` e `/cookie`: adeguarli se le pagine avranno indirizzi diversi.
