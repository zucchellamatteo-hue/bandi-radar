import { useEffect, useMemo, useState } from "react";
import { Link } from "react-router-dom";
import { api, Colore, data, Fonte, NOMI_TIPO, Riepilogo } from "../api";

const ORDINE_COLORE: Record<Colore, number> = { rosso: 0, giallo: 1, verde: 2, pausa: 3 };

export default function Fonti() {
  const [fonti, setFonti] = useState<Fonte[] | null>(null);
  const [riepilogo, setRiepilogo] = useState<Riepilogo | null>(null);
  const [testo, setTesto] = useState("");
  const [tipo, setTipo] = useState("");
  const [colore, setColore] = useState("");
  const [messaggio, setMessaggio] = useState("");

  const carica = () => {
    api.fonti().then(setFonti);
    api.riepilogo().then(setRiepilogo);
  };
  useEffect(carica, []);

  const filtrate = useMemo(() => {
    if (!fonti) return [];
    const t = testo.toLowerCase();
    return fonti
      .filter((f) => (!tipo || f.tipo === tipo) && (!colore || f.colore === colore) &&
        (!t || f.nome.toLowerCase().includes(t) || f.ente.toLowerCase().includes(t) || f.territorio.toLowerCase() === t))
      .sort((a, b) => ORDINE_COLORE[a.colore] - ORDINE_COLORE[b.colore] || a.nome.localeCompare(b.nome));
  }, [fonti, testo, tipo, colore]);

  const rilancia = async (f: Fonte) => {
    const r = await api.rilancia(f.id);
    setMessaggio(`${f.nome}: controllo ${r.stato}. Ricarica tra qualche secondo per vedere l'esito.`);
  };
  const pausa = async (f: Fonte) => {
    await api.pausa(f.id, !f.in_pausa);
    carica();
  };

  if (!fonti || !riepilogo) return <div className="caricamento">Caricamento…</div>;
  return (
    <>
      <h1>Fonti</h1>
      <div className="riquadri">
        {(["verde", "giallo", "rosso", "pausa"] as Colore[]).map((c) => (
          <div className="riquadro" key={c} onClick={() => setColore(colore === c ? "" : c)} style={{ cursor: "pointer" }}>
            <div className="numero"><span className={`pallino ${c}`} />{riepilogo.fonti[c]}</div>
            <div className="etichetta">{{ verde: "regolari", giallo: "da guardare", rosso: "in errore", pausa: "in pausa" }[c]}</div>
          </div>
        ))}
        <div className="riquadro"><div className="numero">{riepilogo.annunci_ultimi_7_giorni}</div><div className="etichetta">novità negli ultimi 7 giorni</div></div>
        <div className="riquadro"><div className="numero" style={{ fontSize: "1.1rem" }}>{data(riepilogo.ultimo_controllo, true)}</div><div className="etichetta">ultimo controllo</div></div>
      </div>
      {riepilogo.allarmi.length > 0 && (
        <div className="allarme"><b>Allarmi:</b>{" "}
          {riepilogo.allarmi.map((a) => <span key={a.fonte_id}><Link to={`/fonti/${a.fonte_id}`}>{a.nome}</Link> ({a.motivo}); </span>)}
        </div>
      )}
      {messaggio && <div className="avviso">{messaggio}</div>}
      <div className="filtri">
        <input type="text" placeholder="Cerca fonte, ente o sigla regione…" value={testo} onChange={(e) => setTesto(e.target.value)} />
        <select value={tipo} onChange={(e) => setTipo(e.target.value)}>
          <option value="">Tutti i tipi</option>
          {Object.entries(NOMI_TIPO).map(([k, v]) => <option key={k} value={k}>{v}</option>)}
        </select>
        <select value={colore} onChange={(e) => setColore(e.target.value)}>
          <option value="">Tutti gli stati</option>
          <option value="rosso">Rosso</option><option value="giallo">Giallo</option><option value="verde">Verde</option><option value="pausa">Pausa</option>
        </select>
        <span className="piccolo">{filtrate.length} fonti</span>
      </div>
      <table>
        <thead><tr>
          <th>Stato</th><th>Fonte</th><th className="nascondi-mobile">Ultimo controllo</th><th>Ultima novità</th>
          <th className="nascondi-mobile">Silenzio</th><th>30 / 90 gg</th><th>Azioni</th>
        </tr></thead>
        <tbody>
          {filtrate.map((f) => (
            <tr key={f.id}>
              <td title={f.motivo}><span className={`pallino ${f.colore}`} /><span className="piccolo">{f.motivo}</span></td>
              <td>
                <Link to={`/fonti/${f.id}`}>{f.nome}</Link>
                <div className="piccolo">{NOMI_TIPO[f.tipo] || f.tipo} · {f.territorio} · {f.modalita} · {f.frequenza.replace(/_/g, " ")}</div>
              </td>
              <td className="nascondi-mobile">{data(f.ultimo_controllo, true)}<div className="piccolo">{f.ultimo_esito}{f.ultimo_messaggio ? `: ${f.ultimo_messaggio}` : ""}</div></td>
              <td>{data(f.ultima_novita)}<div className="piccolo">{f.ultimo_titolo?.slice(0, 70)}</div></td>
              <td className="nascondi-mobile">{f.silenzio_giorni ?? "–"}<span className="piccolo"> / {f.soglia_silenzio_giorni}</span></td>
              <td>{f.novita_30} / {f.novita_90}</td>
              <td>
                <button onClick={() => rilancia(f)} title="Controlla adesso">▶</button>{" "}
                <button onClick={() => pausa(f)} title={f.in_pausa ? "Riprendi" : "Metti in pausa"}>{f.in_pausa ? "▶▶" : "⏸"}</button>{" "}
                {f.url && <a href={f.url} target="_blank" rel="noreferrer" title="Apri la pagina della fonte">↗</a>}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </>
  );
}
