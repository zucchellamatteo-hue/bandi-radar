"""Email settimanale per impresa (05/10/2026, rivista il 07/10/2026 su richiesta di Matteo).

Il lunedi' il servizio di raccolta prepara un'email per ogni impresa iscritta (app/raccolta/demone.py). In fase di
prova (decisione del 23/09) le email restano "da approvare" finche' Matteo non le approva dalla pagina Imprese;
con EMAIL_IMPRESE_APPROVAZIONE=0 nel .env partono subito. Qui non si usa l'IA: l'abbinamento e' quello delle regole.

Due tipi di email (07/10):
- BENVENUTO, la prima per un'impresa che non ha mai ricevuto niente: i bandi piu' interessanti tra quelli aperti oggi
  (al massimo 10) e la riga "Altri N bandi adatti ti aspettano nel tuo portale"; niente sezioni sui bandi gia'
  segnalati ne' sui chiusi.
- SETTIMANALE, per i clienti abituali. Nell'ordine (una sezione vuota non compare):
  1. poche righe di introduzione, che elencano le sezioni nello stesso ordine;
  2. i nuovi bandi adatti (mai due volte lo stesso), al massimo 15, con il rimando al portale per gli altri;
  3. novita' sui bandi gia' segnalati a quell'impresa: in scadenza entro 14 giorni, prorogati o con la scadenza
     cambiata (confronto con bandi_versioni), riaperti, nuovi documenti ufficiali (FAQ, modulistica, decreti);
  4. in fondo, i bandi segnalati che si sono chiusi (scadenza passata, chiusura anticipata, fondi esauriti) negli
     ultimi 7 giorni, o dall'ultima email se piu' recente. Mai chiusure vecchie: un bando segnalato che risulta chiuso
     gia' da prima della segnalazione e' un errore dei nostri dati e va in Segnalazioni (plancia), non nell'email;
  5. le misure nazionali aggiunte da poco e adatte al profilo (app/misure, campo aggiunta_il);
  6. le news pubblicate (tabella news, pagina News della plancia), una volta sola per impresa;
  7. quanti bandi adatti ci sono in tutto, con il link all'area impresa, e l'invito a chiedere supporto.
  Se non ci sono ne' bandi nuovi ne' novita' sui bandi gia' segnalati, l'email non parte (news e misure da sole no).
In entrambe i bandi nuovi sono in quest'ordine: prima i compatibili (e quelli della zona dell'impresa), poi il fondo
perduto piu' alto, poi la scadenza piu' vicina. I bandi oltre il tetto restano nel portale come "visti" (vedi invia()).

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
GIORNI_CHIUSI = 7           # un bando chiuso compare tra le novita' solo se si e' chiuso nell'ultima settimana
MASSIMO_BANDI = 15          # nuovi bandi nell'email settimanale; gli altri nel portale ("Altri N bandi adatti...")
MASSIMO_BANDI_BENVENUTO = 10
MASSIMO_AGGIORNAMENTI = 15
GIORNI_MISURE_NUOVE = 30    # una misura aggiunta da piu' tempo non e' piu' una novita'
MASSIMO_MISURE = 3          # le altre nelle settimane dopo (finche' sono "nuove")
LUNGHEZZA_SINTESI = 200
CATEGORIE_DOCUMENTI = {"faq": "FAQ", "modulistica": "modulistica", "decreto": "decreto", "bando": "testo del bando"}

NOMI_FORMA = {"fondo_perduto": "fondo perduto", "credito_imposta": "credito d'imposta",
              "finanziamento_agevolato": "finanziamento agevolato", "garanzia": "garanzia", "voucher": "voucher"}

# Aspetto dell'email (07/10, Matteo: un carattere "piu' sinuoso e tech"). Outfit di Google Fonts, caricato con <link>
# nell'head: lo usano Apple Mail, iOS e alcuni altri programmi; Gmail e Outlook lo ignorano e usano i ripieghi.
# Stili in linea: molti programmi di posta ignorano i fogli di stile.
CARATTERE = "'Outfit', 'Segoe UI', 'Helvetica Neue', Arial, sans-serif"
LINK_CARATTERE = "https://fonts.googleapis.com/css2?family=Outfit:wght@400;500;600;700&display=swap"
BLU, ROSSO, VERDE, ARANCIO = "#1d4ed8", "#c0392b", "#15803d", "#b45309"
INCHIOSTRO, GRIGIO, GRIGIO_CHIARO, BORDO = "#0f172a", "#475569", "#94a3b8", "#e2e8f0"
STILE_TITOLO = (f"font-family:{CARATTERE};font-size:21px;font-weight:600;letter-spacing:-0.2px;color:{INCHIOSTRO};"
                f"margin:36px 0 8px;padding-left:12px;border-left:4px solid {BLU};line-height:1.25")
STILE_RIQUADRO = f"border:1px solid {BORDO};border-radius:12px;padding:16px 18px;margin:14px 0;background:#ffffff"
STILE_SPIEGA = f"color:{GRIGIO};font-size:14px;margin:0 0 8px"
STILE_PULSANTE = (f"display:inline-block;background:{BLU};color:#ffffff;text-decoration:none;font-weight:600;"
                  f"padding:10px 20px;border-radius:999px;font-size:15px")


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
    """I link delle news possono essere pagine di bandinQiaro ("/impresa/misure"): diventano indirizzi completi."""
    if not link:
        return None
    return utenti.sito_url() + link if link.startswith("/") else link


def _a(url: str, testo: str, colore: str = BLU) -> str:
    return (f"<a href='{html.escape(url)}' style='color:{colore};text-decoration:none;font-weight:500'>"
            f"{html.escape(testo)}</a>")


def _quanti(n: int, uno: str, molti: str) -> str:
    return uno if n == 1 else f"{n} {molti}"


def introduzione(voci: list[dict], aggiornamenti: list[dict], benvenuto: bool = False) -> str:
    """Poche righe in apertura: chi siamo, cosa facciamo per l'impresa e cosa c'e' in questa email, nello stesso ordine
    delle sezioni (nuovi bandi, novita' sui bandi gia' segnalati, bandi chiusi)."""
    chi_siamo = ("Ogni giorno controlliamo i siti di Unione europea, ministeri, Regioni, Camere di commercio e Comuni "
                 "capoluogo e ti scriviamo solo quello che riguarda la tua impresa.")
    if benvenuto:
        return (f"benvenuto in bandinQiaro! {chi_siamo} Ecco i bandi più interessanti per la tua impresa tra quelli "
                "aperti oggi. Da lunedì prossimo ti scriveremo una volta alla settimana, solo per i bandi nuovi e per le "
                "novità importanti su quelli che ti abbiamo segnalato.")
    novita, chiusi = dividi_aggiornamenti(aggiornamenti)
    parti = []
    if voci:
        parti.append(_quanti(len(voci), "un nuovo bando adatto alla tua impresa", "nuovi bandi adatti alla tua impresa"))
    if novita:
        parti.append("una novità su un bando che ti abbiamo già segnalato" if len(novita) == 1 else
                     f"novità su {len(novita)} bandi che ti abbiamo già segnalato")
    if chiusi:
        parti.append(_quanti(len(chiusi), "un bando segnalato che si è appena chiuso",
                             "bandi segnalati che si sono appena chiusi"))
    if not parti:
        return f"ecco il punto della settimana di bandinQiaro sui bandi per la tua impresa. {chi_siamo}"
    elenco = parti[0] if len(parti) == 1 else ", ".join(parti[:-1]) + " e " + parti[-1]
    return f"ecco il punto della settimana di bandinQiaro. {chi_siamo} Questa settimana trovi {elenco}."


def _riga_scadenza(b: dict) -> str:
    ora = b.get("ora_scadenza")
    return _data(b.get("scadenza")) + (f" alle {ora.strftime('%H:%M')}" if ora and hasattr(ora, "strftime") else "")


def data_chiusura(b: dict, oggi: date) -> date | None:
    """Quando un bando chiuso si e' chiuso: la chiusura anticipata (chiuso_il) o la scadenza gia' passata."""
    if b.get("chiuso_il"):
        return b["chiuso_il"]
    s = b.get("scadenza")
    return s if s and s < oggi else None


def eventi_bando(prima: dict, ora: dict, documenti: list[dict], oggi: date, scadenza_gia_avvisata: bool,
                 dal: date | None = None, segnalato_il: date | None = None) -> list[dict]:
    """Cosa e' cambiato in un bando gia' segnalato: confronta il bando com'era (`prima`, alla data `dal` dell'ultima
    email) con com'e' oggi (`ora`). Ogni dizionario ha stato, scadenza, ora_scadenza, chiuso_il, ricontrollo
    (dati.ricontrollo_stato). Ritorna eventi {tipo, testo}: in_scadenza, prorogato, scadenza_cambiata, riaperto,
    documenti; per i bandi chiusi scaduto, chiuso, esaurito (solo chiusure recenti, vedi sotto) oppure
    chiuso_prima_della_segnalazione, che non va nell'email ma in Segnalazioni come errore dei nostri dati."""
    eventi: list[dict] = []
    chiuso_prima = prima.get("stato") == "chiuso"
    chiuso_ora = ora.get("stato") == "chiuso" or bool(ora.get("scadenza") and ora["scadenza"] < oggi)
    if chiuso_ora:
        if chiuso_prima:
            return []
        esito = (ora.get("ricontrollo") or {}).get("stato")
        quando = data_chiusura(ora, oggi)
        if quando and segnalato_il and quando < segnalato_il:
            # Gli avevamo segnalato un bando gia' chiuso: l'errore e' nostro (stato o date sbagliati nella scheda) e
            # l'ha scoperto un nuovo controllo. All'impresa non si scrive (Matteo, 07/10): va corretto in plancia.
            return [{"tipo": "chiuso_prima_della_segnalazione",
                     "testo": f"Segnalato a un'impresa il {_data(segnalato_il)} ma risulta chiuso dal {_data(quando)}."}]
        # Solo chiusure recenti (Matteo, 07/10): negli ultimi GIORNI_CHIUSI giorni, o dall'ultima email se piu' recente.
        # Senza una data di chiusura (chiuso dal ricontrollo della pagina) vale il confronto con l'ultima email, purche'
        # anche quella sia recente.
        limite = max(oggi - timedelta(days=GIORNI_CHIUSI), dal) if dal else oggi - timedelta(days=GIORNI_CHIUSI)
        if (quando and quando < limite) or (not quando and dal and dal < oggi - timedelta(days=GIORNI_CHIUSI)):
            return []
        il = f" il {_data(quando)}" if quando else ""
        if esito == "esaurito":
            eventi.append({"tipo": "esaurito", "testo": f"Fondi esauriti: lo sportello è stato chiuso{il}. Non si "
                                                        "possono più presentare domande."})
        elif ora.get("chiuso_il") or esito == "chiuso" or not quando:
            eventi.append({"tipo": "chiuso", "testo": f"Chiuso in anticipo{il}: non si possono più presentare domande."})
        else:
            eventi.append({"tipo": "scaduto", "testo": f"Scaduto{il}: non si possono più presentare domande."})
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


