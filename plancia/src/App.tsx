import { NavLink, Route, Routes } from "react-router-dom";
import Fonti from "./pagine/Fonti";
import DettaglioFonte from "./pagine/DettaglioFonte";
import Catalogo from "./pagine/Catalogo";
import Novita from "./pagine/Novita";
import Settimana from "./pagine/Settimana";

export default function App() {
  const classe = ({ isActive }: { isActive: boolean }) => (isActive ? "attivo" : "");
  return (
    <>
      <header className="barra">
        <span className="logo">Bandi Radar</span>
        <nav>
          <NavLink to="/" end className={classe}>Fonti</NavLink>{" · "}
          <NavLink to="/catalogo" className={classe}>Catalogo</NavLink>{" · "}
          <NavLink to="/novita" className={classe}>Novità</NavLink>
        </nav>
      </header>
      <main>
        <Routes>
          <Route path="/" element={<Fonti />} />
          <Route path="/fonti/:id" element={<DettaglioFonte />} />
          <Route path="/catalogo" element={<Catalogo />} />
          <Route path="/novita" element={<Novita />} />
          <Route path="/novita/:chiave" element={<Settimana />} />
        </Routes>
      </main>
    </>
  );
}
