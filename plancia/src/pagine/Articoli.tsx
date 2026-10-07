import { useEffect, useState } from "react";
import { api, Articolo, data } from "../api";
import { eAdmin, usePuo, useUtente } from "../utente";

// Blog (07/10/2026, richiesta di Matteo): articoli pubblici su /blog per Google e i motori di risposta IA.
// Chi ha "modifiche" scrive e corregge le bozze; solo l'admin pubblica, rimette in bozza o archivia.
// Il corpo e' Markdown semplice: "## titolo", "### sottotitolo", "- voce", "1. voce", **grassetto**, [testo](https://...).
// La sezione "## Domande frequenti" con le domande in "### ..." diventa anche il dato strutturato FAQPage.

type Modulo = { titolo: string; slug: string; sommario: string; corpo: string; fonti: string; bando_id: string; misura_id: string; autore: string };
const VUOTO: Modulo = { titolo: "", slug: "", sommario: "", corpo: "", fonti: "", bando_id: "", misura_id: "", autore: "" };
const NOME_STATO: Record<string, string> = { bozza: "bozza", pubblicato: "pubblicato", archiviato: "archiviato" };

const daArticolo = (a: Articolo): Modulo => ({
  titolo: a.titolo, slug: a.slug, sommario: a.sommario, corpo: a.corpo,
  fonti: (a.fonti || []).map((f) => `${f.nome} | ${f.url}`).join("\n"), bando_id: a.bando_id ? String(a.bando_id) : "",
  misura_id: a.misura_id || "", autore: a.autore || "",
});
const perApi = (m: Modulo) => ({ ...m, bando_id: m.bando_id.trim() || null, misura_id: m.misura_id || null, autore: m.autore || null, slug: m.slug || null });

export default function Articoli() {
  const modifiche = usePuo("modifiche");
  const admin = eAdmin(useUtente());
  const [r, setR] = useState<Awaited<ReturnType<typeof api.articoli>> | null>(null);
  const [errore, setErrore] = useState<string | null>(null);
  const [modulo, setModulo] = useState<{ id: number | null; m: Modulo } | null>(null);
  const [anteprima, setAnteprima] = useState<string | null>(null);
  const ricarica = () => api.articoli().then(setR).catch((e) => setErrore(String(e.message || e)));
  useEffect(() => { ricarica(); }, []);
  useEffect(() => {
    if (anteprima === null) return;
    const esc = (e: KeyboardEvent) => { if (e.key === "Escape") setAnteprima(null); };
    document.addEventListener("keydown", esc);
    document.body.style.overflow = "hidden";
    return () => { document.removeEventListener("keydown", esc); document.body.style.overflow = ""; };
  }, [anteprima]);
  const azione = async (f: () => Promise<unknown>) => {
    setErrore(null);
    try { await f(); ricarica(); return true; } catch (e) { setErrore(e instanceof Error ? e.message : String(e)); return false; }
  };
  const mostra = async (id: number | null, m: Modulo) => {
    setErrore(null);
    try { setAnteprima((await api.anteprimaArticolo({ ...perApi(m), id })).html); }
    catch (e) { setErrore(e instanceof Error ? e.message : String(e)); }
  };
  if (!r) return errore ? <div className="allarme">{errore}</div> : <div className="caricamento">Caricamento…</div>;
  return (
    <>
      <h1>Blog</h1>
      <p className="piccolo">Articoli pubblici su <a href="/blog" target="_blank" rel="noreferrer">/blog</a>: brevi guide sui bandi
        più cercati e su quelli di nicchia, per farsi trovare da Google e dai motori di risposta IA e portare alla registrazione.
        Un articolo nasce in <b>bozza</b>; lo <b>pubblica</b> solo l'amministratore. Se il bando collegato chiude o scade, la
        pagina mostra da sola il riquadro «Bando chiuso». Senza autore firma «{r.autore_predefinito}».</p>
      {errore && <div className="allarme">{errore}</div>}
      {modifiche && !modulo && <p><button className="primario" onClick={() => setModulo({ id: null, m: VUOTO })}>Nuovo articolo</button></p>}
      {modulo && <form className="riquadro" onSubmit={async (e) => {
        e.preventDefault();
        const ok = await azione(() => modulo.id ? api.modificaArticolo(modulo.id, perApi(modulo.m)) : api.creaArticolo(perApi(modulo.m)));
        if (ok) setModulo(null);
      }}>
        <h2>{modulo.id ? `Modifica articolo n. ${modulo.id}` : "Nuovo articolo"}</h2>
        <Campi m={modulo.m} misure={r.misure} cambia={(c) => setModulo({ ...modulo, m: { ...modulo.m, ...c } })} />
        <button type="submit" className="primario">Salva{modulo.id ? "" : " come bozza"}</button>{" "}
        <button type="button" onClick={() => mostra(modulo.id, modulo.m)}>Anteprima</button>{" "}
        <button type="button" onClick={() => setModulo(null)}>Annulla</button>
      </form>}
      {/* L'anteprima si apre sopra la pagina (07/10): in cima all'elenco non si vedeva se si premeva su un articolo in basso. */}
      {anteprima !== null && <div className="anteprima-sfondo" role="dialog" aria-modal="true" aria-label="Anteprima dell'articolo"
        onClick={(e) => { if (e.target === e.currentTarget) setAnteprima(null); }}>
        <div className="anteprima-finestra">
          <div className="anteprima-testa"><b>Anteprima</b> <span className="piccolo">come la vedrà chi legge (link non attivi)</span>
            <button className="primario" onClick={() => setAnteprima(null)}>Chiudi</button></div>
          <iframe title="Anteprima dell'articolo" srcDoc={anteprima} sandbox="" />
        </div>
      </div>}
      {!r.articoli.length && <p>Nessun articolo.</p>}
      {r.articoli.map((a) => (
        <div key={a.id} className="riquadro" style={a.stato === "bozza" ? { borderStyle: "dashed" } : a.stato === "archiviato" ? { opacity: .7 } : undefined}>
          <div><b>{a.titolo}</b> <span className="piccolo">· {NOME_STATO[a.stato] || a.stato}
            {a.stato === "pubblicato" && <> · <a href={`/blog/${a.slug}`} target="_blank" rel="noreferrer">apri /blog/{a.slug}</a></>}</span></div>
          <p className="piccolo">{a.sommario}</p>
          {a.chiuso && <div className="allarme">Bando chiuso: «{a.chiuso.titolo}» ({a.chiuso.motivo}). La pagina pubblica mostra già il riquadro;
            valuta se archiviarlo o aggiornarlo.</div>}
          <p className="piccolo">#{a.id} · /blog/{a.slug} · {a.parole} parole · aggiornato il {data(a.aggiornato_il)}
            {a.pubblicato_il ? ` · pubblicato il ${data(a.pubblicato_il)}` : ""}
            {a.bando_id ? ` · bando n. ${a.bando_id}${a.bando_titolo ? ` (${a.bando_titolo.slice(0, 60)})` : ""}` : ""}
            {a.misura_id ? ` · misura ${a.misura_id}` : ""}{a.creato_da ? ` · scritto da ${a.creato_da}` : ""}
            {a.aggiornato_da && a.aggiornato_da !== a.creato_da ? `, modificato da ${a.aggiornato_da}` : ""}</p>
          <div>
            <button onClick={() => mostra(a.id, daArticolo(a))}>Anteprima</button>{" "}
            {modifiche && (a.stato === "bozza" || admin) &&
              <button onClick={() => { setModulo({ id: a.id, m: daArticolo(a) }); window.scrollTo(0, 0); }}>Modifica</button>}{" "}
            {admin && a.stato !== "pubblicato" &&
              <button className="primario" onClick={() => { if (confirm("Pubblicare l'articolo? Diventa visibile a tutti su /blog.")) azione(() => api.modificaArticolo(a.id, { stato: "pubblicato" })); }}>Pubblica</button>}{" "}
            {admin && a.stato === "pubblicato" && <button onClick={() => azione(() => api.modificaArticolo(a.id, { stato: "bozza" }))}>Rimetti in bozza</button>}{" "}
            {admin && a.stato !== "archiviato" && <button onClick={() => azione(() => api.modificaArticolo(a.id, { stato: "archiviato" }))}>Archivia</button>}{" "}
            {modifiche && (a.stato === "bozza" || admin) &&
              <button onClick={() => { if (confirm("Cancellare questo articolo?")) azione(() => api.cancellaArticolo(a.id)); }}>✗</button>}
          </div>
        </div>
      ))}
    </>
  );
}

