import { useEffect, useState } from "react";
import { Link, useNavigate, useParams, useSearchParams } from "react-router-dom";
import { Abbonamento as TipoAbbonamento, DatiFatturazione, api, BandoImpresa, data, euro, Impresa, nome, NOMI_STATO_ABBONAMENTO, NOMI_STATO_RICHIESTA, Profilo, RichiestaSupporto, SchedaRidotta, Valori, VistaImpresa, MisuraPerProfilo } from "../api";
import { Importo } from "./Catalogo";
import { Fasce, Modulo, Motivi, VUOTO } from "./Profili";
import Giudizio from "../Giudizio";
import { SiSommaCon } from "./Misure";
import { Fornitori } from "./Bando";

// Area impresa (05/10/2026): le imprese dell'utente, i bandi adatti (mai gli esclusi), la scheda ridotta e la richiesta
// di supporto. Niente pagine di lavoro (fonti, annunci, lavorazione).

export function MieiBandi() {
  const [imprese, setImprese] = useState<Impresa[] | null>(null);
  const [parametri, setParametri] = useSearchParams();
  const [r, setR] = useState<VistaImpresa | null>(null);
  const [errore, setErrore] = useState<string | null>(null);
  useEffect(() => { api.mieImprese().then(setImprese).catch((e) => setErrore(String(e.message || e))); }, []);
  const scelta = Number(parametri.get("impresa")) || imprese?.[0]?.id;
  useEffect(() => {
    if (!scelta) return;
    setR(null);
    api.bandiImpresa(scelta).then(setR).catch((e) => setErrore(String(e.message || e)));
  }, [scelta]);

  if (errore) return <div className="allarme">{errore}</div>;
  if (!imprese) return <div className="caricamento">Caricamento…</div>;
  if (!imprese.length) return (
    <>
      <h1>Benvenuto in bandinQiaro</h1>
      <div className="avviso">Per vedere i bandi adatti, descrivi prima la tua impresa: dove ha le sedi, cosa fa (codice ATECO),
        quanto è grande. Bastano pochi minuti.</div>
      <p><Link to="/impresa/imprese/nuova"><button className="primario">Descrivi la tua impresa</button></Link></p>
    </>
  );
  return (
    <>
      <h1>I bandi per la tua impresa</h1>
      {imprese.length > 1 && <div className="filtri scegli-impresa">
        {imprese.map((i) => <button key={i.id} className={i.id === scelta ? "primario" : ""}
          onClick={() => setParametri({ impresa: String(i.id) })}>{i.nome}</button>)}</div>}
      {!r ? <div className="caricamento">Cerco i bandi…</div> : <>
        {r.bloccato && <div className="avviso"><b>La prova gratuita è finita.</b> Abbonati per vedere i bandi e ricevere l'email
          settimanale. <Link to="/impresa/abbonamento"><button className="primario">Abbonati</button></Link></div>}
        <VistaBandi r={r} scheda={(b) => `/impresa/bandi/${b.id}?impresa=${r.impresa.id}`}
          supporto={(b) => `/impresa/bandi/${b.id}?impresa=${r.impresa.id}&supporto=apri`}
          misure="/impresa/misure" profilo={`/impresa/imprese/${r.impresa.id}`} />
      </>}
    </>
  );
}

// La stessa pagina vista da Matteo per qualunque profilo (07/10): /profili/:codice/impresa.
export function VistaImpresaProfilo() {
  const { codice } = useParams();
  const [r, setR] = useState<VistaImpresa | null>(null);
  const [errore, setErrore] = useState<string | null>(null);
  useEffect(() => { if (codice) api.vistaImpresaProfilo(codice).then(setR).catch((e) => setErrore(String(e.message || e))); }, [codice]);
  if (errore) return <div className="allarme">{errore}</div>;
  return (
    <>
      <p><Link to={`/profili/${encodeURIComponent(codice || "")}`}>← Profilo {codice}</Link></p>
      <h1>{r ? `Come la vede l'impresa: ${r.impresa.nome}` : "Come la vede l'impresa"}</h1>
      <p className="piccolo">È la pagina "I miei bandi" dell'area impresa, calcolata per questo profilo. Le schede si aprono nella
        pagina completa del bando; la richiesta di supporto la fa l'impresa dalla sua area.</p>
      {!r ? <div className="caricamento">Cerco i bandi…</div> :
        <VistaBandi r={r} scheda={(b) => `/bandi/${b.id}`} misure="/misure" profilo={`/profili/${encodeURIComponent(codice || "")}`} />}
    </>
  );
}

