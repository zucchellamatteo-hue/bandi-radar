COPY (
SELECT a.id, a.fonte_id, a.titolo, a.url, coalesce(s.esito, '') AS esito, coalesce(a.bando_id::text, '') AS bando_id,
       coalesce(b.pagina_stato, '') AS pagina, coalesce(b.url, '') AS pagina_url, (b.dati IS NOT NULL) AS scheda,
       coalesce(b.stato, '') AS stato
FROM annunci a LEFT JOIN smistamenti s ON s.annuncio_id = a.id LEFT JOIN bandi b ON b.id = a.bando_id
) TO STDOUT WITH CSV HEADER
