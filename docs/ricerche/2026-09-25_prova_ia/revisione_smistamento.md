# Revisione dello smistamento fatto da Haiku (prova del 25/09/2026)

## Sintesi

Haiku ha smistato 88 dei 90 annunci inviati (2 spariti nel lotto 1). Sono d'accordo con lui su 66 annunci su 88: **accuratezza 75%**. Il dato va letto tenendo conto che questi sono i casi difficili, cioè quelli che le regole a parole chiave non hanno saputo decidere.
Gli errori che contano sono 8: **3 gravi** (bandi per imprese scartati come non rilevanti) e **5 medi** (annunci non per imprese promossi a rilevanti). Gli altri 14 sono lievi (indecisioni o eccessi di sicurezza).
Nessuno dei 3 bandi persi era ancora aperto (2022, 2024, e un bando UE di nicchia). Però il meccanismo dell'errore è pericoloso: Haiku decide i destinatari da una sola parola del titolo ("scuola", "Comuni", "ricercatori") e sceglie "non_rilevante" con sicurezza invece di "da_rivedere".
Gli errori medi hanno una causa unica e facile da correggere: Haiku tratta come aiuto qualunque cosa riguardi "operatori" (posteggi in fiere e sagre, accreditamento di fornitori di servizi sociali, chiarimenti su una norma).
**Giudizio: non ancora pronto per decidere da solo, ma adeguato con quattro condizioni**: controllo degli id con nuovo invio dei mancanti, lotti più piccoli, prompt corretto (testo proposto sotto), e nessuno scarto definitivo senza una rete di sicurezza per le fonti "ad alto rendimento" (Camere, finanziarie regionali, incentivi.gov.it). Poi va rifatta una prova su un campione nuovo.

## Metriche

| Voce | Valore |
|---|---|
| Annunci inviati | 90 (2 lotti da 45) |
| Risposte ricevute | 88 (lotto 1: 43/45; lotto 2: 45/45) |
| Annunci mancanti | 2: **3518** (EDIH Abruzzo-Molise, per me `da_rivedere`) e **1748** (Career Days universitari, per me `non_rilevante`) |
| Ordine e id delle risposte | corretti (nessun id inventato, ordine rispettato) |
| Accordo con il revisore | 66/88 = **75,0%** (66/90 = 73,3% contando i mancanti come errori) |
| Decisioni senza errori gravi o medi | 80/88 = 90,9% |
| Errori GRAVI (bando per imprese → non_rilevante) | **3** |
| Errori MEDI (non per imprese → rilevante) | **5** |
| Errori LIEVI (da_rivedere vs decisione chiara, o viceversa) | **14** |
| Esiti di Haiku | 29 rilevante, 41 non_rilevante, **18 da_rivedere (20%)** |
| Esiti del revisore (su 90) | 27 rilevante, 48 non_rilevante, 15 da_rivedere |
| Precisione dei "rilevante" di Haiku | 21/29 = 72% (5 falsi, 3 dubbi) |
| Bandi rilevanti trovati da Haiku | 21 dei 27 annunci rilevanti = 78% (3 persi, 3 lasciati in dubbio) |
| "Non_rilevante" di Haiku sbagliati | 3 su 41 = 7% (sono i bandi persi) |
| "Da_rivedere" di Haiku davvero indecidibili | 9 su 18 (gli altri 9 si potevano decidere) |

Tabella di confronto (righe = Haiku, colonne = revisore):

| Haiku \ Revisore | rilevante | non_rilevante | da_rivedere |
|---|---|---|---|
| rilevante | 21 | 5 (MEDIO) | 3 (LIEVE) |
| non_rilevante | 3 (GRAVE) | 36 | 2 (LIEVE) |
| da_rivedere | 3 (LIEVE) | 6 (LIEVE) | 9 |
| mancante | 0 | 1 | 1 |

Metodo: ho giudicato ogni annuncio con le stesse istruzioni date a Haiku e con le sole informazioni del prompt. Per i casi dubbi ho aperto 8 pagine originali, con 9 richieste in tutto: Camera di commercio di Trento, incentivi.gov.it, MASAF due volte, Camera di commercio di Roma, Camera valdostana, open data della Lombardia, Fondazione Cariverona (due tentativi, entrambi respinti con errore 403, e non ho insistito). Dove il mio giudizio si basa sulla pagina lo indico nella tabella con "(pagina)". Un limite da dire: anche il mio giudizio sugli annunci col solo titolo è una stima. Per questo ho dato `da_rivedere` quando non c'erano elementi sufficienti.

