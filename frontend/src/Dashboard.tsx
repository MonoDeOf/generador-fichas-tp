import { useEffect, useRef, useState } from "react";

const API_URL = "";

type Props = { onIrACarga: () => void };

/**
 * Muestra el Dashboard Directivo original (backend/templates/dashboard.html)
 * tal cual, dentro de un iframe. Así conserva exactamente su diseño, estilos
 * y gráficos, sin mezclarse con los estilos de esta app.
 */
export default function Dashboard({ onIrACarga }: Props) {
  const [estado, setEstado] = useState<"cargando" | "sin-db" | "error" | "ok">(
    "cargando"
  );
  const [alto, setAlto] = useState(900);
  const iframeRef = useRef<HTMLIFrameElement>(null);

  useEffect(() => {
    (async () => {
      try {
        const r = await fetch(`${API_URL}/api/db-status`);
        if (!r.ok) throw new Error();
        const data = await r.json();
        setEstado(data.cargada ? "ok" : "sin-db");
      } catch {
        setEstado("error");
      }
    })();
  }, []);

  // Ajusta la altura del iframe a su contenido para que no tenga scroll propio.
  const alCargar = () => {
    const doc = iframeRef.current?.contentDocument;
    if (!doc) return;
    const medir = () => setAlto(doc.documentElement.scrollHeight);
    medir();
    new ResizeObserver(medir).observe(doc.body);
  };

  if (estado === "cargando") {
    return (
      <main className="page">
        <div className="content">
          <p>Cargando dashboard...</p>
        </div>
      </main>
    );
  }

  if (estado !== "ok") {
    return (
      <main className="page">
        <div className="content">
          <section className="card empty-state">
            <h2>
              {estado === "sin-db" ? "Aún no hay datos" : "No se pudo conectar"}
            </h2>
            <p>
              {estado === "sin-db"
                ? "El dashboard se construye a partir de la base de datos. Primero carga los CSV en la sección Riesgo."
                : "No se pudo conectar con el servidor."}
            </p>
            {estado === "sin-db" && (
              <button type="button" className="inline-button" onClick={onIrACarga}>
                Ir a cargar la base de datos
              </button>
            )}
          </section>
        </div>
      </main>
    );
  }

  return (
    <iframe
      ref={iframeRef}
      src={`${API_URL}/dashboard-original`}
      title="Dashboard Directivo"
      onLoad={alCargar}
      style={{ display: "block", width: "100%", height: alto, border: 0 }}
    />
  );
}
