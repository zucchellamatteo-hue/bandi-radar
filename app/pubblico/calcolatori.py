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

# Funzioni comuni a tutti i calcolatori (una volta per pagina): formato euro e lettura dei campi numerici.
_COMUNE = """<script>
window.bqEuro = window.bqEuro || new Intl.NumberFormat("it-IT", {style: "currency", currency: "EUR", maximumFractionDigits: 0});
window.bqNum = window.bqNum || function (box, sel) { var v = Number(box.querySelector(sel).value); return isFinite(v) && v > 0 ? v : 0; };
</script>"""

_ALIQUOTE = """<select id="ALIQ">
<option value="0.24">Srl, spa, cooperativa (IRES 24%)</option>
<option value="0.23">Ditta o soci con reddito fino a 28.000 euro (IRPEF 23%)</option>
<option value="0.33">Ditta o soci con reddito tra 28.000 e 50.000 euro (IRPEF 33%)</option>
<option value="0.43">Ditta o soci con reddito oltre 50.000 euro (IRPEF 43%)</option>
</select>"""

# Iperammortamento 2026 (L. 199/2025 c. 427; DM 7/5/2026 art. 4 c. 2): maggiorazione a scaglioni sugli investimenti
# completati nell'anno: 180% fino a 2,5 milioni, 100% fino a 10, 50% fino a 20, oltre nulla. Risparmio = x aliquota.
_IPER = """<div class="calcolatore" id="calcolatore-iper">
<h3>Calcola l'iperammortamento 2026</h3>
<label for="ci-importo">Investimenti in beni 4.0 completati nell'anno (euro)</label>
<input id="ci-importo" type="number" inputmode="numeric" min="0" step="1000" value="100000">
<label for="ci-aliq">Chi investe</label>
""" + _ALIQUOTE.replace("ALIQ", "ci-aliq") + """
<table><tbody>
<tr><td>Maggiorazione (deduzione in più)</td><td class="cr" id="ci-magg">-</td></tr>
<tr><td>Imposte risparmiate in totale</td><td class="cr" id="ci-risp">-</td></tr>
<tr><td>In percentuale della spesa</td><td class="cr" id="ci-perc">-</td></tr>
</tbody></table>
<p class="cs-nota" aria-live="polite"></p>
<p class="piccolo">Scaglioni dell'anno: 180% fino a 2,5 milioni, 100% da 2,5 a 10 milioni, 50% da 10 a 20 milioni, oltre nulla.
Il risparmio arriva negli anni di ammortamento (o del leasing) e solo se c'è reddito tassabile; non vale per l'IRAP.
Se sugli stessi beni c'è un contributo (Sabatini, ZES, bando), la base si riduce di quell'importo.</p>
</div>
<script>
(function () {
  var box = document.getElementById("calcolatore-iper"); if (!box) return;
  function aggiorna() {
    var x = bqNum(box, "#ci-importo"), a = Number(box.querySelector("#ci-aliq").value);
    var m = 1.8 * Math.min(x, 2500000) + 1.0 * Math.max(0, Math.min(x, 10000000) - 2500000)
          + 0.5 * Math.max(0, Math.min(x, 20000000) - 10000000);
    box.querySelector("#ci-magg").textContent = bqEuro.format(m);
    box.querySelector("#ci-risp").textContent = bqEuro.format(m * a);
    box.querySelector("#ci-perc").textContent = x ? (m * a / x * 100).toFixed(1).replace(".", ",") + "%" : "-";
    box.querySelector(".cs-nota").textContent = x > 20000000 ? "Oltre 20 milioni nell'anno la parte in più non ha maggiorazione."
      : x > 2500000 ? "Sopra 2,5 milioni la maggiorazione scende: se possibile, valuta di completare una parte l'anno dopo." : "";
  }
  box.querySelectorAll("input,select").forEach(function (e) { e.addEventListener("input", aggiorna); });
  aggiorna();
})();
</script>"""

