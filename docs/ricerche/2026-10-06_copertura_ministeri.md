# Copertura dei ministeri e degli enti nazionali

**Data**: 06/10/2026

**Domanda** (Matteo): "Abbiamo tutti i ministeri?". Per ogni ministero del governo in carica e per le agenzie e gli enti nazionali che danno incentivi alle imprese: c'è una fonte nel registro? È sana? Se manca, quale pagina o feed si può osservare?

**Metodo**: elenco dei ministeri preso da governo.it (pagine "I Ministeri" e "Ministri e Sottosegretari", lette il 06/10/2026: governo Meloni, 15 ministeri con portafoglio e 9 ministri senza portafoglio). Stato delle fonti nazionali dalla tabella `fonti` di produzione (ultimo controllo, ultimo annuncio). Lettura diretta dei siti dal VPS con curl (User-Agent BandiRadar), controllo di robots.txt, poi prova di ogni voce nuova con il codice della raccolta (`python -m app.raccolta.esegui --prova ID`, in un container con il codice del branch). I numeri di annunci sono quelli letti nella prova.

**Limiti**: per gli enti esclusi la verifica è stata la lettura della home e della sezione bandi, non di tutto il sito. MIT, MUR, MAECI, ENEA e Fondimpresa non si leggono dal server, quindi per loro non c'è un indirizzo verificato. I fondi interprofessionali sono una ventina: qui solo i tre più noti (Fondimpresa, Fondirigenti, For.Te.).

## Stato delle fonti nazionali già nel registro (prima di questa ricerca)

| Fonte | Ultimo controllo | Ultimo annuncio | Giudizio |
|---|---|---|---|
| incentivi_gov_ricerca (catalogo incentivi.gov.it) | ok 06/10, 771 misure | 05/10 | sana |
| mimit_incentivi, mimit_incentivi_aggiornamenti | ok 06/10 | 22/09 e 29/09 | sane |
| invitalia_incentivi_imprese, _in_apertura, _fare_impresa | ok 05-06/10 | 29/09, 03/10 | sane |
| simest_finanziamenti_agevolati, _internazionalizzazione_strumenti, _comunicati_stampa | ok 05-06/10 | 24/09, 28/09 | sane (elenchi che cambiano poco) |
| mcc_fondo_garanzia_news | ok 01/10 | 21/09 | sana (settimanale) |
| gse_bandi_avvisi | ok 04/10 (un errore negli ultimi 14 giorni) | 02/10 | sana |
| masaf_bandi_gare | ok 01/10 | 29/09 | sana |
| mase_bandi_avvisi | ok 06/10 | 02/10 | sana |
| ministero_turismo_strumenti | ok 05/10 | 05/10 | sana |
| lavoro_notizie, inail_incentivi_imprese, inps_circolari_incentivi, unioncamere_marchi_disegni | ok 06/10 (aggiunte oggi) | solo lettura completa | sane, da rivedere tra una settimana |
| ismea_strumenti | errore (difficile) | — | non leggibile (certificato e firewall) |
| cdp_imprese, incentivi_gov_open_data | esclusa | — | escluse con motivo |

## Ministeri del governo in carica

Ministeri con portafoglio (15):

