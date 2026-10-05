-- Prossimi passi (05/10/2026, richiesta di Matteo): promemoria e lavori da fare, modificabili dalla plancia.
-- Servono a Matteo come promemoria e alle sessioni di Claude Code come elenco dei lavori da mandare in produzione
-- (python -m app.passi stampa quelli aperti).
CREATE TABLE IF NOT EXISTS prossimi_passi (
    id            bigserial PRIMARY KEY,
    titolo        text NOT NULL,
    dettaglio     text,
    tipo          text NOT NULL DEFAULT 'promemoria' CHECK (tipo IN ('promemoria', 'da_sviluppare', 'decisione')),
    stato         text NOT NULL DEFAULT 'da_fare' CHECK (stato IN ('da_fare', 'in_corso', 'fatto', 'rimandato')),
    priorita      smallint NOT NULL DEFAULT 2 CHECK (priorita BETWEEN 1 AND 3),   -- 1 alta, 2 media, 3 bassa
    chi           text,                                                          -- Matteo, Claude, Luca...
    creato_il     timestamptz NOT NULL DEFAULT now(),
    aggiornato_il timestamptz NOT NULL DEFAULT now(),
    aggiornato_da text
);

-- Elenco iniziale: lo stato del lavoro al 05/10/2026.
INSERT INTO prossimi_passi (titolo, dettaglio, tipo, stato, priorita, chi) VALUES
('Primo accesso dell''amministratore', 'Entrare su finanzagevolata.qiaro.it con nome utente e password del file .env (diventi il primo admin), poi nella pagina Utenti creare il tuo utente admin con la tua email vera.', 'promemoria', 'da_fare', 1, 'Matteo'),
('Dare l''accesso a Luca', 'Pagina Utenti: email di Luca, ruolo revisore, Invita; spuntare catalogo, giudizi, lavoro, modifiche (ampi poteri, senza gestire utenti né vedere i clienti). Mandargli il link copiato.', 'promemoria', 'da_fare', 1, 'Matteo'),
('Primo giro di giudizi sulle schede', 'Luca e Matteo giudicano una ventina di schede (voto e problemi); poi una sessione di Claude le fa rileggere agli agenti e corregge.', 'promemoria', 'da_fare', 1, 'Luca'),
('Attivare le email (Resend)', 'Servono i record DNS di finanzagevolata.qiaro.it su GoDaddy per verificare il dominio su Resend, e la chiave RESEND_API_KEY nel .env. Senza, inviti e email settimanali non partono.', 'promemoria', 'da_fare', 2, 'Matteo'),
('Correggere l''abbinamento dei bandi dei Comuni di altre regioni', 'Un bando di un Comune di un''altra regione senza vincolo di sede scritto risulta compatibile (es. Rimini per un''impresa di Milano). Da correggere nelle regole.', 'da_sviluppare', 'da_fare', 2, 'Claude'),
('Prima campagna sulla mappatura delle imprese', 'Lanciare strumenti/anagrafiche/esporta_profili.py sul proprio computer, caricare il file nella pagina Campagne, rileggere le bozze prima di usarle.', 'promemoria', 'da_fare', 2, 'Matteo'),
('Testi legali: dati del titolare e revisione', 'Riempire i segnaposto (app/pubblico/testi/LEGGIMI.md) e farli rivedere a un professionista prima di vendere.', 'promemoria', 'da_fare', 2, 'Matteo'),
('Soglie del finanziamento agevolato e quota d''avvio', 'Confermare le soglie 200.000 / 1.000.000 euro (2% / 1,5% / 1%) e se la quota d''avvio si restituisce quando è lo studio a interrompere l''incarico.', 'decisione', 'da_fare', 3, 'Matteo'),
('Durata della prova gratuita', 'Oggi 14 giorni (PROVA_GIORNI), provvisorio.', 'decisione', 'da_fare', 3, 'Matteo'),
('Accendere la pagina pubblica', 'PAGINA_PUBBLICA=1 quando il servizio è pronto per essere mostrato; scegliere le schede di esempio (ESEMPI_BANDI).', 'promemoria', 'rimandato', 3, 'Matteo'),
('Account Stripe e pagamenti in prova', 'Rimandato da Matteo il 05/10: prima verificare che il servizio funzioni abbastanza bene da essere venduto.', 'promemoria', 'rimandato', 3, 'Matteo'),
('Fattura elettronica con Invoicetronic', 'Rimandata con Stripe. Serve anche decidere chi emette le fatture (studio o società) e la compatibilità con l''Ordine.', 'decisione', 'rimandato', 3, 'Matteo'),
('Checkout: seconda casella per le clausole e consenso commerciale', 'Approvazione specifica delle clausole (artt. 1341-1342 c.c.) con registrazione della versione dei termini; casella separata per il consenso alle comunicazioni commerciali.', 'da_sviluppare', 'rimandato', 3, 'Claude'),
('Esportazione dei dati dell''utente (GDPR)', 'Pulsante per scaricare i propri dati e cancellare l''account.', 'da_sviluppare', 'da_fare', 3, 'Claude'),
('Bandi lunghissimi e doppioni arretrati', 'Scheda in due passaggi per i bandi oltre 300.000 caratteri (180, 1276, 4160, 4162, 4180); doppioni 1930/1931, 2402/2406, 4198/4202, 979/4043; 3533 (Puglia Sviluppo); 1768 (ATECO 10.41).', 'da_sviluppare', 'da_fare', 3, 'Claude'),
('Misure nazionali da completare', 'Verificare credito formazione e credito design 2026 e aggiungerli alle misure se vigenti.', 'da_sviluppare', 'da_fare', 3, 'Claude');
