# Forma dell'incentivo per le schede già scritte (sessione)

Per ogni bando assegnato, nella cartella `/tmp/claude-1000/ar/forma/<id>/` trovi:
- `scheda.json`: i campi della scheda che riguardano l'aiuto e, in `ricavata`, una prima versione ricostruita da quei campi (può essere incompleta o sbagliata: è solo un punto di partenza);
- `documenti.txt`: i testi dei documenti ufficiali. È lungo: cerca con Grep (o `grep` da Bash, un comando alla volta) le parole chiave (fondo perduto, contributo, finanziamento, prestito, tasso, garanzia, intensità, %, massimo, ESL, voucher, servizi, credito d'imposta, micro, piccole, medie, linea, misura, asse) e leggi gli articoli su agevolazione, intensità, massimali e spese.

Scrivi `/tmp/claude-1000/ar/forma/<id>/forma.json` con **solo** questo oggetto (regole complete in `app/schede/prompt_scheda.md`, punto 12, `forma_incentivo`):

```json
{"descrizione": "una o due frasi chiare: che aiuto è, in che quota, fino a quanto",
 "righe": [{"per_chi": "Tutti i beneficiari | Micro e piccole imprese | Linea A - ...",
            "forme": [{"forma": "fondo_perduto | finanziamento_agevolato | credito_imposta | garanzia | voucher | servizi | premio | contributo_interessi | altro",
                       "percentuale": numero o null, "massimale": numero o null, "condizioni": "testo o null"}],
            "spesa_minima": numero o null, "spesa_massima": numero o null, "agevolazione_massima": numero o null, "note": "testo o null"}],
 "note": "testo o null"}
```

Regole:
- `percentuale` = quota della **spesa ammessa** coperta da quella forma (0-100), **base**, senza maggiorazioni; le maggiorazioni (rating di legalità, giovani, zone…) vanno in `note`. Per la garanzia, la copertura del prestito va in `condizioni`.
- Agevolazione mista (prestito + fondo perduto): una forma per parte, ognuna con la sua quota e il suo massimale; mai "100%" se è la somma delle due.
- Una riga per gruppo con regole diverse (dimensione, linea, misura, asse, tipo di beneficiario); se sono uguali per tutti, una riga sola "Tutti i beneficiari". Includi **tutte** le linee aperte, non solo la prima.
- Servizi gratuiti (consulenze, percorsi, accompagnamento): `forma: "servizi"`, valore del servizio in `massimale` se scritto.
- Solo ciò che i documenti dicono: niente invenzioni; se un dato manca, `null`.
- Italiano semplice; importi in euro come numeri (50000, non "50.000 €").

Non toccare il database né `scheda.json`. Alla fine rispondi solo "fatto: N file scritti" e i problemi trovati (una riga per bando, solo se ce ne sono).
