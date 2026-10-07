"""Email settimanale per impresa (05/10/2026, arricchita il 07/10/2026 su richiesta di Matteo).

Il lunedi' il servizio di raccolta prepara un'email per ogni impresa iscritta (app/raccolta/demone.py). In fase di
prova (decisione del 23/09) le email restano "da approvare" finche' Matteo non le approva dalla pagina Imprese;
con EMAIL_IMPRESE_APPROVAZIONE=0 nel .env partono subito. Qui non si usa l'IA: l'abbinamento e' quello delle regole.

L'email, nell'ordine (una sezione vuota non compare):
1. poche righe di introduzione;
2. novita' sui bandi gia' segnalati a quell'impresa: in scadenza entro 14 giorni, prorogati o con la scadenza cambiata
   (confronto con bandi_versioni), chiusi in anticipo o esauriti, riaperti, nuovi documenti ufficiali (FAQ, modulistica,
   decreti); ogni novita' una volta sola;
3. i nuovi bandi adatti (mai due volte lo stesso);
4. le misure nazionali aggiunte da poco e adatte al profilo (app/misure, campo aggiunta_il);
5. le news pubblicate (tabella news, pagina News della plancia), una volta sola per impresa;
6. quanti bandi adatti ci sono in tutto, con il link all'area impresa, e l'invito a chiedere supporto.
Se non ci sono ne' bandi nuovi ne' novita' sui bandi gia' segnalati, l'email non parte (news e misure da sole no).

Uso:  python -m app.notifiche.email_imprese prepara            # prepara le email della settimana
      python -m app.notifiche.email_imprese prepara --stampa   # solo a schermo, non scrive niente
      python -m app.notifiche.email_imprese elenco             # email da approvare e ultime decise
"""

from __future__ import annotations

import argparse
import html
import json
import os
import sys
from datetime import date, datetime, timedelta

from app import impresa, utenti
from app.abbinamento import catalogo, regole
from app.impresa import vista

GIORNI_IN_SCADENZA = 14
MASSIMO_BANDI = 20          # il resto alla settimana dopo
MASSIMO_AGGIORNAMENTI = 15
GIORNI_MISURE_NUOVE = 30    # una misura aggiunta da piu' tempo non e' piu' una novita'
MASSIMO_MISURE = 3          # le altre nelle settimane dopo (finche' sono "nuove")
LUNGHEZZA_SINTESI = 200
CATEGORIE_DOCUMENTI = {"faq": "FAQ", "modulistica": "modulistica", "decreto": "decreto", "bando": "testo del bando"}

NOMI_FORMA = {"fondo_perduto": "fondo perduto", "credito_imposta": "credito d'imposta",
              "finanziamento_agevolato": "finanziamento agevolato", "garanzia": "garanzia", "voucher": "voucher"}

# Colori e stili dell'email (in linea: molti programmi di posta ignorano i fogli di stile).
BLU, ROSSO, VERDE, ARANCIO = "#1a4d8f", "#b42318", "#1e7b34", "#8a5a00"
STILE_TITOLO = f"font-size:17px;color:{BLU};margin:28px 0 8px;padding-bottom:4px;border-bottom:2px solid {BLU}"
STILE_RIQUADRO = "border:1px solid #ddd;border-radius:6px;padding:12px;margin:12px 0"


def approvazione_richiesta() -> bool:
    """Fase di prova (23/09): le email partono solo dopo l'approvazione di Matteo, salvo EMAIL_IMPRESE_APPROVAZIONE=0."""
    return os.environ.get("EMAIL_IMPRESE_APPROVAZIONE", "1") != "0"


def settimana_iso(giorno: date) -> str:
    c = giorno.isocalendar()
    return f"{c.year}-W{c.week:02d}"


# --- testo dell'email (senza database: si prova da solo) ---

def _data(d: date | None) -> str:
    return d.strftime("%d/%m/%Y") if d else "non indicata"


def _euro(x) -> str:
    return f"{int(round(float(x))):,}".replace(",", ".") + " euro"


def agevolazione(b: dict) -> str:
    """Forma dell'aiuto e importo massimo, se la scheda li ha."""
    forme = b.get("tipi_agevolazione") or ([b["tipo_agevolazione"]] if b.get("tipo_agevolazione") else [])
    testo = ", ".join(NOMI_FORMA.get(f, str(f).replace("_", " ")) for f in forme)
    massimo = b.get("contributo_massimo") or b.get("fondo_perduto_massimo") or b.get("finanziamento_massimo")
    if massimo:
        testo = f"{testo}, fino a {_euro(massimo)}" if testo else f"fino a {_euro(massimo)}"
    if b.get("percentuale") and testo:
        testo += f" ({float(b['percentuale']):g}% delle spese)"
    return testo


