# Fonti nazionali mancanti e lettura completa di Lazio Innova e MASE

**Data**: 06/10/2026
**Domanda**: le fonti che il rapporto sui bandi discussi (ottobre 2026) indica come mancanti (INAIL, INPS, Unioncamere per Marchi+ e Disegni+, ISMEA) si possono leggere dal server? Si può aggiungere la lettura completa (`scorta`) a `lazio_innova_bandi` e `mase_bandi_avvisi`?

**Metodo**: lettura diretta dei siti dal VPS con curl (User-Agent BandiRadar), controllo di robots.txt, studio del JavaScript delle pagine riempite dal browser (INPS), poi prova di ogni voce con il codice della raccolta (`python -m app.raccolta.esegui --prova ID [--scorta]`, in un container con il codice del branch). Per le modifiche al lettore HTML: confronto tra lettore vecchio e nuovo su tutte le 138 fonti HTML attive, una richiesta per fonte.

**Limiti**: le prove non scrivono nel database; quanti annunci diventeranno bandi lo dirà lo smistamento. Brevetti+ non è stato cercato a parte: è gestito da Invitalia, che è già tra le fonti. `lavoro_notizie` (Ministero del Lavoro) era già stata aggiunta con la PR 83.

## Esito per fonte

| Fonte | Indirizzo visto | robots.txt | Lettura | Annunci alla prova | Giudizio |
|---|---|---|---|---|---|
| `inail_incentivi_imprese` | https://www.inail.it/portale/prevenzione-e-sicurezza/it/prevenzione-e-sicurezza/finanziamenti-per-la-sicurezza/incentivi-alle-imprese.html | vieta solo l'amministrazione trasparente | HTML, selettore `div.pt-4 > ul.list-inline` (il riquadro "Esplora") | 12: Bando ISI 2017–2025, ISI Agricoltura 2019-2020, storico, Bando per la formazione | sì |
| `inps_circolari_incentivi` | https://www.inps.it/it/it/inps-comunica/atti/circolari-messaggi-e-normativa.html | permette tutto (salvo i moduli PDF) | API interna `/content/scorporati/search/jcr:content.search.<parametri in esadecimale>.json`, filtro sull'oggetto "incentiv" | 15 (dal 28/07/2026 al 2025): circolari 55, 56 e 57 del 14/05/2026, messaggi sull'autoimpiego, de minimis | sì, con filtro |
| `unioncamere_marchi_disegni` | https://www.unioncamere.gov.it/innovazione-e-proprieta-industriale/agevolazioni-proprieta-industriale | permette la pagina | HTML, selettore `table td`, titolo dal testo alternativo del logo | 24: Marchi+, Disegni+, Marchi collettivi dal 2021 al 2025 (un sito per edizione) | sì |
| `ismea_strumenti` | https://www.ismea.it/flex/cm/pages/ServeBLOB.php/L/IT/IDPagina/13558 | non letto (certificato) | certificato HTTPS incompleto (la raccolta lo rifiuta); con il controllo disattivato, firewall Barracuda: "You have been blocked"; niente IPv6 | 0 | no: `stato: difficile` |
| `lazio_innova_bandi` (scorta) | https://www.lazioinnova.it/bandi-aperti/ | permette tutto | HTML, selettore `.entry-content`, titolo dal grassetto del paragrafo | 34 avvisi aperti, compresi "Rafforzamento delle capacità manageriali delle imprese" e "Acchiappa Talenti" | sì |
| `mase_bandi_avvisi` (scorta) | https://www.mase.gov.it/portale/bandi-e-avvisi?delta=30&start=1 | robots.txt risponde 403 (nessuna regola) | HTML, 30 per pagina, parametro `start` | 123 in 4 pagine (fino a maggio 2025); con 10 pagine si torna al 2023 | sì, ma il decreto "hard-to-abate" non è nell'elenco |

### Rumore della fonte INPS

