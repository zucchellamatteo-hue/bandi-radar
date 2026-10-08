# Verifica del solo documento (procedura nuova del regista, 08/10/2026)

Per i bandi che hanno già avuto il secondo controllo prima dell'08/10: si risponde solo alle domande A e B di
`ISTRUZIONI_VERIFICA_IA.md` (tipo di agevolazione e documento), senza ricontrollare tutta la scheda.
Per ogni bando assegnato hai la cartella `<id>/` con `scheda.json` e `documenti.txt` (i documenti iniziano con
`===== nome (url)`): leggi l'elenco dei documenti e l'inizio di quelli che sembrano il testo ufficiale.

Scrivi `<id>/documento.json` (UTF-8, JSON valido):
```json
{"id": 123,
 "tipo_procedura": "misura_di_legge | sportello | bando",
 "documento": {"verificato": "si | no", "nome": "nome del documento ufficiale", "problema": null,
               "motivo": "una frase: quale atto e' (numero, data, edizione) o cosa manca e dove cercarlo"}}
```
`verificato` = `si` solo se il documento e' di questo bando, dell'edizione in corso (oggi e' l'08/10/2026), approvato,
e contiene le regole. Altrimenti `no` con `problema` tra `manca`, `solo_sintesi`, `altro_bando`, `edizione_vecchia`,
`bozza`, `atto_generico`, `graduatoria`. Niente inventato. Se noti un errore grave evidente della scheda (non per
imprese, chiuso, importo sbagliato), scrivilo nella risposta finale. Alla fine una riga per bando: id, tipo,
verificato (problema), motivo.
