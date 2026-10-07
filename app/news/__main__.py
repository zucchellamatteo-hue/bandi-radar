"""Elenco delle news (per le sessioni di Claude Code): python -m app.news"""

import sys

from app import news
from app.db.connessione import connetti

if __name__ == "__main__":
    with connetti() as conn:
        for n in news.elenco(conn):
            periodo = f"dal {n['da']:%d/%m/%Y}" + (f" al {n['a']:%d/%m/%Y}" if n["a"] else "")
            print(f"#{n['id']} [{n['stato']}, {news.PUBBLICI[n['pubblico']]}, {periodo}] {n['titolo']}\n  {n['testo']}"
                  + (f"\n  link: {n['link']}" if n["link"] else ""))
    sys.exit(0)