type FiltroTipo = "" | "fondo_perduto" | "credito_imposta" | "finanziamento_agevolato" | "garanzia" | "altro";
const TIPI_FILTRO: [FiltroTipo, string][] = [["", "Tutte le agevolazioni"], ["fondo_perduto", "Fondo perduto e voucher"],
  ["credito_imposta", "Credito d'imposta"], ["finanziamento_agevolato", "Finanziamento agevolato"], ["garanzia", "Garanzia"], ["altro", "Altre"]];
const SCADENZE_FILTRO: [string, string][] = [["", "Qualsiasi scadenza"], ["15", "Entro 15 giorni"], ["30", "Entro 30 giorni"],
  ["90", "Entro 3 mesi"], ["senza", "Senza scadenza (a sportello)"]];

function passaTipo(b: BandoImpresa, t: FiltroTipo): boolean {
  if (!t) return true;
  if (t === "fondo_perduto") return b.fondo_perduto;
  const tipi = (b.tipi_agevolazione && b.tipi_agevolazione.length ? b.tipi_agevolazione : [b.tipo_agevolazione]).filter(Boolean) as string[];
  if (t === "altro") return !b.fondo_perduto && !tipi.some((x) => ["credito_imposta", "finanziamento_agevolato", "garanzia"].includes(x));
  return tipi.includes(t);
}

function passaScadenza(b: BandoImpresa, s: string): boolean {
  if (!s) return true;
  if (s === "senza") return !b.scadenza;
  return b.giorni_alla_scadenza != null && b.giorni_alla_scadenza >= 0 && b.giorni_alla_scadenza <= Number(s);
}

// Il cuore della pagina: riepilogo, filtri, bandi adatti, bandi da valutare (e di altre regioni), misure nazionali.
export function VistaBandi({ r, scheda, supporto, misure, profilo }: {
  r: VistaImpresa; scheda: (b: BandoImpresa) => string; supporto?: (b: BandoImpresa) => string; misure: string; profilo: string;
}) {
  const [tipo, setTipo] = useState<FiltroTipo>("");
  const [scadenza, setScadenza] = useState("");
  const filtrati = r.bandi.filter((b) => passaTipo(b, tipo) && passaScadenza(b, scadenza));
  const gruppo = (g: string) => filtrati.filter((b) => b.gruppo === g);
  const adatti = gruppo("adatti"), daValutare = gruppo("da_valutare"), altrove = gruppo("altre_regioni");
  const filtro = !!(tipo || scadenza);
  // Quanti bandi da valutare si chiarirebbero completando il profilo (motivi che chiedono un dato: "indica ...").
  const daCompletare = r.bandi.filter((b) => b.gruppo !== "adatti" && b.da_verificare_semplici.some((m) => m.startsWith("indica"))).length;
  const c = r.conteggi;
  const inScadenza = String(r.giorni_in_scadenza);
  return (
    <>
      <div className="riepilogo-impresa">
        <a href="#adatti" className="voce adatti"><span className="numero">{c.adatti}</span> {c.adatti === 1 ? "bando adatto" : "bandi adatti"}</a>
        <a href="#da-valutare" className="voce da-valutare"><span className="numero">{c.da_valutare + c.altre_regioni}</span> da valutare</a>
        <button className={`voce in-scadenza ${scadenza === inScadenza ? "attiva" : ""}`} title={`Mostra solo i bandi che scadono entro ${inScadenza} giorni`}
          onClick={() => setScadenza(scadenza === inScadenza ? "" : inScadenza)}>
          <span className="numero">{c.in_scadenza}</span> in scadenza</button>
        <div className="voce nuovi"><span className="numero">{c.nuovi}</span> {c.nuovi === 1 ? "nuovo" : "nuovi"} in {r.giorni_nuovo} giorni</div>
      </div>
      <p className="piccolo">Bandi aperti o in arrivo. "In scadenza" vuol dire entro {r.giorni_in_scadenza} giorni. {r.avvertenza}</p>
      {daCompletare > 0 && <div className="avviso completa-profilo">Completando il profilo (codice ATECO, dimensione, data di costituzione…)
        si chiariscono <b>{daCompletare}</b> bandi da valutare. <Link to={profilo}>Completa il profilo</Link></div>}

      <div className="filtri filtri-impresa">
        <select value={tipo} onChange={(e) => setTipo(e.target.value as FiltroTipo)} aria-label="Tipo di agevolazione">
          {TIPI_FILTRO.map(([v, t]) => <option key={v} value={v}>{t}</option>)}</select>
        <select value={scadenza} onChange={(e) => setScadenza(e.target.value)} aria-label="Scadenza">
          {SCADENZE_FILTRO.map(([v, t]) => <option key={v} value={v}>{t}</option>)}</select>
        {filtro && <button onClick={() => { setTipo(""); setScadenza(""); }}>Togli i filtri</button>}
        {filtro && <span className="piccolo">{filtrati.length} bandi su {r.bandi.length}</span>}
      </div>

      <section id="adatti">
        <h2 className="titolo-gruppo adatti">Bandi adatti <span className="conta">{adatti.length}</span></h2>
        <p className="piccolo">Tutti i requisiti che il bando chiede sono verificati sui dati della tua impresa.</p>
        {adatti.length ? <Card bandi={adatti} scheda={scheda} supporto={supporto} /> :
          <div className="vuoto">{filtro ? "Nessun bando adatto con questi filtri." :
            r.bandi.length ? <>Nessun bando ha tutti i requisiti verificati in questo momento. Guarda quelli da valutare qui sotto:
              spesso basta un dato in più nel profilo per saperlo. <Link to={profilo}>Completa il profilo</Link></> :
            "Per ora nessun bando aperto per la tua impresa. Ogni lunedì controlliamo i bandi nuovi e te li scriviamo."}</div>}
      </section>

      <section id="da-valutare">
        <h2 className="titolo-gruppo da-valutare">Bandi potenzialmente applicabili <span className="conta">{daValutare.length + altrove.length}</span></h2>
        <p className="piccolo">Da valutare: c'è un requisito da controllare nel bando o un dato che manca nel profilo. Sotto ogni bando il motivo.</p>
        {daValutare.length ? <Card bandi={daValutare} scheda={scheda} supporto={supporto} /> :
          <div className="vuoto">{filtro ? "Nessun bando da valutare con questi filtri." : "Nessun bando da valutare nella tua zona."}</div>}
        {altrove.length > 0 && <details className="altre-regioni">
          <summary>Bandi di altre regioni ({altrove.length}): servirebbe una sede o il progetto lì</summary>
          <Card bandi={altrove} scheda={scheda} supporto={supporto} />
        </details>}
      </section>

      <MisureUtili m={r.misure} base={misure} />
    </>
  );
}

