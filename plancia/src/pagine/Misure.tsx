import { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { api, EsempioMisura, Misura, MisuraBreve, nome, ProfiloEsempio } from "../api";

const intervallo = (min: number | null | undefined, max: number | null | undefined) =>
  min == null || max == null ? "" : min === max ? `${min}%` : `${min}–${max}%`;

// Misure nazionali (conto termico, iperammortamento, bonus assunzioni, Fondo di garanzia...): non sono bandi, sono norme
// sempre aperte che spesso si sommano ai bandi. Schede scritte e verificate a mano in app/misure/misure.yaml.
export default function Misure({ base = "/misure" }: { base?: string }) {
  const { id } = useParams();
  const [elenco, setElenco] = useState<Misura[] | null>(null);
  const [profili, setProfili] = useState<ProfiloEsempio[]>([]);
  useEffect(() => { api.misure().then(setElenco); api.profiliEsempio().then(setProfili).catch(() => setProfili([])); }, []);
  if (!elenco) return <div className="caricamento">Caricamento…</div>;
  const m = id ? elenco.find((x) => x.id === id) : null;
  const aperte = elenco.filter((x) => x.stato !== "chiuso"), chiuse = elenco.filter((x) => x.stato === "chiuso");
  if (id && m) return <SchedaMisura m={m} base={base} profili={profili} />;
  return (
    <>
      <h1>Misure nazionali per le imprese</h1>
      <p>Non sono bandi con una scadenza: sono agevolazioni previste dalla legge (su investimenti, assunzioni, garanzie sui prestiti),
        sempre disponibili finché sono in vigore, che spesso si possono <b>sommare</b> ai contributi dei bandi per le stesse spese.</p>
      <div className="griglia-piani">{aperte.map((x) => <Carta key={x.id} x={x} base={base} />)}</div>
      {chiuse.length > 0 && <>
        <h2 className="chiuse">Misure chiuse</h2>
        <p className="piccolo">Non più attive o con i fondi esauriti: restano qui per le eventuali code, gli scorrimenti o una riapertura.
          Non vengono proposte insieme ai bandi.</p>
        <div className="griglia-piani misure-chiuse">{chiuse.map((x) => <Carta key={x.id} x={x} base={base} />)}</div>
      </>}
    </>
  );
}

function Carta({ x, base }: { x: Misura; base: string }) {
  const chiusa = x.stato === "chiuso";
  return (
    <div className="riquadro">
      <div className="etichetta">{x.ente} · {nome(x.tipo)}</div>
      <h3><Link to={`${base}/${x.id}`}>{x.nome}</Link></h3>
      <p className="piccolo">{x.sintesi}</p>
      {x.beneficio_stimato?.percentuale_max != null && <p><b>Beneficio stimato: {intervallo(x.beneficio_stimato.percentuale_min, x.beneficio_stimato.percentuale_max)}</b> della spesa</p>}
      {chiusa ? <><span className="stato-bando chiuso">{x.coda ? "fondi esauriti, domande in coda" : "chiusa"}</span>
          {x.nota_chiusura && <p className="piccolo">{x.nota_chiusura}</p>}</>
        : <span className={`stato-bando ${x.stato === "aperto" ? "aperto" : "non_noto"}`}>{x.stato === "aperto" ? "in vigore" : "da verificare"}</span>}
    </div>
  );
}

function SchedaMisura({ m, base, profili }: { m: Misura; base: string; profili: ProfiloEsempio[] }) {
  const voce = (titolo: string, testo: unknown) => testo ? <><h3>{titolo}</h3><p className="testo-lungo">{String(testo)}</p></> : null;
  return (
    <>
      <p><Link to={base}>← Misure nazionali</Link></p>
      <h1>{m.nome}</h1>
      <p className="piccolo">{m.ente} · {m.norma}{m.url_ufficiale && <> · <a href={m.url_ufficiale} target="_blank" rel="noreferrer">fonte ufficiale ↗</a></>}
        {m.fonte_verificata_il && <> · verificata il {m.fonte_verificata_il}</>}</p>
      {m.stato === "chiuso" && <div className="avviso"><b>Misura chiusa{m.coda ? ": fondi esauriti, domande in coda" : ""}.</b> {m.nota_chiusura}</div>}
      {m.sintesi && <p className="testo-lungo">{m.sintesi}</p>}
      {m.beneficio_stimato && <div className="avviso">
        {m.beneficio_stimato.percentuale_max != null
          ? <b>Beneficio stimato: {intervallo(m.beneficio_stimato.percentuale_min, m.beneficio_stimato.percentuale_max)} della spesa.</b>
          : <b>Beneficio:</b>}{" "}
        {m.beneficio_stimato.nota}</div>}
      {voce("A chi si rivolge", m.a_chi_si_rivolge)}
      {voce("Spese e investimenti ammessi", m.investimenti_ammessi)}
      {voce("Quanto vale", m.intensita)}
      {voce("Come si ottiene", Array.isArray(m.come_si_ottiene) ? m.come_si_ottiene.join("\n") : m.come_si_ottiene)}
      {voce("Tempi", m.tempi)}
      {m.cumulabilita && voce("Si somma ai bandi?", `${m.cumulabilita.regola || ""}${m.cumulabilita.riferimento ? ` (${m.cumulabilita.riferimento})` : ""}`)}
      {voce("Attenzione", Array.isArray(m.attenzione) ? m.attenzione.join("\n") : m.attenzione)}
      <EsempiPerImpresa esempi={m.esempi} profili={profili} />
      <p className="piccolo">Informazione indicativa: verificare la norma e le regole del gestore prima di investire.</p>
    </>
  );
}

// Esempi pratici per tipo di impresa (ufficio, negozio, hotel, capannone, logistica...), gia' ordinati per interesse dall'API.
function EsempiPerImpresa({ esempi, profili }: { esempi?: EsempioMisura[]; profili: ProfiloEsempio[] }) {
  if (!esempi?.length) return null;
  const descrizione = (id: string) => profili.find((p) => p.id === id)?.descrizione;
  return (
    <>
      <h3>Esempi per tipo di impresa</h3>
      <p className="piccolo">Casi tipo con numeri indicativi, calcolati con le regole della misura: servono a capire per chi conta di più.</p>
      <table className="esempi-misura">
        <thead><tr><th>Tipo di impresa</th><th>Interesse</th><th>Esempio</th></tr></thead>
        <tbody>{esempi.map((e) => (
          <tr key={e.profilo}>
            <td><b>{e.profilo_nome}</b>{descrizione(e.profilo) && <div className="piccolo">{descrizione(e.profilo)}</div>}</td>
            <td><span className={`interesse ${e.interesse}`}>{e.interesse}</span></td>
            <td>{e.esempio}</td>
          </tr>))}</tbody>
      </table>
    </>
  );
}

// Riquadro per le schede dei bandi: le misure che si possono sommare per gli stessi investimenti.
export function SiSommaCon({ misure, base = "/misure" }: { misure?: MisuraBreve[]; base?: string }) {
  if (!misure?.length) return null;
  return (
    <div className="avviso">
      <b>Per le stesse spese si può sommare anche:</b>
      <ul>{misure.map((m) => (
        <li key={m.id}><Link to={`${base}/${m.id}`}>{m.nome}</Link>
          {m.beneficio_max != null && <> — circa {intervallo(m.beneficio_min, m.beneficio_max)} della spesa non coperta dal bando</>}
          {m.cumulo && <div className="piccolo">{m.cumulo}</div>}</li>))}</ul>
      <span className="piccolo">Stima indicativa, nei limiti delle regole sul cumulo degli aiuti: da verificare caso per caso.</span>
    </div>
  );
}
