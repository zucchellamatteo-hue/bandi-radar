"""Articoli del blog pubblico (07/10/2026, richiesta di Matteo): brevi articoli sui bandi piu' cercati e su qualche
bando di nicchia, per farsi trovare da Google e dai motori di risposta IA e portare alla registrazione.

- Si scrivono nella pagina "Blog" della plancia (permesso "modifiche") o, per le sessioni di Claude, con
  `python -m app.articoli carica FILE.json` (entrano sempre in bozza).
- Solo l'admin pubblica, rimette in bozza o archivia; solo l'admin modifica un articolo gia' pubblicato.
- Il corpo e' Markdown semplice (titoli ##/###, paragrafi, elenchi, grassetto, corsivo, link): qui diventa HTML
  sicuro, senza passare HTML scritto a mano. La sezione "## Domande frequenti" con le domande in "### ..." diventa
  anche il JSON-LD FAQPage della pagina. Una riga `[[calcolatore:NOME]]` mette un calcolatore interattivo scritto da
  noi (app/pubblico/calcolatori.py, 09/10).
- Se l'articolo e' collegato a un bando chiuso o scaduto (vista bandi_situazione) o a una misura nazionale non piu'
  aperta, la pagina pubblica mostra da sola il riquadro "Bando chiuso".

Uso:  python -m app.articoli                 # elenco con stato e collegamenti
      python -m app.articoli carica FILE     # carica articoli da un file JSON (o "-" = da stdin), sempre in bozza
"""

from __future__ import annotations

import html
import json
import os
import re
import unicodedata
from datetime import date

STATI = {"bozza": "bozza", "pubblicato": "pubblicato", "archiviato": "archiviato"}
CAMPI_TESTO = ("titolo", "slug", "sommario", "corpo", "fonti", "bando_id", "misura_id", "autore", "titolo_seo")
CAMPI = CAMPI_TESTO + ("stato",)
SOMMARIO_MAX = 300          # Google mostra circa 155-160 caratteri: oltre si taglia, ma il testo resta valido
TITOLO_SEO_MAX = 70         # titolo breve per Google (09/10): l'ideale e' entro 60 caratteri, marchio compreso
CORPO_MAX = 40000
TITOLO_FAQ = "domande frequenti"
AUTORE_SEGNAPOSTO = "[NOME E COGNOME], commercialista"


class ErroreArticoli(ValueError):
    pass


def autore_predefinito() -> str:
    """Chi firma gli articoli senza autore: il commercialista (AUTORE_ARTICOLI nel .env, es. "Mario Rossi,
    commercialista"); finche' manca, un segnaposto ben visibile da sostituire prima di pubblicare."""
    return os.environ.get("AUTORE_ARTICOLI", "").strip() or AUTORE_SEGNAPOSTO


def crea_slug(testo: str) -> str:
    """'Nuova Sabatini: come funziona' -> 'nuova-sabatini-come-funziona' (niente accenti, al massimo 80 caratteri)."""
    t = unicodedata.normalize("NFKD", testo or "").encode("ascii", "ignore").decode().lower()
    t = re.sub(r"[^a-z0-9]+", "-", t).strip("-")
    return t[:80].rstrip("-")


def _fonti(valore) -> list[dict]:
    """Fonti come lista di {"nome", "url"}; accetta anche il testo della plancia, una fonte per riga: "nome | url"."""
    if valore in (None, ""):
        return []
    if isinstance(valore, str):
        righe = []
        for riga in valore.splitlines():
            if not riga.strip():
                continue
            nome, _, url = riga.rpartition("|") if "|" in riga else ("", "", riga)
            righe.append({"nome": nome.strip(), "url": url.strip()})
        valore = righe
    if not isinstance(valore, list):
        raise ErroreArticoli("Fonti non valide.")
    fonti = []
    for f in valore:
        url = str((f or {}).get("url") or "").strip()
        if not url.startswith(("https://", "http://")):
            raise ErroreArticoli(f"Ogni fonte deve avere un link https:// ({url or 'link mancante'}).")
        fonti.append({"nome": str(f.get("nome") or "").strip() or url, "url": url})
    return fonti