def _sintesi(testo: str | None, lunghezza: int = LUNGHEZZA_SINTESI) -> str:
    testo = " ".join((testo or "").split())
    if len(testo) <= lunghezza:
        return testo
    return testo[:lunghezza].rsplit(" ", 1)[0].rstrip(",;:.") + "…"


def link_scheda(bando_id: int, impresa_id: int, supporto: bool = False) -> str:
    return f"{utenti.sito_url()}/impresa/bandi/{bando_id}?impresa={impresa_id}" + ("&supporto=1" if supporto else "")


def link_assoluto(link: str | None) -> str | None:
    """I link delle news possono essere pagine di Bandi Radar ("/impresa/misure"): diventano indirizzi completi."""
    if not link:
        return None
    return utenti.sito_url() + link if link.startswith("/") else link


def _a(url: str, testo: str, colore: str = BLU) -> str:
    return f"<a href='{html.escape(url)}' style='color:{colore}'>{html.escape(testo)}</a>"


def introduzione(voci: list[dict], aggiornamenti: list[dict]) -> str:
    """Poche righe in apertura: chi siamo, cosa facciamo per l'impresa, cosa c'e' questa settimana."""
    parti = []
    if aggiornamenti:
        parti.append(f"novità su {len(aggiornamenti)} bandi che ti abbiamo già segnalato" if len(aggiornamenti) > 1
                     else "una novità su un bando che ti abbiamo già segnalato")
    if voci:
        parti.append(f"{len(voci)} nuovi bandi adatti alla tua impresa" if len(voci) > 1
                     else "un nuovo bando adatto alla tua impresa")
    return ("ecco il punto della settimana di Bandi Radar. Ogni giorno controlliamo i siti di Unione europea, ministeri, "
            "Regioni, Camere di commercio e Comuni capoluogo e ti scriviamo solo quello che riguarda la tua impresa. "
            f"Questa settimana trovi {' e '.join(parti)}." if parti else
            "ecco il punto della settimana di Bandi Radar sui bandi per la tua impresa.")


def _riga_scadenza(b: dict) -> str:
    ora = b.get("ora_scadenza")
    return _data(b.get("scadenza")) + (f" alle {ora.strftime('%H:%M')}" if ora and hasattr(ora, "strftime") else "")


def eventi_bando(prima: dict, ora: dict, documenti: list[dict], oggi: date, scadenza_gia_avvisata: bool,
                 dal: date | None = None) -> list[dict]:
    """Cosa e' cambiato in un bando gia' segnalato: confronta il bando com'era (`prima`, alla data `dal` dell'ultima
    email) con com'e' oggi (`ora`). Ogni dizionario ha stato, scadenza, ora_scadenza, chiuso_il, ricontrollo
    (dati.ricontrollo_stato). Ritorna eventi {tipo, testo}: in_scadenza, chiuso, esaurito, riaperto, prorogato,
    scadenza_cambiata, documenti."""
    eventi: list[dict] = []
    chiuso_prima, chiuso_ora = prima.get("stato") == "chiuso", ora.get("stato") == "chiuso"
    if chiuso_ora:
        if chiuso_prima:
            return []
        esito = (ora.get("ricontrollo") or {}).get("stato")
        scad = ora.get("scadenza")
        # Un bando arrivato alla sua scadenza non e' una notizia: lo e' la chiusura prima del tempo.
        if ora.get("chiuso_il") or esito in ("chiuso", "esaurito") or (scad and scad >= oggi):
            if ora.get("chiuso_il") and dal and ora["chiuso_il"] < dal:
                # Chiuso gia' prima della nostra segnalazione: l'ha scoperto un nuovo controllo della pagina ufficiale.
                eventi.append({"tipo": esito if esito == "esaurito" else "chiuso",
                               "testo": f"Da un nuovo controllo della pagina ufficiale il bando risulta chiuso dal "
                                        f"{_data(ora['chiuso_il'])}"
                                        + (" per esaurimento dei fondi" if esito == "esaurito" else "")
                                        + ": non si possono più presentare domande. Ci scusiamo per la segnalazione."})
                return eventi
            quando = f" il {_data(ora['chiuso_il'])}" if ora.get("chiuso_il") else ""
            if esito == "esaurito":
                eventi.append({"tipo": "esaurito", "testo": f"Fondi esauriti: lo sportello è stato chiuso{quando}, "
                                                            "prima della scadenza. Non si possono più presentare domande."})
            else:
                eventi.append({"tipo": "chiuso", "testo": f"Chiuso in anticipo{quando}: non si possono più presentare "
                                                          "domande."})
        return eventi
    s_prima, s_ora = prima.get("scadenza"), ora.get("scadenza")
    if chiuso_prima:
        eventi.append({"tipo": "riaperto", "testo": "Riaperto: si possono di nuovo presentare domande"
                       + (f", fino al {_riga_scadenza(ora)}." if s_ora else ".")})
    elif s_prima and s_ora and s_ora > s_prima:
        eventi.append({"tipo": "prorogato", "testo": f"Scadenza prorogata: dal {_data(s_prima)} al {_riga_scadenza(ora)}."})
    elif s_prima and s_ora and s_ora < s_prima:
        eventi.append({"tipo": "scadenza_cambiata", "testo": f"Attenzione, scadenza anticipata: dal {_data(s_prima)} "
                                                             f"al {_riga_scadenza(ora)}."})
    elif not s_prima and s_ora:
        eventi.append({"tipo": "scadenza_cambiata", "testo": f"Ora c'è la scadenza: {_riga_scadenza(ora)}."})
    if s_ora and oggi <= s_ora <= oggi + timedelta(days=GIORNI_IN_SCADENZA) and not scadenza_gia_avvisata and not eventi:
        giorni = (s_ora - oggi).days
        quando = "oggi" if giorni == 0 else "domani" if giorni == 1 else f"tra {giorni} giorni"
        consiglio = ("se vuoi partecipare, non c'è tempo da perdere." if giorni <= 3 else
                     "se ti interessa, è il momento di preparare la domanda.")
        eventi.append({"tipo": "in_scadenza", "testo": f"Scade {quando}, il {_riga_scadenza(ora)}: {consiglio}"})
    if documenti:
        nomi = [f"{CATEGORIE_DOCUMENTI.get(d.get('categoria'), 'documento')} «{_sintesi(d.get('nome'), 70)}»"
                for d in documenti[:3]]
        altri = f" e altri {len(documenti) - 3}" if len(documenti) > 3 else ""
        eventi.append({"tipo": "documenti", "testo": f"{'Nuovi documenti ufficiali' if len(documenti) > 1 else 'Nuovo documento ufficiale'}: "
                                                     f"{', '.join(nomi)}{altri}."})
    return eventi