## Annunci su cui non sono d'accordo con Haiku (22, più i 2 mancanti)

| id | Titolo breve | Haiku | Revisore | Gravità | Motivo |
|---|---|---|---|---|---|
| 441 | CCIAA Trento – Bando formazione e ASL 2022 | non_rilevante | rilevante | **GRAVE** | (pagina) Contributi alle **imprese** per formazione, sicurezza, e-commerce e alternanza scuola-lavoro. Haiku ha letto "ASL" come "per studenti". Bando del 2022, chiuso. |
| 4254 | incentivi.gov.it – Fondo Comuni marginali, Comune di Gerocarne | non_rilevante | rilevante | **GRAVE** | (pagina) Contributo a fondo perduto per avvio o sviluppo d'impresa, settore commercio, spesa da 12.100 a 28.300 €. Il riassunto citava già le "attività economiche". Haiku ha letto "Comuni" come "residenti". Chiuso a dicembre 2024. |
| 2562 | UE – MSCA Staff Exchanges 2027 | non_rilevante | rilevante | **GRAVE** (impatto pratico basso) | Nel programma MSCA Staff Exchanges partecipano anche organizzazioni non accademiche, imprese comprese. Per coerenza, Haiku ha dato rilevanti gli altri bandi Horizon. |
| 2190 | Brindisi – CIA per locazioni turistiche, chiarimenti | rilevante | non_rilevante | **MEDIO** | Chiarimenti su un obbligo di legge (comunicazione di inizio attività), nessun aiuto. |
| 1952 | Perugia – Home Care Premium, accreditamento operatori | rilevante | non_rilevante | **MEDIO** | L'ente accredita fornitori di prestazioni sociali: per la regola 3 del prompt è `non_rilevante`. |
| 2430 | Oristano – Festa del Rimedio, graduatoria operatori commerciali | rilevante | non_rilevante | **MEDIO** | Assegnazione di posteggi per bancarelle a una sagra: è l'impresa che paga l'ente, non un aiuto. |
| 1518 | Genova – Fiera di Natale, comunicazione operatori | rilevante | non_rilevante | **MEDIO** | Comunicazione agli ambulanti su posteggi e regole di una fiera cittadina. |
| 1144 | Cremona – soggetti accreditati doposcuola | rilevante | non_rilevante | **MEDIO** | Elenco dei fornitori accreditati per un servizio pagato alle famiglie (regola 3). |
| 2535 | UE – Specialised Education Programmes (DIGITAL) | non_rilevante | da_rivedere | LIEVE | Riassunto fuorviante ("tesi di master"). I bandi DIGITAL sulle competenze chiedono consorzi con imprese dentro. Non c'era abbastanza per scartare. |
| 2448 | Cariverona – Bando Zenit Fondo Repubblica Digitale | rilevante | da_rivedere | LIEVE | Solo il titolo; le fondazioni bancarie finanziano di solito enti non profit. La pagina non era leggibile (403). |
| 2447 | Cariverona – Bando Nutrire il cambiamento | rilevante | da_rivedere | LIEVE | Come sopra: la parola "bando" non basta, i destinatari sono ignoti. |
| 2508 | MASAF – Latte nelle scuole, avviso progetti | rilevante | da_rivedere | LIEVE | (pagina di 2509) Sul sito del ministero sta sotto "Gare": è una via di mezzo tra aiuto UE ai fornitori e acquisto di un servizio. |
| 2509 | MASAF – Frutta e verdura nelle scuole, avviso progetti | non_rilevante | da_rivedere | LIEVE | (pagina) È identico a 2508, ma Haiku gli ha dato l'esito opposto: **incoerenza**. |
| 1752 | Città metropolitana di Milano – tavola rotonda sulla transizione energetica | da_rivedere | non_rilevante | LIEVE | Evento senza un bando: per la regola 2 è `non_rilevante`. |
| 3372 | Sviluppumbria – evento "Imprese nell'era dell'AI" | da_rivedere | non_rilevante | LIEVE | Convegno informativo, nessun bando citato (regola 2). |
| 394 | Home page della Camera di commercio di Pordenone-Udine | da_rivedere | non_rilevante | LIEVE | È la home page del sito, non un annuncio. |
| 1129 | Cremona – "Assistenza sociale (6)" | da_rivedere | non_rilevante | LIEVE | È una pagina di categoria (indirizzo con filtro), cioè una voce di menu. |
| 257 | Unioncamere Lombardia – "Sviluppo e competitività delle imprese" | da_rivedere | non_rilevante | LIEVE | Pagina di categoria dell'elenco bandi: i singoli bandi arrivano come annunci separati. |
| 950 | Camera di commercio di Palermo – Infopoint alla Strapapà 2026 | da_rivedere | non_rilevante | LIEVE | Presenza della Camera a una manifestazione, nessun aiuto. |
| 213 | Camera di commercio di Sondrio – Avviso "Trova nuovi mercati" | da_rivedere | rilevante | LIEVE | Avviso camerale per l'internazionalizzazione delle imprese (vecchio, 2014). |
| 37 | Camera valdostana – Artigiano in Fiera, area ristorazione | da_rivedere | rilevante | LIEVE | (pagina) Selezione di un'impresa per la collettiva regionale, pubblicata sotto "Contributi e finanziamenti". |
| 2631 | Lombardia – biosicurezza Peste Suina Africana negli allevamenti | da_rivedere | rilevante | LIEVE | Bando regionale per gli allevamenti suinicoli (imprese agricole). |
| 3518 | Sviluppo Italia Molise – EDIH Abruzzo e Molise | *mancante* | da_rivedere | programma | Servizi digitali agevolati per le PMI, ma la pagina è di presentazione del progetto. |
| 1748 | Città metropolitana di Milano – Career Days | *mancante* | non_rilevante | programma | Ricerca di personale. |