def _controlla(d: dict, nuovo: bool) -> dict:
    v = {k: d[k] for k in CAMPI if k in d}
    for k, massimo, errore in (("titolo", 200, "Scrivi il titolo."), ("sommario", SOMMARIO_MAX, "Scrivi il sommario."),
                               ("corpo", CORPO_MAX, "Scrivi il testo dell'articolo.")):
        if k in v:
            v[k] = " ".join((v[k] or "").split()) if k != "corpo" else (v[k] or "").replace("\r\n", "\n").strip()
            if not v[k]:
                raise ErroreArticoli(errore)
            if len(v[k]) > massimo:
                raise ErroreArticoli(f"{k.capitalize()} troppo lungo (al massimo {massimo} caratteri).")
        elif nuovo:
            raise ErroreArticoli(errore)
    if "slug" in v or nuovo:
        v["slug"] = crea_slug(v.get("slug") or v.get("titolo") or "")
        if not v["slug"]:
            raise ErroreArticoli("Indirizzo (slug) non valido: usa lettere, numeri e trattini.")
    if "fonti" in v:
        v["fonti"] = json.dumps(_fonti(v["fonti"]), ensure_ascii=False)
    if "bando_id" in v:
        b = v["bando_id"]
        if b in (None, ""):
            v["bando_id"] = None
        elif str(b).strip().isdigit():
            v["bando_id"] = int(str(b).strip())
        else:
            raise ErroreArticoli("Numero del bando non valido.")
    if "misura_id" in v:
        v["misura_id"] = (v["misura_id"] or "").strip() or None
        if v["misura_id"]:
            from app import misure

            if not any(m["id"] == v["misura_id"] for m in misure.tutte()):
                raise ErroreArticoli(f"Misura nazionale sconosciuta: {v['misura_id']}.")
    if "autore" in v:
        v["autore"] = " ".join((v["autore"] or "").split()) or None
    if "titolo_seo" in v:
        v["titolo_seo"] = " ".join((v["titolo_seo"] or "").split()) or None
        if v["titolo_seo"] and len(v["titolo_seo"]) > TITOLO_SEO_MAX:
            raise ErroreArticoli(f"Titolo per Google troppo lungo (al massimo {TITOLO_SEO_MAX} caratteri, meglio 50-60).")
    if "stato" in v and v["stato"] not in STATI:
        raise ErroreArticoli("Stato non valido.")
    return v


def _riga(r) -> dict:
    a = dict(r)
    if isinstance(a.get("fonti"), str):
        a["fonti"] = json.loads(a["fonti"])
    return a


def elenco(conn) -> list[dict]:
    with conn.cursor() as cur:
        cur.execute("""SELECT a.*, b.titolo AS bando_titolo FROM articoli a LEFT JOIN bandi b ON b.id = a.bando_id
                       ORDER BY (a.stato = 'bozza') DESC, (a.stato = 'archiviato'), coalesce(a.pubblicato_il, a.aggiornato_il) DESC, a.id DESC""")
        return [_riga(r) for r in cur.fetchall()]


def leggi(conn, articolo_id: int) -> dict | None:
    with conn.cursor() as cur:
        cur.execute("SELECT * FROM articoli WHERE id = %s", (articolo_id,))
        r = cur.fetchone()
    return _riga(r) if r else None


def per_slug(conn, slug: str) -> dict | None:
    with conn.cursor() as cur:
        cur.execute("SELECT * FROM articoli WHERE slug = %s", (slug,))
        r = cur.fetchone()
    return _riga(r) if r else None


def pubblicati(conn) -> list[dict]:
    with conn.cursor() as cur:
        cur.execute("SELECT * FROM articoli WHERE stato = 'pubblicato' ORDER BY pubblicato_il DESC NULLS LAST, id DESC")
        return [_riga(r) for r in cur.fetchall()]


def _slug_libero(conn, slug: str, escluso: int | None = None) -> None:
    with conn.cursor() as cur:
        cur.execute("SELECT id FROM articoli WHERE slug = %s AND id IS DISTINCT FROM %s", (slug, escluso))
        if cur.fetchone():
            raise ErroreArticoli(f"C'è già un articolo con l'indirizzo /blog/{slug}: cambia il titolo o lo slug.")


def _bando_esiste(conn, bando_id: int | None) -> None:
    if bando_id is None:
        return
    with conn.cursor() as cur:
        cur.execute("SELECT 1 FROM bandi WHERE id = %s", (bando_id,))
        if not cur.fetchone():
            raise ErroreArticoli(f"Il bando n. {bando_id} non esiste: controlla il numero.")


