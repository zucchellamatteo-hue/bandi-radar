import { useEffect, useState } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";
import { api, BandoRiga, data, nome, Profilo, ProfiloSalvato, RispostaAbbinamento, Sede, Valori } from "../api";
import { Importo, SegnoEsito } from "./Catalogo";
import { usePuo } from "../utente";

// Profili d'impresa ANONIMI (docs/PROFILO_IMPRESA.md) e i bandi che passano le regole, con il motivo.
// Niente nomi, codici fiscali, partite IVA, email: il codice lo sceglie Matteo e la corrispondenza resta da lui.
export const VUOTO: Profilo = {
  codice: "", soggetto: "impresa", da_costituire: false, forma_giuridica: null, sedi: [{ tipo: "legale_e_operativa", regione: null, provincia: null, comune: null }],
  ateco: [], ateco_versione: "2025", attivita: null, dimensione: null, dipendenti: null, fatturato: null, totale_bilancio: null,
  data_costituzione: null, requisiti: {}, temi: [], categorie_spesa: [], importo_progetto: null, note: null,
};

export default function Profili() {
  const { codice } = useParams();
  const vai = useNavigate();
  const [elenco, setElenco] = useState<ProfiloSalvato[]>([]);
  const [valori, setValori] = useState<Valori | null>(null);
  const [p, setP] = useState<Profilo>(VUOTO);
  const [risultato, setRisultato] = useState<RispostaAbbinamento | null>(null);
  const [errore, setErrore] = useState<string | null>(null);
  const [inCorso, setInCorso] = useState(false);

  const modifiche = usePuo("modifiche");
  const ricarica = () => api.profili().then(setElenco);
  useEffect(() => { ricarica(); api.valori().then(setValori); }, []);
  useEffect(() => {
    setRisultato(null); setErrore(null);
    if (!codice) { setP(VUOTO); return; }
    api.profilo(codice).then((r) => { setP({ ...VUOTO, ...r.profilo }); return api.bandiDelProfilo(codice); })
      .then(setRisultato).catch((e) => setErrore(String(e)));
  }, [codice]);

  const cambia = <K extends keyof Profilo>(k: K, v: Profilo[K]) => setP((x) => ({ ...x, [k]: v }));
  const esegui = async (azione: () => Promise<void>) => {
    setInCorso(true); setErrore(null);
    try { await azione(); } catch (e) { setErrore(e instanceof Error ? e.message : String(e)); } finally { setInCorso(false); }
  };
  const salva = () => esegui(async () => {
    if (!p.codice) throw new Error("Scegli un codice interno (per esempio C001).");
    await api.salvaProfilo(p);
    await ricarica();
    if (codice === p.codice) setRisultato(await api.bandiDelProfilo(p.codice)); else vai(`/profili/${encodeURIComponent(p.codice)}`);
  });
  const prova = () => esegui(async () => setRisultato(await api.abbina(p)));
  const cancella = () => esegui(async () => {
    if (!codice || !confirm(`Cancellare il profilo ${codice}?`)) return;
    await api.cancellaProfilo(codice); await ricarica(); vai("/profili");
  });

  return (
    <>
      <h1>Profili d'impresa</h1>
      <div className="avviso">Compila il profilo di un'impresa e guarda i bandi <b>aperti o in arrivo</b> che le regole le abbinano, con il motivo.
        <b> Il profilo è anonimo</b>: solo un codice interno scelto da te, niente nomi, codici fiscali, partite IVA o email (il sistema li rifiuta).
        Per i soci basta il risultato: "impresa femminile sì/no", "giovanile sì/no". Se un dato manca, i bandi che lo chiedono risultano "da verificare".</div>
      <p>{elenco.map((x) => <Link key={x.codice} to={`/profili/${encodeURIComponent(x.codice)}`}
        className={`etichetta-tipo ${x.codice === codice ? "filtro-attivo" : ""}`}>{x.codice}</Link>)}
        {" "}<Link to="/profili">+ nuovo profilo</Link></p>

      <Modulo p={p} cambia={cambia} valori={valori} bloccaCodice={!!codice} />
      <div className="filtri" style={{ marginTop: ".8rem" }}>
        {modifiche && <button onClick={salva} disabled={inCorso}>Salva e abbina</button>}
        <button onClick={prova} disabled={inCorso}>Prova senza salvare</button>
        {modifiche && codice && <button onClick={cancella} disabled={inCorso}>Cancella il profilo</button>}
        {inCorso && <span className="piccolo">Calcolo…</span>}
      </div>
      {errore && <div className="allarme">{errore}</div>}
      {risultato && <Risultati r={risultato} />}
    </>
  );
}

