# Pagina ufficiale del bando e allegati in ordine (Parte 2)

**Data:** 25/09/2026, sessione sul VPS.
**Domanda:** con il nuovo passo "trova la pagina ufficiale" (`app/schede/pagina_ufficiale.py`, regole nel registro) e gli allegati scaricati dalla pagina ufficiale, Sonnet riceverebbe il bando vero? Nella prova del 25/09 in 5 schede su 10 non l'aveva ricevuto.
**Metodo:** copia del database di produzione in un Postgres temporaneo, deduplica (Parte 1), poi pagina ufficiale e allegati per **29 bandi**: i 9 della prova del 25/09 (annunci 2587, 2585, 2814, 3055, 4136, 4199, 4231, 4383 e, per la notizia 358, il bando della Camera di Padova a cui si riferisce) e **20 bandi scelti a caso** (ordine casuale fisso, `md5('prova2-' || id)`). Richieste reali ai siti, con il nostro User-Agent, robots.txt e 2 secondi tra una richiesta e l'altra. File in un volume Docker di prova, poi cancellato.

## Numeri

| | Bandi | Pagina ufficiale trovata | Non trovata | Testo del bando (o del decreto) tra gli allegati |
|---|---|---|---|---|
| Prova del 25/09 | 9 | **9** | 0 | **9** (il 25/09: 4 su 9) |
| A caso | 20 | 17 | 3 | 13 |
| **Totale** | 29 | **26** | 3 | **22** |

### I 9 bandi della prova del 25/09

| Annuncio | Il 25/09 Sonnet aveva | Oggi |
|---|---|---|
| 2587 Lombardia fiere | pagina di login, nessun documento | pagina di dettaglio trovata **con la ricerca del sito per codice** (RLO12026055023); 6 documenti, il bando per primo |
| 2585 Export su Misura | bando e moduli | uguale (pagina di Unioncamere Lombardia) |
| 2814 Emilia-Romagna polifunzionali | solo la pagina | **DGR 1126/2026 e 4 moduli**, letti dall'API del sito (vedi sotto) |
| 3055 Finpiemonte enti pubblici | bando del 2020 | uguale (bando non per imprese: lo fermerà il controllo preliminare della Parte 4) |
| 4136 IRFIS ciclone Harry | bando e 7 moduli | uguale; i moduli ora sono marcati "modulistica" e restano fuori dal testo per Sonnet |
| 4199 CCIAA Modena (incentivi.gov.it) | solo la scheda del catalogo | **pagina della Camera** (link all'ente del catalogo) con il bando e il modulo |
| 4231 CCIAA Pistoia-Prato (incentivi.gov.it) | solo la scheda del catalogo | **pagina della Camera** con 9 documenti, bando compreso |
| 4383 CCIAA Bari | bando e 6 moduli | uguale; la pagina ora è quella della Camera anche per il doppione del catalogo (4332) |
| 358 notizia di Unioncamere Veneto | solo la notizia | la notizia è un doppione dubbio del bando della Camera di Padova (annuncio 289), che ha pagina, bando e decreto |

### I 3 bandi non trovati (20 a caso)

- **717** "ReStart – Guida e video all'invio online": la pagina non esiste più (errore 404). Non era un bando.
- **718** "Imprenditoria femminile" (Camera di Varese): pagina di menu senza bando. Giusto scartarla.
- **188** "Agevolazione TARIC 2025" (Comune della Spezia): pagina con pochissimo testo e nessun documento. Probabile agevolazione sulla tariffa rifiuti; da guardare a mano, ma senza documenti non c'è niente da far leggere a Sonnet.

### Trovati ma senza il testo del bando (4 su 17)

- **601** notizia del Fondo di garanzia sugli enti del Terzo settore, **911** calendario FESR del Veneto (un file CSV), **915** presentazione FSE+ del Friuli (un PDF di un evento): **non sono bandi**, sono errori dello smistamento. La pagina esiste e contiene parole da bando, quindi il controllo senza IA la accetta. Li fermerà il controllo preliminare con Haiku (Parte 4: "c'è il testo di un bando?").
- **663** Camera di Sondrio, "Bando Fiere internazionali in Lombardia": è la pagina camerale del bando regionale, senza documenti propri. Il bando vero è lo stesso di 459: è un doppione che la deduplica non ha preso, perché i titoli sono diversi.

## Cosa è stato corretto strada facendo

- **Perché la 2814 non aveva allegati.** Il sito Imprese dell'Emilia-Romagna è fatto con Plone/Volto: la pagina si costruisce con JavaScript e nell'HTML non c'è nessun link ai documenti. Il bando e i moduli stanno due livelli sotto ("Presentazione domanda" → "Bando e modulistica") e si vedono solo dall'API del sito (`++api++`). Nuova regola nel registro, `documenti: plone_api`, anche per il Comune di Pordenone (che espone l'API sotto `/api`).
- **Camera di Modena** (Plone classico): i documenti hanno indirizzi senza estensione (`…/allegati/bando-…/download/file`). Ora si riconoscono e il tipo si legge dalla risposta del server.
- **Regione Lombardia**: le pagine `faiDomanda` (domanda con login) sono escluse. La pagina di dettaglio si trova con la ricerca del sito (`/servizi/servizio/bandi/ricerca`, POST con il codice), verificata sul caso RLO12026055023 e su altri 4 codici.
- **Fondo di garanzia (MCC)**: 10 annunci hanno un indirizzo relativo (`/il-fondo-…/`), un difetto della raccolta di quella fonte. La ricerca della pagina lo completa con l'indirizzo della fonte; il difetto della raccolta resta da correggere.
- **Pordenone**: l'API salva l'indirizzo `/api/it/…`. La pagina per le persone è la stessa senza `/api`: regola `sostituisci` nel registro.
- Un PDF della Camera delle Marche conteneva caratteri nulli, che Postgres rifiuta: si tolgono prima di salvare (il difetto c'era già prima).

## Ordine dei documenti per Sonnet

Ogni allegato ha una categoria (bando, pagina, FAQ, decreto, graduatoria, modulistica, altro) ricavata dal nome. Il testo per la scheda (`documenti_per_scheda` in `app/schede/allegati.py`) mette **prima il bando**, poi la pagina ufficiale, le FAQ, il decreto più recente, le graduatorie e il resto. **La modulistica resta fuori.** Se il testo è troppo lungo si tagliano gli ultimi documenti, mai il bando. Nel caso Lombardia fiere il bando (108.000 caratteri) arriva per primo, mentre il 25/09 era arrivato quarto e troncato dopo due delibere.

## Da fare dopo

- Correggere la raccolta del Fondo di garanzia (indirizzi relativi).
- Una regola per i doppioni "stessa pagina ufficiale": oggi due bandi con la stessa pagina restano separati.
- Le pagine camerali che ripetono un bando regionale (663) si riconosceranno meglio quando Haiku deciderà i dubbi.