function Scadenza({ b }: { b: BandoImpresa }) {
  if (b.stato === "in_arrivo" && b.data_apertura)
    return <div className="scadenza-card">Apre il {data(b.data_apertura)}{b.scadenza ? ` · scade il ${data(b.scadenza)}` : ""}</div>;
  if (!b.scadenza) return <div className="scadenza-card senza">Nessuna scadenza indicata{b.modalita_selezione ? ` · ${nome(b.modalita_selezione)}` : ""}</div>;
  const g = b.giorni_alla_scadenza;
  const quando = g == null ? "" : g === 0 ? " · scade oggi" : g === 1 ? " · scade domani" : g > 0 && g <= 60 ? ` · tra ${g} giorni` : "";
  return <div className={`scadenza-card ${b.in_scadenza ? "vicina" : ""}`}>Scade il {data(b.scadenza)}{b.ora_scadenza ? ` ore ${b.ora_scadenza.slice(0, 5)}` : ""}{quando}</div>;
}

function Card({ bandi, scheda, supporto }: { bandi: BandoImpresa[]; scheda: (b: BandoImpresa) => string; supporto?: (b: BandoImpresa) => string }) {
  const [quanti, setQuanti] = useState(12);
  return (
    <>
      <div className="card-griglia">{bandi.slice(0, quanti).map((b) => (
        <article key={b.id} className={`card-bando ${b.gruppo}`}>
          {(b.nuovo || b.in_scadenza || b.stato === "in_arrivo") && <div className="card-segni">
            {b.in_scadenza && <span className="segno-card in-scadenza">In scadenza</span>}
            {b.nuovo && <span className="segno-card nuovo">Nuovo</span>}
            {b.stato === "in_arrivo" && <span className="segno-card in-arrivo">In arrivo</span>}
          </div>}
          <h3><Link to={scheda(b)} className="titolo-annuncio">{b.titolo}</Link></h3>
          <div className="card-ente">{b.ente || "Ente non indicato"}{b.territorio ? ` · ${b.territorio.length > 70 ? b.territorio.slice(0, 70) + "…" : b.territorio}` : ""}</div>
          <div className={`card-agevolazione ${b.fondo_perduto ? "fp" : ""}`}>{b.agevolazione}
            {b.secondo_piano && <span className="piccolo"> · senza contributo in denaro</span>}</div>
          <Scadenza b={b} />
          <div className={`card-motivo ${b.esito.livello}`}>
            <span className="segno">{b.esito.livello === "compatibile" ? "✓" : "?"}</span>
            <span>{b.motivo}{b.da_verificare_semplici.length > 1 &&
              <span className="piccolo"> · e {b.da_verificare_semplici.length - 1} {b.da_verificare_semplici.length === 2 ? "altro punto" : "altri punti"} da controllare</span>}</span>
          </div>
          <div className="card-azioni">
            <Link to={scheda(b)}><button>Apri la scheda</button></Link>
            {supporto && <Link to={supporto(b)}><button className="primario">Richiedi supporto</button></Link>}
          </div>
        </article>))}</div>
      {bandi.length > quanti && <p><button className="mostra-altri" onClick={() => setQuanti(quanti + 24)}>
        Mostra altri {Math.min(24, bandi.length - quanti)} (ne restano {bandi.length - quanti})</button></p>}
    </>
  );
}