| Ministero | Fonte | Stato | Azione | Copertura |
|---|---|---|---|---|
| Affari Esteri e Cooperazione Internazionale (MAECI) | `maeci_opportunita` | difficile | nuova voce: sito dietro il bot manager Radware; gli strumenti per l'export (Fondo 394) arrivano da SIMEST | non chiaro |
| Interno | — | escluso | non dà contributi alle imprese: fondi a comuni e prefetture; il Fondo antiracket è una domanda individuale delle vittime, non un bando | no |
| Giustizia | — | escluso | nessun bando per imprese (gare e concorsi) | no |
| Difesa | — | escluso | solo gare e contratti | no |
| Economia e Finanze (MEF) | — | escluso | non pubblica bandi per imprese: "Bandi" sono gare e concorsi; i crediti d'imposta li gestisce l'Agenzia delle Entrate (misure in `app/misure/misure.yaml`) | no |
| Imprese e Made in Italy (MIMIT) | `mimit_incentivi`, `mimit_incentivi_aggiornamenti`, `incentivi_gov_ricerca` | attive, sane | nessuna | sì |
| Agricoltura, Sovranità alimentare e Foreste (MASAF) | `masaf_bandi_gare` | attiva, sana | nessuna (ISMEA a parte, sotto) | sì |
| Ambiente e Sicurezza energetica (MASE) | `mase_bandi_avvisi` (+ GSE) | attiva, sana | nessuna | sì |
| Infrastrutture e Trasporti (MIT) | `mit_incentivi` | difficile | nuova voce: certificato HTTPS incompleto, la raccolta non si collega; incentivi autotrasporto, Marebonus, Ferrobonus oggi da incentivi.gov.it (6 schede) | non chiaro |
| Lavoro e Politiche sociali | `lavoro_notizie` | attiva | aggiunta stamattina (Fondo screening DAE) | sì |
| Istruzione e Merito (MIM) | — | escluso | bandi per scuole e studenti, nessun contributo alle imprese | no |
| Università e Ricerca (MUR) | `mur_bandi` | difficile | nuova voce: tutto il sito risponde 403 con la verifica Cloudflare; bandi di ricerca aperti anche alle imprese | non chiaro |
| Cultura (MiC) | `cultura_avvisi`, `cultura_bandi`, `cultura_cinema_bandi`, `cultura_spettacolo_news`; `cultura_creativita_bandi` | 4 attive, 1 difficile | **nuove voci**: prima nessuna fonte del MiC | sì |
| Turismo | `ministero_turismo_strumenti` | attiva, sana | nessuna | sì |
| Salute | — | escluso | bandi di ricerca per IRCCS e Regioni, non per imprese | no |

Ministri senza portafoglio (9, strutture della Presidenza del Consiglio):

| Ministro / Dipartimento | Fonte | Stato | Azione | Copertura |
|---|---|---|---|---|
| Rapporti con il Parlamento | — | escluso | nessuna funzione di spesa verso le imprese | no |
| Pubblica Amministrazione (Funzione pubblica) | — | escluso | avvisi per amministrazioni e dipendenti pubblici | no |
| Affari regionali e Autonomie | — | escluso | fondi a comuni (isole minori, montagna, confini): trasferimenti agli enti, non bandi per imprese | no |
| Protezione civile e Politiche del mare | — | escluso | nessun contributo alle imprese | no |
| Sport e Giovani: Dipartimento per lo Sport | `sport_bandi_avvisi` | attiva | **nuova voce** (contributo a fondo perduto ai gestori di impianti natatori) | sì |
| Sport e Giovani: Politiche giovanili e Servizio civile | — | escluso | bandi di servizio civile e per associazioni | no |
| Famiglia, Natalità e Pari opportunità: Dipartimento per le politiche della famiglia | `famiglia_avvisi_bandi` | attiva | **nuova voce** (welfare aziendale, conciliazione vita-lavoro) | sì |
| Famiglia, Natalità e Pari opportunità: Dipartimento Pari opportunità | — | escluso | "Bandi e avvisi" quasi solo per enti del terzo settore e territoriali; la certificazione della parità di genere passa dalle Camere | no |
| Riforme istituzionali | — | escluso | nessuna funzione di spesa | no |
| Disabilità | — | escluso | fondi a enti e Regioni | no |
| Affari europei, Sud, Coesione e PNRR: Dipartimento per le politiche di coesione | `coesione_avvisi_bandi` | attiva | **nuova voce** (Fondo di contrasto alla deindustrializzazione 2026) | sì |
| Presidenza: Dipartimento per l'informazione e l'editoria | `editoria_bandi_avvisi` | attiva | **nuova voce** (avvisi per le imprese editrici) | sì |
| Presidenza: Dipartimento per la trasformazione digitale | — | escluso | avvisi PNRR per le pubbliche amministrazioni | no |

## Agenzie ed enti nazionali