export interface Fasce { dipendenti?: string; fatturato?: string }
export const FASCE_DIPENDENTI: Record<string, string> = { "0": "nessuno", "1-9": "da 1 a 9", "10-49": "da 10 a 49", "50-249": "da 50 a 249", "250+": "250 o più" };
export const FASCE_FATTURATO: Record<string, string> = { fino_2m: "fino a 2 milioni €", "2m-10m": "da 2 a 10 milioni €", "10m-50m": "da 10 a 50 milioni €", oltre_50m: "oltre 50 milioni €" };

// Il modulo del profilo. Con `fasce` (area impresa) niente codice e note, e dipendenti e fatturato a fasce.
export function Modulo({ p, cambia, valori, bloccaCodice, fasce, cambiaFasce }: {
  p: Profilo; cambia: <K extends keyof Profilo>(k: K, v: Profilo[K]) => void; valori: Valori | null; bloccaCodice: boolean;
  fasce?: Fasce; cambiaFasce?: (f: Fasce) => void;
}) {
  const elenco = (campo: string) => ((valori?.[campo] as string[]) || []);
  const numero = (v: string) => (v === "" ? null : Number(v));
  const sede = (i: number, s: Partial<Sede>) => cambia("sedi", p.sedi.map((x, j) => (j === i ? { ...x, ...s } : x)));
  const regioni = Object.entries(valori?.regioni || {}).sort((a, b) => a[1].localeCompare(b[1]));
  const lista = (campo: "temi" | "categorie_spesa", v: string, si: boolean) =>
    cambia(campo, si ? [...p[campo], v] : p[campo].filter((x) => x !== v));
  return (
    <div className="modulo-profilo">
      {!fasce && <fieldset><legend>Codice</legend>
        <label>Codice interno <input value={p.codice} disabled={bloccaCodice} placeholder="es. C001" maxLength={40}
          onChange={(e) => cambia("codice", e.target.value.trim())} /></label>
        <label>Note (niente dati personali)<br /><textarea rows={2} value={p.note || ""} maxLength={500}
          onChange={(e) => cambia("note", e.target.value || null)} /></label>
      </fieldset>}

      <fieldset><legend>Chi è</legend>
        <label>Tipo <select value={p.soggetto || ""} onChange={(e) => cambia("soggetto", (e.target.value || null) as Profilo["soggetto"])}>
          <option value="impresa">impresa</option><option value="libero_professionista">libero professionista</option>
          <option value="ente_terzo_settore">ente del terzo settore</option></select></label>
        <label><input type="checkbox" checked={p.da_costituire} onChange={(e) => cambia("da_costituire", e.target.checked)} /> impresa da costituire</label>
        <label>Forma giuridica <select value={p.forma_giuridica || ""} onChange={(e) => cambia("forma_giuridica", e.target.value || null)}>
          <option value="">non indicata</option>{elenco("forme_giuridiche_ammesse").filter((f) => f !== "altro").map((f) => <option key={f} value={f}>{nome(f)}</option>)}</select></label>
        {!p.da_costituire && <label>Costituita il <input type="date" value={p.data_costituzione || ""} onChange={(e) => cambia("data_costituzione", e.target.value || null)} /></label>}
      </fieldset>

      {fasce && cambiaFasce ? <fieldset><legend>Dimensione</legend>
        <label>Dipendenti <select value={fasce.dipendenti || ""} onChange={(e) => cambiaFasce({ ...fasce, dipendenti: e.target.value || undefined })}>
          <option value="">non indicato</option>{Object.entries(FASCE_DIPENDENTI).map(([k, v]) => <option key={k} value={k}>{v}</option>)}</select></label>
        <label>Fatturato dell'ultimo anno <select value={fasce.fatturato || ""} onChange={(e) => cambiaFasce({ ...fasce, fatturato: e.target.value || undefined })}>
          <option value="">non indicato</option>{Object.entries(FASCE_FATTURATO).map(([k, v]) => <option key={k} value={k}>{v}</option>)}</select></label>
        <label>Classe <select value={p.dimensione || ""} onChange={(e) => cambia("dimensione", (e.target.value || null) as Profilo["dimensione"])}>
          <option value="">calcolala dalle fasce</option>{["micro", "piccola", "media", "grande"].map((d) => <option key={d} value={d}>{d}</option>)}</select></label>
        <div className="piccolo">Se conosci la classe (micro, piccola, media) indicala: è quella che chiedono i bandi.</div>
      </fieldset> : <fieldset><legend>Dimensione</legend>
        <label>Classe <select value={p.dimensione || ""} onChange={(e) => cambia("dimensione", (e.target.value || null) as Profilo["dimensione"])}>
          <option value="">calcolala dai numeri sotto</option>{["micro", "piccola", "media", "grande"].map((d) => <option key={d} value={d}>{d}</option>)}</select></label>
        <label>Dipendenti (ULA) <input type="number" min={0} value={p.dipendenti ?? ""} onChange={(e) => cambia("dipendenti", numero(e.target.value))} /></label>
        <label>Fatturato € <input type="number" min={0} step={1000} value={p.fatturato ?? ""} onChange={(e) => cambia("fatturato", numero(e.target.value))} /></label>
        <label>Totale di bilancio € <input type="number" min={0} step={1000} value={p.totale_bilancio ?? ""} onChange={(e) => cambia("totale_bilancio", numero(e.target.value))} /></label>
      </fieldset>}

      <fieldset><legend>Sedi</legend>
        {p.sedi.map((s, i) => (
          <div key={i} style={{ marginBottom: ".5rem" }}>
            <select value={s.tipo} onChange={(e) => sede(i, { tipo: e.target.value as Sede["tipo"] })}>
              <option value="legale_e_operativa">legale e operativa</option><option value="legale">solo legale</option><option value="operativa">operativa</option></select>{" "}
            <select value={s.regione || ""} onChange={(e) => sede(i, { regione: e.target.value || null, provincia: null })}>
              <option value="">regione</option>{regioni.map(([k, v]) => <option key={k} value={k}>{v}</option>)}</select>{" "}
            <select value={s.provincia || ""} onChange={(e) => sede(i, { provincia: e.target.value || null })}>
              <option value="">prov.</option>{Object.entries(valori?.province || {}).filter(([, r]) => !s.regione || r === s.regione)
                .map(([k]) => k).sort().map((k) => <option key={k} value={k}>{k}</option>)}</select>{" "}
            <input placeholder="comune" value={s.comune || ""} size={14} onChange={(e) => sede(i, { comune: e.target.value || null })} />{" "}
            {p.sedi.length > 1 && <button type="button" onClick={() => cambia("sedi", p.sedi.filter((_, j) => j !== i))}>✗</button>}
          </div>
        ))}
        <button type="button" onClick={() => cambia("sedi", [...p.sedi, { tipo: "operativa", regione: null, provincia: null, comune: null }])}>+ sede</button>
      </fieldset>

      <fieldset><legend>Attività</legend>
        <label>ATECO (il principale per primo, separati da virgola) <input value={p.ateco.join(", ")} placeholder="62.01.00"
          onChange={(e) => cambia("ateco", e.target.value.split(",").map((x) => x.trim()).filter(Boolean))} /></label>
        <label>Versione <select value={p.ateco_versione} onChange={(e) => cambia("ateco_versione", e.target.value as "2007" | "2025")}>
          <option value="2025">ATECO 2025</option><option value="2007">ATECO 2007</option></select></label>
        <label>Cosa fa, a parole<br /><textarea rows={2} value={p.attivita || ""} maxLength={500} onChange={(e) => cambia("attivita", e.target.value || null)} /></label>
      </fieldset>

      <fieldset><legend>Requisiti speciali</legend>
        <div className="piccolo">Lascia "non so" se non lo sai: i bandi che lo chiedono saranno "da verificare".</div>
        {elenco("requisiti_speciali_obbligatori").filter((r) => r !== "altro").map((r) => (
          <label key={r}>{nome(r)}{" "}
            <select value={r in p.requisiti ? (p.requisiti[r] ? "si" : "no") : ""} onChange={(e) => {
              const nuovi = { ...p.requisiti };
              if (e.target.value === "") delete nuovi[r]; else nuovi[r] = e.target.value === "si";
              cambia("requisiti", nuovi);
            }}><option value="">non so</option><option value="si">sì</option><option value="no">no</option></select></label>
        ))}
      </fieldset>

      <fieldset><legend>Cosa vuole fare</legend>
        <div className="scelte">{elenco("temi").filter((t) => t !== "altro").map((t) => (
          <label key={t}><input type="checkbox" checked={p.temi.includes(t)} onChange={(e) => lista("temi", t, e.target.checked)} /> {nome(t)}</label>))}</div>
        <div className="piccolo" style={{ marginTop: ".5rem" }}>Spese previste</div>
        <div className="scelte">{elenco("categorie_spesa").filter((t) => t !== "altro").map((t) => (
          <label key={t}><input type="checkbox" checked={p.categorie_spesa.includes(t)} onChange={(e) => lista("categorie_spesa", t, e.target.checked)} /> {nome(t)}</label>))}</div>
        <label>Importo indicativo del progetto € <input type="number" min={0} step={1000} value={p.importo_progetto ?? ""}
          onChange={(e) => cambia("importo_progetto", numero(e.target.value))} /></label>
      </fieldset>
    </div>
  );
}

