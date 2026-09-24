import { useState } from "react";
import { api, Esito, NOMI_DECISO_DA, NOMI_ESITO } from "./api";

// Esito dello smistamento con i tre pulsanti per correggerlo a mano.
// La correzione si salva come decisa da Matteo; la proposta delle regole resta nel database per tararle.
export default function Smistamento({ annuncioId, esito, decisoDa, motivo }:
  { annuncioId: number; esito: Esito | null | undefined; decisoDa: string | null | undefined; motivo?: string | null }) {
  const [attuale, setAttuale] = useState<{ esito: Esito | null; da: string | null }>({ esito: esito ?? null, da: decisoDa ?? null });
  const [inCorso, setInCorso] = useState(false);
  const correggi = async (nuovo: Esito) => {
    setInCorso(true);
    try {
      const r = await api.correggiSmistamento(annuncioId, nuovo);
      setAttuale({ esito: r.esito, da: r.deciso_da });
    } catch (e) {
      alert(String(e));
    } finally {
      setInCorso(false);
    }
  };
  const pulsanti: [Esito, string, string][] = [["rilevante", "✓", "È rilevante"], ["da_rivedere", "?", "Da rivedere"], ["non_rilevante", "✗", "Non è rilevante"]];
  return (
    <div className="smistamento">
      <span className={`esito ${attuale.esito || "nessuno"}`} title={motivo || undefined}>
        {attuale.esito ? NOMI_ESITO[attuale.esito] : "Non smistato"}
      </span>
      {attuale.da && <span className="piccolo"> ({NOMI_DECISO_DA[attuale.da] || attuale.da})</span>}
      <div className="correggi">
        {pulsanti.map(([valore, simbolo, titolo]) => (
          <button key={valore} title={titolo} disabled={inCorso || attuale.esito === valore}
            className={attuale.esito === valore ? "scelto" : ""} onClick={() => correggi(valore)}>{simbolo}</button>
        ))}
      </div>
    </div>
  );
}
