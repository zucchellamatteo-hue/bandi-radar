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
import Campagne from "./pagine/Campagne";
import Misure from "./pagine/Misure";
import Passi from "./pagine/Passi";
import Guida from "./pagine/Guida";
import { Abbonamento, MieImprese, MieiBandi, MieRichieste, ModuloImpresa, SchedaImpresa } from "./pagine/AreaImpresa";
import { ContestoUtente, puo } from "./utente";


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
  const lavoro = puo(utente, "lavoro");      // tutte le pagine di lavoro (in sola lettura senza "modifiche")
  const imprese = puo(utente, "imprese");
  return (
    <ContestoUtente.Provider value={utente}>
      <header className="barra">
        <span className="logo">Bandi Radar</span>
        {lavoro && <nav>
          <NavLink to="/" end className={classe}>Fonti</NavLink>{" · "}
          <NavLink to="/catalogo" className={classe}>Catalogo</NavLink>{" · "}
          <NavLink to="/misure" className={classe}>Misure</NavLink>{" · "}
          <NavLink to="/profili" className={classe}>Profili</NavLink>{" · "}
          <NavLink to="/annunci" end className={classe}>Annunci</NavLink>{" · "}
          <NavLink to="/lavorazione" className={classe}>Lavorazione</NavLink>{" · "}
          <NavLink to="/supervisione" className={classe}>Supervisione</NavLink>{" · "}
          <NavLink to="/doppioni" className={classe}>Doppioni</NavLink>{" · "}
          <NavLink to="/novita" className={classe}>Novità</NavLink>{" · "}
          <NavLink to="/feedback" className={classe}>Feedback</NavLink>{" · "}
          {imprese && <><NavLink to="/imprese" className={classe}>Imprese</NavLink>{" · "}
            <NavLink to="/campagne" className={classe}>Campagne</NavLink>{" · "}</>}
          <NavLink to="/passi" className={classe}>Prossimi passi</NavLink>{" · "}
          {admin && <><NavLink to="/utenti" className={classe}>Utenti</NavLink>{" · "}</>}
          <NavLink to="/guida" className={classe}>Guida</NavLink>
        </nav>}
        {utente.ruolo === "impresa" && <nav>
          <NavLink to="/impresa" end className={classe}>I miei bandi</NavLink>{" · "}
          <NavLink to="/impresa/misure" className={classe}>Agevolazioni fiscali</NavLink>{" · "}
          <NavLink to="/impresa/imprese" className={classe}>Le mie imprese</NavLink>{" · "}
          <NavLink to="/impresa/richieste" className={classe}>Richieste di supporto</NavLink>{" · "}
          <NavLink to="/impresa/abbonamento" className={classe}>Abbonamento</NavLink>{" · "}
          <NavLink to="/guida" className={classe}>Guida</NavLink>
        </nav>}
        {utente.ruolo === "revisore" && !lavoro && <nav>
          <NavLink to="/catalogo" className={classe}>Catalogo</NavLink>{" · "}
          <NavLink to="/misure" className={classe}>Misure</NavLink>{" · "}
          <NavLink to="/feedback" className={classe}>I miei giudizi</NavLink>
          {imprese && <>{" · "}<NavLink to="/imprese" className={classe}>Imprese</NavLink>{" · "}
            <NavLink to="/campagne" className={classe}>Campagne</NavLink></>}{" · "}
          <NavLink to="/guida" className={classe}>Guida</NavLink>
        </nav>}
        <span className="chi-sono">
          {utente.nome || utente.email} <span className="piccolo">({NOMI_RUOLO_UTENTE[utente.ruolo]})</span>{" "}
          <button onClick={esci}>Esci</button>
        </span>
      </header>
      <main>
        {lavoro ? (
          <Routes>
            <Route path="/" element={<Fonti />} />
            <Route path="/accedi" element={<Navigate to="/" replace />} />
            <Route path="/registrati" element={<Navigate to="/" replace />} />
            <Route path="/fonti/:id" element={<DettaglioFonte />} />
            <Route path="/catalogo" element={<Catalogo />} />
            <Route path="/guida" element={<Guida />} />
            <Route path="/passi" element={<Passi />} />
            <Route path="/misure" element={<Misure />} />
            <Route path="/misure/:id" element={<Misure />} />
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
            {admin && <Route path="/utenti" element={<Utenti />} />}
            <Route path="/feedback" element={<Feedback />} />
            {imprese && <Route path="/imprese" element={<Imprese />} />}
            {imprese && <Route path="/campagne" element={<Campagne />} />}
            {imprese && <Route path="/campagne/:id" element={<Campagne />} />}
            <Route path="/impresa" element={<MieiBandi />} />
            <Route path="/impresa/imprese" element={<MieImprese />} />
            <Route path="/impresa/imprese/:id" element={<ModuloImpresa />} />
            <Route path="/impresa/bandi/:id" element={<SchedaImpresa />} />
            <Route path="/impresa/richieste" element={<MieRichieste />} />
            <Route path="/impresa/abbonamento" element={<Abbonamento />} />
            <Route path="/impresa/misure" element={<Misure base="/impresa/misure" />} />
            <Route path="/impresa/misure/:id" element={<Misure base="/impresa/misure" />} />
          </Routes>
        ) : utente.ruolo === "revisore" ? (
          <Routes>
            <Route path="/catalogo" element={<Catalogo />} />
            <Route path="/guida" element={<Guida />} />
            <Route path="/misure" element={<Misure />} />
            <Route path="/misure/:id" element={<Misure />} />
            <Route path="/bandi/:id" element={<Bando />} />
            <Route path="/feedback" element={<Feedback />} />
            {imprese && <Route path="/imprese" element={<Imprese />} />}
            {imprese && <Route path="/campagne" element={<Campagne />} />}
            {imprese && <Route path="/campagne/:id" element={<Campagne />} />}
            <Route path="*" element={<Navigate to="/catalogo" replace />} />
          </Routes>
        ) : (
          <Routes>
            <Route path="/impresa" element={<MieiBandi />} />
            <Route path="/impresa/imprese" element={<MieImprese />} />
            <Route path="/impresa/imprese/:id" element={<ModuloImpresa />} />
            <Route path="/impresa/bandi/:id" element={<SchedaImpresa />} />
            <Route path="/impresa/richieste" element={<MieRichieste />} />
            <Route path="/impresa/abbonamento" element={<Abbonamento />} />
            <Route path="/impresa/misure" element={<Misure base="/impresa/misure" />} />
            <Route path="/impresa/misure/:id" element={<Misure base="/impresa/misure" />} />
            <Route path="/guida" element={<Guida />} />
            <Route path="*" element={<Navigate to="/impresa" replace />} />
          </Routes>
        )}
      </main>
    </ContestoUtente.Provider>
  );
}
