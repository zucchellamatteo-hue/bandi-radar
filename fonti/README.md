# Registro delle fonti

Qui vive l'elenco delle fonti che Bandi Radar controlla. **Aggiungere una fonte è aggiungere una voce a uno di questi file**, non scrivere codice. I file sono in formato YAML (testo con rientri), uno per gruppo:

| File | Contenuto |
|---|---|
| `nazionali.yaml` | incentivi.gov.it, Portale UE, MIMIT, Invitalia, GSE, SIMEST, cataloghi open data |
| `regioni.yaml` | 19 Regioni e 2 Province autonome, con eventuali dati aperti e calendari degli avvisi |
| `camere.yaml` | Camere di Commercio |
| `capoluoghi.yaml` | Comuni capoluogo di provincia e Province eccezione |
| `fondazioni.yaml` | Fondazioni bancarie (selezione) |
| `contesto.yaml` | Dati di contesto (non bandi): perimetri, elenchi beneficiari, RNA |

## Campi di ogni voce

```yaml
- id: lombardia_bandi_online          # identificativo unico, minuscolo, solo lettere, numeri e _
  nome: Regione Lombardia - Bandi Online  # nome leggibile
  ente: Regione Lombardia
  tipo: regione                        # ue | nazionale | regione | camera | capoluogo | provincia | fondazione | contesto
  territorio: LOM                      # sigla regione (LOM, FVG, ...), ITA per nazionali, UE per europee
  url: https://www.bandi.regione.lombardia.it/...   # pagina elenco da osservare (solo se aperta davvero)
  modalita: html                       # html | rss | api | browser (elenco caricato via JavaScript)
  feed_url:                            # indirizzo RSS o API, se modalita e' rss o api
  piattaforma:                         # famiglia del sito, se riconosciuta: municipium, wordpress_design_comuni, drupal, plone, liferay, opencity, ...
  frequenza: giornaliera               # giornaliera | tre_a_settimana | settimanale | quindicinale | mensile
  stato: attiva                        # attiva | da_verificare | difficile | esclusa
  verificato_il: 2026-09-24            # data dell'ultima verifica a mano dell'indirizzo
  note: >                              # cosa pubblica, filtri consigliati, problemi visti
    Elenco misto, filtrare per "imprese".
  ignora_robots: false                 # true solo per decisione esplicita di Matteo: legge la pagina anche se robots.txt la vieta
```

Regole:
- `url` e `feed_url` vanno scritti **solo se aperti davvero** durante una verifica: mai ricostruiti a memoria.
- Se una fonte ha sia una pagina HTML sia un feed o un'API, si preferisce il feed o l'API (`modalita: rss` o `api`) e la pagina HTML resta in `url` come riferimento per le persone.
- `stato: difficile` per i siti che rifiutano i server o caricano tutto via JavaScript; `esclusa` per fonti valutate e scartate, con il motivo nelle note (così non si rivalutano ogni volta).
- Le frequenze seguono §3 del piano: sono stime da tarare a fine Fase 2.
- La raccolta rispetta `robots.txt`. Alcuni enti vietano tutto a tutti i robot (es. Regione Liguria, Regione Abruzzo): quelle voci restano `da_verificare` finché Matteo non decide, fonte per fonte, se impostare `ignora_robots: true`.

## Controllo

`python -m app.fonti.verifica` legge tutti i file, controlla che siano ben formati (id unici, campi obbligatori, valori ammessi) e prova a scaricare ogni indirizzo, stampando una riga per fonte con esito e tempo di risposta. Serve a fine Fase 0 per la verifica automatica degli indirizzi e, in seguito, come primo passo dell'osservatore.
