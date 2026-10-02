# Verifica di qualita' delle schede (controllo a campione)

Per ogni bando assegnato, nella cartella /tmp/claude-1000/ar/verifica/<id>/ trovi:
- scheda.json: la scheda scritta in precedenza (campi principali + risposta_completa con vincoli e fonti);
- documenti.txt: i testi dei documenti ufficiali (bando, decreti, FAQ). E' lungo: cerca con Grep le parole chiave
  (scadenza, termine, presentazione, contributo, massimo, %, ATECO, micro, PMI, sede, ecc.) e leggi i passaggi.

Confronta la scheda con i documenti e giudica questi campi, uno per uno:
stato, data_apertura, scadenza, tipo_agevolazione, contributo_massimo, percentuale, a_chi_si_rivolge (beneficiari),
territorio, dimensioni_ammesse, codici_ateco / vincolo ateco, spese ammesse (cosa_finanzia), sintesi.

Esito per campo: "giusto", "impreciso" (vero ma incompleto o approssimato, non porta fuori strada),
"sbagliato" (porterebbe un'impresa a una conclusione errata), "non verificabile" (i documenti non lo dicono).
Per "impreciso" e "sbagliato" scrivi in una riga cosa dice la scheda e cosa dice il documento (con citazione breve).

Poi un voto complessivo da 1 a 5 ("se fossi un commercialista, mi fiderei di questa scheda per proporre il bando?")
e se il bando e' davvero un'agevolazione per imprese aperta o in arrivo oggi (02/10/2026).

Scrivi il risultato in /tmp/claude-1000/ar/verifica/<id>/verdetto.json:
{"id": ..., "campi": {"scadenza": {"esito": "...", "nota": "..."}, ...}, "voto": 1-5, "davvero_per_imprese_e_aperto": true/false, "nota_generale": "..."}
Non modificare scheda.json ne' il database. Lavoro solo in lettura.
