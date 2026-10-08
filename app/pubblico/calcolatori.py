"""Calcolatori interattivi negli articoli del blog (09/10/2026, richiesta di Matteo per l'articolo sulla Nuova Sabatini).

Nel corpo Markdown dell'articolo una riga da sola `[[calcolatore:NOME]]` diventa il calcolatore NOME (articoli.in_html).
L'HTML e le poche righe di JavaScript stanno qui, scritti da noi: dal Markdown non passa mai codice. Un nome che non
esiste non mostra niente. Senza JavaScript resta visibile la tabella dell'articolo con le percentuali.
"""

from __future__ import annotations

# Nuova Sabatini: contributo = interessi di un finanziamento convenzionale di 5 anni a 10 rate semestrali costanti
# (formula del foglio di calcolo MIMIT, come app/misure/misure.yaml): i = tasso / 2; rata = F*i/(1-(1+i)^-10);
# contributo = 10*rata - F. Erogazione in un'unica soluzione fino a 200.000 euro di finanziamento, poi in quote annuali.
_SABATINI = """<div class="calcolatore" id="calcolatore-sabatini">
<h3>Calcola il contributo della Nuova Sabatini</h3>
<label for="cs-importo">Importo finanziato (euro, da 20.000 a 4.000.000)</label>
<input id="cs-importo" type="number" inputmode="numeric" min="20000" max="4000000" step="1000" value="100000">
<table><thead><tr><th>Linea</th><th>Tasso</th><th>Contributo stimato</th></tr></thead><tbody>
<tr><td>Ordinaria</td><td>2,75%</td><td data-tasso="0.0275">-</td></tr>
<tr><td>4.0 e green (e Capitalizzazione per le medie)</td><td>3,575%</td><td data-tasso="0.03575">-</td></tr>
<tr><td>Capitalizzazione, micro e piccole</td><td>5%</td><td data-tasso="0.05">-</td></tr>
</tbody></table>
<p class="cs-nota" aria-live="polite"></p>
<p class="piccolo">Stima con la formula del foglio di calcolo del MIMIT (5 anni, rate semestrali costanti). Il contributo
ufficiale lo calcola il Ministero sul finanziamento effettivo e può essere ridotto se si superano i limiti di cumulo.</p>
</div>
<script>
(function () {
  var box = document.getElementById("calcolatore-sabatini");
  if (!box) return;
  var campo = box.querySelector("#cs-importo"), nota = box.querySelector(".cs-nota");
  var euro = new Intl.NumberFormat("it-IT", {style: "currency", currency: "EUR", maximumFractionDigits: 0});
  function contributo(f, tasso) {
    var i = tasso / 2, rata = f * i / (1 - Math.pow(1 + i, -10));
    return 10 * rata - f;
  }
  function aggiorna() {
    var f = Number(campo.value);
    var valido = f >= 20000 && f <= 4000000;
    box.querySelectorAll("td[data-tasso]").forEach(function (td) {
      td.textContent = valido ? euro.format(contributo(f, Number(td.dataset.tasso))) : "-";
    });
    nota.textContent = !valido ? "Il finanziamento deve essere tra 20.000 e 4.000.000 di euro."
      : f <= 200000 ? "Fino a 200.000 euro di finanziamento il contributo arriva in un'unica soluzione."
      : "Sopra 200.000 euro di finanziamento il contributo arriva in quote annuali.";
  }
  campo.addEventListener("input", aggiorna);
  aggiorna();
})();
</script>"""

CALCOLATORI = {"sabatini": _SABATINI}


def html(nome: str) -> str:
    return CALCOLATORI.get(nome, "")


def contributo_sabatini(finanziamento: float, tasso: float) -> float:
    """La stessa formula del calcolatore, per i test."""
    i = tasso / 2
    rata = finanziamento * i / (1 - (1 + i) ** -10)
    return 10 * rata - finanziamento