TIPI_CHIUSI = ("scaduto", "chiuso", "esaurito")
_ORDINE_EVENTI = {"in_scadenza": 0, "scadenza_cambiata": 1, "prorogato": 2, "riaperto": 3, "documenti": 4,
                  "esaurito": 5, "chiuso": 5, "scaduto": 5}
_COLORE_EVENTO = {"in_scadenza": ROSSO, "esaurito": GRIGIO, "chiuso": GRIGIO, "scaduto": GRIGIO,
                  "scadenza_cambiata": ARANCIO, "prorogato": VERDE, "riaperto": VERDE, "documenti": INCHIOSTRO}


def e_chiuso(a: dict) -> bool:
    return any(e["tipo"] in TIPI_CHIUSI for e in a["eventi"])


def dividi_aggiornamenti(aggiornamenti: list[dict]) -> tuple[list[dict], list[dict]]:
    """(novita' sui bandi ancora aperti, bandi chiusi): i chiusi vanno in fondo, in una sezione a parte."""
    return [a for a in aggiornamenti if not e_chiuso(a)], [a for a in aggiornamenti if e_chiuso(a)]


def ordina_aggiornamenti(aggiornamenti: list[dict]) -> list[dict]:
    """Prima le scadenze vicine (dalla piu' vicina), poi cambi di scadenza, proroghe, riaperture, documenti; in fondo
    i bandi chiusi."""
    return sorted(aggiornamenti, key=lambda a: (min(_ORDINE_EVENTI.get(e["tipo"], 9) for e in a["eventi"]),
                                               a.get("scadenza") or date.max, a["id"]))


