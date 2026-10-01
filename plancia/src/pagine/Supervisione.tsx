import { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { api, data, Sistema, SistemaDettaglio } from "../api";

// Tutti i sistemi automatici in un posto (app/sistemi.py): cosa fanno, quando girano, cosa e' in corso, com'e' andata
// l'ultima volta. Cliccando un sistema: le sue ultime esecuzioni e i suoi dati.
const COLORI: Record<string, string> = {
  ok: "verde", "in corso": "giallo", errore: "rosso", interrotto: "rosso", "in ritardo": "giallo", "mai partito": "pausa", esterno: "pausa",
};
const NOMI_STATO: Record<string, string> = {
  ok: "ultimo giro ok", "in corso": "in corso adesso", errore: "ultimo giro in errore", interrotto: "interrotto",
  "in ritardo": "in ritardo", "mai partito": "mai partito", esterno: "sul server",
};

export default function Supervisione() {
  const { id } = useParams();
  const [sistemi, setSistemi] = useState<Sistema[] | null>(null);
  const [errore, setErrore] = useState<string | null>(null);
  const carica = () => api.sistemi().then(setSistemi).catch((e) => setErrore(String(e)));
  useEffect(() => {
    carica();
    const t = setInterval(carica, 30_000);   // si aggiorna da solo ogni 30 secondi
    return () => clearInterval(t);
  }, []);
  if (errore) return <div className="allarme">{errore}</div>;
  if (!sistemi) return <div className="caricamento">Caricamento…</div>;
  const gruppi = [...new Set(sistemi.map((s) => s.gruppo))];
  const inCorso = sistemi.filter((s) => s.stato === "in corso");
  const problemi = sistemi.filter((s) => ["errore", "interrotto", "in ritardo"].includes(s.stato));
  return (
    <>
      <h1>Supervisione</h1>
      <div className="avviso">Tutti i sistemi che lavorano da soli: cosa fanno, quando girano, cosa stanno facendo adesso e com'è
        andata l'ultima volta. Clicca un sistema per vedere le sue esecuzioni e i suoi dati. La pagina si aggiorna da sola ogni 30 secondi.</div>
      <div className="riquadri">
        <div className="riquadro"><div className="numero">{inCorso.length}</div><div className="etichetta">in corso adesso</div>
          <div className="piccolo">{inCorso.map((s) => s.nome).join(", ")}</div></div>
        <div className="riquadro"><div className="numero">{problemi.length}</div><div className="etichetta">da guardare</div>
          <div className="piccolo">{problemi.map((s) => s.nome).join(", ")}</div></div>
        <div className="riquadro"><div className="numero">{sistemi.filter((s) => s.stato === "ok").length}</div>
          <div className="etichetta">ultimo giro ok</div></div>
      </div>
      {id && <Dettaglio id={id} />}
      {gruppi.map((g) => (
        <div key={g}>
          <h2>{g}</h2>
          <table>
            <thead><tr><th>Sistema</th><th>Quando gira</th><th>Ultima esecuzione</th><th className="nascondi-mobile">Adesso</th></tr></thead>
            <tbody>{sistemi.filter((s) => s.gruppo === g).map((s) => (
              <tr key={s.id} className={s.id === id ? "filtro-attivo" : ""}>
                <td><span className={`pallino ${COLORI[s.stato] || "pausa"}`} title={NOMI_STATO[s.stato] || s.stato} />
                  <Link to={`/supervisione/${s.id}`} className="titolo-annuncio">{s.nome}</Link>
                  <div className="riassunto">{s.spiegazione}</div></td>
                <td className="piccolo">{s.programmazione}
                  {s.prossima && <div>prossima verso {data(s.prossima, true)}</div>}</td>
                <td className="piccolo">{s.ultima ? <>
                  <b>{NOMI_STATO[s.stato] || s.stato}</b> · {data(s.ultima.iniziato_il, true)}
                  {s.ultima.finito_il && ` (${durata(s.ultima.iniziato_il, s.ultima.finito_il)})`}
                  {s.ultima.riepilogo && <div>{s.ultima.riepilogo}</div>}
                  {s.ultima.errore && <div className="errore-allegato">{s.ultima.errore.slice(0, 200)}</div>}
                  {s.ultime_24_ore.esecuzioni > 0 && <div>ultime 24 ore: {s.ultime_24_ore.esecuzioni} esecuzioni, {s.ultime_24_ore.errori} errori</div>}
                </> : s.esterno ? "fuori dalla plancia: si vede dal server" : "nessuna esecuzione registrata"}</td>
                <td className="nascondi-mobile piccolo">{s.numeri || "–"}</td>
              </tr>
            ))}</tbody>
          </table>
        </div>
      ))}
    </>
  );
}

function durata(da: string, a: string): string {
  const s = Math.round((new Date(a).getTime() - new Date(da).getTime()) / 1000);
  return s < 90 ? `${s} s` : s < 5400 ? `${Math.round(s / 60)} min` : `${(s / 3600).toFixed(1)} ore`;
}

function cella(v: unknown): string {
  if (v === null || v === undefined) return "–";
  if (typeof v === "string" && /^\d{4}-\d{2}-\d{2}T/.test(v)) return data(v, true);
  return String(v);
}

function Dettaglio({ id }: { id: string }) {
  const [d, setD] = useState<SistemaDettaglio | null>(null);
  useEffect(() => { setD(null); api.sistema(id).then(setD); }, [id]);
  if (!d) return <div className="caricamento">Caricamento…</div>;
  return (
    <div className="riquadro" style={{ marginBottom: "1.5rem" }}>
      <p><Link to="/supervisione">✕ chiudi</Link></p>
      <h2 style={{ marginTop: 0 }}>{d.nome}</h2>
      <p className="piccolo">{d.spiegazione} <b>Quando:</b> {d.programmazione}.</p>
      {!d.esterno && (
        <>
          <h3>Ultime esecuzioni</h3>
          {d.esecuzioni.length === 0 ? <p className="piccolo">Nessuna esecuzione registrata (il registro esiste dal 01/10/2026).</p> : (
            <table><thead><tr><th>Inizio</th><th>Durata</th><th>Esito</th><th>Riepilogo</th></tr></thead>
              <tbody>{d.esecuzioni.map((e) => (
                <tr key={e.id}><td className="piccolo">{data(e.iniziato_il, true)}</td>
                  <td className="piccolo">{e.secondi < 90 ? `${e.secondi} s` : `${Math.round(e.secondi / 60)} min`}</td>
                  <td>{e.esito === "in_corso" ? "in corso" : e.esito}</td>
                  <td className="piccolo">{e.riepilogo}{e.errore && <div className="errore-allegato">{e.errore}</div>}</td></tr>
              ))}</tbody></table>
          )}
        </>
      )}
      {d.dati && (
        <>
          <h3>{d.dati.titolo}</h3>
          {d.dati.righe.length === 0 ? <p className="piccolo">Nessun dato.</p> : (
            <div style={{ overflowX: "auto" }}><table>
              <thead><tr>{d.dati.colonne.map((c) => <th key={c}>{c.replace(/_/g, " ")}</th>)}</tr></thead>
              <tbody>{d.dati.righe.map((r, i) => (
                <tr key={i}>{d.dati!.colonne.map((c) => <td key={c} className="piccolo">{cella(r[c])}</td>)}</tr>
              ))}</tbody></table></div>
          )}
        </>
      )}
      {d.esterno && !d.dati && <p className="piccolo">Questo sistema gira sul server, fuori dai servizi della plancia: lo stato si vede dal server
        (<code>systemctl status bandi-radar-deploy.timer</code>, log del backup). Vedi deploy/MANUALE.md.</p>}
    </div>
  );
}
