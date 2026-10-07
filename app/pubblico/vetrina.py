"""Bandi in vetrina: il riquadro che scorre a destra del primo schermo della presentazione (08/10/2026, Matteo).

Mostra da 1 a QUANTI voci (bandi o misure nazionali), una alla volta, con titolo, ente, agevolazione in una riga,
scadenza e l'invito "Scopri se fa per te" che porta alla registrazione (la scheda completa resta per gli abbonati).

Da dove vengono le voci:
1. app/pubblico/vetrina.yaml, scritto a mano da Matteo o dagli agenti (es. dalla ricerca settimanale dei bandi piu'
   discussi sul web), in ordine di priorita' e solo tra le date da/a;
2. se nel file ci sono meno di QUANTI voci valide, si aggiungono in automatico i bandi migliori: proponibili, aperti o
   in arrivo, con almeno due settimane davanti, a fondo perduto o voucher, adatti anche alle piccole imprese, con un
   importo da piccola-media impresa (IMPORTO_MIN-IMPORTO_MAX), prima i piu' recenti e poi i piu' generosi, un bando
   per ente.
Un bando compare solo se la sua situazione e' "proponibile" (scheda sul bando ufficiale, senza errori gravi, per
imprese) ed e' aperto o in arrivo e non scaduto; una misura solo se e' aperta. Le voci che non passano si saltano.

Il riquadro scorre da solo ogni GIRO_MS millisecondi, si ferma col mouse sopra, col dito o con la tastiera dentro,
ha un pulsante Pausa e i puntini per scegliere la voce; con "riduci movimento" attivo nel telefono o nel computer non
scorre da solo. Per i lettori di schermo le voci nascoste non esistono e il cambio si annuncia solo quando lo
chiede la persona (aria-live spento mentre scorre da solo). Niente librerie: poche righe di JavaScript.
"""

from __future__ import annotations

import logging
import time
from datetime import date, timedelta
from functools import lru_cache
from pathlib import Path

import yaml

log = logging.getLogger(__name__)
FILE = Path(__file__).resolve().parent / "vetrina.yaml"
QUANTI = 4
GIRO_MS = 5500
CACHE_SECONDI = 900
IMPORTO_MIN, IMPORTO_MAX = 10_000, 1_000_000      # importi da PMI: niente "fino a 30 milioni" in vetrina
RECENTI_GIORNI = 30
_cache: dict = {}

_COLONNE = """b.id, b.titolo, b.ente, b.stato, b.scadenza, b.data_apertura, b.tipi_agevolazione, b.contributo_massimo,
              b.percentuale, b.fondo_perduto_massimo, b.percentuale_fondo_perduto, b.finanziamento_massimo,
              b.territorio_regioni, b.vincoli->>'territorio' AS territorio, b.creato_il"""
# Le stesse condizioni per le voci del file e per quelle scelte in automatico (situazione: regola in CLAUDE.md).
_VALIDO = """s.situazione = 'proponibile' AND b.stato IN ('aperto', 'in_arrivo')
             AND (b.scadenza IS NULL OR b.scadenza >= current_date)"""


@lru_cache(maxsize=1)
def _da_file(percorso: str, modificato: float) -> tuple[dict, ...]:
    dati = yaml.safe_load(Path(percorso).read_text(encoding="utf-8")) or {}
    return tuple(v for v in dati.get("vetrina") or [] if isinstance(v, dict) and (v.get("bando") or v.get("misura")))


def _data(x) -> date | None:
    """Data dal file: AAAA-MM-GG (anche tra virgolette); se e' scritta male la voce vale come senza data."""
    if isinstance(x, date):
        return x
    try:
        return date.fromisoformat(str(x)) if x else None
    except ValueError:
        return None


def voci_file(oggi: date | None = None, percorso: Path | None = None) -> list[dict]:
    """Le voci del file valide oggi (tra da e a), in ordine di priorita'."""
    p = percorso or FILE
    if not p.is_file():
        return []
    oggi = oggi or date.today()
    voci = [dict(v) for v in _da_file(str(p), p.stat().st_mtime)
            if (_data(v.get("da")) or oggi) <= oggi <= (_data(v.get("a")) or oggi)]
    return sorted(voci, key=lambda v: v.get("priorita") if isinstance(v.get("priorita"), int) else 999)


def _perc(x) -> str:
    return f"{float(x):g}".replace(".", ",") + "%"


def riga_bando(b: dict) -> str:
    """L'agevolazione in una riga, es. "Fondo perduto 50%, fino a 20.000 €"."""
    from app.pubblico import _euro

    tipi = b.get("tipi_agevolazione") or []
    importo = b.get("fondo_perduto_massimo") or b.get("contributo_massimo")
    perc = b.get("percentuale_fondo_perduto") or b.get("percentuale")
    if "voucher" in tipi:
        nome = "Voucher a fondo perduto" if "fondo_perduto" in tipi else "Voucher"
    elif "fondo_perduto" in tipi:
        nome = "Fondo perduto"
    elif "finanziamento_agevolato" in tipi:
        nome, importo, perc = "Finanziamento agevolato", b.get("finanziamento_massimo") or b.get("contributo_massimo"), None
    elif "credito_imposta" in tipi:
        nome = "Credito d'imposta"
    elif "garanzia" in tipi:
        nome = "Garanzia"
    else:
        nome = "Contributo"
    parti = [nome + (f" {_perc(perc)}" if perc else "")]
    if importo:
        parti.append(f"fino a {_euro(importo)}")
    return ", ".join(parti)