function Campi({ m, misure, cambia }: { m: Modulo; misure: { id: string; nome: string }[]; cambia: (c: Partial<Modulo>) => void }) {
  return (
    <div className="modulo-news">
      <input type="text" placeholder="titolo" value={m.titolo} maxLength={200} required style={{ width: "100%" }}
        onChange={(e) => cambia({ titolo: e.target.value })} />
      <div className="filtri">
        <input type="text" placeholder="indirizzo: /blog/... (vuoto = dal titolo)" value={m.slug} onChange={(e) => cambia({ slug: e.target.value })} />
        <input type="text" placeholder="n. del bando collegato" value={m.bando_id} style={{ minWidth: 0, width: "12rem" }}
          onChange={(e) => cambia({ bando_id: e.target.value })} />
        <select value={m.misura_id} onChange={(e) => cambia({ misura_id: e.target.value })}>
          <option value="">nessuna misura nazionale</option>
          {misure.map((x) => <option key={x.id} value={x.id}>{x.nome}</option>)}</select>
        <input type="text" placeholder="autore (vuoto = il commercialista)" value={m.autore} onChange={(e) => cambia({ autore: e.target.value })} />
      </div>
      <textarea rows={2} placeholder="sommario: 1-2 frasi, è la descrizione che compare su Google" value={m.sommario} maxLength={300} required
        style={{ width: "100%" }} onChange={(e) => cambia({ sommario: e.target.value })} />
      <p className="piccolo">{m.sommario.length}/300 caratteri (Google ne mostra circa 155)</p>
      <textarea rows={22} placeholder={"testo in Markdown semplice:\n## A chi serve\nParagrafo...\n- voce di elenco\n\n## Domande frequenti\n### Domanda?\nRisposta."}
        value={m.corpo} required style={{ width: "100%", fontFamily: "ui-monospace, monospace", fontSize: 16 }}
        onChange={(e) => cambia({ corpo: e.target.value })} />
      <textarea rows={3} placeholder={"fonti ufficiali, una per riga: nome | https://..."} value={m.fonti} style={{ width: "100%" }}
        onChange={(e) => cambia({ fonti: e.target.value })} />
    </div>
  );
}