def _oggetto(nome: str, voci: list[dict], aggiornamenti: list[dict], benvenuto: bool = False) -> str:
    if benvenuto:
        return (f"Benvenuto in bandinQiaro: "
                + (f"i {len(voci)} bandi più interessanti per {nome}" if len(voci) > 1
                   else f"il bando più interessante per {nome}"))
    in_scadenza = sum(1 for v in voci if v["motivo"] == "in_scadenza")
    novita = f"{len(aggiornamenti)} novità sui bandi già segnalati" if aggiornamenti else ""
    if not voci:
        return f"{novita[0].upper()}{novita[1:]} a {nome}" if novita else f"bandinQiaro: la settimana di {nome}"
    oggetto = f"{len(voci)} {'nuovo bando adatto' if len(voci) == 1 else 'nuovi bandi adatti'} a {nome}"
    if in_scadenza:
        oggetto += f" ({in_scadenza} in scadenza)"
    return oggetto + (f" e {novita}" if novita else "")


def documento_html(corpo: str, titolo: str = "bandinQiaro") -> str:
    """Pagina completa: nell'head il carattere Outfit (dove il programma di posta lo carica), nel body il contenuto.
    L'avviso "non rispondere" (app/notifiche/email.py) si aggiunge prima di </body> al momento dell'invio."""
    return ("<!DOCTYPE html><html lang='it'><head><meta charset='utf-8'>"
            "<meta name='viewport' content='width=device-width, initial-scale=1'>"
            f"<title>{html.escape(titolo)}</title>"
            "<link rel='preconnect' href='https://fonts.googleapis.com'>"
            "<link rel='preconnect' href='https://fonts.gstatic.com' crossorigin>"
            f"<link href='{LINK_CARATTERE}' rel='stylesheet'>"
            f"<style>body,td,div,p,a,h1,h2,h3{{font-family:{CARATTERE}}}</style></head>"
            f"<body style='margin:0;padding:24px 12px;background:#f1f5f9;font-family:{CARATTERE};color:{INCHIOSTRO}'>"
            f"{corpo}</body></html>")