function beneficio(m: MisuraPerProfilo): string | null {
  if (m.beneficio_min == null || m.beneficio_max == null) return null;
  return m.beneficio_min === m.beneficio_max ? `circa ${m.beneficio_min}% della spesa` : `dal ${m.beneficio_min}% al ${m.beneficio_max}% della spesa`;
}

function MisureUtili({ m, base }: { m: VistaImpresa["misure"]; base: string }) {
  const [tutte, setTutte] = useState(false);
  if (!m.misure.length) return null;
  const elenco = tutte ? m.misure : m.misure.slice(0, 6);
  return (
    <section id="misure">
      <h2 className="titolo-gruppo misure">Agevolazioni nazionali sempre aperte <span className="conta">{m.misure.length}</span></h2>
      <p className="piccolo">Non sono bandi: sono misure nazionali (crediti d'imposta, contributi a sportello) adatte alla tua impresa, che
        spesso si sommano ai bandi. {m.tipo ? <>Gli esempi sono per un'impresa simile alla tua: <b>{m.tipo.nome.toLowerCase()}</b>.</> :
        "Indica il codice ATECO nel profilo per vedere esempi pratici per il tuo tipo di impresa."}</p>
      <div className="card-griglia">{elenco.map((x) => (
        <article key={x.id} className="card-bando misura">
          {x.esempio && <div className="card-segni"><span className={`interesse ${x.esempio.interesse}`}>interesse {x.esempio.interesse}</span></div>}
          <h3><Link to={`${base}/${x.id}`} className="titolo-misura">{x.nome}</Link></h3>
          <div className="card-ente">{x.ente}</div>
          {beneficio(x) && <div className="card-agevolazione fp">{nome(x.tipo)}: {beneficio(x)}</div>}
          <p className="card-esempio">{x.esempio ? <><b>Esempio:</b> {x.esempio.testo.length > 260 ? x.esempio.testo.slice(0, 260) + "…" : x.esempio.testo}</>
            : x.sintesi.length > 220 ? x.sintesi.slice(0, 220) + "…" : x.sintesi}</p>
          <div className="card-azioni"><Link to={`${base}/${x.id}`}><button>Apri la misura</button></Link></div>
        </article>))}</div>
      {m.misure.length > 6 && !tutte && <p><button className="mostra-altri" onClick={() => setTutte(true)}>Mostra tutte ({m.misure.length})</button></p>}
    </section>
  );
}

export function SchedaImpresa() {
  const { id } = useParams();
  const [parametri] = useSearchParams();
  const [b, setB] = useState<SchedaRidotta | null>(null);
  const [errore, setErrore] = useState<string | null>(null);
  // supporto=1 arriva dall'email del lunedi', supporto=apri dal pulsante "Richiedi supporto" della pagina dei bandi.
  const [supporto, setSupporto] = useState(["1", "apri"].includes(parametri.get("supporto") || ""));
  useEffect(() => {
    if (b && supporto && parametri.get("supporto")) document.querySelector(".riquadro.supporto")?.scrollIntoView({ block: "center" });
  }, [b]);
  useEffect(() => { if (id) api.schedaImpresa(id).then(setB).catch((e) => setErrore(String(e.message || e))); }, [id]);
  if (errore) return <><div className="allarme">{errore}</div><p><Link to="/impresa">← I miei bandi</Link></p></>;
  if (!b) return <div className="caricamento">Caricamento…</div>;
  const impresaId = Number(parametri.get("impresa")) || b.imprese[0].id;
  const perQuale = b.imprese.find((i) => i.id === impresaId) || b.imprese[0];
  const giorni = b.scadenza
    ? Math.round((new Date(b.scadenza + "T00:00:00").getTime() - new Date(new Date().toDateString()).getTime()) / 86400000) : null;
  return (
    <>
      <p><Link to={`/impresa?impresa=${perQuale.id}`}>← I miei bandi</Link></p>
      <h1>{b.titolo}</h1>
      <p className="card-ente"><span className={`stato-bando ${b.stato || "non_noto"}`}>{b.stato ? nome(b.stato) : "stato non noto"}</span>
        {" "}{b.ente}{b.territorio ? ` · ${b.territorio}` : ""}</p>
      <div className="scheda-chiave">
        <div><div className="etichetta">Agevolazione</div><div className="valore">{b.agevolazione || "da leggere nel bando"}</div></div>
        <div><div className="etichetta">Scadenza</div>
          <div className={`valore ${giorni != null && giorni >= 0 && giorni <= 15 ? "vicina" : ""}`}>
            {b.scadenza ? <>{data(b.scadenza)}{b.ora_scadenza ? ` ore ${b.ora_scadenza.slice(0, 5)}` : ""}
              {giorni != null && giorni >= 0 && giorni <= 60 && <span className="piccolo"> ({giorni === 0 ? "oggi" : giorni === 1 ? "domani" : `tra ${giorni} giorni`})</span>}</>
              : "nessuna scadenza scritta"}</div>
          {b.data_apertura && <div className="piccolo">apre il {data(b.data_apertura)}{b.ora_apertura ? ` ore ${b.ora_apertura.slice(0, 5)}` : ""}</div>}</div>
        <div><div className="etichetta">Domanda</div><div className="valore">{b.modalita_selezione ? nome(b.modalita_selezione) : "–"}</div>
          {b.url && <a href={b.url} target="_blank" rel="noreferrer" className="piccolo">bando ufficiale ↗</a>}</div>
      </div>
      <div className={`esito-impresa ${perQuale.esito.livello}`}>
        <b>{perQuale.esito.livello === "compatibile" ? `✓ Adatto a ${perQuale.nome}` : `? Da valutare per ${perQuale.nome}`}</b>
        {perQuale.esito.livello === "compatibile" ? <div>{perQuale.motivo || "In base ai dati che hai indicato il bando è adatto."}</div>
          : <ul>{(perQuale.da_verificare_semplici || perQuale.esito.da_verificare).map((m) => <li key={m}>{m}</li>)}</ul>}
      </div>
      <div className="avviso">{b.avvertenza}</div>

      <div className={`riquadro supporto ${supporto ? "aperto" : ""}`}>
        {!supporto ? <>
          <b>Vuoi presentare la domanda?</b> I nostri consulenti verificano i requisiti e preparano la pratica con te.{" "}
          <button className="primario" onClick={() => setSupporto(true)}>Richiedi supporto per la domanda</button>
        </> : <ModuloSupporto bandoId={b.id} imprese={b.imprese} impresaId={perQuale.id} origine={parametri.get("supporto") === "1" ? "email" : "piattaforma"} />}
      </div>

      {(perQuale.esito.punti_a_favore.length > 0 || perQuale.esito.da_controllare.length > 0) && <h2>Da sapere per {perQuale.nome}</h2>}
      <Motivi classe="a_favore" voci={perQuale.esito.punti_a_favore} segno="+" />
      <Motivi classe="da_controllare" voci={perQuale.esito.da_controllare} segno="•" />

      <h2>In breve</h2>
      {b.sintesi && <p className="testo-lungo">{b.sintesi}</p>}
      <div className="scheda-griglia">
        <div className="riquadro"><div className="etichetta">Agevolazione</div>
          {(b.tipi_agevolazione || [b.tipo_agevolazione]).filter(Boolean).map((t) => <span key={String(t)} className="etichetta-tipo">{nome(String(t))}</span>)}
          <Importo b={b as never} /></div>
        {b.fondo_perduto_massimo != null && <div className="riquadro"><div className="etichetta">Fondo perduto fino a</div><div>{euro(b.fondo_perduto_massimo)}</div></div>}
        {b.finanziamento_massimo != null && <div className="riquadro"><div className="etichetta">Prestito fino a</div><div>{euro(b.finanziamento_massimo)}</div></div>}
        {(b.spesa_minima != null || b.spesa_massima != null) && <div className="riquadro"><div className="etichetta">Progetto ammesso</div>
          <div>{b.spesa_minima != null ? `da ${euro(b.spesa_minima)}` : ""}{b.spesa_massima != null ? ` a ${euro(b.spesa_massima)}` : ""}</div></div>}
        {b.dotazione != null && <div className="riquadro"><div className="etichetta">Dotazione del bando</div><div>{euro(b.dotazione)}</div></div>}
      </div>
      {b.forma_incentivo?.righe?.length ? <><h3>Forma dell'incentivo</h3><ul>{b.forma_incentivo.righe.map((r, i) => (
        <li key={i}><b>{r.per_chi}</b>: {r.forme.map((f) => `${nome(f.forma)}${f.percentuale != null ? ` ${f.percentuale}%` : ""}${f.massimale != null ? ` fino a ${euro(f.massimale)}` : ""}`).join(" + ")}</li>))}</ul></> : null}
      <SiSommaCon misure={b.misure_cumulabili} base="/impresa/misure" />
      {b.a_chi_si_rivolge && <><h3>A chi si rivolge</h3><p className="testo-lungo">{b.a_chi_si_rivolge}</p></>}
      {b.cosa_finanzia && <><h3>Cosa finanzia</h3><p className="testo-lungo">{b.cosa_finanzia}</p></>}
      {b.requisiti && <><h3>Cosa serve</h3><p className="testo-lungo">{b.requisiti}</p></>}
      <Fornitori v={b.vincoli_spese} />
      {b.documenti_ufficiali.length > 0 && <><h3>Documenti ufficiali</h3><ul>{b.documenti_ufficiali.map((d) =>
        <li key={d.url}><a href={d.url} target="_blank" rel="noreferrer">{d.nome} ↗</a></li>)}</ul></>}
      <Giudizio bandoId={b.id} admin={false} perImpresa />
    </>
  );
}