function Risultati({ r }: { r: RispostaAbbinamento }) {
  const gruppo = (livello: string) => r.bandi.filter((b) => b.esito.livello === livello);
  const dubbi = gruppo("da_verificare");
  const quasi = dubbi.filter((b) => !b.esito.fuori_zona && b.esito.dubbi_pesanti === 0);
  const importanti = dubbi.filter((b) => !b.esito.fuori_zona && b.esito.dubbi_pesanti > 0);
  const altrove = dubbi.filter((b) => b.esito.fuori_zona);
  return (
    <>
      <h2>Bandi aperti o in arrivo per questo profilo</h2>
      <p><b>{r.conteggi.compatibile}</b> ✓ compatibili · <b>{quasi.length}</b> quasi compatibili · {importanti.length} con dubbi importanti
        {" "}· {altrove.length} di altre regioni · {r.conteggi.escluso} ✗ esclusi</p>
      <Gruppo titolo="✓ Compatibili" bandi={gruppo("compatibile")} aperto />
      <Gruppo titolo="? Quasi compatibili: solo dettagli da leggere nel bando (soglie, età, forma, scheda su sintesi)" bandi={quasi} aperto />
      <Gruppo titolo="? Da verificare, con dubbi importanti (territorio, beneficiari, settore, dimensione, requisiti)" bandi={importanti} />
      <Gruppo titolo="? Di altre regioni: servirebbe una sede o un progetto lì" bandi={altrove} />
      <Gruppo titolo="✗ Esclusi, con il motivo" bandi={gruppo("escluso")} />
      <Gruppo titolo="In disparte: bandi senza il testo ufficiale (scheda fatta su una sintesi), non proponibili"
        bandi={(r.in_disparte || []).filter((b) => b.esito.livello !== "escluso")} />
    </>
  );
}