# Credito ricerca e sviluppo 2026 (L. 160/2019 c. 200-205): 10% della base; giovani ricercatori e contratti con
# universita', enti di ricerca e startup innovative contano al 150%; meno i contributi sulle stesse spese; massimo
# 5 milioni l'anno; si usa in tre quote annuali dall'anno dopo.
_RS = """<div class="calcolatore" id="calcolatore-rs">
<h3>Calcola il credito ricerca e sviluppo 2026</h3>
<label for="cr-ord">Spese di ricerca e sviluppo ordinarie (personale, strumenti, consulenze, materiali, contratti con altre imprese)</label>
<input id="cr-ord" type="number" inputmode="numeric" min="0" step="1000" value="100000">
<label for="cr-150">Spese che contano al 150% (giovani ricercatori; contratti con università, enti di ricerca, startup innovative)</label>
<input id="cr-150" type="number" inputmode="numeric" min="0" step="1000" value="0">
<label for="cr-contr">Contributi ricevuti per le stesse spese (es. bando regionale)</label>
<input id="cr-contr" type="number" inputmode="numeric" min="0" step="1000" value="0">
<table><tbody>
<tr><td>Base di calcolo</td><td class="cr" id="cr-base">-</td></tr>
<tr><td>Credito d'imposta (10%)</td><td class="cr" id="cr-cred">-</td></tr>
<tr><td>Quota annua in F24 (per 3 anni)</td><td class="cr" id="cr-quota">-</td></tr>
</tbody></table>
<p class="cs-nota" aria-live="polite"></p>
<p class="piccolo">Strumenti e materiali entrano al massimo per il 30% delle spese di personale, le consulenze per il 20%.
Solo vera ricerca e sviluppo (Manuale di Frascati). Le imprese non obbligate alla revisione aggiungono il costo della
certificazione contabile fino a 5.000 euro. Il credito non è tassato.</p>
</div>
<script>
(function () {
  var box = document.getElementById("calcolatore-rs"); if (!box) return;
  function aggiorna() {
    var base = Math.max(0, bqNum(box, "#cr-ord") + 1.5 * bqNum(box, "#cr-150") - bqNum(box, "#cr-contr"));
    var cred = Math.min(0.10 * base, 5000000);
    box.querySelector("#cr-base").textContent = bqEuro.format(base);
    box.querySelector("#cr-cred").textContent = bqEuro.format(cred);
    box.querySelector("#cr-quota").textContent = bqEuro.format(cred / 3);
    box.querySelector(".cs-nota").textContent = 0.10 * base > 5000000 ? "Raggiunto il massimo di 5 milioni l'anno." : "";
  }
  box.querySelectorAll("input").forEach(function (e) { e.addEventListener("input", aggiorna); });
  aggiorna();
})();
</script>"""