def componi(imp: dict, voci: list[dict], aggiornamenti: list[dict] | None = None, news: list[dict] | None = None,
            misure: list[dict] | None = None, totale: int | None = None, altri: int = 0,
            benvenuto: bool = False) -> tuple[str, str, str]:
    """(oggetto, testo semplice, html). `imp`: id, nome, codice_disiscrizione. Ogni voce e' un bando nuovo (campi del
    catalogo) con in piu' `motivo` (nuovo | in_scadenza), `livello` e `da_verificare`. `aggiornamenti`: bandi gia'
    segnalati con i loro `eventi` (eventi_bando); i chiusi vanno in fondo, in una sezione a parte. `news`: titolo,
    testo, link. `misure`: versione breve con sintesi. `totale`: quanti bandi adatti in tutto (per il link all'area
    impresa). `altri`: quanti bandi adatti nuovi non entrano nell'email (riga "Altri N bandi... nel tuo portale").
    `benvenuto`: prima email dell'impresa (niente sezioni sui bandi gia' segnalati)."""
    aggiornamenti = [] if benvenuto else (aggiornamenti or [])
    news, misure = news or [], misure or []
    novita, chiusi = dividi_aggiornamenti(aggiornamenti)
    nome = imp["nome"]
    oggetto = _oggetto(nome, voci, aggiornamenti, benvenuto)
    sito = utenti.sito_url()
    disiscrizione = f"{sito}/disiscrizione?codice={imp['codice_disiscrizione']}"
    area = f"{sito}/impresa?impresa={imp['id']}"
    intro = introduzione(voci, aggiornamenti, benvenuto)

    righe = [f"Buongiorno {nome},", "", intro, ""]
    parti = [f"<div style='max-width:640px;margin:0 auto;background:#ffffff;border-radius:16px;padding:28px 26px;"
             f"font-family:{CARATTERE};color:{INCHIOSTRO};font-size:15px;line-height:1.55'>",
             f"<div style='font-size:13px;font-weight:600;letter-spacing:1.5px;text-transform:uppercase;color:{BLU}'>"
             f"bandinQiaro</div>",
             f"<h1 style='font-family:{CARATTERE};font-size:26px;font-weight:600;letter-spacing:-0.4px;line-height:1.2;"
             f"margin:6px 0 18px;color:{INCHIOSTRO}'>{'Benvenuto' if benvenuto else 'Il punto della settimana'}</h1>",
             f"<p style='margin:0 0 10px'>Buongiorno <b>{html.escape(nome)}</b>,</p>",
             f"<p style='margin:0 0 10px'>{html.escape(intro)}</p>"]

    def titolo(testo: str, spiega: str | None = None) -> None:
        righe.extend([testo.upper(), ""] + ([spiega, ""] if spiega else []))
        parti.append(f"<h2 style='{STILE_TITOLO}'>{html.escape(testo)}</h2>")
        if spiega:
            parti.append(f"<p style='{STILE_SPIEGA}'>{html.escape(spiega)}</p>")

    def collegamenti(bando_id: int, supporto: bool) -> tuple[list[str], str]:
        scheda = link_scheda(bando_id, imp["id"])
        testo = [f"  Scheda: {scheda}"]
        corpo = _a(scheda, "Apri la scheda →")
        if supporto:
            url = link_scheda(bando_id, imp["id"], supporto=True)
            testo.append(f"  Richiedi supporto per la domanda: {url}")
            corpo += f" <span style='color:{GRIGIO_CHIARO}'>&nbsp;·&nbsp;</span> " + _a(url, "Richiedi supporto per la domanda")
        return testo, f"<div style='margin-top:12px;font-size:14px'>{corpo}</div>"

    def riquadro_aggiornamento(a: dict) -> None:
        aperto = not e_chiuso(a)
        righe.append(f"- {a['titolo']}")
        parti.append(f"<div style='{STILE_RIQUADRO}'><div style='font-size:17px;font-weight:600;line-height:1.3'>"
                     f"{_a(link_scheda(a['id'], imp['id']), a['titolo'], INCHIOSTRO)}</div>")
        if a.get("ente"):
            righe.append(f"  {a['ente']}")
            parti.append(f"<div style='color:{GRIGIO};font-size:13px;margin-top:2px'>{html.escape(a['ente'])}</div>")
        for e in a["eventi"]:
            righe.append(f"  > {e['testo']}")
            parti.append(f"<div style='margin-top:8px;color:{_COLORE_EVENTO.get(e['tipo'], INCHIOSTRO)};font-weight:500'>"
                         f"{html.escape(e['testo'])}</div>")
        testo, corpo = collegamenti(a["id"], aperto)
        righe.extend(testo + [""])
        parti.append(corpo + "</div>")

    # 1. Bandi nuovi (nel benvenuto: i piu' interessanti tra quelli aperti oggi)
    if voci:
        if benvenuto:
            titolo("I bandi più interessanti per la tua impresa",
                   "Li abbiamo scelti tra quelli aperti oggi: prima quelli che rispettano tutti i requisiti, poi i "
                   "contributi a fondo perduto più alti, poi le scadenze più vicine.")
        else:
            titolo("Nuovi bandi adatti alla tua impresa",
                   "Ogni bando te lo segnaliamo una volta sola; se poi cambia qualcosa di importante, te lo diciamo qui.")
    for v in voci:
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
        testo, corpo = collegamenti(v["id"], True)
        righe.extend(testo + [""])

        colore = ROSSO if v["motivo"] == "in_scadenza" else INCHIOSTRO
        parti.append(f"<div style='{STILE_RIQUADRO}'>")
        parti.append(f"<div style='font-size:17px;font-weight:600;line-height:1.3'>"
                     f"{_a(link_scheda(v['id'], imp['id']), v['titolo'], INCHIOSTRO)}</div>")
        parti.append(f"<div style='color:{GRIGIO};font-size:13px;margin-top:4px'>"
                     f"{html.escape(v.get('ente') or 'Ente non indicato')} · scadenza "
                     f"<span style='color:{colore};font-weight:600'>{html.escape(scadenza)}</span></div>")
        if aiuto:
            parti.append(f"<div style='margin-top:10px'><span style='display:inline-block;background:#eff6ff;color:{BLU};"
                         f"border-radius:999px;padding:3px 12px;font-size:13px;font-weight:500'>{html.escape(aiuto)}</span></div>")
        if sintesi:
            parti.append(f"<div style='margin-top:10px'>{html.escape(sintesi)}</div>")
        if dubbi:
            parti.append(f"<div style='margin-top:8px;color:{ARANCIO};font-size:14px'>{html.escape(dubbi)}</div>")
        parti.append(corpo + "</div>")
    if voci and altri:
        riga = (f"Altri {altri} bandi adatti ti aspettano nel tuo portale" if altri > 1
                else "Un altro bando adatto ti aspetta nel tuo portale")
        righe += [f"{riga}: {area}", ""]
        parti.append(f"<p style='margin:18px 0 4px;font-weight:500'>{html.escape(riga)}: "
                     f"{_a(area, 'vai ai tuoi bandi →')}</p>")

    # 2. Novita' sui bandi gia' segnalati (ancora aperti)
    if novita:
        titolo("Novità sui bandi che ti abbiamo segnalato")
        for a in novita:
            riquadro_aggiornamento(a)

    # 3. In fondo, i bandi segnalati che si sono chiusi questa settimana
    if chiusi:
        titolo("Bandi segnalati che si sono chiusi",
               "Si sono chiusi negli ultimi giorni: non si possono più presentare domande.")
        for a in chiusi:
            riquadro_aggiornamento(a)

    # 4. Misure nazionali nuove
    if misure:
        titolo("Agevolazioni nazionali da conoscere",
               "Non sono bandi: sono agevolazioni sempre aperte (crediti d'imposta, garanzie, contributi a sportello) "
               "che spesso si sommano ai bandi. Le abbiamo aggiunte da poco e possono interessare la tua impresa.")
        for m in misure:
            url = f"{sito}/impresa/misure/{m['id']}"
            sintesi = _sintesi(m.get("sintesi"), 240)
            righe += [f"- {m['nome']}"] + ([f"  {sintesi}"] if sintesi else []) + [f"  Scheda: {url}", ""]
            parti.append(f"<div style='margin:12px 0'><div style='font-weight:600'>{_a(url, m['nome'])}</div>"
                         + (f"<div style='margin-top:2px;color:{GRIGIO}'>{html.escape(sintesi)}</div>" if sintesi else "")
                         + "</div>")

    # 5. News
    if news:
        titolo("News")
        for n in news:
            link = link_assoluto(n.get("link"))
            righe += [f"* {n['titolo']}", f"  {' '.join(n['testo'].split())}"] + ([f"  {link}"] if link else []) + [""]
            parti.append(f"<div style='margin:12px 0'><div style='font-weight:600'>{html.escape(n['titolo'])}</div>"
                         f"<div style='margin-top:2px;color:{GRIGIO}'>{html.escape(n['testo'])}"
                         + (f" {_a(link, 'Scopri di più')}" if link else "") + "</div></div>")

    # 6. Chiusura: tutti i bandi adatti e la richiesta di supporto
    righe.append("")
    if totale:
        tutti = (f"In tutto, oggi i bandi aperti o in arrivo adatti a {nome} sono {totale}: li trovi tutti, con le schede "
                 f"complete, nella tua area riservata.")
        righe += [tutti, area, ""]
        parti.append(f"<p style='margin:32px 0 14px'>{html.escape(tutti)}</p>"
                     f"<p style='margin:0 0 8px'><a href='{html.escape(area)}' style='{STILE_PULSANTE}'>"
                     f"Vai ai tuoi bandi</a></p>")
    supporto = ("Hai trovato un bando che fa per te? Apri la scheda e premi «Richiedi supporto per la domanda»: i nostri "
                "consulenti verificano con te requisiti, spese ammesse e tempi, e ti aiutano a preparare la domanda.")
    righe += [supporto, "", "Buon lavoro,", "bandinQiaro", ""]
    parti.append(f"<div style='background:#eff6ff;border-radius:12px;padding:16px 18px;margin:22px 0'>"
                 f"{html.escape(supporto)}</div><p style='margin:0 0 6px'>Buon lavoro,<br><b>bandinQiaro</b></p>")

    righe += [impresa.AVVERTENZA, "", f"Non vuoi piu' ricevere questa email? {disiscrizione}", "",
              "bandinQiaro - bandinqiaro.it"]
    parti += [f"<p style='color:{GRIGIO};font-size:12px;margin-top:24px;line-height:1.5'>"
              f"{html.escape(impresa.AVVERTENZA)}</p>",
              f"<p style='color:{GRIGIO_CHIARO};font-size:12px'>Non vuoi piu' ricevere questa email? "
              f"<a href='{html.escape(disiscrizione)}' style='color:{GRIGIO_CHIARO}'>Disiscriviti</a>.<br>"
              f"bandinQiaro - bandinqiaro.it</p></div>"]
    return oggetto, "\n".join(righe), documento_html("\n".join(parti), oggetto)