_ORDINE_EVENTI = {"in_scadenza": 0, "esaurito": 1, "chiuso": 1, "scadenza_cambiata": 2, "prorogato": 3, "riaperto": 4,
                  "documenti": 5}
_COLORE_EVENTO = {"in_scadenza": ROSSO, "esaurito": ROSSO, "chiuso": ROSSO, "scadenza_cambiata": ARANCIO,
                  "prorogato": VERDE, "riaperto": VERDE, "documenti": "#222"}


def ordina_aggiornamenti(aggiornamenti: list[dict]) -> list[dict]:
    """Prima le scadenze vicine (dalla piu' vicina), poi chiusure, cambi di scadenza, riaperture, documenti."""
    return sorted(aggiornamenti, key=lambda a: (min(_ORDINE_EVENTI.get(e["tipo"], 9) for e in a["eventi"]),
                                               a.get("scadenza") or date.max, a["id"]))


def _oggetto(nome: str, voci: list[dict], aggiornamenti: list[dict]) -> str:
    in_scadenza = sum(1 for v in voci if v["motivo"] == "in_scadenza")
    novita = f"{len(aggiornamenti)} novità sui bandi già segnalati" if aggiornamenti else ""
    if not voci:
        return f"{novita[0].upper()}{novita[1:]} a {nome}" if novita else f"Bandi Radar: la settimana di {nome}"
    oggetto = f"{len(voci)} {'bando adatto' if len(voci) == 1 else 'bandi adatti'} a {nome}"
    if in_scadenza:
        oggetto += f" ({in_scadenza} in scadenza)"
    return oggetto + (f" e {novita}" if novita else "")