# Credito ZES unica 2026 (istruzioni AdE, Carta aiuti 2022-2027): costo ammesso da 200.000 euro a 100 milioni;
# intensita' per zona e dimensione; oltre 50 milioni intensita' delle grandi con importo corretto R x (A + 0,5 x B);
# meno gli altri aiuti di Stato sugli stessi beni (art. 16 c. 5; 09/10, richiesta di Matteo), poi la percentuale di
# riparto (2025: 75%; 2026 non ancora nota).
_ZES = """<div class="calcolatore" id="calcolatore-zes">
<h3>Calcola il credito d'imposta ZES unica 2026</h3>
<label for="cz-importo">Costo ammesso del progetto (euro, da 200.000 a 100 milioni)</label>
<input id="cz-importo" type="number" inputmode="numeric" min="200000" max="100000000" step="10000" value="1000000">
<label for="cz-zona">Dove si investe</label>
<select id="cz-zona">
<option value="60,50,40">Campania, Puglia (esclusa prov. di Taranto), Calabria, Sicilia</option>
<option value="50,40,30">Basilicata, Molise, Sardegna (escluso Sulcis-Iglesiente)</option>
<option value="70,60,50">Provincia di Taranto</option>
<option value="60,50,40">Sulcis-Iglesiente (23 comuni)</option>
<option value="35,25,15">Comuni ammessi di Abruzzo, Marche, Umbria</option>
</select>
<label for="cz-dim">Dimensione dell'impresa</label>
<select id="cz-dim"><option value="0">Micro o piccola</option><option value="1">Media</option><option value="2">Grande</option></select>
<label for="cz-altri">Altri aiuti di Stato sugli stessi beni (es. bando regionale a fondo perduto, euro)</label>
<input id="cz-altri" type="number" inputmode="numeric" min="0" step="1000" value="0">
<label for="cz-rip">Percentuale di riparto (2025: 75%; quella 2026 si saprà a fine gennaio 2027)</label>
<input id="cz-rip" type="number" min="1" max="100" step="1" value="75">
<table><tbody>
<tr><td>Intensità applicata</td><td class="cr" id="cz-int">-</td></tr>
<tr><td>Credito teorico (meno gli altri aiuti)</td><td class="cr" id="cz-teo">-</td></tr>
<tr><td>Credito con il riparto indicato</td><td class="cr" id="cz-eff">-</td></tr>
</tbody></table>
<p class="cs-nota" aria-live="polite"></p>
<p class="piccolo">Gli immobili contano al massimo quanto i beni strumentali. Dal credito si tolgono gli altri aiuti di
Stato sugli stessi beni. Nelle zone di Abruzzo, Marche e Umbria le grandi imprese solo per una nuova attività.
Esclusi produzione agricola primaria, pesca, trasporti, energia, siderurgia, banche e assicurazioni.</p>
</div>
<script>
(function () {
  var box = document.getElementById("calcolatore-zes"); if (!box) return;
  function aggiorna() {
    var x = bqNum(box, "#cz-importo"), z = box.querySelector("#cz-zona").value.split(",").map(Number);
    var d = Number(box.querySelector("#cz-dim").value), rip = Math.min(100, bqNum(box, "#cz-rip")) / 100;
    var nota = box.querySelector(".cs-nota"), teo = 0, r;
    if (x < 200000) { nota.textContent = "Sotto 200.000 euro di progetto il credito ZES non spetta."; }
    else {
      var y = Math.min(x, 100000000);
      if (y > 50000000) { r = z[2]; teo = r / 100 * (Math.min(y, 55000000) + 0.5 * Math.max(0, y - 55000000)); }
      else { r = z[d]; teo = r / 100 * y; }
      var altri = bqNum(box, "#cz-altri");
      nota.textContent = x > 100000000 ? "Oltre 100 milioni il costo in più non conta."
        : y > 50000000 ? "Oltre 50 milioni vale l'intensità delle grandi imprese con l'importo corretto."
        : altri >= teo ? "Gli altri aiuti arrivano già all'intensità massima della zona: il credito ZES è zero."
        : altri ? "Gli altri aiuti sugli stessi beni si tolgono prima del riparto." : "";
      teo = Math.max(0, teo - altri);
    }
    box.querySelector("#cz-int").textContent = r ? r + "%" : "-";
    box.querySelector("#cz-teo").textContent = teo ? bqEuro.format(teo) : "-";
    box.querySelector("#cz-eff").textContent = teo ? bqEuro.format(teo * rip) : "-";
  }
  box.querySelectorAll("input,select").forEach(function (e) { e.addEventListener("input", aggiorna); });
  aggiorna();
})();
</script>"""