| Ente | Fonte | Stato | Azione | Copertura |
|---|---|---|---|---|
| incentivi.gov.it | `incentivi_gov_ricerca` | attiva, sana | nessuna | sì |
| Invitalia | 3 voci `invitalia_*` | attive, sane | nessuna | sì |
| SIMEST | 3 voci `simest_*` | attive, sane | nessuna | sì |
| Mediocredito Centrale / Fondo di garanzia | `mcc_fondo_garanzia_news` | attiva, sana | nessuna | sì |
| GSE | `gse_bandi_avvisi` | attiva, sana | nessuna | sì |
| ENEA | `enea_bandi` | difficile | nuova voce: certificato HTTPS incompleto come MIT e ISMEA | non chiaro |
| INAIL | `inail_incentivi_imprese` | attiva | aggiunta stamattina | sì |
| INPS | `inps_circolari_incentivi` | attiva | aggiunta stamattina | sì |
| ICE | `ice_home` | esclusa | nuova voce esclusa: servizi (fiere, formazione), non bandi; la home letta dà 16 link di fiere e notizie in inglese; le "misure straordinarie" sono banner senza testo | no |
| Unioncamere | `unioncamere_marchi_disegni` (+ Unioni regionali in `camere.yaml`) | attiva | nessuna; altre iniziative nazionali (contributi alternanza, imprenditoria femminile) sono progetti delle Camere, già lette | in parte |
| Cassa Depositi e Prestiti | `cdp_imprese` | esclusa | nessuna: prodotti finanziari, non bandi | no |
| SACE | — | escluso | garanzie e assicurazioni a sportello, non bandi; il sito risponde 403 al server | no |
| Agenzia delle Entrate | — | escluso | non pubblica bandi: le finestre dei crediti d'imposta (ZES, 4.0/5.0, R&S) sono seguite nelle misure nazionali e annunciate dal MIMIT | no |
| Agenzia per la Cybersicurezza Nazionale (ACN) | `acn_avvisi` | attiva | **nuova voce** (contributi a fondo perduto per startup cyber, call dei programmi di accelerazione) | sì |
| AgID | — | escluso | avvisi per le pubbliche amministrazioni | no |
| ISMEA | `ismea_strumenti` | difficile | nessuna (valutata stamattina) | non chiaro |
| Sport e Salute | `sportesalute_bandi` | attiva | **nuova voce** (voucher e contributi per ASD/SSD, comuni) | sì |
| Istituto per il Credito Sportivo e Culturale | — | escluso | mutui agevolati e contributi negli interessi a sportello; i bandi "Missione Comune" sono per i comuni | no |
| MiC - DG Cinema e audiovisivo | `cultura_cinema_bandi` | attiva | **nuova voce** | sì |
| MiC - DG Spettacolo | `cultura_spettacolo_news` | attiva | **nuova voce** (feed RSS) | sì |
| MiC - DG Creatività contemporanea | `cultura_creativita_bandi` | difficile | nuova voce: portale in JavaScript con API interna, ma robots.txt vieta tutto | non chiaro |
| AICS (cooperazione allo sviluppo) | — | escluso | i bandi "profit" per imprese sono fermi al 2017-2019; oggi bandi per organizzazioni non profit | no |
| Agenzia Spaziale Italiana | `asi_bandi` | difficile | nuova voce: l'elenco non è nel HTML; bandi soprattutto contratti e appalti della space economy | non chiaro |
| Fondimpresa | `fondimpresa_avvisi` | difficile | nuova voce: il sito non risponde al server | non chiaro |
| Fondirigenti | `fondirigenti_avvisi` | attiva | **nuova voce** | sì |
| Fondo For.Te. | `fondoforte_avvisi` | attiva | **nuova voce** | sì |
| Ente Nazionale per il Microcredito | — | non chiaro | la home non ha sezioni bandi; affianca misure di altri (Resto al Sud), non verificato oltre | non chiaro |

## Fonti aggiunte e prova