def componi(imp: dict, voci: list[dict], aggiornamenti: list[dict] | None = None, news: list[dict] | None = None,
            misure: list[dict] | None = None, totale: int | None = None) -> tuple[str, str, str]:
    """(oggetto, testo semplice, html). `imp`: id, nome, codice_disiscrizione. Ogni voce e' un bando nuovo (campi del
    catalogo) con in piu' `motivo` (nuovo | in_scadenza), `livello` e `da_verificare`. `aggiornamenti`: bandi gia'
    segnalati con i loro `eventi` (eventi_bando). `news`: titolo, testo, link. `misure`: versione breve con sintesi.
    `totale`: quanti bandi adatti in tutto (per il link all'area impresa)."""
    aggiornamenti, news, misure = aggiornamenti or [], news or [], misure or []
    nome = imp["nome"]
    oggetto = _oggetto(nome, voci, aggiornamenti)
    sito = utenti.sito_url()
    disiscrizione = f"{sito}/disiscrizione?codice={imp['codice_disiscrizione']}"
    area = f"{sito}/impresa?impresa={imp['id']}"
    intro = introduzione(voci, aggiornamenti)

    righe = [f"Buongiorno {nome},", "", intro, ""]
    parti = ["<div style='font-family:Arial,sans-serif;color:#222;max-width:640px;line-height:1.45'>",
             f"<p>Buongiorno <b>{html.escape(nome)}</b>,</p>", f"<p>{html.escape(intro)}</p>"]

    def titolo(testo: str) -> None:
        righe.extend([testo.upper(), ""])
        parti.append(f"<h3 style='{STILE_TITOLO}'>{html.escape(testo)}</h3>")

    # 1. Novita' sui bandi gia' segnalati
    if aggiornamenti:
        titolo("Novità sui bandi che ti abbiamo segnalato")
        for a in aggiornamenti:
            scheda = link_scheda(a["id"], imp["id"])
            aperto = not any(e["tipo"] in ("chiuso", "esaurito") for e in a["eventi"])
            righe.append(f"- {a['titolo']}")
            parti.append(f"<div style='{STILE_RIQUADRO}'><div style='font-weight:bold'>{_a(scheda, a['titolo'])}</div>")
            if a.get("ente"):
                righe.append(f"  {a['ente']}")
                parti.append(f"<div style='color:#555;font-size:13px'>{html.escape(a['ente'])}</div>")
            for e in a["eventi"]:
                righe.append(f"  > {e['testo']}")
                parti.append(f"<div style='margin-top:6px;color:{_COLORE_EVENTO.get(e['tipo'], '#222')}'>"
                             f"{html.escape(e['testo'])}</div>")
            righe.append(f"  Scheda: {scheda}")
            collegamenti = _a(scheda, "Apri la scheda")
            if aperto:
                supporto = link_scheda(a["id"], imp["id"], supporto=True)
                righe.append(f"  Richiedi supporto per la domanda: {supporto}")
                collegamenti += " &nbsp;·&nbsp; " + _a(supporto, "Richiedi supporto per la domanda")
            righe.append("")
            parti.append(f"<div style='margin-top:8px;font-size:14px'>{collegamenti}</div></div>")

    # 2. Nuovi bandi adatti
    if voci:
        titolo("Nuovi bandi adatti alla tua impresa")
        spiega = "Ogni bando te lo segnaliamo una volta sola; se poi cambia qualcosa di importante, te lo diciamo qui."
        righe.extend([spiega, ""])
        parti.append(f"<p style='color:#555;font-size:13px;margin-top:0'>{html.escape(spiega)}</p>")
    for v in voci:
        scheda, supporto = link_scheda(v["id"], imp["id"]), link_scheda(v["id"], imp["id"], supporto=True)
        scadenza = _data(v.get("scadenza")) + (" - IN SCADENZA" if v["motivo"] == "in_scadenza" else "")
        aiuto = agevolazione(v)
        sintesi = _sintesi(v.get("sintesi"))
        dubbi = ("da verificare: " + "; ".join(v["da_verificare"][:2])) if v.get("livello") == regole.DA_VERIFICARE and v.get("da_verificare") else ""
        righe.append(f"- {v['titolo']}")
        righe.append(f"  Ente: {v.get('ente') or 'non indicato'} | Scadenza: {scadenza}")
        if aiuto:
            righe.append(f"  Agevolazione: {aiuto}")
        if sintesi:
            righe.append(f"  {sintesi}")
        if dubbi:
            righe.append(f"  {dubbi}")
        righe += [f"  Scheda: {scheda}", f"  Richiedi supporto per la domanda: {supporto}", ""]

        colore = ROSSO if v["motivo"] == "in_scadenza" else "#222"
        parti.append(f"<div style='{STILE_RIQUADRO}'>")
        parti.append(f"<div style='font-size:16px;font-weight:bold'><a href='{html.escape(scheda)}' "
                     f"style='color:{BLU};text-decoration:none'>{html.escape(v['titolo'])}</a></div>")
        parti.append(f"<div style='color:#555;margin-top:4px'>{html.escape(v.get('ente') or 'Ente non indicato')} · "
                     f"scadenza <span style='color:{colore}'>{html.escape(scadenza)}</span></div>")
        if aiuto:
            parti.append(f"<div style='margin-top:4px'>Agevolazione: {html.escape(aiuto)}</div>")
        if sintesi:
            parti.append(f"<div style='margin-top:6px'>{html.escape(sintesi)}</div>")
        if dubbi:
            parti.append(f"<div style='margin-top:6px;color:{ARANCIO}'>{html.escape(dubbi)}</div>")
        parti.append(f"<div style='margin-top:8px'><a href='{html.escape(scheda)}' style='color:{BLU}'>Apri la scheda</a>"
                     f" &nbsp;·&nbsp; <a href='{html.escape(supporto)}' style='color:{BLU}'>Richiedi supporto per la "
                     f"domanda</a></div></div>")

    # 3. Misure nazionali nuove
    if misure:
        titolo("Agevolazioni nazionali da conoscere")
        spiega = ("Non sono bandi: sono agevolazioni sempre aperte (crediti d'imposta, garanzie, contributi a sportello) "
                  "che spesso si sommano ai bandi. Le abbiamo aggiunte da poco e possono interessare la tua impresa.")
        righe.extend([spiega, ""])
        parti.append(f"<p style='color:#555;font-size:13px;margin-top:0'>{html.escape(spiega)}</p>")
        for m in misure:
            url = f"{sito}/impresa/misure/{m['id']}"
            sintesi = _sintesi(m.get("sintesi"), 240)
            righe += [f"- {m['nome']}"] + ([f"  {sintesi}"] if sintesi else []) + [f"  Scheda: {url}", ""]
            parti.append(f"<div style='margin:10px 0'><b>{_a(url, m['nome'])}</b>"
                         + (f"<div style='margin-top:2px'>{html.escape(sintesi)}</div>" if sintesi else "") + "</div>")

    # 4. News
    if news:
        titolo("News")
        for n in news:
            link = link_assoluto(n.get("link"))
            righe += [f"* {n['titolo']}", f"  {' '.join(n['testo'].split())}"] + ([f"  {link}"] if link else []) + [""]
            parti.append(f"<div style='margin:10px 0'><b>{html.escape(n['titolo'])}</b>"
                         f"<div style='margin-top:2px'>{html.escape(n['testo'])}"
                         + (f" {_a(link, 'Scopri di più')}" if link else "") + "</div></div>")

    # 5. Chiusura: tutti i bandi adatti e la richiesta di supporto
    righe.append("")
    if totale:
        tutti = (f"In tutto, oggi i bandi aperti o in arrivo adatti a {nome} sono {totale}: li trovi tutti, con le schede "
                 f"complete, nella tua area riservata.")
        righe += [tutti, area, ""]
        parti.append(f"<p style='margin-top:24px'>{html.escape(tutti)} {_a(area, 'Vai ai tuoi bandi')}</p>")
    supporto = ("Hai trovato un bando che fa per te? Apri la scheda e premi «Richiedi supporto per la domanda»: i nostri "
                "consulenti verificano con te requisiti, spese ammesse e tempi, e ti aiutano a preparare la domanda.")
    righe += [supporto, "", "Buon lavoro,", "Bandi Radar", ""]
    parti.append(f"<div style='background:#eef3fa;border-radius:6px;padding:12px;margin:16px 0'>{html.escape(supporto)}</div>"
                 "<p>Buon lavoro,<br>Bandi Radar</p>")

    righe += [impresa.AVVERTENZA, "", f"Non vuoi piu' ricevere questa email? {disiscrizione}", "",
              "Bandi Radar - finanzagevolata.qiaro.it"]
    parti += [f"<p style='color:#555;font-size:13px'>{html.escape(impresa.AVVERTENZA)}</p>",
              f"<p style='color:#888;font-size:12px'>Non vuoi piu' ricevere questa email? "
              f"<a href='{html.escape(disiscrizione)}' style='color:#888'>Disiscriviti</a>.<br>"
              f"Bandi Radar - finanzagevolata.qiaro.it</p></div>"]
    return oggetto, "\n".join(righe), "\n".join(parti)


