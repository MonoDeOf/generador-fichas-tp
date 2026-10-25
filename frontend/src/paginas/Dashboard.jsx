import { api } from '../api/cliente'
import { ConDatos } from '../componentes/Estado'
import GraficoBarras from '../componentes/GraficoBarras'
import { useDatos } from '../hooks/useDatos'

const COLOR_RIESGO = { Rojo: '#dc3545', Amarillo: '#ffc107', Verde: '#198754' }

function Indicador({ titulo, valor }) {
  return (
    <div className="col-6 col-md-3">
      <div className="card card-body h-100">
        <div className="text-secondary small">{titulo}</div>
        <div className="fs-3 fw-semibold">{valor ?? '-'}</div>
      </div>
    </div>
  )
}

function TablaGrupos({ titulo, filas }) {
  return (
    <div className="card card-body mb-4">
      <h2 className="h5">{titulo}</h2>
      <div className="table-responsive">
        <table className="table table-sm align-middle mb-0">
          <thead><tr><th>Grupo</th><th>Estudiantes</th><th>Asistencia prom.</th><th>Inasistencia</th><th>Atrasos</th>
            <th>Rojo</th><th>Amarillo</th><th>Verde</th></tr></thead>
          <tbody>
            {filas.map((f) => (
              <tr key={f.id}><td>{f.nombre}</td><td>{f.estudiantes}</td><td>{f.asistencia_promedio}%</td>
                <td>{f.tasa_inasistencia}%</td><td>{f.tasa_atraso}%</td>
                <td>{f.riesgo.Rojo}</td><td>{f.riesgo.Amarillo}</td><td>{f.riesgo.Verde}</td></tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  )
}

// RF02 / HU 1.2: indicadores generales del liceo (solo datos agregados).
export default function Dashboard() {
  const estado = useDatos(() => api.dashboard())
  return (
    <ConDatos estado={estado}>
      {(d) => d.total_estudiantes === 0 ? (
        <>
          <h1 className="h3">Dashboard institucional</h1>
          <div className="alert alert-info">Aún no hay datos cargados. El administrador debe importar los archivos CSV en "Importar datos".</div>
        </>
      ) : (
        <>
          <h1 className="h3">Dashboard institucional</h1>
          <p className="text-secondary">Periodo con registros: {d.periodo.desde} a {d.periodo.hasta}</p>
          <div className="row g-3 mb-4">
            <Indicador titulo="Estudiantes" valor={d.total_estudiantes} />
            <Indicador titulo="Tasa de asistencia" valor={`${d.tasa_asistencia}%`} />
            <Indicador titulo="Tasa de inasistencia" valor={`${d.tasa_inasistencia}%`} />
            <Indicador titulo="Tasa de atrasos" valor={`${d.tasa_atraso}%`} />
          </div>
          <div className="row g-4 mb-4">
            <div className="col-lg-6">
              <div className="card card-body h-100">
                <h2 className="h5">Asistencia promedio por nivel</h2>
                <GraficoBarras datos={d.por_nivel.map((n) => ({ etiqueta: n.nombre, valor: n.asistencia_promedio }))} />
              </div>
            </div>
            <div className="col-lg-6">
              <div className="card card-body h-100">
                <h2 className="h5">Niveles de riesgo</h2>
                <GraficoBarras maximo={d.total_estudiantes} sufijo=""
                  datos={Object.entries(d.riesgo).map(([nivel, n]) => ({ etiqueta: nivel, valor: n, color: COLOR_RIESGO[nivel] }))} />
              </div>
            </div>
          </div>
          <div className="card card-body mb-4">
            <h2 className="h5">Tendencia mensual de inasistencia</h2>
            <GraficoBarras maximo={Math.max(...d.por_mes.map((m) => m.tasa_inasistencia), 1)} color="#dc3545"
              datos={d.por_mes.map((m) => ({ etiqueta: m.mes, valor: m.tasa_inasistencia }))} />
          </div>
          <TablaGrupos titulo="Por nivel" filas={d.por_nivel} />
          <TablaGrupos titulo="Por especialidad (3M y 4M)" filas={d.por_especialidad} />
        </>
      )}
    </ConDatos>
  )
}
