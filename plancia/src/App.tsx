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
import Segnalazioni from "./pagine/Segnalazioni";
import Segnala from "./Segnala";
import Guida from "./pagine/Guida";
import Account from "./pagine/Account";
import { Abbonamento, MieImprese, MieiBandi, MieRichieste, ModuloImpresa, SchedaImpresa } from "./pagine/AreaImpresa";
import { ContestoUtente, puo } from "./utente";
import { useTabelleMobili } from "./tabelle";


export default function App() {
  const [utente, setUtente] = useState<Utente | null | undefined>(undefined);   // undefined = sto controllando
  const posizione = useLocation();
  const vai = useNavigate();
  const [menuAperto, setMenuAperto] = useState(false);
  useEffect(() => { api.io().then(setUtente).catch(() => setUtente(null)); }, []);
  useEffect(() => { setMenuAperto(false); }, [posizione.pathname, posizione.search]);
  useTabelleMobili();

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
  // Le voci del menu: [indirizzo, nome, solo indirizzo esatto]. Sul computer stanno in fila nella barra, sul telefono
  // in un menu a tendina aperto dal pulsante "☰" (06/10).
  const voci: [string, string, boolean?][] = lavoro ? [
    ["/", "Fonti", true], ["/catalogo", "Catalogo"], ["/misure", "Misure"], ["/profili", "Profili"], ["/annunci", "Annunci", true],
    ["/lavorazione", "Lavorazione"], ["/supervisione", "Supervisione"], ["/doppioni", "Doppioni"], ["/novita", "Novità"],
    ["/feedback", "Feedback"], ["/segnalazioni", "Segnalazioni"],
    ...(imprese ? [["/imprese", "Imprese"], ["/campagne", "Campagne"]] as [string, string][] : []),
    ["/passi", "Prossimi passi"], ...(admin ? [["/utenti", "Utenti"]] as [string, string][] : []), ["/guida", "Guida"],
  ] : utente.ruolo === "impresa" ? [
    ["/impresa", "I miei bandi", true], ["/impresa/misure", "Agevolazioni fiscali"], ["/impresa/imprese", "Le mie imprese"],
    ["/impresa/richieste", "Richieste di supporto"], ["/impresa/abbonamento", "Abbonamento"], ["/guida", "Guida"],
  ] : utente.ruolo === "revisore" ? [
    ["/catalogo", "Catalogo"], ["/misure", "Misure"], ["/feedback", "I miei giudizi"],
    ...(imprese ? [["/imprese", "Imprese"], ["/campagne", "Campagne"]] as [string, string][] : []), ["/guida", "Guida"],
  ] : [];
  const attiva = [...voci].sort((a, b) => b[0].length - a[0].length).find(([to, , fine]) =>
    fine ? posizione.pathname === to : posizione.pathname === to || posizione.pathname.startsWith(to + "/"));
  // Sul telefono il pulsante del menu dice in che pagina si e'; le pagine di dettaglio prendono il nome della loro sezione.
  const nomePagina = attiva?.[1] || [["/bandi/", "Catalogo"], ["/fonti/", "Fonti"], ["/impresa/bandi/", "I miei bandi"], ["/account", "Il mio account"]]
    .find(([inizio]) => posizione.pathname.startsWith(inizio))?.[1] || "Menu";
  return (
    <ContestoUtente.Provider value={utente}>
      <header className="barra">
        <span className="logo">Bandi Radar</span>
        <Segnala />
        <button className="menu-pulsante" aria-expanded={menuAperto} aria-controls="menu-corpo"
          onClick={() => setMenuAperto(!menuAperto)}>{menuAperto ? "✕" : "☰"} {nomePagina}</button>
        <div id="menu-corpo" className={`menu-corpo${menuAperto ? " aperto" : ""}`}>
          {voci.length > 0 && <nav>{voci.map(([to, testo, fine], i) => <span key={to}>
            {i > 0 && <span className="sep">{" · "}</span>}<NavLink to={to} end={fine} className={classe}>{testo}</NavLink></span>)}</nav>}
          <span className="chi-sono">
            <NavLink to="/account" className={classe} title="Il mio account">{utente.nome || utente.email}</NavLink> <span className="piccolo">({NOMI_RUOLO_UTENTE[utente.ruolo]})</span>{" "}
            <button onClick={esci}>Esci</button>
          </span>
        </div>
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
            <Route path="/account" element={<Account />} />
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
            <Route path="/segnalazioni" element={<Segnalazioni />} />
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
            <Route path="/account" element={<Account />} />
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
            <Route path="/account" element={<Account />} />
            <Route path="*" element={<Navigate to="/impresa" replace />} />
          </Routes>
        )}
      </main>
    </ContestoUtente.Provider>
  );
}
