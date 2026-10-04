# Verifica di qualita' delle schede (controllo a campione, 04/10/2026)

Per ogni bando assegnato, nella cartella /tmp/claude-1000/ar/verifica/verifica-03-10/<id>/ trovi:
- scheda.json: la scheda (campi principali + risposta_completa con vincoli, fonti e avvertenze; `stato` e
  `per_imprese` sono quelli che il sistema usa oggi);
- documenti.txt: i testi dei documenti ufficiali (bando, decreti, FAQ, modulistica, pagina). E' lungo: cerca con Grep
  le parole chiave (scadenza, termine, presentazione, chiuso, esaurit, contributo, massimo, %, ATECO, micro, PMI, sede,
  beneficiari, dichiara) e leggi i passaggi.

**Strumenti: Read, Grep, Write.** Niente rete. Confronta la scheda con i documenti e giudica questi campi, uno per uno:
stato, data_apertura, scadenza, tipo_agevolazione, contributo_massimo, percentuale (dal 03/10 e' la percentuale BASE,
senza maggiorazioni), a_chi_si_rivolge (beneficiari), territorio (testo ed elenco delle regioni), dimensioni_ammesse,
codici_ateco / vincolo ateco, spese ammesse (cosa_finanzia), sintesi.

Esito per campo: "giusto", "impreciso" (vero ma incompleto o approssimato, non porta fuori strada), "sbagliato"
(porterebbe un'impresa a una conclusione errata), "non verificabile" (i documenti non lo dicono). Per "impreciso" e
"sbagliato" scrivi in una riga cosa dice la scheda e cosa dice il documento (citazione breve).

Segnala anche, se ci sono: avvertenze che dicono che manca un documento che invece c'e' tra i documenti; bando a piu'
misure ridotto a un numero solo; fondi esauriti non in evidenza.

Poi un voto complessivo da 1 a 5 ("se fossi un commercialista, mi fiderei di questa scheda per proporre il bando?")
e se il bando e' davvero un'agevolazione per imprese aperta o in arrivo oggi (04/10/2026).

Scrivi /tmp/claude-1000/ar/verifica/verifica-03-10/<id>/verdetto.json:
{"id": ..., "campi": {"scadenza": {"esito": "...", "nota": "..."}, ...}, "voto": 1-5, "davvero_per_imprese_e_aperto": true/false,
 "avvertenza_falsa_allegato": true/false, "nota_generale": "..."}
Non modificare scheda.json ne' il database. Alla fine rispondi solo "fatto: N verdetti".
