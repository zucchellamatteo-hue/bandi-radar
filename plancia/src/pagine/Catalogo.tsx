import { useEffect, useState } from "react";
import { Link, useSearchParams } from "react-router-dom";
import { api, BandoRiga, data, euro, nome, NOMI_TIPO, RispostaCatalogo, Valori } from "../api";

// Catalogo dei bandi con scheda. I filtri su "chi può partecipare" usano le regole dell'abbinamento
// (app/abbinamento/regole.py): passano i bandi che ammettono il valore e quelli senza vincolo; quelli con il
// vincolo "non noto" escono con il segno "?" e il motivo, dopo i compatibili. Mai nascosti.
export default function Catalogo() {
  const [parametri, setParametri] = useSearchParams();
  const [risposta, setRisposta] = useState<RispostaCatalogo | null>(null);
  const [valori, setValori] = useState<Valori | null>(null);
  const [testo, setTesto] = useState(parametri.get("q") || "");
  const [ateco, setAteco] = useState(parametri.get("ateco") || "");
  const pagina = Number(parametri.get("pagina") || "1");

  const imposta = (chiave: string, valore: string) => {
    const p = new URLSearchParams(parametri);
    if (valore) p.set(chiave, valore); else p.delete(chiave);
    if (chiave === "regione") p.delete("provincia");
    if (chiave !== "pagina") p.delete("pagina");
    setParametri(p);
  };
  useEffect(() => { api.valori().then(setValori); }, []);
  // Il menu a scelta multipla si chiude cliccando fuori.
  useEffect(() => {
    const chiudi = (e: MouseEvent) => document.querySelectorAll("details.multiplo[open]").forEach((d) => {
      if (!d.contains(e.target as Node)) d.removeAttribute("open");
    });
    document.addEventListener("click", chiudi);
    return () => document.removeEventListener("click", chiudi);
  }, []);
  useEffect(() => {
    const p: Record<string, string> = {};
    parametri.forEach((v, k) => (p[k] = v));
    setRisposta(null);
    api.bandi(p).then(setRisposta);
  }, [parametri]);

  const menu = (chiave: string, vuoto: string, voci: [string, string][]) => (
    <select value={parametri.get(chiave) || ""} onChange={(e) => imposta(chiave, e.target.value)}
      className={parametri.get(chiave) ? "filtro-attivo" : ""}>
      <option value="">{vuoto}</option>
      {voci.map(([k, v]) => <option key={k} value={k}>{v}</option>)}
    </select>
  );
  // Scelta multipla (regioni): un menu a tendina con le caselle; il valore va nell'indirizzo separato da virgole.
  const multiplo = (chiave: string, vuoto: string, voci: [string, string][]) => {
    const scelti = (parametri.get(chiave) || "").split(",").filter(Boolean);
    const cambia = (k: string) => imposta(chiave, (scelti.includes(k) ? scelti.filter((x) => x !== k) : [...scelti, k]).join(","));
    const testo = scelti.length === 0 ? vuoto : scelti.length <= 2 ? scelti.map((k) => voci.find(([v]) => v === k)?.[1] || k).join(", ")
      : `${scelti.length} regioni`;
    return (
      <details className={`multiplo ${scelti.length ? "filtro-attivo" : ""}`}>
        <summary>{testo}</summary>
        <div className="multiplo-voci">
          {scelti.length > 0 && <button type="button" onClick={() => imposta(chiave, "")}>Togli tutte</button>}
          {voci.map(([k, v]) => (
            <label key={k}><input type="checkbox" checked={scelti.includes(k)} onChange={() => cambia(k)} /> {v}</label>
          ))}
        </div>
      </details>
    );
  };
  const elenco = (campo: string) => ((valori?.[campo] as string[]) || []).map((v) => [v, nome(v)] as [string, string]);
  const regioni = (parametri.get("regione") || "").split(",").filter(Boolean);
  const province = Object.entries(valori?.province || {}).filter(([, r]) => !regioni.length || regioni.includes(r))
    .map(([p]) => [p, p] as [string, string]).sort();

  const perPagina = 50;
  const ultimaPagina = risposta ? Math.max(1, Math.ceil(risposta.totale / perPagina)) : 1;
  const filtriAttivi = [...parametri.keys()].filter((k) => k !== "pagina").length > 0;
  return (
    <>
      <h1>Catalogo dei bandi</h1>
      <div className="avviso">Un bando per riga, con la sua scheda. I filtri su <b>chi può partecipare</b> (territorio, soggetto,
        forma giuridica, dimensione, ATECO) mostrano i bandi che lo ammettono e quelli senza limiti: <b>✓ compatibile</b>.
        Se la scheda non lo dice, o è fatta solo su una sintesi, il bando esce lo stesso con <b>? da verificare</b> e il motivo.
        {risposta && <> Schede: {risposta.con_scheda}, di cui <b>{risposta.proponibili} proponibili</b> (fatte sul bando ufficiale);
          le altre, fatte solo su una sintesi, stanno <b>in disparte</b> e si vedono scegliendolo nei filtri.
          Bandi ancora senza scheda: {risposta.senza_scheda}.</>}</div>

      <form className="filtri" onSubmit={(e) => { e.preventDefault(); imposta("q", testo); }}>
        <input type="text" placeholder="Cerca nel titolo, nell'ente, nella sintesi o il numero…" value={testo} onChange={(e) => setTesto(e.target.value)} />
        <button type="submit">Cerca</button>
        <select value={parametri.get("stato") || "aperti"} onChange={(e) => imposta("stato", e.target.value === "aperti" ? "" : e.target.value)}>
          <option value="aperti">Aperti e in arrivo</option><option value="aperto">Solo aperti</option>
          <option value="in_arrivo">Solo in arrivo</option><option value="chiuso">Chiusi</option>
          <option value="non_noto">Senza date (stato non noto)</option><option value="tutti">Tutti</option>
        </select>
        {menu("scadenza_entro", "Qualunque scadenza", [["7", "Scade entro 7 giorni"], ["30", "Scade entro 30 giorni"], ["90", "Scade entro 90 giorni"]])}
        {menu("livello", "Tutti gli enti", Object.entries(NOMI_TIPO).filter(([k]) => k !== "contesto"))}
      </form>

      <div className="filtri">
        <span className="piccolo etichetta-filtri">Chi partecipa</span>
        {multiplo("regione", "Tutte le regioni", Object.entries(valori?.regioni || {}).sort((a, b) => a[1].localeCompare(b[1])))}
        {menu("provincia", "Provincia", province)}
        {menu("soggetto", "Tipo di soggetto", elenco("soggetti_ammessi").filter(([k]) => k !== "altro"))}
        {menu("forma_giuridica", "Forma giuridica", elenco("forme_giuridiche_ammesse").filter(([k]) => k !== "altro"))}
        {menu("dimensione", "Dimensione", elenco("dimensioni_ammesse"))}
        <form onSubmit={(e) => { e.preventDefault(); imposta("ateco", ateco.trim()); }}>
          <input type="text" className={`ateco ${parametri.get("ateco") ? "filtro-attivo" : ""}`} placeholder="ATECO (es. 62.01)"
            value={ateco} onChange={(e) => setAteco(e.target.value)} onBlur={() => imposta("ateco", ateco.trim())} />
        </form>
        {menu("requisito", "Riservati o con punti per…", elenco("requisiti_speciali_obbligatori").filter(([k]) => k !== "altro"))}
      </div>

      <div className="filtri">
        <span className="piccolo etichetta-filtri">Cosa e come</span>
        {menu("tipo_agevolazione", "Tipo di agevolazione", elenco("tipi_agevolazione"))}
        {menu("tema", "Tema", elenco("temi"))}
        {menu("categoria_spesa", "Spese finanziate", elenco("categorie_spesa"))}
        {menu("modalita", "Selezione", elenco("modalita_selezione"))}
        {menu("regime", "Regime d'aiuto", elenco("regime_aiuto"))}
        <select value={parametri.get("in_disparte") || "no"} onChange={(e) => imposta("in_disparte", e.target.value === "no" ? "" : e.target.value)}
          className={parametri.get("in_disparte") ? "filtro-attivo" : ""}>
          <option value="no">Solo bandi proponibili (scheda sul bando ufficiale)</option>
          <option value="anche">Anche quelli in disparte</option>
          <option value="solo">Solo quelli in disparte (senza bando ufficiale)</option>
        </select>
        {filtriAttivi && <button type="button" onClick={() => { setTesto(""); setAteco(""); setParametri(new URLSearchParams()); }}>Azzera filtri</button>}
      </div>

      {risposta && <p className="piccolo"><b>{risposta.totale}</b> bandi: {risposta.conteggi.compatibile} ✓ compatibili,
        {" "}{risposta.conteggi.da_verificare} ? da verificare</p>}
      {!risposta ? <div className="caricamento">Caricamento…</div> : (
        <table>
          <thead><tr><th></th><th>Bando</th><th>Stato e scadenza</th><th>Agevolazione</th><th className="nascondi-mobile">Ente</th></tr></thead>
          <tbody>{risposta.bandi.map((b) => <Riga key={b.id} b={b} />)}</tbody>
        </table>
      )}
      <div className="pagine">
        <button disabled={pagina <= 1} onClick={() => imposta("pagina", String(pagina - 1))}>← Precedente</button>
        <span className="piccolo">pagina {pagina} di {ultimaPagina}</span>
        <button disabled={pagina >= ultimaPagina} onClick={() => imposta("pagina", String(pagina + 1))}>Successiva →</button>
      </div>
    </>
  );
}

