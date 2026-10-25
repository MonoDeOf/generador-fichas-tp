import { api } from '../api/cliente'
import { ConDatos } from '../componentes/Estado'
import { useDatos } from '../hooks/useDatos'
import { enlace } from '../hooks/useRuta'

// RF03 / HU 1.3: resumen semanal de estudiantes que ingresaron o permanecen en riesgo.
export default function ReportesSemanales() {
  const estado = useDatos(() => api.reportesSemanales())
  return (
    <>
      <h1 className="h3">Reportes semanales</h1>
      <p className="text-secondary">Se generan automáticamente los viernes a las 14:00.</p>
      <ConDatos estado={estado}>
        {(reportes) => reportes.length === 0 ? <p className="text-secondary">Aún no hay reportes generados.</p> : reportes.map((r) => (
          <div className="card mb-3" key={`${r.semana}-${r.profesor}`}>
            <div className="card-header d-flex justify-content-between flex-wrap">
              <strong>Semana {r.semana} · {r.profesor}</strong>
              <small>{r.fecha_generacion.replace('T', ' ')} · {r.enviado_correo ? 'Enviado por correo' : 'No enviado por correo'}</small>
            </div>
            <ul className="list-group list-group-flush">
              {r.estudiantes.map((e) => (
                <li className="list-group-item d-flex gap-2 align-items-center" key={e.rut_estudiante}>
                  <span className={`semaforo semaforo-${e.nivel_riesgo}`} aria-label={e.nivel_riesgo} />
                  <a href={enlace('estudiante', e.rut_estudiante)}>{e.nombre}</a>
                  <span className={`badge ${e.condicion === 'nuevo' ? 'bg-danger' : 'bg-secondary'}`}>
                    {e.condicion === 'nuevo' ? 'Ingresó esta semana' : 'Permanece'}
                  </span>
                </li>
              ))}
            </ul>
          </div>
        ))}
      </ConDatos>
    </>
  )
}