# --- preparazione ---

def _imprese_iscritte(conn) -> list[dict]:
    with conn.cursor() as cur:
        cur.execute("""SELECT i.id, i.nome, i.codice_disiscrizione, p.profilo, u.email FROM imprese i
                       JOIN utenti u ON u.id = i.utente_id JOIN profili p ON p.codice = i.profilo_codice
                       WHERE i.email_settimanale AND u.attivo AND u.email_confermata_il IS NOT NULL ORDER BY i.id""")
        return [dict(r) for r in cur.fetchall()]


def storia(conn, impresa_id: int) -> dict:
    """Cosa ha gia' ricevuto l'impresa: i bandi segnalati per email con la data da cui cercare novita' (l'ultima email
    inviata, quando e' stata preparata) e la data della segnalazione, tutti i bandi gia' proposti (anche solo "visti nel
    portale", che non tornano come nuovi), le scadenze gia' annunciate, le news e le misure gia' mandate, e se e' la
    prima email (nessuna email inviata e nessun bando segnalato: allora e' l'email di benvenuto)."""
    with conn.cursor() as cur:
        cur.execute("SELECT bando_id, segnalato_il, modo FROM bandi_segnalati WHERE impresa_id = %s", (impresa_id,))
        righe = [dict(r) for r in cur.fetchall()]
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
    per_email = [r for r in righe if r["modo"] == "email"]
    return {"segnalati": {r["bando_id"]: (riferimento or r["segnalato_il"]) for r in per_email},
            "segnalati_il": {r["bando_id"]: r["segnalato_il"] for r in per_email},
            "proposti": {r["bando_id"] for r in righe}, "prima_email": not inviate and not righe,
            "avvisati": avvisati, "news": news_mandate, "misure": misure_mandate}


