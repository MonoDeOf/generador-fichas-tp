import { useEffect, useRef, useState } from "react";

// Vacío = mismo servidor que sirve la página (FastAPI).
const API_URL = "";

type RiskConfig = {
  umbral_asistencia: number;
  minimo_notas_deficientes: number;
  nota_deficiente: number;
  atraso_cuenta_como_asistencia: boolean;
  operador_logico: "AND" | "OR";
};

type StudentRisk = {
  rut_estudiante: string;
  nombre: string;
  apellido_paterno: string;
  asistencia: number | null;
  cantidad_notas_deficientes: number;
  cumple_condicion_asistencia: boolean;
  cumple_condicion_notas: boolean;
  operador_logico: string;
  regla_disparada: boolean;
  nivel_riesgo: "BAJO" | "MEDIO" | "ALTO";
};

type DbStatus = {
  cargada: boolean;
  tablas: Record<string, number>;
  cargada_en: string | null;
};

const leerError = async (response: Response, porDefecto: string) => {
  try {
    const data = await response.json();
    return typeof data.detail === "string" ? data.detail : porDefecto;
  } catch {
    return porDefecto;
  }
};

export default function RiskPage() {
  // --- Base de datos ---
  const [dbStatus, setDbStatus] = useState<DbStatus | null>(null);
  const [archivos, setArchivos] = useState<File[]>([]);
  const [subiendo, setSubiendo] = useState(false);
  const [mensajeDb, setMensajeDb] = useState("");
  const [errorDb, setErrorDb] = useState(false);
  const [versionDb, setVersionDb] = useState(0);
  const inputArchivosRef = useRef<HTMLInputElement>(null);

  // --- Configuración ---
  const [umbralAsistencia, setUmbralAsistencia] = useState(75);
  const [minimoNotasDeficientes, setMinimoNotasDeficientes] = useState(2);
  const [notaDeficiente, setNotaDeficiente] = useState(4.0);
  const [atrasoCuenta, setAtrasoCuenta] = useState(true);
  const [operadorLogico, setOperadorLogico] = useState<"AND" | "OR">("AND");
  const [mensaje, setMensaje] = useState("");
  const [errorConfig, setErrorConfig] = useState(false);

  // --- Estudiantes ---
  const [estudiantes, setEstudiantes] = useState<StudentRisk[]>([]);
  const [cargandoEstudiantes, setCargandoEstudiantes] = useState(false);
  const [errorEstudiantes, setErrorEstudiantes] = useState("");

  const dbLista = dbStatus?.cargada === true;

  const cargarEstadoDb = async () => {
    try {
      const response = await fetch(`${API_URL}/api/db-status`);
      if (!response.ok) throw new Error();
      const data: DbStatus = await response.json();
      setDbStatus(data);
      return data;
    } catch {
      setDbStatus({ cargada: false, tablas: {}, cargada_en: null });
      setMensajeDb("No se pudo conectar con el servidor.");
      setErrorDb(true);
      return null;
    }
  };

  const cargarConfiguracion = async () => {
    try {
      const response = await fetch(`${API_URL}/api/risk-config`);
      if (!response.ok) throw new Error();
      const data: RiskConfig = await response.json();
      setUmbralAsistencia(data.umbral_asistencia);
      setMinimoNotasDeficientes(data.minimo_notas_deficientes);
      setNotaDeficiente(data.nota_deficiente);
      setAtrasoCuenta(data.atraso_cuenta_como_asistencia);
      setOperadorLogico(data.operador_logico);
    } catch {
      setMensaje("No se pudo cargar la configuración actual.");
      setErrorConfig(true);
    }
  };

  const cargarEstudiantes = async () => {
    try {
      setCargandoEstudiantes(true);
      setErrorEstudiantes("");
      const response = await fetch(`${API_URL}/api/students-risk`);
      if (!response.ok) throw new Error();
      const data: StudentRisk[] = await response.json();
      setEstudiantes(data);
    } catch {
      setErrorEstudiantes("No se pudo cargar la lista de estudiantes.");
    } finally {
      setCargandoEstudiantes(false);
    }
  };

  useEffect(() => {
    cargarEstadoDb();
  }, []);

  // Cuando la base queda disponible, se habilita el resto del flujo.
  useEffect(() => {
    if (dbLista) {
      cargarConfiguracion();
      cargarEstudiantes();
    } else {
      setEstudiantes([]);
    }
  }, [dbLista, versionDb]);

  const subirBaseDatos = async (e: React.FormEvent) => {
    e.preventDefault();
    setMensajeDb("");
    setErrorDb(false);

    if (archivos.length === 0) {
      setMensajeDb("Selecciona los archivos CSV o un ZIP que los contenga.");
      setErrorDb(true);
      return;
    }

    const formData = new FormData();
    archivos.forEach((archivo) => formData.append("files", archivo));

    try {
      setSubiendo(true);
      const response = await fetch(`${API_URL}/api/upload-db`, {
        method: "POST",
        body: formData,
      });

      if (!response.ok) {
        throw new Error(
          await leerError(response, "No se pudo cargar la base de datos.")
        );
      }

      const data: DbStatus = await response.json();
      setDbStatus(data);
      setVersionDb((v) => v + 1);
      setArchivos([]);
      if (inputArchivosRef.current) inputArchivosRef.current.value = "";
      setMensajeDb(
        `Base de datos cargada: ${Object.keys(data.tablas).length} tablas.`
      );
    } catch (err) {
      setMensajeDb(
        err instanceof Error && err.message
          ? err.message
          : "No se pudo cargar la base de datos."
      );
      setErrorDb(true);
    } finally {
      setSubiendo(false);
    }
  };

  const descartarBaseDatos = async () => {
    if (!confirm("¿Descartar la base de datos cargada?")) return;
    try {
      await fetch(`${API_URL}/api/db`, { method: "DELETE" });
    } finally {
      setMensaje("");
      setMensajeDb("");
      await cargarEstadoDb();
    }
  };

  const guardarConfiguracion = async (e: React.FormEvent) => {
    e.preventDefault();
    setMensaje("");
    setErrorConfig(false);

    const error = (texto: string) => {
      setMensaje(texto);
      setErrorConfig(true);
    };

    if (umbralAsistencia < 0 || umbralAsistencia > 100) {
      return error("El porcentaje de asistencia debe estar entre 0 y 100.");
    }
    if (minimoNotasDeficientes < 0) {
      return error(
        "La cantidad mínima de notas deficientes no puede ser negativa."
      );
    }
    if (notaDeficiente < 1 || notaDeficiente > 7) {
      return error("La nota deficiente debe estar entre 1.0 y 7.0.");
    }

    try {
      const response = await fetch(`${API_URL}/api/risk-config`, {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          umbral_asistencia: umbralAsistencia,
          minimo_notas_deficientes: minimoNotasDeficientes,
          nota_deficiente: notaDeficiente,
          atraso_cuenta_como_asistencia: atrasoCuenta,
          operador_logico: operadorLogico,
        }),
      });

      if (!response.ok) {
        throw new Error(
          await leerError(response, "No se pudo guardar la configuración.")
        );
      }

      setMensaje("Configuración actualizada correctamente.");
      await cargarEstudiantes();
    } catch (err) {
      error(
        err instanceof Error && err.message
          ? err.message
          : "No se pudo guardar la configuración."
      );
    }
  };

  const obtenerClaseRiesgo = (nivel: StudentRisk["nivel_riesgo"]) => {
    if (nivel === "ALTO") return "risk-dot risk-high";
    if (nivel === "MEDIO") return "risk-dot risk-medium";
    return "risk-dot risk-low";
  };

  const resumen = {
    ALTO: estudiantes.filter((e) => e.nivel_riesgo === "ALTO").length,
    MEDIO: estudiantes.filter((e) => e.nivel_riesgo === "MEDIO").length,
    BAJO: estudiantes.filter((e) => e.nivel_riesgo === "BAJO").length,
  };

  return (
    <div className="content">
        {/* PASO 1: Cargar base de datos */}
        <section className="card">
          <div className="header">
            <span className="step">Paso 1</span>
            <h1>Cargar base de datos</h1>
            <p>
              Sube los archivos CSV de la base (uno por tabla) o un ZIP que
              los contenga. Son obligatorios <strong>ESTUDIANTE.csv</strong>,{" "}
              <strong>ASISTENCIA.csv</strong> y{" "}
              <strong>CALIFICACION.csv</strong>.
            </p>
          </div>

          {dbLista && dbStatus && (
            <div className="db-status">
              <div className="db-status-header">
                <strong>✓ Base de datos cargada</strong>
                {dbStatus.cargada_en && (
                  <span>
                    {new Date(dbStatus.cargada_en).toLocaleString("es-CL")}
                  </span>
                )}
              </div>
              <ul className="table-chips">
                {Object.entries(dbStatus.tablas).map(([tabla, filas]) => (
                  <li key={tabla}>
                    {tabla} <span>{filas.toLocaleString("es-CL")}</span>
                  </li>
                ))}
              </ul>
            </div>
          )}

          <form onSubmit={subirBaseDatos}>
            <div className="field">
              <label htmlFor="archivos">
                {dbLista ? "Reemplazar con otros archivos" : "Archivos CSV o ZIP"}
              </label>
              <input
                ref={inputArchivosRef}
                id="archivos"
                type="file"
                accept=".csv,.zip"
                multiple
                onChange={(e) => setArchivos(Array.from(e.target.files ?? []))}
              />
              {archivos.length > 0 && (
                <small className="hint">
                  {archivos.length} archivo(s) seleccionado(s):{" "}
                  {archivos.map((a) => a.name).join(", ")}
                </small>
              )}
            </div>

            <div className="actions">
              <button type="submit" disabled={subiendo}>
                {subiendo
                  ? "Cargando..."
                  : dbLista
                  ? "Reemplazar base de datos"
                  : "Cargar base de datos"}
              </button>
              {dbLista && (
                <button
                  type="button"
                  className="secondary"
                  onClick={descartarBaseDatos}
                >
                  Descartar base
                </button>
              )}
            </div>

            {mensajeDb && (
              <p className={`message ${errorDb ? "error" : ""}`}>{mensajeDb}</p>
            )}
          </form>
        </section>

        {/* PASO 2: Configuración */}
        <section className={`card ${dbLista ? "" : "locked"}`}>
          <div className="header">
            <span className="step">Paso 2</span>
            <h2>Configuración de riesgo</h2>
            <p>
              {dbLista
                ? "Modifica los criterios utilizados para identificar estudiantes en situación de riesgo."
                : "Carga la base de datos para poder configurar los umbrales."}
            </p>
          </div>

          <form onSubmit={guardarConfiguracion}>
            <fieldset disabled={!dbLista}>
              <div className="grid">
                <div className="field">
                  <label htmlFor="asistencia">Umbral crítico de asistencia</label>
                  <div className="input-with-suffix">
                    <input
                      id="asistencia"
                      type="number"
                      min="0"
                      max="100"
                      step="0.1"
                      value={umbralAsistencia}
                      onChange={(e) =>
                        setUmbralAsistencia(Number(e.target.value))
                      }
                    />
                    <span>%</span>
                  </div>
                  <small className="hint">
                    Se cumple si la asistencia es menor a este valor.
                  </small>
                </div>

                <div className="field">
                  <label htmlFor="nota-deficiente">Nota deficiente bajo</label>
                  <input
                    id="nota-deficiente"
                    type="number"
                    min="1"
                    max="7"
                    step="0.1"
                    value={notaDeficiente}
                    onChange={(e) => setNotaDeficiente(Number(e.target.value))}
                  />
                  <small className="hint">
                    Una nota cuenta como deficiente si es menor a este valor.
                  </small>
                </div>

                <div className="field">
                  <label htmlFor="notas">
                    Cantidad mínima de notas deficientes
                  </label>
                  <input
                    id="notas"
                    type="number"
                    min="0"
                    value={minimoNotasDeficientes}
                    onChange={(e) =>
                      setMinimoNotasDeficientes(Number(e.target.value))
                    }
                  />
                </div>

                <div className="field">
                  <label htmlFor="operador">Operador lógico</label>
                  <select
                    id="operador"
                    value={operadorLogico}
                    onChange={(e) =>
                      setOperadorLogico(e.target.value as "AND" | "OR")
                    }
                  >
                    <option value="AND">AND (ambas condiciones)</option>
                    <option value="OR">OR (cualquiera de las dos)</option>
                  </select>
                </div>
              </div>

              <label className="checkbox">
                <input
                  type="checkbox"
                  checked={atrasoCuenta}
                  onChange={(e) => setAtrasoCuenta(e.target.checked)}
                />
                Contar los atrasos como asistencia
              </label>

              <button type="submit">Guardar cambios</button>
            </fieldset>

            {mensaje && (
              <p className={`message ${errorConfig ? "error" : ""}`}>
                {mensaje}
              </p>
            )}
          </form>
        </section>

        {/* PASO 3: Estudiantes */}
        {dbLista && (
          <section className="card students-card">
            <div className="header">
              <span className="step">Resultado</span>
              <h2>Lista de estudiantes</h2>
              <p>Nivel de riesgo calculado según la configuración vigente.</p>
            </div>

            {!cargandoEstudiantes && !errorEstudiantes && (
              <div className="summary">
                <span>
                  <i className="risk-dot risk-high" /> {resumen.ALTO} alto
                </span>
                <span>
                  <i className="risk-dot risk-medium" /> {resumen.MEDIO} medio
                </span>
                <span>
                  <i className="risk-dot risk-low" /> {resumen.BAJO} bajo
                </span>
              </div>
            )}

            {cargandoEstudiantes && <p>Cargando estudiantes...</p>}

            {errorEstudiantes && (
              <p className="message error">{errorEstudiantes}</p>
            )}

            {!cargandoEstudiantes && !errorEstudiantes && (
              <div className="table-wrapper">
                <table className="students-table">
                  <thead>
                    <tr>
                      <th>Estudiante</th>
                      <th>RUT</th>
                      <th>Asistencia</th>
                      <th>Notas deficientes</th>
                      <th>Riesgo</th>
                    </tr>
                  </thead>
                  <tbody>
                    {estudiantes.map((estudiante) => (
                      <tr key={estudiante.rut_estudiante}>
                        <td>
                          {estudiante.nombre} {estudiante.apellido_paterno}
                        </td>
                        <td>{estudiante.rut_estudiante}</td>
                        <td
                          className={
                            estudiante.cumple_condicion_asistencia ? "flag" : ""
                          }
                        >
                          {estudiante.asistencia === null
                            ? "Sin registros"
                            : `${estudiante.asistencia}%`}
                        </td>
                        <td
                          className={
                            estudiante.cumple_condicion_notas ? "flag" : ""
                          }
                        >
                          {estudiante.cantidad_notas_deficientes}
                        </td>
                        <td>
                          <div className="risk-cell">
                            <span
                              className={obtenerClaseRiesgo(
                                estudiante.nivel_riesgo
                              )}
                              aria-label={`Riesgo ${estudiante.nivel_riesgo}`}
                            />
                            <span>{estudiante.nivel_riesgo}</span>
                          </div>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </section>
        )}
    </div>
  );
}