function Gruppo({ titolo, bandi, aperto }: { titolo: string; bandi: BandoRiga[]; aperto?: boolean }) {
  const [quanti, setQuanti] = useState(50);
  if (!bandi.length) return <p className="piccolo">{titolo}: nessuno.</p>;
  return (
    <details open={aperto}>
      <summary><b>{titolo}</b> ({bandi.length})</summary>
      <table>
        <tbody>{bandi.slice(0, quanti).map((b) => (
          <tr key={b.id}>
            <td><SegnoEsito livello={b.esito.livello} /></td>
            <td><Link to={`/bandi/${b.id}`} className="titolo-annuncio">{b.titolo}</Link>
              <div className="piccolo">{b.ente}</div>
              <Motivi classe="esclusioni" voci={b.esito.esclusioni} segno="✗" />
              <Motivi classe="da_verificare" voci={b.esito.da_verificare} segno="?" />
              <Motivi classe="a_favore" voci={b.esito.punti_a_favore} segno="+" />
              <Motivi classe="da_controllare" voci={b.esito.da_controllare} segno="•" /></td>
            <td><span className={`stato-bando ${b.stato || "non_noto"}`}>{b.stato ? nome(b.stato) : "stato non noto"}</span>
              {b.scadenza && <div className="scadenza">scade il {data(b.scadenza)}</div>}</td>
            <td>{(b.tipi_agevolazione || []).map((t) => <span key={t} className="etichetta-tipo">{nome(t)}</span>)}<Importo b={b} /></td>
          </tr>
        ))}</tbody>
      </table>
      {bandi.length > quanti && <button onClick={() => setQuanti(quanti + 100)}>Mostra altri ({bandi.length - quanti})</button>}
    </details>
  );
}

export function Motivi({ classe, voci, segno }: { classe: string; voci: string[]; segno: string }) {
  if (!voci.length) return null;
  return <ul className={`motivi ${classe}`}>{voci.map((v) => <li key={v}>{segno} {v}</li>)}</ul>;
}
