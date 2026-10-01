# Analisi della struttura e delle prestazioni (02/10/2026)

*Richiesta di Matteo: valutare debolezze e miglioramenti di progetto e orchestratori. Misure del 01/10 (12:17–23:31 UTC) su produzione, solo in lettura. Lo stato degli interventi è in fondo.*

## Numeri misurati

| Cosa | Valore |
|---|---|
| Server | 4 CPU, 7,6 GB di RAM (2,1 usati), carico medio 0,3; disco 72 GB, 43 liberi |
| Database | 340 MB (allegati 211 MB di testo estratto, bandi 47, versioni 46, annunci 22) |
| Volume allegati | 11 GB, 25.161 file; crescita 0,7–1,2 GB al giorno; recuperabili 1,6 GB di doppi (stessa impronta) |
| Backup notturno | 117 MB compressi, solo il database, sullo stesso disco |
| Giro della raccolta | 0–3,7 minuti; controllo medio 1,2 s; fonti più lente: Latina 60 s, MIMIT fino a 66 s |
| Giro del regista | mediana 15 minuti, massimo 30 (documenti 6–17 min; smistamento IA fino a 21 min per aprire le pagine) |
| Intervallo reale tra i giri | 68–84 minuti (l'ora di attesa parte dopo la fine del lavoro) |
| Batch API | circa 13,5 ore dall'invio alla risposta |
| Spesa IA | 2,60 $ in tutto al 01/10: doppione 0,0045 $, preliminare 0,011 $, lotto di smistamento da 20 annunci 0,042 $ |
| Query della plancia | catalogo 104 ms, imbuto 114 ms, supervisione < 75 ms: oggi non sono un problema |

## Debolezze e stato

| Gravità | Debolezza | Stato |
|---|---|---|
| alta | Nessuna protezione se due lavori girano insieme (giro del regista e comandi a mano sugli stessi bandi; migrazioni lanciate insieme da app e raccolta) | **risolto** (PR del 02/10): blocchi nel database per ogni passo (`app/db/blocchi.py`) e per le migrazioni |
| alta | Una scheda nuova arrivava dopo 1–3 giorni: un solo lotto Batch alla volta per tutto, preliminare e scheda in due lotti successivi | **risolto**: controlli preliminari con chiamata diretta nello stesso giro (circa 1 centesimo l'uno), un lotto in volo per tipo; una scheda arriva in circa 13 ore |
| alta | La Supervisione diceva "0 fonti controllate" (ora di Roma contro UTC) e "email inviata" anche senza destinatario | **risolto**; l'email registra "non inviata: manca EMAIL_MATTEO". Resta da mettere `EMAIL_MATTEO` e `RESEND_API_KEY` nel `.env` (Matteo) |
| media | Lotti falliti mai riprovati | **risolto**: una riprova automatica |
| media | Il tetto di spesa non contava i lotti in volo | **risolto**: conta il costo stimato dei lotti in attesa. Il tetto resta 30 $ (scelta di Matteo); il piano stimava 45–75 $ al mese con tutto acceso |
| media | Smistamento IA che blocca il giro 20 minuti (apre una pagina per annuncio) | **ridotto**: 100 annunci per giro invece di 400 |
| media | Strumenti delle sessioni in `/tmp`, che si svuota dopo 30 giorni | **risolto**: `strumenti/sessione/` nel repository |
| media | Homepage degli enti prese come pagina ufficiale (bs.camcom.it per 3 bandi) | **risolto per i bandi nuovi**: la homepage del portale di un ente (Comune, Camera, Regione, Provincia, Ministero, Invitalia) non vale; i siti dedicati a una misura sì. 30 bandi esistenti hanno una homepage come pagina: quasi tutti "in disparte" (scheda su sintesi) |
| media | Nessun controllo automatico dei test prima di unire in `main` | **risolto**: GitHub Actions con un Postgres di prova (tutti i test, anche quelli sul database) e build della plancia |
| media | Documenti (11 GB) senza un backup verificato; backup del database sullo stesso disco, senza controllo dell'esito | **da fare**: serve una destinazione fuori dal server e verificare il backup del disco OVH (Matteo) |
| media | Ogni unione in `main` ricostruisce e riavvia tutto, anche a metà giro | **da fare** (script di deploy sul server) |
| bassa | Log dei container senza limite | **risolto**: 5 file da 20 MB per servizio |
| bassa | `CLAUDE.md` e manuale non aggiornati (modelli, ritmo del regista) | **risolto** |
| bassa | 26 bandi "aperti" per le date ma "chiusi" per il controllo preliminare; 311 schede senza date; 21 coppie di bandi con titolo ed ente identici | da guardare |
| bassa | `bandi_versioni` cresce con i ricalcoli di stato (17.484 righe, 46 MB) | da fare quando servirà |
| bassa | File grandi (`ia.py` 965 righe, `allegati.py` 932), logica preliminare→scheda in due posti | da fare con calma |

## Cosa va bene

La raccolta è veloce ed educata con i siti; database e CPU sono quasi scarichi; ogni passo del regista è protetto (se uno fallisce gli altri vanno avanti); segreti solo nel `.env`; le query reggono senza problemi questi volumi.
