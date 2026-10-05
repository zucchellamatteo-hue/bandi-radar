-- Permessi per utente (05/10/2026, richiesta di Matteo): oltre al ruolo, cosa vede e cosa puo' fare chi non e' admin.
-- catalogo (schede e documenti), giudizi (voto e segnalazioni), lavoro (tutte le pagine di lavoro e i giudizi di
-- tutti, in sola lettura), modifiche (rilanciare, pausa, correzioni, doppioni, gestione dei giudizi), imprese (pagina
-- Imprese: clienti, richieste, email, abbonamenti). L'admin ha tutto; l'impresa usa solo la sua area.
ALTER TABLE utenti ADD COLUMN IF NOT EXISTS permessi text[] NOT NULL DEFAULT '{catalogo,giudizi}';