# Maxi-deduzione nuovi assunti (D.Lgs. 216/2023 art. 4; circ. AdE 1/E/2025): base = minore tra costo dei nuovi assunti
# a tempo indeterminato e aumento del costo complessivo del personale; maggiorazione 20% (30% categorie allegato 1).
_MAXI = """<div class="calcolatore" id="calcolatore-maxi">
<h3>Calcola la maxi-deduzione dei nuovi assunti</h3>
<label for="cm-costo">Costo dei nuovi assunti a tempo indeterminato nell'anno (solo i mesi lavorati)</label>
<input id="cm-costo" type="number" inputmode="numeric" min="0" step="1000" value="35000">
<label for="cm-aum">Aumento del costo complessivo del personale rispetto all'anno prima</label>
<input id="cm-aum" type="number" inputmode="numeric" min="0" step="1000" value="35000">
<label for="cm-cat">Categoria dei nuovi assunti</label>
<select id="cm-cat"><option value="0.20">Qualunque lavoratore (120%)</option>
<option value="0.30">Categorie al 130% (es. sede di lavoro al Sud, disabili, molto svantaggiati, donne con 2 figli)</option></select>
<label for="cm-aliq">Chi assume</label>
""" + _ALIQUOTE.replace("ALIQ", "cm-aliq") + """
<table><tbody>
<tr><td>Base (il minore dei due importi)</td><td class="cr" id="cm-base">-</td></tr>
<tr><td>Deduzione in più</td><td class="cr" id="cm-magg">-</td></tr>
<tr><td>Imposte risparmiate</td><td class="cr" id="cm-risp">-</td></tr>
</tbody></table>
<p class="cs-nota" aria-live="polite"></p>
<p class="piccolo">Serve un aumento sia dei dipendenti a tempo indeterminato sia del totale dei dipendenti rispetto all'anno
prima. Esclusi forfettari e imprese attive da meno di 365 giorni. Non riduce l'IRAP; il vantaggio arriva con il saldo
delle imposte dell'anno dopo.</p>
</div>
<script>
(function () {
  var box = document.getElementById("calcolatore-maxi"); if (!box) return;
  function aggiorna() {
    var c = bqNum(box, "#cm-costo"), au = bqNum(box, "#cm-aum"), base = Math.min(c, au);
    var m = base * Number(box.querySelector("#cm-cat").value), a = Number(box.querySelector("#cm-aliq").value);
    box.querySelector("#cm-base").textContent = bqEuro.format(base);
    box.querySelector("#cm-magg").textContent = bqEuro.format(m);
    box.querySelector("#cm-risp").textContent = bqEuro.format(m * a);
    box.querySelector(".cs-nota").textContent = au < c ? "L'aumento complessivo è minore del costo dei nuovi assunti: conta quello." : "";
  }
  box.querySelectorAll("input,select").forEach(function (e) { e.addEventListener("input", aggiorna); });
  aggiorna();
})();
</script>"""

# Art Bonus (DL 83/2014 art. 1): credito 65% della donazione; per le imprese al massimo il 5 per mille dei ricavi;
# tre quote annuali uguali in F24 dall'anno dopo.
_ARTBONUS = """<div class="calcolatore" id="calcolatore-artbonus">
<h3>Calcola l'Art Bonus per la tua impresa</h3>
<label for="ca-don">Donazione (euro)</label>
<input id="ca-don" type="number" inputmode="numeric" min="0" step="100" value="5000">
<label for="ca-ric">Ricavi annui dell'impresa (euro)</label>
<input id="ca-ric" type="number" inputmode="numeric" min="0" step="10000" value="1000000">
<table><tbody>
<tr><td>Credito d'imposta</td><td class="cr" id="ca-cred">-</td></tr>
<tr><td>Quota annua in F24 (per 3 anni)</td><td class="cr" id="ca-quota">-</td></tr>
<tr><td>Costo vero della donazione</td><td class="cr" id="ca-costo">-</td></tr>
<tr><td>Donazione massima con credito pieno</td><td class="cr" id="ca-max">-</td></tr>
</tbody></table>
<p class="cs-nota" aria-live="polite"></p>
<p class="piccolo">Credito del 65% nel limite del 5 per mille dei ricavi dell'anno della donazione. Solo erogazioni in denaro
tracciabili a favore dei beneficiari ammessi (portale artbonus.gov.it). Il credito non è tassato.</p>
</div>
<script>
(function () {
  var box = document.getElementById("calcolatore-artbonus"); if (!box) return;
  function aggiorna() {
    var d = bqNum(box, "#ca-don"), lim = 0.005 * bqNum(box, "#ca-ric"), cred = Math.min(0.65 * d, lim);
    box.querySelector("#ca-cred").textContent = bqEuro.format(cred);
    box.querySelector("#ca-quota").textContent = bqEuro.format(cred / 3);
    box.querySelector("#ca-costo").textContent = bqEuro.format(d - cred);
    box.querySelector("#ca-max").textContent = bqEuro.format(lim / 0.65);
    box.querySelector(".cs-nota").textContent = 0.65 * d > lim ? "La donazione supera il limite: la parte in più non dà credito." : "";
  }
  box.querySelectorAll("input").forEach(function (e) { e.addEventListener("input", aggiorna); });
  aggiorna();
})();
</script>"""