Casi su cui sono d'accordo ma che segnalo:
- **655** (ITS Academy della Camera di Roma, `non_rilevante`): esatto, la pagina conferma borse di studio per studenti. Haiku però ha indovinato dal solo titolo.
- **2498** (graduatoria MASAF del DM 361695): `da_rivedere` è accettabile. La pagina sta sotto "Qualità": sono probabilmente contributi ai consorzi di tutela, quindi con il testo della pagina sarebbe stato `rilevante`.

## Cause ricorrenti degli errori

1. **Destinatari decisi da una sola parola del titolo** (i 3 errori gravi). Haiku ha letto "ASL" e "scuola" come studenti, "Comuni" come residenti, "Staff Exchanges" come ricercatori. Ha ignorato altri indizi, per esempio il riassunto di 4254 che parla di "attività economiche", e la fonte (Camera di commercio, catalogo incentivi.gov.it). In questi casi non ha applicato la regola 4 ("nel dubbio da_rivedere"): era sicuro e sbagliava.
2. **"Operatori" confuso con "aiuto"** (tutti i 5 errori medi). Posteggi per ambulanti, accreditamento di fornitori, chiarimenti su una norma: per Haiku basta che l'annuncio riguardi imprese per renderlo rilevante. Il prompt dice di guardare "chi riceve i soldi", ma non dà esempi dei casi in cui è l'impresa a pagare l'ente o a vendergli un servizio.
3. **Regola 4 usata a sproposito nell'altra direzione** (6 lievi). Eventi senza bando, home page, pagine di categoria: il prompt li classifica già come `non_rilevante` (regola 2 e "voci di menu"), ma Haiku li manda in `da_rivedere`. Così la regola 4 diventa una scappatoia generica.
4. **La fonte non viene usata come indizio**. Un "Bando X" di una Camera di commercio o di una finanziaria regionale è quasi sempre per imprese; un "Bando X" di una fondazione bancaria quasi mai. Haiku ha fatto il contrario: fondazioni rilevanti; Camera di Trento scartata, Camera di Sondrio lasciata in dubbio.
5. **Incoerenza tra annunci gemelli** (2508 e 2509): stessa formula, esiti opposti nello stesso giro.
6. **Mancano informazioni in ingresso**: circa metà degli annunci del campione ha il riassunto vuoto. Sei degli errori, gravi e lievi, si risolvevano leggendo le prime righe della pagina.
7. **Risposte incomplete**: con 45 annunci per chiamata, Haiku ne ha saltati 2, entrambi alla fine del lotto 1 (posizioni 44 e 45). È il sintomo tipico di un lotto troppo lungo.

