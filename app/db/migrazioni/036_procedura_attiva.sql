-- Procedura nuova del regista ACCESA (PIANO_QUALITA azione 0; via di Matteo dopo il ripasso dei proponibili).
-- Un bando con la scheda sul bando ufficiale si propone solo a procedura finita (app/catena/procedura.py, ESITO_SQL):
--   documento verificato e secondo controllo fatto dopo l'ultima scheda, senza errori gravi aperti.
-- Altrimenti:
--   in_disparte / documento_non_valido        il documento non e' il testo ufficiale giusto: lista "da recuperare"
--   in_lavorazione / documento_da_verificare  nessuno ha ancora verificato il documento
--   in_lavorazione / secondo_controllo_da_fare
--   in_lavorazione / errori_da_correggere     il secondo controllo ha trovato errori gravi non ancora corretti
-- Il resto e' la vista della migrazione 031. Ordine dei casi: vince la prima condizione vera.
CREATE OR REPLACE VIEW bandi_situazione AS
SELECT x.id, x.titolo, x.ente, x.stato, x.scadenza, x.unito_a, x.situazione, x.fase,
       CASE
           WHEN x.situazione = 'unito' THEN 'doppione: unito al bando n. ' || x.unito_a
           WHEN x.situazione IN ('per_non_profit', 'fuori_target') THEN
               CASE WHEN x.fase = 'destinatari_da_determinare' THEN 'destinatari da determinare'
                    WHEN x.preliminare->>'agevolazione' = 'no' THEN 'non e'' un''agevolazione'
                    ELSE 'destinatari: ' || coalesce(nullif(x.destinatari_testo, ''), 'non indicati') END
               || coalesce('. ' || nullif(x.preliminare->>'motivo', ''), '')
           WHEN x.situazione IN ('scartato_chiuso', 'scartato_altro')
                OR x.fase = 'seconda_lettura_in_coda' THEN x.preliminare->>'motivo'
           WHEN x.situazione = 'chiuso_con_scheda' THEN
               CASE WHEN x.chiuso_il IS NOT NULL THEN 'chiuso il ' || to_char(x.chiuso_il, 'DD/MM/YYYY')
                    WHEN x.scadenza IS NOT NULL THEN 'scaduto il ' || to_char(x.scadenza, 'DD/MM/YYYY')
                    ELSE 'chiuso' END
               || coalesce(': ' || CASE WHEN x.ricontrollo->>'stato' IN ('chiuso', 'esaurito') THEN x.ricontrollo->>'motivo' END, '')
           WHEN x.situazione = 'nascosto_per_errori' THEN
               (SELECT string_agg(g, '; ') FROM jsonb_array_elements_text(x.controllo->'gravi') g)
           WHEN x.fase = 'documento_non_valido' THEN
               'documento non valido (' || coalesce(x.verifica_documento->>'problema', 'non indicato') || ')'
               || coalesce(': ' || nullif(x.verifica_documento->>'motivo', ''), '')
           WHEN x.fase = 'documento_da_verificare' THEN 'nessuno ha ancora verificato che il documento sia il testo ufficiale giusto'
           WHEN x.fase = 'secondo_controllo_da_fare' THEN 'scheda da controllare con il testo del bando (secondo controllo)'
           WHEN x.fase = 'errori_da_correggere' THEN
               coalesce(x.secondo_controllo->>'gravi', '') || ' errori gravi trovati dal secondo controllo, da correggere'
           WHEN x.situazione = 'proponibile' THEN x.da_aggiornare
           WHEN x.fase = 'scheda_solo_sintesi' THEN 'scheda fatta su una sintesi: manca il testo ufficiale del bando'
           WHEN x.fase = 'scheda_nessun_documento' THEN 'scheda fatta senza documenti del bando'
           WHEN x.situazione = 'in_disparte' THEN x.documentazione_motivo
           WHEN x.fase = 'pagina_non_trovata' THEN x.pagina_motivo
           WHEN x.fase = 'scheda_in_coda' THEN 'controllo preliminare superato: ' || coalesce(x.preliminare->>'motivo', '')
           WHEN x.fase = 'preliminare_in_coda' THEN x.documentazione_motivo
       END AS motivo,
       CASE
           WHEN x.situazione IN ('per_non_profit', 'fuori_target', 'scartato_chiuso', 'scartato_altro')
                OR x.fase = 'seconda_lettura_in_coda' THEN
               coalesce(x.preliminare->>'deciso_da',
                        CASE WHEN x.preliminare->>'motivo' LIKE 'Ricontrollo%'
                                  OR x.preliminare->>'compilato_da' LIKE 'claude-code%' THEN 'sessione' ELSE 'ia' END)
           WHEN x.situazione = 'chiuso_con_scheda' THEN
               CASE WHEN x.ricontrollo->>'stato' IN ('chiuso', 'esaurito') THEN 'sessione' ELSE 'regole' END
           WHEN x.situazione = 'nascosto_per_errori' THEN 'regole'
           WHEN x.fase = 'documento_non_valido' THEN coalesce(x.verifica_documento->>'deciso_da', 'regole')
           WHEN x.fase IN ('documento_da_verificare', 'secondo_controllo_da_fare', 'errori_da_correggere') THEN 'regole'
           WHEN x.situazione IN ('proponibile', 'in_disparte') AND x.completezza IS NOT NULL THEN
               CASE WHEN x.modello_scheda LIKE 'claude-code%' THEN 'sessione' WHEN x.modello_scheda IS NOT NULL THEN 'ia' END
           WHEN x.situazione = 'in_disparte' THEN 'regole'
       END AS deciso_da,
       CASE
           WHEN x.situazione = 'unito' THEN
               (SELECT max(v.salvata_il) FROM bandi_versioni v
                 WHERE v.bando_id = x.id AND (v.dati->>'unito_a') IS DISTINCT FROM x.unito_a::text)
           WHEN x.situazione IN ('per_non_profit', 'fuori_target', 'scartato_chiuso', 'scartato_altro')
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
    SELECT y.*,
           CASE
               WHEN y.unito_a IS NOT NULL THEN 'unito'
               WHEN y.non_profit THEN 'per_non_profit'
               WHEN y.preliminare->>'per_imprese' = 'no' THEN 'fuori_target'
               WHEN y.completezza IS NOT NULL AND y.stato = 'chiuso' THEN 'chiuso_con_scheda'
               WHEN y.completezza = 'bando_ufficiale' AND y.gravi THEN 'nascosto_per_errori'
               WHEN y.completezza = 'bando_ufficiale' AND y.procedura = 'da_recuperare' THEN 'in_disparte'
               WHEN y.completezza = 'bando_ufficiale' AND y.procedura <> 'pronto' THEN 'in_lavorazione'
               WHEN y.completezza = 'bando_ufficiale' THEN 'proponibile'
               WHEN y.completezza IS NOT NULL THEN 'in_disparte'
               WHEN y.preliminare->>'seconda_lettura' = 'da_fare' THEN 'in_lavorazione'
               WHEN y.preliminare->>'edizione_in_corso' = 'no' OR y.preliminare->>'stato' = 'chiuso' THEN 'scartato_chiuso'
               WHEN y.preliminare->>'testo_bando' = 'no' THEN 'scartato_altro'
               WHEN y.documentazione IN ('sintesi', 'nessuno') THEN 'in_disparte'
               ELSE 'in_lavorazione'
           END AS situazione,
           CASE
               WHEN y.unito_a IS NOT NULL THEN 'unito'
               -- Per il non profit: dove sta il bando (la scheda si fa dopo quelle per le imprese).
               WHEN y.non_profit THEN
                   CASE WHEN y.stato = 'chiuso' OR (y.completezza IS NULL AND (y.preliminare->>'edizione_in_corso' = 'no'
                                                                                OR y.preliminare->>'stato' = 'chiuso'))
                             THEN 'non_profit_chiuso'
                        WHEN y.completezza = 'bando_ufficiale' THEN 'non_profit_con_scheda'
                        WHEN y.completezza IS NOT NULL THEN 'non_profit_scheda_su_sintesi'
                        WHEN y.preliminare->>'testo_bando' = 'no' OR y.documentazione IN ('sintesi', 'nessuno')
                             THEN 'non_profit_senza_testo'
                        ELSE 'scheda_non_profit_in_coda' END
               WHEN y.preliminare->>'per_imprese' = 'no' THEN
                   CASE WHEN jsonb_typeof(y.preliminare->'destinatari') IS DISTINCT FROM 'array'
                             OR y.preliminare->'destinatari' ? 'da_determinare' THEN 'destinatari_da_determinare'
                        WHEN y.preliminare->>'agevolazione' = 'no' THEN 'non_agevolazione'
                        WHEN y.completezza IS NOT NULL THEN 'dopo_la_scheda'
                        ELSE 'prima_della_scheda' END
               WHEN y.completezza IS NOT NULL AND y.stato = 'chiuso' THEN
                   CASE WHEN y.chiuso_il IS NOT NULL THEN 'chiusura_anticipata' ELSE 'scaduto' END
               WHEN y.completezza = 'bando_ufficiale' AND y.gravi THEN 'problemi_gravi'
               WHEN y.completezza = 'bando_ufficiale' AND y.procedura = 'da_recuperare' THEN 'documento_non_valido'
               WHEN y.completezza = 'bando_ufficiale' AND y.procedura <> 'pronto' THEN y.procedura
               WHEN y.completezza = 'bando_ufficiale' THEN
                   CASE WHEN y.da_aggiornare IS NOT NULL THEN 'scheda_da_aggiornare' ELSE 'scheda_pronta' END
               WHEN y.completezza IS NOT NULL THEN 'scheda_' || y.completezza
               WHEN y.preliminare->>'seconda_lettura' = 'da_fare' THEN 'seconda_lettura_in_coda'
               WHEN y.preliminare->>'edizione_in_corso' = 'no' THEN 'edizione_passata'
               WHEN y.preliminare->>'stato' = 'chiuso' THEN 'chiuso'
               WHEN y.preliminare->>'testo_bando' = 'no' THEN 'senza_testo_del_bando'
               WHEN y.documentazione IN ('sintesi', 'nessuno') THEN 'senza_scheda_' || y.documentazione
               WHEN y.pagina_stato IS NULL THEN 'pagina_da_cercare'
               WHEN y.pagina_stato = 'non_trovata' THEN 'pagina_non_trovata'
               WHEN y.allegati_cercati_il IS NULL THEN 'documenti_da_scaricare'
               WHEN y.documentazione IS NULL THEN 'filtro_da_fare'
               WHEN y.preliminare IS NULL THEN 'preliminare_in_coda'
               ELSE 'scheda_in_coda'
           END AS fase
    FROM (
        SELECT b.id, b.titolo, b.ente, b.stato, b.scadenza, b.chiuso_il, b.unito_a, b.completezza, b.controllo, b.preliminare,
               b.documentazione_motivo, b.pagina_motivo, b.da_aggiornare, b.scheda_il, b.stato_calcolato_il, b.aggiornato_il,
               b.pagina_cercata_il, b.allegati_cercati_il, b.dati->>'modello' AS modello_scheda,
               b.dati->'ricontrollo_stato' AS ricontrollo, b.documentazione, b.pagina_stato, g.gravi,
               b.verifica_documento, b.secondo_controllo, p.procedura,
               -- solo non profit: non per imprese, ma tra i destinatari c'e' il non profit ed e' un'agevolazione
               -- (come ia.solo_non_profit)
               (b.preliminare->>'per_imprese' = 'no' AND coalesce(b.preliminare->>'agevolazione', '') <> 'no'
                AND jsonb_typeof(b.preliminare->'destinatari') = 'array'
                AND b.preliminare->'destinatari' ? 'non_profit') IS TRUE AS non_profit,
               CASE WHEN jsonb_typeof(b.preliminare->'destinatari') = 'array' THEN
                   (SELECT string_agg(replace(d, '_', ' '), ', ') FROM jsonb_array_elements_text(b.preliminare->'destinatari') d)
               END AS destinatari_testo
        FROM bandi b
        -- problemi gravi del controllo delle schede (app/schede/controlli.py), come catalogo.proponibile
        CROSS JOIN LATERAL (SELECT CASE WHEN jsonb_typeof(b.controllo->'gravi') = 'array'
                                        THEN jsonb_array_length(b.controllo->'gravi') > 0 ELSE false END AS gravi) g
        -- a che punto e' della procedura nuova (uguale ad app/catena/procedura.py, ESITO_SQL)
        CROSS JOIN LATERAL (SELECT CASE
                WHEN coalesce(b.verifica_documento->>'verificato', '') NOT IN ('si', 'no') THEN 'documento_da_verificare'
                WHEN b.verifica_documento->>'verificato' = 'no' THEN 'da_recuperare'
                WHEN b.secondo_controllo->>'esito' IS NULL OR b.secondo_controllo->>'fatto_il' IS NULL THEN 'secondo_controllo_da_fare'
                WHEN b.scheda_il IS NOT NULL AND (b.secondo_controllo->>'fatto_il')::timestamptz < b.scheda_il
                     THEN 'secondo_controllo_da_fare'
                WHEN b.secondo_controllo->>'esito' = 'grave'
                     AND coalesce(b.secondo_controllo->>'correzioni_applicate', 'false') <> 'true' THEN 'errori_da_correggere'
                ELSE 'pronto' END AS procedura) p
    ) y
) x;