# --- preparazione ---

def _imprese_iscritte(conn) -> list[dict]:
    with conn.cursor() as cur:
        cur.execute("""SELECT i.id, i.nome, i.codice_disiscrizione, p.profilo, u.email FROM imprese i
                       JOIN utenti u ON u.id = i.utente_id JOIN profili p ON p.codice = i.profilo_codice
                       WHERE i.email_settimanale AND u.attivo AND u.email_confermata_il IS NOT NULL ORDER BY i.id""")
        return [dict(r) for r in cur.fetchall()]


def storia(conn, impresa_id: int) -> dict:
    """Cosa ha gia' ricevuto l'impresa: i bandi segnalati con la data da cui cercare novita' (l'ultima email inviata,
    quando e' stata preparata), le scadenze gia' annunciate, le news e le misure gia' mandate."""
    with conn.cursor() as cur:
        cur.execute("SELECT bando_id, segnalato_il FROM bandi_segnalati WHERE impresa_id = %s", (impresa_id,))
        segnalati = {r["bando_id"]: r["segnalato_il"] for r in cur.fetchall()}
        cur.execute("""SELECT bandi, contenuti, creata_il FROM email_imprese WHERE impresa_id = %s AND stato = 'inviata'
                       ORDER BY creata_il""", (impresa_id,))
        inviate = [dict(r) for r in cur.fetchall()]
    riferimento = inviate[-1]["creata_il"] if inviate else None
    avvisati: dict[int, set] = {}
    news_mandate, misure_mandate = set(), set()
    for e in inviate:
        for b in e["bandi"] or []:
            if b.get("motivo") == "in_scadenza":
                avvisati.setdefault(b["bando_id"], set()).add(b.get("scadenza"))   # None = scadenza non registrata
        contenuti = e.get("contenuti") or {}
        for a in contenuti.get("aggiornamenti") or []:
            if "in_scadenza" in (a.get("eventi") or []):
                avvisati.setdefault(a["bando_id"], set()).add(a.get("scadenza"))
        news_mandate |= set(contenuti.get("news") or [])
        misure_mandate |= set(contenuti.get("misure") or [])
    return {"segnalati": {b: (riferimento or quando) for b, quando in segnalati.items()}, "avvisati": avvisati,
            "news": news_mandate, "misure": misure_mandate}