## Proposte

### A. Prompt (`app/schede/prompt_smistamento.md`)

Aggiungere dopo la regola 3:

```
3-bis. Non sono aiuti, quindi `non_rilevante`, anche se riguardano imprese o "operatori":
   - assegnazione o graduatoria di posteggi, bancarelle, stand a pagamento in fiere, sagre, mercati cittadini;
   - accreditamento o elenchi di fornitori che erogano servizi per conto dell'ente
     (doposcuola, assistenza domiciliare, servizi sociali, anche se pagati con voucher alle famiglie);
   - sponsorizzazioni cercate dall'ente, aste e vendite di beni pubblici, concessione di impianti sportivi;
   - chiarimenti su obblighi, autorizzazioni, tributi, SCIA/CIA senza un contributo.
   È invece `rilevante` la partecipazione a fiere con spazio gratuito o costi coperti, o in una collettiva organizzata da Camera o Regione.

3-ter. Usa la fonte come indizio:
   - un "Bando ..." o "Avviso ..." di una Camera di commercio, di Unioncamere, di una finanziaria regionale
     (Fincalabra, Sviluppumbria, Sviluppo Campania, Finlombarda...) o del catalogo incentivi.gov.it è quasi sempre per imprese:
     `rilevante` salvo segni chiari del contrario (borse di studio per studenti, selezione di personale, sponsorizzazioni, acquisti dell'ente);
   - un bando di una fondazione bancaria senza cenni a imprese è di solito per enti non profit: `da_rivedere`;
   - bandi UE (Horizon, Digital Europe, EIC, SMP/COSME, LIFE, MSCA): `rilevante` se possono partecipare imprese anche in consorzio;
     `non_rilevante` solo se riservati a enti pubblici o persone fisiche.

3-quater. Prima di scegliere `non_rilevante` per "destinatari non imprese" rileggi titolo, riassunto, fonte e indirizzo:
   una parola come "scuola", "Comuni", "formazione", "ricercatori" non basta a escludere le imprese
   (es. contributi alle imprese che ospitano studenti, contributi alle attività economiche dei Comuni marginali).
   Se un indizio dice imprese e un altro dice non imprese, scegli `da_rivedere`.
```

Cambiare la regola 4 in:

```
4. Usa `da_rivedere` solo se il dubbio riguarda chi riceve i soldi. Eventi e convegni senza un bando indicato,
   home page, pagine di categoria o di elenco (es. "Assistenza sociale (6)"), pagine su privacy, trasparenza,
   accesso agli atti sono `non_rilevante` senza dubbio.
```

Aggiungere in fondo alle regole:

```
7. Annunci con la stessa formula (es. due avvisi dello stesso programma) devono avere lo stesso esito.
8. Devi restituire esattamente un oggetto per ogni annuncio ricevuto: sono {{numero_annunci}}. Controlla di non averne saltato nessuno.
```

Utile anche aggiungere 6-8 esempi presi dagli errori di questa prova (441, 4254, 2430, 1144, 2190, 1752, 37), ognuno con l'esito giusto e il motivo.

### B. Regole a parole chiave (`app/schede/regole_smistamento.yaml`)

Le parole `non_rilevante` sono a basso rischio, perché un segnale `rilevante` vince sempre. Quelle nuove avrebbero deciso da sole una ventina di annunci di questo campione (quelli indicati tra parentesi), tutti in modo corretto:
- `pagine_e_menu_del_sito`: `accesso agli atti` (2090, 2094), `social media policy` (1223), `informazioni legali` (3306), `termini e condizioni` (274), `prevenzione della corruzione` (3892), `cookie policy`.
- `comunicazioni_istituzionali`: `chiusura uffici` (2267), `auguri del sindaco` (2399).
- `elezioni_e_istituzioni`: `consiglio provinciale`, `convocazione consiglio` (1343), `seduta di` (1762).
- `servizi_e_viabilita`: `viabilita` da sola (1802, 2424), `rete idrica`, `disservizi` (1333), `bus navetta` (2070).
- nuovo gruppo `beni_e_spazi_pubblici`: `asta pubblica`, `alienazione` (1446), `impianti sportivi`, `palestre` (2250, 1913), `sponsorizzazione` (994).
- `concorsi_e_personale`: `career day*` (1748), `direttore generale` (con: `selezione`, `nomina`) (3534).