# Conto Termico 3.0 per le imprese (DM 7/8/2025 art. 27; Regole Applicative GSE 19/12/2025 par. 4.2.1, 4.6, 4.7):
# Titolo II 25% (30% multi-intervento = due o piu' interventi del Titolo II sullo stesso edificio) + 20 piccole / 10
# medie + 15 zona 107.3.a o 5 zona 107.3.c + 15 se l'energia primaria scende di almeno il 40%; tetto 65% PMI, 60%
# grandi. Titolo III 45% + 20 piccole / 10 medie (tetti 65/55/45). Punti percentuali (tabella 11 delle Regole).
# Pagamento: fino a 15.000 euro rata unica; oltre, 2 anni per pompe di calore, ibridi e scaldacqua fino a 35 kW,
# 5 anni per il Titolo II e gli impianti piu' grandi (con piu' interventi la durata piu' lunga). Trattenuta GSE 1%,
# al massimo 250 euro piu' IVA, sulla prima rata.
_CONTO_TERMICO = """<div class="calcolatore" id="calcolatore-ct">
<h3>Calcola il Conto Termico 3.0 della tua impresa</h3>
<label for="ct-dim">Dimensione dell'impresa</label>
<select id="ct-dim"><option value="20">Micro o piccola</option><option value="10">Media</option><option value="0">Grande</option></select>
<label for="ct-t3">Spesa per impianti a fonti rinnovabili (Titolo III: pompe di calore, ibridi, biomassa, solare termico), euro IVA esclusa</label>
<input id="ct-t3" type="number" inputmode="numeric" min="0" step="1000" value="30000">
<label class="spunta"><input id="ct-piccolo" type="checkbox" checked> Pompa di calore, sistema ibrido o scaldacqua fino a 35 kW</label>
<label for="ct-t2">Spesa per efficienza dell'edificio (Titolo II: cappotto, infissi, schermature, LED, building automation), euro IVA esclusa</label>
<input id="ct-t2" type="number" inputmode="numeric" min="0" step="1000" value="0">
<label class="spunta"><input id="ct-multi" type="checkbox"> Due o più interventi del Titolo II sullo stesso edificio (multi-intervento)</label>
<label for="ct-zona">Zona dell'edificio (aiuti a finalità regionale)</label>
<select id="ct-zona"><option value="0">Fuori dalle zone assistite</option><option value="5">Zona assistita art. 107.3.c</option>
<option value="15">Zona assistita art. 107.3.a (Mezzogiorno)</option></select>
<label class="spunta"><input id="ct-40" type="checkbox"> Il fabbisogno di energia primaria scende di almeno il 40% (APE prima e dopo)</label>
<table><tbody>
<tr><td>Percentuale Titolo III</td><td class="cr" id="ct-p3">-</td></tr>
<tr><td>Percentuale Titolo II</td><td class="cr" id="ct-p2">-</td></tr>
<tr><td>Contributo stimato</td><td class="cr" id="ct-tot">-</td></tr>
<tr><td>Come arriva</td><td class="cr" id="ct-rate">-</td></tr>
</tbody></table>
<p class="cs-nota" aria-live="polite"></p>
<p class="piccolo">Stima sulle percentuali del decreto. Il GSE calcola il contributo sui costi ammissibili entro i costi
massimi unitari (euro al m², euro al kW) e può riconoscere meno. Dalla prima rata trattiene l'1% (al massimo 250 euro più
IVA). Per le imprese la richiesta preliminare va inviata prima del primo ordine.</p>
</div>
<script>
(function () {
  var box = document.getElementById("calcolatore-ct"); if (!box) return;
  function v(sel) { return box.querySelector(sel); }
  function perc(x) { return x + "%"; }
  function aggiorna() {
    var dim = Number(v("#ct-dim").value), t3 = bqNum(box, "#ct-t3"), t2 = bqNum(box, "#ct-t2");
    var p3 = Math.min(45 + dim, dim === 20 ? 65 : dim === 10 ? 55 : 45);
    var p2 = Math.min((v("#ct-multi").checked ? 30 : 25) + dim + Number(v("#ct-zona").value) + (v("#ct-40").checked ? 15 : 0),
                      dim > 0 ? 65 : 60);
    var tot = t3 * p3 / 100 + t2 * p2 / 100, anni = 1;
    if (tot > 15000) { anni = (t2 > 0 || (t3 > 0 && !v("#ct-piccolo").checked)) ? 5 : 2; }
    v("#ct-p3").textContent = t3 ? perc(p3) : "-";
    v("#ct-p2").textContent = t2 ? perc(p2) : "-";
    v("#ct-tot").textContent = bqEuro.format(tot);
    v("#ct-rate").textContent = !tot ? "-" : anni === 1 ? "rata unica" : anni + " rate annuali da " + bqEuro.format(tot / anni);
    v(".cs-nota").textContent = t2 ? (v("#ct-multi").checked
        ? "Multi-intervento: serve un risparmio di energia primaria di almeno il 20%, dimostrato con l'APE."
        : "Intervento singolo del Titolo II: serve un risparmio di energia primaria di almeno il 10%, dimostrato con l'APE.") : "";
  }
  box.querySelectorAll("input,select").forEach(function (e) { e.addEventListener("input", aggiorna); e.addEventListener("change", aggiorna); });
  aggiorna();
})();
</script>"""

