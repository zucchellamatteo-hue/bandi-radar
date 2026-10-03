# Complemento delle schede già scritte (sessione del 03/10/2026)

Per ogni bando assegnato, nella cartella `/tmp/claude-1000/ar/complemento/<id>/` trovi:
- `scheda.json`: i campi della scheda che servono, `serve` (quali parti compilare: `forma`, `ateco`, `territorio`) e
  `forma_ricavata` (una prima forma dell'incentivo ricostruita dai campi: solo un punto di partenza, può essere sbagliata);
- `documenti.txt`: i testi dei documenti ufficiali. È lungo: cerca con Grep le parole chiave (fondo perduto, contributo,
  finanziamento, intensità, %, massimo, micro, piccole, medie, linea, misura, asse; settori, ATECO, attività, sede,
  Regione, Provincia) e leggi gli articoli su beneficiari, agevolazione, intensità, massimali.

**Strumenti: Read, Grep e Write.** Niente rete, niente database. Scrivi `/tmp/claude-1000/ar/complemento/<id>/complemento.json`
con **solo** questo oggetto, compilando soltanto le parti che in `serve` valgono `true` (le altre: `null`):

```json
{"forma_incentivo": {"descrizione": "...", "righe": [{"per_chi": "...", "forme": [{"forma": "...", "percentuale": 50, "massimale": 100000, "condizioni": null}],
                     "spesa_minima": null, "spesa_massima": null, "agevolazione_massima": null, "note": null}], "note": null},
 "ateco": {"codici_ateco": ["55", "56"], "ateco_versione": "2025", "frase": "la frase del bando che descrive i settori", "fonte": "allegato: <nome> - art. N"},
 "territorio": {"territorio_regioni": ["UMB"], "territorio_province": [], "frase": "la frase del bando", "fonte": "allegato: <nome> - art. N"}}
```

Regole:
- `forma_incentivo`: come in `app/schede/prompt_scheda.md`, punto 12 (anche `/tmp/claude-1000/ar/ISTRUZIONI_FORMA.md`). Percentuale
  **base**, maggiorazioni nelle `note`; una riga per gruppo o linea con regole diverse, **tutte** le misure o assi.
- `ateco`: traduci la descrizione dei settori nelle **sezioni o divisioni ATECO** che le corrispondono con certezza (per
  esempio "imprese turistiche ricettive" → "55", "commercio al dettaglio" → "47", "ristorazione" → "56", "manifattura" → "C",
  "agricole" → "01"). Versione del bando, o "2025" se non la dice. Se la descrizione è troppo vaga per un codice sicuro,
  `"ateco": null`.
- `territorio`: solo se il bando limita la **sede dell'impresa** a regioni o province scritte nel testo (sigle regioni: ABR, BAS, BZ,
  CAL, CAM, EMR, FVG, LAZ, LIG, LOM, MAR, MOL, PIE, PUG, SAR, SIC, TN, TOS, UMB, VDA, VEN; province con la sigla automobilistica).
  Se il limite è un'area più piccola (un comune, un cratere sismico) o non è sulla sede, `"territorio": null`.
- Niente invenzioni: solo ciò che i documenti dicono, con la frase e la fonte.

Alla fine rispondi solo "fatto: N file scritti" e i problemi trovati (una riga per bando, solo se ce ne sono).