function ModuloSupporto({ bandoId, imprese, impresaId, origine }: {
  bandoId: number; imprese: SchedaRidotta["imprese"]; impresaId: number; origine: "piattaforma" | "email";
}) {
  const [quale, setQuale] = useState(impresaId);
  const [messaggio, setMessaggio] = useState("");
  const [esito, setEsito] = useState<string | null>(null);
  const [errore, setErrore] = useState<string | null>(null);
  const invia = async () => {
    setErrore(null);
    try { setEsito((await api.richiediSupporto({ impresa_id: quale, bando_id: bandoId, messaggio, origine })).messaggio); }
    catch (e) { setErrore(e instanceof Error ? e.message : String(e)); }
  };
  if (esito) return <div><b>✓ {esito}</b> <Link to="/impresa/richieste">Le mie richieste</Link></div>;
  return (
    <div>
      <b>Richiedi supporto per la domanda</b>
      <p className="piccolo">Ti ricontatta un nostro consulente. Il servizio è a successo: si paga solo se il contributo viene concesso.</p>
      {imprese.length > 1 && <p><select value={quale} onChange={(e) => setQuale(Number(e.target.value))}>
        {imprese.map((i) => <option key={i.id} value={i.id}>{i.nome}</option>)}</select></p>}
      <textarea rows={3} placeholder="Cosa vorresti fare con questo bando? (facoltativo)" value={messaggio} onChange={(e) => setMessaggio(e.target.value)} />
      {errore && <div className="allarme">{errore}</div>}
      <p><button className="primario" onClick={invia}>Invia la richiesta</button></p>
    </div>
  );
}

