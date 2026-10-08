# Istruzioni per gli agenti: il bando è ancora aperto? (sessione del 03/10/2026)

Oggi è il 03/10/2026. bandinQiaro propone ai clienti solo bandi aperti o in arrivo. Per ogni bando c'è un file
`/tmp/claude-1000/ar/stato/pagine/<id>.md` con: i dati della scheda, il motivo del ricontrollo, la pagina ufficiale
**scaricata oggi** e quella salvata prima.

**Strumenti: solo Read e Write.** Niente Bash, niente WebFetch, niente ricerche in rete: decidi solo da quel file.

Per ogni id che ti è assegnato: leggi il file per intero e scrivi `/tmp/claude-1000/ar/stato/esiti/<id>.json` con
**solo** questo oggetto JSON:

```
{"stato": "aperto|in_arrivo|chiuso|esaurito|non_chiaro",
 "apertura": "AAAA-MM-GG o null", "scadenza": "AAAA-MM-GG o null", "chiuso_il": "AAAA-MM-GG o null",
 "per_imprese": "si|no|incerto",
 "citazione": "la frase esatta della pagina (massimo 300 caratteri) su cui si basa la decisione",
 "motivo": "una frase, massimo 30 parole"}
```

Regole:
- **La pagina di oggi conta più di quella salvata e più della scheda.** Se oggi dice "chiuso", "scaduto", "sportello
  chiuso", "non è più possibile presentare domanda", "dotazione esaurita", "Opportunità scaduta", "Stato: Valutazione",
  il bando è chiuso (o `esaurito` se il motivo è la fine dei fondi).
- `chiuso` anche quando l'unica finestra per le domande indicata (in questa edizione) ha una data finale già passata.
  `chiuso_il`: la data in cui ha chiuso (la scadenza passata, o la data del decreto di chiusura); se non si sa, null.
- Le formule "fino a esaurimento delle risorse", "salvo chiusura anticipata", "lo sportello potrà essere sospeso"
  descrivono un bando **aperto**, non chiuso. Una graduatoria pubblicata non chiude da sola uno sportello o un bando a
  più finestre: guarda se ci sono finestre future.
- Programmi vecchi (POR 2014-2020) senza atti recenti e senza nessuna data futura: `chiuso` solo se la pagina lo dice
  o se le date sono passate; altrimenti `non_chiaro`.
- `in_arrivo`: le domande si apriranno in una data futura scritta nella pagina.
- `aperto`: la pagina dice che si possono presentare domande ora (sportello attivo, scadenza futura).
- `non_chiaro`: la pagina non dice né l'una né l'altra cosa (non scrivere "aperto" per abitudine).
- Date in `apertura` e `scadenza` solo se scritte nella pagina (quelle della finestra in corso o della prossima).
- `per_imprese`: `no` se i beneficiari sono solo enti pubblici, Comuni, scuole, persone fisiche/famiglie senza
  impresa, associazioni sportive dilettantistiche o enti non commerciali ("Destinatari: ENTE"); cooperative e
  imprese sociali **sono** imprese. Altrimenti `si`, o `incerto` se la pagina non lo dice.

Alla fine rispondi con **una sola riga**: `fatto: <N> file scritti` e, se ci sono stati, `; problemi: <id> <frase>`.
