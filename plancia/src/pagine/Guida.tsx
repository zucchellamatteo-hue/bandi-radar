import { Fragment, ReactNode, useEffect, useState } from "react";
import { api } from "../api";

// Guida (05/10/2026): sezioni di app/guida/guida.yaml, filtrate dal server secondo il ruolo e i permessi di chi legge.

function grassetto(riga: string): ReactNode[] {
  return riga.split(/(\*\*[^*]+\*\*)/).map((pezzo, i) =>
    pezzo.startsWith("**") && pezzo.endsWith("**") ? <b key={i}>{pezzo.slice(2, -2)}</b> : <Fragment key={i}>{pezzo}</Fragment>);
}

// Testo semplice: paragrafi separati da una riga vuota, elenchi con "- " o "1. " (anche dopo una frase che li introduce),
// **grassetto**.
export function Testo({ testo }: { testo: string }) {
  const pezzi: ReactNode[] = [];
  testo.trim().split(/\n\s*\n/).forEach((blocco, i) => {
    let testoCorrente: string[] = [], lista: string[] = [], numerata = false;
    const chiudi = (k: string) => {
      if (testoCorrente.length) pezzi.push(<p key={`${k}p`}>{grassetto(testoCorrente.join(" "))}</p>);
      if (lista.length) {
        const voci = lista.map((r, j) => <li key={j}>{grassetto(r)}</li>);
        pezzi.push(numerata ? <ol key={`${k}l`}>{voci}</ol> : <ul key={`${k}l`}>{voci}</ul>);
      }
      testoCorrente = []; lista = [];
    };
    blocco.split("\n").map((r) => r.trim()).filter(Boolean).forEach((r, j) => {
      const puntata = /^- /.test(r), numero = /^\d+\. /.test(r);
      if (puntata || numero) {
        if (testoCorrente.length || (lista.length && numerata !== numero)) chiudi(`${i}-${j}`);
        numerata = numero; lista.push(r.replace(/^(- |\d+\. )/, ""));
      } else if (lista.length) { lista[lista.length - 1] += " " + r; }
      else testoCorrente.push(r);
    });
    chiudi(`${i}-fine`);
  });
  return <>{pezzi}</>;
}

export default function Guida() {
  const [sezioni, setSezioni] = useState<{ id: string; titolo: string; testo: string; per: string[] }[] | null>(null);
  useEffect(() => { api.guida().then(setSezioni); }, []);
  if (!sezioni) return <div className="caricamento">Caricamento…</div>;
  return (
    <div className="guida">
      <h1>Guida</h1>
      <p className="piccolo">Qui trovi come fare le cose che il tuo profilo ti permette.</p>
      <ul className="indice">{sezioni.map((s) => <li key={s.id}><a href={`#${s.id}`}>{s.titolo}</a></li>)}</ul>
      {sezioni.map((s) => (
        <section key={s.id} id={s.id} className="riquadro">
          <h2>{s.titolo}</h2>
          <Testo testo={s.testo} />
        </section>))}
    </div>
  );
}