Senza filtro l'elenco di circolari e messaggi porta circa 5 voci a settimana (50 tra il 26/07 e il 04/10/2026), quasi tutte su pensioni, contributi e prestazioni: troppo rumore per lo smistamento. Il filtro che il sito stesso usa ("Oggetto contiene") è un parametro dell'API: con "incentiv" escono una decina di voci all'anno, quasi tutte pertinenti. Provati anche "esonero" (esoneri contributivi, anche agricoli: utile ma più misto), "bonus" (mescola bonus alle famiglie) e "agevolaz" (asili nido): non usati.

### Modifiche al lettore HTML (necessarie per Lazio, Unioncamere e MASE)

1. **Titolo dal grassetto del paragrafo**: nella pagina "Bandi aperti" di Lazio Innova ogni avviso è un paragrafo "**Titolo**: domande entro il ... Per saperne di più". Prima il titolo sarebbe stato il titolo della sezione ("Programma Regionale FSE+ 2021-2027") per tutti gli avvisi, e la scadenza quella del primo paragrafo della pagina. Ora titolo e scadenza vengono dal paragrafo.
2. **Logo con testo alternativo**: solo con un selettore nel registro, un link fatto solo di un'immagine prende il titolo dal testo alternativo ("Marchi+ 2025").
3. **`p_l_back_url` di Liferay**: il MASE aggiunge a ogni link la pagina di provenienza, diversa per ogni pagina dell'elenco; senza toglierla, la scorta vedrebbe lo stesso bando come un link nuovo a ogni pagina. Il parametro si toglie anche nella chiave usata per riconoscere i doppioni dei bandi.

Confronto sulle 138 fonti HTML attive: cambiano solo `mase_bandi_avvisi` (link senza il parametro), `unioncamere_marchi_disegni` (nuova), un link non di bando della Città metropolitana di Torino (impresainungiorno.gov.it, titolo diverso) e un link a una guida PDF di Fincalabra (corretto dopo il confronto: se il grassetto è troppo corto si torna al titolo della scheda).

**Da fare al momento dell'unione**: i 42 annunci MASE già in produzione hanno il parametro nel link. Per non vederli tornare come novità, subito dopo il rilascio:

```sql
UPDATE annunci SET url = regexp_replace(url, '\?p_l_back_url=[^&]*$', '')
WHERE fonte_id = 'mase_bandi_avvisi' AND url LIKE '%?p_l_back_url=%';
```

(verificato il 06/10: 42 annunci, 42 indirizzi distinti dopo la pulizia, nessun conflitto).

## Sintesi

- Tre fonti nuove attive: INAIL (Bando ISI: l'ISI 2026 atteso a dicembre comparirà come nuova pagina), INPS (solo circolari e messaggi con "incentiv" nell'oggetto, una decina all'anno), Unioncamere (Marchi+, Disegni+, Marchi collettivi: ogni edizione ha un suo sito che compare nella pagina).
- ISMEA resta fuori: certificato incompleto e firewall che blocca il server; in registro come `difficile` con il motivo.
- Lazio Innova: la pagina "Bandi aperti" elenca 34 avvisi aperti, compresi i due che mancavano; la scorta la legge ogni settimana.
- MASE: la scorta legge 4 pagine da 30 (circa 16 mesi). Il decreto hard-to-abate non è nella sezione "Bandi e avvisi": va inserito a mano o cercato in altre sezioni del sito.
- Avvisi INAIL (chiusure di sedi, orari) non aggiunti: rumore.

## Conseguenze per il registro delle fonti

- Aggiunte in `fonti/nazionali.yaml`: `inail_incentivi_imprese`, `inps_circolari_incentivi`, `unioncamere_marchi_disegni` (attive, settimanali), `ismea_strumenti` (`difficile`).
- `scorta` aggiunta a `lazio_innova_bandi` (`fonti/regioni.yaml`, settimanale) e a `mase_bandi_avvisi` (mensile, 4 pagine).
- Da valutare con Matteo: una seconda fonte INPS con il filtro "esonero"; ISMEA da riprovare se il sito sistema il certificato.
