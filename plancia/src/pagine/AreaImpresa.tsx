import { useEffect, useState } from "react";
import { Link, useNavigate, useParams, useSearchParams } from "react-router-dom";
import { api, BandoRiga, data, euro, Impresa, nome, NOMI_STATO_RICHIESTA, Profilo, RichiestaSupporto, SchedaRidotta, Valori } from "../api";
import { Importo, SegnoEsito } from "./Catalogo";
import { Fasce, Modulo, Motivi, VUOTO } from "./Profili";
import Giudizio from "../Giudizio";

// Area impresa (05/10/2026): le imprese dell'utente, i bandi adatti (mai gli esclusi), la scheda ridotta e la richiesta
// di supporto. Niente pagine di lavoro (fonti, annunci, lavorazione).

export function MieiBandi() {
  const [imprese, setImprese] = useState<Impresa[] | null>(null);
  const [parametri, setParametri] = useSearchParams();
  const [r, setR] = useState<Awaited<ReturnType<typeof api.bandiImpresa>> | null>(null);
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
      <h1>Benvenuto in Bandi Radar</h1>
      <div className="avviso">Per vedere i bandi adatti, descrivi prima la tua impresa: dove ha le sedi, cosa fa (codice ATECO),
        quanto è grande. Bastano pochi minuti.</div>
      <p><Link to="/impresa/imprese/nuova"><button className="primario">Descrivi la tua impresa</button></Link></p>
    </>
  );
  const compatibili = r?.bandi.filter((b) => b.esito.livello === "compatibile") || [];
  const daVerificare = r?.bandi.filter((b) => b.esito.livello === "da_verificare") || [];
  return (
    <>
      <h1>I bandi per la tua impresa</h1>
      {imprese.length > 1 && <div className="filtri">
        {imprese.map((i) => <button key={i.id} className={i.id === scelta ? "primario" : ""}
          onClick={() => setParametri({ impresa: String(i.id) })}>{i.nome}</button>)}</div>}
      {!r ? <div className="caricamento">Cerco i bandi…</div> : (
        <>
          <p>Bandi aperti o in arrivo: <b>{r.conteggi.compatibile}</b> adatti a <b>{r.impresa.nome}</b> e <b>{r.conteggi.da_verificare}</b> da
            verificare (manca un dato o il bando pone condizioni da controllare). <span className="piccolo">Informazione indicativa:
            verifica sempre il bando ufficiale.</span></p>
          <ElencoBandi titolo="✓ Adatti alla tua impresa" bandi={compatibili} impresaId={r.impresa.id} />
          <ElencoBandi titolo="? Da verificare" bandi={daVerificare} impresaId={r.impresa.id} />
        </>
      )}
    </>
  );
}

function ElencoBandi({ titolo, bandi, impresaId }: { titolo: string; bandi: BandoRiga[]; impresaId: number }) {
  const [quanti, setQuanti] = useState(30);
  if (!bandi.length) return <p className="piccolo">{titolo}: nessuno al momento.</p>;
  return (
    <>
      <h2>{titolo} ({bandi.length})</h2>
      <table>
        <tbody>{bandi.slice(0, quanti).map((b) => (
          <tr key={b.id}>
            <td><SegnoEsito livello={b.esito.livello} /></td>
            <td><Link to={`/impresa/bandi/${b.id}?impresa=${impresaId}`} className="titolo-annuncio">{b.titolo}</Link>
              <div className="piccolo">{b.ente}</div>
              <div className="riassunto">{b.sintesi}</div>
              <Motivi classe="da_verificare" voci={b.esito.da_verificare.slice(0, 3)} segno="?" /></td>
            <td><span className={`stato-bando ${b.stato || "non_noto"}`}>{b.stato ? nome(b.stato) : "stato non noto"}</span>
              {b.scadenza && <div className="scadenza">scade il {data(b.scadenza)}</div>}</td>
            <td>{(b.tipi_agevolazione || []).map((t) => <span key={t} className="etichetta-tipo">{nome(t)}</span>)}<Importo b={b} /></td>
          </tr>))}</tbody>
      </table>
      {bandi.length > quanti && <button onClick={() => setQuanti(quanti + 50)}>Mostra altri ({bandi.length - quanti})</button>}
    </>
  );
}

export function SchedaImpresa() {
  const { id } = useParams();
  const [parametri] = useSearchParams();
  const [b, setB] = useState<SchedaRidotta | null>(null);
  const [errore, setErrore] = useState<string | null>(null);
  const [supporto, setSupporto] = useState(parametri.get("supporto") === "1");
  useEffect(() => { if (id) api.schedaImpresa(id).then(setB).catch((e) => setErrore(String(e.message || e))); }, [id]);
  if (errore) return <><div className="allarme">{errore}</div><p><Link to="/impresa">← I miei bandi</Link></p></>;
  if (!b) return <div className="caricamento">Caricamento…</div>;
  const impresaId = Number(parametri.get("impresa")) || b.imprese[0].id;
  const perQuale = b.imprese.find((i) => i.id === impresaId) || b.imprese[0];
  return (
    <>
      <p><Link to={`/impresa?impresa=${perQuale.id}`}>← I miei bandi</Link></p>
      <h1>{b.titolo}</h1>
      <p><span className={`stato-bando ${b.stato || "non_noto"}`}>{b.stato ? nome(b.stato) : "stato non noto"}</span>
        <span className="piccolo"> · {b.ente}</span></p>
      <p>{b.data_apertura && <>apre il <b>{data(b.data_apertura)}</b>{b.ora_apertura ? ` ore ${b.ora_apertura.slice(0, 5)}` : ""} · </>}
        {b.scadenza ? <>scade il <b className="scadenza">{data(b.scadenza)}</b>{b.ora_scadenza ? ` ore ${b.ora_scadenza.slice(0, 5)}` : ""}</> : "nessuna scadenza scritta"}
        {b.modalita_selezione ? ` · ${nome(b.modalita_selezione)}` : ""}
        {b.url && <> · <a href={b.url} target="_blank" rel="noreferrer">bando ufficiale ↗</a></>}</p>
      <div className="avviso">{b.avvertenza}</div>

      <div className={`riquadro supporto ${supporto ? "aperto" : ""}`}>
        {!supporto ? <>
          <b>Vuoi presentare la domanda?</b> I nostri consulenti verificano i requisiti e preparano la pratica con te.{" "}
          <button className="primario" onClick={() => setSupporto(true)}>Richiedi supporto per la domanda</button>
        </> : <ModuloSupporto bandoId={b.id} imprese={b.imprese} impresaId={perQuale.id} origine={parametri.get("supporto") === "1" ? "email" : "piattaforma"} />}
      </div>

      <h2>Per {perQuale.nome}</h2>
      <p><SegnoEsito livello={perQuale.esito.livello} /> {perQuale.esito.livello === "compatibile" ? "In base ai dati che hai indicato il bando è adatto." : "Da verificare:"}</p>
      <Motivi classe="da_verificare" voci={perQuale.esito.da_verificare} segno="?" />
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
      {b.a_chi_si_rivolge && <><h3>A chi si rivolge</h3><p className="testo-lungo">{b.a_chi_si_rivolge}</p></>}
      {b.cosa_finanzia && <><h3>Cosa finanzia</h3><p className="testo-lungo">{b.cosa_finanzia}</p></>}
      {b.requisiti && <><h3>Cosa serve</h3><p className="testo-lungo">{b.requisiti}</p></>}
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
    if (!confirm(`Togliere ${nomeImpresa} da Bandi Radar?`)) return;
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