export function SegnoEsito({ livello }: { livello: string }) {
  const segni: Record<string, [string, string]> = {
    compatibile: ["✓", "compatibile"], da_verificare: ["?", "da verificare"], escluso: ["✗", "escluso"],
  };
  const [segno, titolo] = segni[livello] || ["", ""];
  return <span className={`segno-esito ${livello}`} title={titolo}>{segno}</span>;
}

export function Importo({ b }: { b: Pick<BandoRiga, "contributo_massimo" | "fondo_perduto_massimo" | "finanziamento_massimo" | "percentuale"> }) {
  const massimo = b.contributo_massimo ?? b.fondo_perduto_massimo ?? b.finanziamento_massimo;
  return (
    <>{massimo != null && <div>fino a {euro(massimo)}</div>}
      {b.percentuale != null && <div className="piccolo">{b.percentuale}% delle spese</div>}</>
  );
}

function Riga({ b }: { b: BandoRiga }) {
  return (
    <tr>
      <td><SegnoEsito livello={b.esito.livello} /></td>
      <td><Link to={`/bandi/${b.id}`} className="titolo-annuncio">{b.titolo}</Link>
        {b.url && <> <a href={b.url} target="_blank" rel="noreferrer" className="piccolo" title="Pagina ufficiale">ufficiale ↗</a></>}
        {b.sintesi && <div className="riassunto">{b.sintesi}{b.sintesi.length >= 260 ? "…" : ""}</div>}
        {b.esito.da_verificare.length > 0 && (
          <ul className="motivi da_verificare">{b.esito.da_verificare.map((m) => <li key={m}>? {m}</li>)}</ul>
        )}</td>
      <td><span className={`stato-bando ${b.stato || "non_noto"}`}>{b.stato ? nome(b.stato) : "stato non noto"}</span>
        {b.scadenza && <div className="scadenza">scade il {data(b.scadenza)}{b.ora_scadenza ? ` ore ${b.ora_scadenza.slice(0, 5)}` : ""}</div>}
        {b.stato === "in_arrivo" && b.data_apertura && <div className="piccolo">apre il {data(b.data_apertura)}</div>}
        {b.modalita_selezione && <div className="piccolo">{nome(b.modalita_selezione)}</div>}</td>
      <td>{(b.tipi_agevolazione && b.tipi_agevolazione.length ? b.tipi_agevolazione : [b.tipo_agevolazione]).filter(Boolean)
        .map((t) => <span key={t} className="etichetta-tipo">{nome(t)}</span>)}
        <Importo b={b} /></td>
      <td className="nascondi-mobile">{b.livelli.map((l) => <span key={l} className="etichetta-tipo">{NOMI_TIPO[l] || l}</span>)}
        <div className="piccolo">{b.ente}</div></td>
    </tr>
  );
}