Parole `rilevante` (quelle segnate con * decidono un bando perso o lasciato in dubbio in questa prova):
- nel gruppo `bando_o_misura_per_imprese`, aggiungere a `con:` le voci `attivita economiche`\* (4254), `allevament*`, `allevatori`\* (2631), `proprietari forestali`; aggiungere a `parole:` `iniziative`.
- nel gruppo `bando_su_temi_di_impresa`, aggiungere a `con:` le voci `nuovi mercati`\* (213) e `alternanza scuola`\* (441, solo se c'è anche "bando").
- nuove frasi: `partecipazione collettiva` (4185, 4299), `aiuti agli investimenti` (3702), `aiuti a favore` (4351), `comuni marginali` (4254; resta rilevante grazie ad "attività economiche").

### C. Programma

1. **Controllo degli id** (indispensabile). Dopo ogni risposta, verificare che:
   - il JSON sia valido;
   - l'insieme degli id restituiti sia uguale a quello inviato;
   - ogni esito sia uno dei tre ammessi.

   Gli id mancanti vanno rimandati in una seconda chiamata piccola. Se mancano ancora, restano `da_rivedere` con motivo "l'IA non ha risposto". Id sconosciuti o doppi si scartano e finiscono nel registro.
2. **Lotti da 20-25 annunci** invece di 45: in questa prova i due annunci saltati erano gli ultimi del lotto lungo. Il costo non cambia molto, perché le istruzioni si possono mettere in cache e si pagano una volta sola.
3. **Risposta in formato fisso**: chiedere la risposta con uno schema JSON obbligatorio (uno strumento con schema), non con testo libero, e temperatura 0. Così spariscono risposte malformate e variazioni tra un giro e l'altro.
4. **Testo della pagina quando il riassunto è vuoto**: prima di chiamare Haiku, per gli annunci senza riassunto scaricare la pagina (una volta, con il nostro User-Agent e rispettando robots.txt) e passare 1.000-1.500 caratteri del testo principale. In questa prova avrebbe risolto 441, 37 e 2498, e probabilmente 213, 2447 e 2448.
5. **Regole per fonte nel registro**: un campo tipo `smistamento: sempre_rilevante` per il catalogo di incentivi.gov.it e per le pagine di bandi di EIC ed EISMEA. Sono cataloghi di incentivi, quindi non ha senso chiedere all'IA. Avrebbe evitato l'errore grave 4254.
6. **Rete di sicurezza sugli scarti**: gli annunci che Haiku dà `non_rilevante` e che vengono da Camere, Unioncamere, finanziarie regionali, ministeri economici o incentivi.gov.it non vanno scartati in silenzio. Serve un elenco "scartati dall'IA" nella plancia, da scorrere in pochi minuti la settimana. Sono pochi: in questo campione 8 su 41.

## Giudizio

**Con questo prompt e questo programma, Haiku non è adeguato a decidere da solo in produzione.** Il motivo non è il numero di errori, ma il tipo: 3 scarti sbagliati su 41 (7%), fatti con sicurezza e senza passare da `da_rivedere`. E manca il controllo che nessun annuncio vada perso nella risposta.

**È adeguato a queste condizioni**, tutte a basso costo:
1. controllo degli id con nuovo invio dei mancanti, e lotti da 20-25 (senza queste due cose non va in produzione);
2. prompt corretto con i punti 3-bis, 3-ter, 3-quater, la nuova regola 4 e alcuni esempi;
3. testo della pagina per gli annunci senza riassunto, e regola per fonte per incentivi.gov.it;
4. per il primo mese, elenco degli scarti dell'IA dalle fonti ad alto rendimento visibile a Matteo nella plancia;
5. nuova prova su un campione fresco di circa 100 annunci `da_rivedere`, con questi obiettivi: nessun bando aperto perso, al massimo 3% di rilevanti falsi, al massimo 10% di `da_rivedere` rimasti.

Gli errori medi (5 su 29 rilevanti) costano solo qualche scheda Sonnet inutile e qualche minuto di Matteo: sono tollerabili già ora e il punto 3-bis dovrebbe eliminarli quasi tutti. Il 20% di `da_rivedere` lasciato da Haiku è gestibile, ma metà di questi casi erano decidibili: con la nuova regola 4 dovrebbe scendere intorno al 10%.
