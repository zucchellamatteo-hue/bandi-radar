-- Situazione dei bandi (06/10/2026, richiesta di Matteo): ogni bando ha UNA situazione, calcolata solo qui, con il
-- perche' accanto (motivo, chi ha deciso, quando). Plancia, revisioni, sessioni e agenti contano e descrivono i bandi
-- SOLO da questa vista (app/catena/situazione.py; a mano: python -m app.catena.situazione). Nomi e spiegazioni delle
-- voci sono in app/catena/situazione.py. L'ordine dei casi conta: vince la prima condizione vera.
--
--   unito                     doppione: i suoi annunci sono passati a un altro bando (unito_a)
--   scartato_non_per_imprese  controllo preliminare o ricontrollo: non e' per imprese (anche se ha una scheda)
--   chiuso_con_scheda         scheda fatta, ma il bando ora e' chiuso (scadenza passata o chiusura anticipata)
--   nascosto_per_errori       scheda sul bando ufficiale con problemi gravi del controllo senza IA
--   proponibile               scheda sul bando ufficiale, senza problemi gravi, non chiuso: si propone alle imprese
--   in_disparte               manca il testo ufficiale: scheda fatta su una sintesi, oppure solo sintesi tra i documenti
--   scartato_chiuso           fermato prima della scheda: chiuso o edizione passata
--   scartato_altro            fermato prima della scheda per altri motivi (nessun testo del bando da leggere)
--   in_lavorazione            ancora in catena: la colonna "fase" dice dove (pagina, documenti, preliminare, scheda)
CREATE OR REPLACE VIEW bandi_situazione AS
SELECT x.id, x.titolo, x.ente, x.stato, x.scadenza, x.unito_a, x.situazione, x.fase,
       CASE
           WHEN x.situazione = 'unito' THEN 'doppione: unito al bando n. ' || x.unito_a
           WHEN x.situazione IN ('scartato_non_per_imprese', 'scartato_chiuso', 'scartato_altro')
                OR x.fase = 'seconda_lettura_in_coda' THEN x.preliminare->>'motivo'
           WHEN x.situazione = 'chiuso_con_scheda' THEN
               CASE WHEN x.chiuso_il IS NOT NULL THEN 'chiuso il ' || to_char(x.chiuso_il, 'DD/MM/YYYY')
                    WHEN x.scadenza IS NOT NULL THEN 'scaduto il ' || to_char(x.scadenza, 'DD/MM/YYYY')
                    ELSE 'chiuso' END
               || coalesce(': ' || CASE WHEN x.ricontrollo->>'stato' IN ('chiuso', 'esaurito') THEN x.ricontrollo->>'motivo' END, '')
           WHEN x.situazione = 'nascosto_per_errori' THEN
               (SELECT string_agg(g, '; ') FROM jsonb_array_elements_text(x.controllo->'gravi') g)
           WHEN x.situazione = 'proponibile' THEN x.da_aggiornare
           WHEN x.fase = 'scheda_solo_sintesi' THEN 'scheda fatta su una sintesi: manca il testo ufficiale del bando'
           WHEN x.fase = 'scheda_nessun_documento' THEN 'scheda fatta senza documenti del bando'
           WHEN x.situazione = 'in_disparte' THEN x.documentazione_motivo
           WHEN x.fase = 'pagina_non_trovata' THEN x.pagina_motivo
           WHEN x.fase = 'scheda_in_coda' THEN 'controllo preliminare superato: ' || coalesce(x.preliminare->>'motivo', '')
           WHEN x.fase = 'preliminare_in_coda' THEN x.documentazione_motivo
       END AS motivo,
       CASE
           WHEN x.situazione IN ('scartato_non_per_imprese', 'scartato_chiuso', 'scartato_altro')
                OR x.fase = 'seconda_lettura_in_coda' THEN
               coalesce(x.preliminare->>'deciso_da',
                        CASE WHEN x.preliminare->>'motivo' LIKE 'Ricontrollo%'
                                  OR x.preliminare->>'compilato_da' LIKE 'claude-code%' THEN 'sessione' ELSE 'ia' END)
           WHEN x.situazione = 'chiuso_con_scheda' THEN
               CASE WHEN x.ricontrollo->>'stato' IN ('chiuso', 'esaurito') THEN 'sessione' ELSE 'regole' END
           WHEN x.situazione = 'nascosto_per_errori' THEN 'regole'
           WHEN x.situazione IN ('proponibile', 'in_disparte') AND x.completezza IS NOT NULL THEN
               CASE WHEN x.modello_scheda LIKE 'claude-code%' THEN 'sessione' WHEN x.modello_scheda IS NOT NULL THEN 'ia' END
           WHEN x.situazione = 'in_disparte' THEN 'regole'
       END AS deciso_da,
       CASE
           WHEN x.situazione = 'unito' THEN
               (SELECT max(v.salvata_il) FROM bandi_versioni v
                 WHERE v.bando_id = x.id AND (v.dati->>'unito_a') IS DISTINCT FROM x.unito_a::text)
           WHEN x.situazione IN ('scartato_non_per_imprese', 'scartato_chiuso', 'scartato_altro')
                OR x.fase = 'seconda_lettura_in_coda' THEN
               coalesce((x.preliminare->>'deciso_il')::timestamptz,
                        (SELECT max(v.salvata_il) FROM bandi_versioni v
                          WHERE v.bando_id = x.id AND v.dati->'preliminare' IS DISTINCT FROM x.preliminare))
           WHEN x.situazione = 'chiuso_con_scheda' THEN x.stato_calcolato_il::timestamptz
           WHEN x.situazione = 'nascosto_per_errori' THEN (x.controllo->>'fatto_il')::timestamptz
           WHEN x.completezza IS NOT NULL THEN x.scheda_il
           WHEN x.situazione = 'in_disparte' THEN x.allegati_cercati_il
           ELSE greatest(x.aggiornato_il, x.pagina_cercata_il, x.allegati_cercati_il)
       END AS deciso_il
