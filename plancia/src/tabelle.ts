import { useEffect } from "react";

// Tabelle sul telefono (06/10). Sul computer le tabelle restano come sono; sotto i 700 px di larghezza il CSS
// (styles.css, "Telefono") le mostra come schede impilate. Qui si preparano, una volta per tutte le pagine:
// - le tabelle con l'intestazione ricevono la classe "impila" (ogni riga diventa una scheda) e ogni cella il nome della
//   sua colonna in data-etichetta, che il CSS scrive sopra il valore;
// - le tabelle "nome: valore" senza intestazione ma con il nome in <th> ricevono "impila-chiave" (una scheda sola, il
//   nome sopra il valore).
// Le tabelle con la classe "non-impilare" restano tabelle anche sul telefono (si scorrono di lato).
function prepara(tabella: HTMLTableElement) {
  if (tabella.classList.contains("non-impilare")) return;
  const intestazione = tabella.tHead?.rows[tabella.tHead.rows.length - 1];
  if (intestazione) {
    tabella.classList.add("impila");
    const nomi = Array.from(intestazione.cells).flatMap((c) => Array(c.colSpan || 1).fill((c.textContent || "").trim()) as string[]);
    for (const corpo of Array.from(tabella.tBodies)) {
      for (const riga of Array.from(corpo.rows)) {
        let colonna = 0;
        for (const cella of Array.from(riga.cells)) {
          const nome = cella.colSpan > 1 ? "" : nomi[colonna] || "";
          if (nome) { if (cella.getAttribute("data-etichetta") !== nome) cella.setAttribute("data-etichetta", nome); }
          else if (cella.hasAttribute("data-etichetta")) cella.removeAttribute("data-etichetta");
          colonna += cella.colSpan || 1;
        }
      }
    }
  } else if (tabella.querySelector(":scope > tbody > tr > th")) {
    tabella.classList.add("impila-chiave");
  }
}

export function useTabelleMobili() {
  useEffect(() => {
    let atteso = 0;
    const tutte = () => { atteso = 0; document.querySelectorAll("main table").forEach((t) => prepara(t as HTMLTableElement)); };
    const osservatore = new MutationObserver(() => { if (!atteso) atteso = requestAnimationFrame(tutte); });
    osservatore.observe(document.body, { childList: true, subtree: true, characterData: true });
    tutte();
    return () => { osservatore.disconnect(); if (atteso) cancelAnimationFrame(atteso); };
  }, []);
}