def crea(conn, d: dict, chi: str) -> dict:
    """Nuovo articolo, sempre in bozza (lo stato si cambia solo con pubblica/rimetti in bozza/archivia)."""
    v = _controlla({k: d[k] for k in CAMPI_TESTO if k in d}, True)
    _slug_libero(conn, v["slug"])
    _bando_esiste(conn, v.get("bando_id"))
    colonne = list(v)
    with conn.cursor() as cur:
        cur.execute(f"INSERT INTO articoli ({', '.join(colonne)}, creato_da, aggiornato_da) VALUES "
                    f"({', '.join(['%s'] * len(colonne))}, %s, %s) RETURNING *", (*v.values(), chi, chi))
        return _riga(cur.fetchone())


def modifica(conn, articolo_id: int, d: dict, chi: str, admin: bool = False) -> dict:
    """Cambia testo e collegamenti e/o lo stato. Lo stato lo cambia solo l'admin; un articolo pubblicato lo modifica
    solo l'admin (chi scrive lo fa rimettere in bozza). "Aggiornato il" cambia solo se cambia il contenuto."""
    v = _controlla(d, False)
    if not v:
        raise ErroreArticoli("Niente da modificare.")
    prima = leggi(conn, articolo_id)
    if not prima:
        raise ErroreArticoli("Articolo non trovato.")
    if "stato" in v and v["stato"] != prima["stato"] and not admin:
        raise PermissionError("Solo l'amministratore pubblica, rimette in bozza o archivia gli articoli.")
    if prima["stato"] != "bozza" and set(v) - {"stato"} and not admin:
        raise PermissionError("L'articolo è già pubblicato: solo l'amministratore lo modifica (o lo rimette in bozza).")
    if "slug" in v:
        _slug_libero(conn, v["slug"], articolo_id)
    _bando_esiste(conn, v.get("bando_id"))
    insiemi = [f"{k} = %s" for k in v]
    if set(v) - {"stato"}:
        insiemi.append("aggiornato_il = now()")
    if v.get("stato") == "pubblicato":
        insiemi.append("pubblicato_il = coalesce(pubblicato_il, now())")
    with conn.cursor() as cur:
        cur.execute(f"UPDATE articoli SET {', '.join(insiemi)}, aggiornato_da = %s WHERE id = %s RETURNING *",
                    (*v.values(), chi, articolo_id))
        return _riga(cur.fetchone())


def cancella(conn, articolo_id: int, admin: bool = False) -> None:
    a = leggi(conn, articolo_id)
    if not a:
        raise ErroreArticoli("Articolo non trovato.")
    if a["stato"] != "bozza" and not admin:
        raise PermissionError("Si cancellano solo le bozze; gli articoli pubblicati si archiviano.")
    with conn.cursor() as cur:
        cur.execute("DELETE FROM articoli WHERE id = %s", (articolo_id,))


def carica(conn, voci: list[dict], chi: str) -> list[tuple[str, str]]:
    """Carica articoli (es. scritti da una sessione) SEMPRE in bozza; salta quelli con uno slug gia' presente."""
    esiti = []
    for d in voci:
        slug = crea_slug(d.get("slug") or d.get("titolo") or "")
        if per_slug(conn, slug):
            esiti.append((slug, "c'era già: non toccato"))
            continue
        a = crea(conn, d, chi)
        esiti.append((a["slug"], f"caricato in bozza (n. {a['id']}, {parole(a['corpo'])} parole)"))
    return esiti


# --- situazione del bando o della misura collegati ---

