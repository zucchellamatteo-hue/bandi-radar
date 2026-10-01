"""Fotografa pagine della plancia di prova. Uso: foto.py nome=/percorso ... (larghezza 1300)."""
import sys

from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    browser = p.chromium.launch()
    pagina = browser.new_page(viewport={"width": 1300, "height": 900}, http_credentials={"username": "prova", "password": "prova"})
    errori = []
    pagina.on("pageerror", lambda e: errori.append(str(e)))
    for arg in sys.argv[1:]:
        nome, percorso = arg.split("=", 1)
        pagina.goto("http://br-prova:8000" + percorso)
        pagina.wait_for_timeout(2500)
        pagina.screenshot(path=f"/out/foto_{nome}.png", full_page=True)
        print(nome, "ok", pagina.title())
    print("errori:", errori)
    browser.close()