def _quando_bando(b: dict, oggi: date) -> str:
    scade = f"scade il {b['scadenza']:%d/%m/%Y}" if b.get("scadenza") else ""
    if b.get("stato") == "in_arrivo" and b.get("data_apertura") and b["data_apertura"] > oggi:
        return f"Domande dal {b['data_apertura']:%d/%m/%Y}" + (f" · {scade}" if scade else "")
    return scade.capitalize() if scade else "Senza scadenza fissa"


def _dove(b: dict) -> str:
    from app.abbinamento.territorio import NOMI_REGIONI

    regioni = [NOMI_REGIONI[r] for r in b.get("territorio_regioni") or [] if r in NOMI_REGIONI]
    if b.get("territorio") == "nessun_vincolo":
        return "Tutta Italia"
    if len(regioni) == 1:
        return regioni[0]
    return f"{len(regioni)} regioni" if regioni else ""


def _voce_bando(b: dict, sopra: dict, oggi: date) -> dict:
    titolo = sopra.get("titolo") or b["titolo"]
    if len(titolo) > 120:
        titolo = titolo[:117].rstrip() + "…"
    return {"tipo": "bando", "id": b["id"], "titolo": titolo, "ente": sopra.get("ente") or b.get("ente") or "",
            "riga": sopra.get("riga") or riga_bando(b), "quando": _quando_bando(b, oggi), "dove": _dove(b)}


def _voce_misura(m: dict, sopra: dict) -> dict:
    fino = _data(m.get("in_vigore_fino_al"))
    riga = sopra.get("riga")
    if not riga:
        massimo = (m.get("beneficio_stimato") or {}).get("percentuale_max")
        riga = f"Beneficio stimato fino a circa il {round(float(massimo))}% della spesa" if massimo else "Agevolazione nazionale"
    return {"tipo": "misura", "id": m["id"], "titolo": sopra.get("titolo") or m["nome"],
            "ente": sopra.get("ente") or (m.get("ente") or "").split(";")[0].split(",")[0],
            "riga": riga, "quando": f"Aperta fino al {fino:%d/%m/%Y}" if fino else "Sempre aperta", "dove": "Misura nazionale"}


def _automatici(cur, esclusi: list[int], quanti: int, oggi: date) -> list[dict]:
    cur.execute(f"""SELECT {_COLONNE} FROM bandi b JOIN bandi_situazione s USING (id)
                    WHERE {_VALIDO} AND b.da_aggiornare IS NULL AND NOT (b.id = ANY(%s))
                      AND (b.scadenza IS NULL OR b.scadenza >= current_date + 14)
                      AND b.tipi_agevolazione && ARRAY['fondo_perduto', 'voucher']
                      AND coalesce(b.fondo_perduto_massimo, b.contributo_massimo) BETWEEN %s AND %s
                      AND coalesce(b.percentuale_fondo_perduto, b.percentuale) IS NOT NULL
                      AND (coalesce(cardinality(b.dimensioni_ammesse), 0) = 0
                           OR b.dimensioni_ammesse && ARRAY['micro', 'piccola'])""",
                (esclusi, IMPORTO_MIN, IMPORTO_MAX))
    righe = [dict(r) for r in cur.fetchall()]
    recente = oggi - timedelta(days=RECENTI_GIORNI)
    righe.sort(key=lambda r: (-(r["creato_il"].date() >= recente if r.get("creato_il") else 0),
                              -float(r.get("fondo_perduto_massimo") or r.get("contributo_massimo") or 0), r["id"]))
    scelti, enti = [], set()
    for r in righe:
        if r["ente"] in enti:
            continue
        enti.add(r["ente"])
        scelti.append(r)
        if len(scelti) >= quanti:
            break
    return scelti


def _scegli(conn, quanti: int, oggi: date) -> list[dict]:
    from app import misure

    dal_file = voci_file(oggi)
    numeri = [int(v["bando"]) for v in dal_file if str(v.get("bando", "")).isdigit()]
    with conn.cursor() as cur:
        cur.execute(f"SELECT {_COLONNE} FROM bandi b JOIN bandi_situazione s USING (id) WHERE {_VALIDO} AND b.id = ANY(%s)",
                    (numeri,))
        validi = {r["id"]: dict(r) for r in cur.fetchall()}
        voci = []
        for v in dal_file:
            if v.get("bando") and int(v["bando"]) in validi:
                voci.append(_voce_bando(validi[int(v["bando"])], v, oggi))
            elif v.get("misura") and (m := misure.una(str(v["misura"]))) and m.get("stato") == "aperto":
                voci.append(_voce_misura(m, v))
            if len(voci) >= quanti:
                return voci
        presi = [x["id"] for x in voci if x["tipo"] == "bando"]
        voci += [_voce_bando(b, {}, oggi) for b in _automatici(cur, presi, quanti - len(voci), oggi)]
    return voci


