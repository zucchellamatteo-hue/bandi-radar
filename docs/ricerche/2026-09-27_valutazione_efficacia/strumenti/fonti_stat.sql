COPY (
SELECT f.id, f.tipo, f.modalita, coalesce(f.piattaforma, '') AS piattaforma, f.territorio, coalesce(f.url, '') AS url,
       count(a.id) AS annunci,
       count(a.id) FILTER (WHERE s.esito = 'rilevante') AS rilevanti,
       count(a.id) FILTER (WHERE s.esito = 'da_rivedere') AS da_rivedere,
       count(DISTINCT a.bando_id) AS bandi
FROM fonti f LEFT JOIN annunci a ON a.fonte_id = f.id LEFT JOIN smistamenti s ON s.annuncio_id = a.id
WHERE f.stato = 'attiva'
GROUP BY 1, 2, 3, 4, 5, 6
) TO STDOUT WITH CSV HEADER
