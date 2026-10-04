"""Email settimanale per impresa (05/10/2026): i bandi pertinenti nuovi o in scadenza, mai due volte lo stesso.

Il lunedi' il servizio di raccolta prepara un'email per ogni impresa iscritta (app/raccolta/demone.py). In fase di
prova (decisione del 23/09) le email restano "da approvare" finche' Matteo non le approva dalla pagina Imprese;
con EMAIL_IMPRESE_APPROVAZIONE=0 nel .env partono subito. Qui non si usa l'IA: l'abbinamento e' quello delle regole.

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
from datetime import date, timedelta

from app import impresa, utenti
from app.abbinamento import catalogo, regole

GIORNI_IN_SCADENZA = 14
MASSIMO_BANDI = 20          # il resto alla settimana dopo
LUNGHEZZA_SINTESI = 200

NOMI_FORMA = {"fondo_perduto": "fondo perduto", "credito_imposta": "credito d'imposta",
              "finanziamento_agevolato": "finanziamento agevolato", "garanzia": "garanzia", "voucher": "voucher"}


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


def _sintesi(testo: str | None) -> str:
    testo = " ".join((testo or "").split())
    if len(testo) <= LUNGHEZZA_SINTESI:
        return testo
    return testo[:LUNGHEZZA_SINTESI].rsplit(" ", 1)[0].rstrip(",;:.") + "…"


def link_scheda(bando_id: int, impresa_id: int, supporto: bool = False) -> str:
    return f"{utenti.sito_url()}/impresa/bandi/{bando_id}?impresa={impresa_id}" + ("&supporto=1" if supporto else "")


def componi(imp: dict, voci: list[dict]) -> tuple[str, str, str]:
    """(oggetto, testo semplice, html). `imp`: id, nome, codice_disiscrizione. Ogni voce e' un bando (campi del
    catalogo) con in piu' `motivo` (nuovo | in_scadenza), `livello` e `da_verificare` (motivi dell'abbinamento)."""
    nome = imp["nome"]
    in_scadenza = sum(1 for v in voci if v["motivo"] == "in_scadenza")
    oggetto = f"{len(voci)} {'bando adatto' if len(voci) == 1 else 'bandi adatti'} a {nome}"
    if in_scadenza:
        oggetto += f" ({in_scadenza} in scadenza)"
    disiscrizione = f"{utenti.sito_url()}/disiscrizione?codice={imp['codice_disiscrizione']}"
    introduzione = ("ecco i bandi aperti o in arrivo che sembrano adatti alla tua impresa, trovati questa settimana. "
                    "Ogni bando te lo segnaliamo una volta sola.")

    righe = [f"Buongiorno {nome},", "", introduzione, ""]
    css = "font-family:Arial,sans-serif;color:#222"
    parti = [f"<div style='{css};max-width:640px'>",
             f"<p>Buongiorno <b>{html.escape(nome)}</b>,</p>",
             f"<p>{html.escape(introduzione)}</p>"]
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

        colore = "#b42318" if v["motivo"] == "in_scadenza" else "#222"
        parti.append("<div style='border:1px solid #ddd;border-radius:6px;padding:12px;margin:12px 0'>")
        parti.append(f"<div style='font-size:16px;font-weight:bold'><a href='{html.escape(scheda)}' "
                     f"style='color:#1a4d8f;text-decoration:none'>{html.escape(v['titolo'])}</a></div>")
        parti.append(f"<div style='color:#555;margin-top:4px'>{html.escape(v.get('ente') or 'Ente non indicato')} · "
                     f"scadenza <span style='color:{colore}'>{html.escape(scadenza)}</span></div>")
        if aiuto:
            parti.append(f"<div style='margin-top:4px'>Agevolazione: {html.escape(aiuto)}</div>")
        if sintesi:
            parti.append(f"<div style='margin-top:6px'>{html.escape(sintesi)}</div>")
        if dubbi:
            parti.append(f"<div style='margin-top:6px;color:#8a5a00'>{html.escape(dubbi)}</div>")
        parti.append(f"<div style='margin-top:8px'><a href='{html.escape(scheda)}' style='color:#1a4d8f'>Apri la scheda</a>"
                     f" &nbsp;·&nbsp; <a href='{html.escape(supporto)}' style='color:#1a4d8f'>Richiedi supporto per la "
                     f"domanda</a></div></div>")
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


def _gia_segnalati(conn, impresa_id: int) -> set[int]:
    with conn.cursor() as cur:
        cur.execute("SELECT bando_id FROM bandi_segnalati WHERE impresa_id = %s", (impresa_id,))
        return {r["bando_id"] for r in cur.fetchall()}


def scegli_bandi(bandi: list[dict], profilo: dict, segnalati: set[int], oggi: date) -> list[dict]:
    """I bandi pertinenti mai segnalati, con il motivo: compatibili prima, poi da verificare, per scadenza; al massimo 20."""
    from app.abbinamento.profilo import Profilo

    voci = []
    for b, esito in impresa.pertinenti(bandi, Profilo.model_validate(profilo).per_regole(), oggi):
        if b["id"] in segnalati or (b.get("scadenza") and b["scadenza"] < oggi):
            continue
        motivo = "in_scadenza" if b.get("scadenza") and b["scadenza"] <= oggi + timedelta(days=GIORNI_IN_SCADENZA) else "nuovo"
        voci.append({**b, "motivo": motivo, "livello": esito.livello, "da_verificare": esito.da_verificare})
    voci.sort(key=lambda v: (v["livello"] != regole.COMPATIBILE, v.get("scadenza") is None, v.get("scadenza") or date.max))
    return voci[:MASSIMO_BANDI]


def prepara(conn, oggi: date | None = None, solo_stampa: bool = False) -> dict:
    """Prepara l'email della settimana per ogni impresa iscritta (una sola per settimana). Con `solo_stampa` le mostra a
    schermo senza scrivere niente. Se l'approvazione non e' richiesta, le manda subito. Salva (commit) da sola."""
    oggi = oggi or date.today()
    settimana = settimana_iso(oggi)
    conteggi = {"imprese": 0, "senza_bandi": 0, "create": 0, "gia_preparate": 0, "inviate": 0, "errori": 0}
    imprese = _imprese_iscritte(conn)
    conteggi["imprese"] = len(imprese)
    if not imprese:
        return conteggi
    bandi = catalogo.carica_bandi(conn)   # una volta sola per tutte le imprese
    nuove = []
    for imp in imprese:
        voci = scegli_bandi(bandi, imp["profilo"], _gia_segnalati(conn, imp["id"]), oggi)
        if not voci:
            conteggi["senza_bandi"] += 1
            continue
        oggetto, testo, corpo_html = componi(imp, voci)
        if solo_stampa:
            print(f"A: {imp['email']}\nOggetto: {oggetto}\n\n{testo}\n\n{'=' * 70}\n")
            conteggi["create"] += 1
            continue
        elenco_bandi = [{"bando_id": v["id"], "motivo": v["motivo"]} for v in voci]
        with conn.cursor() as cur:
            cur.execute("""INSERT INTO email_imprese (impresa_id, settimana, bandi, oggetto, testo, html)
                           VALUES (%s, %s, %s::jsonb, %s, %s, %s)
                           ON CONFLICT (impresa_id, settimana) DO NOTHING RETURNING id""",
                        (imp["id"], settimana, json.dumps(elenco_bandi), oggetto, testo, corpo_html))
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
    """L'email non parte; i suoi bandi NON diventano segnalati: tornano la settimana dopo."""
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