| Voce | Indirizzo | Modalità | Annunci letti in prova | Note |
|---|---|---|---|---|
| `cultura_avvisi` | cultura.gov.it/comunicati/avvisi | html, selettore `#cardsList h3.card-title` | 15 | senza selettore entravano 5 notizie del 2021 da un riquadro laterale |
| `cultura_bandi` | cultura.gov.it/comunicati/bandi-e-concorsi | html, stesso selettore | 15 | soprattutto gare: smistamento con l'IA |
| `cultura_cinema_bandi` | cinema.cultura.gov.it/comunicazione/notizie/bandi-incentivi/ | html | 15 | poche notizie all'anno |
| `cultura_spettacolo_news` | spettacolo.cultura.gov.it/feed/ | rss | 12 | bandi FNSV, jazz, festival, carnevali |
| `coesione_avvisi_bandi` | politichecoesione.governo.it/it/finanziamenti-avvisi-e-bandi/ | html, `#main-page .card` | 76 | schede con sottopagine: la nuova edizione di una misura è una sottopagina |
| `sport_bandi_avvisi` | sport.governo.it/it/bandi-e-avvisi/ | html, solo titoli delle schede | 24 | con le sottopagine erano 130 (allegati e modelli) |
| `sportesalute_bandi` | sportesalute.eu/bandi-e-avvisi.html | html | 104 (circa 35 titoli diversi: più link per scheda) | titoli dalla scheda dell'avviso |
| `famiglia_avvisi_bandi` | famiglia.governo.it/.../avvisi-e-bandi/ | html | 9 | il feed RSS è vuoto |
| `editoria_bandi_avvisi` | informazioneeditoria.gov.it/it/attivita/bandi-e-avvisi/ | html, `#main-page .card` | 27 | 3 avvisi con le sottopagine |
| `acn_avvisi` | acn.gov.it/portale/avvisi | html | 20 | il feed RSS del sito è quello delle vulnerabilità |
| `fondirigenti_avvisi` | fondirigenti.it (home, schede degli avvisi) | html | 5 | la pagina /avvisi ha solo PDF con titoli uguali |
| `fondoforte_avvisi` | fondoforte.it/elenco-avvisi/ | html | 5 | |

Per Fondirigenti e Sport e Salute il lettore delle pagine è stato ritoccato: i link "Approfondisci" e "Visita la pagina dedicata" ora prendono il titolo della scheda che li contiene (come già "Scopri di più"), e il titolo generico scritto dentro il link stesso non vale come titolo della scheda. In produzione nessun annuncio ha oggi un titolo che comincia con "Approfondisci", e uno solo con "visita la pagina": il ritocco non cambia le altre fonti. Controllo a campione su 7 fonti HTML già attive (Invitalia ×2, Unioncamere, INAIL, SIMEST, Lavoro, GSE): stessi annunci letti in produzione. Non è stato rifatto il confronto completo su tutte le 138 fonti HTML.

## Sintesi

1. **Prima**: dei 15 ministeri con portafoglio ne avevamo 5 con una fonte propria (MIMIT, MASAF, MASE, Lavoro da stamattina, Turismo), nessuno dei 9 ministri senza portafoglio; tra gli enti, incentivi.gov.it, Invitalia, SIMEST, MCC, GSE, INAIL, INPS, Unioncamere.
2. **Dopo**: 6 ministeri con portafoglio coperti (si aggiunge la **Cultura**, con 4 fonti), 3 difficili (MAECI, MIT, MUR) e 6 esclusi perché non danno contributi alle imprese. Tra i senza portafoglio: coperti Sport, Famiglia, Coesione e PNRR, più il Dipartimento editoria della Presidenza; gli altri esclusi.
3. **Enti nuovi**: ACN, Sport e Salute, Fondirigenti, For.Te.; difficili ENEA, Fondimpresa, ASI, DG Creatività contemporanea.
4. Il buco più importante era il **Ministero della Cultura**: 19 misure su incentivi.gov.it e decine di bandi l'anno di direzioni generali (libro, cinema, spettacolo) che non leggevamo.
5. MIT ed ENEA (e ISMEA) hanno lo stesso problema tecnico: certificato HTTPS incompleto. Insegnare alla raccolta a completare la catena dei certificati sbloccherebbe tre fonti insieme.
6. MUR e MAECI sono dietro protezioni anti-robot (Cloudflare, Radware): servirebbe il browser senza interfaccia, come per il Ministero del Turismo, con esito incerto.

## Conseguenze per il registro delle fonti

- Aggiunte a `fonti/nazionali.yaml` 12 voci attive (frequenza settimanale, `cultura_avvisi` tre volte a settimana), 7 voci difficili (`mit_incentivi`, `mur_bandi`, `maeci_opportunita`, `enea_bandi`, `fondimpresa_avvisi`, `cultura_creativita_bandi`, `asi_bandi`) e una esclusa (`ice_home`), ognuna con il motivo.
- Le voci nuove sono quasi tutte elenchi misti (gare, concorsi, contributi a comuni e associazioni): lo smistamento scarta il resto, come per MASAF e MASE.
- Da fare: certificati incompleti (MIT, ENEA, ISMEA); provare MUR e MAECI con il browser; mappare gli altri fondi interprofessionali (Fondartigianato, Fon.Coop, Fondoprofessioni, Fonter...) in una ricerca a parte, se Matteo li vuole.