def _data_json(x) -> date | None:
    if not x:
        return None
    try:
        return date.fromisoformat(str(x)[:10])
    except ValueError:
        return None


def _giorno(x) -> date | None:
    return x.date() if isinstance(x, datetime) else x


def aggiornamenti_bandi(conn, segnalati: dict[int, datetime], avvisati: dict[int, set], oggi: date,
                        segnalati_il: dict[int, datetime] | None = None, errori: list[dict] | None = None) -> list[dict]:
    """Le novita' sui bandi gia' segnalati, ciascuno confrontato con com'era alla data di riferimento: la prima versione
    salvata dopo quella data (bandi_versioni conserva la riga prima di ogni modifica) e' il bando di allora.
    `segnalati_il`: quando ogni bando e' stato segnalato (di base la data di riferimento). I bandi che risultano chiusi
    da prima della segnalazione non vanno nell'email: finiscono in `errori` (se passato), per Segnalazioni."""
    if not segnalati:
        return []
    segnalati_il = segnalati_il or segnalati
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
        if p is None:
            # Nessuna modifica salvata da allora: il bando era com'e' oggi, salvo una scadenza passata nel frattempo
            # (il bando era ancora aperto alla data di riferimento).
            chiuso_dopo = (data_chiusura(ora, oggi) or date.min) >= r["rif"].date()
            prima = {**ora, "stato": "aperto"} if chiuso_dopo else ora
        else:
            prima = {"stato": p.get("stato"), "scadenza": _data_json(p.get("scadenza")),
                     "chiuso_il": _data_json(p.get("chiuso_il")), "ricontrollo": (p.get("dati") or {}).get("ricontrollo_stato")}
        gia = avvisati.get(r["id"], set())
        avvisata = None in gia or (r["scadenza"] is not None and r["scadenza"].isoformat() in gia)
        eventi = eventi_bando(prima, ora, r["documenti"] or [], oggi, avvisata, r["rif"].date(),
                              _giorno(segnalati_il.get(r["id"])))
        voce = {"id": r["id"], "titolo": r["titolo"], "ente": r["ente"], "scadenza": r["scadenza"], "eventi": eventi}
        if any(e["tipo"] == "chiuso_prima_della_segnalazione" for e in eventi):
            if errori is not None:
                errori.append(voce)
        elif eventi:
            uscita.append(voce)
    return ordina_aggiornamenti(uscita)[:MASSIMO_AGGIORNAMENTI]


