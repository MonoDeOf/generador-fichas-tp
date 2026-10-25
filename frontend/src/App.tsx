import { useEffect, useState } from "react";
import "./App.css";
import Dashboard from "./Dashboard";
import RiskPage from "./RiskPage";

type Pagina = "riesgo" | "dashboard";

// La página activa se guarda en la URL (#/dashboard) para que
// recargar el navegador no te devuelva al inicio.
const leerPagina = (): Pagina =>
  window.location.hash.replace("#/", "") === "dashboard" ? "dashboard" : "riesgo";

function App() {
  const [pagina, setPagina] = useState<Pagina>(leerPagina);

  useEffect(() => {
    const alCambiar = () => setPagina(leerPagina());
    window.addEventListener("hashchange", alCambiar);
    return () => window.removeEventListener("hashchange", alCambiar);
  }, []);

  const irA = (p: Pagina) => {
    window.location.hash = `/${p}`;
    window.scrollTo({ top: 0 });
  };

  return (
    <>
      <header className="app-header">
        <div className="app-header-inner">
          <div className="brand">
            <span className="brand-mark" aria-hidden="true">H</span>
            <span>Proyecto Horizonte</span>
          </div>

          <nav className="nav" aria-label="Secciones">
            <a
              href="#/riesgo"
              className={pagina === "riesgo" ? "active" : ""}
              aria-current={pagina === "riesgo" ? "page" : undefined}
            >
              Riesgo
            </a>
            <a
              href="#/dashboard"
              className={pagina === "dashboard" ? "active" : ""}
              aria-current={pagina === "dashboard" ? "page" : undefined}
            >
              Dashboard
            </a>
          </nav>
        </div>
      </header>

      {pagina === "riesgo" ? (
        <main className="page">
          <RiskPage />
        </main>
      ) : (
        <Dashboard onIrACarga={() => irA("riesgo")} />
      )}
    </>
  );
}

export default App;
