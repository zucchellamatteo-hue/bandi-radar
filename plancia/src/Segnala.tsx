import { useEffect, useState } from "react";
import { Link, useLocation } from "react-router-dom";
import { api, data, Segnalazione, StatoSegnalazione, TipoSegnalazione } from "./api";
import { usePuo } from "./utente";

// Pulsante "Segnala" (06/10): sempre visibile in basso a destra. Si sceglie il tipo di problema, si compilano i pochi
// campi del tipo e si scrive un testo libero. La pagina corrente parte da sola; nella pagina di un bando il suo numero
// e' gia' scritto nel campo "Bando".
type Tipi = { tipi: Record<string, TipoSegnalazione>; stati: Record<StatoSegnalazione, string> };

function bandoDellaPagina(percorso: string): number | null {
  const m = percorso.match(/^\/(?:impresa\/)?bandi\/(\d+)/);
  return m ? Number(m[1]) : null;
}

export default function Segnala() {
  const posizione = useLocation();
  const lavoro = usePuo("lavoro");
  const [aperto, setAperto] = useState(false);
  const [tipi, setTipi] = useState<Tipi | null>(null);
  const [tipo, setTipo] = useState<string | null>(null);
  const [dettagli, setDettagli] = useState<Record<string, string>>({});
  const [testo, setTesto] = useState("");
  const [inviata, setInviata] = useState<Segnalazione | null>(null);
  const [mie, setMie] = useState<Segnalazione[] | null>(null);
  const [errore, setErrore] = useState<string | null>(null);
  const [invio, setInvio] = useState(false);
  const pagina = posizione.pathname + posizione.search;
  const bandoId = bandoDellaPagina(posizione.pathname);

  useEffect(() => {
    if (aperto && !tipi) api.tipiSegnalazione().then(setTipi).catch((e) => setErrore(String(e.message || e)));
  }, [aperto]);
  useEffect(() => {
    if (!aperto) return;
    const esc = (e: KeyboardEvent) => { if (e.key === "Escape") chiudi(); };
    window.addEventListener("keydown", esc);
    return () => window.removeEventListener("keydown", esc);
  }, [aperto]);

  const azzera = () => { setTipo(null); setDettagli({}); setTesto(""); setInviata(null); setMie(null); setErrore(null); };
  const chiudi = () => { setAperto(false); azzera(); };
  const scegli = (t: string) => {
    setTipo(t); setErrore(null);
    setDettagli(bandoId && tipi?.tipi[t]?.campi.bando ? { bando: String(bandoId) } : {});
  };
  const invia = async () => {
    if (!tipo || !tipi) return;
    setErrore(null); setInvio(true);
    try {
      // Il numero del bando della pagina va sempre con la segnalazione, tranne quando il campo "Bando" dice altro.
      const conCampoBando = "bando" in tipi.tipi[tipo].campi;
      setInviata(await api.segnala({ tipo, testo, dettagli, pagina, bando_id: conCampoBando ? null : bandoId }));
    } catch (e) { setErrore(e instanceof Error ? e.message : String(e)); }
    setInvio(false);
  };
  const vediMie = () => api.segnalazioni({}).then((r) => setMie(r.segnalazioni.slice(0, 5))).catch((e) => setErrore(String(e.message || e)));

  if (!aperto) return <button className="segnala-pulsante" onClick={() => setAperto(true)} title="Segnala un problema o un'idea">Segnala</button>;
  const scelto = tipo && tipi ? tipi.tipi[tipo] : null;
  return (
    <div className="segnala-pannello" role="dialog" aria-label="Segnala">
      <div className="segnala-testa">
        <b>{scelto ? scelto.nome : "Cosa vuoi segnalare?"}</b>
        <button onClick={chiudi} title="Chiudi">✕</button>
      </div>
      {errore && <div className="allarme">{errore}</div>}
      {inviata ? <>
        <p>Grazie, segnalazione <b>#{inviata.id}</b> ricevuta. La leggiamo e ti rispondiamo qui.</p>
        <p><button onClick={azzera}>Segnala altro</button>{" "}<button onClick={chiudi}>Chiudi</button></p>
      </> : !tipi ? <div className="caricamento">Caricamento…</div>
      : !scelto ? <>
        <ul className="segnala-tipi">
          {Object.entries(tipi.tipi).map(([k, t]) => <li key={k}><button onClick={() => scegli(k)}>
            <b>{t.nome}</b><span className="piccolo">{t.descrizione}</span></button></li>)}
        </ul>
        <p className="piccolo">
          {lavoro ? <Link to="/segnalazioni" onClick={chiudi}>Tutte le segnalazioni →</Link>
            : <button className="collegamento" onClick={vediMie}>Le mie segnalazioni e le risposte</button>}
        </p>
        {mie && (mie.length ? <ul className="segnala-mie">{mie.map((s) => <li key={s.id}>
            <b>#{s.id} {tipi.tipi[s.tipo]?.nome}</b> · {data(s.creata_il)} · {tipi.stati[s.stato]}
            {s.risposta && <div className="piccolo">{s.risposta}</div>}</li>)}</ul>
          : <p className="piccolo">Non hai ancora mandato segnalazioni.</p>)}
      </> : <form onSubmit={(e) => { e.preventDefault(); invia(); }}>
        <p className="piccolo">{scelto.descrizione}</p>
        {Object.entries(scelto.campi).map(([k, etichetta]) => <label key={k}>{etichetta}
          <input type="text" value={dettagli[k] || ""} onChange={(e) => setDettagli({ ...dettagli, [k]: e.target.value })} /></label>)}
        <label>{Object.keys(scelto.campi).length ? "Altro da aggiungere" : "Cosa vuoi dirci"}
          <textarea rows={4} value={testo} onChange={(e) => setTesto(e.target.value)} /></label>
        <p className="piccolo">Pagina: {pagina}</p>
        <p><button type="submit" className="primario" disabled={invio}>Invia</button>{" "}
          <button type="button" onClick={() => { setTipo(null); setErrore(null); }}>← Indietro</button></p>
      </form>}
    </div>
  );
}