CALCOLATORI = {"sabatini": _SABATINI, "iperammortamento": _IPER, "credito_rs": _RS, "zes": _ZES,
               "maxi_deduzione": _MAXI, "art_bonus": _ARTBONUS, "conto_termico": _CONTO_TERMICO}


def html(nome: str) -> str:
    """L'HTML del calcolatore; le funzioni comuni si aggiungono davanti (sono innocue se ripetute)."""
    return (_COMUNE + CALCOLATORI[nome]) if nome in CALCOLATORI else ""


def contributo_sabatini(finanziamento: float, tasso: float) -> float:
    """La stessa formula del calcolatore, per i test."""
    i = tasso / 2
    rata = finanziamento * i / (1 - (1 + i) ** -10)
    return 10 * rata - finanziamento


# Le stesse formule dei calcolatori, per i test.
def iperammortamento(investimento: float) -> float:
    x = investimento
    return 1.8 * min(x, 2_500_000) + max(0, min(x, 10_000_000) - 2_500_000) + 0.5 * max(0, min(x, 20_000_000) - 10_000_000)


def credito_rs(ordinarie: float, al_150: float = 0, contributi: float = 0) -> float:
    return min(0.10 * max(0, ordinarie + 1.5 * al_150 - contributi), 5_000_000)


def credito_zes(costo: float, intensita: tuple[int, int, int], dimensione: int, altri_aiuti: float = 0) -> float:
    """Credito teorico, prima del riparto, meno gli altri aiuti di Stato sugli stessi beni."""
    if costo < 200_000:
        return 0
    y = min(costo, 100_000_000)
    if y > 50_000_000:
        teorico = intensita[2] / 100 * (min(y, 55_000_000) + 0.5 * max(0, y - 55_000_000))
    else:
        teorico = intensita[dimensione] / 100 * y
    return max(0, teorico - altri_aiuti)


def art_bonus(donazione: float, ricavi: float) -> float:
    return min(0.65 * donazione, 0.005 * ricavi)


def conto_termico(dimensione: int, titolo3: float = 0, titolo2: float = 0, multi: bool = False, zona: int = 0,
                  risparmio_40: bool = False, pompa_piccola: bool = True) -> tuple[float, int]:
    """(contributo, anni di pagamento). `dimensione`: 20 piccola, 10 media, 0 grande (punti in piu')."""
    p3 = min(45 + dimensione, {20: 65, 10: 55}.get(dimensione, 45))
    p2 = min((30 if multi else 25) + dimensione + zona + (15 if risparmio_40 else 0), 65 if dimensione else 60)
    totale = titolo3 * p3 / 100 + titolo2 * p2 / 100
    if totale <= 15_000:
        return totale, 1
    return totale, 5 if titolo2 > 0 or (titolo3 > 0 and not pompa_piccola) else 2
