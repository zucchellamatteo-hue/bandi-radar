import { useEffect, useState } from "react";
import { Link, useSearchParams } from "react-router-dom";
import { api, data, FaseLavorazione, Lavorazione as TipoLavorazione, RigaLavorazione, RigaSituazione, SchedaDaRivedere,
  Situazione } from "../api";

// A che punto e' la fase 2: dagli annunci raccolti alla scheda. I numeri li calcola il regista
// (app/catena/regista.py) dai dati; cliccando una fase si vedono i bandi o gli annunci fermi li', con il motivo.
export default function Lavorazione() {
  const [parametri, setParametri] = useSearchParams();
  const [dati, setDati] = useState<TipoLavorazione | null>(null);
  const [righe, setRighe] = useState<RigaLavorazione[] | null>(null);
  const tipo = parametri.get("tipo") as "bandi" | "annunci" | null;
  const fase = parametri.get("fase");
  const [rivedere, setRivedere] = useState<SchedaDaRivedere[] | null>(null);
  const [soloGravi, setSoloGravi] = useState(true);
  useEffect(() => { api.lavorazione().then(setDati); api.controlli().then(setRivedere).catch(() => setRivedere([])); }, []);
  useEffect(() => {
    setRighe(null);
    if (tipo && fase) api.lavorazioneFase(tipo, fase).then(setRighe);
  }, [tipo, fase]);
  if (!dati) return <div className="caricamento">Caricamento…</div>;
  const scegli = (t: string, f: string) => setParametri(new URLSearchParams({ tipo: t, fase: f }));
  const nomeFase = [...dati.bandi, ...dati.annunci].find((x) => x.fase === fase)?.nome;
  return (
    <>
      <h1>Lavorazione</h1>
      <SituazioneBandi />
      <div className="avviso">Dove si trova ogni annuncio e ogni bando tra la raccolta e la scheda. Ogni ora il <b>regista</b> li porta
        avanti di un passo, riprova quelli fermi (pagine non trovate dopo 14 giorni, documenti dei bandi aperti ogni 14 giorni),
        decide i doppioni (regole, e l'IA per i dubbi) e chiede di aggiornare le schede quando arrivano proroghe o documenti nuovi.
        Clicca una riga per vedere chi è fermo lì e perché.</div>
      <p className="piccolo">IA nel mese: {dati.ia.chiamate_mese} chiamate, {dati.ia.costo_mese.toFixed(2)} $
        {dati.ia.in_volo ? ` · ${dati.ia.in_volo} richieste in attesa di risposta (Batch API)` : ""}</p>
      <div className="scheda-griglia">
        <Imbuto titolo="Annunci" fasi={dati.annunci} tipo="annunci" scegli={scegli} attiva={fase} />
        <Imbuto titolo="Bandi" fasi={dati.bandi} tipo="bandi" scegli={scegli} attiva={fase} />
      </div>
      {tipo && fase && (
        <>
          <h2>{nomeFase} <span className="piccolo">(al massimo 200, i più recenti)</span></h2>
          {!righe ? <div className="caricamento">Caricamento…</div> : righe.length === 0 ? <p className="piccolo">Nessuno.</p> : (
            <table>
              <thead><tr><th>{tipo === "bandi" ? "Bando" : "Annuncio"}</th><th>Motivo</th><th className="nascondi-mobile">Ultimo passo</th></tr></thead>
              <tbody>{righe.map((r) => (
                <tr key={r.id}>
                  <td><Link to={`/${tipo}/${r.id}`} className="titolo-annuncio">{r.titolo}</Link>
                    <div className="piccolo">{r.ente || r.fonte}{r.scadenza ? ` · scade il ${data(r.scadenza)}` : ""}</div></td>
                  <td className="piccolo">{r.motivo || "–"}</td>
                  <td className="nascondi-mobile piccolo">{data(r.ultimo, true)}</td>
                </tr>
              ))}</tbody>
            </table>
          )}
        </>
      )}
      {rivedere && <DaRivedere righe={rivedere} soloGravi={soloGravi} cambia={setSoloGravi} />}
      <h2>Ultime azioni del regista</h2>
      <table>
        <thead><tr><th>Quando</th><th>Cosa</th><th>Esito</th><th className="nascondi-mobile">Motivo</th></tr></thead>
        <tbody>{dati.eventi.map((e, i) => (
          <tr key={i}>
            <td className="piccolo">{data(e.quando, true)}</td>
            <td>{e.oggetto === "giro" ? "giro orario" : <Link to={`/${e.oggetto === "bando" ? "bandi" : "annunci"}/${e.oggetto_id}`}>{e.oggetto} {e.oggetto_id}</Link>}
              <div className="piccolo">{e.passo}</div></td>
            <td>{e.esito}</td>
            <td className="nascondi-mobile piccolo">{e.motivo}</td>
          </tr>
        ))}</tbody>
      </table>
    </>
  );
}

function Imbuto({ titolo, fasi, tipo, scegli, attiva }: {
  titolo: string; fasi: FaseLavorazione[]; tipo: string; scegli: (t: string, f: string) => void; attiva: string | null;
}) {
  const totale = fasi.reduce((s, f) => s + f.n, 0);
  return (
    <div className="riquadro">
      <div className="etichetta">{titolo}: {totale.toLocaleString("it-IT")}</div>
      <table className="vincoli"><tbody>{fasi.map((f) => (
        <tr key={f.fase} onClick={() => scegli(tipo, f.fase)} style={{ cursor: "pointer" }}
          className={attiva === f.fase ? "filtro-attivo" : ""}>
          <td>{f.nome}<div className="piccolo">{f.prossimo}</div></td>
          <td style={{ textAlign: "right" }}><b>{f.n.toLocaleString("it-IT")}</b></td>
        </tr>
      ))}</tbody></table>
    </div>
  );
}

// Il controllo delle schede senza IA: le gravi non si propongono alle imprese finche' non sono sistemate.
function DaRivedere({ righe, soloGravi, cambia }: { righe: SchedaDaRivedere[]; soloGravi: boolean; cambia: (v: boolean) => void }) {
  const gravi = righe.filter((r) => r.controllo.gravi.length > 0).length;
  const mostra = (soloGravi ? righe.filter((r) => r.controllo.gravi.length > 0) : righe).slice(0, 200);
  return (
    <>
      <h2>Da rivedere <span className="piccolo">({gravi} con problemi gravi, {righe.length - gravi} da migliorare)</span></h2>
      <p className="piccolo">Ogni ora il regista ricontrolla senza IA le schede nuove o cambiate. Le schede con problemi
        <b> gravi</b> non vengono proposte alle imprese finché non sono sistemate.{" "}
        <label><input type="checkbox" checked={soloGravi} onChange={(e) => cambia(e.target.checked)} /> solo i gravi</label></p>
      {mostra.length === 0 ? <p className="piccolo">Nessuna.</p> : (
        <table>
          <thead><tr><th>Bando</th><th>Problemi</th></tr></thead>
          <tbody>{mostra.map((r) => (
            <tr key={r.id}>
              <td><Link to={`/bandi/${r.id}`} className="titolo-annuncio">{r.titolo}</Link>
                <div className="piccolo">{r.ente}{r.stato ? ` · ${r.stato}` : ""}{r.scadenza ? ` · scade il ${data(r.scadenza)}` : ""}</div></td>
              <td className="piccolo">
                {r.controllo.gravi.map((g, i) => <div key={"g" + i}><b>Grave:</b> {g}</div>)}
                {r.controllo.da_migliorare.map((g, i) => <div key={"m" + i}>{g}</div>)}
              </td>
            </tr>
          ))}</tbody>
        </table>
      )}
    </>
  );
}

// Situazione dei bandi: ogni bando ha UNA situazione, calcolata solo nella vista bandi_situazione (app/catena/situazione.py),
// con il perche' accanto. Per contare i bandi si usano questi numeri, non altri.
function SituazioneBandi() {
  const [parametri, setParametri] = useSearchParams();
  const [dati, setDati] = useState<Situazione | null>(null);
  const [righe, setRighe] = useState<RigaSituazione[] | null>(null);
  const scelta = parametri.get("situazione");
  const fase = parametri.get("sfase");
  useEffect(() => { api.situazione().then(setDati).catch(() => setDati(null)); }, []);
  useEffect(() => {
    setRighe(null);
    if (scelta) api.situazioneElenco(scelta, fase).then(setRighe).catch(() => setRighe([]));
  }, [scelta, fase]);
  if (!dati) return null;
  const scegli = (s: string, f?: string) => setParametri(new URLSearchParams(f ? { situazione: s, sfase: f } : { situazione: s }));
  const voce = dati.situazioni.find((v) => v.situazione === scelta);
  // Scartati: chiusi, senza testo e fuori target (solo enti pubblici o persone fisiche). I bandi per il non profit no:
  // si mappano anche loro, con priorita' piu' bassa (07/10).
  const scartato = (s: string) => s.startsWith("scartato_") || s === "fuori_target";
  const scartati = dati.situazioni.filter((v) => scartato(v.situazione));
  return (
    <div className="riquadro">
      <div className="etichetta">Situazione dei bandi: {dati.totale.toLocaleString("it-IT")}{" "}
        <span className="piccolo">(una sola voce per bando; scartati in tutto: {scartati.reduce((t, v) => t + v.n, 0).toLocaleString("it-IT")} —{" "}
          <a href="#" onClick={(e) => { e.preventDefault(); scegli("scartato_chiuso"); }}>vedi gli scartati e il perché</a>)</span></div>
      <table className="vincoli"><tbody>{dati.situazioni.map((v) => (
        <tr key={v.situazione} onClick={() => scegli(v.situazione)} style={{ cursor: "pointer" }}
          className={scelta === v.situazione ? "filtro-attivo" : ""}>
          <td><b>{v.nome}</b><div className="piccolo">{v.spiegazione}</div>
            {v.fasi.length > 1 && <div className="piccolo">{v.fasi.map((f, i) => (
              <span key={f.fase}>{i ? " · " : ""}<a href="#" onClick={(e) => { e.preventDefault(); e.stopPropagation(); scegli(v.situazione, f.fase); }}
                className={fase === f.fase && scelta === v.situazione ? "filtro-attivo" : ""}>{f.nome}: {f.n.toLocaleString("it-IT")}</a></span>
            ))}</div>}</td>
          <td style={{ textAlign: "right" }}><b>{v.n.toLocaleString("it-IT")}</b></td>
        </tr>
      ))}</tbody></table>
      {scelta && voce && (
        <>
          <h2>{voce.nome}{fase ? ` / ${voce.fasi.find((f) => f.fase === fase)?.nome || fase}` : ""}{" "}
            <span className="piccolo">(al massimo 200, i più recenti)</span>
            {scartato(voce.situazione) && <span className="piccolo">
              {scartati.filter((v) => v.situazione !== scelta).map((v) => (
                <span key={v.situazione}> · <a href="#" onClick={(e) => { e.preventDefault(); scegli(v.situazione); }}>{v.nome}</a></span>))}</span>}
            {" "}<a href="#" className="piccolo" onClick={(e) => { e.preventDefault(); setParametri(new URLSearchParams()); }}>chiudi</a></h2>
          {!righe ? <div className="caricamento">Caricamento…</div> : righe.length === 0 ? <p className="piccolo">Nessuno.</p> : (
            <table>
              <thead><tr><th>Bando</th><th>Perché</th><th className="nascondi-mobile">Chi ha deciso, quando</th></tr></thead>
              <tbody>{righe.map((r) => (
                <tr key={r.id}>
                  <td><Link to={`/bandi/${r.id}`} className="titolo-annuncio">{r.titolo}</Link>
                    <div className="piccolo">n. {r.id} · {r.ente || "–"}{r.scadenza ? ` · scade il ${data(r.scadenza)}` : ""}</div></td>
                  <td className="piccolo"><b>{r.nome_fase}</b>{r.motivo ? `: ${r.motivo}` : ""}
                    {r.unito_a ? <> (<Link to={`/bandi/${r.unito_a}`}>bando {r.unito_a}</Link>)</> : null}</td>
                  <td className="nascondi-mobile piccolo">{r.chi || "–"}<div>{data(r.deciso_il, true)}</div></td>
                </tr>
              ))}</tbody>
            </table>
          )}
        </>
      )}
    </div>
  );
}