def situazione_collegata(conn, articolo: dict, oggi: date | None = None) -> dict | None:
    """Se il bando collegato e' chiuso o scaduto (o la misura non e' piu' aperta): {"cosa", "titolo", "motivo"}.
    Un bando unito a un altro (doppione) si legge dal bando in cui e' confluito."""
    oggi = oggi or date.today()
    if articolo.get("bando_id"):
        with conn.cursor() as cur:
            cur.execute("""SELECT coalesce(u.id, s.id) AS id FROM bandi_situazione s
                           LEFT JOIN bandi_situazione u ON u.id = s.unito_a WHERE s.id = %s""", (articolo["bando_id"],))
            r = cur.fetchone()
            if r:
                cur.execute("""SELECT s.id, s.titolo, s.stato, s.scadenza, s.situazione, s.motivo, b.chiuso_il
                               FROM bandi_situazione s JOIN bandi b USING (id) WHERE s.id = %s""", (r["id"],))
                b = cur.fetchone()
                if b:
                    chiuso = (b["situazione"] in ("chiuso_con_scheda", "scartato_chiuso") or b["stato"] == "chiuso"
                              or (b["scadenza"] is not None and b["scadenza"] < oggi)
                              or (b["chiuso_il"] is not None and b["chiuso_il"] <= oggi))
                    if chiuso:
                        if b["chiuso_il"]:
                            motivo = f"chiuso il {b['chiuso_il']:%d/%m/%Y}"
                        elif b["scadenza"] and b["scadenza"] < oggi:
                            motivo = f"scaduto il {b['scadenza']:%d/%m/%Y}"
                        else:
                            motivo = "le domande non sono più aperte"
                        return {"cosa": "bando", "titolo": b["titolo"], "motivo": motivo}
    if articolo.get("misura_id"):
        from app import misure

        m = next((m for m in misure.tutte() if m["id"] == articolo["misura_id"]), None)
        if m:
            fine = str(m.get("in_vigore_fino_al") or "")[:10]
            if m.get("stato") != "aperto" or (fine and fine < oggi.isoformat()):
                motivo = f"in vigore fino al {date.fromisoformat(fine):%d/%m/%Y}" if fine else "non più aperta"
                return {"cosa": "misura", "titolo": m["nome"], "motivo": motivo}
    return None


# --- Markdown semplice -> HTML sicuro ---

_LINK = re.compile(r"\[([^\]\n]+)\]\(([^)\s]+)\)")
_GRASSETTO = re.compile(r"\*\*(.+?)\*\*")
_CORSIVO = re.compile(r"(?<![\w*])\*(?!\s)(.+?)(?<!\s)\*(?![\w*])")


def _in_linea(testo: str) -> str:
    """Grassetto, corsivo e link su testo gia' protetto (html.escape): nessun tag scritto a mano passa."""
    t = html.escape(testo, quote=True)

    def link(m):
        etichetta, url = m.group(1), html.unescape(m.group(2))
        if url.startswith(("https://", "http://")):
            return (f'<a href="{html.escape(url, quote=True)}" rel="noopener" target="_blank">{etichetta}</a>')
        if url.startswith("/") and not url.startswith("//"):
            return f'<a href="{html.escape(url, quote=True)}">{etichetta}</a>'
        return etichetta                                     # javascript:, data: e simili: resta solo il testo
    t = _LINK.sub(link, t)
    t = _GRASSETTO.sub(r"<strong>\1</strong>", t)
    return _CORSIVO.sub(r"<em>\1</em>", t)


def _testo_semplice(testo: str) -> str:
    """Markdown in linea -> testo semplice (per JSON-LD e /llms.txt)."""
    t = _LINK.sub(r"\1", testo)
    t = _GRASSETTO.sub(r"\1", t)
    return " ".join(_CORSIVO.sub(r"\1", t).split())


_SEPARATORE = re.compile(r"^\|?\s*:?-{2,}:?\s*(\|\s*:?-{2,}:?\s*)*\|?$")


def _righe_tabelle_chiuse(righe: list[str]) -> list[str]:
    """Tabelle scritte senza le barre ai lati (stile GitHub: "Voce | Valore" e sotto "--- | ---"), come le scrivono
    spesso i programmi di scrittura e le IA (09/10): si aggiungono le barre esterne, cosi' diventano tabelle anche loro.
    Una riga con "|" diventa tabella solo se sotto c'e' la riga di separazione: il testo normale con "|" resta testo."""
    fuori: list[str] = []
    in_tabella = False
    for i, riga in enumerate(righe):
        s = riga.strip()
        if not s:
            in_tabella = False
        elif "|" in s and not (s.startswith("|") and s.endswith("|")):
            sotto = righe[i + 1].strip() if i + 1 < len(righe) else ""
            if in_tabella or (_SEPARATORE.match(sotto) and "-" in sotto and "|" in sotto) or (_SEPARATORE.match(s) and "|" in s):
                in_tabella = True
                riga = "| " + s.strip("|").strip() + " |"
        elif s.startswith("|") and s.endswith("|"):
            in_tabella = True
        else:
            in_tabella = False
        fuori.append(riga)
    return fuori