def _data_json(x) -> date | None:
    if not x:
        return None
    try:
        return date.fromisoformat(str(x)[:10])
    except ValueError:
        return None


def aggiornamenti_bandi(conn, segnalati: dict[int, datetime], avvisati: dict[int, set], oggi: date) -> list[dict]:
    """Le novita' sui bandi gia' segnalati, ciascuno confrontato con com'era alla data di riferimento: la prima versione
    salvata dopo quella data (bandi_versioni conserva la riga prima di ogni modifica) e' il bando di allora."""
    if not segnalati:
        return []
    ids = list(segnalati)
    with conn.cursor() as cur:
        cur.execute("""
            WITH s AS (SELECT * FROM unnest(%s::bigint[], %s::timestamptz[]) AS s(bando_id, rif))
            SELECT b.id, b.titolo, b.ente, b.stato, b.scadenza, b.ora_scadenza, b.chiuso_il,
                   b.dati->'ricontrollo_stato' AS ricontrollo, v.dati AS prima, s.rif,
                   coalesce((SELECT jsonb_agg(jsonb_build_object('nome', al.nome, 'categoria', al.categoria) ORDER BY al.id)
                             FROM allegati al WHERE al.bando_id = b.id AND al.annuncio_id IS NULL AND al.errore IS NULL
                               AND al.tipo <> 'pagina' AND al.categoria IN ('bando', 'modulistica', 'faq', 'decreto')
                               AND al.creato_il > s.rif), '[]') AS documenti
            FROM s JOIN bandi b ON b.id = s.bando_id
            LEFT JOIN LATERAL (SELECT x.dati FROM bandi_versioni x WHERE x.bando_id = b.id AND x.salvata_il > s.rif
                               ORDER BY x.salvata_il, x.id LIMIT 1) v ON true
            WHERE b.unito_a IS NULL AND coalesce(b.preliminare->>'per_imprese', '') <> 'no'""",
                    (ids, [segnalati[i] for i in ids]))
        righe = [dict(r) for r in cur.fetchall()]
    uscita = []
    for r in righe:
        ora = {"stato": r["stato"], "scadenza": r["scadenza"], "ora_scadenza": r["ora_scadenza"],
               "chiuso_il": r["chiuso_il"], "ricontrollo": r["ricontrollo"]}
        p = r["prima"]
        prima = ora if p is None else {
            "stato": p.get("stato"), "scadenza": _data_json(p.get("scadenza")), "chiuso_il": _data_json(p.get("chiuso_il")),
            "ricontrollo": (p.get("dati") or {}).get("ricontrollo_stato")}
        gia = avvisati.get(r["id"], set())
        avvisata = None in gia or (r["scadenza"] is not None and r["scadenza"].isoformat() in gia)
        eventi = eventi_bando(prima, ora, r["documenti"] or [], oggi, avvisata, r["rif"].date())
        if eventi:
            uscita.append({"id": r["id"], "titolo": r["titolo"], "ente": r["ente"], "scadenza": r["scadenza"],
                           "eventi": eventi})
    return ordina_aggiornamenti(uscita)[:MASSIMO_AGGIORNAMENTI]


def scegli_bandi(bandi: list[dict], profilo: dict, segnalati, oggi: date,
                 pertinenti: list[tuple[dict, regole.Esito]] | None = None) -> list[dict]:
    """I bandi pertinenti mai segnalati, con il motivo: compatibili prima, poi da verificare, per scadenza; al massimo 20."""
    if pertinenti is None:
        from app.abbinamento.profilo import Profilo

        pertinenti = impresa.pertinenti(bandi, Profilo.model_validate(profilo).per_regole(), oggi)
    voci = []
    for b, esito in pertinenti:
        if b["id"] in segnalati or (b.get("scadenza") and b["scadenza"] < oggi):
            continue
        motivo = "in_scadenza" if b.get("scadenza") and b["scadenza"] <= oggi + timedelta(days=GIORNI_IN_SCADENZA) else "nuovo"
        voci.append({**b, "motivo": motivo, "livello": esito.livello, "da_verificare": vista.motivi_semplici(esito),
                     "fuori_zona": esito.fuori_zona})
    # Compatibili prima, poi a fondo perduto prima degli altri (Matteo, 05/10), poi per scadenza. I bandi di enti di
    # altre regioni in fondo (07/10): con il tetto di 20 lasciano il posto a quelli della zona dell'impresa.
    voci.sort(key=lambda v: (v["livello"] != regole.COMPATIBILE, v["fuori_zona"], not catalogo.a_fondo_perduto(v),
                             v.get("scadenza") is None, v.get("scadenza") or date.max))
    return voci[:MASSIMO_BANDI]


