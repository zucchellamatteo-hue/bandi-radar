-- Bandi per il non profit (07/10/2026, decisione di Matteo): i bandi per associazioni ed enti senza scopo di lucro si
-- mappano comunque (potrebbe offrire servizi anche a loro), con priorita' piu' bassa delle imprese. Il controllo
-- preliminare ora dice i `destinatari` (imprese, non_profit, enti_pubblici, persone_fisiche, altri) e se c'e'
-- un'`agevolazione`; per_imprese si ricava da loro (app/schede/ia.py, completa_destinatari).
--
-- La vecchia voce "scartato_non_per_imprese" si divide in due:
--   per_non_profit  non per imprese ma aperto al non profit (associazioni, ETS, fondazioni, ASD/SSD, cooperative e
--                   imprese sociali, enti religiosi): scheda in coda con priorita' bassa, oppure gia' fatta
--   fuori_target    solo enti pubblici o persone fisiche, o non e' un'agevolazione (gara, concorso, elenco
--                   fornitori); i bandi decisi prima del 07/10 senza destinatari restano qui con la fase
--                   "destinatari_da_determinare" finche' non passa lo script di derivazione (o un nuovo preliminare)
-- Il resto della vista e' quello della migrazione 028. Ordine dei casi: vince la prima condizione vera.
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
    ) y
) x;