def _blocchi(md: str) -> list[tuple[str, object]]:
    """Il Markdown diviso in blocchi: ("h2"|"h3"|"p", testo), ("ul"|"ol", [voci]) o ("table", [righe di celle]).
    La prima riga di una tabella e' l'intestazione (07/10)."""
    blocchi: list[tuple[str, object]] = []
    paragrafo: list[str] = []

    def chiudi():
        if paragrafo:
            blocchi.append(("p", " ".join(s.strip() for s in paragrafo)))
            paragrafo.clear()
    for riga in _righe_tabelle_chiuse((md or "").replace("\r\n", "\n").split("\n")):
        s = riga.strip()
        m_ol = re.match(r"^\d+[.)]\s+(.*)$", s)
        m_calc = re.fullmatch(r"\[\[calcolatore:([a-z_]+)\]\]", s)
        if not s:
            chiudi()
        elif m_calc:                                      # calcolatore interattivo (app/pubblico/calcolatori.py, 09/10)
            chiudi()
            blocchi.append(("calcolatore", m_calc.group(1)))
        elif s.startswith("|") and s.endswith("|"):     # riga di tabella: | a | b |
            chiudi()
            celle = [c.strip() for c in s.strip("|").split("|")]
            if all(re.fullmatch(r":?-{2,}:?", c) for c in celle if c):
                continue                                  # riga di separazione sotto l'intestazione
            if blocchi and blocchi[-1][0] == "table":
                blocchi[-1][1].append(celle)
            else:
                blocchi.append(("table", [celle]))
        elif s.startswith("### "):
            chiudi()
            blocchi.append(("h3", s[4:].strip()))
        elif s.startswith("## ") or s.startswith("# "):
            chiudi()
            blocchi.append(("h2", s.lstrip("#").strip()))
        elif s[:2] in ("- ", "* ", "• "):
            chiudi()
            if blocchi and blocchi[-1][0] == "ul":
                blocchi[-1][1].append(s[2:].strip())
            else:
                blocchi.append(("ul", [s[2:].strip()]))
        elif m_ol:
            chiudi()
            if blocchi and blocchi[-1][0] == "ol":
                blocchi[-1][1].append(m_ol.group(1).strip())
            else:
                blocchi.append(("ol", [m_ol.group(1).strip()]))
        elif blocchi and blocchi[-1][0] in ("ul", "ol") and not paragrafo and riga[:1] in (" ", "\t"):
            blocchi[-1][1][-1] += " " + s                   # riga che continua la voce dell'elenco
        else:
            paragrafo.append(s)
    chiudi()
    return blocchi


def in_html(md: str) -> str:
    """Markdown semplice -> HTML sicuro. Ai titoli ## si aggiunge un id (ancora) per i link interni."""
    parti = []
    for tipo, contenuto in _blocchi(md):
        if tipo == "h2":
            parti.append(f'<h2 id="{crea_slug(contenuto)}">{_in_linea(contenuto)}</h2>')
        elif tipo == "calcolatore":
            from app.pubblico import calcolatori

            parti.append(calcolatori.html(contenuto))
        elif tipo in ("h3", "p"):
            parti.append(f"<{tipo}>{_in_linea(contenuto)}</{tipo}>")
        elif tipo == "table":
            testa, *corpo = contenuto
            th = "".join(f"<th>{_in_linea(c)}</th>" for c in testa)
            righe = "".join("<tr>" + "".join(f"<td>{_in_linea(c)}</td>" for c in r) + "</tr>" for r in corpo)
            parti.append(f'<div class="tabella"><table><thead><tr>{th}</tr></thead><tbody>{righe}</tbody></table></div>')
        else:
            voci = "".join(f"<li>{_in_linea(v)}</li>" for v in contenuto)
            parti.append(f"<{tipo}>{voci}</{tipo}>")
    return "\n".join(parti)


def domande_frequenti(md: str) -> list[tuple[str, str]]:
    """Le FAQ dell'articolo: nella sezione "## Domande frequenti", ogni "### domanda" con il testo che la segue."""
    faq: list[tuple[str, list[str]]] = []
    dentro = False
    for tipo, contenuto in _blocchi(md):
        if tipo == "h2":
            dentro = contenuto.strip().lower().startswith(TITOLO_FAQ)
        elif dentro and tipo == "h3":
            faq.append((_testo_semplice(contenuto), []))
        elif dentro and faq:
            testo = contenuto if isinstance(contenuto, str) else "; ".join(
                " | ".join(c) if isinstance(c, list) else c for c in contenuto)
            faq[-1][1].append(_testo_semplice(testo))
    return [(d, " ".join(r)) for d, r in faq if r]


def parole(md: str) -> int:
    return len(re.findall(r"\w+", _testo_semplice(re.sub(r"^#+\s*", "", md or "", flags=re.M))))