def contenuto_settimana(conn, profilo: dict, bandi: list[dict], gia: dict, news_attive: list[dict], oggi: date) -> dict:
    """Tutto cio' che va nell'email di un'impresa: voci (bandi nuovi), aggiornamenti, misure, news, totale.
    `gia` e' la storia dell'impresa (storia())."""
    from app import misure as misure_naz
    from app.abbinamento.profilo import Profilo

    per_regole = Profilo.model_validate(profilo).per_regole()
    pertinenti = impresa.pertinenti(bandi, per_regole, oggi)
    return {"voci": scegli_bandi(bandi, profilo, gia["segnalati"], oggi, pertinenti),
            "aggiornamenti": aggiornamenti_bandi(conn, gia["segnalati"], gia["avvisati"], oggi),
            "misure": misure_naz.nuove_per_profilo(per_regole, oggi, GIORNI_MISURE_NUOVE, gia["misure"])[:MASSIMO_MISURE],
            "news": [n for n in news_attive if n["id"] not in gia["news"]],
            "totale": len(pertinenti)}


def prepara(conn, oggi: date | None = None, solo_stampa: bool = False) -> dict:
    """Prepara l'email della settimana per ogni impresa iscritta (una sola per settimana). Con `solo_stampa` le mostra a
    schermo senza scrivere niente. Se l'approvazione non e' richiesta, le manda subito. Salva (commit) da sola."""
    from app import news as news_mod

    oggi = oggi or date.today()
    settimana = settimana_iso(oggi)
    conteggi = {"imprese": 0, "senza_bandi": 0, "create": 0, "gia_preparate": 0, "inviate": 0, "errori": 0}
    imprese = _imprese_iscritte(conn)
    conteggi["imprese"] = len(imprese)
    if not imprese:
        return conteggi
    bandi = catalogo.carica_bandi(conn)   # una volta sola per tutte le imprese
    news_attive = news_mod.attive(conn, oggi)
    nuove = []
    for imp in imprese:
        c = contenuto_settimana(conn, imp["profilo"], bandi, storia(conn, imp["id"]), news_attive, oggi)
        if not c["voci"] and not c["aggiornamenti"]:   # niente di nuovo: l'email non parte
            conteggi["senza_bandi"] += 1
            continue
        oggetto, testo, corpo_html = componi(imp, c["voci"], c["aggiornamenti"], c["news"], c["misure"], c["totale"])
        if solo_stampa:
            print(f"A: {imp['email']}\nOggetto: {oggetto}\n\n{testo}\n\n{'=' * 70}\n")
            conteggi["create"] += 1
            continue
        elenco_bandi = [{"bando_id": v["id"], "motivo": v["motivo"],
                         "scadenza": v["scadenza"].isoformat() if v.get("scadenza") else None} for v in c["voci"]]
        contenuti = {"aggiornamenti": [{"bando_id": a["id"], "eventi": [e["tipo"] for e in a["eventi"]],
                                        "scadenza": a["scadenza"].isoformat() if a.get("scadenza") else None}
                                       for a in c["aggiornamenti"]],
                     "news": [n["id"] for n in c["news"]], "misure": [m["id"] for m in c["misure"]]}
        with conn.cursor() as cur:
            cur.execute("""INSERT INTO email_imprese (impresa_id, settimana, bandi, contenuti, oggetto, testo, html)
                           VALUES (%s, %s, %s::jsonb, %s::jsonb, %s, %s, %s)
                           ON CONFLICT (impresa_id, settimana) DO NOTHING RETURNING id""",
                        (imp["id"], settimana, json.dumps(elenco_bandi), json.dumps(contenuti), oggetto, testo, corpo_html))
            r = cur.fetchone()
        if r:
            conteggi["create"] += 1
            nuove.append(r["id"])
        else:
            conteggi["gia_preparate"] += 1
    if solo_stampa:
        return conteggi
    conn.commit()
    if not approvazione_richiesta():
        for email_id in nuove:
            esito = invia(conn, email_id, "automatico")
            conteggi["inviate" if esito != "errore" else "errori"] += 1
    return conteggi


# --- approvazione ---