def segnala_errori(conn, impresa_id: int, errori: list[dict]) -> int:
    """Un bando segnalato a un'impresa che risulta chiuso da prima della segnalazione: l'errore e' nei nostri dati
    (stato o date della scheda). Diventa una segnalazione "Stato o scadenza sbagliati" nella plancia, una sola per bando
    finche' resta aperta. Ritorna quante ne ha create."""
    from app import segnalazioni

    nuove = 0
    for e in errori:
        with conn.cursor() as cur:
            cur.execute("""SELECT 1 FROM segnalazioni WHERE bando_id = %s AND tipo = 'stato_scadenza'
                           AND stato IN ('nuova', 'presa_in_carico') AND testo LIKE 'Email alle imprese:%%'""", (e["id"],))
            if cur.fetchone():
                continue
        testo = (f"Email alle imprese: il bando «{e['titolo']}» era stato proposto all'impresa n. {impresa_id}. "
                 f"{e['eventi'][0]['testo']} Controllare stato e date della scheda: nell'email non compare.")
        segnalazioni.crea(conn, {"tipo": "stato_scadenza", "bando_id": e["id"], "testo": testo,
                                 "dettagli": {"bando": str(e["id"]), "giusto": "chiuso"}}, None)
        nuove += 1
    return nuove


def importo_fondo_perduto(b: dict) -> float:
    """Quanto vale il bando a fondo perduto, per l'ordine delle proposte: il fondo perduto massimo, o il contributo
    massimo se il bando e' a fondo perduto. Non c'e' ancora una stima del beneficio per impresa: si usa il tetto."""
    if b.get("fondo_perduto_massimo"):
        return float(b["fondo_perduto_massimo"])
    if catalogo.a_fondo_perduto(b) and b.get("contributo_massimo"):
        return float(b["contributo_massimo"])
    return 0.0


def chiave_proposta(v: dict) -> tuple:
    """Ordine dei bandi nuovi (Matteo, 05/10 e 07/10): compatibili prima; i bandi di enti di altre regioni in fondo
    (lasciano il posto a quelli della zona); poi il fondo perduto, dal piu' alto (a parita' d'importo la percentuale
    piu' alta); poi la scadenza piu' vicina."""
    fondo_perduto = catalogo.a_fondo_perduto(v)
    percentuale = float(v.get("percentuale_fondo_perduto") or v.get("percentuale") or 0) if fondo_perduto else 0.0
    return (v["livello"] != regole.COMPATIBILE, bool(v.get("fuori_zona")), not fondo_perduto,
            -importo_fondo_perduto(v), -percentuale, v.get("scadenza") is None, v.get("scadenza") or date.max)


def scegli_bandi(bandi: list[dict], profilo: dict, proposti, oggi: date,
                 pertinenti: list[tuple[dict, regole.Esito]] | None = None) -> list[dict]:
    """Tutti i bandi pertinenti mai proposti all'impresa, con il motivo, nell'ordine delle proposte (chiave_proposta).
    Il tetto (10 nel benvenuto, 15 le altre settimane) lo mette contenuto_settimana."""
    if pertinenti is None:
        from app.abbinamento.profilo import Profilo

        pertinenti = impresa.pertinenti(bandi, Profilo.model_validate(profilo).per_regole(), oggi)
    voci = []
    for b, esito in pertinenti:
        if b["id"] in proposti or (b.get("scadenza") and b["scadenza"] < oggi):
            continue
        motivo = "in_scadenza" if b.get("scadenza") and b["scadenza"] <= oggi + timedelta(days=GIORNI_IN_SCADENZA) else "nuovo"
        voci.append({**b, "motivo": motivo, "livello": esito.livello, "da_verificare": vista.motivi_semplici(esito),
                     "fuori_zona": esito.fuori_zona})
    voci.sort(key=chiave_proposta)
    return voci


def contenuto_settimana(conn, profilo: dict, bandi: list[dict], gia: dict, news_attive: list[dict], oggi: date,
                        errori: list[dict] | None = None) -> dict:
    """Tutto cio' che va nell'email di un'impresa: voci (bandi nuovi), visti_portale, aggiornamenti, misure, news,
    totale, benvenuto. `gia` e' la storia dell'impresa (storia()).

    Tetto e "visti nel portale" (Matteo, 07/10): nell'email entrano al massimo 10 bandi (benvenuto) o 15 (le altre
    settimane), i piu' rilevanti; gli altri adatti sono nel portale, con la riga "Altri N bandi adatti ti aspettano".
    Quando l'email parte, anche questi altri si registrano come "visti nel portale" (bandi_segnalati.modo = 'portale'):
    cosi' le email dopo parlano solo dei bandi davvero nuovi, invece di riversare a pezzi, settimana dopo settimana,
    un arretrato che l'impresa ha gia' nel portale. Sui bandi solo "visti" non si mandano novita' (non li abbiamo mai
    scritti all'impresa)."""
    from app import misure as misure_naz
    from app.abbinamento.profilo import Profilo

    per_regole = Profilo.model_validate(profilo).per_regole()
    pertinenti = impresa.pertinenti(bandi, per_regole, oggi)
    benvenuto = gia["prima_email"]
    tutti = scegli_bandi(bandi, profilo, gia["proposti"], oggi, pertinenti)
    massimo = MASSIMO_BANDI_BENVENUTO if benvenuto else MASSIMO_BANDI
    aggiornamenti = [] if benvenuto else aggiornamenti_bandi(conn, gia["segnalati"], gia["avvisati"], oggi,
                                                             gia.get("segnalati_il"), errori)
    return {"voci": tutti[:massimo], "visti_portale": [v["id"] for v in tutti[massimo:]],
            "aggiornamenti": aggiornamenti, "benvenuto": benvenuto,
            "misure": misure_naz.nuove_per_profilo(per_regole, oggi, GIORNI_MISURE_NUOVE, gia["misure"])[:MASSIMO_MISURE],
            "news": [n for n in news_attive if n["id"] not in gia["news"]],
            "totale": len(pertinenti)}


