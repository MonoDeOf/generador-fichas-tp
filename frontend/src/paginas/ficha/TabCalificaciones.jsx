import { api } from '../../api/cliente'
import { ConDatos } from '../../componentes/Estado'
import { useDatos } from '../../hooks/useDatos'

function Notas({ semestre }) {
  if (!semestre.notas.length) return <span className="text-secondary">-</span>
  return (
    <>
      {semestre.notas.map((n) => (
        <span key={n.numero_evaluacion} className={`me-2 ${n.nota < 4 ? 'text-danger fw-semibold' : ''}`} title={`Evaluación ${n.numero_evaluacion}`}>
          {n.nota.toFixed(1)}
        </span>
      ))}
      <strong className={semestre.promedio < 4 ? 'text-danger' : ''}>(prom. {semestre.promedio.toFixed(1)})</strong>
    </>
  )
}

export default function TabCalificaciones({ rut }) {
  const estado = useDatos(() => api.calificaciones(rut), [rut])
  return (
    <ConDatos estado={estado}>
      {(filas) => (
        <div className="card">
          <div className="table-responsive">
            <table className="table table-sm align-middle mb-0">
              <thead><tr><th>Asignatura</th><th>Horas</th><th>Semestre 1</th><th>Semestre 2</th></tr></thead>
              <tbody>
                {filas.map((f) => (
                  <tr key={f.id_asignatura}>
                    <td>{f.nombre_asignatura}</td><td>{f.horas}</td>
                    <td><Notas semestre={f.semestres[0]} /></td><td><Notas semestre={f.semestres[1]} /></td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          <div className="card-footer small text-secondary">Notas bajo 4.0 destacadas en rojo.</div>
        </div>
      )}
    </ConDatos>
  )
}