def invia(conn, email_id: int, chi: str) -> str:
    """Manda un'email 'da approvare' all'utente dell'impresa; se parte, i suoi bandi diventano "segnalati". Salva da sola
    (commit) subito dopo l'invio, cosi' un errore successivo non la fa ripartire due volte."""
    with conn.cursor() as cur:
        cur.execute("""SELECT e.*, u.email, u.attivo, i.email_settimanale FROM email_imprese e
                       JOIN imprese i ON i.id = e.impresa_id JOIN utenti u ON u.id = i.utente_id
                       WHERE e.id = %s FOR UPDATE OF e""", (email_id,))
        e = cur.fetchone()
    if not e:
        raise ValueError("Email non trovata.")
    if e["stato"] != "da_approvare":
        raise ValueError(f"L'email non e' da approvare (stato: {e['stato']}).")
    if not e["attivo"] or not e["email_settimanale"]:
        # Nel frattempo l'utente e' stato disattivato o l'impresa si e' disiscritta: non si manda.
        with conn.cursor() as cur:
            cur.execute("""UPDATE email_imprese SET stato = 'errore', decisa_il = now(), decisa_da = %s, errore = %s
                           WHERE id = %s""", (chi, "utente non attivo o impresa disiscritta", email_id))
        conn.commit()
        return "errore"
    esito = utenti.manda(e["email"], e["oggetto"], e["testo"], e["html"])
    with conn.cursor() as cur:
        if esito in ("inviata", "stampata"):
            cur.execute("UPDATE email_imprese SET stato = 'inviata', decisa_il = now(), decisa_da = %s, errore = NULL "
                        "WHERE id = %s", (chi, email_id))
            # Solo i bandi ancora esistenti (un bando cancellato nel frattempo non blocca l'invio).
            cur.execute("""INSERT INTO bandi_segnalati (impresa_id, bando_id, email_id)
                           SELECT %s, b.id, %s FROM jsonb_array_elements(%s::jsonb) x
                           JOIN bandi b ON b.id = (x->>'bando_id')::bigint
                           ON CONFLICT DO NOTHING""", (e["impresa_id"], email_id, json.dumps(e["bandi"])))
        else:
            cur.execute("""UPDATE email_imprese SET stato = 'errore', decisa_il = now(), decisa_da = %s, errore = %s
                           WHERE id = %s""", (chi, "invio non riuscito (servizio email)", email_id))
    conn.commit()
    return esito


def scarta(conn, email_id: int, chi: str) -> None:
    """L'email non parte; i suoi bandi NON diventano segnalati: tornano la settimana dopo (e cosi' le novita')."""
    with conn.cursor() as cur:
        cur.execute("""UPDATE email_imprese SET stato = 'scartata', decisa_il = now(), decisa_da = %s
                       WHERE id = %s AND stato = 'da_approvare' RETURNING id""", (chi, email_id))
        if cur.fetchone() is None:
            cur.execute("SELECT stato FROM email_imprese WHERE id = %s", (email_id,))
            r = cur.fetchone()
            raise ValueError("Email non trovata." if not r else f"L'email non e' da approvare (stato: {r['stato']}).")
    conn.commit()


def in_attesa(conn) -> list[dict]:
    """Per l'admin: tutte le email da approvare e le ultime 50 decise."""
    colonne = """e.id, e.impresa_id, e.settimana, e.oggetto, e.testo, e.html, e.stato, e.creata_il, e.decisa_il,
                 e.decisa_da, e.errore, jsonb_array_length(e.bandi) AS n_bandi, i.nome AS impresa_nome,
                 u.email AS utente_email"""
    origine = "FROM email_imprese e JOIN imprese i ON i.id = e.impresa_id JOIN utenti u ON u.id = i.utente_id"
    with conn.cursor() as cur:
        cur.execute(f"SELECT {colonne} {origine} WHERE e.stato = 'da_approvare' ORDER BY e.creata_il, e.id")
        da_approvare = [dict(r) for r in cur.fetchall()]
        cur.execute(f"SELECT {colonne} {origine} WHERE e.stato <> 'da_approvare' ORDER BY e.decisa_il DESC NULLS LAST, "
                    f"e.id DESC LIMIT 50")
        decise = [dict(r) for r in cur.fetchall()]
    return da_approvare + decise


def main(argv: list[str] | None = None) -> int:
    from app.db.connessione import connetti

    parser = argparse.ArgumentParser(description="Email settimanale per impresa.")
    comandi = parser.add_subparsers(dest="comando", required=True)
    p = comandi.add_parser("prepara", help="prepara le email della settimana")
    p.add_argument("--stampa", action="store_true", help="solo a schermo, senza scrivere niente")
    comandi.add_parser("elenco", help="email da approvare e ultime decise")
    args = parser.parse_args(argv)
    with connetti() as conn:
        if args.comando == "prepara":
            print(prepara(conn, solo_stampa=args.stampa))
        else:
            for e in in_attesa(conn):
                print(f"{e['id']:>5}  {e['stato']:<12} {e['settimana']}  {e['n_bandi']:>2} bandi  "
                      f"{e['impresa_nome']} <{e['utente_email']}>  {e['oggetto']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
