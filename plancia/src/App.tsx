import { useEffect, useState } from "react";
import { NavLink, Navigate, Route, Routes, useLocation, useNavigate } from "react-router-dom";
import { api, NOMI_RUOLO_UTENTE, Utente } from "./api";
import Fonti from "./pagine/Fonti";
import DettaglioFonte from "./pagine/DettaglioFonte";
import Catalogo from "./pagine/Catalogo";
import Annunci from "./pagine/Annunci";
import DettaglioAnnuncio from "./pagine/DettaglioAnnuncio";
import Novita from "./pagine/Novita";
import Settimana from "./pagine/Settimana";
import Bando from "./pagine/Bando";
import Doppioni from "./pagine/Doppioni";
import Profili from "./pagine/Profili";
import Lavorazione from "./pagine/Lavorazione";
import Supervisione from "./pagine/Supervisione";
import Utenti from "./pagine/Utenti";
import Feedback from "./pagine/Feedback";
import { Accesso, ConfermaEmail, Disiscrizione, ImpostaPassword, Registrati } from "./pagine/Accesso";
import Imprese from "./pagine/Imprese";
import { MieImprese, MieiBandi, MieRichieste, ModuloImpresa, SchedaImpresa } from "./pagine/AreaImpresa";
import { ContestoUtente } from "./utente";


export default function App() {
  const [utente, setUtente] = useState<Utente | null | undefined>(undefined);   // undefined = sto controllando
  const posizione = useLocation();
  const vai = useNavigate();
  useEffect(() => { api.io().then(setUtente).catch(() => setUtente(null)); }, []);

  // Pagine raggiungibili dai link delle email, anche senza accesso.
  if (posizione.pathname === "/imposta-password") return <ImpostaPassword entrato={setUtente} />;
  if (posizione.pathname === "/conferma-email") return <ConfermaEmail entrato={setUtente} />;
  if (posizione.pathname === "/disiscrizione") return <Disiscrizione />;
  if (posizione.pathname === "/registrati" && utente === null) return <Registrati />;
  if (utente === undefined) return null;
  if (utente === null) return <Accesso entrato={setUtente} />;

  const esci = async () => { await api.esci().catch(() => null); setUtente(null); vai("/", { replace: true }); };
  const classe = ({ isActive }: { isActive: boolean }) => (isActive ? "attivo" : "");
  const admin = utente.ruolo === "admin";
  return (
    <ContestoUtente.Provider value={utente}>
      <header className="barra">
        <span className="logo">Bandi Radar</span>
        {admin && <nav>
          <NavLink to="/" end className={classe}>Fonti</NavLink>{" · "}
          <NavLink to="/catalogo" className={classe}>Catalogo</NavLink>{" · "}
          <NavLink to="/profili" className={classe}>Profili</NavLink>{" · "}
          <NavLink to="/annunci" end className={classe}>Annunci</NavLink>{" · "}
          <NavLink to="/lavorazione" className={classe}>Lavorazione</NavLink>{" · "}
          <NavLink to="/supervisione" className={classe}>Supervisione</NavLink>{" · "}
          <NavLink to="/doppioni" className={classe}>Doppioni</NavLink>{" · "}
          <NavLink to="/novita" className={classe}>Novità</NavLink>{" · "}
          <NavLink to="/feedback" className={classe}>Feedback</NavLink>{" · "}
          <NavLink to="/imprese" className={classe}>Imprese</NavLink>{" · "}
          <NavLink to="/utenti" className={classe}>Utenti</NavLink>
        </nav>}
        {utente.ruolo === "impresa" && <nav>
          <NavLink to="/impresa" end className={classe}>I miei bandi</NavLink>{" · "}
          <NavLink to="/impresa/imprese" className={classe}>Le mie imprese</NavLink>{" · "}
          <NavLink to="/impresa/richieste" className={classe}>Richieste di supporto</NavLink>
        </nav>}
        {utente.ruolo === "revisore" && <nav>
          <NavLink to="/catalogo" className={classe}>Catalogo</NavLink>{" · "}
          <NavLink to="/feedback" className={classe}>I miei giudizi</NavLink>
        </nav>}
        <span className="chi-sono">
          {utente.nome || utente.email} <span className="piccolo">({NOMI_RUOLO_UTENTE[utente.ruolo]})</span>{" "}
          <button onClick={esci}>Esci</button>
        </span>
      </header>
      <main>
        {admin ? (
          <Routes>
            <Route path="/" element={<Fonti />} />
            <Route path="/fonti/:id" element={<DettaglioFonte />} />
            <Route path="/catalogo" element={<Catalogo />} />
            <Route path="/annunci" element={<Annunci />} />
            <Route path="/profili" element={<Profili />} />
            <Route path="/lavorazione" element={<Lavorazione />} />
            <Route path="/supervisione" element={<Supervisione />} />
            <Route path="/supervisione/:id" element={<Supervisione />} />
            <Route path="/profili/:codice" element={<Profili />} />
            <Route path="/annunci/:id" element={<DettaglioAnnuncio />} />
            <Route path="/bandi/:id" element={<Bando />} />
            <Route path="/doppioni" element={<Doppioni />} />
            <Route path="/novita" element={<Novita />} />
            <Route path="/novita/:chiave" element={<Settimana />} />
            <Route path="/utenti" element={<Utenti />} />
            <Route path="/feedback" element={<Feedback />} />
            <Route path="/imprese" element={<Imprese />} />
            <Route path="/impresa" element={<MieiBandi />} />
            <Route path="/impresa/imprese" element={<MieImprese />} />
            <Route path="/impresa/imprese/:id" element={<ModuloImpresa />} />
            <Route path="/impresa/bandi/:id" element={<SchedaImpresa />} />
            <Route path="/impresa/richieste" element={<MieRichieste />} />
          </Routes>
        ) : utente.ruolo === "revisore" ? (
          <Routes>
            <Route path="/catalogo" element={<Catalogo />} />
            <Route path="/bandi/:id" element={<Bando />} />
            <Route path="/feedback" element={<Feedback />} />
            <Route path="*" element={<Navigate to="/catalogo" replace />} />
          </Routes>
        ) : (
          <Routes>
            <Route path="/impresa" element={<MieiBandi />} />
            <Route path="/impresa/imprese" element={<MieImprese />} />
            <Route path="/impresa/imprese/:id" element={<ModuloImpresa />} />
            <Route path="/impresa/bandi/:id" element={<SchedaImpresa />} />
            <Route path="/impresa/richieste" element={<MieRichieste />} />
            <Route path="*" element={<Navigate to="/impresa" replace />} />
          </Routes>
        )}
      </main>
    </ContestoUtente.Provider>
  );
}