def scegli(conn, quanti: int = QUANTI) -> list[dict]:
    """Le voci della vetrina, tenute in memoria CACHE_SECONDI (si ricalcolano subito se cambia il file).
    Se il database non risponde: l'ultima vetrina calcolata, o nessuna."""
    adesso = time.monotonic()
    firma = (FILE.stat().st_mtime if FILE.is_file() else 0, quanti, date.today())
    if _cache.get("scade", 0) > adesso and _cache.get("firma") == firma:
        return _cache["voci"]
    try:
        voci = _scegli(conn, quanti, date.today())
    except Exception:  # noqa: BLE001 - la pagina pubblica non deve cadere per la vetrina
        log.exception("vetrina della pagina pubblica non calcolata")
        conn.rollback()
        return _cache.get("voci", [])
    _cache.update(voci=voci, firma=firma, scade=adesso + CACHE_SECONDI)
    return voci


_SCRIPT = """<script>
(function(){
  var v = document.querySelector(".vetrina"); if (!v) return;
  var voci = v.querySelectorAll(".voce"), punti = v.querySelectorAll(".puntini button"), box = v.querySelector(".voci");
  var pausa = v.querySelector(".pausa"), comandi = v.querySelector(".comandi");
  if (voci.length < 2) return;
  var i = 0, timer = null, fermo = false, dentro = false;
  var ridotto = window.matchMedia && window.matchMedia("(prefers-reduced-motion: reduce)").matches;
  comandi.hidden = false; if (!ridotto) pausa.hidden = false;
  function mostra(n){
    voci[i].classList.remove("attiva"); punti[i].removeAttribute("aria-current");
    i = (n + voci.length) % voci.length;
    voci[i].classList.add("attiva"); punti[i].setAttribute("aria-current", "true");
  }
  function gira(){
    clearInterval(timer); timer = null;
    if (!fermo && !dentro && !ridotto && !document.hidden) timer = setInterval(function(){ mostra(i + 1); }, __GIRO__);
    box.setAttribute("aria-live", timer ? "off" : "polite");
  }
  function ferma(si){ fermo = si; pausa.textContent = si ? "▶ Riprendi" : "❚❚ Pausa";
    pausa.setAttribute("aria-label", si ? "Riprendi lo scorrimento dei bandi" : "Ferma lo scorrimento dei bandi"); gira(); }
  Array.prototype.forEach.call(punti, function(p, k){ p.addEventListener("click", function(){ mostra(k); gira(); }); });
  pausa.addEventListener("click", function(){ ferma(!fermo); });
  v.addEventListener("mouseenter", function(){ dentro = true; gira(); });
  v.addEventListener("mouseleave", function(){ dentro = false; gira(); });
  v.addEventListener("focusin", function(){ dentro = true; gira(); });
  v.addEventListener("focusout", function(e){ if (!v.contains(e.relatedTarget)) { dentro = false; gira(); } });
  v.addEventListener("touchstart", function(){ if (!fermo) ferma(true); }, {passive: true});
  document.addEventListener("visibilitychange", gira);
  gira();
})();
</script>"""


def html(voci: list[dict]) -> str:
    """Il riquadro "Bandi in vetrina". Senza JavaScript si vede la prima voce (le altre restano nascoste)."""
    from app.pubblico import _e

    if not voci:
        return ""
    n = len(voci)
    schede = []
    for k, x in enumerate(voci):
        dove = f'<span class="tipo">{_e(x["dove"])}</span>' if x.get("dove") else ""
        schede.append(
            f'<article class="voce{" attiva" if k == 0 else ""}" role="group" aria-roledescription="bando" '
            f'aria-label="{k + 1} di {n}"><div class="piccolo">{_e(x["ente"])}</div><h3>{_e(x["titolo"])}</h3>'
            f'<p class="agevolazione">{dove} <b>{_e(x["riga"])}</b></p><p class="quando">{_e(x["quando"])}</p>'
            f'<a class="bottone" href="/registrati">Scopri se fa per te</a></article>')
    corrente = ' aria-current="true"'
    punti = "".join(f'<button type="button" aria-label="Mostra il bando {k + 1} di {n}: {_e(x["titolo"])}"'
                    f'{corrente if k == 0 else ""}></button>' for k, x in enumerate(voci))
    return (f'<section class="carta vetrina" aria-roledescription="carosello" aria-labelledby="vetrina-titolo">'
            f'<h2 id="vetrina-titolo" class="etichetta">Bandi in vetrina</h2>'
            f'<div class="voci" aria-live="polite">{"".join(schede)}</div>'
            f'<div class="comandi" hidden><div class="puntini">{punti}</div>'
            f'<button type="button" class="pausa" hidden aria-label="Ferma lo scorrimento dei bandi">❚❚ Pausa</button></div>'
            f'</section>{_SCRIPT.replace("__GIRO__", str(GIRO_MS))}')
