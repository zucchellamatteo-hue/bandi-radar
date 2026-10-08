# Istruzioni per gli agenti: il bando è per imprese? (sessione del 03/10/2026)

bandinQiaro propone bandi di finanza agevolata alle **imprese** clienti di un commercialista. Le regole automatiche
hanno trovato in questi bandi frasi che fanno pensare a beneficiari diversi dalle imprese (enti pubblici, scuole,
associazioni sportive dilettantistiche, enti non commerciali, enti del terzo settore, persone fisiche). Spesso è un
falso allarme: l'elenco dei beneficiari comprende anche le imprese.

**Strumenti: solo Read e Write.** Niente Bash, niente rete. Per ogni id assegnato leggi
`/tmp/claude-1000/ar/imprese/<id>.md` e scrivi `/tmp/claude-1000/ar/imprese/<id>.json` con **solo**:

`{"per_imprese": "si|no|incerto", "citazione": "frase esatta, massimo 300 caratteri", "motivo": "massimo 30 parole"}`

- `no` solo se **nessuna** impresa può presentare domanda: beneficiari solo enti pubblici, Comuni, scuole, università,
  persone fisiche o famiglie senza attività d'impresa, ASD/SSD in regime L. 398/1991 o "non ente commerciale", enti
  del terzo settore **non iscritti al Registro delle imprese**, enti titolari di musei/biblioteche, enti di formazione
  accreditati (salvo che il bando ammetta imprese come tali).
- `si` se tra i beneficiari ci sono imprese di qualunque forma: società, ditte individuali, lavoratori autonomi e
  professionisti con partita IVA, **cooperative e imprese sociali**, consorzi di imprese, start-up; anche se ci sono
  pure enti o associazioni. Le persone che **avviano** un'impresa o un lavoro autonomo contano come imprese.
- Il **modulo di domanda** conta quanto l'articolo sui beneficiari: se le dichiarazioni richieste ("dichiara di
  essere ASD in regime L. 398/1991", "di non essere ente commerciale", "codice IPA dell'ente") escludono le imprese, è `no`.
- `incerto` se i testi non bastano.

Alla fine rispondi con **una sola riga**: `fatto: <N> file scritti` e, se ci sono stati, `; problemi: <id> <frase>`.