export function MieImprese() {
  const [imprese, setImprese] = useState<Impresa[] | null>(null);
  useEffect(() => { api.mieImprese().then(setImprese); }, []);
  if (!imprese) return <div className="caricamento">Caricamento…</div>;
  return (
    <>
      <h1>Le mie imprese</h1>
      <table>
        <thead><tr><th>Impresa</th><th>Sedi</th><th>Email settimanale</th><th></th></tr></thead>
        <tbody>{imprese.map((i) => (
          <tr key={i.id}>
            <td><b>{i.nome}</b><div className="piccolo">{(i.profilo.ateco || []).join(", ") || "ATECO non indicato"}</div></td>
            <td>{i.sedi}</td>
            <td>{i.email_settimanale ? "sì" : "no"}</td>
            <td><Link to={`/impresa/imprese/${i.id}`}>Modifica</Link> · <Link to={`/impresa?impresa=${i.id}`}>Vedi i bandi</Link></td>
          </tr>))}</tbody>
      </table>
      <p><Link to="/impresa/imprese/nuova"><button>+ Aggiungi un'impresa</button></Link></p>
    </>
  );
}

export function ModuloImpresa() {
  const { id } = useParams();
  const vai = useNavigate();
  const nuova = !id || id === "nuova";
  const [valori, setValori] = useState<Valori | null>(null);
  const [nomeImpresa, setNomeImpresa] = useState("");
  const [p, setP] = useState<Profilo>({ ...VUOTO, codice: "impresa" });
  const [fasce, setFasce] = useState<Fasce>({});
  const [emailSettimanale, setEmailSettimanale] = useState(true);
  const [errore, setErrore] = useState<string | null>(null);
  useEffect(() => { api.valori().then(setValori); }, []);
  useEffect(() => {
    if (nuova) return;
    api.mieImprese().then((elenco) => {
      const i = elenco.find((x) => x.id === Number(id));
      if (!i) { setErrore("Impresa non trovata."); return; }
      setNomeImpresa(i.nome); setP({ ...VUOTO, ...i.profilo }); setFasce(i.fasce || {}); setEmailSettimanale(i.email_settimanale);
    });
  }, [id]);
  const cambia = <K extends keyof Profilo>(k: K, v: Profilo[K]) => setP((x) => ({ ...x, [k]: v }));
  const salva = async () => {
    setErrore(null);
    try {
      const r = nuova ? await api.creaImpresa({ nome: nomeImpresa, profilo: p, fasce })
        : await api.modificaImpresa(Number(id), { nome: nomeImpresa, profilo: p, fasce, email_settimanale: emailSettimanale });
      vai(`/impresa?impresa=${r.id}`);
    } catch (e) { setErrore(e instanceof Error ? e.message : String(e)); }
  };
  const cancella = async () => {
    if (!confirm(`Togliere ${nomeImpresa} da bandinQiaro?`)) return;
    await api.cancellaImpresa(Number(id)); vai("/impresa/imprese");
  };
  return (
    <>
      <h1>{nuova ? "Descrivi la tua impresa" : nomeImpresa}</h1>
      <div className="avviso">Questi dati servono solo a scegliere i bandi adatti. Se un dato non lo sai, lascialo vuoto: i bandi che lo
        chiedono saranno "da verificare", non scartati. Il nome dell'impresa resta separato dal resto e non viene mai mandato a servizi esterni.</div>
      <div className="modulo-profilo">
        <fieldset><legend>Impresa</legend>
          <label>Nome o ragione sociale <input value={nomeImpresa} maxLength={200} onChange={(e) => setNomeImpresa(e.target.value)} /></label>
          {!nuova && <label><input type="checkbox" checked={emailSettimanale} onChange={(e) => setEmailSettimanale(e.target.checked)} /> ricevi l'email settimanale con i bandi nuovi</label>}
        </fieldset>
      </div>
      <Modulo p={p} cambia={cambia} valori={valori} bloccaCodice fasce={fasce} cambiaFasce={setFasce} />
      {errore && <div className="allarme">{errore}</div>}
      <div className="filtri" style={{ marginTop: ".8rem" }}>
        <button className="primario" onClick={salva}>Salva e vedi i bandi</button>
        {!nuova && <button onClick={cancella}>Togli questa impresa</button>}
      </div>
    </>
  );
}

export function MieRichieste() {
  const [r, setR] = useState<RichiestaSupporto[] | null>(null);
  useEffect(() => { api.mieRichieste().then(setR); }, []);
  if (!r) return <div className="caricamento">Caricamento…</div>;
  return (
    <>
      <h1>Le mie richieste di supporto</h1>
      {!r.length ? <p>Nessuna richiesta. Dalla scheda di un bando puoi chiedere il supporto dei nostri consulenti per la domanda.</p> : (
        <table>
          <thead><tr><th>Bando</th><th>Impresa</th><th>Inviata</th><th>Stato</th></tr></thead>
          <tbody>{r.map((x) => (
            <tr key={x.id}>
              <td><Link to={`/impresa/bandi/${x.bando_id}?impresa=${x.impresa_id}`}>{x.bando_titolo}</Link>
                {x.messaggio && <div className="piccolo">{x.messaggio}</div>}</td>
              <td>{x.impresa_nome}</td><td>{data(x.creata_il)}</td><td>{NOMI_STATO_RICHIESTA[x.stato]}</td>
            </tr>))}</tbody>
        </table>
      )}
    </>
  );
}

export function Abbonamento() {
  const [a, setA] = useState<TipoAbbonamento | null>(null);
  const [parametri] = useSearchParams();
  const [errore, setErrore] = useState<string | null>(null);
  useEffect(() => { api.abbonamento().then(setA).catch((e) => setErrore(String(e.message || e))); }, []);
  const vai = async (f: () => Promise<{ url: string }>) => {
    setErrore(null);
    try { window.location.href = (await f()).url; } catch (e) { setErrore(e instanceof Error ? e.message : String(e)); }
  };
  if (!a) return errore ? <div className="allarme">{errore}</div> : <div className="caricamento">Caricamento…</div>;
  const iva = a.iva_inclusa ? "IVA inclusa" : "+ IVA";
  const extra = a.imprese_extra * a.prezzi.impresa + a.sedi_extra * a.prezzi.sede;
  const pagante = a.stato === "attivo" || a.stato === "in_ritardo";
  return (
    <>
      <h1>Abbonamento</h1>
      {parametri.get("esito") === "ok" && <div className="avviso">Grazie! Il pagamento è registrato: lo stato si aggiorna entro qualche secondo.</div>}
      <p>Stato: <b>{NOMI_STATO_ABBONAMENTO[a.stato] || a.stato}</b>{a.piano ? ` · piano ${a.piano}` : ""}
        {a.stato === "prova" && a.giorni_prova != null && <> · {a.giorni_prova > 0 ? `restano ${a.giorni_prova} giorni di prova` : "prova finita"}</>}
        {a.fine_impegno && a.piano === "annuale" && <> · impegno fino al {data(a.fine_impegno)}</>}
        {a.stato === "disdetto" && a.fine_periodo && <> · accesso fino al {data(a.fine_periodo)}</>}</p>
      {!a.attivi && <p className="piccolo">In questa fase l'accesso è gratuito per tutti: puoi provare il pagamento, ma non è richiesto.</p>}
      {a.stato === "in_ritardo" && <div className="allarme">L'ultimo addebito non è riuscito: aggiorna la carta da "Gestisci abbonamento".</div>}
      {a.stato === "gratuito" ? <p>Il tuo abbonamento è gratuito: non devi fare niente.</p> : !pagante && (
        <div className="griglia-piani">
          <div className="riquadro"><div className="etichetta">Mensile</div><div className="numero">{a.prezzi.mensile} €</div>
            <div className="piccolo">al mese {iva}, disdici quando vuoi</div>
            <button className="primario" disabled={!a.stripe} onClick={() => vai(() => api.paga("mensile"))}>Scegli il mensile</button></div>
          <div className="riquadro"><div className="etichetta">Annuale</div><div className="numero">{a.prezzi.annuale} €</div>
            <div className="piccolo">al mese {iva}, pagato ogni mese, impegno di 12 mesi</div>
            <button className="primario" disabled={!a.stripe} onClick={() => vai(() => api.paga("annuale"))}>Scegli l'annuale</button></div>
        </div>)}
      {(a.imprese_extra > 0 || a.sedi_extra > 0) && <p>Con le tue imprese: {a.imprese_extra} impresa/e in più ({a.prezzi.impresa} € l'una) e {a.sedi_extra} sede/i
        in più ({a.prezzi.sede} € l'una): {extra} € al mese in più {iva}.</p>}
      {a.portale && <p><button onClick={() => vai(api.portale)}>Gestisci abbonamento: carta, fatture, disdetta</button></p>}
      {!a.stripe && <p className="piccolo">I pagamenti online non sono ancora attivi.</p>}
      {errore && <div className="allarme">{errore}</div>}
      <p className="piccolo">Pagamento sicuro con Stripe: i dati della carta non passano da bandinQiaro. <a href="/termini">Termini del servizio</a>.</p>
      <ModuloFatturazione />
    </>
  );
}

const VUOTI: DatiFatturazione = { denominazione: "", partita_iva: "", codice_fiscale: "", codice_destinatario: "", pec: "", indirizzo: "", cap: "", comune: "", provincia: "" };

function ModuloFatturazione() {
  const [d, setD] = useState<DatiFatturazione>(VUOTI);
  const [richiesti, setRichiesti] = useState(false);
  const [esito, setEsito] = useState<string | null>(null);
  const [errore, setErrore] = useState<string | null>(null);
  useEffect(() => { api.fatturazione().then((r) => { if (r.dati) setD({ ...VUOTI, ...r.dati }); setRichiesti(r.richiesti); }); }, []);
  const campo = (k: keyof DatiFatturazione, etichetta: string, extra: Partial<React.InputHTMLAttributes<HTMLInputElement>> = {}) => (
    <label>{etichetta}<input value={d[k] || ""} onChange={(e) => setD({ ...d, [k]: e.target.value })} {...extra} /></label>);
  const salva = async () => {
    setErrore(null); setEsito(null);
    try { setD({ ...VUOTI, ...(await api.salvaFatturazione(d)) }); setEsito("Dati salvati."); }
    catch (e) { setErrore(e instanceof Error ? e.message : String(e)); }
  };
  return (
    <>
      <h2>Dati di fatturazione</h2>
      <p className="piccolo">Per la fattura elettronica{richiesti ? " (servono prima di abbonarsi)" : ""}. Indica il codice destinatario SDI oppure la PEC.</p>
      <div className="modulo-profilo"><fieldset><legend>Intestatario</legend>
        {campo("denominazione", "Ragione sociale")}{campo("partita_iva", "Partita IVA", { maxLength: 13 })}
        {campo("codice_fiscale", "Codice fiscale (se diverso)", { maxLength: 16 })}
        {campo("codice_destinatario", "Codice destinatario SDI", { maxLength: 7 })}{campo("pec", "PEC (se non hai il codice)")}
      </fieldset><fieldset><legend>Sede</legend>
        {campo("indirizzo", "Indirizzo")}{campo("cap", "CAP", { maxLength: 5 })}{campo("comune", "Comune")}{campo("provincia", "Provincia (sigla)", { maxLength: 2 })}
      </fieldset></div>
      {errore && <div className="allarme">{errore}</div>}
      {esito && <div className="avviso">{esito}</div>}
      <p><button onClick={salva}>Salva i dati di fatturazione</button></p>
    </>
  );
}
