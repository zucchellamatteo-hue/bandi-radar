#!/bin/bash
# Avanzamento della catena: pagine ufficiali e allegati, lavoratori attivi.
/tmp/claude-1000/sql.sh "SELECT coalesce(pagina_stato,'da cercare') pagina, (allegati_cercati_il IS NOT NULL) allegati, count(*) FROM bandi GROUP BY 1,2 ORDER BY 1,2"
echo "lavoratori in esecuzione: $(pgrep -f 'lavoratore.py' | wc -l)"
tail -q -n 1 /tmp/claude-1000/sp/log/*.log 2>/dev/null | cut -c1-150