def prepara(conn, oggi: date | None = None, solo_stampa: bool = False) -> dict:
    """Prepara l'email della settimana per ogni impresa iscritta (una sola per settimana). Con `solo_stampa` le mostra a
    schermo senza scrivere niente. Se l'approvazione non e' richiesta, le manda subito. Salva (commit) da sola."""
    from app import news as news_mod

    oggi = oggi or date.today()
    settimana = settimana_iso(oggi)
    conteggi = {"imprese": 0, "senza_bandi": 0, "create": 0, "gia_preparate": 0, "inviate": 0, "errori": 0,
                "benvenuto": 0, "errori_qualita": 0}
    imprese = _imprese_iscritte(conn)
    conteggi["imprese"] = len(imprese)
    if not imprese:
        return conteggi
    bandi = catalogo.carica_bandi(conn)   # una volta sola per tutte le imprese
    news_attive = news_mod.attive(conn, oggi)
    nuove = []
    for imp in imprese:
        errori: list[dict] = []
        c = contenuto_settimana(conn, imp["profilo"], bandi, storia(conn, imp["id"]), news_attive, oggi, errori)
        if errori and not solo_stampa:
            conteggi["errori_qualita"] += segnala_errori(conn, imp["id"], errori)
        if not c["voci"] and not c["aggiornamenti"]:   # niente di nuovo: l'email non parte
            conteggi["senza_bandi"] += 1
            continue
        oggetto, testo, corpo_html = componi(imp, c["voci"], c["aggiornamenti"], c["news"], c["misure"], c["totale"],
                                             altri=len(c["visti_portale"]), benvenuto=c["benvenuto"])
        if solo_stampa:
            print(f"A: {imp['email']}\nOggetto: {oggetto}\n\n{testo}\n\n{'=' * 70}\n")
            conteggi["create"] += 1
            continue
        elenco_bandi = [{"bando_id": v["id"], "motivo": v["motivo"],
                         "scadenza": v["scadenza"].isoformat() if v.get("scadenza") else None} for v in c["voci"]]
        contenuti = {"aggiornamenti": [{"bando_id": a["id"], "eventi": [e["tipo"] for e in a["eventi"]],
                                        "scadenza": a["scadenza"].isoformat() if a.get("scadenza") else None}
                                       for a in c["aggiornamenti"]],
                     "news": [n["id"] for n in c["news"]], "misure": [m["id"] for m in c["misure"]],
                     "visti_portale": c["visti_portale"], "benvenuto": c["benvenuto"]}
        with conn.cursor() as cur:
            cur.execute("""INSERT INTO email_imprese (impresa_id, settimana, bandi, contenuti, oggetto, testo, html)
                           VALUES (%s, %s, %s::jsonb, %s::jsonb, %s, %s, %s)
                           ON CONFLICT (impresa_id, settimana) DO NOTHING RETURNING id""",
                        (imp["id"], settimana, json.dumps(elenco_bandi), json.dumps(contenuti), oggetto, testo, corpo_html))
            r = cur.fetchone()
        if r:
            conteggi["create"] += 1
            conteggi["benvenuto"] += 1 if c["benvenuto"] else 0
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
    """Manda un'email 'da approvare' all'utente dell'impresa; se parte, i suoi bandi diventano "segnalati" (modo
    'email') e gli altri adatti rimandati al portale "visti nel portale" (modo 'portale', vedi contenuto_settimana).
    Salva da sola (commit) subito dopo l'invio, cosi' un errore successivo non la fa ripartire due volte."""
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
            cur.execute("""INSERT INTO bandi_segnalati (impresa_id, bando_id, email_id, modo)
                           SELECT %s, b.id, %s, 'email' FROM jsonb_array_elements(%s::jsonb) x
                           JOIN bandi b ON b.id = (x->>'bando_id')::bigint
                           ON CONFLICT DO NOTHING""", (e["impresa_id"], email_id, json.dumps(e["bandi"])))
            visti = (e.get("contenuti") or {}).get("visti_portale") or []
            cur.execute("""INSERT INTO bandi_segnalati (impresa_id, bando_id, email_id, modo)
                           SELECT %s, b.id, %s, 'portale' FROM bandi b WHERE b.id = ANY(%s::bigint[])
                           ON CONFLICT DO NOTHING""", (e["impresa_id"], email_id, visti))
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