FROM (
    SELECT b.id, b.titolo, b.ente, b.stato, b.scadenza, b.chiuso_il, b.unito_a, b.completezza, b.controllo, b.preliminare,
           b.documentazione_motivo, b.pagina_motivo, b.da_aggiornare, b.scheda_il, b.stato_calcolato_il, b.aggiornato_il,
           b.pagina_cercata_il, b.allegati_cercati_il, b.dati->>'modello' AS modello_scheda, b.dati->'ricontrollo_stato' AS ricontrollo,
           CASE
               WHEN b.unito_a IS NOT NULL THEN 'unito'
               WHEN b.preliminare->>'per_imprese' = 'no' THEN 'scartato_non_per_imprese'
               WHEN b.completezza IS NOT NULL AND b.stato = 'chiuso' THEN 'chiuso_con_scheda'
               WHEN b.completezza = 'bando_ufficiale' AND g.gravi THEN 'nascosto_per_errori'
               WHEN b.completezza = 'bando_ufficiale' THEN 'proponibile'
               WHEN b.completezza IS NOT NULL THEN 'in_disparte'
               WHEN b.preliminare->>'seconda_lettura' = 'da_fare' THEN 'in_lavorazione'
               WHEN b.preliminare->>'edizione_in_corso' = 'no' OR b.preliminare->>'stato' = 'chiuso' THEN 'scartato_chiuso'
               WHEN b.preliminare->>'testo_bando' = 'no' THEN 'scartato_altro'
               WHEN b.documentazione IN ('sintesi', 'nessuno') THEN 'in_disparte'
               ELSE 'in_lavorazione'
           END AS situazione,
           CASE
               WHEN b.unito_a IS NOT NULL THEN 'unito'
               WHEN b.preliminare->>'per_imprese' = 'no' THEN
                   CASE WHEN b.completezza IS NOT NULL THEN 'dopo_la_scheda' ELSE 'prima_della_scheda' END
               WHEN b.completezza IS NOT NULL AND b.stato = 'chiuso' THEN
                   CASE WHEN b.chiuso_il IS NOT NULL THEN 'chiusura_anticipata' ELSE 'scaduto' END
               WHEN b.completezza = 'bando_ufficiale' AND g.gravi THEN 'problemi_gravi'
               WHEN b.completezza = 'bando_ufficiale' THEN
                   CASE WHEN b.da_aggiornare IS NOT NULL THEN 'scheda_da_aggiornare' ELSE 'scheda_pronta' END
               WHEN b.completezza IS NOT NULL THEN 'scheda_' || b.completezza
               WHEN b.preliminare->>'seconda_lettura' = 'da_fare' THEN 'seconda_lettura_in_coda'
               WHEN b.preliminare->>'edizione_in_corso' = 'no' THEN 'edizione_passata'
               WHEN b.preliminare->>'stato' = 'chiuso' THEN 'chiuso'
               WHEN b.preliminare->>'testo_bando' = 'no' THEN 'senza_testo_del_bando'
               WHEN b.documentazione IN ('sintesi', 'nessuno') THEN 'senza_scheda_' || b.documentazione
               WHEN b.pagina_stato IS NULL THEN 'pagina_da_cercare'
               WHEN b.pagina_stato = 'non_trovata' THEN 'pagina_non_trovata'
               WHEN b.allegati_cercati_il IS NULL THEN 'documenti_da_scaricare'
               WHEN b.documentazione IS NULL THEN 'filtro_da_fare'
               WHEN b.preliminare IS NULL THEN 'preliminare_in_coda'
               ELSE 'scheda_in_coda'
           END AS fase,
           b.documentazione
    FROM bandi b
    -- problemi gravi del controllo delle schede (app/schede/controlli.py), come catalogo.proponibile
    CROSS JOIN LATERAL (SELECT CASE WHEN jsonb_typeof(b.controllo->'gravi') = 'array'
                                    THEN jsonb_array_length(b.controllo->'gravi') > 0 ELSE false END AS gravi) g
) x;
